#!/usr/bin/env python3
"""Convert existing field Zarr and cycle Parquet into the validation NPZ contract.

Retrospective segmentation is not a real-time/causal guarantee. See protocol docs.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--zarr', type=Path, default=Path('data/processed/fields.zarr'))
    p.add_argument('--cycles', type=Path, default=Path('data/processed/cycles.parquet'))
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--bin-days', type=int, default=15)
    p.add_argument('--max-days', type=int, default=540)
    args = p.parse_args()
    if args.bin_days < 1 or args.max_days < 1:
        p.error('bin-days and max-days must be positive')
    ds = xr.open_zarr(args.zarr)
    cycles = pd.read_parquet(args.cycles)
    times = np.asarray(ds.time.values).astype('datetime64[D]')
    if not len(times) or np.isnat(times).any() or np.any(times[1:] < times[:-1]):
        raise ValueError('Zarr time must be sorted and valid')
    fields = np.asarray(ds.field.values)
    bands = [str(x) for x in ds.band.values]
    if 'SR_B4' not in bands or 'SR_B5' not in bands:
        raise ValueError('SR_B4 and SR_B5 are required to calculate NDVI')
    med = np.asarray(ds['median'].values)
    n_bins = int(np.ceil(args.max_days / args.bin_days))
    rows, starts, ends, fids, dates = [], [], [], [], []
    for _, row in cycles.iterrows():
        if bool(row['censored']):
            continue
        indices = np.flatnonzero(fields == row['field'])
        if len(indices) != 1:
            raise ValueError(f'unknown or duplicate field {row["field"]}')
        start = times[0] + np.timedelta64(int(row['t_start']), 'D')
        end = times[0] + np.timedelta64(int(row['t_end']), 'D')
        harvest = times[0] + np.timedelta64(int(row.get('start_harvest', row['t_start'])), 'D')
        if end <= start:
            continue
        obs = (times >= start) & (times < end)
        dsh = (times[obs] - harvest).astype(int)
        raw = med[indices[0], obs, :]
        red, nir = raw[:, bands.index('SR_B4')], raw[:, bands.index('SR_B5')]
        denom = nir + red
        ndvi = np.divide(nir-red, denom, out=np.full(len(red), np.nan),
                         where=np.isfinite(denom) & (np.abs(denom) > 1e-6))
        valid = (dsh >= 0) & (dsh < args.max_days) & np.isfinite(ndvi)
        x = np.full((n_bins, 1), np.nan)
        for b in np.unique(dsh[valid] // args.bin_days):
            x[int(b), 0] = np.median(ndvi[valid & (dsh // args.bin_days == b)])
        if np.isfinite(x).sum() < 3:
            continue
        rows.append(x); starts.append(str(start)); ends.append(str(end)); fids.append(str(row['field']))
        dates.append(harvest + np.arange(n_bins).astype('timedelta64[D]') * args.bin_days)
    if not rows:
        raise ValueError('no eligible cycles')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.output, X=np.stack(rows), start_dates=np.asarray(starts),
                        end_dates=np.asarray(ends), field_ids=np.asarray(fids),
                        bin_dates=np.stack(dates).astype('datetime64[D]'), bin_days=np.array(args.bin_days))
    print(f'Wrote {len(rows)} NDVI cycles to {args.output}; band index is 0')


if __name__ == '__main__':
    main()
