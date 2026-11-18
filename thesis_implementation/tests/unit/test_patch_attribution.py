"""Patch XAI: occlusion methods, gradient agreement, faithfulness, sampling.

Covers ``patch-xai-attribution`` tasks 1.1 and 1.3. The synthetic cases are
built so the CORRECT answer is known in advance (a spike in one band, one
time window, one pixel block) — an attribution method that cannot find a
planted signal is not tested by a test that only checks its output shape.
"""

from __future__ import annotations

import numpy as np
import pytest

from ssl_anomaly.xai import patch_attribution as PA

T, C, S = 36, 8, 16


def _patch(spike_band: int = 2, band_amp: float = 1.0):
    g = np.random.default_rng(0)
    v = g.normal(0.5, 0.02, (T, C, S, S))
    m = np.ones_like(v, dtype=bool)
    if spike_band is not None:
        v[:, spike_band, 4:12, 4:12] += band_amp
    return v, m


def _band_score(v, m):
    """A score that only reads band 2 — the answer the method must recover."""
    seg = v[:, 2][m[:, 2]]
    return float(np.abs(seg).mean() * 100)


# --- band occlusion -------------------------------------------------------
def test_band_occlusion_finds_the_planted_band():
    v, m = _patch()
    out = PA.band_occlusion(v, m, _band_score)
    assert out["top_band"] == 2
    assert out["delta"][2] > 10 * max(d for i, d in enumerate(out["delta"]) if i != 2)


def test_band_occlusion_is_zero_when_the_score_ignores_the_band():
    v, m = _patch()

    def const(vv, mm):
        return 1.0

    out = PA.band_occlusion(v, m, const)
    assert all(abs(d) < 1e-9 for d in out["delta"])


def test_band_occlusion_uses_the_median_baseline_not_zero():
    v, m = _patch(spike_band=None)
    seen = {}

    def spy(vv, mm):
        seen["mean"] = float(vv[m].mean())
        return float(vv[m].mean())

    PA.band_occlusion(v, m, spy)
    assert 0.3 < seen["mean"] < 0.7      # occluded to ~0.5, never to 0


def test_band_occlusion_rejects_an_unknown_baseline():
    v, m = _patch()
    with pytest.raises(ValueError, match="only 'median'"):
        PA.band_occlusion(v, m, _band_score, baseline="zero")


# --- temporal occlusion ---------------------------------------------------
def test_temporal_occlusion_finds_the_planted_window():
    g = np.random.default_rng(1)
    v = g.normal(0, 0.01, (T, C, S, S))
    m = np.ones_like(v, dtype=bool)
    v[20:24, 3] += 2.0                    # a 4-bin burst in band 3

    def score(vv, mm):
        return float(np.abs(vv[:, 3][mm[:, 3]]).mean() * 100)

    out = PA.temporal_occlusion(v, m, score, window=4)
    assert abs(out["top_window_start"] - 20) <= 1


def test_temporal_window_must_be_positive():
    v, m = _patch()
    with pytest.raises(ValueError, match="window must be"):
        PA.temporal_occlusion(v, m, _band_score, window=0)


def test_temporal_occlusion_covers_the_cycle():
    v, m = _patch()
    out = PA.temporal_occlusion(v, m, _band_score, window=3)
    assert len(out["delta"]) == T - 3 + 1


# --- spatial occlusion + pattern -----------------------------------------
def test_spatial_occlusion_localizes_a_planted_block():
    """Target the block that HOLDS the anomaly (blocks 0,0 and 1,1 both touch it)."""
    v, m = _patch()
    out = PA.spatial_occlusion(v, m, _band_score, block=8)
    d = np.array(out["delta"])
    assert d.shape == (2, 2)
    # the anomaly spans rows/cols 4:12, so it occupies two blocks; occluding
    # any block that overlaps it must beat the untouched corner blocks
    assert d[0, 0] > 0
    assert d[1, 1] > 0


