"""Contamination machinery + A_patch (patch-contamination-absorption task 1.1).

The machinary is data-free: selection, the physical injection, the absorption
statistic, its bootstrap CI, curation, and the config axes that keep a resumed
run honest.
"""

from __future__ import annotations

import numpy as np
import pytest

from ssl_anomaly.monitor.perturbations import CH_NDVI
from ssl_anomaly.train import contamination as C

T, CH = 36, 8


def _cycles(n=20, seed=0):
    g = np.random.default_rng(seed)
    X = np.full((n, T, CH), 0.70, dtype=np.float64)
    X[:, :, 3] = 0.15
    X[:, :, 4] = 0.55
    X += g.normal(0, 0.01, X.shape)
    M = np.ones((n, T, CH), dtype=bool)
    return X, M


# --- selection ------------------------------------------------------------
def test_fraction_is_exact_and_seed_fixed():
    keys = [f"{100 + i}:c{j}" for i in range(4) for j in range(25)]
    a = C.select_contaminated_cycles(keys, fraction=0.10, seed=13)
    b = C.select_contaminated_cycles(keys, fraction=0.10, seed=13)
    assert a == b
    assert len(a) == 10
    assert len(set(a)) == 10


def test_a_different_seed_selects_different_cycles():
    keys = [f"1:c{j}" for j in range(100)]
    a = C.select_contaminated_cycles(keys, fraction=0.1, seed=13)
    b = C.select_contaminated_cycles(keys, fraction=0.1, seed=42)
    assert a != b


def test_holdout_fields_are_never_selected():
    keys = [f"{f}:c{j}" for f in range(1, 6) for j in range(20)]
    sel = C.select_contaminated_cycles(keys, fraction=0.2, seed=0, excluded_fields={1, 2})
    assert sel, "expected a non-empty selection"
    assert all(C._field_of(k) not in (1, 2) for k in sel)


def test_excluding_everything_is_a_loud_error_not_silent_nothing():
    keys = [f"1:c{j}" for j in range(20)]
    with pytest.raises(ValueError, match="only 0 are eligible"):
        C.select_contaminated_cycles(keys, fraction=0.1, seed=0, excluded_fields={1})


def test_zero_fraction_selects_nothing():
    keys = [f"1:c{j}" for j in range(20)]
    assert C.select_contaminated_cycles(keys, fraction=0.0, seed=0) == []


def test_bad_fraction_is_rejected():
    with pytest.raises(ValueError, match="in \\[0, 1\\]"):
        C.select_contaminated_cycles(["1:c0"], fraction=1.5, seed=0)


# --- injection ------------------------------------------------------------
def test_contamination_applies_the_frozen_s4_profile():
    X, M = _cycles()
    out, m_out, meta = C.contaminate_dataset(X, M, [3, 7], rng=np.random.default_rng(0))
    assert len(meta) == 2
    for rec in meta:
        b = rec["row"]
        onset = rec["onset_bin"]
        # delta inside the persistent window, zero outside it
        drop = X[b, onset:onset + rec["n_bins_window"], CH_NDVI] - \
            out[b, onset:onset + rec["n_bins_window"], CH_NDVI]
        assert np.allclose(drop, rec["delta"], atol=0.02)
        assert np.allclose(out[b, :onset, CH_NDVI], X[b, :onset, CH_NDVI])
    # untouched rows are byte-identical
    np.testing.assert_array_equal(out[0], X[0])
    np.testing.assert_array_equal(m_out, M)


def test_contamination_never_moves_the_mask():
    X, M = _cycles()
    M[:, 4, :] = False
    _out, m_out, _meta = C.contaminate_dataset(X, M, [1], rng=np.random.default_rng(1))
    np.testing.assert_array_equal(m_out, M)


def test_contamination_leaves_unobserved_bins_alone():
    X, M = _cycles()
    M[2, 10:16, CH_NDVI] = False
    out, _m, meta = C.contaminate_dataset(X, M, [2], rng=np.random.default_rng(0))
    onset = meta[0]["onset_bin"]
    for b in range(10, 16):
        if b >= onset:
            assert out[2, b, CH_NDVI] == pytest.approx(X[2, b, CH_NDVI])


def test_selection_and_injection_are_reproducible_together():
    X, M = _cycles()
    keys = [f"1:c{j}" for j in range(len(X))]
    s1 = C.select_contaminated_cycles(keys, fraction=0.15, seed=7)
    s2 = C.select_contaminated_cycles(keys, fraction=0.15, seed=7)
    idx1 = [int(k.split(":")[1][1:]) for k in s1]
    idx2 = [int(k.split(":")[1][1:]) for k in s2]
    a, _, meta_a = C.contaminate_dataset(X, M, idx1, rng=np.random.default_rng(1))
    b, _, meta_b = C.contaminate_dataset(X, M, idx2, rng=np.random.default_rng(1))
    np.testing.assert_array_equal(a, b)
    assert meta_a == meta_b


# --- A_patch --------------------------------------------------------------
def _a_case(factor: float) -> dict:
    """A synthetic cycle where the model passes ``factor`` of the injection."""
    X, M = _cycles(n=1)
    x_clean = X[0]
    x_cont = x_clean.copy()
    x_cont[14:, CH_NDVI] -= 0.16
    pred_clean = x_clean.copy()
    pred_cont = pred_clean.copy()
    pred_cont[14:, CH_NDVI] -= 0.16 * factor
    return C.absorption_a(pred_clean, pred_cont, x_clean, x_cont, M[0], onset=14)


