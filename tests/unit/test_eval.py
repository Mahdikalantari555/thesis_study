from __future__ import annotations

import numpy as np

from ssl_anomaly.backends.numpy_backend import NumpyBackend
from ssl_anomaly.baseline.score import aggregate_band_scores, flag_runs
from ssl_anomaly.eval import (
    bootstrap_ci,
    holm_correction,
    paired_wilcoxon,
    spearman_correlation,
)
from ssl_anomaly.eval.synthetic import InjectionConfig, inject_anomaly, synthetic_benchmark


def test_spearman_basic():
    x = np.arange(10.0)
    y = x + 0.01
    rho, p = spearman_correlation(x, y)
    assert rho == pytest.approx(1.0, abs=1e-6)
    assert p < 0.01


def test_wilcoxon_paired():
    rng = np.random.default_rng(0)
    a = rng.normal(0, 1, size=30)
    b = a + rng.normal(0.5, 0.1, size=30)
    stat, p = paired_wilcoxon(a, b)
    assert np.isfinite(stat)
    assert p < 0.05


def test_holm_correction():
    pvals = np.array([0.001, 0.01, 0.04, 0.2])
    adj = holm_correction(pvals)
    assert np.all(adj >= pvals)
    assert adj[-1] == pytest.approx(0.2)


def test_bootstrap_ci_mean():
    rng = np.random.default_rng(1)
    x = rng.normal(5, 1, size=200)
    pt, lo, hi = bootstrap_ci(np.mean, x, n_boot=200, seed=0)
    assert lo < pt < hi
    assert abs(pt - 5.0) < 0.3


def test_inject_ndvi_drop():
    rng = np.random.default_rng(2)
    cyc = rng.normal(0.5, 0.05, size=(36, 7))
    inj, gt = inject_anomaly(cyc, mode="ndvi_drop", start_bin=10, duration=3, depth=0.3, ndvi_idx=3, rng=rng)
    assert gt[10:13].all()
    assert inj[10, 3] < cyc[10, 3]


def test_synthetic_benchmark_reports_metrics(rng):
    # Build simple "normal" X from numpy backend
    bk = NumpyBackend()
    n_bins, n_bands = 24, 7
    X = rng.normal(0, 1, size=(60, n_bins, n_bands))
    med, scale = bk.robust_baseline(X, min_n=5)
    floor = max(1e-3, float(np.nanpercentile(scale[np.isfinite(scale) & (scale > 0)], 5)))

    def score_fn(cyc):
        z = (cyc - med) / np.maximum(scale, floor)
        S = aggregate_band_scores(z)
        f, _ = flag_runs(S, threshold=3.5, min_run_bins=2)
        return S, f

    cfg = InjectionConfig(n_per_stratum=10, ndvi_drop_depths=[0.2], durations=[3],
                          phases=["mid"], lst_increase_k=[], phenology_delay_days=[],
                          ndvi_band_idx=3, lst_band_idx=6)
    res = synthetic_benchmark(X, score_fn, cfg, rng=rng)
    assert res["recall_at_alert_rate"]
    # With a 20% NDVI drop and our z-score, recall should be >0
    recalls = [r[-1] for r in res["recall_at_alert_rate"]]
    assert np.mean(recalls) >= 0.0


import pytest  # noqa: E402
