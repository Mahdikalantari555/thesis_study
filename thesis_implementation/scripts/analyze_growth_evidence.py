#!/usr/bin/env python3
"""Summarize weather and neighboring events as consistency evidence, not ground truth."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd


def analyze(events, weather, *, reference_end, variables, edges=None, model_weather='unknown', min_reference=3):
    e = events.copy(); w = weather.copy()
    required_e = {'event_id', 'field_id', 'start_date', 'end_date'}
    required_w = {'field_id', 'date', *variables}
    if not required_e.issubset(e.columns) or not required_w.issubset(w.columns):
        raise ValueError('events or weather columns missing')
    if model_weather not in ('yes', 'no', 'unknown') or min_reference < 1:
        raise ValueError('invalid evidence settings')
    e['field_id'] = e['field_id'].astype(str); w['field_id'] = w['field_id'].astype(str)
    e['start_date'] = pd.to_datetime(e['start_date'], errors='raise').dt.normalize()
    e['end_date'] = pd.to_datetime(e['end_date'], errors='raise').dt.normalize()
    w['date'] = pd.to_datetime(w['date'], errors='raise').dt.normalize()
    cutoff = pd.Timestamp(reference_end).normalize()
    if e[['start_date', 'end_date']].isna().any().any() or w['date'].isna().any():
        raise ValueError('missing dates are not allowed')
    if (e['start_date'] > e['end_date']).any() or (e['start_date'] <= cutoff).any():
        raise ValueError('events must be valid and strictly after historical reference')
    if e['event_id'].isna().any() or e['event_id'].duplicated().any() or w.duplicated(['field_id', 'date']).any():
        raise ValueError('duplicate or missing event IDs or weather field/dates')
    for var in variables:
        w[var] = pd.to_numeric(w[var], errors='raise')
    # Same calendar month / field, historical observations only. No interpolation.
    w['month'] = w['date'].dt.month
    ref = w[w.date <= cutoff]
    climatology = ref.groupby(['field_id', 'month'])[variables].agg(['mean', 'count'])
    adj = {}
    if edges is not None:
        if not {'field_id', 'neighbor_id'}.issubset(edges.columns):
            raise ValueError('edges requires field_id and neighbor_id')
        for a, b in zip(edges.field_id.astype(str), edges.neighbor_id.astype(str)):
            if a != b:
                adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
    result = []
    for _, row in e.iterrows():
        subset = w[(w.field_id == row.field_id) & w.date.between(row.start_date, row.end_date)]
        evidence = {}
        for var in variables:
            current = []; baselines = []
            for obs in subset.itertuples(index=False):
                value = getattr(obs, var)
                key = (row.field_id, obs.month)
                if not np.isfinite(value) or key not in climatology.index:
                    continue
                mean = climatology.loc[key, (var, 'mean')]
                count = climatology.loc[key, (var, 'count')]
                if count >= min_reference and np.isfinite(mean):
                    current.append(float(value)); baselines.append(float(mean))
            evidence[var] = {'matched_observations': len(current),
                             'event_mean': float(np.mean(current)) if current else None,
                             'historical_same_month_mean': float(np.mean(baselines)) if current else None,
                             'mean_difference': float(np.mean(np.array(current)-np.array(baselines))) if current else None}
        neighbors = adj.get(row.field_id, set())
        matching = e[(e.field_id.isin(neighbors)) & (e.start_date <= row.end_date) & (e.end_date >= row.start_date)]
        result.append({'event_id': str(row.event_id), 'field_id': row.field_id,
                       'start_date': row.start_date.strftime('%Y-%m-%d'),
                       'end_date': row.end_date.strftime('%Y-%m-%d'),
                       'event_days': int((row.end_date-row.start_date).days + 1),
                       'weather_observation_days': int(len(subset)), 'weather': evidence,
                       'known_neighbors': len(neighbors), 'neighbors_with_overlapping_events': int(matching.field_id.nunique()),
                       'neighbor_event_ids': matching.event_id.astype(str).tolist()})
    return {'protocol': {'reference_end': str(cutoff.date()), 'reference': 'same_field_same_calendar_month',
                         'minimum_reference_observations': min_reference,
                         'model_uses_weather': model_weather,
                         'independence': 'not_assured_review_sources_and_model_inputs',
                         'interpretation': 'descriptive_consistency_not_causal_or_stress_ground_truth'},
            'events': result}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--events', required=True, type=Path)
    p.add_argument('--weather', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--reference-end', required=True)
    p.add_argument('--variables', required=True, help='comma-separated numeric weather columns')
    p.add_argument('--edges', type=Path, help='CSV field_id,neighbor_id; externally defined adjacency')
    p.add_argument('--model-uses-weather', choices=['yes', 'no', 'unknown'], default='unknown')
    p.add_argument('--min-reference', type=int, default=3)
    a = p.parse_args()
    variables = a.variables.split(',')
    if any(not v or not v.isidentifier() for v in variables):
        p.error('variables must be valid column identifiers')
    read = lambda path: pd.read_csv(path, dtype={'field_id': str, 'neighbor_id': str, 'event_id': str})
    result = analyze(read(a.events), read(a.weather), reference_end=a.reference_end, variables=variables,
                     edges=read(a.edges) if a.edges else None, model_weather=a.model_uses_weather,
                     min_reference=a.min_reference)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False))
    print(f'Wrote evidence for {len(result["events"])} events to {a.output}')


if __name__ == '__main__':
    main()
