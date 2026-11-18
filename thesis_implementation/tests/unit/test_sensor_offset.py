"""L8/L9 band-offset estimation (task 2.5).

The estimator's job is to be SKEPTICAL: too few pairs, a CI that straddles
zero, or a missing band must all end in "not applied" rather than in a
calibration that quietly adds noise to the archive.
"""

from __future__ import annotations

import numpy as np
import pytest

from ssl_anomaly.io import sensor_offset as SO


def _cy(fid, cid, day, sensor):
    return SO.CycleRef(field_id=fid, cycle_id=cid, day=day, sensor=sensor)


# --- pair search -----------------------------------------------------------
def test_pairs_are_cross_sensor_and_within_a_field():
    cycles = [_cy(1, 1, 100, "L8"), _cy(1, 2, 101, "L9"),
              _cy(2, 3, 100, "L8"), _cy(2, 4, 120, "L9")]
    pairs = SO.find_pairs(cycles)
    assert len(pairs) == 1
    assert pairs[0][0].field_id == 1


def test_a_gap_beyond_the_window_is_not_a_pair():
    assert SO.find_pairs([_cy(1, 1, 100, "L8"), _cy(1, 2, 108, "L9")]) == []
    assert len(SO.find_pairs([_cy(1, 1, 100, "L8"), _cy(1, 2, 103, "L9")],
                             max_gap_days=3)) == 1


def test_the_closest_partner_wins_so_a_cycle_is_counted_once():
    cycles = [_cy(1, 1, 100, "L8"), _cy(1, 2, 101, "L9"), _cy(1, 3, 103, "L9")]
    pairs = SO.find_pairs(cycles, max_gap_days=4)
    assert len(pairs) == 1
    assert pairs[0][1].day == 101


def test_pairs_are_deterministically_ordered():
    cycles = [_cy(1, 2, 101, "L9"), _cy(1, 1, 100, "L8"), _cy(0, 9, 50, "L9"),
              _cy(0, 8, 49, "L8")]
    a = SO.find_pairs(cycles)
    b = SO.find_pairs(list(reversed(cycles)))
    assert [(p[0].field_id, p[0].cycle_id) for p in a] == \
           [(p[0].field_id, p[0].cycle_id) for p in b]


def test_same_sensor_never_pairs_with_itself():
    assert SO.find_pairs([_cy(1, 1, 100, "L8"), _cy(1, 2, 100, "L8")]) == []


# --- a single band ---------------------------------------------------------
def test_a_clean_offset_is_resolved():
    got = SO.band_offset("red", np.full(20, 0.01), min_pairs=10)
    assert got.offset == pytest.approx(0.01)
    assert got.resolved
    assert got.n_pairs == 20


def test_too_few_pairs_is_unresolved_even_with_a_tiny_ci():
    got = SO.band_offset("red", np.full(4, 0.01), min_pairs=10)
    assert got.n_pairs == 4
    assert not got.resolved


def test_an_offset_straddling_zero_is_unresolved():
    rng = np.random.default_rng(0)
    got = SO.band_offset("red", rng.normal(0.0, 0.01, 50))
    assert not got.resolved


def test_the_median_resists_a_single_wild_pair():
    d = np.r_[np.full(19, 0.01), 5.0]
    got = SO.band_offset("red", d, min_pairs=10)
    assert got.offset == pytest.approx(0.01)
    assert got.mad == pytest.approx(0.0)


def test_non_finite_differences_are_dropped_not_averaged():
    got = SO.band_offset("red", [0.01, np.nan, 0.01, np.inf], min_pairs=2)
    assert got.n_pairs == 2
    assert got.offset == pytest.approx(0.01)


def test_no_finite_difference_raises():
    with pytest.raises(ValueError, match="no finite"):
        SO.band_offset("red", [np.nan, np.inf])


def test_the_robust_sigma_follows_the_mad():
    got = SO.band_offset("red", [0.00, 0.01, 0.02, 0.03, 0.04], min_pairs=2)
    assert got.sigma == pytest.approx(1.4826 * got.mad)


