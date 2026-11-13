"""Data quality report per design D3 (openspec/changes/data-and-phenology-readiness/design.md).

Per year & block: obs/cycle, valid fraction, LST outside 15-55 C, NaN bands,
valid_frac < 0.5 acquisitions. Plus the 538-vs-539 date check and a cycle
recount (docs/findings/02_phenology_cycles.md states 1704 non-censored;
splits_490.json states 799).

Outputs reports/data_quality.json (carries data_source, n, date range, seeds, git SHA).

Usage:
  python scripts/data_quality_report.py --smoke   # agent smoke test (subset, fast)
  python scripts/data_quality_report.py --all     # user runs full report
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(r"D:\RS\Thesis\thesis_implementation")
SRC_ROOT = REPO_ROOT / "src"
DATA_ROOT = Path(r"D:\RS\Thesis\Data\Processed")
REPORTS = REPO_ROOT / "reports"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

LST_K_MIN = 273.15 + 15.0   # 15 C -> Kelvin
LST_K_MAX = 273.15 + 55.0   # 55 C -> Kelvin

try:
    from ssl_anomaly.phenology.cycles import segment_cycles  # noqa: E402
    _HAS_SEG = True
except Exception:  # pragma: no cover - import environment dependent
    _HAS_SEG = False


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL, text=True,
        ).strip()
    except Exception:
        return "unknown"


def load_tables():
    farms = pd.read_parquet(DATA_ROOT / "coordinates" / "farms.parquet")
    inventory = pd.read_parquet(DATA_ROOT / "satellite" / "scene_inventory.parquet")
    stats_long = pd.read_parquet(DATA_ROOT / "satellite" / "stats_long.parquet")
    return farms, inventory, stats_long


def recount_cycles(farms, stats_long, max_fields=None):
    """Non-censored cycle count via segmentation (src/ssl_anomaly/phenology/cycles.py)."""
    if not _HAS_SEG:
        return None, "segmentation import unavailable"
    epoch = pd.Timestamp("1970-01-01")
    field_ids = sorted(farms["field_id"].unique())
    if max_fields:
        field_ids = field_ids[:max_fields]
    total = 0
    for fid in field_ids:
        sf = stats_long[stats_long["field_id"] == fid].sort_values("date")
        ndvi = sf[sf["band"] == "ndvi"]
        if len(ndvi) < 30:
            continue
        days = (pd.to_datetime(ndvi["date"]) - epoch).dt.days.values.astype("int64")
        try:
            for c in segment_cycles(int(fid), days, ndvi["median"].to_numpy(dtype="float64")):
                if not c.censored:
                    total += 1
        except Exception:
            continue
    return total, None


def build_report(smoke: bool) -> dict:
    farms, inventory, stats_long = load_tables()
    report = {
        "script": "scripts/data_quality_report.py",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_source": str(DATA_ROOT),
        "git_sha": git_sha(),
        "smoke": smoke,
        "scene_inventory_n": int(len(inventory)),
        "products_n": 539,
        "date_mismatch_538_vs_539": bool(len(inventory) != 539),
        "inventory_date_min": str(pd.to_datetime(inventory["acquisition_date"]).min().date()),
        "inventory_date_max": str(pd.to_datetime(inventory["acquisition_date"]).max().date()),
    }

    stats_long = stats_long.copy()
    stats_long["date"] = pd.to_datetime(stats_long["date"])
    report["date_range_min"] = str(stats_long["date"].min().date())
    report["date_range_max"] = str(stats_long["date"].max().date())
    report["n_acquisitions"] = int(stats_long["date"].nunique())

    if smoke:
        farms = farms.head(20)
        stats_long = stats_long[stats_long["field_id"].isin(farms["field_id"])]
    report["n_fields_evaluated"] = int(farms["field_id"].nunique())

    farms_idx = farms.set_index("field_id")[["block"]]
    sl = stats_long.merge(farms_idx, left_on="field_id", right_index=True, how="left")
    sl["year"] = sl["date"].dt.year

    per_year_block = []
    for b in sorted(sl["block"].dropna().unique()):
        for y in sorted(sl["year"].unique()):
            sy = sl[(sl["block"] == b) & (sl["year"] == y)]
            if sy.empty:
                continue
            lst = sy[sy["band"] == "lst"]["mean"]
            per_year_block.append({
                "block": b,
                "year": int(y),
                "n_fields": int(sy["field_id"].nunique()),
                "n_acquisitions": int(sy["date"].nunique()),
                "valid_frac_mean": float(sy["valid_frac"].mean()),
                "valid_frac_lt_05_count": int((sy["valid_frac"] < 0.5).sum()),
                "lst_outside_15_55C_count": int(((lst < LST_K_MIN) | (lst > LST_K_MAX)).sum()),
                "nan_bands_count": int(sy[["mean", "median", "std"]].isna().any(axis=1).sum()),
            })
    report["per_year_block"] = per_year_block

    if smoke:
        report["cycle_recount_non_censored"] = None
        report["cycle_recount_note"] = (
            "smoke: segmentation recount skipped; known discrepancy "
            "docs/findings/02=1704 vs splits_490.json=799 resolved by running --all"
        )
    else:
        count, err = recount_cycles(farms, stats_long)
        report["cycle_recount_non_censored"] = count
        report["cycle_recount_note"] = err or "ran via src/ssl_anomaly/phenology/cycles.py"

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "data_quality.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    build_report(smoke=bool(args.smoke and not args.all))


if __name__ == "__main__":
    main()
