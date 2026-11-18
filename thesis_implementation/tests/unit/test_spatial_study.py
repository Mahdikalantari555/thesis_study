"""Spatial-representation study analysis (compare-spatial-representation).

Covers the pure, data-free half of finding 24: spatial arithmetic, the geometry
memo, equal-budget capacity flags, the PAIRED detectability crossing, chronicity
diagnostics, the static-pattern control, the noise-null gap and the one table.
"""

from __future__ import annotations

import numpy as np
import pytest

from ssl_anomaly.monitor import spatial_study as SS

S, T = 32, 36


# --- spatial arithmetic ---------------------------------------------------
def test_one_pixel_is_nine_hundred_square_metres():
    sup = SS.spatial_support(1)
    assert sup["min_resolvable_m2"] == 900.0
    assert sup["min_resolvable_ha"] == pytest.approx(0.09)


def test_sixteen_pixel_crop_is_about_23_hectares():
    sup = SS.spatial_support(16)
    assert sup["side_m"] == 480.0
    assert 22.5 < sup["area_ha"] < 23.5


def test_support_scales_quadratically():
    a = SS.spatial_support(16)["area_ha"]
    b = SS.spatial_support(32)["area_ha"]
    assert b == pytest.approx(4 * a, rel=1e-9)


def test_support_rejects_a_non_positive_window():
    with pytest.raises(ValueError, match="positive"):
        SS.spatial_support(0)


def test_geometry_memo_excludes_the_64_window_with_a_stated_reason():
    memo = SS.geometry_memo()
    assert memo["default_window_px"] == 32
    assert memo["excluded_window_px"] == 64
    assert memo["excluded_window_ratio_to_median_field"] > 3.0
    assert memo["default_window_margin_over_max_field"] > 0.5
    assert "explicit flag" in memo["decision"]


# --- equal budget ---------------------------------------------------------
def test_capacity_flag_uses_the_median_and_flags_outliers():
    out = SS.capacity_flag({"R1": 90_000, "R2": 92_000, "R3": 430_000})
    assert out["flags"]["R1"]["flagged"] is False
    assert out["flags"]["R3"]["flagged"] is True
    assert out["flags"]["R3"]["relative_deviation"] > 2.0


def test_capacity_flag_handles_parameterless_arms():
    out = SS.capacity_flag({"R0": 0, "R1": 90_000, "R2": 95_000})
    assert "R0" not in out["flags"]      # a rule-based arm has no params to flag


def test_capacity_flag_is_empty_without_params():
    assert SS.capacity_flag({"R0": 0})["reference"] is None


# --- paired crossing ------------------------------------------------------
def test_crossing_cells_sum_to_the_injection_count():
    p = np.array([1, 1, 1, 0, 0, 0, 1, 0], dtype=bool)
    z = np.array([1, 0, 0, 1, 0, 0, 1, 0], dtype=bool)
    out = SS.crossing_table({"S3": p}, {"S3": z})["S3"]
    total = out["patch_only"] + out["zonal_only"] + out["both"] + out["neither"]
    assert total == out["n"] == 8
    assert out["both"] == 2
    assert out["patch_only"] == 2
    assert out["zonal_only"] == 1


def test_crossing_refuses_misaligned_arrays():
    with pytest.raises(ValueError, match="paired"):
        SS.crossing_table({"S3": np.ones(5, bool)}, {"S3": np.ones(4, bool)})


def test_crossing_reports_wilson_cis():
    p = np.ones(10, bool)
    z = np.zeros(10, bool)
    out = SS.crossing_table({"S1": p}, {"S1": z})["S1"]
    lo, hi = out["patch_rate_ci95"]
    assert 0.0 <= lo <= out["patch_rate"] <= hi + 1e-9
    assert out["patch_rate"] == 1.0


def test_only_shared_levels_are_reported():
    out = SS.crossing_table(
        {"S1": np.ones(4, bool), "S2": np.ones(4, bool)},
        {"S1": np.ones(4, bool)},
    )
    assert set(out) == {"S1"}


