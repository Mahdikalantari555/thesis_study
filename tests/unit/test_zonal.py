from __future__ import annotations

import numpy as np

from ssl_anomaly.io.zonal import zonal_scene


def test_zonal_scene_basic():
    """Two rectangular fields with constant values: bincount should return exact mean/median."""
    H, W = 60, 60
    labels = np.zeros((H, W), dtype=np.uint32)
    labels[:30, :30] = 1  # field 1
    labels[:30, 30:] = 2  # field 2
    labels[30:, :] = 0  # outside
    valid = np.ones((H, W), dtype=bool)
    valid[10:12, 10:12] = False  # small cloud patch
    bands = {"B1": np.full((H, W), 0.5, dtype=np.float32)}
    bands["B1"][:30, :30] = 0.8  # field 1
    bands["B1"][:30, 30:] = 0.2  # field 2

    df = zonal_scene(bands, valid, labels, n_fields=2)
    assert set(df.columns) >= {"field", "valid_frac", "B1_mean", "B1_median"}
    assert len(df) == 2
    f1 = df[df.field == 1].iloc[0]
    f2 = df[df.field == 2].iloc[0]
    # Most of field 1 valid (except cloud patch which covers 4 of 900 pixels)
    assert f1.valid_frac > 0.99
    assert f1.B1_mean == pytest.approx(0.8, abs=0.01)
    assert f1.B1_median == pytest.approx(0.8, abs=0.01)
    assert f2.B1_mean == pytest.approx(0.2, abs=0.01)


def test_zonal_scene_min_valid_fraction_zeros_out():
    H, W = 30, 30
    labels = np.ones((H, W), dtype=np.uint32)
    # No valid pixels at all
    valid = np.zeros((H, W), dtype=bool)
    bands = {"B1": np.ones((H, W), dtype=np.float32)}
    df = zonal_scene(bands, valid, labels, n_fields=1, min_valid_fraction=0.3)
    row = df.iloc[0]
    assert row.valid_frac == 0.0
    assert np.isnan(row.B1_mean)
    assert np.isnan(row.B1_median)


def test_zonal_scene_shape_mismatch_raises():
    import pytest
    labels = np.zeros((10, 10), dtype=np.uint32)
    valid = np.zeros((10, 10), dtype=bool)
    bands = {"B1": np.zeros((8, 8), dtype=np.float32)}
    with pytest.raises(ValueError):
        zonal_scene(bands, valid, labels, n_fields=1)


import pytest  # noqa: E402
