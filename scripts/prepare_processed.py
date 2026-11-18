"""Prepare farm-level processed data under Data/Processed (PRD V1.0).

This script generates the *fast* artifacts (coordinates, weather, quality metadata,
scene inventory) and reorganizes existing processed outputs. Heavy extraction
(8-statistic band distributions, farm-masked pixels) is provided by
extract_stats.py / extract_pixels.py and is NOT run here.

Run:
    python scripts/prepare_processed.py
    python scripts/prepare_processed.py --staging D:/RS/Thesis/thesis_implementation/data/_staging
    python scripts/prepare_processed.py --out D:/RS/Thesis/Data/Processed   # if writable
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from rasterio.transform import array_bounds

DATA_ROOT = Path("D:/RS/Thesis/Data")
METRIC_ROOT = DATA_ROOT / "Metric"
WEATHER_ROOT = DATA_ROOT / "Weather"
ROI_ROOT = DATA_ROOT / "RoI"
DEFAULT_STAGING = Path("D:/RS/Thesis/thesis_implementation/data/_staging")
DEFAULT_OUT = DATA_ROOT / "Processed"


def make_dirs(root: Path) -> None:
    for sub in ("satellite", "weather", "indices", "coordinates", "manifests", "interim"):
        (root / sub).mkdir(parents=True, exist_ok=True)


def build_farms(root: Path) -> pd.DataFrame:
    gdf = gpd.read_file(ROI_ROOT / "Farms.geojson")
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    gdf = gdf.to_crs("EPSG:32639")
    if "field_id" not in gdf.columns:
        gdf = gdf.reset_index(drop=True)
        gdf["field_id"] = np.arange(1, len(gdf) + 1, dtype=np.int64)
    meta = pd.DataFrame({
        "field_id": gdf["field_id"].astype(int).values,
        "farm": gdf.get("Farm", pd.Series([""] * len(gdf))).astype(str).values,
        "block": gdf.get("block", pd.Series([""] * len(gdf))).astype(str).values,
        "variety": gdf.get("variete", pd.Series([""] * len(gdf))).astype(str).values,
        "age": pd.to_numeric(gdf.get("age", pd.Series([np.nan] * len(gdf))), errors="coerce").values,
        "status": gdf.get("status", pd.Series([""] * len(gdf))).astype(str).values,
        "management": gdf.get("management", pd.Series([""] * len(gdf))).astype(str).values,
        "office": gdf.get("office", pd.Series([""] * len(gdf))).astype(str).values,
        "area_ha": pd.to_numeric(gdf.get("area", pd.Series([np.nan] * len(gdf))), errors="coerce").values,
        "geometry_area_ha": (gdf.geometry.area / 1e4).values,
        "centroid_x": gdf.geometry.centroid.x.values,
        "centroid_y": gdf.geometry.centroid.y.values,
    })
    meta.to_parquet(root / "coordinates" / "farms.parquet", index=False)
    # also keep full geojson copy (subset-readable reference)
    gdf[["field_id", "geometry"]].to_file(root / "coordinates" / "farms.geojson", driver="GeoJSON")
    return meta


def build_field_mask(root: Path) -> tuple[np.ndarray, object, object]:
    ref_tif = sorted((METRIC_ROOT / "products" / "NDVI").glob("*.tif"))
    ref_tif = [p for p in ref_tif if "_interp" not in p.name][0]
    with rasterio.open(ref_tif) as src:
        transform = src.transform
        shape = src.shape
        crs = src.crs
    gdf = gpd.read_file(ROI_ROOT / "Farms.geojson")
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    gdf = gdf.to_crs(crs)
    if "field_id" not in gdf.columns:
        gdf = gdf.reset_index(drop=True)
        gdf["field_id"] = np.arange(1, len(gdf) + 1, dtype=np.int64)
    shapes = ((geom, int(fid)) for geom, fid in zip(gdf.geometry.values, gdf["field_id"].astype(int).values))
    mask = rasterize(shapes, out_shape=shape, transform=transform, fill=0, dtype="uint32", all_touched=False)
    (root / "interim").mkdir(parents=True, exist_ok=True)
    profile = {"driver": "GTiff", "height": shape[0], "width": shape[1], "count": 1,
               "dtype": "uint32", "crs": crs, "transform": transform, "compress": "lzw"}
    with rasterio.open(root / "interim" / "field_mask_full.tif", "w", **profile) as dst:
        dst.write(mask, 1)
    return mask, transform, crs


def build_farm_pixels(root: Path, mask: np.ndarray, transform) -> pd.DataFrame:
    inside = mask > 0
    rows, cols = np.where(inside)
    fields = mask[rows, cols]
    xs = transform.c + cols * transform.a + rows * transform.b
    ys = transform.f + cols * transform.d + rows * transform.e
    pix = pd.DataFrame({
        "field_id": fields.astype(np.int64),
        "pixel_id": np.arange(len(fields), dtype=np.int64),
        "row": rows.astype(np.int64),
        "col": cols.astype(np.int64),
        "x": np.asarray(xs, dtype=np.float64),
        "y": np.asarray(ys, dtype=np.float64),
    })
    # per-field local pixel index for subset reads
    pix["local_pixel"] = pix.groupby("field_id").cumcount().astype(np.int64)
    pix.to_parquet(root / "coordinates" / "farm_pixels.parquet", index=False)
    return pix


def build_weather_shared(root: Path) -> pd.DataFrame:
    hourly = pd.read_parquet(WEATHER_ROOT / "raw" / "point_01_raw_hourly.parquet")
    hourly["date"] = pd.to_datetime(hourly["date"]).dt.tz_localize(None).dt.normalize() if pd.to_datetime(hourly["date"]).dt.tz is not None else pd.to_datetime(hourly["date"]).dt.normalize()
    # aggregate hourly -> daily
    daily = hourly.groupby("date").agg(
        temperature_mean=("temperature_2m", "mean"),
        temperature_min=("temperature_2m", "min"),
        temperature_max=("temperature_2m", "max"),
        relative_humidity_mean=("relative_humidity_2m", "mean"),
        vpd_mean=("vapour_pressure_deficit", "mean"),
        precipitation_sum=("precipitation", "sum"),
        solar_radiation_mean=("shortwave_radiation", "mean"),
        solar_radiation_sum=("shortwave_radiation", "sum"),
        wind_speed_mean=("wind_speed_10m", "mean"),
        et0_sum=("et0_fao_evapotranspiration", "sum"),
        soil_moisture_mean=("soil_moisture_0_to_7cm", "mean"),
        soil_temperature_mean=("soil_temperature_0_to_7cm", "mean"),
    ).reset_index()
    daily = daily.sort_values("date").reset_index(drop=True)
    # rolling windows (retrospective, end at date inclusive)
    for w in (3, 7, 14, 30):
        daily[f"temperature_mean_{w}d"] = daily["temperature_mean"].rolling(w, min_periods=1).mean()
        daily[f"temperature_max_{w}d"] = daily["temperature_max"].rolling(w, min_periods=1).max()
        daily[f"temperature_min_{w}d"] = daily["temperature_min"].rolling(w, min_periods=1).min()
        daily[f"relative_humidity_mean_{w}d"] = daily["relative_humidity_mean"].rolling(w, min_periods=1).mean()
        daily[f"vpd_mean_{w}d"] = daily["vpd_mean"].rolling(w, min_periods=1).mean()
        daily[f"precipitation_sum_{w}d"] = daily["precipitation_sum"].rolling(w, min_periods=1).sum()
        daily[f"solar_radiation_mean_{w}d"] = daily["solar_radiation_mean"].rolling(w, min_periods=1).mean()
        daily[f"wind_speed_mean_{w}d"] = daily["wind_speed_mean"].rolling(w, min_periods=1).mean()
        daily[f"et0_sum_{w}d"] = daily["et0_sum"].rolling(w, min_periods=1).sum()
        daily[f"soil_moisture_mean_{w}d"] = daily["soil_moisture_mean"].rolling(w, min_periods=1).mean()
        daily[f"soil_temperature_mean_{w}d"] = daily["soil_temperature_mean"].rolling(w, min_periods=1).mean()
    daily.to_parquet(root / "weather" / "weather_shared.parquet", index=False)
    return daily


def build_weather_aligned(root: Path, daily: pd.DataFrame) -> pd.DataFrame:
    # Landsat acquisition dates from METRIC metadata
    dates = set()
    for p in glob.glob(str(METRIC_ROOT / "products" / "metadata" / "*.geojson")):
        try:
            d = json.load(open(p, encoding="utf-8"))
            t = d.get("acquisition_time")
            if t:
                dates.add(pd.to_datetime(t).date())
        except Exception:
            pass
    # also NDVI filenames
    import re
    for p in (METRIC_ROOT / "products" / "NDVI").glob("*.tif"):
        if "_interp" in p.name:
            continue
        m = re.search(r"_(\d{4}-\d{2}-\d{2})_AOI", p.name)
        if m:
            dates.add(pd.to_datetime(m.group(1)).date())
    landsat_dates = sorted(dates)
    daily = daily.copy()
    daily["date"] = pd.to_datetime(daily["date"]).dt.date
    # map date -> row
    by_date = {r["date"]: r for _, r in daily.iterrows()}
    # base daily aggregates lookup
    def lookup(d, col):
        r = by_date.get(d)
        if r is None:
            return np.nan
        return r[col]
    rows = []
    for d in landsat_dates:
        row = {"acquisition_date": pd.Timestamp(d)}
        r = by_date.get(d)
        if r is not None:
            for col in daily.columns:
                if col != "date":
                    row[col] = r[col]
        # daily aggregates fallback (single day) if not present
        for col in ["temperature_mean", "temperature_min", "temperature_max",
                    "relative_humidity_mean", "vpd_mean", "precipitation_sum",
                    "solar_radiation_mean", "wind_speed_mean", "et0_sum",
                    "soil_moisture_mean", "soil_temperature_mean"]:
            if col not in row and r is not None:
                row[col] = r[col]
        rows.append(row)
    out = pd.DataFrame(rows)
    out = out.loc[:, ~out.columns.duplicated()]
    out.to_parquet(root / "weather" / "weather_aligned.parquet", index=False)
    return out


def build_quality(root: Path) -> pd.DataFrame:
    recs = []
    for p in sorted((METRIC_ROOT / "products" / "metadata").glob("*.geojson")):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        q = d.get("quality", {}) or {}
        si = d.get("scene_info", {}) or {}
        cal = d.get("calibration", {}) or {}
        recs.append({
            "scene_id": d.get("scene_id"),
            "acquisition_time": d.get("acquisition_time"),
            "acquisition_date": pd.to_datetime(d.get("acquisition_time")).date() if d.get("acquisition_time") else None,
            "sensor": si.get("sensor"),
            "crs": si.get("crs"),
            "shape_x": (si.get("shape") or {}).get("x"),
            "shape_y": (si.get("shape") or {}).get("y"),
            "sun_elevation": si.get("sun_elevation"),
            "sun_azimuth": si.get("sun_azimuth"),
            "scene_quality": q.get("scene_quality"),
            "cloud_coverage": q.get("cloud_coverage"),
            "valid_pixels": q.get("valid_pixels"),
            "ndvi_mean": (q.get("ndvi_range") or {}).get("mean"),
            "ndvi_min": (q.get("ndvi_range") or {}).get("min"),
            "ndvi_max": (q.get("ndvi_range") or {}).get("max"),
            "lst_mean": (q.get("temperature_range") or {}).get("mean"),
            "calibration_valid": cal.get("valid"),
            "calibration_errors": "; ".join(cal.get("errors") or []),
            "metadata_file": p.name,
        })
    qdf = pd.DataFrame(recs)
    qdf.to_parquet(root / "satellite" / "quality.parquet", index=False)
    # scene inventory (one row per scene)
    inv = qdf[["scene_id", "acquisition_date", "sensor", "scene_quality",
               "cloud_coverage", "valid_pixels", "sun_elevation"]].copy()
    inv.to_parquet(root / "satellite" / "scene_inventory.parquet", index=False)
    return qdf


def copy_existing_processed(root: Path) -> None:
    src = Path("D:/RS/Thesis/thesis_implementation/data/processed")
    if not src.exists():
        return
    dst = root / "satellite"
    # fields.zarr -> stats_current.zarr
    fz = src / "fields.zarr"
    if fz.exists():
        target = dst / "stats_current.zarr"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(fz, target)
    # derived parquets
    derived = dst / "derived"
    derived.mkdir(parents=True, exist_ok=True)
    for name in ("cycles.parquet", "scores.parquet", "daily_anomaly.parquet", "baseline.npz"):
        p = src / name
        if p.exists():
            shutil.copy2(p, derived / name)
    # zonal dir (if any parquets)
    zonal = src / "zonal"
    if zonal.exists():
        for p in zonal.glob("*.parquet"):
            shutil.copy2(p, derived / p.name)


def write_readme(root: Path) -> None:
    text = """# Processed Data (PRD V1.0)

