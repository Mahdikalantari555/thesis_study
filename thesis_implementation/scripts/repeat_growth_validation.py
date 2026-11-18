#!/usr/bin/env python3
"""Repeat a fixed growth benchmark over seeds; do not select seeds by test results."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import numpy as np


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', required=True, type=Path)
    p.add_argument('--output-dir', required=True, type=Path)
    p.add_argument('--band', required=True, type=int)
    p.add_argument('--seeds', default='42,43,44')
    p.add_argument('--models', default='phase_mad,field_phase_mad,window_iforest,window_ocsvm,gru_ae,masked_transformer')
    p.add_argument('--epochs', default=15, type=int)
    p.add_argument('--spatial-layout', type=Path)
    p.add_argument('--holdout-fields', default='')
    p.add_argument('--train-end', default='2021-12-31')
    p.add_argument('--val-end', default='2023-12-31')
    p.add_argument('--test-end', default='2026-12-31')
    p.add_argument('--quantile', type=float, default=.95)
    p.add_argument('--bootstrap', type=int, default=500)
    a = p.parse_args()
    seeds = [int(s) for s in a.seeds.split(',')]
    if not seeds or len(set(seeds)) != len(seeds):
        p.error('seeds must be non-empty and unique')
    a.output_dir.mkdir(parents=True, exist_ok=True)
    runner = Path(__file__).with_name('validate_growth.py')
    reports = []
    for seed in seeds:
        out = a.output_dir / f'seed_{seed}.json'
        cmd = [sys.executable, str(runner), '--input', str(a.input), '--output', str(out),
               '--band', str(a.band), '--seed', str(seed), '--models', a.models,
               '--epochs', str(a.epochs), '--train-end', a.train_end, '--val-end', a.val_end,
               '--test-end', a.test_end, '--quantile', str(a.quantile), '--bootstrap', str(a.bootstrap)]
        if a.spatial_layout:
            cmd += ['--spatial-layout', str(a.spatial_layout)]
        if a.holdout_fields:
            cmd += ['--holdout-fields', a.holdout_fields]
        subprocess.run(cmd, check=True)
        reports.append(json.loads(out.read_text()))
    by_key = {}
    for seed, report in zip(seeds, reports):
        for model, data in report['models'].items():
            for scenario in data['scenarios']:
                key = (model, scenario['subset'], scenario['kind'], scenario['magnitude'],
                       scenario['phase'], scenario['duration_bins'])
                by_key.setdefault(key, []).append((seed, scenario['event_recall']))
    rows = []
    for key, vals in sorted(by_key.items()):
        finite = [v for _, v in vals if v is not None]
        rows.append({'model': key[0], 'subset': key[1], 'kind': key[2], 'magnitude': key[3],
                     'phase': key[4], 'duration_bins': key[5],
                     'event_recall_by_seed': {str(s): v for s,v in vals},
                     'mean_event_recall': float(np.mean(finite)) if finite else None,
                     'std_event_recall': float(np.std(finite, ddof=1)) if len(finite) > 1 else None})
    result = {'seeds': seeds, 'interpretation': 'descriptive_test_seed_variability_not_selection', 'scenarios': rows}
    (a.output_dir / 'seed_summary.json').write_text(json.dumps(result, indent=2, allow_nan=False))
    print(f'Wrote {len(seeds)} runs and seed_summary.json')


if __name__ == '__main__':
    main()
