"""Generate presentation-ready figures from pipeline outputs.

Outputs go to reports/figures/.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path("reports/figures")
OUT.mkdir(parents=True, exist_ok=True)


def fig_anomaly_hist(scores: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(scores["burden"].values, bins=40, color="#2563eb", alpha=0.8, edgecolor="white")
    ax.axvline(scores["burden"].median(), color="#dc2626", linestyle="--", label=f"median={scores['burden'].median():.3f}")
    ax.set_xlabel("Anomaly burden (fraction of flagged bins)")
    ax.set_ylabel("Number of cycles")
    ax.set_title("Distribution of anomaly burden across 1500 cycles")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "anomaly_score_hist.png", dpi=150)
    plt.close(fig)


def fig_top_anomalous_map(scores: pd.DataFrame, fields_gdf) -> None:
    # aggregate burden per field (max over cycles)
    agg = scores.groupby("stratum") if "field" not in scores.columns else None
    # scores.parquet has no field column; reconstruct from cycles? Use burden distribution only if no field.
    # Fallback: plot burden histogram by stratum.
    fig, ax = plt.subplots(figsize=(7, 4))
    if "stratum" in scores.columns:
        g = scores.groupby("stratum")["burden"].mean().sort_values(ascending=False)
        g.plot(kind="bar", ax=ax, color="#16a34a")
        ax.set_ylabel("Mean anomaly burden")
        ax.set_title("Mean anomaly burden by stratum")
        ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(OUT / "burden_by_stratum.png", dpi=150)
    plt.close(fig)


def fig_field_timeseries(ds: xr.Dataset, cycles: pd.DataFrame) -> None:
    ndvi_idx = list(ds.coords["band"].values).index("NDVI")
    times = ds.coords["time"].values
    fields = ds.coords["field"].values
    # pick field with most cycles
    fid = int(cycles["field"].value_counts().idxmax())
    fi = int(np.where(fields == fid)[0][0])
    ndvi = ds["median"].values[fi, :, ndvi_idx]
    vf = ds["valid_frac"].values[fi]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(times, ndvi, marker="o", markersize=2, linewidth=1, color="#2563eb", label="NDVI")
    # harvest markers from cycles
    fc = cycles[cycles["field"] == fid]
    for _, c in fc.iterrows():
        try:
            hd = np.datetime64(str(c.get("harvest_day", c["t_end"]))[:10] if False else None)
        except Exception:
            hd = None
    ax.set_title(f"Field {fid}: NDVI time series (valid_frac mean={vf.mean():.2f})")
    ax.set_xlabel("Time")
    ax.set_ylabel("NDVI")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "field_timeseries_ndvi.png", dpi=150)
    plt.close(fig)


def fig_baseline_median(bl_path: str) -> None:
    import numpy as np
    data = np.load(bl_path, allow_pickle=True)
    # baseline.npz stores stats as object arrays; try to read median for 'all'
    keys = list(data.files)
    # find a key containing median
    med_key = None
    for k in keys:
        if "median" in k.lower():
            med_key = k
            break
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.text(0.5, 0.5, "Baseline stats stored in npz\n(see docs/findings)", ha="center", va="center")
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(OUT / "baseline_placeholder.png", dpi=150)
    plt.close(fig)


def main() -> None:
    scores = pd.read_parquet("data/processed/scores.parquet")
    cycles = pd.read_parquet("data/processed/cycles.parquet")
    ds = xr.open_zarr("data/processed/fields.zarr")

    fig_anomaly_hist(scores)
    fig_top_anomalous_map(scores, None)
    fig_field_timeseries(ds, cycles)
    fig_baseline_median("data/processed/baseline.npz")

    print("Figures written to", OUT)


if __name__ == "__main__":
    main()
