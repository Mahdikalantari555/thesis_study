"""Generate presentation-ready figures using PIL (matplotlib is broken in this env)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from PIL import Image, ImageDraw, ImageFont

OUT = Path("reports/figures")
OUT.mkdir(parents=True, exist_ok=True)
W, H = 900, 500


def canvas(title: str):
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.text((20, 15), title, fill="black")
    return im, d


def hist(scores: pd.DataFrame) -> None:
    im, d = canvas("Anomaly burden distribution (1500 cycles)")
    vals = scores["burden"].values
    bins = np.linspace(0, vals.max(), 21)
    counts, _ = np.histogram(vals, bins=bins)
    maxc = counts.max()
    x0, y0, x1, y1 = 60, 60, W - 40, H - 60
    for i, c in enumerate(counts):
        bx0 = x0 + i * (x1 - x0) / len(counts)
        bx1 = x0 + (i + 1) * (x1 - x0) / len(counts) - 2
        bh = (c / maxc) * (y1 - y0)
        d.rectangle([bx0, y1 - bh, bx1, y1], fill="#2563eb")
    d.line([x0, y1, x1, y1], fill="black")
    d.line([x0, y0, x0, y1], fill="black")
    d.text((x0, y1 + 5), f"min={vals.min():.3f} max={vals.max():.3f} median={np.median(vals):.3f}", fill="black")
    im.save(OUT / "anomaly_score_hist.png")


def burden_by_stratum(scores: pd.DataFrame) -> None:
    im, d = canvas("Mean anomaly burden by stratum")
    g = scores.groupby("stratum")["burden"].mean().sort_values(ascending=False)
    labels = list(g.index)
    vals = g.values
    maxv = vals.max()
    x0, y0, x1, y1 = 60, 60, W - 40, H - 60
    bw = (x1 - x0) / len(vals)
    for i, (lab, v) in enumerate(zip(labels, vals)):
        bx0 = x0 + i * bw + 4
        bx1 = x0 + (i + 1) * bw - 4
        bh = (v / maxv) * (y1 - y0)
        d.rectangle([bx0, y1 - bh, bx1, y1], fill="#16a34a")
        d.text((bx0, y1 + 5), str(lab)[:10], fill="black")
    d.line([x0, y1, x1, y1], fill="black")
    im.save(OUT / "burden_by_stratum.png")


def field_ts(ds: xr.Dataset, cycles: pd.DataFrame) -> None:
    ndvi_idx = list(ds.coords["band"].values).index("NDVI")
    times = ds.coords["time"].values
    fields = ds.coords["field"].values
    fid = int(cycles["field"].value_counts().idxmax())
    fi = int(np.where(fields == fid)[0][0])
    ndvi = ds["median"].values[fi, :, ndvi_idx]
    im, d = canvas(f"Field {fid} NDVI time series")
    x0, y0, x1, y1 = 60, 60, W - 40, H - 60
    vmin, vmax = np.nanmin(ndvi), np.nanmax(ndvi)
    pts = []
    for i, v in enumerate(ndvi):
        if np.isnan(v):
            continue
        x = x0 + i * (x1 - x0) / (len(ndvi) - 1)
        y = y1 - (v - vmin) / (vmax - vmin) * (y1 - y0)
        pts.append((x, y))
    for a, b in zip(pts, pts[1:]):
        d.line([a, b], fill="#2563eb", width=2)
    d.text((x0, y1 + 5), f"NDVI min={vmin:.3f} max={vmax:.3f}", fill="black")
    im.save(OUT / "field_timeseries_ndvi.png")


def main() -> None:
    scores = pd.read_parquet("data/processed/scores.parquet")
    cycles = pd.read_parquet("data/processed/cycles.parquet")
    ds = xr.open_zarr("data/processed/fields.zarr")
    hist(scores)
    burden_by_stratum(scores)
    field_ts(ds, cycles)
    print("PIL figures written to", OUT)


if __name__ == "__main__":
    main()
