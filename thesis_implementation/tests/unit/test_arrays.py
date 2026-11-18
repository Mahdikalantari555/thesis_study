"""Tests for small array helpers."""

from __future__ import annotations

import numpy as np

from ssl_anomaly.utils.arrays import (
    contiguous_runs,
    hampel_filter,
    mad_scale,
    robust_standardize,
)


def test_mad_scale_basic(rng):
    x = rng.normal(0, 1, size=(100, 5))
    med, scale, floor = mad_scale(x, axis=0)
    assert med.shape == (5,)
    assert scale.shape == (5,)
    assert floor > 0
    # Standardize should be ~zero mean, ~unit scale
    z = robust_standardize(x, med, scale, floor)
    assert np.nanmean(z) == pytest.approx(0.0, abs=0.2)  # type: ignore[name-defined]


def test_contiguous_runs():
    mask = np.array([False, True, True, False, True, True, True, False])
    runs = contiguous_runs(mask, min_length=2)
    assert runs == [(1, 3), (4, 7)]
    runs_3 = contiguous_runs(mask, min_length=3)
    assert runs_3 == [(4, 7)]
    # Single spike filtered out
    spike = np.array([True, False, False, True])
    assert contiguous_runs(spike, min_length=2) == []


def test_hampel_finds_spike(rng):
    t = np.arange(50, dtype=float)
    y = np.sin(t / 5.0)
    y[25] = 10.0  # inject spike
    mask = hampel_filter(t, y, window=5, n_sigma=3)
    assert mask[25]


# Fix missing name import for pytest.approx
import pytest  # noqa: E402
