from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

SCRIPTS_DIR = str(Path(__file__).resolve().parents[2] / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


def test_pixel_harvest_scatter_on_synthetic_raster():
    """Verify raster pixel extraction detects small scatter for uniform farm and high scatter for staggered farm."""
    from run_eintra import compute_field_pixel_scatter, extract_pixels_from_raster_stack

    rng = np.random.default_rng(7)
    t_days = np.arange(0, 1100, 8, dtype=np.int64)
    T = t_days.size
    H, W = 6, 8
    field_mask = np.zeros((H, W), dtype=np.int32)
    field_mask[:3, :] = 1  # Farm 1: uniform harvest at day 360 and 720
    field_mask[3:, :] = 2  # Farm 2: staggered harvest across columns (-40d .. +40d)

    stack = np.zeros((T, H, W), dtype=np.float32)
    for r in range(H):
        for c in range(W):
            fid = field_mask[r, c]
            shift = 0.0 if fid == 1 else (c - 3.5) * 12.0  # ~84-day spread across Farm 2
            phase = ((t_days - shift) % 360.0) / 360.0
            # Smooth crop growth curve with deep harvest trough near phase=0/1
            ndvi = 0.15 + 0.65 * np.sin(np.pi * phase) ** 0.7 + rng.normal(0, 0.015, size=T)
            stack[:, r, c] = np.clip(ndvi, 0.05, 0.9)

    extracted = extract_pixels_from_raster_stack(stack, field_mask, max_pixels_per_field=24, seed=0)
    res_uniform = compute_field_pixel_scatter(1, t_days, *extracted[1], lam=50.0)
    res_stagger = compute_field_pixel_scatter(2, t_days, *extracted[2], lam=50.0)

    assert res_uniform["n_matched_harvests"] >= 1
    assert res_stagger["n_matched_harvests"] >= 1
    assert res_uniform["mean_std_days"] < 10.0
    assert res_stagger["mean_std_days"] > 20.0
    assert res_stagger["mean_std_days"] > res_uniform["mean_std_days"] * 3.0