def test_a_patch_is_one_when_the_anomaly_is_fully_passed_through():
    out = _a_case(1.0)
    assert out["usable"]
    assert out["a_patch"] == pytest.approx(1.0, abs=1e-6)
    assert out["share_absorbed"] == pytest.approx(0.0, abs=1e-6)


def test_a_patch_is_zero_when_the_model_absorbs_the_anomaly():
    out = _a_case(0.0)
    assert out["a_patch"] == pytest.approx(0.0, abs=1e-9)
    assert out["share_absorbed"] == pytest.approx(1.0, abs=1e-9)


def test_a_patch_is_linear_in_the_passed_share():
    for f in (0.25, 0.5, 0.75):
        assert _a_case(f)["a_patch"] == pytest.approx(f, abs=1e-6)


def test_pre_onset_bins_do_not_enter_the_statistic():
    X, M = _cycles(n=1)
    x_clean = X[0]
    x_cont = x_clean.copy()
    x_cont[14:, CH_NDVI] -= 0.16
    pred_clean = x_clean.copy()
    pred_cont = pred_clean.copy()
    pred_cont[14:, CH_NDVI] -= 0.08
    pred_cont[:14, CH_NDVI] += 99.0        # garbage before the onset
    out = C.absorption_a(pred_clean, pred_cont, x_clean, x_cont, M[0], onset=14)
    assert out["a_patch"] == pytest.approx(0.5, abs=1e-6)


def test_unobserved_bins_are_excluded():
    X, M = _cycles(n=1)
    x_clean = X[0]
    x_cont = x_clean.copy()
    x_cont[14:, CH_NDVI] -= 0.16
    pred_clean = x_clean.copy()
    pred_cont = pred_clean.copy()
    pred_cont[14:, CH_NDVI] -= 0.08
    M[0, 20:30, CH_NDVI] = False           # those bins carry no evidence
    out = C.absorption_a(pred_clean, pred_cont, x_clean, x_cont, M[0], onset=14)
    assert out["usable"]
    assert out["n_bins"] == 36 - 14 - 10
    assert out["a_patch"] == pytest.approx(0.5, abs=1e-6)


def test_no_injected_shift_is_reported_as_unusable_not_as_nan_math():
    X, M = _cycles(n=1)
    out = C.absorption_a(X[0], X[0], X[0], X[0], M[0], onset=14)
    assert out["usable"] is False
    assert "no observed post-onset bin" in out["reason"]


# --- bootstrap ------------------------------------------------------------
def test_bootstrap_ci_brackets_the_mean():
    vals = [0.4, 0.45, 0.5, 0.55, 0.6] * 6
    out = C.absorption_bootstrap(vals, n_boot=500, seed=0)
    lo, hi = out["ci95"]
    assert lo < out["mean"] < hi
    assert out["n_cycles"] == 30


def test_bootstrap_is_seeded():
    vals = list(np.random.default_rng(0).random(40))
    a = C.absorption_bootstrap(vals, n_boot=200, seed=3)
    b = C.absorption_bootstrap(vals, n_boot=200, seed=3)
    assert a["ci95"] == b["ci95"]


def test_bootstrap_reports_whether_the_ci_excludes_zero():
    positive = C.absorption_bootstrap([0.9, 0.92, 0.88, 0.91] * 5, n_boot=300, seed=0)
    assert positive["excludes_zero"] is True
    straddling = C.absorption_bootstrap([-0.5, 0.5] * 10, n_boot=300, seed=0)
    assert straddling["excludes_zero"] is False


def test_bootstrap_handles_no_cycles_and_one_cycle():
    assert C.absorption_bootstrap([])["n_cycles"] == 0
    one = C.absorption_bootstrap([0.5])
    assert one["mean"] == 0.5
    assert one["n_cycles"] == 1


# --- curation -------------------------------------------------------------
def test_curation_removes_the_two_percent_worst():
    scores = np.arange(100, dtype=float)
    sel = C.curation_select(scores, top_frac=0.02)
    assert len(sel.removed) == 2
    assert sel.removed == [98, 99]
    assert len(sel.keep) == 98
    assert sel.threshold == 98.0


def test_curation_is_deterministic_with_ties():
    scores = np.ones(50)
    a = C.curation_select(scores, top_frac=0.1)
    b = C.curation_select(scores, top_frac=0.1)
    assert a.removed == b.removed
    # ties are broken by ascending row index — deterministic, documented
    assert a.removed == list(range(5))


def test_curation_of_an_empty_set_is_empty():
    sel = C.curation_select(np.array([]))
    assert sel.keep == []
    assert sel.removed == []


def test_curation_removed_ids_are_in_the_manifest_payload():
    sel = C.curation_select(np.arange(10.0), top_frac=0.2)
    payload = sel.to_dict()
    assert payload["removed_ids"] == [8, 9]
    assert payload["n_keep"] == 8


# --- config axes ----------------------------------------------------------
def test_contamination_axes_are_declared_for_the_config_hash():
    cfg = C.contamination_config(0.05, trimmed=True, curation=False)
    assert cfg == {"contaminate_fraction": 0.05, "trimmed_loss": True, "curation": False}
    assert cfg != C.contamination_config(0.10, trimmed=True, curation=False)


def test_the_preregistered_level_is_not_the_trivial_one():
    """S5/S6 are detected by every arm; S1–S3 are the undetectable floor."""
    assert C.CONTAMINATION_LEVEL == "S4"
    assert C.CONTAMINATION_FAMILY == "persistent"