def test_sign_test_is_exact_and_two_sided():
    assert SS.sign_test(0, 0)["p_value"] == 1.0
    assert SS.sign_test(5, 5)["p_value"] == 1.0
    # 9 vs 0 discordant: p = 2 * 2^-9
    assert SS.sign_test(9, 0)["p_value"] == pytest.approx(2 / 512, abs=1e-6)
    # a one-sided-looking 9:2 must NOT be significant at 0.05
    assert SS.sign_test(9, 2)["p_value"] > 0.05
    assert SS.sign_test(9, 2)["favours"] == "patch"


def test_sign_test_names_the_winner_only_when_there_is_one():
    assert SS.sign_test(3, 3)["favours"] is None


# --- chronicity -----------------------------------------------------------
def _clean_paths(n=4, spike=None, seed=0):
    g = np.random.default_rng(seed)
    p = g.random((n, T, S, S))
    infield = np.zeros((S, S), dtype=bool)
    infield[4:28, 4:28] = True
    if spike is not None:
        p[:, :, spike[0]:spike[1], spike[2]:spike[3]] = 50.0
    return p, infield


def test_chronic_pixels_are_identified_as_chronic():
    """A detector that flags the same pixels every cycle reports heterogeneity."""
    # the chronic patch must be the top-q set itself (top_q covers exactly it)
    paths, infield = _clean_paths(spike=(8, 16, 8, 16))
    area = 64 / float(infield.sum())
    diag = SS.alarm_frequency_diagnostic(paths, tau=10.0, in_field=infield, top_q=area)
    assert diag["mean_successive_topq_jaccard"] > 0.9      # same pixels, every cycle
    assert diag["mean_alarm_frequency"] > 0.02


def test_uncorrelated_alarms_have_low_successive_overlap():
    paths, infield = _clean_paths(seed=3)
    diag = SS.alarm_frequency_diagnostic(paths, tau=0.999, in_field=infield, top_q=0.1)
    assert diag["mean_successive_topq_jaccard"] < 0.5


def test_alarm_frequency_is_restricted_to_the_field():
    paths, infield = _clean_paths()
    paths[:, :, :4, :] = 1e6                 # huge values outside the field
    diag = SS.alarm_frequency_diagnostic(paths, tau=1.0, in_field=infield)
    assert diag["per_field"][0]["share_pixels_alarming_in_most_bins"] == 0.0


def test_entropy_is_zero_for_a_single_pixel():
    assert SS._entropy(np.array([5.0])) == 0.0
    assert SS._entropy(np.array([1.0, 1.0, 1.0, 1.0])) == pytest.approx(1.0)


def test_diagnostic_rejects_a_wrong_rank():
    with pytest.raises(ValueError, match="\\(N, T, S, S\\)"):
        SS.alarm_frequency_diagnostic(np.ones((T, S, S)), 1.0, np.ones((S, S), bool))


# --- static-pattern control ----------------------------------------------
def test_static_normalizer_absorbs_a_chronic_offset():
    """The control must make a stable chronic offset stop looking anomalous."""
    g = np.random.default_rng(0)
    base = np.zeros((6, T, S, S))
    base += g.normal(0, 0.05, base.shape)
    base[:, :, 10:20, 10:20] += 0.6          # a chronic bright patch
    norm = SS.static_pattern_normalizer(base, floor_quantile=5.0)
    scores = SS.static_pattern_scores(base[0], norm)
    inside = np.nanmean(scores[10:20, 10:20])
    outside = np.nanmean(scores[4:8, 4:8])
    assert inside < 3.0                      # no longer anomalous
    assert abs(inside - outside) < 3.0


def test_static_normalizer_floors_the_scale():
    flat = np.zeros((4, T, S, S))            # a perfectly quiet field
    norm = SS.static_pattern_normalizer(flat)
    assert np.all(norm["scale"] > 0)
    assert np.isfinite(SS.static_pattern_scores(flat[0], norm)).all()


