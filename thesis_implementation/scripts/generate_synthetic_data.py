#!/usr/bin/env python3
"""Generate a small synthetic dataset (fields.zarr + cycles.parquet) for
unit/integration tests and local development when no real Landsat data is
available. This is NOT a replacement for real ingest — it produces
phenologically plausible sugarcane-like NDVI curves with cloud gaps and
harvests so every downstream stage can be exercised end-to-end.

Usage::

    python scripts/generate_synthetic_data.py --n-fields 80 --n-years 10 --out data/processed
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr


def trapezoid_cycle(t: np.ndarray, *, p_veg: float = 0.3, p_mat: float = 0.5,
                    ndvi_max: float = 0.8, ndvi_min: float = 0.2, noise: float = 0.03,
                    rng: np.random.Generator = None) -> np.ndarray:
    """Sugarcane-like trapezoidal NDVI curve over days-since-harvest ``t``."""
    rng = rng or np.random.default_rng()
    T = t.size
    y = np.full(T, ndvi_min, dtype=np.float64)
    p_veg_end = int(T * p_veg)
    p_mat_end = int(T * (p_veg + p_mat))
    # Establishment/tillering: linear rise
    y[:p_veg_end] = ndvi_min + (ndvi_max - ndvi_min) * np.linspace(0, 1, p_veg_end)
    # Plateau
    y[p_veg_end:p_mat_end] = ndvi_max
    # Maturation/harvest: slow fall
    fall_len = max(1, T - p_mat_end)
    y[p_mat_end:] = ndvi_max - (ndvi_max - ndvi_min) * np.linspace(0, 1, fall_len)
    y = y + rng.normal(0, noise, size=T)
    # Cloud gaps: drop some observations to NaN at random
    drop = rng.random(T) < 0.25
    y[drop] = np.nan
    return np.clip(y, 0.0, 1.0)


def generate(n_fields: int = 80, n_years: int = 10, out: Path = Path("data/processed"),
             seed: int = 42) -> None:
    rng = np.random.default_rng(seed)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    geo_out = out.parent / "geo"
    geo_out.mkdir(parents=True, exist_ok=True)

    cadence = 8  # ~8 day composite (L8+L9)
    days_total = n_years * 365
    start = np.datetime64("2013-04-01")
    offsets = np.arange(0, days_total, cadence)
    t = start + offsets.astype("timedelta64[D]")
    T = len(t)

    bands = ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7", "ST_B10"]
    B = len(bands)
    med = np.full((n_fields, T, B), np.nan, dtype=np.float32)
    mean = np.full((n_fields, T, B), np.nan, dtype=np.float32)
    vf = np.zeros((n_fields, T), dtype=np.float32)
    sensor = np.array(["L8"] * T, dtype=object)
    sensor[-T // 4:] = "L9"

    cycle_records: list[dict] = []
    field_meta = []

    # Planting date offsets per field (so harvests aren't perfectly aligned)
    starts = rng.integers(0, 180, size=n_fields)
    cycle_len_mean = rng.integers(330, 420, size=n_fields)  # sugarcane ~11-14 months
    ratoon_ns_per_field = rng.integers(2, 6, size=n_fields)

    for f in range(n_fields):
        # Generate harvest times
        harvest_days: list[int] = [int(starts[f])]
        while harvest_days[-1] < days_total - 200:
            n_cycles_so_far = len(harvest_days) - 1
            is_ratoon = n_cycles_so_far <= ratoon_ns_per_field[f]
            length = int(cycle_len_mean[f] + rng.normal(0, 25))
            length = int(np.clip(length, 250, 500))
            # Replant every few ratoons
            if not is_ratoon and rng.random() < 0.3:
                # Fallow gap
                harvest_days.append(harvest_days[-1] + length + 90)
            else:
                harvest_days.append(harvest_days[-1] + length)

        ndvi = np.full(T, np.nan, dtype=np.float32)
        # Map each observation to its cycle dsh and build trapezoid NDVI
        for ci in range(len(harvest_days) - 1):
            h0, h1 = harvest_days[ci], harvest_days[ci + 1]
            # Map day index → observation
            days = (t - t[0]).astype("timedelta64[D]").astype(int)
            mask = (days >= h0) & (days < h1)
            if not mask.any():
                continue
            dsh_local = days[mask] - h0
            daily_ndvi = trapezoid_cycle(
                np.arange(h1 - h0),
                ndvi_max=float(rng.uniform(0.75, 0.9)),
                ndvi_min=float(rng.uniform(0.15, 0.25)),
                noise=0.02, rng=rng,
            )
            obs_vals = daily_ndvi[np.clip(dsh_local, 0, daily_ndvi.size - 1)]
            ndvi[mask] = obs_vals

            cycle_records.append({
                "field": int(f + 1),
                "cycle_id": ci,
                "t_start": int(h0),
                "t_end": int(h1),
                "harvest_day": int(h1),
                "length_days": int(h1 - h0),
                "censored": (ci == 0) or (ci == len(harvest_days) - 2),
                "kind": "plant" if ci == 0 else "ratoon",
                "ratoon_no": max(0, ci - 1),
                "ndvi_at_harvest": float(ndvi[mask][-1]) if mask.any() else 0.2,
                "stratum": "all",
            })

        # Convert NDVI into synthetic bands (proxy reflectances)
        ndvi_arr = np.nan_to_num(ndvi, nan=0.0)
        red = 0.05 + 0.25 * (1 - ndvi_arr)
        nir = 0.05 + 0.45 * ndvi_arr
        green = 0.03 + 0.1 * ndvi_arr
        blue = 0.02 + 0.05 * (1 - ndvi_arr)
        swir1 = 0.1 + 0.25 * (1 - ndvi_arr)
        swir2 = 0.05 + 0.15 * (1 - ndvi_arr)
        # LST ~ 290-310 K; higher when NDVI is low (stress proxy)
        lst = 295 + 12 * (1 - ndvi_arr) + rng.normal(0, 1.5, size=T)
        med[f, :, 0] = blue
        med[f, :, 1] = green
        med[f, :, 2] = red
        med[f, :, 3] = nir
        med[f, :, 4] = swir1
        med[f, :, 5] = swir2
        med[f, :, 6] = lst
        mean[f] = med[f]
        vf[f] = np.where(np.isnan(ndvi), 0.0, rng.uniform(0.6, 1.0, size=T)).astype(np.float32)

        region = f"R{(f % 5) + 1}"
        variety = f"V{(f % 3) + 1}"
        field_meta.append({
            "field": int(f + 1), "region": region, "variety": variety,
            "variety_group": variety,
        })

    ds = xr.Dataset(
        {
            "median": (("field", "time", "band"), med),
            "mean": (("field", "time", "band"), mean),
            "valid_frac": (("field", "time"), vf),
        },
        coords={
            "field": np.arange(1, n_fields + 1, dtype=np.int64),
            "time": t,
            "band": np.array(bands, dtype=object),
            "sensor": (("time",), sensor),
        },
        attrs={"source": "synthetic", "crs": "EPSG:32639", "pixel_size_m": 30.0},
    )
    ds.to_zarr(out / "fields.zarr", mode="w", consolidated=True)
    pd.DataFrame(cycle_records).to_parquet(out / "cycles.parquet")
    pd.DataFrame(field_meta).to_parquet(geo_out / "fields.parquet")
    print(f"Wrote synthetic data to {out} ({n_fields} fields, {T} times, {len(cycle_records)} cycles)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--n-fields", type=int, default=80)
    p.add_argument("--n-years", type=int, default=10)
    p.add_argument("--out", type=Path, default=Path("data/processed"))
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    generate(n_fields=args.n_fields, n_years=args.n_years, out=args.out, seed=args.seed)
