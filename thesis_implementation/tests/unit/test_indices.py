from __future__ import annotations

import numpy as np

from ssl_anomaly.phenology.indices import evi, ndvi, ndwi


def test_ndvi_basic():
    red = np.array([[0.1]], dtype=np.float32)
    nir = np.array([[0.5]], dtype=np.float32)
    out = ndvi(red, nir)
    assert out.shape == (1, 1)
    assert out[0, 0] == pytest.approx((0.5 - 0.1) / (0.5 + 0.1))


def test_ndvi_handles_zero():
    red = np.array([0.0])
    nir = np.array([0.0])
    out = ndvi(red, nir)
    assert np.isnan(out[0])


def test_evi_runs():
    red = np.array([0.1])
    nir = np.array([0.5])
    blue = np.array([0.05])
    out = evi(red, nir, blue)
    assert np.isfinite(out[0])


def test_ndwi_runs():
    nir = np.array([0.4])
    swir = np.array([0.2])
    out = ndwi(nir, swir)
    assert np.isfinite(out[0])


import pytest  # noqa: E402
