#!/usr/bin/env python3
"""Compute per-field, per-date anomaly score (S = RMS z) from per-bin baseline stats."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from ssl_anomaly.baseline.robust import RobustBaseline, build_stratum_table, lookup_median_scale
from ssl_anomaly.baseline.score import aggregate_band_scores
from ssl_anomaly.phenology import add_spectral_indices
from ssl_anomaly.utils.logging import get_logger
from ssl_anomaly.utils.throttle import limit_threads

log = get_logger("ssl_anomaly.scripts.daily_anomaly")


def _fill_missing_bins_nearest(arr: np.ndarray) -> np.ndarray:
    """Fill bins that remain NaN across all strata using nearest observed bin per band."""
    out = arr.copy()
    n_bins, n_bands = out.shape
    for b in range(n_bands):
        col = out[:, b]
        valid = np.where(np.isfinite(col) & (col != 0 if False else True))[0]
        if valid.size == 0:
            continue
        missing = np.where(~np.isfinite(col))[0]
        for m_idx in missing:
            nearest = valid[int(np.argmin(np.abs(valid - m_idx)))]
            col[m_idx] = col[nearest]
    return out


def compute_daily_anomaly_df(
    zarr_path: str | Path = "data/processed/fields.zarr",
    cycles_path: str | Path = "data/processed/cycles.parquet",
    baseline_path: str | Path = "data/processed/baseline.npz",
    *,
    bin_days: int = 15,
    include_censored: bool = True,
) -> pd.DataFrame:
    """Compute per-field, per-date RMS modified z-score ``S`` using phase-bin stats."""
    ds = xr.open_zarr(zarr_path)
    ds = add_spectral_indices(ds)
    times = pd.to_datetime(ds.coords["time"].values)
    fields = ds.coords["field"].values
    ds_bands = list(ds.coords["band"].values)
    med_all = ds["median"].values  # (F, T, B_ds)

    bl = RobustBaseline.from_npz(str(baseline_path))
    bl_bands = list(bl.band_names)
    # Align dataset band slice to baseline band_names
    if all(b in ds_bands for b in bl_bands):
        col_idx = [ds_bands.index(b) for b in bl_bands]
    else:
        col_idx = list(range(min(len(ds_bands), len(bl_bands))))
    med = med_all[:, :, col_idx]
    n_bins = int(bl.bin_centers.size)
    n_bands = len(col_idx)

    cycles = pd.read_parquet(cycles_path)
    cycles = build_stratum_table(cycles)
    epoch = pd.to_datetime(times[0])

    field_to_idx = {int(f): idx for idx, f in enumerate(fields)}
    rows: list[dict] = []

    for _, c in cycles.iterrows():
        is_censored = bool(c["censored"])
        if is_censored and not include_censored:
            continue
        fid = int(c["field"])
        fi = field_to_idx.get(fid)
        if fi is None:
            continue

        stratum = str(c.get("stratum_full", c.get("stratum", "all")))
        med_grid, scale_grid = lookup_median_scale(bl, stratum, (n_bins, n_bands))
        med_grid = _fill_missing_bins_nearest(med_grid)
        scale_grid = _fill_missing_bins_nearest(scale_grid)
        if fid in bl.field_offset and bl.field_offset[fid].shape == (n_bins, n_bands):
            offset = np.where(np.isfinite(bl.field_offset[fid]), bl.field_offset[fid], 0.0)
            med_grid = med_grid + offset

        t_start_dt = epoch + pd.Timedelta(days=int(c["t_start"]))
        t_end_dt = epoch + pd.Timedelta(days=int(c["t_end"]))
        start_h = int(c.get("start_harvest", c["t_start"]))
        if start_h < 0:
            # Leading censored cycle has no preceding harvest anchor (dsh undefined)
            continue
        harvest_dt = epoch + pd.Timedelta(days=start_h)
        max_dsh = n_bins * bin_days

        mask = (times >= t_start_dt) & (times < t_end_dt)
        ti_list = np.where(mask)[0]
        cid = int(c.get("cycle_id", 0))

        for ti in ti_list:
            t = times[ti]
            dsh = int((t - harvest_dt).days)
            if dsh < 0 or dsh >= max_dsh:
                continue
            bin_idx = dsh // bin_days
            obs = med[fi, ti, :].astype(np.float64)
            if not np.isfinite(obs).any():
                continue
            m = med_grid[bin_idx]
            s = np.maximum(scale_grid[bin_idx], bl.floor)
            with np.errstate(all="ignore"):
                z = (obs - m) / s
            s_val = float(aggregate_band_scores(z[None, :])[0])
            if np.isfinite(s_val):
                rows.append({
                    "field": fid,
                    "date": t.strftime("%Y-%m-%d"),
                    "cycle_id": cid,
                    "dsh": int(dsh),
                    "bin_idx": int(bin_idx),
                    "anomaly": s_val,
                })

    if not rows:
        return pd.DataFrame(columns=["field", "date", "cycle_id", "dsh", "bin_idx", "anomaly"])

    df = pd.DataFrame(rows)
    # If cycle boundaries overlap on an exact harvest date, keep highest-anomaly record
    df = (
        df.sort_values(["field", "date", "anomaly"], ascending=[True, True, False])
        .drop_duplicates(subset=["field", "date"], keep="first")
        .sort_values(["field", "date"])
        .reset_index(drop=True)
    )
    return df


def main() -> int:
    limit_threads(2)
    ap = argparse.ArgumentParser(description="Compute per-field, per-date anomaly scores.")
    ap.add_argument("--zarr", default="data/processed/fields.zarr", type=Path)
    ap.add_argument("--cycles", default="data/processed/cycles.parquet", type=Path)
    ap.add_argument("--baseline", default="data/processed/baseline.npz", type=Path)
    ap.add_argument("--out", default="data/processed/daily_anomaly.parquet", type=Path)
    ap.add_argument("--bin-days", default=15, type=int)
    ap.add_argument("--no-censored", action="store_true", help="Exclude censored cycles.")
    args = ap.parse_args()

    df = compute_daily_anomaly_df(
        zarr_path=args.zarr,
        cycles_path=args.cycles,
        baseline_path=args.baseline,
        bin_days=args.bin_days,
        include_censored=not args.no_censored,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.out, index=False)
    log.info("Wrote %d daily anomaly records (%d fields, %d dates) to %s",
             len(df), df["field"].nunique(), df["date"].nunique(), args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