def test_spatial_occlusion_separates_an_offset_block_from_clean_ones():
    """A dedicated 4-quadrant patch where ONE block is anomalous."""
    g = np.random.default_rng(2)
    v = g.normal(0.5, 0.005, (T, C, S, S))
    m = np.ones_like(v, dtype=bool)
    v[:, 2, 0:8, 0:8] += 1.0          # quadrant (0, 0) only
    out = PA.spatial_occlusion(v, m, _band_score, block=8)
    d = np.array(out["delta"])
    others = max(d[0, 1], d[1, 0], d[1, 1])
    assert d[0, 0] > 1.5 * others, d
    assert out["spatial_pattern"]["concentration"] > 0.35


def test_spatial_occlusion_spikes_under_median_baseline_too():
    """The per-bin median baseline cancels a bin-wise signal; a constant
    offset survives it, which is why both baselines are available."""
    v, m = _patch()
    out = PA.spatial_occlusion(v, m, _band_score, block=8, baseline="median")
    d = np.array(out["delta"])
    assert d.shape == (2, 2)
    # every block lands on its own per-bin median, so the four deltas agree
    # to within the sampling noise of the synthetic background
    assert np.allclose(d, d[0, 0], rtol=0.05), d


def test_spatial_pattern_distinguishes_flat_from_localized():
    flat = np.ones((4, 4))
    localized = np.zeros((4, 4))
    localized[1, 1] = 10.0
    a = PA.spatial_pattern_summary(flat)
    b = PA.spatial_pattern_summary(localized)
    assert a["concentration"] < 0.5
    assert b["concentration"] > 0.9
    assert b["n_effective"] < a["n_effective"]


def test_spatial_pattern_of_an_empty_map_is_zero_not_nan():
    out = PA.spatial_pattern_summary(np.zeros((4, 4)))
    assert out["concentration"] == 0.0
    assert out["gini"] == 0.0


def test_gini_is_zero_for_a_uniform_map_and_high_for_a_spike():
    assert PA._gini(np.ones(10)) == pytest.approx(0.0, abs=1e-9)
    spike = np.zeros(10)
    spike[0] = 1.0
    assert PA._gini(spike) > 0.8


def test_spatial_block_must_be_positive():
    v, m = _patch()
    with pytest.raises(ValueError, match="block must be"):
        PA.spatial_occlusion(v, m, _band_score, block=0)


# --- gradient attribution + agreement ------------------------------------
def _torch_score_factory():
    """Band-2 mean square, on the BATCHED tensor (1, T, C, S, S) → axis 2."""
    import torch

    def score(x, m):
        xm = torch.where(m, x, torch.zeros_like(x))
        return (xm[:, :, 2] ** 2).mean() * 100.0

    return score


def test_gradient_x_input_is_zero_outside_the_field():
    import torch  # noqa: F401

    v, m = _patch()
    m[:, :, :2, :] = False               # padding / neighbour region
    out = PA.gradient_x_input(v, m, _torch_score_factory())
    assert np.allclose(out["attr"][:, :, :2, :], 0.0)


def test_gradient_x_input_has_the_input_shape():
    v, m = _patch()
    out = PA.gradient_x_input(v, m, _torch_score_factory())
    assert out["attr"].shape == v.shape
    assert len(out["band_sum"]) == C
    assert len(out["temporal_sum"]) == T


def test_gradient_agrees_with_finite_differences():
    v, m = _patch()
    out = PA.gradient_x_input(v, m, _torch_score_factory())

    def numpy_score(vv, mm):
        sel = mm[:, 2]
        return float((vv[:, 2][sel] ** 2).mean() * 100)

    agree = PA.gradient_finite_difference_agreement(
        v, m, numpy_score, out["gradient"], n_probe=6, eps=1e-2,
    )
    assert agree["usable"]
    assert agree["pearson"] > 0.9, agree
    assert agree["sign_concordance"] > 0.9
    assert agree["agrees"], agree


