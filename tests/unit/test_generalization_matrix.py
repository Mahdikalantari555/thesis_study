"""The matrix skeleton: cells, runtime estimate, resume, acceptance.

Covers ``patch-generalization-suite`` 1.2's data-free half and 2.2's report
shape. The acceptance function is a transcription of the pre-registered rule,
so it is tested against hand-computed cases rather than trusting the code.
"""

from __future__ import annotations

import json

import pytest

from ssl_anomaly.monitor import generalization as G
from ssl_anomaly.monitor import generalization_matrix as GM


def _folds():
    """Ten blocks in a 5x2 grid, one field each, paired by adjacency."""
    xy = {b + 1: ((b // 2) * 100.0, (b % 2) * 100.0) for b in range(10)}
    block_of = {b + 1: b for b in range(10)}
    return G.build_folds(block_of, xy)


# --- cells ---------------------------------------------------------------
def test_plan_matrix_has_a_spatial_and_a_quadrant_cell_per_fold():
    cells = GM.plan_matrix(_folds(), temporal_cutoff_day=None)
    spatial = [c for c in cells if c.axis == "spatial_fold"]
    quadrant = [c for c in cells if c.axis == "quadrant"]
    temporal = [c for c in cells if c.axis == "temporal"]
    assert len(spatial) == 5
    assert len(quadrant) == 5
    assert len(temporal) == 1


def test_temporal_cell_retrain_decision_depends_on_the_cutoff():
    a = GM.plan_matrix(_folds(), temporal_cutoff_day=None)
    b = GM.plan_matrix(_folds(), temporal_cutoff_day=200)
    ta = next(c for c in a if c.axis == "temporal")
    tb = next(c for c in b if c.axis == "temporal")
    assert ta.needs_retrain is True
    assert "cutoff unknown" in ta.reason
    assert tb.needs_retrain is False
    assert "reuse" in tb.reason


def test_spatial_cells_always_retrain():
    for c in GM.plan_matrix(_folds()):
        if c.axis in ("spatial_fold", "quadrant"):
            assert c.needs_retrain is True


def test_cell_ids_are_unique_and_hashed():
    cells = GM.plan_matrix(_folds())
    ids = [c.cell_id for c in cells]
    assert len(ids) == len(set(ids))
    assert GM.cells_sha256(cells) == GM.cells_sha256(GM.plan_matrix(_folds()))
    cells[0].held_out_blocks = [99]
    assert GM.cells_sha256(cells) != GM.cells_sha256(GM.plan_matrix(_folds()))


# --- runtime estimate ----------------------------------------------------
def test_runtime_estimate_separates_screening_from_final():
    cells = GM.plan_matrix(_folds())
    est = GM.estimate_matrix_runtime(
        cells, seconds_per_epoch=10.0, epochs=5, seconds_per_eval_cell=2.0,
    )
    assert est["n_cells"] == 11
    # 10 spatial/quadrant cells retrain; the temporal cell needs data
    # (temporal_cutoff_day=None here) so it is routed to a retrain as well
    assert est["n_retrain_cells"] == 11
    assert est["n_reuse_cells"] == 0
    with_cutoff = GM.plan_matrix(_folds(), temporal_cutoff_day=200)
    est2 = GM.estimate_matrix_runtime(with_cutoff, seconds_per_epoch=10.0, epochs=5,
                                      seconds_per_eval_cell=2.0)
    assert est2["n_retrain_cells"] == 10
    assert est2["n_reuse_cells"] == 1
    # with the defaults (6 screening arms x 1 seed vs 2 final arms x 3 seeds)
    # the two phases cost the same: 6*1 == 2*3 — the design's point is that
    # 3-seed runs are cheap only because few arms reach them
    assert est["final_seconds"] == pytest.approx(est["screening_seconds"])
    assert est["total_hours"] > 0


def test_runtime_estimate_final_runs_are_restricted_to_few_arms():
    cells = GM.plan_matrix(_folds())
    est = GM.estimate_matrix_runtime(
        cells, seconds_per_epoch=1.0, epochs=1, seconds_per_eval_cell=1.0,
        n_arms_screening=10, n_arms_final=1,
    )
    # 3 seeds x 2 arms vs 1 seed x 10 arms: final is cheaper because the design
    # restricts it to the surviving arms
    assert est["assumptions"]["arms_final"] == 1
    assert est["final_seconds"] < est["screening_seconds"] * 3


# --- resume --------------------------------------------------------------
def _cell():
    return GM.plan_matrix(_folds())[0]


def test_artifact_roundtrip_and_resume_detection(tmp_path):
    cell = _cell()
    assert GM.completed_cells(tmp_path) == set()
    GM.write_cell_artifact(tmp_path, arm="patch_cnn_gru", cell=cell, seed=13,
                           metrics={"mdm80": {"acute/ndvi": "S3"}})
    done = GM.completed_cells(tmp_path)
    assert ("patch_cnn_gru", cell.cell_id, 13) in done


def test_torn_artifact_is_not_counted_as_done(tmp_path):
    cell = _cell()
    p = GM.cell_artifact_path(tmp_path, "patch_cnn_gru", cell.cell_id, 13)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('{"arm": "patch_cnn_gru", "cell_id":')
    assert GM.completed_cells(tmp_path) == set()


def test_artifact_without_a_hash_is_not_counted(tmp_path):
    p = tmp_path / "x__y__seed13.json"
    p.write_text(json.dumps({"arm": "a", "cell_id": "b", "seed": 13}))
    assert GM.completed_cells(tmp_path) == set()


# --- aggregation ---------------------------------------------------------
def _rec(arm="arm1", cell="spatial_fold_0", axis="spatial_fold", seed=13,
         acute="S3", era=None):
    r = {"arm": arm, "cell_id": cell, "axis": axis, "seed": seed,
         "mdm80": {"acute/ndvi": acute, "persistent/ndvi": acute}}
    if era:
        r["sensor_era"] = era
    return r


def test_aggregate_parses_label_and_censored_values():
    m = GM.aggregate_matrix([_rec(acute="S3")])
    key = "arm1::spatial_fold_0"
    assert m["cells"][key]["mean_sentinel"] == pytest.approx(3.0)
    m2 = GM.aggregate_matrix([_rec(acute=">S6")])
    assert m2["cells"][key]["mean_sentinel"] == pytest.approx(GM.CENSORED_SENTINEL)


def test_aggregate_groups_by_axis_and_era():
    recs = [_rec(cell=f"spatial_fold_{i}", acute="S3") for i in range(5)]
    recs.append(_rec(cell="temporal", axis="temporal", acute="S4"))
    recs.append(_rec(cell="spatial_fold_0", acute="S3", era="L9"))
    m = GM.aggregate_matrix(recs)
    assert len(m["by_axis"]["spatial_fold"]) == 5
    assert m["by_axis"]["temporal"] == ["arm1::temporal"]
    assert m["by_era"] == ["L9"]


def test_aggregate_reports_seed_dispersion():
    recs = [_rec(seed=13, acute="S2"), _rec(seed=42, acute="S4"),
            _rec(seed=2026, acute="S3")]
    m = GM.aggregate_matrix(recs)
    rec = m["cells"]["arm1::spatial_fold_0"]
    assert rec["n_seeds"] == 3
    assert rec["std_sentinel"] > 0


# --- acceptance ----------------------------------------------------------
def _matrix(sentinels, *, temporal=None, arm="arm1"):
    recs = [{"arm": arm, "cell_id": f"spatial_fold_{i}", "axis": "spatial_fold",
             "seed": 13, "mdm80": {"acute/ndvi": v}}
            for i, v in enumerate(sentinels)]
    if temporal is not None:
        recs.append({"arm": arm, "cell_id": "temporal", "axis": "temporal",
                     "seed": 13, "mdm80": {"acute/ndvi": temporal}})
    return GM.aggregate_matrix(recs)


def test_acceptance_passes_a_tight_spread():
    verdict = GM.apply_acceptance(_matrix(["S3", "S3", "S4", "S3", "S3"], temporal="S3"),
                                  arm="arm1", dev_se_sentinel=0.5, in_block_sentinel=3.0)
    assert verdict["pass"] is True
    assert verdict["spread"] == pytest.approx(1.0)
    assert verdict["spread_limit"] == pytest.approx(1.0)


def test_acceptance_fails_a_wide_spread_and_names_the_cells():
    verdict = GM.apply_acceptance(_matrix(["S1", "S3", "S4", "S3", "S6"], temporal="S3"),
                                  arm="arm1", dev_se_sentinel=0.5, in_block_sentinel=3.0)
    assert verdict["pass"] is False
    assert verdict["conditions"]["spread_within_2se"] is False
    assert set(verdict["failing_cells"]) == {"spatial_fold_0", "spatial_fold_4"}


def test_acceptance_fails_new_censoring():
    verdict = GM.apply_acceptance(_matrix(["S3", "S3", "S3", "S3", ">S6"], temporal="S3"),
                                  arm="arm1", dev_se_sentinel=2.0, in_block_sentinel=3.0)
    assert verdict["conditions"]["no_new_censoring"] is False
    assert "spatial_fold_4" in verdict["failing_cells"]


def test_censoring_is_excused_when_the_in_block_estimate_is_censored_too():
    verdict = GM.apply_acceptance(_matrix(["S3", "S3", "S3", "S3", ">S6"], temporal="S3"),
                                  arm="arm1", dev_se_sentinel=2.0,
                                  in_block_sentinel=GM.CENSORED_SENTINEL)
    assert verdict["conditions"]["no_new_censoring"] is True


def test_acceptance_fails_a_material_temporal_drop():
    verdict = GM.apply_acceptance(_matrix(["S3"] * 5, temporal="S5"),
                                  arm="arm1", dev_se_sentinel=1.0, in_block_sentinel=3.0)
    assert verdict["conditions"]["temporal_drop_material_ok"] is False
    assert verdict["temporal_drop_levels"] == pytest.approx(2.0)


def test_acceptance_allows_a_one_level_temporal_drop():
    verdict = GM.apply_acceptance(_matrix(["S3"] * 5, temporal="S4"),
                                  arm="arm1", dev_se_sentinel=1.0, in_block_sentinel=3.0)
    assert verdict["conditions"]["temporal_drop_material_ok"] is True


def test_acceptance_requires_a_temporal_cell():
    verdict = GM.apply_acceptance(_matrix(["S3"] * 5), arm="arm1",
                                  dev_se_sentinel=1.0, in_block_sentinel=3.0)
    assert verdict["pass"] is False
    assert verdict["conditions"]["temporal_drop_material_ok"] is False


def test_acceptance_fails_an_arm_with_no_folds():
    verdict = GM.apply_acceptance({"cells": {}}, arm="ghost", dev_se_sentinel=1.0)
    assert verdict["pass"] is False
    assert "no spatial folds" in verdict["reason"]


def test_acceptance_material_threshold_is_a_constant_not_a_parameter_default():
    assert GM.MATERIAL_TEMPORAL_DROP_LEVELS == 1.0
