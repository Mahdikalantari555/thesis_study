"""Path-B families: relation model, relational appliers, shape warps, the gate.

Covers ``anomaly-definition-path-b`` tasks 1.1-1.4. These are verdict-
INDEPENDENT machinery: §2 (evaluation) is hard-gated on both path-C gates
failing, and the gate itself is tested here.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from ssl_anomaly.monitor import path_b as PB

T, C = 36, 8
NAMES = ("ndvi", "blue", "green", "red", "nir", "swir1", "swir2", "lst")


def _cycles(n=40, seed=0, *, slope=8.0):
    """Synthetic train cycles with a KNOWN lst = slope*ndvi + 300 relation."""
    g = np.random.default_rng(seed)
    X = np.zeros((n, T, C))
    M = np.ones((n, T, C), dtype=bool)
    for t in range(T):
        ndvi = 0.2 + 0.6 * np.exp(-((t - 18) ** 2) / 200.0) + g.normal(0, 0.02, n)
        X[:, t, 0] = ndvi
        X[:, t, 6] = 0.2 + 0.1 * g.normal(0, 1, n)          # swir1
        X[:, t, 7] = slope * ndvi + 300.0 + g.normal(0, 0.05, n)
    return X, M


# --- 1.1 relation model --------------------------------------------------
def test_relation_fit_recovers_the_planted_slope():
    X, M = _cycles(slope=8.0)
    fit = PB.fit_relations(X, M, NAMES)
    rec = fit.pairs["lst|ndvi"]
    slopes = np.asarray(rec["slope"], dtype=float)
    mid = slopes[np.isfinite(slopes)]
    assert mid.size > 0
    np.testing.assert_allclose(np.median(mid), 8.0, rtol=0.05)


def test_relation_fit_hash_is_deterministic_and_data_sensitive():
    X, M = _cycles()
    a = PB.fit_relations(X, M, NAMES)
    b = PB.fit_relations(X, M, NAMES)
    assert a.sha256 == b.sha256
    X2 = X.copy()
    X2[:, :, 7] += 0.4
    assert PB.fit_relations(X2, M, NAMES).sha256 != a.sha256


def test_relation_fit_is_robust_to_injected_outlier_cycles():
    """Theil-Sen, not OLS: an anomalous train cycle must not tilt the line."""
    X, M = _cycles()
    X_bad, M_bad = X.copy(), M.copy()
    X_bad[:5, 10:14, 0] -= 0.3                          # decoupled NDVI
    clean = np.median(np.asarray(PB.fit_relations(X, M, NAMES).pairs["lst|ndvi"]["slope"],
                                 dtype=float)[5:14][np.isfinite(
        np.asarray(PB.fit_relations(X, M, NAMES).pairs["lst|ndvi"]["slope"],
                   dtype=float)[5:14])])
    dirty = np.asarray(PB.fit_relations(X_bad, M_bad, NAMES).pairs["lst|ndvi"]["slope"],
                       dtype=float)
    dirty_mid = np.median(dirty[np.isfinite(dirty)])
    assert abs(dirty_mid - clean) < 0.5                  # OLS would move by ≫ 1


def test_relation_fit_needs_both_channels():
    X, M = _cycles()
    with pytest.raises(ValueError, match="needs both channels"):
        PB.fit_relations(X[:, :, :5], M[:, :, :5], NAMES[:5])


def test_relation_fit_reports_nan_where_a_bin_was_never_covered():
    X, M = _cycles()
    M[:, 30:, 7] = False                                 # no LST after bin 30
    fit = PB.fit_relations(X, M, NAMES)
    scales = np.asarray(fit.pairs["lst|ndvi"]["scale"], dtype=float)
    assert np.isnan(scales[-1])
    with pytest.raises(ValueError, match="no fit for bin"):
        fit.predict("lst|ndvi", 35, np.array([0.5]))


def test_predict_returns_the_relation_and_its_scale():
    X, M = _cycles(slope=8.0)
    fit = PB.fit_relations(X, M, NAMES)
    pred, scale = fit.predict("lst|ndvi", 12, np.array([0.5]))
    assert np.isfinite(pred).all()
    assert 300.0 < float(pred[0]) < 310.0
    assert scale > 0


# --- 1.2 relational appliers ---------------------------------------------
def _one_cycle(seed=1):
    X, M = _cycles(seed=seed)
    return X[0].copy(), M[0].copy()


def test_ndvi_drop_with_lst_held_breaks_the_relation():
    X, M = _cycles()
    fit = PB.fit_relations(X, M, NAMES)
    x, m = _one_cycle()
    out = PB.inject_relational_break(x, m, fit, pair="lst|ndvi", level_id="S4",
                                     onset_bin=12, duration_bins=2)
    # NDVI moved, LST untouched
    assert not np.allclose(out.x[12:14, 0], x[12:14, 0])
    np.testing.assert_allclose(out.x[:, 7], x[:, 7])
    assert out.meta["achieved_deviation_mad"]


def test_lst_is_held_within_epsilon():
    X, M = _cycles()
    fit = PB.fit_relations(X, M, NAMES)
    x, m = _one_cycle()
    out = PB.inject_relational_break(x, m, fit, level_id="S6", onset_bin=12,
                                     duration_bins=3, lst_epsilon=0.5)
    # epsilon applies to the injected window only; the rest of the series is
    # untouched, so the anomaly cannot be found by a global offset
    np.testing.assert_allclose(out.x[12:15, 7], x[12:15, 7] - 0.5, atol=1e-9)
    np.testing.assert_allclose(out.x[:12, 7], x[:12, 7])


def test_lst_epsilon_beyond_the_physical_bound_is_refused():
    X, M = _cycles()
    fit = PB.fit_relations(X, M, NAMES)
    x, m = _one_cycle()
    with pytest.raises(ValueError, match="lst_epsilon"):
        PB.inject_relational_break(x, m, fit, lst_epsilon=PB.LST_EPSILON_MAX_K + 0.1)


def test_swir_break_leaves_ndvi_fixed():
    X, M = _cycles()
    fit = PB.fit_relations(X, M, NAMES)
    x, m = _one_cycle()
    out = PB.inject_relational_break(x, m, fit, pair="swir1|ndvi", level_id="S2")
    np.testing.assert_allclose(out.x[:, 0], x[:, 0])
    assert not np.allclose(out.x[12:14, 5], x[12:14, 5])


def test_relational_level_ordering_matches_the_severity_table():
    assert [lv for lv, _ in PB.RELATIONAL_LEVELS] == ["S1", "S2", "S4", "S6"]
    assert [k for _, k in PB.RELATIONAL_LEVELS] == sorted(k for _, k in PB.RELATIONAL_LEVELS)


def test_relational_severity_is_measured_back_not_assumed():
    X, M = _cycles()
    fit = PB.fit_relations(X, M, NAMES)
    lo = PB.inject_relational_break(X[0], M[0], fit, level_id="S1")
    hi = PB.inject_relational_break(X[0], M[0], fit, level_id="S6")
    assert max(hi.meta["achieved_deviation_mad"]) > max(lo.meta["achieved_deviation_mad"])


def test_relational_applier_works_on_a_patch_tensor():
    X, M = _cycles()
    fit = PB.fit_relations(X, M, NAMES)
    x = np.repeat(X[0][:, :, None, None], 4, axis=2).repeat(4, axis=3)
    m = np.ones_like(x, dtype=bool)
    out = PB.inject_relational_break(x, m, fit, level_id="S4")
    assert out.x.shape == x.shape
    assert out.x.ndim == 4


def test_relational_mask_is_never_changed():
    X, M = _cycles()
    fit = PB.fit_relations(X, M, NAMES)
    x, m = _one_cycle()
    m = m.copy()
    m[5:9, 0] = False
    out = PB.inject_relational_break(x, m, fit, level_id="S4", onset_bin=5, duration_bins=4)
    np.testing.assert_array_equal(out.m, m)
    # unobserved NDVI is not modified
    np.testing.assert_allclose(out.x[5:9, 0][~m[5:9, 0]], x[5:9, 0][~m[5:9, 0]])


def test_relational_result_hash_record_is_stable():
    X, M = _cycles()
    fit = PB.fit_relations(X, M, NAMES)
    a = PB.inject_relational_break(X[0], M[0], fit, level_id="S4").to_hash_record()
    b = PB.inject_relational_break(X[0], M[0], fit, level_id="S4").to_hash_record()
    assert a == b
    assert "sha256" in a
    c = PB.inject_relational_break(X[0], M[0], fit, level_id="S6").to_hash_record()
    assert c["sha256"] != a["sha256"]


def test_relational_wording_never_says_stress():
    X, M = _cycles()
    fit = PB.fit_relations(X, M, NAMES)
    res = PB.inject_relational_break(X[0], M[0], fit)
    assert "not stress" in res.meta["wording"]
    assert "stress" not in res.pert_type
    assert set(res.to_hash_record()) >= {"pert_type", "pair", "severity_mad", "sha256"}
    # a shape warp keeps the same discipline
    shape = PB.warp_shape(X[0], M[0], kind="greenup_delay", amount=2)
    assert "not stress" in shape.meta["wording"]


# --- 1.3 shape warps -----------------------------------------------------
def test_greenup_delay_moves_the_rise_later():
    x, m = _one_cycle()
    out = PB.warp_shape(x, m, kind="greenup_delay", amount=4)
    a = PB._stage_anchors(x[:, 0], m[:, 0])
    b = PB._stage_anchors(out.x[:, 0], m[:, 0])
    assert b["peak"] >= a["peak"]


def test_warp_never_widens_the_mask():
    x, m = _one_cycle()
    m2 = m.copy()
    m2[:, 0] = False
    m2[10:14, 0] = True
    out = PB.warp_shape(x, m2, kind="greenup_delay", amount=2)
    # the mask is returned VERBATIM: a warp may never invent an observation
    np.testing.assert_array_equal(out.m, m2)
    assert out.meta["n_skipped_unobserved"] > 0      # and it says what it skipped


def test_growth_compression_shortens_the_rise():
    x, m = _one_cycle()
    a = PB._stage_anchors(x[:, 0], m[:, 0])
    out = PB.warp_shape(x, m, kind="growth_compression", amount=0.40)
    rec = out.meta
    assert rec["compression"] == 0.40
    assert rec["n_moved_bins"] > 0
    b = PB._stage_anchors(out.x[:, 0], out.m[:, 0])
    assert b["peak"] - b["greenup"] <= a["peak"] - a["greenup"]


def test_early_senescence_moves_the_decline_earlier():
    x, m = _one_cycle()
    out = PB.warp_shape(x, m, kind="early_senescence", amount=4)
    assert out.meta["shifts"] == 4


def test_warp_leaves_burn_in_bins_untouched():
    x, m = _one_cycle()
    out = PB.warp_shape(x, m, kind="early_senescence", amount=6)
    np.testing.assert_allclose(out.x[:2], x[:2])


def test_warp_rejects_an_unknown_kind_and_a_bad_compression():
    x, m = _one_cycle()
    with pytest.raises(ValueError, match="unknown shape kind"):
        PB.warp_shape(x, m, kind="flip", amount=1)
    with pytest.raises(ValueError, match="must be in"):
        PB.warp_shape(x, m, kind="growth_compression", amount=1.5)


def test_warp_family_table_is_the_frozen_ladder():
    tbl = PB.shape_family_table()
    kinds = [r["kind"] for r in tbl]
    assert kinds.count("greenup_delay") == 2
    assert kinds.count("growth_compression") == 2
    assert kinds.count("early_senescence") == 2
    assert {r["unit"] for r in tbl} == {"bins", "fraction"}


def test_warp_anchor_comes_from_the_cycle_not_a_template():
    x, m = _one_cycle()
    shifted = x.copy()
    shifted[:, 0] = np.roll(shifted[:, 0], 4)     # a different season shape
    a = PB._stage_anchors(x[:, 0], m[:, 0])
    b = PB._stage_anchors(shifted[:, 0], m[:, 0])
    assert a["peak"] != b["peak"]


def test_warp_records_the_covariate_consequence():
    x, m = _one_cycle()
    out = PB.warp_shape(x, m, kind="greenup_delay", amount=2)
    assert "regenerated" in out.meta["covariate_note"]


# --- 1.4 the gate file ---------------------------------------------------
def test_gate_opens_only_when_both_path_c_gates_fail():
    ok = PB.require_path_c_failure(
        {"gates": {"detection": {"verdict": "fail"}, "generalization": {"verdict": "fail"}}}
    )
    assert ok["open"] is True


@pytest.mark.parametrize("gates", [
    {"gates": {"detection": {"verdict": "pass"}, "generalization": {"verdict": "fail"}}},
    {"gates": {"detection": {"verdict": "fail"}, "generalization": {"verdict": "pass"}}},
])
def test_gate_refuses_when_either_gate_passed(gates):
    with pytest.raises(PB.PathCGateClosedError, match="do not both fail"):
        PB.require_path_c_failure(gates)


def test_gate_refuses_a_missing_or_empty_record():
    with pytest.raises(PB.PathCGateClosedError, match="no gate file content"):
        PB.require_path_c_failure({})
    with pytest.raises(PB.PathCGateClosedError, match="not recorded"):
        PB.require_path_c_failure({"gates": {"detection": {"verdict": "fail"}}})
    with pytest.raises(PB.PathCGateClosedError, match="only 'pass'/'fail'"):
        PB.require_path_c_failure(
            {"gates": {"detection": {"verdict": ""},
                       "generalization": {"verdict": "fail"}}}
        )


def test_gate_file_roundtrip(tmp_path):
    path = tmp_path / "gates.json"
    PB.write_gates(str(path), detection="fail", generalization="fail",
                   recorded_by="owner", date="2026-11-16")
    payload = json.loads(path.read_text())
    assert payload["gates"]["detection"]["verdict"] == "fail"
    assert PB.require_path_c_failure(PB.load_gates(str(path)))["open"] is True


def test_gate_file_refuses_an_unknown_verdict(tmp_path):
    with pytest.raises(ValueError, match="pass"):
        PB.write_gates(str(tmp_path / "g.json"), detection="maybe", generalization="fail")


def test_absent_gate_file_blocks_by_default(tmp_path):
    with pytest.raises(PB.PathCGateClosedError, match="gate file not found"):
        PB.load_gates(str(tmp_path / "missing.json"))
