#!/usr/bin/env python3
"""Stage-conditioned anomaly detection with npphen-style confidence envelope.

Purpose
-------
Distinguish stress-induced NDVI decline from natural phenological decline
(senescence, harvest, dormancy). For each non-censored cycle, observations
are assigned a phenology stage based on normalized progress within the cycle
(0 = just after harvest, 1 = next harvest). Stage-conditioned thresholds are
built from the pooled NDVI distribution across all cycles at each stage. An
observation is flagged as anomalous only when NDVI falls below the stage's
lower confidence envelope — natural within-stage decline that stays inside
the envelope is NOT flagged.

Phenology stages (by normalized progress within cycle):
  S1 establishment/growth   : progress 0.00–0.25  (bins 0–8)
  S2 vegetative/reproductive: progress 0.25–0.60  (bins 9–21)
  S3 maturity/senescence    : progress 0.60–0.85  (bins 22–30)
  S4 harvest/dormancy       : progress 0.85–1.00  (bins 31–35)

Method
------
1. Load growth_cycles_490.npz (799 non-censored cycles × 36 bins × 8 channels).
2. For each cycle-bin with valid NDVI, compute normalized progress =
   (bin_index * bin_days) / cycle_length_days.
3. Assign stage by progress thresholds.
4. Pool NDVI values per stage across all cycles; compute median and MAD.
5. Lower envelope = median - 2.0 * MAD per stage.
6. Flag cycle-bin as anomalous if NDVI < lower_envelope[stage] AND NDVI is valid.
7. Output stage_conditioned_anomaly.parquet with per-bin results + summary.json.

Usage
-----
  python scripts/stage_conditioned_anomaly.py --smoke      # 20 fields, fast
  python scripts/stage_conditioned_anomaly.py --all        # all fields
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

# Subprocess-safe, thread-light
try:
    from ssl_anomaly.utils.throttle import limit_threads

    limit_threads(2)
except Exception:
    pass


# ── Stage definitions ──────────────────────────────────────────────────────
STAGE_BOUNDS = [
    (0.00, 0.25, "S1_establishment_growth"),
    (0.25, 0.60, "S2_vegetative_reproductive"),
    (0.60, 0.85, "S3_maturity_senescence"),
    (0.85, 1.00, "S4_harvest_dormancy"),
]

STAGE_NAMES = [s[2] for s in STAGE_BOUNDS]
ENVELOPE_K = 2.0  # median - K * MAD


def stage_for_progress(progress: float) -> str | None:
    """Map normalized progress in [0,1] to a phenology stage name."""
    for lo, hi, name in STAGE_BOUNDS:
        if lo <= progress < hi or (hi == 1.0 and progress == 1.0):
            return name
    return None


def build_envelopes(
    ndvi_by_stage: dict[str, list[float]], k: float = ENVELOPE_K
) -> dict[str, dict]:
    """Build per-stage confidence envelopes from pooled NDVI values.

    Returns dict: stage -> {median, mad, lower, upper, n}
    """
    envelopes: dict[str, dict] = {}
    for stage, values in ndvi_by_stage.items():
        arr = np.array(values, dtype=np.float64)
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            envelopes[stage] = {
                "median": np.nan,
                "mad": np.nan,
                "lower": np.nan,
                "upper": np.nan,
                "n": 0,
            }
            continue
        median = float(np.median(arr))
        mad = float(np.median(np.abs(arr - median)))
        envelopes[stage] = {
            "median": median,
            "mad": mad,
            "lower": median - k * mad,
            "upper": median + k * mad,
            "n": int(arr.size),
        }
    return envelopes


def run(
    npz_path: str = "data/interim/growth_cycles_490.npz",
    cycles_path: str = "data/processed/cycles_490.parquet",
    out_dir: str = "reports/stage_conditioned_anomaly",
    *,
    smoke: bool = False,
    n_smoke_fields: int = 20,
    seed: int = 20261111,
) -> dict:
    t0 = time.time()

    npz_path = ROOT_DIR / npz_path
    cycles_path = ROOT_DIR / cycles_path
    out_dir = ROOT_DIR / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Load data ────────────────────────────────────────────────────────
    d = np.load(npz_path)
    X = d["X"]  # (n_cycles, 36, 8)
    channel_names = list(d["channel_names"])
    bin_days = int(d["bin_days"])
    ndvi_idx = channel_names.index("ndvi")

    cycles_df = pd.read_parquet(cycles_path)

    # Map field -> list of cycle row indices in X
    field_ids = np.asarray(d["field_ids"], dtype=str)
    start_dates = np.asarray(d["start_dates"], dtype=str)
    end_dates = np.asarray(d["end_dates"], dtype=str)

    # Build field -> X-row indices
    field_to_rows: dict[str, list[int]] = {}
    for i, fid in enumerate(field_ids):
        field_to_rows.setdefault(str(fid), []).append(i)

    # Determine fields to process
    all_fields = sorted(field_to_rows.keys(), key=lambda x: int(x))
    if smoke:
        rng = np.random.default_rng(seed)
        fields = sorted(rng.choice(all_fields, size=min(n_smoke_fields, len(all_fields)), replace=False), key=lambda x: int(x))
    else:
        fields = all_fields

    log_prefix = "[SMOKE]" if smoke else "[ALL]"

    print(f"{log_prefix} Processing {len(fields)} fields ({'smoke' if smoke else 'all'})")
    print(f"{log_prefix} Cycles available: {X.shape[0]} non-censored × {X.shape[1]} bins × {X.shape[2]} channels")

    # ── Pass 1: build per-stage NDVI pool from ALL fields ────────────────
    # We pool across all fields (not just smoke) so envelopes are stable.
    ndvi_by_stage: dict[str, list[float]] = {s: [] for s in STAGE_NAMES}

    for fid in fields:
        rows = field_to_rows[fid]
        for ri in rows:
            cycle_len = int(cycles_df[
                (cycles_df["field"] == int(fid)) &
                (cycles_df["cycle_id"] == ri - sum(1 for fj in field_ids[:ri] if str(fj) == fid))
            ]["length_days"].iloc[0]) if len(cycles_df[
                (cycles_df["field"] == int(fid)) &
                (cycles_df["cycle_id"] == ri - sum(1 for fj in field_ids[:ri] if str(fj) == fid))
            ]) > 0 else X.shape[1] * bin_days

            x_cycle = X[ri, :, ndvi_idx]  # (36,)
            for b in range(X.shape[1]):
                val = x_cycle[b]
                if not np.isfinite(val):
                    continue
                progress = (b * bin_days) / cycle_len
                stage = stage_for_progress(progress)
                if stage is not None:
                    ndvi_by_stage[stage].append(float(val))

    envelopes = build_envelopes(ndvi_by_stage, k=ENVELOPE_K)

    print(f"{log_prefix} Stage envelope pool sizes:")
    for stage in STAGE_NAMES:
        e = envelopes[stage]
        print(f"  {stage}: n={e['n']}, median={e['median']:.3f}, MAD={e['mad']:.3f}, "
              f"lower={e['lower']:.3f}, upper={e['upper']:.3f}")

    # ── Pass 2: flag anomalies per cycle-bin ─────────────────────────────
    results: list[dict] = []
    n_flagged = 0
    n_valid = 0
    n_cycles_processed = 0

    for fid in fields:
        rows = field_to_rows[fid]
        field_cycles = cycles_df[cycles_df["field"] == int(fid)].sort_values("cycle_id")

        for ri in rows:
            x_cycle = X[ri, :, ndvi_idx]
            # Find matching cycle row in cycles_df
            x_in_field = sum(1 for fj in field_ids[:ri] if str(fj) == fid)
            cycle_row = field_cycles[field_cycles["cycle_id"] == x_in_field]
            if cycle_row.empty:
                continue
            cycle_row = cycle_row.iloc[0]
            cycle_len = int(cycle_row["length_days"])
            is_censored = bool(cycle_row["censored"])

            n_cycles_processed += 1

            for b in range(X.shape[1]):
                val = x_cycle[b]
                if not np.isfinite(val):
                    continue
                n_valid += 1
                progress = (b * bin_days) / cycle_len
                stage = stage_for_progress(progress)
                if stage is None:
                    continue
                env = envelopes[stage]
                lower = env["lower"]
                if not np.isfinite(lower):
                    continue
                is_anomaly = bool(val < lower)
                if is_anomaly:
                    n_flagged += 1
                bin_date = None
                try:
                    bin_date = str(d["bin_dates"][ri][b])
                except Exception:
                    bin_date = None
                results.append({
                    "field": int(fid),
                    "cycle_id": int(cycle_row["cycle_id"]),
                    "bin_index": int(b),
                    "progress": round(progress, 4),
                    "stage": stage,
                    "ndvi": round(float(val), 4),
                    "cycle_length_days": cycle_len,
                    "censored": is_censored,
                    "envelope_median": round(env["median"], 4),
                    "envelope_mad": round(env["mad"], 4),
                    "envelope_lower": round(lower, 4),
                    "envelope_upper": round(env["upper"], 4),
                    "is_anomaly": is_anomaly,
                    "bin_date": bin_date,
                })

    # ── Write outputs ────────────────────────────────────────────────────
    results_df = pd.DataFrame(results)
    anomalies_df = results_df[results_df["is_anomaly"]] if len(results_df) else results_df

    parquet_out = out_dir / "stage_conditioned_anomaly.parquet"
    results_df.to_parquet(parquet_out, index=False)

    anomalies_out = out_dir / "stage_conditioned_anomalies_only.parquet"
    anomalies_df.to_parquet(anomalies_out, index=False)

    summary = {
        "script": "scripts/stage_conditioned_anomaly.py",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_source": str(npz_path),
        "smoke": smoke,
        "seed": seed,
        "n_fields": len(fields),
        "n_cycles_processed": n_cycles_processed,
        "n_valid_obs": n_valid,
        "n_flagged": int(n_flagged),
        "flag_rate": round(n_flagged / n_valid, 6) if n_valid else 0.0,
        "bin_days": bin_days,
        "envelope_k": ENVELOPE_K,
        "stage_envelopes": envelopes,
        "wall_time_seconds": round(time.time() - t0, 2),
        "output_parquet": str(parquet_out),
        "output_anomalies": str(anomalies_out),
        "git_sha": None,
    }

    try:
        import subprocess
        result = subprocess.run(
            ["git", "-C", str(ROOT_DIR), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            summary["git_sha"] = result.stdout.strip()
    except Exception:
        pass

    summary_path = out_dir / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"{log_prefix} Done in {summary['wall_time_seconds']}s")
    print(f"{log_prefix} Valid obs: {n_valid}, Flagged: {n_flagged} ({summary['flag_rate']*100:.2f}%)")
    print(f"{log_prefix} Wrote {parquet_out}")
    print(f"{log_prefix} Wrote {anomalies_out}")
    print(f"{log_prefix} Wrote {summary_path}")

    return summary


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Stage-conditioned anomaly detection with confidence envelope."
    )
    ap.add_argument("--npz", default="data/interim/growth_cycles_490.npz", type=Path)
    ap.add_argument("--cycles", default="data/processed/cycles_490.parquet", type=Path)
    ap.add_argument("--out", default="reports/stage_conditioned_anomaly", type=Path)
    ap.add_argument("--smoke", action="store_true", help="Smoke test on 20 fields.")
    ap.add_argument("--all", action="store_true", help="Process all fields.")
    ap.add_argument("--n-smoke", type=int, default=20, help="Number of fields for smoke test.")
    ap.add_argument("--seed", type=int, default=20261111, help="Random seed for smoke sampling.")
    args = ap.parse_args()

    smoke = args.smoke or not args.all
    run(
        npz_path=str(args.npz),
        cycles_path=str(args.cycles),
        out_dir=str(args.out),
        smoke=smoke,
        n_smoke_fields=args.n_smoke,
        seed=args.seed,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
