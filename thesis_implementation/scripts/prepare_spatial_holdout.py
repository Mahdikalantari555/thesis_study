#!/usr/bin/env python3
"""Create a predeclared spatial block holdout from projected field centroids."""
import argparse
import importlib.util
import json
from pathlib import Path
import pandas as pd

path = Path(__file__).resolve().parents[1] / 'src/ssl_anomaly/eval/growth_validation.py'
spec = importlib.util.spec_from_file_location('growth_validation', path)
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fields', required=True, type=Path, help='CSV field_id,x,y in a projected CRS')
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--crs', required=True, help='projected CRS identifier, e.g. EPSG:32639')
    p.add_argument('--block-size', required=True, type=float)
    p.add_argument('--origin-x', required=True, type=float)
    p.add_argument('--origin-y', required=True, type=float)
    p.add_argument('--holdout-block', required=True, action='append', help='block indices x,y; repeatable')
    p.add_argument('--buffer', default=0, type=float, help='exclude centroids this distance from holdout centroids')
    a = p.parse_args()
    d = pd.read_csv(a.fields, dtype={'field_id': str})
    if not {'field_id', 'x', 'y'}.issubset(d.columns) or d.field_id.isna().any():
        p.error('fields CSV requires field_id,x,y and no missing IDs')
    try:
        blocks = [tuple(int(i) for i in b.split(',')) for b in a.holdout_block]
        if any(len(b) != 2 for b in blocks):
            raise ValueError
    except ValueError:
        p.error('each --holdout-block must be two integer indices x,y')
    layout = g.geographic_holdout(d.field_id, d.x, d.y, block_size=a.block_size, origin_x=a.origin_x,
                                  origin_y=a.origin_y, holdout_blocks=blocks, buffer=a.buffer)
    layout['geometry'] = {'crs': a.crs, 'coordinates': 'field_centroids', 'block_size': a.block_size,
                          'origin_x': a.origin_x, 'origin_y': a.origin_y, 'holdout_blocks': blocks,
                          'buffer_centroid_distance': a.buffer}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(layout, indent=2, allow_nan=False))
    print(f'Wrote {a.output}; {len(layout["holdout_fields"])} holdout and {len(layout["excluded_fields"])} buffered fields')


if __name__ == '__main__':
    main()
