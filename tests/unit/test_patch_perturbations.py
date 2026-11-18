"""Patch-tensor + gradual-shape injections.

Covers ``patch-level-controlled-trial`` task 2.3 and
``gradual-severity-shape`` tasks 1.1/1.2/1.2b.
"""

from __future__ import annotations

import numpy as np
import pytest

from ssl_anomaly.monitor import patch_perturbations as PP
from ssl_anomaly.monitor import perturbations as FP
from ssl_anomaly.monitor.severity_table import PERSISTENT_DURATION_BINS, SEVERITY_TABLE

T, C, S = 36, 8, 32


def _patch(ndvi=0.70, red=0.15, nir=0.55, infield_slice=(4, 28)):
    x = np.zeros((T, C, S, S))
    x[:, 0] = ndvi
    x[:, 3] = red
    x[:, 4] = nir
    m = np.zeros((T, C, S, S), dtype=bool)
    in_field = np.zeros((S, S), dtype=bool)
    lo, hi = infield_slice
    in_field[lo:hi, lo:hi] = True
    m[:] = in_field[None, None]
    return x, m, in_field


def _delta(level_id: str) -> float:
    return {lv.level_id: lv.delta_ndvi for lv in SEVERITY_TABLE}[level_id]


# --- ramp profile (gradual 1.1) -------------------------------------------
@pytest.mark.parametrize("d", PP.GRADUAL_DURATIONS)
def test_ramp_is_linear_then_held(d):
    prof = PP.ramp_profile(d, n_bins=T, onset=10, n_steps=12)
    expected = [min(1.0, (t + 1) / d) for t in range(12)]
    np.testing.assert_allclose(prof, expected, atol=1e-12)
    assert np.allclose(prof[d:], 1.0)


def test_ramp_duration_must_be_positive():
    with pytest.raises(ValueError, match="≥ 1"):
        PP.ramp_profile(0, n_bins=T, onset=0)


def test_gradual_onset_is_shifted_so_the_ramp_fits():
    """The full ramp must fit inside the cycle — shift onset, never truncate."""
    onset = PP.onset_for_shape(PP.SHAPE_GRADUAL, n_bins=T, phase_start=34, duration=6)
    assert onset + 6 <= T
    assert onset < 34


def test_acute_onset_is_not_moved():
    assert PP.onset_for_shape(PP.SHAPE_ACUTE, n_bins=T, phase_start=34, duration=6) == 34


# --- gradual injection values --------------------------------------------
@pytest.mark.parametrize("d", PP.GRADUAL_DURATIONS)
def test_each_ramp_bin_drops_delta_times_the_profile(d):
    x, m, inf = _patch()
    delta = _delta("S4")
    inj = PP.inject_patch_drop(
        x, m, index="ndvi", delta=delta, onset_bin=10, shape=PP.SHAPE_GRADUAL,
        ramp_duration=d, in_field=inf, level_id="S4",
    )
    got = x[:, 0, 16, 16] - inj.x[:, 0, 16, 16]
    for t in range(d):
        assert got[10 + t] == pytest.approx(delta * (t + 1) / d, abs=1e-9)
    assert np.allclose(got[10 + d:], delta, atol=1e-9)   # held to cycle end
    assert np.allclose(got[:10], 0.0)


def test_gradual_ndvi_floors_at_the_physical_range():
    x, m, inf = _patch(ndvi=0.05)
    # δ beyond the physical span forces the floor on the later ramp bins
    inj = PP.inject_patch_drop(x, m, index="ndvi", delta=1.5, onset_bin=5,
                               shape=PP.SHAPE_GRADUAL, ramp_duration=3, in_field=inf)
    assert inj.meta["n_floored_values"] > 0
    assert float(inj.x[:, 0].min()) >= FP.NDVI_PHYSICAL_RANGE[0]


def test_ndvi_stays_inside_the_physical_range_for_the_real_ladder():
    """No floor is hit by the S1–S6 ladder on a healthy field — the meta field
    must therefore report exactly zero, not a spurious count."""
    x, m, inf = _patch(ndvi=0.70)
    for lv in SEVERITY_TABLE:
        inj = PP.inject_patch_drop(x, m, index="ndvi", delta=lv.delta_ndvi,
                                   onset_bin=10, duration=2, in_field=inf)
        assert inj.meta["n_floored_values"] == 0, lv.level_id
        assert float(inj.x[:, 0].min()) >= FP.NDVI_PHYSICAL_RANGE[0]


