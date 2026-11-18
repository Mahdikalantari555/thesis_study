#!/usr/bin/env python3
"""Export actual Zarr weather observations without interpolation or imputation."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--zarr', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--variables', required=True, help='comma-separated exact Zarr data variable names')
    p.add_argument('--allow-shared-weather', action='store_true',
                   help='explicitly replicate region-wide time series across fields')
    a = p.parse_args()
    variables = a.variables.split(',')
    if not variables or any(not v for v in variables) or len(set(variables)) != len(variables):
        p.error('variables must be non-empty and unique')
    ds = xr.open_zarr(a.zarr)
    fields = np.asarray(ds.field.values).astype(str)
    times = pd.to_datetime(ds.time.values).normalize()
    if times.isna().any() or times.duplicated().any() or len(set(fields)) != len(fields):
        raise ValueError('field IDs and observation days must be unique and valid')
    frame = pd.DataFrame({'field_id': np.repeat(fields, len(times)),
                          'date': np.tile(times.strftime('%Y-%m-%d'), len(fields))})
    for var in variables:
        if var not in ds:
            raise ValueError(f'weather variable {var!r} is absent; no fallback')
        da = ds[var]
        if set(da.dims) == {'field', 'time'} and da.ndim == 2:
            values = da.transpose('field', 'time').values
        elif da.dims == ('time',) and a.allow_shared_weather:
            values = np.broadcast_to(da.values, (len(fields), len(times)))
        elif da.dims == ('time',):
            raise ValueError(f'{var} is shared across fields; explicitly use --allow-shared-weather')
        else:
            raise ValueError(f'unsupported dimensions for {var}: {da.dims}')
        frame[var] = np.asarray(values, dtype=float).reshape(-1)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(a.output, index=False)
    print(f'Wrote {len(frame)} field/date rows from existing observations; no gap filling')


if __name__ == '__main__':
    main()
