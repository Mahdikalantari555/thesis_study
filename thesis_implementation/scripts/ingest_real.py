"""Ingest real METRIC products into fields.zarr (field x time x band).

Unlike the raw-Landsat ingest, this reads already-processed per-product GeoTIFFs
(NDVI, LST, ETaDaily, ...) aligned to a common 30 m UTM grid, rasterizes the
farm polygons onto that grid, and computes per-field zonal means via bincount.

Usage:
    python scripts/ingest_real.py --root . --fields D:/RS/Thesis/Data/RoI/Farms.geojson
"""
from __future__ import annotations

import argparse
import os
import re
import glob
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
import zarr
import xarray as xr

PRODUCTS_ROOT = Path("D:/RS/Thesis/Data/Metric/products")
# Only raw bands + LST (ST_B10). Indices are derived later (add_spectral_indices).
RAW_BAND_MAP = {
    "blue.tif": "SR_B2",
    "green.tif": "SR_B3",
    "red.tif": "SR_B4",
    "nir08.tif": "SR_B5",
    "swir16.tif": "SR_B6",
    "swir22.tif": "SR_B7",
    "lwir11.tif": "ST_B10",
}
RAW_BANDS = list(RAW_BAND_MAP.values())
PRODUCT_BANDS = []  # no derived products in the scientific run


def parse_scene_id(fname: str) -> str | None:
    m = re.search(r"_(L[89]_L2SP_\d+_\d{4}-\d{2}-\d{2})_AOI", fname)
    return m.group(1) if m else None


def parse_date(fname: str) -> str | None:
    m = re.search(r"_(\d{4}-\d{2}-\d{2})_AOI", fname)
    return m.group(1) if m else None


def find_product(band_dir: Path, scene_id: str) -> Path | None:
    matches = list(band_dir.glob(f"*_{scene_id}_AOI.tif"))
    # exclude interpolated
    matches = [m for m in matches if "_interp" not in m.name]
    return matches[0] if matches else None


def raw_scene_dir(scene_id: str) -> Path | None:
    # scene_id like L8_L2SP_165039_2013-05-18
    m = re.search(r"_(\d{4})-(\d{2})-(\d{2})", scene_id)
    if not m:
        return None
    date_nd = m.group(1) + m.group(2) + m.group(3)
    wrs = None
    parts = scene_id.split("_")
    if len(parts) >= 3:
        wrs = parts[2]  # 165039
    if not wrs or len(wrs) != 6:
        return None
    path, row = wrs[:3], wrs[3:]
    # strip leading zeros? folder uses 165_039 (no leading zero strip? observed 165, 039)
    folder = Path("D:/RS/Thesis/Data/Metric/scenes") / f"landsat_{date_nd}_{int(path)}_{row}"
    if folder.exists():
        return folder
    # try without int conversion
    folder2 = Path("D:/RS/Thesis/Data/Metric/scenes") / f"landsat_{date_nd}_{path}_{row}"
    if folder2.exists():
        return folder2
    return None


