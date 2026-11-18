"""Landsat QA_PIXEL masking and per-scene band loading.

Implements Collection-2 Level-2 QA_PIXEL bit unpacking per the USGS docs:
- Bit 1: Dilated cloud
- Bit 2: Cirrus
- Bit 3: Cloud
- Bit 4: Cloud shadow
- Bit 5: Snow
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..config import QualityCfg

log = logging.getLogger("ssl_anomaly.io.landsat")

# Landsat 8/9 surface reflectance band names in standard order
STANDARD_SR_BANDS = ("SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7")
STANDARD_ST_BANDS = ("ST_B10",)


@dataclass
class SceneMeta:
    scene_id: str
    sensor: str  # "L8" or "L9"
    path: Path
    timestamp: np.datetime64  # acquisition date


def parse_scene_id(scene_id: str) -> dict:
    """Parse a Landsat Collection 2 scene ID (e.g. LC08_L2SP_166039_20230615_...)."""
    parts = scene_id.split("_")
    sensor_code = parts[0]
    sensor = "L8" if sensor_code.startswith("LC08") else "L9" if sensor_code.startswith("LC09") else "LX"
    date = parts[3] if len(parts) > 3 else ""
    return {"sensor": sensor, "date": date}


def quality_mask(qa_pixel: np.ndarray, cfg: QualityCfg) -> np.ndarray:
    """Return boolean mask (True = VALID pixel; False = cloud/shadow/cirrus/snow).

    Bits follow Landsat C2 L2 QA_PIXEL specification.
    """
    qa = qa_pixel.astype(np.uint16)
    bad = np.zeros_like(qa, dtype=bool)
    # Bit 0: Fill (no-data) pixels are never valid.
    bad |= (qa & 1) == 1
    if cfg.dilated_cloud:
        bad |= ((qa >> cfg.bits_dilated_cloud) & 1) == 1
    if cfg.cirrus:
        bad |= ((qa >> cfg.bits_cirrus) & 1) == 1
    if cfg.cloud:
        bad |= ((qa >> cfg.bits_cloud) & 1) == 1
    if cfg.cloud_shadow:
        bad |= ((qa >> cfg.bits_cloud_shadow) & 1) == 1
    if cfg.snow:
        bad |= ((qa >> cfg.bits_snow) & 1) == 1
    return ~bad


def apply_scale_sr(arr: np.ndarray, scale: float, offset: float) -> np.ndarray:
    """Apply scale/offset to surface reflectance; set nodata (0) and saturated
    values (>1) to NaN.

    The saturation test is applied AFTER scaling. Testing the raw DN against
    1.6 (as this function used to) marks every DN as saturated — DN values are
    in the thousands — and turns every raw scene into all-NaN.
    """
    src = arr.astype(np.float32)
    out = src * scale + offset
    out[(arr == 0) | ~np.isfinite(src)] = np.nan          # nodata stays NaN
    out[(out < -0.1) | (out > 1.2)] = np.nan              # saturated / invalid
    return out


def apply_scale_st(arr: np.ndarray, scale: float, offset: float) -> np.ndarray:
    """Apply scale/offset to surface temperature (Kelvin); set nodata to NaN."""
    out = arr.astype(np.float32) * scale + offset
    out[arr == 0] = np.nan
    return out


def load_scene(
    scene_dir: str | Path,
    bands: list[str],
    cfg: QualityCfg,
    scale_sr: float = 0.0000275,
    offset_sr: float = -0.2,
    scale_st: float = 0.00341802,
    offset_st: float = 149.0,
) -> tuple[dict[str, np.ndarray], np.ndarray, SceneMeta] | None:
    """Load bands + QA_PIXEL for one scene. Returns (bands_dict, valid_mask, meta).

    Returns None if the scene directory or required files are missing.
    """
    import rasterio

    scene_dir = Path(scene_dir)
    if not scene_dir.exists():
        log.warning("Scene directory not found: %s", scene_dir)
        return None

    # Find files by suffix (Landsat C2 naming *_SR_B2.TIF, *_QA_PIXEL.TIF, ...)
    tifs = list(scene_dir.glob("*.TIF")) + list(scene_dir.glob("*.tif"))
    if not tifs:
        log.warning("No TIFs in %s", scene_dir)
        return None

    by_suffix: dict[str, Path] = {}
    for p in tifs:
        # Last underscore-delimited token before extension is the band name
        stem = p.stem
        if "_" in stem:
            suffix = stem.rsplit("_", 1)[-1]
            by_suffix[suffix] = p
        else:
            by_suffix[stem] = p

    if "QA_PIXEL" not in by_suffix:
        log.warning("Scene %s missing QA_PIXEL; skipping", scene_dir.name)
        return None

    # Read QA
    with rasterio.open(by_suffix["QA_PIXEL"]) as src:
        qa = src.read(1)

    valid = quality_mask(qa, cfg)

    out_bands: dict[str, np.ndarray] = {}
    for b in bands:
        if b not in by_suffix:
            log.warning("Scene %s missing band %s; skipping band", scene_dir.name, b)
            continue
        with rasterio.open(by_suffix[b]) as src:
            arr = src.read(1)
        if b.startswith("ST_"):
            out_bands[b] = apply_scale_st(arr, scale_st, offset_st)
        else:
            out_bands[b] = apply_scale_sr(arr, scale_sr, offset_sr)

    if not out_bands:
        return None

    scene_id = scene_dir.name
    info = parse_scene_id(scene_id)
    try:
        ts = np.datetime64(info["date"][:4] + "-" + info["date"][4:6] + "-" + info["date"][6:8])
    except Exception:
        # Fallback: use directory mtime
        ts = np.datetime64(int(scene_dir.stat().st_mtime), "s")

    meta = SceneMeta(scene_id=scene_id, sensor=info["sensor"], path=scene_dir, timestamp=ts)
    return out_bands, valid, meta
