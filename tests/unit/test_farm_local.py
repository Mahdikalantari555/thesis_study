"""Farm-local scoring: basis registry, independence tests, σ table, summaries.

Covers ``farm-local-anomaly-scoring`` tasks 1.1, 1.2, 2.1, 2.3, 4.1 and 4.2.
Every independence test here is paired with the NEGATIVE CONTROL that proves
it can fail — an invariance test that has never failed is not evidence.
"""

from __future__ import annotations

import numpy as np
import pytest

from ssl_anomaly.monitor import farm_local as FL


# --- 1.1 basis registry ---------------------------------------------------
def test_every_eval_arm_has_a_declared_basis():
    """The registry must cover the arms eval_dev can name."""
    for arm in ("b0_calendar", "b1", "b3", "gru_ae_main", "gru_pred",
                "patch_cnn_gru", "patch_pixelwise",
                "r05_level", "r05_lower", "r05_spread", "r05_dist"):
        assert FL.basis_of(arm) in FL.BASIS_TIERS, arm


def test_undeclared_arm_fails_the_report_build():
    with pytest.raises(ValueError, match="no scoring-basis declaration"):
        FL.require_declarations(["b1", "some_new_arm"])


def test_population_ranked_components_are_declared_as_such():
    for comp in ("s_hyb", "z_f(t)", "common_mode", "indicator_z"):
        assert FL.basis_of(comp) == FL.BASIS_POPULATION_RANKED, comp
    for comp in ("s_pred", "s_rec", "s_lat"):
        assert FL.is_locally_anchored(comp), comp


def test_report_header_names_the_cross_farm_read():
    hdr = FL.report_header(["b1", "s_hyb"])
    assert hdr["has_population_ranked"] is True
    assert "percentile rank" in hdr["cross_farm_reads"]["s_hyb"]


def test_a_local_only_report_has_no_cross_farm_reads():
    hdr = FL.report_header(["b1", "patch_cnn_gru", "sigma_farmlocal"])
    assert hdr["has_population_ranked"] is False
    assert hdr["cross_farm_reads"] == {}


def test_strictly_local_tier_exists_for_the_farm_sigma_variant():
    assert FL.basis_of("sigma_farmlocal") == FL.BASIS_STRICTLY_LOCAL


# --- 1.2 independence tests WITH negative controls -----------------------
def _scorer(x):
    return np.array([float(np.mean(np.abs(x)))])


def test_other_farm_perturbation_invariance_passes_for_a_local_scorer():
    values = np.random.default_rng(0).normal(size=(36, 8))
    assert FL.other_farm_perturbation_is_invariant(values, scorer=_scorer) is True


def test_no_cross_field_read_passes_for_a_local_component():
    values = np.random.default_rng(0).normal(size=(36, 8))
    rec = FL.score_field_only(7, values, scorer=_scorer)
    assert FL.no_cross_field_read(rec, allowed_fields={7})


def test_no_cross_field_read_FAILS_for_the_planted_control():
    """The negative control: a population-ranked component must be caught."""
    own = np.random.default_rng(0).normal(size=(36, 8))
    others = np.random.default_rng(1).normal(size=(4, 36, 8))
    rec = FL.planted_population_ranked_component(own, others)
    assert not FL.no_cross_field_read(rec, allowed_fields={1}), (
        "the planted population-ranked component was NOT caught — the test is vacuous"
    )


def test_pooled_whitelist_is_enforced():
    values = np.random.default_rng(0).normal(size=(36, 8))
    rec = FL.score_field_only(1, values, scorer=_scorer, pooled_constants={"frozen_mad"})
    assert FL.no_cross_field_read(rec, allowed_fields={1}, pooled_whitelist={"frozen_mad"})
    assert not FL.no_cross_field_read(rec, allowed_fields={1}, pooled_whitelist=set())


def test_field_id_permutation_is_invariant_for_a_local_scorer():
    data = {f: np.random.default_rng(f).normal(size=(36, 8)) for f in (1, 2, 3)}

    def local(field_id, values):          # ignores the id entirely
        return np.array([float(np.mean(np.abs(values)))])

    assert FL.field_id_permutation_is_invariant(data, scorer=local) is True


def test_field_id_permutation_FAILS_for_a_field_id_dependent_scorer():
    """Negative control: a scorer that uses the field id must be caught."""
    data = {f: np.ones((4, 2)) for f in (1, 2, 3)}     # identical values everywhere

    def id_scorer(field_id, values):      # the ONLY input that differs is the id
        return np.array([float(field_id)])

    assert FL.field_id_permutation_is_invariant(data, scorer=id_scorer) is False


def test_unknown_basis_lookup_is_loud():
    with pytest.raises(KeyError, match="no declared scoring basis"):
        FL.basis_of("nope")


# --- 2.1 per-field sigma table -------------------------------------------
def _residuals(scales=(1.0, 3.0), n=200, seed=0):
    rng = np.random.default_rng(seed)
    return {i + 1: rng.normal(0, s, n) for i, s in enumerate(scales)}


