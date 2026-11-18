# ruff: noqa: E402
#!/usr/bin/env python3
"""RQ5 (Gap G5): Early-Detection Lead-Time Benchmark under LOYO Validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from ssl_anomaly.eval import (
    add_source_argument,
    build_provenance,
    load_real490_archive,
    require_real_archive,
    simulated_output_path,
)
from ssl_anomaly.eval.early_detection import (
    run_loyo_early_detection,
    simulate_progressive_onset_archive,
)
from ssl_anomaly.eval.growth_validation import inject_growth
from ssl_anomaly.utils.throttle import limit_threads

limit_threads(2)

import pandas as pd
import torch

torch.set_num_threads(2)


def _inject_onset_on_real_cycles(archive: dict, seed: int = 42) -> dict:
    """Inject progressive-onset deviations into held-out real cycles for RQ5."""
    import numpy as np

    X = archive["X"].copy()
    years = archive["start_years"]
    y_stress = archive.get("y_stress", np.zeros(len(X)))
    N, K, C = X.shape

    # Build years array
    years_arr = years if years.ndim == 1 else np.zeros(N, dtype=np.int64)
    bin_days = 15

    # Mark test cycles (last ~20% of years) as stressed for RQ5 evaluation
    uniq_years = sorted(np.unique(years_arr))
    n_test_years = max(1, len(uniq_years) // 5)
    test_years = set(uniq_years[-n_test_years:])

    is_stress = np.zeros(N, dtype=np.int32)
    onset_bin = np.full(N, K // 2, dtype=np.int64)

    rng = np.random.default_rng(seed)
    for i in range(N):
        if int(years_arr[i]) in test_years:
            is_stress[i] = 1
            # Inject progressive onset at random bin
            start_bin = int(rng.integers(K // 4, 3 * K // 4))
            onset_bin[i] = start_bin
            # Inject gradual deviation into NDVI band (index 0)
            X[i], _ = inject_growth(
                X[i], kind="gradual", start=start_bin, duration=max(3, K // 8),
                magnitude=float(rng.uniform(0.3, 0.7)), band=0, shift=1,
            )

    return {
        "X": X,
        "years": years_arr,
        "is_stress": is_stress,
        "onset_bin": onset_bin,
        "bin_days": bin_days,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Run RQ5 early-detection lead-time benchmark.")
    add_source_argument(ap, default="real490")
    ap.add_argument("--n-cycles", default=400, type=int)
    ap.add_argument("--far", default=0.05, type=float)
    ap.add_argument("--out", default="reports/rq5_early_detection.json", type=Path)
    args = ap.parse_args()

    source = args.source
    out_path = args.out

    if source == "real490":
        archive = load_real490_archive()  # fail-closed
        prov = build_provenance(archive, seeds=[42])
        arch = _inject_onset_on_real_cycles(archive, seed=42)
    elif source == "simulated":
        arch = simulate_progressive_onset_archive(n_cycles=args.n_cycles, seed=42)
        arch["provenance"] = {
            "data_source": "simulated",
            "n_fields": int(np.unique(arch.get("field_ids", np.zeros(len(arch["X"])))).size),
            "n_cycles": arch["X"].shape[0],
            "n_dates": 0,
            "first_acquisition_date": "",
            "last_acquisition_date": "",
            "cycle_file_sha256": "simulated",
            "git_sha": "unknown",
            "splits_sha256": "unknown",
            "seeds": [42],
            "y_stress_proxy": "simulated_top20pct_cwsi",
            "eta_deficit_source": "simulated",
            "cwsi_source": "simulated",
        }
        prov = arch["provenance"]
        out_path = simulated_output_path(args.out)
    elif source == "real32":
        print("real32 source not available: fields.zarr/cycles.parquet missing at workspace root.", file=sys.stderr)
        return 1
    else:
        print(f"Unknown source: {source}", file=sys.stderr)
        return 1

    report = run_loyo_early_detection(arch, false_alarm_budget=args.far, seed=42)
    report["provenance"] = prov
    report["data_source"] = prov["data_source"]
    report["source"] = source
    report["n_fields"] = prov["n_fields"]
    report["n_cycles"] = prov["n_cycles"]

    args.out = out_path
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))

    rows = [
        {
            "detector": m,
            "detection_rate_at_5pct_far": d["detection_rate_at_5pct_far"],
            "mean_delay_days": d["mean_delay_days_from_onset"],
            "delay_ci_lo": d["delay_days_ci_95"][0],
            "delay_ci_hi": d["delay_days_ci_95"][1],
            "median_delay_days": d["median_delay_days_from_onset"],
        }
        for m, d in report["methods"].items()
    ]
    df = pd.DataFrame(rows)
    df.to_csv(out_path.with_suffix(".csv"), index=False)

    print(f"\n=== RQ5 Early Detection Lead-Time Benchmark (source={prov['data_source']}) ===")
    print(df.to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    print(
        f"SSL lead-time advantage over NDVI threshold: "
        f"mean = {report['ssl_lead_time_vs_ndvi_mean_days']:+.2f} d "
        f"(95% CI [{report['ssl_lead_time_vs_ndvi_ci_95'][0]:+.2f}, {report['ssl_lead_time_vs_ndvi_ci_95'][1]:+.2f}] d, "
        f"median = {report['ssl_lead_time_vs_ndvi_median_days']:+.2f} d) vs EigenCL 12.0 d reference"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