Farm-level standardized dataset for self-supervised learning and anomaly detection.

## Layout

```
Processed/
├── satellite/
│   ├── stats_current.zarr/     # existing mean/median/std (v2) — to be superseded by stats.zarr
│   ├── quality.parquet         # per-scene quality metadata (METRIC)
│   ├── scene_inventory.parquet # scene list (date, sensor, cloud, valid pixels)
│   └── derived/                # cycles, scores, daily anomaly, baseline (ML outputs)
├── weather/
│   ├── weather_shared.parquet  # daily aggregates + retrospective windows (shared covariate)
│   └── weather_aligned.parquet # Landsat acquisition dates x windows
├── coordinates/
│   ├── farms.parquet           # farm metadata (490 farms)
│   ├── farms.geojson           # farm polygons (UTM 32639)
│   └── farm_pixels.parquet     # pixel->farm mapping for subset reads
├── indices/                    # optional, separately stored spectral indices (empty by default)
├── manifests/
└── interim/
    └── field_mask_full.tif     # farm raster mask (all 490 farms)
```

## Subset reads (fast tests)

- Farms: `pd.read_parquet('coordinates/farms.parquet')` then filter by block/field_id.
- Pixels of one farm: `farm_pixels.parquet` filtered by field_id -> list of (row,col,x,y).
- Weather for a date range: filter `weather_shared.parquet` by date.
- Zarr: open with xarray and slice `ds.sel(field=..., time=slice(...))`.