def test_shrinkage_identity_zero_history_gives_the_pooled_scale():
    assert FL.shrink_weight(0) == 0.0
    table = FL.build_field_sigma_table({1: np.array([]), 2: _residuals()[2]}, basis="shrunk")
    assert float(table.sigma[1][0]) == pytest.approx(float(table.pooled[0]))


def test_shrinkage_weight_grows_with_history():
    assert FL.shrink_weight(0) < FL.shrink_weight(5) < FL.shrink_weight(1000)
    assert FL.shrink_weight(1000) > 0.98


def test_pooled_basis_is_identical_for_every_field():
    table = FL.build_field_sigma_table(_residuals(), basis="pooled")
    vals = {float(v[0]) for v in table.sigma.values()}
    assert len(vals) == 1


def test_farmlocal_basis_keeps_the_field_own_scale():
    table = FL.build_field_sigma_table(_residuals((1.0, 3.0)), basis="farmlocal")
    assert float(table.sigma[2][0]) > 2 * float(table.sigma[1][0])


def test_shrunk_basis_lies_between_own_and_pooled():
    res = _residuals((1.0, 3.0), n=50)
    pooled = FL.build_field_sigma_table(res, basis="pooled")
    own = FL.build_field_sigma_table(res, basis="farmlocal")
    shrunk = FL.build_field_sigma_table(res, basis="shrunk")
    lo = min(float(own.sigma[2][0]), float(pooled.sigma[2][0]))
    hi = max(float(own.sigma[2][0]), float(pooled.sigma[2][0]))
    assert lo <= float(shrunk.sigma[2][0]) <= hi


def test_floor_protects_an_implausibly_quiet_field():
    res = {1: np.zeros(100), 2: np.random.default_rng(0).normal(0, 1.0, 100)}
    table = FL.build_field_sigma_table(res, basis="farmlocal")
    assert float(table.sigma[1][0]) > 0
    assert float(table.sigma[1][0]) >= table.floor


def test_sigma_table_is_deterministic_and_hashed():
    a = FL.build_field_sigma_table(_residuals(), basis="shrunk")
    b = FL.build_field_sigma_table(_residuals(), basis="shrunk")
    assert a.sha256 == b.sha256
    c = FL.build_field_sigma_table(_residuals(scales=(1.0, 5.0)), basis="shrunk")
    assert c.sha256 != a.sha256


def test_history_tiers_are_reported():
    table = FL.build_field_sigma_table(_residuals(n=3) | {9: np.array([])}, basis="shrunk")
    assert table.tier[1] == "sparse"
    assert table.tier[9] == "none"


def test_unknown_basis_is_rejected():
    with pytest.raises(ValueError, match="unknown sigma basis"):
        FL.build_field_sigma_table(_residuals(), basis="magic")


def test_empty_input_is_loud():
    with pytest.raises(ValueError, match="no fields given"):
        FL.build_field_sigma_table({})


def test_provenance_round_trips_into_the_dict():
    table = FL.build_field_sigma_table(
        _residuals(), basis="shrunk",
        provenance={"run_id": "gru_ae_main_s13", "splits_sha256": "abc"},
    )
    d = table.to_dict()
    assert d["provenance"]["run_id"] == "gru_ae_main_s13"
    assert d["basis"] == "shrunk"
    assert len(d["sha256"]) == 64


def test_lookup_falls_back_to_pooled_for_an_unknown_field():
    table = FL.build_field_sigma_table(_residuals(), basis="farmlocal")
    np.testing.assert_array_equal(table.lookup(999), table.pooled)


# --- 4.1 alarm summary + components --------------------------------------
def test_connected_components_counts_separate_blobs():
    m = np.zeros((32, 32), dtype=bool)
    m[2:6, 2:6] = True       # 16 px
    m[20:23, 20:23] = True   # 9 px
    comps = FL.connected_components(m)
    assert len(comps) == 2
    assert sorted(c["n_pixels"] for c in comps) == [9, 16]


def test_components_are_four_connected_not_eight():
    m = np.zeros((8, 8), dtype=bool)
    m[1, 1] = m[2, 2] = True      # diagonal only
    assert len(FL.connected_components(m)) == 2


def test_component_area_uses_the_30m_arithmetic():
    m = np.zeros((32, 32), dtype=bool)
    m[0:10, 0:10] = True
    comp = FL.connected_components(m)[0]
    assert comp["area_ha"] == pytest.approx(100 * 0.09)
    assert comp["n_pixels"] == 100


def test_alarm_touching_two_fields_counts_two_components_not_one():
    """The spec's explicit test: components are computed WITHIN one field."""
    # one field's alarm map: two blobs at opposite corners of the polygon
    field_a = np.zeros((32, 32), dtype=bool)
    field_a[1:4, 1:4] = True
    field_a[28:31, 28:31] = True
    # a neighbouring field's alarm map, stored separately (as the caller must)
    field_b = np.zeros((32, 32), dtype=bool)
    field_b[5:8, 5:8] = True
    a = FL.alarm_summary_record(
        field_id=1, cycle="1:c0", first_alarm_bin=10, severity_level="S4",
        persistence_len=3, pixel_alarm_mask=field_a, score=2.0, basis_tier="shrunk",
    )
    b = FL.alarm_summary_record(
        field_id=2, cycle="2:c0", first_alarm_bin=10, severity_level="S4",
        persistence_len=3, pixel_alarm_mask=field_b, score=2.0, basis_tier="shrunk",
    )
    assert a["n_components"] == 2, "two blobs in ONE field must be two components"
    assert b["n_components"] == 1, "the neighbour is its own field, never merged"
    assert a["field_id"] != b["field_id"]