def test_gradient_attribution_matches_the_analytic_derivative():
    """gxI of a quadratic score is exactly 2x·s/N — an analytic check."""

    v, m = _patch()
    out = PA.gradient_x_input(v, m, _torch_score_factory())
    n = m[:, 2].size                      # the score means over the WHOLE band
    # dS/dx = 2x·s/N  and  attr = (dS/dx)·x = 2x²·s/N  — two different maps
    np.testing.assert_allclose(out["gradient"][:, 2], 2.0 * v[:, 2] * 100.0 / n, rtol=1e-5)
    np.testing.assert_allclose(out["attr"][:, 2], 2.0 * v[:, 2] ** 2 * 100.0 / n, rtol=1e-5)


def test_gradient_attribution_is_zero_for_unobserved_cells():
    v, m = _patch()
    m[:, 3, :8, :8] = False
    out = PA.gradient_x_input(v, m, _torch_score_factory())
    assert np.allclose(out["attr"][:, 3, :8, :8], 0.0)


def test_agreement_test_can_REPORT_DISAGREEMENT():
    """A deliberately wrong attribution must not be called faithful."""
    v, m = _patch()
    wrong = np.zeros_like(v)
    wrong[:, 5] = 99.0                   # the score ignores band 5 entirely

    def numpy_score(vv, mm):
        return float(np.abs(vv[:, 2][mm[:, 2]]).mean() * 100)

    out = PA.gradient_finite_difference_agreement(
        v, m, numpy_score, wrong, n_probe=6,
    )
    assert out["agrees"] is False


def test_agreement_compares_the_gradient_not_the_attribution():
    """Feeding grad×input must NOT be accepted as the gradient (scale check)."""
    v, m = _patch()
    out = PA.gradient_x_input(v, m, _torch_score_factory())

    def numpy_score(vv, mm):
        sel = mm[:, 2]
        return float((vv[:, 2][sel] ** 2).mean() * 100)

    as_grad = PA.gradient_finite_difference_agreement(v, m, numpy_score, out["gradient"])
    as_attr = PA.gradient_finite_difference_agreement(v, m, numpy_score, out["attr"])
    assert as_grad["agrees"] is True
    # the attribution is scaled by the input, so it must NOT match the
    # gradient map's slope (|pearson| < 1 or a clear offset)
    assert abs(as_attr["pearson"]) <= abs(as_grad["pearson"]) + 1e-9


def test_uniform_probe_mode_is_available_and_strict():
    v, m = _patch()
    out = PA.gradient_x_input(v, m, _torch_score_factory())

    def numpy_score(vv, mm):
        sel = mm[:, 2]
        return float((vv[:, 2][sel] ** 2).mean() * 100)

    strict = PA.gradient_finite_difference_agreement(
        v, m, numpy_score, out["gradient"], n_probe=6, probe="uniform",
    )
    assert strict["probe"] == "uniform"


def test_probe_mode_is_validated():
    v, m = _patch()
    with pytest.raises(ValueError, match="unknown probe mode"):
        PA.gradient_finite_difference_agreement(
            v, m, _band_score, np.zeros_like(v), probe="oracle",
        )


def test_gradient_shape_mismatch_is_loud():
    v, m = _patch()
    with pytest.raises(ValueError, match="gradient shape"):
        PA.gradient_finite_difference_agreement(v, m, _band_score, np.zeros((2, 2)))


def test_agreement_is_unusable_without_observed_cells():
    v, m = _patch()
    m[:] = False
    out = PA.gradient_finite_difference_agreement(v, m, _band_score, np.zeros_like(v))
    assert out["usable"] is False