def test_gradual_savi_uses_the_solver_at_each_partial_delta():
    x, m, inf = _patch()
    delta = _delta("S4")
    inj = PP.inject_patch_drop(x, m, index="savi", delta=delta, onset_bin=8,
                               shape=PP.SHAPE_GRADUAL, ramp_duration=4, in_field=inf)
    base = FP.savi_from_red_nir(x[0, 3, 16, 16], x[0, 4, 16, 16])
    for t, mult in enumerate([0.25, 0.5, 0.75, 1.0]):
        got = base - FP.savi_from_red_nir(inj.x[8 + t, 3, 16, 16], inj.x[8 + t, 4, 16, 16])
        assert got == pytest.approx(delta * mult, abs=1e-6)
    # sum-preserving: brightness is not smuggled in
    assert inj.x[8, 3, 16, 16] + inj.x[8, 4, 16, 16] == pytest.approx(0.15 + 0.55, abs=1e-9)


# --- field-level / patch-level equivalence (gradual 1.1) ------------------
@pytest.mark.parametrize("index", ["ndvi", "savi"])
@pytest.mark.parametrize("family", ["acute", "persistent"])
def test_patch_and_field_appliers_agree_bin_for_bin(index, family):
    """The same parameters must give the same per-bin δ profile on both paths.

    This is the comparability contract behind findings 18/22: a patch arm can
    only be compared to a field arm on the same injection.
    """
    x, m, inf = _patch()
    delta = _delta("S3")
    duration = (PERSISTENT_DURATION_BINS if family == "persistent"
                else {lv.level_id: lv.duration_bins for lv in SEVERITY_TABLE}["S3"])
    onset = 12

    patch_inj = PP.inject_patch_drop(
        x, m, index=index, delta=delta, onset_bin=onset, shape=family,
        duration=duration, in_field=inf, footprint=1.0,
    )
    field_inj = FP.inject_index_drop(
        x[:, :, 16, 16], m[:, :, 16, 16], index=index, onset_bin=onset,
        duration=duration, delta=delta, family=family,
    )
    if index == "ndvi":
        np.testing.assert_allclose(patch_inj.x[:, 0, 16, 16], field_inj.x[:, 0], atol=1e-9)
    else:
        for ch in (3, 4):
            np.testing.assert_allclose(patch_inj.x[:, ch, 16, 16], field_inj.x[:, ch], atol=1e-9)


def test_acute_and_persistent_hashes_are_distinct_but_reproducible():
    x, m, inf = _patch()
    a1 = PP.inject_patch_drop(x, m, index="ndvi", delta=0.08, onset_bin=9,
                              shape=PP.SHAPE_ACUTE, duration=2, in_field=inf)
    a2 = PP.inject_patch_drop(x, m, index="ndvi", delta=0.08, onset_bin=9,
                              shape=PP.SHAPE_ACUTE, duration=2, in_field=inf)
    p1 = PP.inject_patch_drop(x, m, index="ndvi", delta=0.08, onset_bin=9,
                              shape=PP.SHAPE_PERSISTENT, duration=5, in_field=inf)
    assert a1.to_hash_record()["sha256"] == a2.to_hash_record()["sha256"]
    assert a1.to_hash_record()["sha256"] != p1.to_hash_record()["sha256"]


# --- footprint (spatial extent axis) -------------------------------------
@pytest.mark.parametrize("frac", PP.EXTENT_SWEEP)
def test_footprint_realizes_the_requested_share(frac):
    x, m, inf = _patch()
    inj = PP.inject_patch_drop(x, m, index="ndvi", delta=0.16, onset_bin=10,
                               duration=2, in_field=inf, footprint=frac)
    assert inj.meta["footprint_realized"] == pytest.approx(frac, abs=0.01)
    assert int(inj.footprint_mask.sum()) == int(round(frac * inf.sum()))


def test_footprint_never_leaves_the_field():
    x, m, inf = _patch()
    inj = PP.inject_patch_drop(x, m, index="ndvi", delta=0.16, onset_bin=10,
                               duration=2, in_field=inf, footprint=0.3)
    assert not bool((inj.footprint_mask & ~inf).any())


def test_localization_probe_footprint_is_the_pre_registered_one():
    assert PP.FOOTPRINT_LOCALIZATION == 0.3
    assert PP.FOOTPRINT_PROTOCOL == 1.0