## Heavy extraction (not run by this script)

- `scripts/extract_stats.py`  -> computes 8 statistics (mean/median/std/p10/p25/p75/p90/iqr)
  per (farm, date, band) -> satellite/stats_long.parquet, stats_wide.parquet, stats.zarr.
- `scripts/extract_pixels.py` -> farm-masked pixels per (farm, date) -> satellite/pixel.zarr.

Both support checkpoint/resume and --subset for fast validation.

## Zarr version

v2 (xarray-compatible). Migration to v3 is deferred (see PRD).

## Bands (harmonized)

blue, green, red, nir, swir1, swir2 (SR) + lst (thermal, stored separately).
"""
    (root / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--staging", default=str(DEFAULT_STAGING))
    ap.add_argument("--out", default=None, help="if given, also mirror staging to this path (must be writable)")
    args = ap.parse_args()

    staging = Path(args.staging)
    make_dirs(staging)

    print("[1/7] farms + geometry")
    build_farms(staging)
    print("[2/7] field mask (full 490 farms)")
    mask, transform, crs = build_field_mask(staging)
    print("[3/7] farm_pixels")
    build_farm_pixels(staging, mask, transform)
    print("[4/7] weather_shared (daily aggregates + windows)")
    daily = build_weather_shared(staging)
    print("[5/7] weather_aligned (Landsat dates)")
    build_weather_aligned(staging, daily)
    print("[6/7] quality + scene inventory")
    build_quality(staging)
    print("[7/7] copy existing processed + README")
    copy_existing_processed(staging)
    write_readme(staging)

    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        # mirror
        for item in staging.iterdir():
            target = out / item.name
            if item.is_dir():
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
        print("mirrored to", out)

    print("done. staging:", staging)


if __name__ == "__main__":
    main()