def test_alarm_summary_record_has_every_required_field():
    m = np.zeros((32, 32), dtype=bool)
    m[8:16, 8:16] = True
    rec = FL.alarm_summary_record(
        field_id=42, cycle="42:c3", first_alarm_bin=12, severity_level="S5",
        persistence_len=4, pixel_alarm_mask=m, score=3.5, basis_tier="shrunk",
        phi_bin=7,
    )
    for key in ("field_id", "cycle", "first_alarm_bin", "severity_level",
                "persistence_len", "affected_pixels", "affected_area_frac",
                "n_components", "max_component_px", "max_component_ha",
                "centroid_xy", "score", "basis_tier", "phi_bin"):
        assert key in rec, key
    assert rec["affected_area_frac"] == pytest.approx(64 / (32 * 32), abs=1e-4)


def test_area_fraction_is_relative_to_the_mask_domain():
    small = np.zeros((16, 16), dtype=bool)
    small[:8, :8] = True
    rec = FL.alarm_summary_record(
        field_id=1, cycle="1:c0", first_alarm_bin=1, severity_level="S1",
        persistence_len=1, pixel_alarm_mask=small, score=1.0, basis_tier="pooled",
    )
    assert rec["affected_area_frac"] == pytest.approx(0.25)


def test_empty_alarm_map_is_allowed_and_reports_zero():
    rec = FL.alarm_summary_record(
        field_id=1, cycle="1:c0", first_alarm_bin=-1, severity_level="none",
        persistence_len=0, pixel_alarm_mask=np.zeros((8, 8), bool), score=0.0,
        basis_tier="pooled",
    )
    assert rec["n_components"] == 0
    assert rec["affected_pixels"] == 0
    assert rec["centroid_xy"] is None


# --- 4.2 summary table ----------------------------------------------------
def test_summary_table_aggregates_by_severity_and_phenophase():
    m = np.zeros((10, 10), dtype=bool)
    m[:5, :5] = True
    recs = [
        FL.alarm_summary_record(field_id=i, cycle=f"{i}:c", first_alarm_bin=3,
                                severity_level="S4", persistence_len=2,
                                pixel_alarm_mask=m, score=2.0, basis_tier="shrunk",
                                phi_bin=phi)
        for i, phi in enumerate((1, 1, 2))
    ]
    table = FL.alarm_summary_table(recs)
    assert table["n_alarms"] == 3
    assert table["by_severity"]["S4"]["n"] == 3
    assert table["by_phi_bin"]["1"]["n"] == 2
    assert table["by_severity"]["S4"]["affected_area_frac_median"] == pytest.approx(0.25)


def test_empty_summary_table_is_explicit():
    out = FL.alarm_summary_table([])
    assert out["n_alarms"] == 0
    assert out["by_severity"] == {}


# --- 2.3 pre-registered adoption rule ------------------------------------
def test_adoption_rule_is_recorded_before_any_run():
    assert "pre-registered" in FL.ADOPTION_RULE["name"]
    assert len(FL.ADOPTION_RULE["criteria"]) == 3
    assert "pooled sigma stays" in FL.ADOPTION_RULE["default_if_failed"]


def test_rule_adopts_only_when_all_three_criteria_hold():
    adopt = FL.apply_adoption_rule(
        mdm80_delta=-0.3, delta_ci=(-0.5, -0.1), far_achieved=0.04,
        far_target=0.05, concentration_delta=-0.02,
    )
    assert adopt["adopt_farm_local"] is True


def test_rule_refuses_when_the_ci_straddles_zero():
    out = FL.apply_adoption_rule(
        mdm80_delta=-0.3, delta_ci=(-0.5, 0.1), far_achieved=0.04,
        far_target=0.05, concentration_delta=-0.02,
    )
    assert out["adopt_farm_local"] is False
    assert out["decision"] == "pooled sigma stays frozen"


def test_rule_refuses_when_the_far_budget_is_missed():
    out = FL.apply_adoption_rule(
        mdm80_delta=-0.3, delta_ci=(-0.5, -0.1), far_achieved=0.09,
        far_target=0.05, concentration_delta=0.0,
    )
    assert out["checks"]["far_budget_met"] is False
    assert out["adopt_farm_local"] is False


def test_rule_refuses_when_concentration_increases():
    out = FL.apply_adoption_rule(
        mdm80_delta=-0.3, delta_ci=(-0.5, -0.1), far_achieved=0.05,
        far_target=0.05, concentration_delta=0.2,
    )
    assert out["checks"]["concentration_not_worse"] is False
    assert out["adopt_farm_local"] is False
