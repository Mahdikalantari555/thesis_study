"""Data quality report per design D3 (openspec/changes/data-and-phenology-readiness/design.md).

Per year & block: obs/cycle, valid fraction, LST outside 15-55 C, NaN bands,
valid_frac < 0.5 acquisitions. Plus the 538-vs-539 date check and a cycle
recount (docs/findings/02_phenology_cycles.md states 1704 non-censored;
splits_490.json states 799).

Fix (2026-11-14): the recount previously filtered stats_long on
band == "ndvi", a band that does not exist, so every field was skipped and the
report recorded cycle_recount_non_censored = 0 as if it were a real count.
NDVI is now computed from red + nir and per-field skips/errors are reported.

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


def recount_cycles(farms, stats_long):
    """Non-censored cycle count via segmentation (src/ssl_anomaly/phenology/cycles.py).

    NDVI is computed from red + nir bands per field. stats_long has NO 'ndvi'
    band — the previous `band == "ndvi"` filter silently matched nothing and
    reported cycle_recount_non_censored = 0 (fixed 2026-11-14). Per-field
    failures are counted, not swallowed: the returned details must accompany
    the count so a 0 can be told apart from "nothing scanned".
    """
    if not _HAS_SEG:
        return None, "segmentation import unavailable", {}
    epoch = pd.Timestamp("1970-01-01")
    frames = {int(fid): f.sort_values("date") for fid, f in stats_long.groupby("field_id")}
    field_ids = sorted(int(f) for f in farms["field_id"].unique())
    total = 0
    skipped_no_data = errors = 0
    for fid in field_ids:
        sf = frames.get(fid)
        if sf is None:
            skipped_no_data += 1
            continue
        red = sf[sf["band"] == "red"][["date", "median"]].rename(columns={"median": "red"})
        nir = sf[sf["band"] == "nir"][["date", "median"]].rename(columns={"median": "nir"})
        m = pd.merge(red, nir, on="date", how="inner")
        if len(m) < 30:
            skipped_no_data += 1
            continue
        r = m["red"].to_numpy(dtype="float64")
        n = m["nir"].to_numpy(dtype="float64")
        denom = n + r
        ndvi = np.full(len(m), np.nan)
        good = np.abs(denom) > 1e-9
        ndvi[good] = (n[good] - r[good]) / denom[good]
        ok = np.isfinite(ndvi)
        days = (pd.to_datetime(m.loc[ok, "date"]) - epoch).dt.days.values.astype("int64")
        if len(days) < 30:
            skipped_no_data += 1
            continue
        try:
            for c in segment_cycles(int(fid), days, ndvi[ok]):
                if not c.censored:
                    total += 1
        except Exception:
            errors += 1
            continue
    details = {"fields_scanned": len(field_ids), "fields_skipped_no_data": skipped_no_data,
               "fields_errors": errors}
    return total, None, details


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
        count, err, details = recount_cycles(farms, stats_long)
        report["cycle_recount_non_censored"] = count
        report["cycle_recount_details"] = details
        report["cycle_recount_note"] = err or (
            "NDVI computed from red+nir (stats_long has no 'ndvi' band); "
            "count is non-censored cycles over scanned fields — see cycle_recount_details"
        )

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
