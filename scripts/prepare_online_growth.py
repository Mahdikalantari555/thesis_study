#!/usr/bin/env python3
"""Build causally binned fixed-horizon cycles using externally known starting anchors.

An anchor must be known by its own start date; do not use retrospectively detected
harvests. Bins are available only after their end. No interpolation or smoothing.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd


def prepare(observations, anchors, *, as_of, bin_days=15, horizon_days=540):
    if bin_days < 1 or horizon_days < 1 or horizon_days % bin_days:
        raise ValueError('horizon must be a positive multiple of bin_days')
    obs = observations.copy(); anc = anchors.copy()
    if not {'field_id', 'date', 'ndvi'}.issubset(obs) or not {'field_id', 'start_date', 'known_date'}.issubset(anc):
        raise ValueError('missing required columns')
    obs['field_id'] = obs['field_id'].astype(str); anc['field_id'] = anc['field_id'].astype(str)
    for frame, cols in [(obs, ['date']), (anc, ['start_date', 'known_date'])]:
        for col in cols:
            frame[col] = pd.to_datetime(frame[col], errors='raise').dt.normalize()
            if frame[col].isna().any():
                raise ValueError('invalid missing dates')
    obs['ndvi'] = pd.to_numeric(obs['ndvi'], errors='raise')
    cutoff = pd.Timestamp(as_of).normalize()
    if (anc.known_date > anc.start_date).any():
        raise ValueError('all anchors must be available no later than their start date')
    if anc.duplicated(['field_id', 'start_date']).any():
        raise ValueError('duplicate field and start date')
    anc = anc.sort_values(['field_id','start_date'])
    for _, part in anc.groupby('field_id'):
        if (part.start_date.diff().dropna().dt.days < horizon_days).any():
            raise ValueError('fixed horizons for one field must not overlap')
    n_bins = horizon_days // bin_days
    rows, ids, starts, ends, dates = [], [], [], [], []
    for row in anc.itertuples(index=False):
        end = row.start_date + pd.Timedelta(days=horizon_days-1)
        # Avoid treating an unobserved future as a completed monitoring horizon.
        if end > cutoff:
            continue
        sub = obs[(obs.field_id == row.field_id) & obs.date.between(row.start_date, end) & (obs.date <= cutoff)]
        delta = (sub.date - row.start_date).dt.days.to_numpy()
        values = sub.ndvi.to_numpy(float)
        x = np.full((n_bins, 1), np.nan)
        for i in range(n_bins):
            valid = (delta // bin_days == i) & np.isfinite(values)
            if valid.any():
                x[i,0] = np.median(values[valid])
        if not np.isfinite(x).any():
            continue
        rows.append(x); ids.append(row.field_id); starts.append(str(row.start_date.date())); ends.append(str(end.date()))
        dates.append(np.datetime64(row.start_date.date(), 'D') +
                     np.arange(n_bins).astype('timedelta64[D]') * bin_days)
    if not rows:
        raise ValueError('no fully elapsed, observed fixed-horizon cycles')
    return {'X': np.stack(rows), 'field_ids': np.array(ids), 'start_dates': np.array(starts),
            'end_dates': np.array(ends), 'bin_dates': np.stack(dates), 'bin_days': np.array(bin_days)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--observations', type=Path, required=True, help='CSV field_id,date,ndvi')
    p.add_argument('--anchors', type=Path, required=True, help='CSV field_id,start_date,known_date')
    p.add_argument('--as-of', required=True, help='latest data available YYYY-MM-DD')
    p.add_argument('--bin-days', type=int, default=15)
    p.add_argument('--horizon-days', type=int, default=540)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    d = prepare(pd.read_csv(a.observations, dtype={'field_id': str}),
                pd.read_csv(a.anchors, dtype={'field_id': str}), as_of=a.as_of,
                bin_days=a.bin_days, horizon_days=a.horizon_days)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(a.output, **d)
    print(f'Wrote {len(d["X"])} elapsed anchored horizons; scores available at bin close')


if __name__ == '__main__':
    main()
