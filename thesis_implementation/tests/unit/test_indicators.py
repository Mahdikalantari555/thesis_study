"""Independent indicators: CWSI, both z units, availability, ERA5 context.

Covers ``patch-independent-indicators`` tasks 1.1–1.4. The recurring theme of
these tests is the ABSENT discipline: a missing input must never degrade into
a number that reads as "no stress".
"""

from __future__ import annotations

import numpy as np
import pytest

from ssl_anomaly.monitor import indicators as I


# --- 1.1 physical CWSI ---------------------------------------------------
def test_cwsi_is_one_at_the_dry_limit_and_zero_at_the_wet_limit():
    assert I.cwsi_idso_jackson(320.0, 300.0, wet_baseline=298.0, dry_baseline=320.0)["value"] == pytest.approx(1.0)
    assert I.cwsi_idso_jackson(298.0, 300.0, wet_baseline=298.0, dry_baseline=320.0)["value"] == pytest.approx(0.0)


def test_cwsi_midpoint_is_a_half():
    out = I.cwsi_idso_jackson(309.0, 300.0, wet_baseline=298.0, dry_baseline=320.0)
    assert out["value"] == pytest.approx(0.5)
    assert out["baseline_source"] == "measured"


def test_cwsi_clips_outside_the_envelope():
    out = I.cwsi_idso_jackson(340.0, 300.0, wet_baseline=298.0, dry_baseline=320.0)
    assert out["value"] == pytest.approx(1.0)
    assert out["clipped"] is True


def test_cwsi_is_absent_without_air_temperature():
    out = I.cwsi_idso_jackson(310.0, np.nan)
    assert out["value"] == I.ABSENT
    assert "air temperature" in out["reason"]


def test_cwsi_is_absent_without_canopy_temperature():
    assert I.cwsi_idso_jackson(np.nan, 300.0)["value"] == I.ABSENT


def test_cwsi_fallback_to_the_empirical_envelope_is_labelled():
    out = I.cwsi_idso_jackson(312.0, 300.0, vpd=2.0)
    assert out["value"] != I.ABSENT
    assert out["baseline_source"] == "idso_empirical_envelope"


def test_cwsi_fallback_needs_vpd():
    out = I.cwsi_idso_jackson(312.0, 300.0)
    assert out["value"] == I.ABSENT
    assert "VPD" in out["reason"]


def test_cwsi_coefficients_carry_their_sources():
    out = I.cwsi_idso_jackson(312.0, 300.0, vpd=2.0)
    for src in out["coefficient_sources"].values():
        assert "Idso" in src
    assert all("source" in v for v in I.CWSI_COEFFICIENTS.values())


def test_cwsi_missing_coefficients_is_absent():
    out = I.cwsi_idso_jackson(312.0, 300.0, vpd=2.0, coefficients={})
    assert out["value"] == I.ABSENT


def test_cwsi_handles_arrays_and_counts_absent_cells():
    tc = np.array([300.0, 310.0, np.nan])
    out = I.cwsi_idso_jackson(tc, 300.0, wet_baseline=298.0, dry_baseline=320.0)
    assert out["n_absent"] == 1
    assert out["n_valid"] == 2


# --- 1.2 both z units ----------------------------------------------------
def _series(seed=0, n=36):
    return np.random.default_rng(seed).normal(0.5, 0.05, n)


def test_across_field_z_is_population_referenced():
    own = _series()
    pop = np.random.default_rng(1).normal(0.5, 0.05, (40, 36))
    out = I.indicator_z(own, across_field=pop, unit="across_field")
    assert out.unit == "across_field"
    assert out.tier == "population"
    assert np.isfinite(out.values).all()


def test_across_field_z_labels_a_single_farm_as_an_outlier():
    pop = np.random.default_rng(1).normal(0.5, 0.01, (40, 36))
    own = np.full(36, 0.6)
    out = I.indicator_z(own, across_field=pop, unit="across_field")
    assert np.nanmax(out.values) > 5


def test_farm_own_z_uses_the_fields_own_history():
    hist = np.random.default_rng(2).normal(0.5, 0.01, 36)
    own = np.full(36, 0.6)                    # far from its OWN history
    out = I.indicator_z(own, pooled_history=hist, unit="farm_own")
    assert out.unit == "farm_own"
    assert out.tier in ("moderate", "rich")
    assert not out.fallback_used
    assert np.nanmin(out.values) > 5


def test_farm_own_falls_back_and_says_so_when_history_is_thin():
    hist = np.array([0.5, 0.51, np.nan, np.nan])
    out = I.indicator_z(np.full(36, 0.6), pooled_history=hist, unit="farm_own")
    assert out.fallback_used is True
    assert out.tier in ("none", "sparse")


def test_unit_must_be_declared():
    with pytest.raises(ValueError, match="unknown indicator z unit"):
        I.indicator_z(_series(), pooled_history=_series(), unit="vibes")


def test_across_field_unit_requires_the_population():
    with pytest.raises(ValueError, match=r"needs the \(N, T\) population"):
        I.indicator_z(_series(), unit="across_field")


def test_farm_own_unit_requires_history():
    with pytest.raises(ValueError, match="needs the field's own clean history"):
        I.indicator_z(_series(), unit="farm_own")


def test_mismatched_bin_counts_are_loud():
    with pytest.raises(ValueError, match="bins"):
        I.indicator_z(_series(n=36), across_field=np.ones((4, 10)), unit="across_field")


def test_indicator_z_dict_is_json_friendly():
    out = I.indicator_z(_series(), across_field=np.ones((4, 36)), unit="across_field")
    d = out.to_dict()
    assert d["unit"] == "across_field"
    assert len(d["values"]) == 36


