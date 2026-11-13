"""Standalone daily ERA5 / meteorological Zarr v3 store with dynamic T_base GDD.

Per ``docs/final_plan.md`` §3.1–3.2, meteorological variables (``tmean``, ``et0``,
``rad``, ``rh``, ``precip``) live in a separate daily ``era5.zarr`` store without
hard-coding a single fixed GDD base temperature; cumulative GDD is computed on the
fly for any ``t_base`` and ``t_cap`` hyperparameter.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import xarray as xr

RAW_WEATHER_VARS = ("tmean", "et0", "rad", "rh")


def write_era5_zarr(
    times: np.ndarray,
    variables: dict[str, np.ndarray],
    out_path: str | Path,
) -> Path:
    """Write daily meteorological arrays ``(time,)`` to a standalone Zarr v3 store."""
    t_raw = np.asarray(times, dtype="datetime64[D]")
    order = np.argsort(t_raw)
    t_sorted = t_raw[order]

    # Interpolate onto a continuous 1-day grid so dynamic GDD integration is exact
    t0 = t_sorted[0]
    t1 = t_sorted[-1]
    daily_times = np.arange(t0, t1 + np.timedelta64(1, "D"), np.timedelta64(1, "D"))
    obs_days = (t_sorted - t0).astype("timedelta64[D]").astype(np.float64)
    grid_days = (daily_times - t0).astype("timedelta64[D]").astype(np.float64)

    data_vars: dict[str, tuple[tuple[str], np.ndarray]] = {}
    for name, vals in variables.items():
        v = np.asarray(vals, dtype=np.float64)[order]
        fin = np.isfinite(v)
        if int(fin.sum()) >= 2:
            daily_v = np.interp(grid_days, obs_days[fin], v[fin]).astype(np.float32)
        elif int(fin.sum()) == 1:
            daily_v = np.full(daily_times.size, float(v[fin][0]), dtype=np.float32)
        else:
            daily_v = np.zeros(daily_times.size, dtype=np.float32)
        data_vars[name] = (("time",), daily_v)

    ds = xr.Dataset(
        data_vars=data_vars,
        coords={"time": daily_times.astype("datetime64[ns]")},
        attrs={"store_version": "1.0", "description": "Daily agro-meteorological store (GDD computed dynamically)"},
    )
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    ds.to_zarr(str(out), mode="w", zarr_format=3, consolidated=False)
    return out


def extract_era5_from_fields_zarr(
    fields_zarr_path: str | Path = "data/processed/fields.zarr",
    era5_zarr_path: str | Path = "data/processed/era5.zarr",
) -> Path:
    """Populate standalone ``era5.zarr`` from weather series stored in ``fields.zarr``."""
    ds = xr.open_zarr(str(fields_zarr_path), consolidated=False)
    times = ds.coords["time"].values
    vars_dict: dict[str, np.ndarray] = {}
    for short in RAW_WEATHER_VARS:
        col = f"weather_{short}"
        if col in ds.data_vars:
            vars_dict[short] = ds[col].values
    return write_era5_zarr(times, vars_dict, era5_zarr_path)


def load_era5_zarr(era5_zarr_path: str | Path) -> xr.Dataset:
    """Open standalone ``era5.zarr`` store."""
    return xr.open_zarr(str(era5_zarr_path), consolidated=False)


def compute_dynamic_gdd_from_era5(
    era5_ds: xr.Dataset,
    start_time: np.datetime64,
    query_times: np.ndarray,
    *,
    t_base: float = 12.0,
    t_cap: float | None = 36.0,
) -> np.ndarray:
    """Compute cumulative GDD since ``start_time`` at ``query_times`` for arbitrary ``t_base``."""
    store_t = era5_ds.coords["time"].values.astype("datetime64[D]")
    tmean = era5_ds["tmean"].values.astype(np.float64)
    t_start = np.datetime64(start_time, "D")
    q_t = np.asarray(query_times, dtype="datetime64[D]")
    t_end = max(t_start, q_t.max()) if q_t.size else t_start

    grid = np.arange(t_start, t_end + np.timedelta64(1, "D"), np.timedelta64(1, "D"))
    store_days = (store_t - store_t[0]).astype("timedelta64[D]").astype(np.float64)
    grid_days = (grid - store_t[0]).astype("timedelta64[D]").astype(np.float64)
    daily_t = np.interp(grid_days, store_days, tmean)

    daily_gdd = np.maximum(0.0, daily_t - float(t_base))
    if t_cap is not None:
        daily_gdd = np.minimum(daily_gdd, max(0.0, float(t_cap) - float(t_base)))
    cum = np.cumsum(daily_gdd)
    cum = cum - cum[0]

    q_days = (np.clip(q_t, t_start, t_end) - t_start).astype("timedelta64[D]").astype(np.int64)
    return cum[np.clip(q_days, 0, cum.size - 1)]