def test_static_scores_are_nan_only_where_input_is_nan():
    g = np.random.default_rng(1)
    v = g.normal(size=(T, S, S))
    v[0, 0, 0] = np.nan
    norm = SS.static_pattern_normalizer(np.stack([v, v]))
    out = SS.static_pattern_scores(v, norm)
    assert np.isnan(out[0, 0, 0])
    assert np.isfinite(out[1:, :, :]).all()


def test_static_normalizer_rejects_a_wrong_rank():
    with pytest.raises(ValueError, match="\\(N, T, S, S\\)"):
        SS.static_pattern_normalizer(np.zeros((T, S, S)))


# --- noise null -----------------------------------------------------------
def test_noise_null_gap_favours_coherence():
    out = SS.noise_null_gap(2.0, 4.0)
    assert out["favours_coherence"] is True
    assert out["gap"] == 2.0


def test_noise_null_is_never_gate_eligible():
    out = SS.noise_null_gap(4.0, 2.0)
    assert out["gate_eligible"] is False
    assert out["diagnostic_only"] is True
    assert out["favours_coherence"] is False


# --- the one table --------------------------------------------------------
def _rows():
    return [
        SS.ComparisonRow("R0", "b1", "zonal_mean", "farm_local",
                         mdm80={"acute": "S5", "gradual": "S6"}, far_achieved=0.05,
                         confound="trained and calibrated on all 490 fields"),
        SS.ComparisonRow("R0.5", "r05_dist", "zonal_dist", "farm_local",
                         mdm80={"acute": "S4", "gradual": "S5"}, far_achieved=0.05),
        SS.ComparisonRow("R1", "patch_cnn_gru", "patch", "farm_local",
                         n_parameters=91_028, window_px=32,
                         mdm80={"acute": "S3", "gradual": "S4"},
                         localization_auprc=0.72, far_achieved=0.048,
                         epoch_seconds=12.3, peak_ram_mb=980, throughput_samples_s=3.4),
    ]


def test_table_has_every_dimension_and_the_support_column():
    md = SS.render_comparison_table(_rows(), shapes=("acute", "persistent", "gradual"))
    for token in ("MDM80 acute", "MDM80 gradual", "loc-AUPRC", "epoch s",
                  "peak MB", "samples/s", "support (ha / min)"):
        assert token in md
    assert "92.2 / 0.09" in md                       # 32 px support


def test_table_states_confounds_rather_than_leaving_them_to_the_reader():
    md = SS.render_comparison_table(_rows(), shapes=("acute", "gradual"))
    assert "all 490 fields" in md
    assert "—" in md


def test_table_carries_the_30m_interpretation_limit():
    md = SS.render_comparison_table(_rows(), shapes=("acute",))
    assert "30 m pixel bounds every localization claim" in md


def test_rule_based_row_has_no_parameter_claim():
    row = SS.ComparisonRow("R0", "b1", "zonal_mean", "farm_local")
    d = row.to_dict()
    assert d["spatial_support"] is None
    assert d["n_parameters"] is None


def test_capacity_flag_appears_in_the_table_when_triggered():
    rows = _rows() + [
        SS.ComparisonRow("R3", "patch_ms", "multi_scale", "farm_local",
                         n_parameters=430_000, window_px=32),
    ]
    md = SS.render_comparison_table(rows, shapes=("acute",))
    assert "Capacity flag" in md
    assert "R3" in md


def test_missing_mdm_cells_render_as_an_explicit_dash():
    md = SS.render_comparison_table(_rows(), shapes=("acute", "gradual"))
    row = [ln for ln in md.splitlines() if ln.startswith("| R0 ")]
    assert row
    assert "—" in row[0]


def test_representations_are_the_declared_ladder():
    assert SS.REPRESENTATIONS == ("R0", "R0.5", "R1", "R2", "R3")
