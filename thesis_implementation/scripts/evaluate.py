#!/usr/bin/env python3
"""Run evaluation (synthetic injection + statistical comparison) on B1.

Writes reports/metrics.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from ssl_anomaly.baseline.robust import RobustBaseline
from ssl_anomaly.baseline.score import aggregate_band_scores, flag_runs
from ssl_anomaly.eval import InjectionConfig, synthetic_benchmark
from ssl_anomaly.utils.logging import get_logger
from ssl_anomaly.utils.throttle import limit_threads

log = get_logger("ssl_anomaly.scripts.evaluate")


def main() -> int:
    limit_threads(2)
    base_p = Path("data/processed/baseline.npz")
    scores_p = Path("data/processed/scores.parquet")
    if not base_p.exists() or not scores_p.exists():
        log.error("Run build_baseline.py first.")
        return 1

    bl = RobustBaseline.from_npz(str(base_p))
    scores = pd.read_parquet(scores_p)
    log.info("Loaded baseline and scores: %d cycles scored", len(scores))

    rng = np.random.default_rng(0)
    n_samp = 50
    n_bins = bl.bin_centers.size
    n_bands = len(bl.band_names)
    med_key = "all" if "all" in bl.stats else next(iter(bl.stats))

    if med_key not in bl.stats or bl.stats[med_key].median.size == 0:
        metrics = {"n_scored": len(scores), "n_with_run": int(scores["has_run"].sum())}
        Path("reports").mkdir(exist_ok=True)
        Path("reports/metrics.json").write_text(json.dumps(metrics, indent=2))
        return 0

    m = bl.stats[med_key].median
    s = np.maximum(bl.stats[med_key].scale, bl.floor)
    noise = rng.normal(0, 1.0, size=(n_samp, n_bins, n_bands))
    # Normal cycles: centered at median with unit-scale noise
    X_norm = m[None, :, :] + noise * np.nan_to_num(s[None, :, :], nan=1.0)

    def score_fn(cycle: np.ndarray):
        med_s = bl.stats[med_key].median
        scale_s = np.maximum(bl.stats[med_key].scale, bl.floor)
        with np.errstate(all="ignore"):
            z = (cycle - med_s) / scale_s
        S = aggregate_band_scores(z)
        f, _ = flag_runs(S, threshold=3.5, min_run_bins=2)
        return S, f

    inj = InjectionConfig()
    if "NDVI" in bl.band_names:
        inj.ndvi_band_idx = bl.band_names.index("NDVI")
    if "ST_B10" in bl.band_names:
        inj.lst_band_idx = bl.band_names.index("ST_B10")
    results = synthetic_benchmark(X_norm, score_fn, inj, rng=rng)
    rec = results["recall_at_alert_rate"]
    mean_recall = float(np.mean([r[-1] for r in rec])) if rec else 0.0
    delays = [r[-1] for r in results["detection_delay"] if r[-1] >= 0]
    mean_delay = float(np.mean(delays)) if delays else -1.0
    metrics = {
        "n_scored": len(scores),
        "n_with_run": int(scores["has_run"].sum()),
        "mean_burden": float(scores["burden"].mean()),
        "synthetic_mean_recall_at_5pct": mean_recall,
        "synthetic_mean_detection_delay_bins": mean_delay,
        "n_injection_scenarios": len(rec),
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/metrics.json").write_text(json.dumps(metrics, indent=2))
    log.info("Wrote metrics: %s", json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
