"""Build the scene index manifest for the RGB/NDVI tile layer.

Scans the raw Landsat scene directories (each ``landsat_YYYYMMDD_PPP_RRR``
folder holds one band GeoTIFF per spectral band plus ``MTL.json``), reads the
acquisition date from MTL.json and the scene bounds from the red band header
(reprojected to EPSG:4326 for the manifest), and emits
``platform/src/data/scenes_index.json`` in the format fixed by the
``add-rgb-ndvi-tile-layer`` design (date, path, bounds, bands, has_rgb,
has_ndvi), sorted by date so the artifact is deterministic.

Only per-scene header reads happen here (MTL.json + one band header), so a
full 607-scene run takes seconds, not minutes. The manifest is informational
for the frontend (which dates exist, where they are); the tile server resolves
paths from ``--scenes-dir`` at request time.

Usage:
    python scripts/build_tile_index.py \
        --scenes-dir D:/RS/Thesis/Data/Metric/scenes \
        --out platform/src/data/scenes_index.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import warnings
from pathlib import Path

# rasterio emits a benign "GDAL_DATA is not defined" warning on this machine.
warnings.filterwarnings("ignore")

from pyproj import Transformer
import rasterio

# Canonical band order for the manifest (matches the design example); any
# extra GeoTIFFs found in a scene dir are appended alphabetically at the end.
CANONICAL_BANDS = ["blue", "green", "red", "nir08", "swir16", "swir22", "lwir11", "qa_pixel"]

# Scene dirs are named landsat_YYYYMMDD_PPP_RRR (used as the date fallback and
# as a sanity filter so stray folders under scenes/ are skipped).
SCENE_DIR_RE = re.compile(r"^landsat_(\d{4})(\d{2})(\d{2})_\d{3}_\d{3}$")

RGB_BANDS = ("blue", "green", "red")
NDVI_BANDS = ("red", "nir08")

WGS84 = "EPSG:4326"


def parse_mtl_date(scene_dir: Path) -> str | None:
    """Read the acquisition date (``YYYY-MM-DD``) from a scene's MTL.json.

    MTL.json here is the USGS collection-2 STAC-wrapped metadata: the date
    lives in ``properties.datetime`` and/or
    ``METADATA.PRODUCT_METADATA.ACQUISITION_DATE``. Both are tried, then a
    regex sweep as a last resort before falling back to the directory name.
    """
    mtl_path = scene_dir / "MTL.json"
    if not mtl_path.exists():
        return None
    try:
        mtl = json.loads(mtl_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    product = mtl.get("METADATA", {}).get("PRODUCT_METADATA", {})
    for key in ("ACQUISITION_DATE", "DATE_ACQUIRED", "SCENE_CENTER_TIME"):
        raw = product.get(key)
        if isinstance(raw, str) and (match := re.match(r"(\d{4}-\d{2}-\d{2})", raw)):
            return match.group(1)
    raw = mtl.get("properties", {}).get("datetime")
    if isinstance(raw, str) and (match := re.match(r"(\d{4}-\d{2}-\d{2})", raw)):
        return match.group(1)
    # Text sweep over the whole document (key names vary across collections).
    match = re.search(r'"(?:ACQUISITION_DATE|DATE_ACQUIRED)"\s*:\s*"(\d{4}-\d{2}-\d{2})', mtl_path.read_text(encoding="utf-8", errors="ignore"))
    return match.group(1) if match else None


def scene_date(scene_dir: Path) -> str | None:
    """Acquisition date for a scene dir: MTL.json first, dir name fallback."""
    return parse_mtl_date(scene_dir) or _date_from_dir_name(scene_dir.name)


def _date_from_dir_name(name: str) -> str | None:
    match = SCENE_DIR_RE.match(name)
    if not match:
        return None
    year, month, day = match.groups()
    return f"{year}-{month}-{day}"


def scene_bounds(scene_dir: Path, bands: list[str]) -> list[float] | None:
    """Scene bounds as ``[xmin, ymin, xmax, ymax]`` in EPSG:4326.

    Reads the header of the red band (falling back to the first available
    band) and reprojects its UTM bounds with pyproj. Header-only, no pixels.
    """
    # Red band first when present (it defines every scene's grid), else any band.
    order = list(dict.fromkeys(("red", *bands)))
    for band in order:
        try:
            with rasterio.open(scene_dir / f"{band}.tif") as src:
                transformer = Transformer.from_crs(src.crs, WGS84, always_xy=True)
                xmin, ymin, xmax, ymax = src.bounds
        except Exception:  # rasterio raises RasterioIOError (an OSError subclass)
            continue
        left, bottom = transformer.transform(xmin, ymin)
        right, top = transformer.transform(xmax, ymax)
        return [round(left, 6), round(bottom, 6), round(right, 6), round(top, 6)]
    return None


def list_bands(scene_dir: Path) -> list[str]:
    """Band names present in the scene dir, in canonical order."""
    present = {p.stem for p in scene_dir.glob("*.tif")}
    ordered = [b for b in CANONICAL_BANDS if b in present]
    ordered += sorted(present - set(CANONICAL_BANDS))
    return ordered


def build_index(scenes_dir: Path, limit: int | None = None) -> dict:
    """Build the manifest dict: ``{"scenes": [...]}``, sorted by date then dir."""
    if not scenes_dir.is_dir():
        raise SystemExit(f"scenes dir not found: {scenes_dir}")
    # Path anchor mirrors the design example: "Data/Metric/scenes/<scene>/"
    # relative to the grandparent of the scenes dir's parent (i.e. the tree
    # root that contains Data/Metric/scenes).
    anchor = scenes_dir.parents[2]

    scenes: list[dict] = []
    scene_dirs = sorted(p for p in scenes_dir.iterdir() if p.is_dir() and SCENE_DIR_RE.match(p.name))
    for scene_dir in scene_dirs:
        bands = list_bands(scene_dir)
        if not bands:
            continue  # nothing usable to tile
        date = scene_date(scene_dir)
        if date is None:
            continue
        bounds = scene_bounds(scene_dir, bands)
        if bounds is None:
            continue
        has = set(bands)
        try:
            rel_path = scene_dir.relative_to(anchor).as_posix() + "/"
        except ValueError:
            rel_path = scene_dir.as_posix() + "/"
        scenes.append({
            "date": date,
            "path": rel_path,
            "bounds": bounds,
            "bands": bands,
            "has_rgb": all(b in has for b in RGB_BANDS),
            "has_ndvi": all(b in has for b in NDVI_BANDS),
        })
        if limit is not None and len(scenes) >= limit:
            break

    scenes.sort(key=lambda s: (s["date"], s["path"]))
    return {"scenes": scenes}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scenes-dir", default="D:/RS/Thesis/Data/Metric/scenes")
    ap.add_argument("--out", default="platform/src/data/scenes_index.json")
    ap.add_argument("--limit", type=int, default=None, help="index only the first N scenes (tests)")
    args = ap.parse_args()

    index = build_index(Path(args.scenes_dir), limit=args.limit)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    n = len(index["scenes"])
    print(f"wrote {n} scenes to {out_path}")


if __name__ == "__main__":
    sys.exit(main())
