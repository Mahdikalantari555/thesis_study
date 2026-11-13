#!/usr/bin/env python3
"""Export original unmodified test alert runs for descriptive evidence analysis."""
import argparse
import csv
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report', required=True, type=Path)
    p.add_argument('--model', required=True)
    p.add_argument('--subset', choices=['temporal_test', 'spatial_test'], required=True)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    report = json.loads(a.report.read_text())
    rows = report['models'][a.model].get(a.subset + '_original_events', [])
    if any(not r['start_date'] or not r['end_date'] for r in rows):
        raise ValueError('report lacks bin dates; prepare input with prepare_growth_validation.py')
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['event_id', 'field_id', 'start_date', 'end_date'], extrasaction='ignore')
        writer.writeheader(); writer.writerows(rows)
    print(f'Wrote {len(rows)} original alert runs to {a.output}')


if __name__ == '__main__':
    main()