# --- the estimator over pairs ---------------------------------------------
BANDS = ("red", "nir")


def _sampler(offset_red=0.02, n=16, valid=True):
    """An L8 cycle reads ``offset_red`` higher in red than the same L9 cycle."""
    def fn(ref):
        v = np.zeros((2, 4, 4))
        v[0] = 0.30 + (offset_red if ref.sensor == "L8" else 0.0)
        v[1] = 0.60
        m = np.full((4, 4), valid)
        return v, m
    return fn


def _pairs(n):
    out = []
    for i in range(n):
        out.append((_cy(0, i, 100 + i, "L8"), _cy(0, 100 + i, 100 + i, "L9")))
    return out


def test_estimate_recovers_the_injected_offset():
    got = SO.estimate_offsets(_pairs(20), _sampler(0.02), bands=BANDS)
    assert got["bands"]["red"]["offset"] == pytest.approx(0.02)
    assert got["bands"]["nir"]["offset"] == pytest.approx(0.0)
    assert got["bands"]["red"]["resolved"]
    assert not got["bands"]["nir"]["resolved"]


def test_the_estimate_records_pair_counts_and_the_reference_sensor():
    got = SO.estimate_offsets(_pairs(12), _sampler(), bands=BANDS)
    assert got["n_pairs_found"] == 12
    assert got["n_pairs_used"] == 12
    assert got["reference_sensor"] == "L9"
    assert got["resolved_count"] == 1


def test_too_few_pairs_leaves_every_band_unresolved():
    got = SO.estimate_offsets(_pairs(3), _sampler(0.5), bands=BANDS)
    assert got["bands"]["red"]["offset"] == pytest.approx(0.5)
    assert not got["bands"]["red"]["resolved"]


def test_an_empty_mask_pair_is_skipped():
    got = SO.estimate_offsets(_pairs(5), _sampler(valid=False), bands=BANDS)
    assert got["n_pairs_used"] == 0
    assert got["skipped_bands"] == list(BANDS)


def test_band_order_is_preserved_in_the_output():
    got = SO.estimate_offsets(_pairs(12), _sampler(), bands=BANDS)
    assert list(got["bands"]) == list(BANDS)


# --- application -----------------------------------------------------------
def _offset_table(resolved=True):
    return {"bands": {
        "red": {"band": "red", "offset": 0.02, "resolved": resolved},
        "nir": {"band": "nir", "offset": 0.01, "resolved": resolved},
    }}


def test_l8_values_move_into_the_l9_frame():
    v = np.full((2, 4, 4), 0.50)
    out, rec = SO.apply_offsets(v, "L8", _offset_table(), bands=BANDS)
    assert out[0] == pytest.approx(0.48)
    assert out[1] == pytest.approx(0.49)
    assert rec["applied"] == ["red", "nir"]


def test_l9_values_are_untouched():
    v = np.full((2, 4, 4), 0.50)
    out, rec = SO.apply_offsets(v, "L9", _offset_table(), bands=BANDS)
    assert np.allclose(out, v)
    assert rec["reason"] == "already the reference"


def test_nan_pixels_stay_nan():
    v = np.full((2, 4, 4), np.nan)
    v[1, 0, 0] = 0.5
    out, _ = SO.apply_offsets(v, "L8", _offset_table(), bands=BANDS)
    assert np.isnan(out[0]).all()
    assert out[1, 0, 0] == pytest.approx(0.49)


def test_the_input_is_not_mutated():
    v = np.full((2, 2, 2), 0.5)
    SO.apply_offsets(v, "L8", _offset_table(), bands=BANDS)
    assert np.allclose(v, 0.5)


def test_an_unresolved_band_is_refused_by_default():
    out, rec = SO.apply_offsets(np.full((2, 4, 4), 0.5), "L8",
                                _offset_table(resolved=False), bands=BANDS)
    assert rec["applied"] == []
    assert all("unresolved" in r for r in rec["refused"])
    assert np.allclose(out, 0.5)