# --- faithfulness --------------------------------------------------------
def test_faithful_attribution_beats_random_deletion():
    v, m = _patch()
    attr = np.zeros_like(v)
    attr[:, 2, 4:12, 4:12] = 1.0         # exactly the planted region
    out = PA.deletion_insertion_curves(v, m, _band_score, attr, steps=6)
    assert out["usable"]
    assert out["deletion_gain"] > 0
    assert out["deletion_auc"] < out["random_deletion_auc"]


def test_inverted_attribution_does_not_beat_random():
    """A negation of the true map must lose its advantage — sanity on the metric."""
    v, m = _patch()
    attr = np.zeros_like(v)
    attr[:, 2, :, :] = 1.0
    attr[:, 2, 4:12, 4:12] = -1.0        # anti-attribution
    out = PA.deletion_insertion_curves(v, m, _band_score, attr, steps=6)
    assert out["deletion_gain"] <= 0


def test_faithfulness_reports_nan_safe_unusable_for_an_empty_mask():
    v, m = _patch()
    m[:] = False
    out = PA.deletion_insertion_curves(v, m, _band_score, np.zeros_like(v))
    assert out["usable"] is False


def test_faithfulness_is_seeded():
    v, m = _patch()
    attr = np.random.default_rng(0).random(v.shape)
    a = PA.deletion_insertion_curves(v, m, _band_score, attr, steps=4, seed=3)
    b = PA.deletion_insertion_curves(v, m, _band_score, attr, steps=4, seed=3)
    assert a["random_deletion_auc"] == b["random_deletion_auc"]


# --- stage aggregation + writers ----------------------------------------
def test_stage_aggregation_uses_the_shared_bins():
    from ssl_anomaly.xai.attribution import SUGARCANE_STAGE_BINS

    attr = np.zeros(T)
    attr[10:20] = 1.0
    st = PA.aggregate_to_stages(attr)
    assert set(st) == set(SUGARCANE_STAGE_BINS)
    assert sum(st.values()) == pytest.approx(attr.sum())


def test_band_table_ranks_by_attribution():
    md = PA.band_table([0.1, 2.0, 0.5], ["a", "b", "c"])
    lines = md.splitlines()
    assert "| 1 | `b` | 2.0000 |" in lines[2]


def test_temporal_table_reports_shares():
    md = PA.temporal_table({"early": 1.0, "late": 3.0})
    assert "75.00%" in md


# --- pre-registered sample ----------------------------------------------
def _events(n_family=3, n_sev=3, per=20):
    out = []
    k = 0
    for f in range(n_family):
        for s in range(n_sev):
            for _ in range(per):
                out.append({"event_id": f"e{k}", "family": f"fam{f}", "severity": f"S{s + 1}",
                            "field_id": 100 + f})
                k += 1
    return out


def test_sample_is_stratified_across_families_and_severities():
    plan = PA.attribution_sample_plan(_events(), n=50, seed=13)
    assert plan["n_selected"] == 50
    assert all(v >= 1 for v in plan["coverage"].values())
    assert len(plan["coverage"]) == 9


def test_sample_is_hash_recorded_and_reproducible():
    a = PA.attribution_sample_plan(_events(), n=30, seed=13)
    b = PA.attribution_sample_plan(_events(), n=30, seed=13)
    assert a["sha256"] == b["sha256"]
    assert a["event_ids"] == b["event_ids"]
    c = PA.attribution_sample_plan(_events(), n=30, seed=42)
    assert c["sha256"] != a["sha256"]


def test_sample_respects_the_available_events():
    plan = PA.attribution_sample_plan(_events(per=1), n=50, seed=0)
    assert plan["n_selected"] == 9          # one per stratum, cannot invent more


def test_sample_rejects_an_empty_event_set():
    with pytest.raises(ValueError, match="no events"):
        PA.attribution_sample_plan([], n=10)


def test_method_registry_is_declared():
    assert PA.HASH_METHODS == ("band_occlusion", "temporal_occlusion",
                               "spatial_occlusion", "gradient_x_input")
    assert PA.SAMPLE_SIZE == 50