# --- 1.3 availability ----------------------------------------------------
def test_availability_flags_an_indicator_below_the_usable_threshold():
    cov = {
        "cwsi_physical": {"n_total": 100, "n_present": 60},
        "tvdi": {"n_total": 100, "n_present": 4,
                 "absent_reasons": {"no_clear_sky_edges": 96}},
    }
    rep = I.availability_report(cov)
    assert "cwsi_physical" in rep["usable"]
    assert "tvdi" in rep["not_usable"]
    assert rep["indicators"]["tvdi"]["absent_reasons"]["no_clear_sky_edges"] == 96


def test_availability_marks_an_uncomputed_indicator_explicitly():
    rep = I.availability_report({})
    for name in I.INDICATORS:
        assert rep["indicators"][name]["present"] is False
    assert rep["usable"] == []


def test_availability_reports_zero_coverage_without_dividing_by_zero():
    rep = I.availability_report({"cwsi_et": {"n_total": 0, "n_present": 0}})
    assert rep["indicators"]["cwsi_et"]["coverage"] == 0.0
    assert rep["indicators"]["cwsi_et"]["usable_for_agreement"] is False


def test_availability_covers_every_declared_indicator():
    assert set(I.INDICATORS) == {"cwsi_et", "tvdi", "cwsi_physical", "eta_etrf"}
    rep = I.availability_report({n: {"n_total": 10, "n_present": 10} for n in I.INDICATORS})
    assert set(rep["usable"]) == set(I.INDICATORS)


# --- 1.4 ERA5 context + classification ----------------------------------
def test_context_reports_a_rainfall_deficit():
    event = {"precip": np.array([0.0, 0.0, 1.0]), "tmax": np.array([305.0] * 3)}
    hist = {"precip": np.array([4.0] * 30), "tmax": np.array([300.0] * 30)}
    ctx = I.era5_context(event, hist)
    # 30 historical days of 4 mm = ten 3-day windows of 12 mm; the event got 1
    assert ctx["context"]["precip_deficit_mm"]["reference_window_mean"] == pytest.approx(12.0)
    assert ctx["context"]["precip_deficit_mm"]["value"] == pytest.approx(11.0)
    assert ctx["context"]["tmax_anomaly_k"]["value"] == pytest.approx(5.0)


def test_context_marks_a_missing_variable_as_absent_not_zero():
    ctx = I.era5_context({"precip": np.array([0.0])}, {"precip": np.array([2.0])})
    assert ctx["context"]["tmax_anomaly_k"]["value"] == I.ABSENT
    assert "tmax_anomaly_k" in ctx["absent_variables"]


def test_reference_window_mean_falls_back_when_windows_do_not_tile():
    ref = np.array([1.0, 2.0, 3.0, 4.0])
    assert I._reference_window_mean(ref, 3) == pytest.approx(2.5 * 3)


def test_context_handles_et0_from_an_explicit_window():
    ctx = I.era5_context(
        {"precip": np.array([1.0]), "tmax": np.array([300.0])},
        {"precip": np.array([1.0]), "tmax": np.array([300.0]), "et0": np.array([4.0] * 5)},
        et0_window=np.array([6.0, 7.0]),
    )
    assert ctx["context"]["et0_anomaly_mm"]["value"] == pytest.approx(2.5)


def test_neighbor_share_counts_same_sign_and_half_magnitude():
    out = I.neighbor_deviation_share(-1.0, np.array([-0.9, -0.6, 0.5, -0.2]))
    assert out["share"] == pytest.approx(0.5)      # -0.9 and -0.6 qualify
    assert out["n_shared"] == 2


def test_neighbor_share_is_absent_without_neighbours():
    out = I.neighbor_deviation_share(-1.0, np.array([np.nan]))
    assert out["share"] == I.ABSENT


def test_regional_common_mode_is_named_as_weather():
    cls = I.alarm_classification({}, {"share": 0.9})
    assert cls["classification"] == "regional_common_mode"
    assert any("weather" in c for c in cls["candidate_causes"])


def test_local_consistent_needs_a_context_driver():
    ctx = I.era5_context(
        {"precip": np.array([0.0]), "tmax": np.array([308.0]),
         "vpd": np.array([3.5])},
        {"precip": np.array([5.0] * 20), "tmax": np.array([300.0] * 20),
         "vpd": np.array([2.0] * 20)},
    )
    cls = I.alarm_classification(ctx, {"share": 0.0})
    assert cls["classification"] == "local_consistent"
    assert cls["candidate_causes"]


def test_local_unexplained_when_no_driver_and_no_neighbours_agree():
    ctx = I.era5_context(
        {"precip": np.array([5.0]), "tmax": np.array([300.0])},
        {"precip": np.array([5.0] * 20), "tmax": np.array([300.0] * 20)},
    )
    cls = I.alarm_classification(ctx, {"share": 0.0})
    assert cls["classification"] == "local_unexplained"
    assert "pest/disease" in " ".join(cls["candidate_causes"])


def test_no_neighbour_data_never_becomes_a_local_claim():
    cls = I.alarm_classification({}, {"share": I.ABSENT})
    assert cls["classification"] == "local_unexplained"
    assert "cannot separate" in cls["reason"]


def test_et_etrf_is_absent_where_the_reference_is_missing():
    out = I.et_etrf(np.array([3.0, 3.0]), np.array([4.0, 0.0]))
    assert out["n_valid"] == 1
    assert out["n_absent"] == 1
    assert np.isnan(out["value"][1])


def test_et_etrf_shape_mismatch_is_loud():
    with pytest.raises(ValueError, match="shape mismatch"):
        I.et_etrf(np.array([1.0]), np.array([1.0, 2.0]))
