from __future__ import annotations

import numpy as np

from ssl_anomaly.phenology.align import (
    assign_stratum,
    coarse_strata,
    compute_dsh,
    compute_gdd,
    default_phase_bins,
    phase_bin,
)


def test_dsh_computes_offset_from_harvest():
    dsh = compute_dsh(harvest_day=1000, obs_days=np.array([990, 1000, 1015, 1030]))
    np.testing.assert_array_equal(dsh, [-10, 0, 15, 30])


def test_gdd_cumulative(rng):
    days = np.arange(0, 30)
    t_mean = 15.0 + rng.normal(0, 2, size=days.size)
    gdd = compute_gdd(t_mean, obs_days=days, harvest_day=0, t_base=10.0)
    assert gdd.shape == days.shape
    assert gdd[0] == 0.0
    assert np.all(np.diff(gdd) >= 0)  # non-decreasing cumulative


def test_phase_bin_assigns_and_medians():
    rng = np.random.default_rng(0)
    bin_days = 15
    dsh = np.arange(0, 300, 8)
    # Use a trapezoid-like rising curve so early < mid
    ndvi_curve = np.where(dsh < 150, dsh / 150.0, 2.0 - dsh / 150.0)  # peaks at day 150
    values = {"NDVI": ndvi_curve + rng.normal(0, 0.01, size=dsh.size)}
    out = phase_bin(values, dsh, bin_days=bin_days, max_cycle_days=300)
    assert out["NDVI"].shape == (300 // bin_days,)
    # Early bins (0-5 = 0-75 days) should be lower than peak bins (10=150 days)
    assert np.nanmean(out["NDVI"][:5]) < np.nanmax(out["NDVI"])


def test_phase_bin_unobserved_bins_are_nan():
    dsh = np.array([30, 45, 300])  # few points; most bins empty
    values = {"NDVI": np.array([0.5, 0.6, 0.2])}
    out = phase_bin(values, dsh, bin_days=15, max_cycle_days=360)
    # Most bins should be NaN
    n_obs = np.sum(~np.isnan(out["NDVI"]))
    assert n_obs <= 5


def test_stratum_hierarchy():
    s = assign_stratum("ratoon", 2, "V1")
    assert s == "ratoon_2|V1"
    coarse = coarse_strata(s)
    assert coarse == ["ratoon_2|V1", "ratoon_2", "ratoon", "all"]


def test_default_bins():
    bins = default_phase_bins(bin_days=15, max_cycle_days=360)
    assert bins.n_bins == 24
    assert bins.edges[0] == 0
