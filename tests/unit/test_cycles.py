from __future__ import annotations

import numpy as np

from ssl_anomaly.phenology.cycles import (
    detect_harvests,
    segment_cycles,
)
from ssl_anomaly.phenology.smoothing import to_daily_grid


def _trapezoid_ndvi(rng, length=360, ndvi_max=0.85, ndvi_min=0.2, noise=0.02):
    """Sugarcane-like trapezoid over daily grid."""
    y = np.full(length, ndvi_min)
    p1 = length // 4
    p2 = (3 * length) // 4
    y[:p1] = np.linspace(ndvi_min, ndvi_max, p1)
    y[p1:p2] = ndvi_max
    y[p2:] = np.linspace(ndvi_max, ndvi_min, length - p2)
    y += rng.normal(0, noise, size=length)
    return np.clip(y, 0.0, 1.0)


def test_detect_harvests_finds_trough_on_clean_curve(rng):
    daily = np.arange(1000)
    ndvi = np.concatenate([_trapezoid_ndvi(rng, length=340), _trapezoid_ndvi(rng, length=330), _trapezoid_ndvi(rng, length=330)])[:1000]
    grid, ys = to_daily_grid(daily, ndvi, quality=np.ones_like(ndvi), lam=50.0)
    harvests = detect_harvests(grid, ys, min_prominence=0.1, min_cycle_days=250, plateau_frac=0.6, rise_frac=0.1)
    assert harvests.size >= 2
    # Harvests should be roughly a year apart (300-400 days for sugarcane)
    assert 250 < np.diff(harvests).mean() < 450


def test_segment_cycles_synthetic(rng):
    # Build a multi-cycle NDVI series sampled at 8-day cadence
    daily_ndvi = np.concatenate([
        _trapezoid_ndvi(rng, length=350),
        _trapezoid_ndvi(rng, length=340),
        _trapezoid_ndvi(rng, length=330),
    ])
    cadence = 8
    t_days = np.arange(0, daily_ndvi.size, cadence)
    obs_ndvi = daily_ndvi[t_days] + rng.normal(0, 0.01, size=t_days.size)
    # Drop some clouded observations
    mask = rng.random(t_days.size) > 0.15
    t_days, obs_ndvi = t_days[mask], obs_ndvi[mask]

    cycles = segment_cycles(
        field_id=1,
        times_days=t_days,
        ndvi=obs_ndvi,
        quality=np.ones_like(obs_ndvi),
        min_cycle_days=250, max_cycle_days=450,
        min_prominence=0.1, plateau_frac=0.6, rise_frac=0.1,
    )
    assert len(cycles) >= 3
    # Censoring: first and last
    assert cycles[0].censored is True
    assert cycles[-1].censored is True
    # At least one non-censored cycle between
    assert any(not c.censored for c in cycles)
    # Each cycle within length bounds (for non-censored)
    for c in cycles:
        if not c.censored:
            assert 250 <= c.length_days <= 450
