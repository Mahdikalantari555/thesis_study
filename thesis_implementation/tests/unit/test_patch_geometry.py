"""Tests for patch geometry, bin aggregation and the store schema
(change patch-data-pipeline, tasks 1.1 and 1.3).

Pure-array tests: no rasterio/geopandas and no data archive needed. The
measured field-size extremes quoted in the proposal (2.27 ha and 34.6 ha) are
expressed as pixel counts at 30 m, which is what the geometry sees.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.io import patches as P  # noqa: E402

# 30 m pixels: 2.27 ha ≈ 25 px, 34.6 ha ≈ 384 px → ~5×5 and ~20×20 sides.
PX_AREA_HA = 0.09
SMALL_SIDE = int(round(np.sqrt(2.27 / PX_AREA_HA)))     # 5
LARGE_SIDE = int(round(np.sqrt(34.6 / PX_AREA_HA)))     # 20


def rect_mask(shape=(40, 40), r0=5, c0=7, h=5, w=5) -> np.ndarray:
    m = np.zeros(shape, dtype=bool)
    m[r0 : r0 + h, c0 : c0 + w] = True
    return m


# ---------------------------------------------------------------------------
# Task 1.1 — bbox crop/pad, no resampling
# ---------------------------------------------------------------------------
def test_window_centres_the_bbox_in_the_patch() -> None:
    win = P.field_window(rect_mask(h=5, w=5), size=32)
    assert (win.height, win.width) == (SMALL_SIDE, SMALL_SIDE)
    assert win.pad_top == (32 - 5) // 2
    assert win.pad_left == (32 - 5) // 2
    assert win.pad_top + win.height + win.pad_bottom == 32
    assert win.pad_left + win.width + win.pad_right == 32


def test_small_field_pads_never_resamples() -> None:
    """A 5×5 field becomes a 32×32 patch by padding — pixel count is preserved."""
    mask = rect_mask(h=SMALL_SIDE, w=SMALL_SIDE)
    win = P.field_window(mask, size=32)
    vals = np.arange(40 * 40, dtype=np.float32).reshape(40, 40)
    patch = P.crop_and_pad(vals, win)
    assert patch.shape == (32, 32)
    inside = patch[win.pad_top : win.pad_top + win.height,
                   win.pad_left : win.pad_left + win.width]
    # Exactly the field's own pixels, untouched (no interpolation, no scaling).
    np.testing.assert_array_equal(
        inside, vals[win.row0 : win.row0 + win.height, win.col0 : win.col0 + win.width],
    )
    # Everything outside the bbox is NaN — padding is absence, not a value.
    outside = patch.copy()
    outside[win.pad_top : win.pad_top + win.height,
            win.pad_left : win.pad_left + win.width] = np.nan
    assert np.isnan(outside).all()


def test_large_field_offcentre_bbox_is_handled() -> None:
    """A 20×20 (largest measured) field centred off-grid still fits."""
    mask = rect_mask(shape=(60, 60), r0=30, c0=2, h=LARGE_SIDE, w=LARGE_SIDE)
    win = P.field_window(mask, size=32)
    assert (win.height, win.width) == (LARGE_SIDE, LARGE_SIDE)
    assert win.row0 == 30 and win.col0 == 2


def test_field_larger_than_patch_is_a_hard_error() -> None:
    mask = rect_mask(shape=(80, 80), r0=0, c0=0, h=40, w=40)
    with pytest.raises(ValueError, match="exceeds the 32 x 32 patch"):
        P.field_window(mask, size=32)


def test_empty_field_returns_none() -> None:
    assert P.field_window(np.zeros((20, 20), dtype=bool)) is None


def test_inner_buffer_shrinks_the_mask_and_can_consume_it() -> None:
    mask = rect_mask(h=6, w=6)
    win = P.field_window(mask, size=32, inner_buffer_px=1)
    assert (win.height, win.width) == (4, 4), "1 px erosion removes the outer ring"
    tiny = rect_mask(h=2, w=2)
    assert P.field_window(tiny, size=32, inner_buffer_px=1) is None


def test_window_origin_accounts_for_padding() -> None:
    win = P.field_window(rect_mask(h=5, w=5), size=32)
    origin = win.to_bbox_origin()
    assert origin == (win.row0 - win.pad_top, win.col0 - win.pad_left)
    assert win.as_dict()["size"] == 32


def test_window_at_raster_edge_fills_with_nan() -> None:
    """Negative origins at the raster edge must pad, not wrap."""
    mask = np.zeros((20, 20), dtype=bool)
    mask[0, 0] = True
    win = P.field_window(mask, size=32)
    win = P.FieldWindow(row0=-3, col0=-2, height=8, width=8, size=32,
                        pad_top=12, pad_left=12)
    vals = np.ones((20, 20), dtype=np.float32)
    patch = P.crop_and_pad(vals, win)
    assert patch.shape == (32, 32)
    # The part above/left of the raster is NaN-filled.
    assert np.isnan(patch[12:15, 12:14]).all()
    assert (patch[15:20, 14:20] == 1.0).all()


def test_in_field_mask_excludes_neighbouring_fields() -> None:
    """The static mask is the field's polygon only — neighbours are 0."""
    own = resample_like = np.zeros((40, 40), dtype=bool)
    own[5:15, 5:15] = True
    neighbour = np.zeros((40, 40), dtype=bool)
    neighbour[5:15, 15:25] = True          # touches the field's eastern edge
    win = P.field_window(own, size=32)
    mask = P.patch_in_field_mask(own, win)
    assert mask.dtype == np.uint8
    assert mask.sum() == 100, "only the field's own pixels are in-field"
    # The neighbour shares the bbox: prove those columns are excluded.
    combined = own | neighbour
    win2 = P.field_window(combined, size=32)
    assert win2.width > win.width, "the union bbox is wider"
    mask2 = P.patch_in_field_mask(own, win2)
    assert mask2.sum() == 100
    assert mask2.shape == (32, 32)


