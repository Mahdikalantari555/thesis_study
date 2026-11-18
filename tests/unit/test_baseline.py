from __future__ import annotations

import numpy as np
import pytest

from ssl_anomaly.baseline.robust import RobustBaseline, fit_baseline, lookup_median_scale
from ssl_anomaly.baseline.score import (
    aggregate_band_scores,
    flag_runs,
    score_cycle,
)
from ssl_anomaly.baseline.trimming import trimmed_normal_cycles


def _synthetic_X(rng, normal_shape=(80, 24, 7), anom_shape=(20, 24, 7)):
    """Generate normal cycles (N(0,1) per bin/band) plus anomaly cycles with a
    strong spike."""
    X_norm = rng.normal(0, 1, size=normal_shape).astype(np.float64)
    X_anom = rng.normal(0, 1, size=anom_shape).astype(np.float64)
    # Inject strong anomaly mid-cycle
    X_anom[:, 10:12, :] += 6.0
    return X_norm, X_anom


def test_fit_baseline_basic(rng):
    X_norm, X_anom = _synthetic_X(rng)
    X = {"all": np.concatenate([X_norm, X_anom], axis=0)}
    bl = fit_baseline(X, X_by_field={}, min_n=5, kappa=2.5, floor_pct=5.0)
    assert "all" in bl.stats
    assert bl.floor > 0
    assert bl.stats["all"].median.shape == (24, 7)


def test_lookup_fallback(rng):
    # When 'all' is populated, lookups for missing strata return all
    X_norm, _ = _synthetic_X(rng)
    X = {"all": X_norm}
    bl = fit_baseline(X, X_by_field={}, min_n=5)
    med, scale = lookup_median_scale(bl, "ratoon_2|V1", (24, 7))
    assert np.all(np.isfinite(med))
    assert np.all(np.isfinite(scale))


def test_score_cycle_detects_anomaly(rng):
    X_norm, X_anom = _synthetic_X(rng)
    X = {"all": X_norm}
    bl = fit_baseline(X, X_by_field={}, min_n=5)
    # Anomalous cycle should have high z-scores mid-cycle
    z = score_cycle(X_anom[0], bl, stratum="all")
    assert z.shape == (24, 7)
    # mid-cycle (where we injected) should have higher |z| than early bins
    mid = np.nanmean(np.abs(z[10:12]))
    early = np.nanmean(np.abs(z[:3]))
    assert mid > early
    # Aggregate score
    S = aggregate_band_scores(z)
    assert S.shape == (24,)
    assert np.nanmax(S[10:12]) > 3.5


def test_flag_runs_min_length():
    S = np.array([0.1, 0.2, 5.0, 4.0, 0.2, 6.0, 0.1])
    flags, runs = flag_runs(S, threshold=3.5, min_run_bins=2)
    assert flags.tolist() == [False, False, True, True, False, False, False]
    assert runs == [(2, 4)]


def test_trimming_removes_seeded_anomalies(rng):
    X_norm, X_anom = _synthetic_X(rng)
    X = {"all": np.concatenate([X_norm, X_anom], axis=0)}
    n_total = X["all"].shape[0]
    n_anom = X_anom.shape[0]
    active = trimmed_normal_cycles(
        X, strata_per_cycle={"all": np.ones(n_total, dtype=bool)},
        X_by_field={}, min_n=5, q=0.2, iters=3, threshold=3.5,
    )
    # After trimming, most seeded anomalies should be marked inactive
    active_arr = active["all"]
    # The last n_anom entries are the injected anomalies (we stacked after normals)
    removed_anom = np.sum(~active_arr[-n_anom:])
    assert removed_anom >= n_anom * 0.5  # at least half of seeded anomalies


def test_baseline_save_load_roundtrip(rng, tmp_path):
    X_norm, _ = _synthetic_X(rng)
    X = {"all": X_norm}
    bl = fit_baseline(X, X_by_field={}, min_n=5)
    bl.band_names = [f"b{i}" for i in range(7)]
    path = tmp_path / "bl.npz"
    bl.to_npz(str(path))
    bl2 = RobustBaseline.from_npz(str(path))
    np.testing.assert_allclose(
        bl.stats["all"].median, bl2.stats["all"].median, equal_nan=True
    )
    assert bl.floor == pytest.approx(bl2.floor)
