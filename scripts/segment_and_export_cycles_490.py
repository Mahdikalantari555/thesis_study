"""Segment cycles for all 490 fields and export cycles_490.parquet and growth_cycles_490.npz.

Tasks 1.2 and 1.3:
- Reads stats.zarr (490 fields, 538 dates, 7 bands).
- Runs segment_cycles across 2013-2026.
- Exports thesis_implementation/data/processed/cycles_490.parquet.
- Bins multi-band and NDVI cycles into 36 15-day bins (max 540 days).
- Exports thesis_implementation/data/interim/growth_cycles_490.npz.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add src to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from ssl_anomaly.io.stats_zarr import load_stats_zarr
from ssl_anomaly.phenology.cycles import segment_cycles
from ssl_anomaly.phenology.align import default_phase_bins

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("segment_cycles_490")


def run(
    zarr_path: str = "Data/Processed/satellite/stats.zarr",
    cycles_out: str = "data/processed/cycles_490.parquet",
    npz_out: str = "data/interim/growth_cycles_490.npz",
    bin_days: int = 15,
    max_days: int = 540,
) -> tuple[pd.DataFrame, dict]:
    log.info("Loading stats.zarr from %s", zarr_path)
    reader = load_stats_zarr(zarr_path)
    fields = reader.fields
    dates = reader.dates
    bands = reader.bands
    b_idx = reader.band_index

    # Days since start
    times = dates.to_numpy().astype("datetime64[D]")
    epoch = times[0]
    time_days = (times - epoch).astype(int)

    indices = reader.compute_indices("median")
    ndvi = indices["ndvi"]
    valid_frac = reader.valid_frac
    median_cube = reader.get_stat("median")

    log.info("Running harvest segmentation on all %d fields...", len(fields))
    all_cycles = []
    for fi, fid in enumerate(fields):
        field_cycles = segment_cycles(
            field_id=int(fid),
            times_days=time_days,
            ndvi=ndvi[fi],
            quality=valid_frac[fi],
            min_cycle_days=180,
            max_cycle_days=max_days,
            min_prominence=0.15,
            plateau_frac=0.7,
            rise_frac=0.15,
        )
        for c in field_cycles:
            all_cycles.append(c.to_dict())

    cycles_df = pd.DataFrame(all_cycles)
    cycles_path = ROOT_DIR / cycles_out
    cycles_path.parent.mkdir(parents=True, exist_ok=True)
    cycles_df.to_parquet(cycles_path, index=False)
    log.info(
        "Saved %d cycles (%d non-censored) across %d fields to %s",
        len(cycles_df),
        (~cycles_df["censored"]).sum(),
        cycles_df["field"].nunique(),
        cycles_path,
    )

    # Now bin cycles for growth_cycles_490.npz
    # Phase bins: 15-day bins up to 540 days -> 36 bins
    n_bins = int(np.ceil(max_days / bin_days))
    phase_bins = default_phase_bins(bin_days=bin_days, max_cycle_days=max_days)

    # Band channels: Band 0 is NDVI, Bands 1..7 are blue, green, red, nir, swir1, swir2, lst
    # Total 8 channels for full multi-spectral representation
    channel_names = ["ndvi"] + bands

    rows = []
    starts = []
    ends = []
    fids = []
    bin_dates = []

    for _, row in cycles_df.iterrows():
        if bool(row["censored"]):
            continue

        fid = int(row["field"])
        fi = int(np.where(fields == fid)[0][0])

        start_day = int(row["t_start"])
        end_day = int(row["t_end"])
        harvest_day = int(row.get("start_harvest", row["t_start"]))

        start_dt = times[0] + np.timedelta64(start_day, "D")
        end_dt = times[0] + np.timedelta64(end_day, "D")
        harvest_dt = times[0] + np.timedelta64(harvest_day, "D")

        if end_dt <= start_dt:
            continue

        # Find observations inside cycle
        obs_mask = (times >= start_dt) & (times < end_dt)
        if obs_mask.sum() < 3:
            continue

        obs_times = times[obs_mask]
        dsh = (obs_times - harvest_dt).astype(int)

        valid_obs = (dsh >= 0) & (dsh < max_days)
        if valid_obs.sum() < 3:
            continue

        dsh_valid = dsh[valid_obs]
        ndvi_obs = ndvi[fi, obs_mask][valid_obs]
        cube_obs = median_cube[fi, obs_mask][valid_obs]  # (n_obs, 7)

        # Build (36, 8) binned array
        x_cycle = np.full((n_bins, len(channel_names)), np.nan, dtype=np.float32)

        assigned_bins = dsh_valid // bin_days
        for b in np.unique(assigned_bins):
            if b >= n_bins:
                continue
            b_mask = assigned_bins == b
            # Channel 0: NDVI
            x_cycle[int(b), 0] = np.nanmedian(ndvi_obs[b_mask])
            # Channels 1..7: raw spectral bands
            for ci, bname in enumerate(bands):
                x_cycle[int(b), ci + 1] = np.nanmedian(cube_obs[b_mask, b_idx[bname]])

        # Interpolate single missing gaps within observed range
        observed_bin_indices = np.where(np.isfinite(x_cycle[:, 0]))[0]
        if len(observed_bin_indices) < 3:
            continue

        first_b, last_b = observed_bin_indices[0], observed_bin_indices[-1]
        for ch in range(len(channel_names)):
            series = x_cycle[:, ch]
            # Linearly interpolate interior isolated gaps
            for b in range(first_b + 1, last_b):
                if np.isnan(series[b]):
                    prev_val = series[b - 1]
                    # Look ahead for next valid
                    next_idx = None
                    for look in range(b + 1, min(b + 3, last_b + 1)):
                        if np.isfinite(series[look]):
                            next_idx = look
                            break
                    if next_idx is not None and np.isfinite(prev_val):
                        # Simple linear interpolation
                        series[b] = prev_val + (series[next_idx] - prev_val) * (1 / (next_idx - b + 1))
            x_cycle[:, ch] = series

        dates_for_cycle = harvest_dt + np.arange(n_bins).astype("timedelta64[D]") * bin_days

        rows.append(x_cycle)
        starts.append(str(start_dt))
        ends.append(str(end_dt))
        fids.append(str(fid))
        bin_dates.append(dates_for_cycle)

    X = np.stack(rows)  # (N, 36, 8)
    npz_path = ROOT_DIR / npz_out
    npz_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        npz_path,
        X=X,
        start_dates=np.asarray(starts),
        end_dates=np.asarray(ends),
        field_ids=np.asarray(fids),
        bin_dates=np.stack(bin_dates).astype("datetime64[D]"),
        bin_days=np.array(bin_days),
        channel_names=np.asarray(channel_names),
    )
    log.info(
        "Saved %d binned cycles with shape %s to %s",
        len(rows),
        X.shape,
        npz_path,
    )

    return cycles_df, {"X": X, "n_cycles": len(rows), "npz_path": str(npz_path)}


if __name__ == "__main__":
    run()
