"""Extract farm-masked pixel-level data per (farm, date).

For each Landsat scene, writes the pixels inside farm polygons (with their
band values and quality mask) to a per-scene Parquet. Supports checkpoint/resume
and --max-scenes for smoke tests.

Usage:
    python scripts/extract_pixels.py                    # full run
    python scripts/extract_pixels.py --max-scenes 3     # smoke test
    python scripts/extract_pixels.py --out D:/RS/Thesis/Data/Processed
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

FILE_MAP = {
    "blue": "blue.tif", "green": "green.tif", "red": "red.tif",
    "nir": "nir08.tif", "swir1": "swir16.tif", "swir2": "swir22.tif",
    "lst": "lwir11.tif",
}


def load_field_mask(mask_path: Path):
    with rasterio.open(mask_path) as src:
        mask = src.read(1); transform = src.transform; crs = src.crs; shape = src.shape
    return mask, transform, crs, shape


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="D:/RS/Thesis/Data/Processed")
    ap.add_argument("--mask", default=None)
    ap.add_argument("--scenes-root", default="D:/RS/Thesis/Data/Metric/scenes")
    ap.add_argument("--max-scenes", type=int, default=None)
    args = ap.parse_args()

    out = Path(args.out)
    mask_path = Path(args.mask) if args.mask else out / "interim" / "field_mask_full.tif"
    if not mask_path.exists():
        alt = Path("D:/RS/Thesis/thesis_implementation/data/interim/field_mask.tif")
        if alt.exists():
            mask_path = alt
    mask, transform, crs, shape = load_field_mask(mask_path)

    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from ssl_anomaly.io.landsat import quality_mask, QualityCfg
    qcfg = QualityCfg()

    scenes_root = Path(args.scenes_root)
    pixel_dir = out / "satellite" / "pixels"
    pixel_dir.mkdir(parents=True, exist_ok=True)

    metas = sorted(glob.glob("D:/RS/Thesis/Data/Metric/products/metadata/*.geojson"))
    dates = []
    for p in metas:
        try:
            d = json.load(open(p, encoding="utf-8"))
            t = d.get("acquisition_time")
            if t:
                dates.append(pd.to_datetime(t).date())
        except Exception:
            pass
    dates = sorted(set(dates))
    if args.max_scenes:
        dates = dates[:args.max_scenes]

    for i, d in enumerate(dates):
        date_str = str(d)
        out_file = pixel_dir / f"{date_str}.parquet"
        if out_file.exists():
            print(f"[{i+1}/{len(dates)}] skip {date_str}")
            continue
        sdir = None
        nd = date_str.replace("-", "")
        for p in scenes_root.glob(f"landsat_{nd}_*"):
            sdir = p; break
        if sdir is None:
            print(f"[{i+1}/{len(dates)}] no scene dir {date_str}")
            continue
        qa_path = sdir / "qa_pixel.tif"
        if not qa_path.exists():
            cands = list(sdir.glob("*qa_pixel*")) + list(sdir.glob("*QA_PIXEL*"))
            if not cands:
                print(f"[{i+1}/{len(dates)}] no qa {date_str}")
                continue
            qa_path = cands[0]
        with rasterio.open(qa_path) as src:
            qa = src.read(1); sc = src.crs
        if str(sc).upper() != str(crs).upper():
            print(f"[{i+1}/{len(dates)}] crs mismatch {date_str}")
            continue
        valid = quality_mask(qa, qcfg)

        bands = {}
        for band, fname in FILE_MAP.items():
            fpath = sdir / fname
            cands = [fpath] if fpath.exists() else list(sdir.glob(f"*{band}*"))
            if not cands:
                continue
            with rasterio.open(cands[0]) as src:
                arr = src.read(1)
            bands[band] = arr.astype(np.float32)
        if not bands:
            print(f"[{i+1}/{len(dates)}] no bands {date_str}")
            continue
        h = min(valid.shape[0], min(v.shape[0] for v in bands.values()), mask.shape[0])
        w = min(valid.shape[1], min(v.shape[1] for v in bands.values()), mask.shape[1])
        valid = valid[:h, :w]
        bands = {k: v[:h, :w] for k, v in bands.items()}
        mask_c = mask[:h, :w]

        inside = mask_c > 0
        rows, cols = np.where(inside)
        fields = mask_c[rows, cols]
        xs = transform.c + cols * transform.a + rows * transform.b
        ys = transform.f + cols * transform.d + rows * transform.e

        data = {
            "field_id": fields.astype(np.int64),
            "row": rows.astype(np.int64),
            "col": cols.astype(np.int64),
            "x": np.asarray(xs, dtype=np.float64),
            "y": np.asarray(ys, dtype=np.float64),
            "valid": valid[rows, cols].astype(bool),
        }
        for band, arr in bands.items():
            data[band] = arr[rows, cols].astype(np.float32)
        pdf = pd.DataFrame(data)
        pdf["scene_date"] = date_str
        pdf["sensor"] = "L8"
        pdf["local_pixel"] = pdf.groupby("field_id").cumcount().astype(np.int64)
        pdf.to_parquet(out_file, index=False)
        print(f"[{i+1}/{len(dates)}] done {date_str} ({len(pdf)} pixels)")

    print("done. pixel files in", pixel_dir)


if __name__ == "__main__":
    main()
