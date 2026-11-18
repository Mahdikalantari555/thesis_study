#!/usr/bin/env python3
"""Fit the robust B1 baseline and score all cycles.

Usage::

    python scripts/build_baseline.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from ssl_anomaly.baseline import (
    build_stratum_table,
    fit_baseline,
    score_all_cycles,
    trimmed_normal_cycles,
)
from ssl_anomaly.phenology import add_spectral_indices, phase_bin
from ssl_anomaly.utils.logging import get_logger
from ssl_anomaly.utils.throttle import limit_threads

log = get_logger("ssl_anomaly.scripts.baseline")


def main() -> int:
    limit_threads(2)
    paths = {
        "zarr": Path("data/processed/fields.zarr"),
        "cycles": Path("data/processed/cycles.parquet"),
        "out_npz": Path("data/processed/baseline.npz"),
        "out_scores": Path("data/processed/scores.parquet"),
    }
    if not paths["zarr"].exists():
        log.error(
            "fields.zarr not found at %s; generate synthetic data first with "
            "scripts/generate_synthetic_data.py",
            paths["zarr"],
        )
        return 1

    ds = xr.open_zarr(paths["zarr"])
    ds = add_spectral_indices(ds)
    med = ds["median"].values  # (F,T,B)
    times = ds.coords["time"].values
    bands = list(ds.coords["band"].values)
    fields = ds.coords["field"].values
    band_idx = {b: i for i, b in enumerate(bands)}

    ndvi_idx = band_idx.get("NDVI")
    if ndvi_idx is None:
        log.error("NDVI band missing — was add_spectral_indices applied?")
        return 1

    cycles_df = pd.read_parquet(paths["cycles"])
    cycles_df = build_stratum_table(cycles_df)

    # Build per-cycle binned arrays
    bin_days = 15
    max_cycle = 540

    X_by_stratum: dict[str, list[np.ndarray]] = {}
    X_fields_by_stratum: dict[str, list[int]] = {}
    X_by_field: dict[int, list[np.ndarray]] = {}

    epoch = times[0]
    for fid in fields:
        fmask = cycles_df["field"] == fid
        fc = cycles_df[fmask].sort_values("cycle_id")
        fi = int(np.where(fields == fid)[0][0])
        field_cycles_binned = []
        for _, c in fc.iterrows():
            if c["censored"]:
                continue
            # Cycle attributes are days since ``epoch`` (times[0]).
            # dsh is measured from start_harvest (the harvest that began this cycle).
            t_start_dt = epoch + np.timedelta64(int(c["t_start"]), "D")
            t_end_dt = epoch + np.timedelta64(int(c["t_end"]), "D")
            start_h = int(c.get("start_harvest", c["t_start"]))
            harvest_dt = epoch + np.timedelta64(start_h, "D")
            tmask = (times >= t_start_dt) & (times < t_end_dt)
            if tmask.sum() < 3:
                continue
            t_cycle = times[tmask]
            bands_cycle = med[fi][tmask]
            dsh = (t_cycle - harvest_dt).astype("timedelta64[D]").astype(int)
            values = {b: bands_cycle[:, band_idx[b]] for b in bands}
            binned = phase_bin(values, dsh, bin_days=bin_days, max_cycle_days=max_cycle)
            arr = np.stack([binned[b] for b in bands], axis=-1)  # (bins, bands)
            key = str(c.get("stratum_full", "all"))
            X_by_stratum.setdefault(key, []).append(arr)
            X_fields_by_stratum.setdefault(key, []).append(int(fid))
            field_cycles_binned.append(arr)
        if field_cycles_binned:
            X_by_field[fi] = np.stack(field_cycles_binned, axis=0)

    X = {k: np.stack(v, axis=0) for k, v in X_by_stratum.items() if v}
    if "all" not in X:
        all_cycles = np.concatenate(list(X.values()), axis=0)
        X["all"] = all_cycles
    for k in X:
        if X[k].ndim != 3:
            log.warning("Stratum %s has shape %s (expected 3-D); skipping", k, X[k].shape)
    X = {k: v for k, v in X.items() if v.ndim == 3}

    log.info("Binned %d cycles across %d strata for baseline",
             sum(v.shape[0] for v in X.values()), len(X))

    # Trimming → normal cycles
    active = trimmed_normal_cycles(
        X, strata_per_cycle={k: np.ones(v.shape[0], dtype=bool) for k, v in X.items()},
        X_by_field=X_by_field, min_n=5, q=0.15, iters=3, threshold=3.5,
    )
    X_active = {k: v[active[k]] for k, v in X.items() if active[k].any()}
    if "all" not in X_active:
        X_active["all"] = np.concatenate(list(X_active.values()), axis=0)

    bl = fit_baseline(X_active, X_by_field, min_n=5, kappa=2.5, floor_pct=5.0)
    bl.band_names = bands
    paths["out_npz"].parent.mkdir(parents=True, exist_ok=True)
    bl.to_npz(str(paths["out_npz"]))

    # Score all cycles (including inactive/censored) and build per-cycle summary
    info = {k: {"field_ids": np.zeros(v.shape[0], dtype=np.int64)} for k, v in X.items()}
    scores = score_all_cycles(X, info, bl, threshold=3.5, min_run_bins=2)

    # Flatten to DataFrame
    rows = []
    for key in X:
        bur = scores["burden"].get(key, np.zeros(X[key].shape[0]))
        mx = scores["max_score"].get(key, np.zeros(X[key].shape[0]))
        flags = scores["flags"].get(key, np.zeros_like(X[key][..., 0], dtype=bool))
        fids = X_fields_by_stratum.get(key, [0] * X[key].shape[0])
        for i in range(X[key].shape[0]):
            rows.append({
                "stratum": key, "cycle_idx": i,
                "field": int(fids[i]) if i < len(fids) else 0,
                "burden": float(bur[i]), "max_score": float(mx[i]),
                "has_run": bool(flags[i].any()),
                "n_flagged_bins": int(flags[i].sum()),
            })
    pd.DataFrame(rows).to_parquet(paths["out_scores"])
    (Path("reports")).mkdir(parents=True, exist_ok=True)
    metrics = {
        "n_cycles_scored": len(rows),
        "n_cycles_with_run": int(sum(1 for r in rows if r["has_run"])),
        "mean_burden": float(np.mean([r["burden"] for r in rows])),
        "baseline_floor": float(bl.floor),
        "n_strata": len(bl.stats),
        "n_normal_cycles": int(sum(v.shape[0] for v in X_active.values())),
    }
    Path("reports/metrics.json").write_text(json.dumps(metrics, indent=2))
    log.info("Baseline & scoring complete: %s", json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