def test_in_field_default_is_off_buffer() -> None:
    """inner_buffer_px defaults to 0 — the flag is recorded, not silently on."""
    mask = rect_mask(h=6, w=6)
    win = P.field_window(mask)
    assert (win.height, win.width) == (6, 6)


# ---------------------------------------------------------------------------
# Task 1.3 — per-pixel per-bin median aggregation
# ---------------------------------------------------------------------------
def make_scenes(n=3, c=8, s=4, seed=0):
    rng = np.random.default_rng(seed)
    scenes, masks = [], []
    for _ in range(n):
        scenes.append(rng.normal(0.4, 0.05, size=(c, s, s)).astype(np.float32))
        masks.append(np.ones((s, s), dtype=bool))
    return scenes, masks


def test_aggregate_bin_takes_the_per_pixel_median() -> None:
    c, s = 8, 3
    scenes = [np.full((c, s, s), v, dtype=np.float32) for v in (0.1, 0.5, 0.9)]
    masks = [np.ones((s, s), dtype=bool)] * 3
    out = P.aggregate_bin(scenes, masks, dtype=np.float32)
    np.testing.assert_allclose(out.values, 0.5, atol=1e-6)
    assert out.values.shape == (c, s, s)
    assert out.pixel_valid.all()
    assert out.n_obs == 3