def test_allow_unresolved_is_an_explicit_opt_in_that_is_recorded():
    _, rec = SO.apply_offsets(np.full((2, 4, 4), 0.5), "L8",
                              _offset_table(resolved=False), bands=BANDS,
                              allow_unresolved=True)
    assert rec["applied"] == ["red", "nir"]
    assert rec["allow_unresolved"] is True


def test_a_band_with_no_estimate_is_refused_by_name():
    _, rec = SO.apply_offsets(np.full((2, 4, 4), 0.5), "L8",
                              {"bands": {"red": {"offset": 0.02, "resolved": True}}},
                              bands=BANDS)
    assert rec["applied"] == ["red"]
    assert rec["refused"] == ["nir: no estimate"]


def test_the_stamp_names_the_flag_the_manifest_carries():
    assert SO.marks_applied({"applied": ["red"]})["sensor_offset_applied"] is True


# --- the applied / not-applied decision -----------------------------------
def test_the_plan_states_both_required_conditions():
    p = SO.comparison_plan(n_l8_cycles=200, n_l9_cycles=100)
    assert p["arms"] == ["offsets_off", "offsets_on"]
    assert p["decision_rule"]["both_required"] is True
    assert len(p["decision_rule"]["keep_offsets_iff"]) == 2


def test_offsets_are_kept_when_the_era_gap_shrinks_without_new_alarms():
    d = SO.decide_applied(era_gap_off=0.20, era_gap_on=0.10,
                          l8_far_off=0.05, l8_far_on=0.05)
    assert d["keep_offsets"]
    assert d["era_gap_reduction_frac"] == pytest.approx(0.5)


def test_offsets_are_dropped_if_the_gap_does_not_shrink_enough():
    d = SO.decide_applied(0.20, 0.19, l8_far_off=0.05, l8_far_on=0.05)
    assert not d["keep_offsets"]
    assert not d["gap_ok"]
    assert "era gap" in d["reason"]


def test_offsets_are_dropped_if_l8_only_alarms_rise():
    d = SO.decide_applied(0.20, 0.05, l8_far_off=0.05, l8_far_on=0.06)
    assert not d["keep_offsets"]
    assert not d["far_ok"]
    assert "L8-only FAR" in d["reason"]


def test_both_conditions_are_needed_so_one_pass_is_not_enough():
    d = SO.decide_applied(0.20, 0.05, l8_far_off=0.05, l8_far_on=0.09)
    assert d["gap_ok"]
    assert not d["far_ok"]
    assert not d["keep_offsets"]


def test_a_zero_era_gap_cannot_be_improved_so_offsets_are_dropped():
    d = SO.decide_applied(0.0, 0.0, l8_far_off=0.05, l8_far_on=0.05)
    assert d["era_gap_reduction_frac"] == 0.0
    assert not d["keep_offsets"]


def test_naming_the_channel_axis_catches_a_band_that_is_not_there():
    with pytest.raises(ValueError, match="not in the channel axis"):
        SO.estimate_offsets(_pairs(12), _sampler(), bands=("red",),
                            channel_names=("blue", "green"))


def test_a_named_channel_axis_reads_the_right_row():
    """Row 0 is ``blue`` and is identical for both sensors; row 1 is ``red``
    and reads 0.07 higher on L8. Asking for ``red`` with an explicit axis must
    return 0.07 — reading row 0 would return a confident zero."""
    def fn(ref):
        v = np.zeros((2, 4, 4))
        v[0] = 0.30                                   # blue: same on both sensors
        v[1] = 0.30 + (0.07 if ref.sensor == "L8" else 0.0)
        return v, np.ones((4, 4), dtype=bool)

    got = SO.estimate_offsets(_pairs(12), fn, bands=("red",),
                              channel_names=("blue", "red"))
    assert got["bands"]["red"]["offset"] == pytest.approx(0.07)
    blue = SO.estimate_offsets(_pairs(12), fn, bands=("blue",),
                               channel_names=("blue", "red"))
    assert blue["bands"]["blue"]["offset"] == pytest.approx(0.0)
    assert not blue["bands"]["blue"]["resolved"]
