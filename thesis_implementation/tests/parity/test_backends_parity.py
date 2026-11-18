"""Parity tests between NumPy reference backend and PyO3 Rust backend (ssl_anomaly_rs).

Enforces rtol=1e-6 across randomized 3-D cycle tensors (with NaNs and sparse bins)
and batched irregular Whittaker-Eilers smoothing signals.
"""

from __future__ import annotations

import numpy as np
import pytest

from ssl_anomaly.backends import get_backend

try:
    import ssl_anomaly_rs  # noqa: F401

    HAS_RUST = True
except ImportError:
    HAS_RUST = False


def _random_cycles(seed: int = 42, n: int = 21, bins: int = 24, bands: int = 7) -> np.ndarray:
    r = np.random.default_rng(seed)
    X = r.normal(0, 1, size=(n, bins, bands))
    mask = r.random(X.shape) < 0.15
    X[mask] = np.nan
    # Under-sampled bin (< min_n)
    X[3:, 0, :] = np.nan
    # All-NaN bin
    X[:, 1, 0] = np.nan
    return X


def _random_signals(seed: int = 42, B: int = 8, T: int = 200) -> tuple[np.ndarray, np.ndarray]:
    r = np.random.default_rng(seed)
    y = 0.5 + 0.35 * np.sin(np.linspace(0, 6 * np.pi, T)) + r.normal(0, 0.08, size=(B, T))
    w = r.uniform(0.3, 1.0, size=(B, T))
    w[:, 40:55] = 0.0
    nan_mask = r.random(y.shape) < 0.1
    y[nan_mask] = np.nan
    return y, w


@pytest.mark.skipif(not HAS_RUST, reason="Rust backend (ssl_anomaly_rs) not installed")
@pytest.mark.parity
def test_rust_robust_baseline_matches_numpy():
    npy = get_backend("numpy")
    rust = get_backend("rust")
    for seed in range(20):
        n_cyc = 18 + (seed % 5)  # test both even and odd counts
        X = _random_cycles(seed=seed, n=n_cyc)
        m0, s0 = npy.robust_baseline(X, min_n=5)
        m1, s1 = rust.robust_baseline(X, min_n=5)
        np.testing.assert_allclose(m0, m1, rtol=1e-6, atol=0.0, equal_nan=True)
        np.testing.assert_allclose(s0, s1, rtol=1e-6, atol=0.0, equal_nan=True)

    # Verify float32 input handling as well
    X32 = _random_cycles(seed=99).astype(np.float32)
    m0, s0 = npy.robust_baseline(X32, min_n=5)
    m1, s1 = rust.robust_baseline(X32, min_n=5)
    np.testing.assert_allclose(m0, m1, rtol=1e-6, equal_nan=True)
    np.testing.assert_allclose(s0, s1, rtol=1e-6, equal_nan=True)


@pytest.mark.skipif(not HAS_RUST, reason="Rust backend (ssl_anomaly_rs) not installed")
@pytest.mark.parity
def test_rust_whittaker_matches_numpy():
    npy = get_backend("numpy")
    rust = get_backend("rust")
    for seed in range(20):
        y, w = _random_signals(seed=seed)
        lam = [10.0, 50.0, 250.0][seed % 3]
        z0 = npy.whittaker_batch(y, w, lam=lam)
        z1 = rust.whittaker_batch(y, w, lam=lam)
        np.testing.assert_allclose(z0, z1, rtol=1e-6, atol=1e-10)

    # Verify 1-D input promotion matches NumPy reference
    y1d, w1d = _random_signals(seed=7, B=1, T=80)
    z0_1d = npy.whittaker_batch(y1d[0], w1d[0], lam=100.0)
    z1_1d = rust.whittaker_batch(y1d[0], w1d[0], lam=100.0)
    assert z0_1d.shape == z1_1d.shape == (1, 80)
    np.testing.assert_allclose(z0_1d, z1_1d, rtol=1e-6, atol=1e-10)