def test_aggregate_bin_propagates_nan_and_never_zero_fills() -> None:
    c, s = 2, 2
    a = np.full((c, s, s), 0.4, dtype=np.float32)
    b = np.full((c, s, s), 0.6, dtype=np.float32)
    mask_a = np.ones((s, s), dtype=bool)
    mask_b = np.ones((s, s), dtype=bool)
    mask_b[0, 0] = False            # clouded in the second acquisition
    a[:, 1, 1] = np.nan             # no valid retrieval at this pixel
    out = P.aggregate_bin([a, b], [mask_a, mask_b], dtype=np.float32)
    # pixel (0,0): only acquisition a → median 0.4
    np.testing.assert_allclose(out.values[:, 0, 0], 0.4, atol=1e-6)
    # pixel (1,1): NaN in a, valid in b → 0.6 (not 0, not NaN)
    np.testing.assert_allclose(out.values[:, 1, 1], 0.6, atol=1e-6)
    assert out.pixel_valid[1, 1] == 1


def test_aggregate_bin_all_invalid_pixel_is_nan_and_marked_invalid() -> None:
    c, s = 1, 2
    a = np.full((c, s, s), np.nan, dtype=np.float32)
    mask = np.zeros((s, s), dtype=bool)
    out = P.aggregate_bin([a], [mask], dtype=np.float32)
    assert np.isnan(out.values).all()
    assert not out.pixel_valid.any()
    assert out.n_obs == 0


def test_aggregate_bin_in_field_mask_excludes_outside_pixels() -> None:
    """Pixels outside the polygon are never asserted as observed."""
    c, s = 2, 4
    scenes = [np.zeros((c, s, s), dtype=np.float32)]
    masks = [np.ones((s, s), dtype=bool)]
    in_field = np.zeros((s, s), dtype=np.uint8)
    in_field[1:3, 1:3] = 1
    out = P.aggregate_bin(scenes, masks, in_field=in_field, dtype=np.float32)
    assert out.pixel_valid.sum() == 4
    assert np.isnan(out.values[:, 0, 0]).all()
    assert (out.values[:, 1:3, 1:3] == 0.0).all()


def test_aggregate_bin_empty_bin_is_all_nan() -> None:
    out = P.aggregate_bin([], [])
    assert out.n_obs == 0
    assert out.sensor_id == P.SENSOR_IDS["unknown"]
    assert np.isnan(out.values).all()


def test_aggregate_bin_shape_mismatch_raises() -> None:
    scenes, masks = make_scenes(n=2, s=4)
    with pytest.raises(ValueError, match="masks"):
        P.aggregate_bin(scenes, masks[:1])
    with pytest.raises(ValueError, match="expected"):
        P.aggregate_bin(scenes[:1], [np.ones((5, 5), dtype=bool)])


def test_n_obs_counts_acquisitions_with_a_valid_pixel() -> None:
    c, s = 1, 2
    scenes = [np.full((c, s, s), 0.3, dtype=np.float32),
              np.full((c, s, s), np.nan, dtype=np.float32)]
    masks = [np.ones((s, s), dtype=bool), np.ones((s, s), dtype=bool)]
    out = P.aggregate_bin(scenes, masks, dtype=np.float32)
    assert out.n_obs == 1, "an acquisition with no finite value does not count"


def test_majority_sensor_is_deterministic_on_ties() -> None:
    assert P.majority_sensor([1, 1, 2]) == 1
    assert P.majority_sensor([2, 1]) == 1, "ties go to the smaller id (L8)"
    assert P.majority_sensor([]) == P.SENSOR_IDS["unknown"]
    assert P.majority_sensor([2, 2, 2]) == 2


def test_aggregate_bin_fp16_roundtrip_keeps_validity() -> None:
    scenes, masks = make_scenes(n=2, s=3)
    out = P.aggregate_bin(scenes, masks)
    assert out.values.dtype == np.float16
    assert out.pixel_valid.dtype == np.uint8


def test_store_byte_estimate_matches_the_proposal_order_of_magnitude() -> None:
    """1,717 cycles × 36 bins × 8 ch × 1024 px × 2 B ≈ 1.0 GB (the quoted figure)."""
    size = P.estimate_store_bytes(490, 1717)
    assert 0.95e9 < size < 1.15e9, f"{size} bytes is not ~1.0 GB"
