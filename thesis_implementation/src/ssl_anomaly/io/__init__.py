"""IO: Landsat ingest, field mask, zonal stats, zarr aggregation."""

from __future__ import annotations

from .era5 import (
    compute_dynamic_gdd_from_era5,
    extract_era5_from_fields_zarr,
    load_era5_zarr,
    write_era5_zarr,
)
from .field_mask import build_field_mask
from .stats_zarr import StatsZarrReader, load_stats_zarr
from .zarr_store import FIELDS_ZARR_BANDS, aggregate_to_zarr
from .zonal import zonal_scene

__all__ = [
    "FIELDS_ZARR_BANDS",
    "aggregate_to_zarr",
    "build_field_mask",
    "compute_dynamic_gdd_from_era5",
    "extract_era5_from_fields_zarr",
    "load_era5_zarr",
    "load_stats_zarr",
    "StatsZarrReader",
    "write_era5_zarr",
    "zonal_scene",
]