def test_white_null_is_seeded_and_footprint_matched():
    x, m, inf = _patch()
    a = PP.inject_patch_drop(x, m, index="ndvi", delta=0.16, onset_bin=10, duration=2,
                             in_field=inf, footprint=0.3, spatial=PP.SPATIAL_WHITE,
                             rng=np.random.default_rng(11))
    b = PP.inject_patch_drop(x, m, index="ndvi", delta=0.16, onset_bin=10, duration=2,
                             in_field=inf, footprint=0.3, spatial=PP.SPATIAL_WHITE,
                             rng=np.random.default_rng(11))
    assert np.array_equal(a.footprint_mask, b.footprint_mask)
    assert a.meta["footprint_realized"] == pytest.approx(0.3, abs=0.01)
    # white ≠ contiguous (structure actually removed)
    c = PP.inject_patch_drop(x, m, index="ndvi", delta=0.16, onset_bin=10, duration=2,
                             in_field=inf, footprint=0.3)
    assert not np.array_equal(a.footprint_mask, c.footprint_mask)


def test_white_null_requires_an_rng():
    x, m, inf = _patch()
    with pytest.raises(ValueError, match="seeded rng"):
        PP.inject_patch_drop(x, m, index="ndvi", delta=0.1, onset_bin=5, duration=1,
                             in_field=inf, footprint=0.3, spatial=PP.SPATIAL_WHITE)


# --- masks are never touched ---------------------------------------------
def test_mask_is_byte_identical_after_injection():
    x, m, inf = _patch()
    for index in ("ndvi", "savi"):
        for shape in PP.PRIMARY_SHAPES:
            inj = PP.inject_patch_drop(x, m, index=index, delta=0.16, onset_bin=8,
                                       shape=shape, duration=3, ramp_duration=3,
                                       in_field=inf)
            assert np.array_equal(inj.m, m)


def test_unobserved_pixels_are_never_injected():
    x, m, inf = _patch()
    m[:, :, 10:14] = False                   # a stripe of missing data
    inj = PP.inject_patch_drop(x, m, index="ndvi", delta=0.4, onset_bin=5,
                               duration=3, in_field=inf)
    np.testing.assert_allclose(inj.x[:, :, 10:14], x[:, :, 10:14], atol=0)


# --- secondary shapes stay secondary -------------------------------------
def test_secondary_shapes_are_registered_separately():
    assert PP.SHAPE_GRADUAL in PP.PRIMARY_SHAPES
    assert PP.SHAPE_PEAK in PP.SECONDARY_SHAPES
    assert PP.SHAPE_RECOVERY in PP.SECONDARY_SHAPES
    assert not set(PP.PRIMARY_SHAPES) & set(PP.SECONDARY_SHAPES)


@pytest.mark.parametrize("mode", ["fail", "slow"])
def test_recovery_shapes_apply_and_are_flagged_secondary(mode):
    x, m, inf = _patch()
    inj = PP.inject_patch_recovery(
        x, m, index="ndvi", delta=0.16, onset_bin=10, drop_bins=2,
        mode=mode, hold_bins=3, in_field=inf,
    )
    assert inj.meta["secondary"] is True
    got = x[:, 0, 16, 16] - inj.x[:, 0, 16, 16]
    assert got[10] == pytest.approx(0.16)
    if mode == "fail":
        assert got[13] == pytest.approx(0.16)          # level held
    else:
        assert 0.16 > got[13] > 0.0                    # ramping back


def test_recovery_mode_is_validated():
    x, m, inf = _patch()
    with pytest.raises(ValueError, match="recovery mode"):
        PP.inject_patch_recovery(x, m, index="ndvi", delta=0.1, onset_bin=5,
                                 drop_bins=2, mode="teleport", in_field=inf)


# --- bad input ------------------------------------------------------------
def test_unknown_index_and_shape_are_loud():
    x, m, inf = _patch()
    with pytest.raises(ValueError, match="unknown index"):
        PP.inject_patch_drop(x, m, index="ndwi", delta=0.1, onset_bin=5, duration=1, in_field=inf)
    with pytest.raises(ValueError, match="unsupported shape"):
        PP.inject_patch_drop(x, m, index="ndvi", delta=0.1, onset_bin=5,
                             shape="explosive", duration=1, in_field=inf)


def test_mask_shape_mismatch_is_loud():
    x, m, inf = _patch()
    with pytest.raises(ValueError, match="mask shape"):
        PP.inject_patch_drop(x, m[:10], index="ndvi", delta=0.1, onset_bin=5,
                             duration=1, in_field=inf)


def test_injection_set_hash_changes_with_the_set():
    x, m, inf = _patch()
    a = PP.inject_patch_drop(x, m, index="ndvi", delta=0.08, onset_bin=9, duration=2, in_field=inf)
    b = PP.inject_patch_drop(x, m, index="ndvi", delta=0.08, onset_bin=14, duration=2, in_field=inf)
    h1 = PP.injection_set_sha256([a])
    h2 = PP.injection_set_sha256([a, b])
    assert h1 != h2
    assert h1 == PP.injection_set_sha256([a])
