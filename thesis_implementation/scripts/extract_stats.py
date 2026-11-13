"""Extract farm-level distribution statistics (8 stats) per (farm, date, band).

Computes mean/median/std/p10/p25/p75/p90/iqr + valid_frac + n_pixels for every
Landsat scene and every farm, using the pre-built field mask.

Usage:
    python scripts/extract_stats.py                    # full run (resumable)
    python scripts/extract_stats.py --max-scenes 5    # quick smoke test
    python scripts/extract_stats.py --out D:/RS/Thesis/Data/Processed
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import from_bounds

BAND_ORDER = ["blue", "green", "red", "nir", "swir1", "swir2", "lst"]
FILE_MAP = {
    "blue": "blue.tif", "green": "green.tif", "red": "red.tif",
    "nir": "nir08.tif", "swir1": "swir16.tif", "swir2": "swir22.tif",
    "lst": "lwir11.tif",
}
HARMONIZED = {b: b for b in BAND_ORDER}
STATS = ("mean", "median", "std", "p10", "p25", "p75", "p90", "iqr")


def parse_scene_id_dir(d: Path) -> str | None:
    # folder name landsat_YYYYMMDD_path_row
    m = re.search(r"landsat_(\d{8})_(\d{3})_(\d{3})", d.name)
    if not m:
        return None
    date_nd, path, row = m.groups()
    ts = f"{date_nd[:4]}-{date_nd[4:6]}-{date_nd[6:8]}"
    return f"L8_L2SP_{path}{row}_{ts}"  # placeholder sensor; refined from MTL if present


def load_field_mask(mask_path: Path):
    with rasterio.open(mask_path) as src:
        mask = src.read(1)
        transform = src.transform
        crs = src.crs
        shape = src.shape
    n_fields = int(mask.max())
    return mask, transform, crs, shape, n_fields


def scene_dir_for_date(date_str: str, scenes_root: Path) -> Path | None:
    nd = date_str.replace("-", "")
    for p in scenes_root.glob(f"landsat_{nd}_*"):
        return p
    return None


def load_scene_arrays(scene_dir: Path, mask_shape, transform, mask_crs):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from ssl_anomaly.io.landsat import quality_mask, QualityCfg
    qcfg = QualityCfg()
    qa_path = scene_dir / "qa_pixel.tif"
    if not qa_path.exists():
        cands = list(scene_dir.glob("*QA_PIXEL*")) + list(scene_dir.glob("*qa_pixel*"))
        if not cands:
            return None
        qa_path = cands[0]
    with rasterio.open(qa_path) as src:
        qa = src.read(1)
        scene_crs = src.crs
    if str(scene_crs).upper() != str(mask_crs).upper():
        return None
    valid = quality_mask(qa, qcfg)

    out = {}
    for band, fname in FILE_MAP.items():
        fpath = scene_dir / fname
        if not fpath.exists():
            cands = list(scene_dir.glob(f"*{band}*"))
            if not cands:
                continue
            fpath = cands[0]
        with rasterio.open(fpath) as src:
            arr = src.read(1)
        out[band] = arr.astype(np.float32)
    if not out:
        return None
    # align shapes (all should be 472x496 already)
    h = min(valid.shape[0], min(v.shape[0] for v in out.values()))
    w = min(valid.shape[1], min(v.shape[1] for v in out.values()))
    valid = valid[:h, :w]
    out = {k: v[:h, :w] for k, v in out.items()}
    return out, valid


def zonal_stats_one_scene(mask, transform, bands, valid, n_fields):
    inside = mask > 0
    # If mask shape != bands shape, crop mask to common
    h = min(mask.shape[0], valid.shape[0])
    w = min(mask.shape[1], valid.shape[1])
    mask_c = mask[:h, :w]
    valid_c = valid[:h, :w]
    bands_c = {k: v[:h, :w] for k, v in bands.items()}

    inside = mask_c > 0
    lab_inside = mask_c[inside]
    ok_inside = valid_c[inside]
    n_all = np.bincount(lab_inside, minlength=n_fields + 1)
    n_ok = np.bincount(lab_inside[ok_inside], minlength=n_fields + 1)
    valid_frac = n_ok / np.maximum(n_all, 1)

    ok_pixels = inside & valid_c
    lab_ok = mask_c[ok_pixels]

    rows = []
    for fid in range(1, n_fields + 1):
        row = {"field": fid, "valid_frac": float(valid_frac[fid]),
               "n_pixels": int(n_ok[fid])}
        msk = lab_ok == fid
        for band in bands_c:
            vals = bands_c[band][ok_pixels][msk].astype(np.float64)
            vals = vals[np.isfinite(vals)]
            if vals.size == 0:
                for s in STATS:
                    row[f"{band}_{s}"] = np.nan
                continue
            row[f"{band}_mean"] = float(np.mean(vals))
            row[f"{band}_median"] = float(np.median(vals))
            row[f"{band}_std"] = float(np.std(vals, ddof=1)) if vals.size > 1 else 0.0
            row[f"{band}_p10"] = float(np.percentile(vals, 10))
            row[f"{band}_p25"] = float(np.percentile(vals, 25))
            row[f"{band}_p75"] = float(np.percentile(vals, 75))
            row[f"{band}_p90"] = float(np.percentile(vals, 90))
            row[f"{band}_iqr"] = float(np.percentile(vals, 75) - np.percentile(vals, 25))
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="D:/RS/Thesis/Data/Processed")
    ap.add_argument("--mask", default=None)
    ap.add_argument("--scenes-root", default="D:/RS/Thesis/Data/Metric/scenes")
    ap.add_argument("--max-scenes", type=int, default=None)
    ap.add_argument("--resume", action="store_true", default=True)
    args = ap.parse_args()

    out = Path(args.out)
    mask_path = Path(args.mask) if args.mask else out / "interim" / "field_mask_full.tif"
    if not mask_path.exists():
        # fallback to thesis interim
        alt = Path("D:/RS/Thesis/thesis_implementation/data/interim/field_mask.tif")
        if alt.exists():
            mask_path = alt
    mask, transform, crs, shape, n_fields = load_field_mask(mask_path)
    scenes_root = Path(args.scenes_root)
    zonal_dir = out / "satellite" / "zonal_stats"
    zonal_dir.mkdir(parents=True, exist_ok=True)

    # sensor map from metadata
    sensor_map = {}
    for p in glob.glob("D:/RS/Thesis/Data/Metric/products/metadata/*.geojson"):
        try:
            d = json.load(open(p, encoding="utf-8"))
            t = d.get("acquisition_time")
            si = d.get("scene_info", {}) or {}
            if t:
                sensor_map[pd.to_datetime(t).date()] = "L9" if "LC09" in (d.get("scene_id") or "") else "L8"
        except Exception:
            pass
    scene_dates = sorted(sensor_map.keys())
    if args.max_scenes:
        scene_dates = scene_dates[:args.max_scenes]

    for i, d in enumerate(scene_dates):
        date_str = str(d)
        out_file = zonal_dir / f"{date_str}.parquet"
        if args.resume and out_file.exists():
            print(f"[{i+1}/{len(scene_dates)}] skip {date_str}")
            continue
        sdir = scene_dir_for_date(date_str, scenes_root)
        if sdir is None:
            print(f"[{i+1}/{len(scene_dates)}] no scene dir {date_str}")
            continue
        loaded = load_scene_arrays(sdir, shape, transform, crs)
        if loaded is None:
            print(f"[{i+1}/{len(scene_dates)}] load failed {date_str}")
            continue
        bands, valid = loaded
        # sensor from folder? default L8
        sensor = sensor_map.get(d, "L8")
        df = zonal_stats_one_scene(mask, transform, bands, valid, n_fields)
        df["scene_date"] = date_str
        df["sensor"] = sensor
        df.to_parquet(out_file, index=False)
        print(f"[{i+1}/{len(scene_dates)}] done {date_str} ({len(df)} farms)")

    # aggregate
    print("aggregating...")
    files = sorted(zonal_dir.glob("*.parquet"))
    if not files:
        print("no zonal files")
        return
    frames = [pd.read_parquet(f) for f in files]
    all_df = pd.concat(frames, ignore_index=True)
    # long format: one row per farm x date x band
    long_rows = []
    for _, r in all_df.iterrows():
        for band_raw, band_h in HARMONIZED.items():
            # columns are like SR_B2_mean -> need mapping; our zonal used band keys SR_B2 etc.
            pass
    # Build long from column naming: {band}_{stat}
    records = []
    for _, r in all_df.iterrows():
        for band_raw, band_h in HARMONIZED.items():
            rec = {"field_id": r["field"], "date": r["scene_date"],
                   "sensor": r["sensor"], "band_raw": band_raw, "band": band_h,
                   "valid_frac": r["valid_frac"], "n_pixels": r["n_pixels"]}
            for s in STATS:
                col = f"{band_raw}_{s}"
                rec[s] = r.get(col, np.nan)
            records.append(rec)
    long_df = pd.DataFrame(records)
    long_df.to_parquet(out / "satellite" / "stats_long.parquet", index=False)

    # wide: one row per farm x date
    # pivot stats into columns band_stat
    wide = all_df.copy()
    wide.to_parquet(out / "satellite" / "stats_wide_raw.parquet", index=False)

    import xarray as xr
    fields = sorted(all_df["field"].unique())
    times = sorted(all_df["scene_date"].unique())
    bands = list(HARMONIZED.values())
    f_idx = {f: i for i, f in enumerate(fields)}
    t_idx = {t: i for i, t in enumerate(times)}
    n_f, n_t, n_b = len(fields), len(times), len(bands)
    bmap = {v: i for i, v in enumerate(bands)}
    arrays = {s: np.full((n_f, n_t, n_b), np.nan, dtype=np.float32) for s in STATS}
    valid_arr = np.full((n_f, n_t), np.nan, dtype=np.float32)
    npix_arr = np.zeros((n_f, n_t), dtype=np.int64)
    sensor_per_time = [None] * n_t
    for _, r in all_df.iterrows():
        fi = f_idx[r["field"]]; ti = t_idx[r["scene_date"]]
        valid_arr[fi, ti] = r["valid_frac"]
        npix_arr[fi, ti] = int(r["n_pixels"])
        if sensor_per_time[ti] is None:
            sensor_per_time[ti] = r["sensor"]
        for band_raw, band_h in HARMONIZED.items():
            bi = bmap[band_h]
            for s in STATS:
                col = f"{band_raw}_{s}"
                if col in all_df.columns and pd.notna(r.get(col)):
                    arrays[s][fi, ti, bi] = r[col]
    times_ns = np.array(times, dtype="datetime64[D]")
    ds = xr.Dataset(
        {s: (("field", "time", "band"), arrays[s]) for s in STATS} | {
            "valid_frac": (("field", "time"), valid_arr),
            "n_pixels": (("field", "time"), npix_arr),
        },
        coords={
            "field": np.array(fields, dtype=np.int64),
            "time": times_ns,
            "band": np.array(bands, dtype=object),
            "sensor": (("time",), [s if s else "L8" for s in sensor_per_time]),
        },
        attrs={"zarr_format": 2, "crs": "EPSG:32639", "pixel_size_m": 30.0,
               "source": "extract_stats", "stats": list(STATS)},
    )
    zarr_path = out / "satellite" / "stats.zarr"
    if zarr_path.exists():
        import shutil
        shutil.rmtree(zarr_path)
    ds.to_zarr(str(zarr_path), mode="w", consolidated=True)
    print("wrote", zarr_path, "fields", n_f, "times", n_t, "bands", n_b)
    print("done. long rows:", len(long_df))


if __name__ == "__main__":
    main()
