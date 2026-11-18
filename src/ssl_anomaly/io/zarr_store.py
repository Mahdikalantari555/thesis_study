"""Aggregate per-scene zonal Parquet files into ``fields.zarr`` (field x time x band).

v2 is used here (compatible with xarray's Zarr backend) rather than v3 because
the Python zarr v3 API was still stabilizing at implementation time; the store
is documented as v2 and can be migrated to v3 when ready per spec.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

log = logging.getLogger("ssl_anomaly.io.zarr_store")

FIELDS_ZARR_BANDS = (
    "SR_B2",
    "SR_B3",
    "SR_B4",
    "SR_B5",
    "SR_B6",
    "SR_B7",
    "ST_B10",
)


def _discover_scenes(zonal_dir: Path) -> list[Path]:
    files = sorted(zonal_dir.glob("*.parquet"))
    return [f for f in files if not f.name.endswith(".tmp")]


def _load_scene_tables(zonal_dir: Path) -> pd.DataFrame:
    files = _discover_scenes(zonal_dir)
    if not files:
        raise FileNotFoundError(f"No zonal parquet files in {zonal_dir}")
    frames = []
    for p in files:
        try:
            frames.append(pd.read_parquet(p))
        except Exception as exc:  # corrupt parquet → skip with warning
            log.warning("Skipping unreadable zonal parquet %s: %s", p.name, exc)
    df = pd.concat(frames, ignore_index=True)
    return df


def aggregate_to_zarr(
    zonal_dir: str | Path,
    out_path: str | Path,
    *,
    bands: tuple[str, ...] = FIELDS_ZARR_BANDS,
    field_parquet: str | Path | None = None,
    mode: str = "w",
) -> xr.Dataset:
    """Aggregate per-scene zonal parquet → fields.zarr (field, time, band).

    The resulting dataset has:
      - ``median``   (field, time, band) float32  — per-field per-scene median
      - ``mean``     (field, time, band) float32
      - ``valid_frac`` (field, time)      float32
      - coords: field (int64), time (datetime64[ns]), band (str), sensor (time)
    """
    zonal_dir = Path(zonal_dir)
    out_path = Path(out_path)

    df = _load_scene_tables(zonal_dir)
    required = {"field", "timestamp", "valid_frac", "sensor"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Zonal frames missing required columns: {missing}")

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["field", "timestamp"]).reset_index(drop=True)

    # Build index
    fields = sorted(df["field"].unique())
    times = sorted(df["timestamp"].unique())
    band_list = list(bands)
    f_idx = {f: i for i, f in enumerate(fields)}
    t_idx = {t: i for i, t in enumerate(times)}
    n_f, n_t, n_b = len(fields), len(times), len(band_list)

    med = np.full((n_f, n_t, n_b), np.nan, dtype=np.float32)
    mean = np.full((n_f, n_t, n_b), np.nan, dtype=np.float32)
    vf = np.zeros((n_f, n_t), dtype=np.float32)
    sensor = np.full(n_t, "", dtype=object)

    for b_i, b in enumerate(band_list):
        m_col = f"{b}_median"
        mu_col = f"{b}_mean"
        sub = df[["field", "timestamp", "valid_frac", "sensor", m_col, mu_col]]
        for _, row in sub.iterrows():
            fi = f_idx[int(row.field)]
            ti = t_idx[row.timestamp]
            if m_col in df.columns and pd.notna(row[m_col]):
                med[fi, ti, b_i] = row[m_col]
            if mu_col in df.columns and pd.notna(row[mu_col]):
                mean[fi, ti, b_i] = row[mu_col]
            vf[fi, ti] = max(vf[fi, ti], float(row.valid_frac))
            if sensor[ti] == "":
                sensor[ti] = str(row.sensor)

    times_ns = np.array(times, dtype="datetime64[ns]")
    ds = xr.Dataset(
        {
            "median": (("field", "time", "band"), med),
            "mean": (("field", "time", "band"), mean),
            "valid_frac": (("field", "time"), vf),
        },
        coords={
            "field": np.array(fields, dtype=np.int64),
            "time": times_ns,
            "band": np.array(band_list, dtype=object),
            "sensor": (("time",), sensor),
        },
        attrs={
            "zarr_format": 2,
            "crs": "EPSG:32639",
            "pixel_size_m": 30.0,
            "n_fields": n_f,
            "n_times": n_t,
            "source": "ssl_anomaly.aggregate_to_zarr",
        },
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    ds.to_zarr(str(out_path), mode=mode, consolidated=True)
    log.info(
        "Wrote fields.zarr to %s: fields=%d times=%d bands=%d",
        out_path, n_f, n_t, n_b,
    )
    return ds


def load_fields_zarr(path: str | Path) -> xr.Dataset:
    return xr.open_zarr(str(path))
