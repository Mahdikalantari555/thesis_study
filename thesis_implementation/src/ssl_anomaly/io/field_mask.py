"""Build (or load) a 30 m raster mask mapping pixel → field_id.

The mask is built ONCE and reused for every scene (spec L1). It uses rasterio
features rasterize to burn field polygon IDs into a grid aligned to the
Landsat tile (EPSG:32639, 30 m) for zonal ``bincount``.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

log = logging.getLogger("ssl_anomaly.io.field_mask")


def _read_fields(fields_path: str | Path):
    """Load field polygons from GPKG/GeoJSON/Shapefile via geopandas."""
    import geopandas as gpd

    return gpd.read_file(fields_path)


def build_field_mask(
    fields_path: str | Path,
    out_path: str | Path,
    *,
    pixel_size: float = 30.0,
    crs: str = "EPSG:32639",
    id_col: str = "field_id",
    force: bool = False,
) -> dict:
    """Rasterize field polygons to ``out_path`` (single-band uint32 GeoTIFF).

    Returns metadata dict (shape, transform, field_ids). If ``out_path`` exists
    and ``force`` is False, simply returns the existing mask metadata without
    rebuilding (mask reuse per spec L1).
    """
    out_path = Path(out_path)
    if out_path.exists() and not force:
        log.info("Field mask exists at %s; reusing (set force=True to rebuild)", out_path)
        return _load_mask_metadata(out_path)

    import rasterio
    from rasterio import features
    from rasterio.transform import from_bounds

    fields_path = Path(fields_path)
    if not fields_path.exists():
        raise FileNotFoundError(f"Field polygons not found: {fields_path}")

    gdf = _read_fields(fields_path)
    if gdf.crs is None:
        raise ValueError(f"Field file {fields_path} has no CRS; cannot rasterize")

    gdf = gdf.to_crs(crs)

    if id_col not in gdf.columns:
        # Fall back to row-index-based id
        log.warning("id_col=%r not in fields; using sequential id", id_col)
        gdf = gdf.reset_index(drop=True)
        gdf[id_col] = np.arange(1, len(gdf) + 1, dtype=np.uint32)

    minx, miny, maxx, maxy = gdf.total_bounds
    # Snap to pixel grid
    width = int(np.ceil((maxx - minx) / pixel_size))
    height = int(np.ceil((maxy - miny) / pixel_size))
    # Adjust bounds to integer pixel dimensions
    transform = from_bounds(minx, miny, minx + width * pixel_size, miny + height * pixel_size, width, height)

    shapes = (
        (geom, int(fid))
        for geom, fid in zip(gdf.geometry.values, gdf[id_col].astype(int).values)
    )

    mask = np.zeros((height, width), dtype=np.uint32)
    features.rasterize(
        shapes=shapes,
        out=mask,
        transform=transform,
        dtype=np.uint32,
        fill=0,
        all_touched=False,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "uint32",
        "crs": crs,
        "transform": transform,
        "compress": "lzw",
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(mask, 1)

    field_ids = np.unique(mask[mask > 0])
    log.info(
        "Wrote field mask to %s: shape=(%d,%d), %d fields", out_path, height, width, len(field_ids)
    )
    return {
        "path": str(out_path),
        "shape": (height, width),
        "transform": transform,
        "crs": crs,
        "field_ids": field_ids.astype(np.int64),
        "id_col": id_col,
    }


def _load_mask_metadata(path: Path) -> dict:
    import rasterio

    with rasterio.open(path) as src:
        mask = src.read(1)
        return {
            "path": str(path),
            "shape": src.shape,
            "transform": src.transform,
            "crs": str(src.crs),
            "field_ids": np.unique(mask[mask > 0]).astype(np.int64),
        }


def load_field_mask(path: str | Path) -> tuple[np.ndarray, dict]:
    """Load the mask array and metadata. Returns (mask_uint32, meta)."""
    import rasterio

    with rasterio.open(path) as src:
        mask = src.read(1).astype(np.uint32)
        meta = {
            "shape": src.shape,
            "transform": src.transform,
            "crs": str(src.crs),
            "field_ids": np.unique(mask[mask > 0]).astype(np.int64),
        }
    return mask, meta
