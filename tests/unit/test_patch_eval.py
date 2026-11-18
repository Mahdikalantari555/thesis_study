"""Patch arms inside eval_dev: the join, the reference, the injection.

Covers ``patch-level-controlled-trial`` task 2.4's data-free half: how a patch
store is joined to a field-level cycle list, how the calibration reference for
the empirical p-value is built, and that a severity cell is injected in the
PATCH tensor with the field-level ladder's severity and hashes.
"""

from __future__ import annotations

import numpy as np
import pytest
from tests.patch_fixtures import bind_patch_store

from ssl_anomaly.io import patches as P
from ssl_anomaly.monitor import patch_eval as PE
from ssl_anomaly.monitor import patch_scores as PS
from ssl_anomaly.monitor import severity_table as sev
from ssl_anomaly.train import patch_data as PD

T, C, S = P.N_BINS, P.N_CHANNELS, 8


def _store(tmp_path, field_ids=(11, 22), n_cycles=3, seed=0):
    g = np.random.default_rng(seed)
    root = P.create_store(tmp_path / "patches.zarr", field_ids=list(field_ids),
                          max_cycles=n_cycles, size=S)
    root["field_ids"][:] = np.asarray(field_ids, dtype=np.int64)
    for fi in range(len(field_ids)):
        root["in_field"][fi, 0, : S // 2, : S // 2] = 1
        for ci in range(n_cycles):
            root["cycle_valid"][fi, ci] = 1
            root["cycle_ids"][fi, ci] = ci
            root["cycle_start_day"][fi, ci] = 10 + ci
            root["cycle_end_day"][fi, ci] = 10 + ci + P.MAX_CYCLE_DAYS - 1
            root["sensor_id"][fi, ci] = 1
            root["n_obs"][fi, ci] = 2
            vals = g.normal(0.4, 0.05, size=(T, C, S, S)).astype(np.float32)
            # out-of-field pixels carry garbage on purpose: they must never be read
            vals[:, :, S // 2 :, :] = 99.0
            root["values"][fi, ci] = vals
            root["pixel_valid"][fi, ci, :, 0] = 1
    bind_patch_store(root, known=field_ids)
    return root


def _norm(median=0.4, iqr=0.05):
    per_ch = {name: {"median": median, "iqr": iqr, "n": 100} for name in P.CHANNELS}
    return {"stats": {"L8": per_ch, "L9": per_ch, "unknown": per_ch},
            "channel_order": list(P.CHANNELS)}


# --- the join ------------------------------------------------------------
def test_join_uses_field_and_cycle_ids_not_row_position(tmp_path):
    root = _store(tmp_path)
    root["cycle_ids"][1, 1] = 81  # the ID need not equal the slot
    out = PE.patch_batch_for_cycles(root, [22, 11], [81, 2], norm=_norm())
    assert out["X"].shape == (2, T, C, S, S)
    # row 0 must be field 22 / cycle 1, i.e. the SECOND store row
    direct = np.asarray(root["values"][1, 1], dtype=np.float32)
    in_field = np.asarray(root["in_field"][1, 0], dtype=bool)
    expect = np.where(np.isfinite(direct) & in_field[None, None], (direct - 0.4) / 0.05, 0.0)
    np.testing.assert_allclose(out["X"][0], expect, rtol=1e-5, atol=1e-5)


def test_join_refuses_a_field_absent_from_the_store(tmp_path):
    root = _store(tmp_path)
    with pytest.raises(ValueError, match="not in the store"):
        PE.patch_batch_for_cycles(root, [11, 999], [0, 0], norm=_norm())


def test_join_refuses_misaligned_id_vectors(tmp_path):
    root = _store(tmp_path)
    with pytest.raises(ValueError, match="must align"):
        PE.patch_batch_for_cycles(root, [11, 22], [0], norm=_norm())


def test_join_normalizes_and_never_asserts_out_of_field_pixels(tmp_path):
    root = _store(tmp_path)
    out = PE.patch_batch_for_cycles(root, [11], [0], norm=_norm())
    assert out["pixel_valid"][0, 0, S // 2 :, :].sum() == 0
    assert out["pixel_valid"][0, 0, : S // 2, : S // 2].all()
    assert np.abs(out["X"][0][:, :, S // 2 :, :]).max() == 0.0   # zero-filled, not 99


def test_join_keeps_unobserved_values_at_zero_after_normalization(tmp_path):
    root = _store(tmp_path)
    root["values"][0, 0, 5] = np.nan
    out = PE.patch_batch_for_cycles(root, [11], [0], norm=_norm())
    assert np.all(out["X"][0, 5] == 0.0)


def test_join_flags_a_missing_channel_sidecar(tmp_path):
    root = _store(tmp_path)
    with pytest.raises(ValueError, match="expected stats"):
        PE.patch_batch_for_cycles(root, [11], [0], norm={})


# --- reference paths -----------------------------------------------------
class _Arm:
    """Minimal stand-in for PatchArmScorer.loo_batch."""

    def __init__(self, value=1.0):
        self.value = value
        self.seen = []

    def loo_batch(self, X, M, **kw):
        self.seen.append(X.shape[0])
        return np.full((X.shape[0], X.shape[1]), self.value), np.zeros(
            (X.shape[0], X.shape[1], X.shape[2]))


def test_reference_paths_use_only_the_calibration_indices():
    arm = _Arm()
    batch = {"X": np.zeros((6, T, C, S, S), dtype=np.float32),
             "pixel_valid": np.ones((6, T, S, S), bool)}
    paths = PE.patch_reference_paths(arm, batch, reference_idx=np.array([0, 2, 4]), chunk=2)
    assert paths.shape == (3, T)
    assert arm.seen == [2, 1]          # chunked, and only three samples read


def test_reference_paths_refuse_an_empty_calibration_set():
    with pytest.raises(ValueError, match="calibration"):
        PE.patch_reference_paths(_Arm(), {"X": np.zeros((2, T, C, S, S))},
                                 reference_idx=np.array([], dtype=int))


# --- severity cell -------------------------------------------------------
def _scorer(n=4, seed=0, in_field_shape=None):
    g = np.random.default_rng(seed)
    res = g.normal(0, 1, size=(n, T, C, S, S))
    obs = g.random((n, T, C, S, S)) > 0.2
    sigma = PS.fit_patch_sigma(res, obs, np.ones((n, T), dtype=int))
    from ssl_anomaly.models.patch_cnn_gru import build_patch_model
    model = build_patch_model(use_cnn=True, n_channels=C, d_model=8, n_horizons=2,
                              stem_widths=(8, 8))
    return PS.PatchDeepScorer("patch_cnn_gru", model, sigma,
                              in_field=np.ones((S, S), bool), n_channels=C)


def _batch(n=4, seed=0):
    g = np.random.default_rng(seed)
    raw = g.uniform(0.1, 0.7, size=(n, T, C, S, S)).astype(np.float32)
    return {"X": raw.copy(), "raw": raw, "obs": np.ones(raw.shape, bool),
            "sensor_id": np.ones((n, T), int), "norm_stats": _norm(0.0, 1.0)["stats"],
            "pixel_valid": np.ones((n, T, S, S), bool),
            "in_field": np.ones((n, S, S), bool)}


def test_cell_scores_a_patch_batch_and_records_the_injections():
    scorer = _scorer()
    arm = PS.PatchArmScorer(scorer, np.ones((12, T)))
    out = PE.patch_arm_scores(arm, _batch(), level_id="S3", family=sev.ACUTE_FAMILY,
                              index="ndvi", round_idx=0)
    assert out["z2"].shape == (4, T, 1)
    assert len(out["injections"]) == 4
    assert all("sha256" in rec for rec in out["injections"])


def test_cell_injection_uses_the_severity_table_delta():
    scorer = _scorer()
    arm = PS.PatchArmScorer(scorer, np.ones((12, T)))
    out = PE.patch_arm_scores(arm, _batch(), level_id="S6", family=sev.ACUTE_FAMILY,
                              index="ndvi", round_idx=0)
    lv = {v.level_id: v for v in sev.load_table()}["S6"]
    assert out["injections"][0]["severity"] == pytest.approx(float(lv.delta_ndvi), rel=1e-6)


def test_cell_refuses_an_unknown_level():
    arm = PS.PatchArmScorer(_scorer(), np.ones((12, T)))
    with pytest.raises(ValueError, match="unknown severity level"):
        PE.patch_arm_scores(arm, _batch(), level_id="S99", family=sev.ACUTE_FAMILY,
                            index="ndvi", round_idx=0)


def test_persistent_cell_uses_the_frozen_duration():
    arm = PS.PatchArmScorer(_scorer(), np.ones((12, T)))
    out = PE.patch_arm_scores(arm, _batch(), level_id="S3", family=sev.PERSISTENT_FAMILY,
                              index="ndvi", round_idx=0)
    assert out["injections"][0]["duration_bins"] == int(sev.PERSISTENT_DURATION_BINS)


# --- the eval_dev patch path, end to end ---------------------------------
def test_patch_severity_cli_consumes_the_new_trainer_checkpoint(tmp_path, monkeypatch):
    """Build the real norm, train the fixture and exercise the dev report path."""
    import hashlib
    import importlib.util
    import json
    from pathlib import Path

    import torch

    from ssl_anomaly.monitor import holdout as H

    repo = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("eval_dev", repo / "scripts/eval_dev.py")
    E = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(E)
    spec = importlib.util.spec_from_file_location("train_patch", repo / "scripts/train_patch.py")
    trainer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(trainer)

    root = _store(tmp_path, field_ids=(33, 11, 22), n_cycles=10)
    cycle_keys = [f"{fid}:{ci}" for fid in (11, 22) for ci in range(10)]
    splits, holdout = bind_patch_store(root, known=(11, 22, 33), dev_keys=cycle_keys)
    lock = tmp_path / "splits.json"
    lock.write_text(json.dumps(splits))
    holdout_path = H.save_holdout_manifest(holdout, path=tmp_path / "holdout.json")
    norm = P.build_patch_norm(root=root, splits_manifest=splits, holdout_manifest=holdout)
    norm_path = P.save_patch_norm(norm, tmp_path / P.NORM_STATS_NAME)
    store = tmp_path / "patches.zarr"
    assert trainer.main([
        "--splits", str(lock), "--holdout-manifest", str(holdout_path), "--store", str(store),
        "--norm", str(norm_path), "--out", str(tmp_path), "--seed", "13", "--smoke",
        "--epochs", "1", "--d-model", "8", "--n-horizons", "1", "--batch-size", "1",
        "--max-fields", "1", "--max-cycles", "1", "--device", "cpu", "--no-benchmark",
    ]) == 0
    ckpt = tmp_path / "patch_cnn_gru_seed13" / "_smoke" / "last.pt"
    norm_hash = P.norm_stats_sha256(norm)
    assert P.load_patch_norm(ckpt.with_name(P.NORM_STATS_NAME))["sha256"] == norm_hash
    # This table is only a synthetic fixture for the frozen artifact contract,
    # not an estimate of any real dev residual scale.
    sigma = PS.fit_patch_sigma(
        np.random.default_rng(0).normal(0, 1, (20, T, C, S, S)),
        np.ones((20, T, C, S, S), bool), np.ones((20, T), dtype=int),
    )
    sigma_path = tmp_path / "patch_sigma.npz"
    sigma_args = {
        "sigma": sigma.sigma, "fallback": sigma.fallback, "n": sigma.n,
        "min_n": sigma.min_n, "sha256": sigma.sha256,
        "model_sha256": hashlib.sha256(ckpt.read_bytes()).hexdigest(),
        "norm_sha256": norm_hash, "input_protocol": PD.PATCH_INPUT_PROTOCOL,
    }
    np.savez(sigma_path, **sigma_args)

    epoch = np.datetime64(splits["base_date"], "D")
    index = P.patch_cycle_index(root)
    dev = {"cycle_keys": cycle_keys,
           "start_dates": np.array([epoch + index[k].start_day for k in cycle_keys]),
           "end_dates": np.array([epoch + index[k].end_day + 1 for k in cycle_keys])}
    monkeypatch.setattr(E.msplits, "load_splits_locked", lambda: splits)
    monkeypatch.setattr(E.minputs, "load_masked_cycles", lambda: None)
    monkeypatch.setattr(E.mproto, "select_splits", lambda *_a, **_kw: dev)
    monkeypatch.setattr(E.mproto, "DEV_DIR", tmp_path / "reports")
    argv = [
        "--run-id", "r1", "--model", "patch_cnn_gru", "--scorer", "patch_cnn_gru",
        "--patch-store", str(store), "--patch-checkpoint", str(ckpt), "--patch-sigma", str(sigma_path),
        "--holdout-manifest", str(holdout_path), "--rounds", "1", "--seeds", "13", "--device", "cpu",
        "--smoke",
    ]
    assert E.main(argv) == 0
    path = tmp_path / "reports/r1/metrics_patch_cnn_gru_sev_patch_cnn_gru_smoke.json"
    assert "NaN" not in path.read_text()
    metrics = json.loads(path.read_text())
    assert metrics["ladder_rung"] == "engineering_smoke_only"
    assert metrics["input_protocol"] == PD.PATCH_INPUT_PROTOCOL
    assert metrics["protocol"] == "severity_sweep_patch_v1"
    assert metrics["n_calib_cycles"] + metrics["n_eval_cycles"] == 20
    assert metrics["n_calib_cycles"] >= 8
    result = metrics["per_seed"][0]
    assert set(result["mdm80"]) == {
        f"{fam}/{idx}" for fam in (sev.ACUTE_FAMILY, sev.PERSISTENT_FAMILY)
        for idx in ("ndvi", "savi")
    }
    assert result["patch_sigma_sha256"] == sigma.sha256
    assert result["patch_norm_sha256"] == norm_hash
    for cell in result["cells"].values():
        assert cell["n"] == metrics["n_eval_cycles"]
        assert 0.0 <= cell["detection_rate"] <= 1.0

    with pytest.raises(ValueError, match="requires exactly the seed"):
        E.main([*argv, "--seeds", "13,42"])
    dev["end_dates"][0] += np.timedelta64(1, "D")
    with pytest.raises(ValueError, match="patch bounds for 11:0"):
        E.main(argv)

    np.savez(sigma_path, **(sigma_args | {"model_sha256": "other model"}))
    with pytest.raises(ValueError, match="sigma is not bound"):
        E.load_patch_artifacts("r1", checkpoint_path=ckpt, sigma_path=sigma_path)
    payload = torch.load(ckpt, map_location="cpu", weights_only=False)
    payload["config"].pop("input_protocol")
    legacy = ckpt.with_name("legacy.pt")
    torch.save(payload, legacy)
    with pytest.raises(ValueError, match="do not rescore legacy weights"):
        E.load_patch_artifacts("r1", checkpoint_path=legacy, sigma_path=sigma_path)


def test_patch_path_refuses_an_absent_store(tmp_path):
    import importlib.util
    from pathlib import Path as _Path

    repo = _Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("eval_dev_missing",
                                                  repo / "scripts" / "eval_dev.py")
    E = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(E)
    args = E.parse_args(["--run-id", "r1", "--model", "gru_ae",
                         "--scorer", "patch_cnn_gru",
                         "--patch-store", str(tmp_path / "nope.zarr")])
    with pytest.raises(SystemExit, match="patch store not found"):
        E.run_patch_severity_protocol(args, {}, {"cycle_keys": []}, [13], "cpu")


def test_patch_path_refuses_a_cycle_missing_from_the_store(tmp_path):
    import importlib.util
    from pathlib import Path as _Path

    repo = _Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("eval_dev_missing2",
                                                  repo / "scripts" / "eval_dev.py")
    E = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(E)
    from ssl_anomaly.monitor import holdout as H

    root = _store(tmp_path, field_ids=(11,), n_cycles=1)
    keys = ["11:0", "11:5"]
    splits, holdout = bind_patch_store(root, known=(11,), dev_keys=keys)
    path = H.save_holdout_manifest(holdout, path=tmp_path / "holdout.json")
    args = E.parse_args(["--run-id", "r1", "--model", "patch_cnn_gru", "--scorer", "patch_cnn_gru",
                         "--holdout-manifest", str(path),
                         "--patch-store", str(tmp_path / "patches.zarr")])
    cycle = P.patch_cycle_index(root)["11:0"]
    epoch = np.datetime64(splits["base_date"], "D")
    with pytest.raises(ValueError, match="dev patch cycle 11:5 is not in the store"):
        E.run_patch_severity_protocol(args, splits, {
            "cycle_keys": keys, "start_dates": [epoch + cycle.start_day, epoch],
            "end_dates": [epoch + cycle.end_day + 1, epoch],
        }, [13], "cpu")