def build_field_mask(fields_gdf: gpd.GeoDataFrame, ref_tif: Path, out_path: Path, id_col: str = "field_id"):
    with rasterio.open(ref_tif) as src:
        transform = src.transform
        shape = src.shape
        crs = src.crs
    if fields_gdf.crs is None:
        fields_gdf = fields_gdf.set_crs("EPSG:4326")
    fields_gdf = fields_gdf.to_crs(crs)
    if id_col not in fields_gdf.columns:
        fields_gdf = fields_gdf.reset_index(drop=True)
        fields_gdf[id_col] = np.arange(1, len(fields_gdf) + 1, dtype=np.int64)

    shapes = ((geom, int(fid)) for geom, fid in zip(fields_gdf.geometry.values, fields_gdf[id_col].astype(int).values))
    mask = rasterize(shapes, out_shape=shape, transform=transform, fill=0, dtype="uint32", all_touched=False)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff", "height": shape[0], "width": shape[1], "count": 1,
        "dtype": "uint32", "crs": crs, "transform": transform, "compress": "lzw",
    }
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(mask, 1)
    return mask, transform, crs, fields_gdf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--fields", default="D:/RS/Thesis/Data/RoI/Farms.geojson")
    ap.add_argument("--subset", action="store_true", help="use Farms_subset.geojson")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    paths = root / "data"
    (paths / "geo").mkdir(parents=True, exist_ok=True)
    (paths / "interim").mkdir(parents=True, exist_ok=True)
    (paths / "processed").mkdir(parents=True, exist_ok=True)
    (paths / "manifests").mkdir(parents=True, exist_ok=True)

    fields_path = Path(args.fields)
    if args.subset:
        fields_path = Path("D:/RS/Thesis/Data/RoI/Farms_subset.geojson")
    gdf = gpd.read_file(fields_path)

    # reference product for grid
    ref_tif = sorted((PRODUCTS_ROOT / "NDVI").glob("*.tif"))[0]
    ref_tif = [p for p in (PRODUCTS_ROOT / "NDVI").glob("*.tif") if "_interp" not in p.name][0]

    mask_path = paths / "interim" / "field_mask.tif"
    mask, transform, crs, gdf = build_field_mask(gdf, ref_tif, mask_path, id_col="field_id")

    # metadata parquet
    meta_df = pd.DataFrame({
        "field_id": gdf["field_id"].astype(int).values,
        "farm": gdf.get("Farm", pd.Series([""] * len(gdf))).values,
        "block": gdf.get("block", pd.Series([""] * len(gdf))).values,
        "variety": gdf.get("variete", pd.Series([""] * len(gdf))).values,
        "age": gdf.get("age", pd.Series([""] * len(gdf))).values,
        "status": gdf.get("status", pd.Series([""] * len(gdf))).values,
        "management": gdf.get("management", pd.Series([""] * len(gdf))).values,
        "office": gdf.get("office", pd.Series([""] * len(gdf))).values,
        "area": gdf.get("area", pd.Series([np.nan] * len(gdf))).values,
    })
    meta_df.to_parquet(paths / "geo" / "fields.parquet", index=False)
    n_fields = len(gdf)
    print("n_fields", n_fields, "mask shape", mask.shape)

    # scene list from NDVI folder
    ndvi_files = sorted([p for p in (PRODUCTS_ROOT / "NDVI").glob("*.tif") if "_interp" not in p.name])
    scene_ids = []
    for p in ndvi_files:
        sid = parse_scene_id(p.name)
        if sid:
            scene_ids.append(sid)
    scene_ids = sorted(set(scene_ids))
    print("n scenes", len(scene_ids))

    # Build per-scene zonal and collect
    records = []  # list of (scene_id, date, sensor, df)
    for si, sid in enumerate(scene_ids):
        date_str = None
        m = re.search(r"(\d{4}-\d{2}-\d{2})", sid)
        if m:
            date_str = m.group(1)
        sensor = "L8" if sid.startswith("L8") else "L9" if sid.startswith("L9") else "LX"
        # load bands
        bands = {}
        valid = None
        # Product bands
        for band in PRODUCT_BANDS:
            bdir = PRODUCTS_ROOT / band
            p = find_product(bdir, sid)
            if p is None:
                continue
            with rasterio.open(p) as src:
                arr = src.read(1).astype(np.float32)
            bands[band] = arr
            if valid is None:
                valid = np.isfinite(arr)
        # Raw bands from scenes/
        rsd = raw_scene_dir(sid)
        qa_valid = None
        if rsd is not None:
            from ssl_anomaly.io.landsat import quality_mask, apply_scale_sr, apply_scale_st
            from ssl_anomaly.config import QualityCfg
            qcfg = QualityCfg()
            qa_path = rsd / "qa_pixel.tif"
            if qa_path.exists():
                with rasterio.open(qa_path) as src:
                    qa = src.read(1)
                qa_valid = quality_mask(qa, qcfg)
            for fname, bname in RAW_BAND_MAP.items():
                fpath = rsd / fname
                if not fpath.exists():
                    continue
                with rasterio.open(fpath) as src:
                    arr = src.read(1)
                # Raw scene TIFFs are already scaled (reflectance 0-1, LST K).
                bands[bname] = arr.astype(np.float32)
                if qa_valid is not None and valid is None:
                    valid = qa_valid
        if qa_valid is not None:
            valid = qa_valid if valid is None else (valid & qa_valid)
        if valid is None:
            # fallback
            if bands:
                valid = np.isfinite(list(bands.values())[0])
        if not bands or valid is None:
            continue
        # ensure all bands same shape
        # zonal
        inside = mask > 0
        lab_inside = mask[inside]
        ok_inside = valid[inside]
        n_all = np.bincount(lab_inside, minlength=n_fields + 1)
        n_ok = np.bincount(lab_inside[ok_inside], minlength=n_fields + 1)
        valid_frac = n_ok / np.maximum(n_all, 1)

        ok_pixels = inside & valid
        lab_ok = mask[ok_pixels]
        out = {
            "field": np.arange(1, n_fields + 1, dtype=np.int64),
            "valid_frac": valid_frac[1:n_fields + 1].astype(np.float32),
        }
        for band, arr in bands.items():
            v = arr[ok_pixels].astype(np.float64)
            finite = np.isfinite(v)
            vf, lf = v[finite], lab_ok[finite]
            wsum = np.bincount(lf, weights=vf, minlength=n_fields + 1)
            cnt = np.bincount(lf, minlength=n_fields + 1)
            mean = np.full(n_fields + 1, np.nan, dtype=np.float64)
            np.divide(wsum, np.maximum(cnt, 1), out=mean, where=cnt > 0)
            # median via pandas
            if lf.size > 0:
                med = (pd.Series(vf).groupby(lf).median().reindex(np.arange(n_fields + 1)).to_numpy())
                std = (pd.Series(vf).groupby(lf).std().reindex(np.arange(n_fields + 1)).to_numpy())
            else:
                med = np.full(n_fields + 1, np.nan)
                std = np.full(n_fields + 1, np.nan)
            out[f"{band}_mean"] = mean[1:n_fields + 1].astype(np.float32)
            out[f"{band}_median"] = med[1:n_fields + 1].astype(np.float32)
            out[f"{band}_std"] = std[1:n_fields + 1].astype(np.float32)

        # CWSI_ET product (for visualization toggle) - zonal mean
        cwsi_p = find_product(Path("D:/RS/Thesis/Data/Metric/products/CWSI_ET"), sid)
        if cwsi_p is not None:
            with rasterio.open(cwsi_p) as src:
                cwsi_full = src.read(1).astype(np.float64)
            v = cwsi_full[ok_pixels].astype(np.float64)
            lf2 = lab_ok.copy()
            finite2 = np.isfinite(v)
            vf2, lf2f = v[finite2], lf2[finite2]
            wsum2 = np.bincount(lf2f, weights=vf2, minlength=n_fields + 1)
            cnt2 = np.bincount(lf2f, minlength=n_fields + 1)
            cwsi_mean = np.full(n_fields + 1, np.nan, dtype=np.float64)
            np.divide(wsum2, np.maximum(cnt2, 1), out=cwsi_mean, where=cnt2 > 0)
            out["cwsi_et_mean"] = cwsi_mean[1:n_fields + 1].astype(np.float32)

        df = pd.DataFrame(out)
        df["scene_id"] = sid
        df["timestamp"] = np.datetime64(date_str) if date_str else None
        df["sensor"] = sensor
        records.append(df)

        if (si + 1) % 50 == 0:
            print(f"processed {si+1}/{len(scene_ids)}")

    # Aggregate into xarray / zarr
    # Build arrays: fields x time x band using median? The implementation uses 'median' variable.
    # We'll store median (per field/time/band) and valid_frac (field/time).
    all_fields = np.arange(1, n_fields + 1)
    times = sorted({str(r["timestamp"].iloc[0])[:10] for r in records})
    # map timestamp to index
    time_to_idx = {t: i for i, t in enumerate(times)}
    band_names = PRODUCT_BANDS + RAW_BANDS
    # only bands present in all? use BANDS
    n_time = len(times)
    median_arr = np.full((n_fields, n_time, len(band_names)), np.nan, dtype=np.float32)
    std_arr = np.full((n_fields, n_time, len(band_names)), np.nan, dtype=np.float32)
    valid_arr = np.full((n_fields, n_time), np.nan, dtype=np.float32)
    ndvi_arr = np.full((n_fields, n_time), np.nan, dtype=np.float32)
    cwsi_arr = np.full((n_fields, n_time), np.nan, dtype=np.float32)

    for df in records:
        ts = str(df["timestamp"].iloc[0])[:10]
        ti = time_to_idx[ts]
        # field order 1..n
        fidx = df["field"].values.astype(int) - 1
        valid_arr[fidx, ti] = df["valid_frac"].values
        for bi, band in enumerate(band_names):
            col = f"{band}_median"
            if col in df.columns:
                median_arr[fidx, ti, bi] = df[col].values
            col_std = f"{band}_std"
            if col_std in df.columns:
                std_arr[fidx, ti, bi] = df[col_std].values
        # cwsi_et
        if "cwsi_et_mean" in df.columns:
            cwsi_arr[fidx, ti] = df["cwsi_et_mean"].values
        # ndvi from SR_B4 (red) and SR_B5 (nir)
        if "SR_B4_median" in df.columns and "SR_B5_median" in df.columns:
            red = df["SR_B4_median"].values.astype(np.float64)
            nir = df["SR_B5_median"].values.astype(np.float64)
            denom = nir + red
            ndvi_val = np.where((denom != 0) & np.isfinite(denom), (nir - red) / np.where(denom == 0, 1, denom), np.nan)
            ndvi_arr[fidx, ti] = ndvi_val.astype(np.float32)

    # Weather (ERA5 daily) aligned to scene dates
    wdf = pd.read_csv("D:/RS/Thesis/Data/Weather/metric_input/weather_combined.csv")
    wdf["date"] = pd.to_datetime(wdf["time"]).dt.date.astype(str)
    wdf["gdd"] = (wdf["temperature_2m"] - 10.0).clip(lower=0.0)
    wmap = {r["date"]: r for _, r in wdf.iterrows()}
    w_tmean = np.full(n_time, np.nan, dtype=np.float32)
    w_et0 = np.full(n_time, np.nan, dtype=np.float32)
    w_rad = np.full(n_time, np.nan, dtype=np.float32)
    w_rh = np.full(n_time, np.nan, dtype=np.float32)
    w_gdd = np.full(n_time, np.nan, dtype=np.float32)
    for ti, t in enumerate(times):
        d = str(t)[:10]
        if d in wmap:
            r = wmap[d]
            w_tmean[ti] = float(r["temperature_2m"])
            w_et0[ti] = float(r["et0_fao_evapotranspiration"])
            w_rad[ti] = float(r["shortwave_radiation"])
            w_rh[ti] = float(r["relative_humidity_2m"])
            w_gdd[ti] = float(r["gdd"])

    # sensor per time
    sensor_per_time = []
    for t in times:
        # find a record with that time
        s = None
        for df in records:
            if str(df["timestamp"].iloc[0])[:10] == t:
                s = df["sensor"].iloc[0]
                break
        sensor_per_time.append(s if s else "L8")

    ds = xr.Dataset(
        {
            "median": (("field", "time", "band"), median_arr),
            "std": (("field", "time", "band"), std_arr),
            "valid_frac": (("field", "time"), valid_arr),
            "ndvi": (("field", "time"), ndvi_arr),
            "cwsi_et": (("field", "time"), cwsi_arr),
            "weather_tmean": (("time",), w_tmean),
            "weather_et0": (("time",), w_et0),
            "weather_rad": (("time",), w_rad),
            "weather_rh": (("time",), w_rh),
            "weather_gdd": (("time",), w_gdd),
        },
        coords={
            "field": all_fields,
            "time": np.array(times, dtype="datetime64[D]"),
            "band": band_names,
            "sensor": ("time", sensor_per_time),
        },
    )
    zarr_path = paths / "processed" / "fields.zarr"
    if zarr_path.exists():
        import shutil
        shutil.rmtree(zarr_path)
    ds.to_zarr(str(zarr_path), mode="w", zarr_format=3)
    print("wrote", zarr_path)
    print("times", n_time, "fields", n_fields, "bands", len(band_names))


if __name__ == "__main__":
    main()
