from __future__ import annotations

import numpy as np

from ssl_anomaly.phenology.smoothing import (
    to_daily_grid,
    whittaker_smooth,
    whittaker_tune_lambda,
)


def test_whittaker_on_smooth_signal(rng):
    n = 200
    t = np.arange(n)
    y_true = np.sin(t / 20.0)
    y = y_true + rng.normal(0, 0.2, n)
    z = whittaker_smooth(y, lam=100.0)
    assert z.shape == (n,)
    # RMSE should be substantially smaller than noise
    err_rough = np.sqrt(np.mean((y - y_true) ** 2))
    err_smooth = np.sqrt(np.mean((z - y_true) ** 2))
    assert err_smooth < err_rough


def test_whittaker_handles_nans(rng):
    n = 100
    y = rng.normal(0, 1, n)
    y[30:40] = np.nan
    w = np.ones(n)
    w[30:40] = 0.0
    z = whittaker_smooth(y, w=w, lam=50.0)
    assert np.all(np.isfinite(z))


def test_to_daily_grid(rng):
    # Irregular observations every ~8 days for one year
    t = np.sort(rng.choice(np.arange(0, 365, 8), size=40, replace=False))
    y = np.sin(t / 60.0) + rng.normal(0, 0.05, size=t.size)
    grid, z = to_daily_grid(t, y, lam=50.0)
    assert grid.size == t.max() - t.min() + 1
    assert z.size == grid.size
    assert np.all(np.isfinite(z))


def test_lambda_tuning_returns_finite():
    rng = np.random.default_rng(7)
    t = np.arange(0, 365, 8)
    y = np.sin(t / 60.0) + rng.normal(0, 0.05, size=t.size)
    best, diag = whittaker_tune_lambda(t, y, cv_folds=3, seed=0)
    assert np.isfinite(best)
    assert best > 0
    assert diag["grid_mse"]
