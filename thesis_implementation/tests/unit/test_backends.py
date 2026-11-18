from __future__ import annotations

import numpy as np

from ssl_anomaly.backends import get_backend
from ssl_anomaly.backends.numpy_backend import NumpyBackend


def test_numpy_backend_whittaker_batch(rng):
    bk = NumpyBackend()
    T = 200
    x = np.sin(np.linspace(0, 4 * np.pi, T)) + rng.normal(0, 0.2, size=(3, T))
    w = np.ones_like(x)
    w[:, 50:60] = 0.0
    z = bk.whittaker_batch(x, w, lam=50.0)
    assert z.shape == x.shape
    assert np.all(np.isfinite(z))


def test_numpy_backend_robust_baseline_handles_nans(rng):
    bk = NumpyBackend()
    X = rng.normal(0, 1, size=(30, 24, 7))
    X[0, 0, :] = np.nan
    med, scale = bk.robust_baseline(X, min_n=5)
    assert med.shape == (24, 7)
    assert scale.shape == (24, 7)
    assert np.nanmedian(scale) > 0


def test_get_backend_numpy():
    bk = get_backend("numpy")
    assert isinstance(bk, NumpyBackend)


def test_get_backend_rust_or_fallback(monkeypatch):
    import sys

    import pytest

    try:
        import ssl_anomaly_rs  # noqa: F401
        bk = get_backend("rust")
        assert bk.name == "rust"
    except ImportError:
        pass

    # Verify clean NotImplementedError when Rust extension is unavailable
    monkeypatch.setitem(sys.modules, "ssl_anomaly_rs", None)
    with pytest.raises(NotImplementedError):
        get_backend("rust")
