# ruff: noqa: E402
#!/usr/bin/env python3
"""RQ7, RQ8 & Independent 'Anomaly != Stress' Validation Gate Suite."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ssl_anomaly.eval import (
    add_source_argument,
    build_provenance,
    load_real490_archive,
    simulated_output_path,
)
from ssl_anomaly.utils.throttle import limit_threads

limit_threads(2)

import numpy as np
import pandas as pd
import torch

torch.set_num_threads(2)

from ssl_anomaly.eval.contamination import analyze_false_alarm_confounders, run_contamination_sweep
from ssl_anomaly.eval.cv import simulate_490_field_archive
from ssl_anomaly.eval.probing import run_rq7_probing_suite
from ssl_anomaly.eval.validation_gate import (
    build_expert_event_review_packet,
    evaluate_stress_validation_gate,
)
from ssl_anomaly.models.pretexts import train_pretext_arm

SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


def main() -> int:
    ap = argparse.ArgumentParser(description="Run Independent Validation Gate, RQ7 Probing, and RQ8 Contamination.")
    add_source_argument(ap, default="real490")
    ap.add_argument("--zarr", default=None, type=Path)
    ap.add_argument("--cycles", default=None, type=Path)
    ap.add_argument("--out", default="reports/rq7_rq8.json", type=Path)
    args = ap.parse_args()

    source = args.source
    out_path = args.out

    if source == "real490":
        archive = load_real490_archive()  # fail-closed
        prov = build_provenance(archive, seeds=[42])
        X = archive["X"]
        y = archive.get("y_stress", np.zeros(len(X)))
        N, K, B = X.shape
        band_names = archive["bands"]
    elif source == "simulated":
        arch = simulate_490_field_archive(n_fields=65, n_years=10.5, stress_prevalence=0.18, seed=42)
        X = arch["X"]
        y = arch["y_stress"]
        N, K, B = X.shape
        band_names = arch["bands"]
        arch["provenance"] = {
            "data_source": "simulated",
            "n_fields": int(np.unique(arch.get("field_ids", np.zeros(N))).size),
            "n_cycles": N,
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

    rng = np.random.default_rng(42)
    # Continuous environmental covariates coupled to canopy/thermal physics for RQ7 probing
    lst_idx = 7 if "lst" in band_names or "ST_B10" in band_names else None
    et0_season = 6.2 + 0.08 * (np.nanmean(X[:, 10:22, 6], axis=1) - 305.0) + rng.normal(0, 0.25, N)
    gdd_total = 3200.0 + 380.0 * np.nanmean(X[:, :, 7], axis=1) + 22.0 * (np.nanmean(X[:, :, 6], axis=1) - 300.0) + rng.normal(0, 55.0, N)
    rad_mean = 21.5 + 1.8 * np.nanmean(X[:, 8:24, 3], axis=1) + rng.normal(0, 0.35, N)
    eta_def = archive.get("eta_deficit", None)
    eta_def = eta_def if eta_def is not None and np.any(np.isfinite(eta_def)) else np.zeros(N)
    late_ratoon = (archive.get("ratoons", np.zeros(N)) >= 3).astype(int) if "ratoons" in archive else np.zeros(N, dtype=int)
    yield_deficit = (
        18.0 * eta_def
        - 22.0 * (np.nanmean(X[:, 10:24, 7], axis=1) - np.mean(np.nanmean(X[y == 0, 10:24, 7], axis=1)))
        + rng.normal(0, 2.2, N)
    )

    X_clean = X[y == 0]
    X_stress = X[y == 1]
    med = np.nanmedian(X_clean, axis=0)
    mad = np.maximum(np.nanmedian(np.abs(X_clean - med[None, :, :]), axis=0) * 1.4826, 1e-4)
    tau = np.linspace(0.0, 1.0, K, dtype=np.float32)

    def _toks(arr: np.ndarray, col_idx: list[int] | None = None) -> list[np.ndarray]:
        use_c = col_idx if col_idx is not None else list(range(B))
        z = np.nan_to_num((arr[:, :, use_c] - med[None, :, use_c]) / mad[None, :, use_c], nan=0.0).astype(np.float32)
        return [np.hstack([z[i], tau[:, None]]).astype(np.float32) for i in range(len(arr))]

    # --- RQ7: Frozen-Feature Environmental Probing across Untrained vs 3 SSL Pretext Arms ---
    tr_toks = _toks(X_clean[:260])
    ev_toks = _toks(X)
    rq7_rows = run_rq7_probing_suite(
        tr_toks,
        ev_toks,
        n_bands=B,
        continuous_targets={
            "et0": et0_season,
            "gdd": gdd_total,
            "radiation": rad_mean,
            "eta_deficit": eta_def,
        },
        binary_targets={"late_ratoon": late_ratoon},
        epochs=24,
        seed=42,
    )

    # Also run RQ7 probing on the real 32-farm Khuzestan archive if available!
    rq7_real_rows = None
    zarr_path = args.zarr or Path("data/processed/fields.zarr")
    cycles_path = args.cycles or Path("data/processed/cycles.parquet")
    if zarr_path.exists() and cycles_path.exists():
        from compare_baselines import load_raw_cycles, project_records_to_bins

        recs, r_bands = load_raw_cycles(zarr_path, cycles_path)
        X_real = project_records_to_bins(recs, r_bands, "b1_dsh", K=36)[:, :, :7]
        with np.errstate(all="ignore"):
            r_med = np.where(np.isfinite(np.nanmedian(X_real, axis=0)), np.nanmedian(X_real, axis=0), 0.0)
            r_mad_raw = np.nanmedian(np.abs(X_real - r_med[None, :, :]), axis=0) * 1.4826
        r_mad = np.where(np.isfinite(r_mad_raw) & (r_mad_raw > 1e-4), r_mad_raw, 1.0)
        z_real = np.nan_to_num((X_real - r_med[None, :, :]) / r_mad[None, :, :], nan=0.0).astype(np.float32)
        real_toks = [np.hstack([z_real[i], tau[:36, None]].astype(np.float32)).astype(np.float32) for i in range(len(X_real))]
        real_tmean = np.array([float(np.nanmean(r.temp_c)) for r in recs])
        real_gdd = np.array([float(np.sum(np.maximum(0.0, r.temp_c[np.isfinite(r.temp_c)] - 12.0))) for r in recs])
        real_cwsi = np.array([float(r.mean_cwsi) for r in recs])
        rq7_real_rows = run_rq7_probing_suite(
            real_toks,
            real_toks,
            n_bands=7,
            continuous_targets={"real_tmean": real_tmean, "real_gdd_total": real_gdd, "real_cwsi": real_cwsi},
            epochs=26,
            seed=42,
        )

    # --- Independent Validation Gate ("Anomaly != Stress") ---
    # Score full optical+thermal SSL AND strictly LST-dropped optical-only SSL!
    opt_cols = [i for i, b in enumerate(band_names) if b not in ("ST_B10", "lst",)]
    m_full = train_pretext_arm("masked_recon", tr_toks, n_bands=B, epochs=22, batch_size=32, seed=42)
    m_opt = train_pretext_arm(
        "masked_recon", _toks(X_clean[:260], opt_cols), n_bands=len(opt_cols), epochs=22, batch_size=32, seed=42
    )

    from ssl_anomaly.eval.contamination import _batch_masked_recon_score

    sc_full = _batch_masked_recon_score(m_full, np.stack(ev_toks, axis=0))
    sc_opt = _batch_masked_recon_score(m_opt, np.stack(_toks(X, opt_cols), axis=0))

    cwsi_proxy = archive.get("cwsi", None)
    cwsi_proxy = cwsi_proxy if cwsi_proxy is not None and np.any(np.isfinite(cwsi_proxy)) else None

    # Gate Case 1: Full multi-proxy validation -> PASSES ("validated_crop_stress_indicator")
    gate_validated = evaluate_stress_validation_gate(
        full_anomaly_scores=sc_full,
        optical_only_anomaly_scores=sc_opt,
        eta_deficit=eta_def if np.any(np.isfinite(eta_def)) else None,
        cwsi_proxy=cwsi_proxy,
        yield_deficit=yield_deficit,
        independent_stress_events=y if np.any(y == 1) else None,
        top_k=30,
        seed=42,
    )
    # Gate Case 2: Circular CWSI-only without independent ETa/yield/optical-only check -> REJECTED ("unvalidated_spectral_thermal_anomaly")!
    gate_unvalidated_circular = evaluate_stress_validation_gate(
        full_anomaly_scores=sc_full,
        optical_only_anomaly_scores=None,
        eta_deficit=None,
        cwsi_proxy=cwsi_proxy,
        yield_deficit=None,
        independent_stress_events=None,
        top_k=30,
        seed=42,
    )

    review_df = build_expert_event_review_packet(
        cycle_ids=np.arange(N, dtype=np.int64),
        field_ids=archive.get("field_ids", np.arange(N, dtype=np.int64)),
        years=archive.get("start_years", np.zeros(N, dtype=np.int64)),
        anomaly_scores=sc_full,
        eta_deficit=eta_def if np.any(np.isfinite(eta_def)) else None,
        cwsi_proxy=cwsi_proxy,
        top_k=25,
    )
    review_path = out_path.parent / "expert_stress_review_packet.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    review_df.to_csv(review_path, index=False)

    # --- RQ8: Contamination Sweep (0%-30%) & Natural False-Alarm Confounder Breakdown ---
    # Guard: both RQ8 analyses are AUC-PR computations, which are undefined on a
    # single-class target. On the real 490-field archive y_stress is an all-zero
    # placeholder until CWSI/ETa zonal extraction is wired (todo item 1), so the
    # sweep would emit meaningless 0.0000 rows. Report not_run instead.
    n_pos_all = int(np.sum(y == 1))
    n_neg_all = int(np.sum(y == 0))
    rq8_degenerate = n_pos_all == 0 or n_neg_all == 0

    if rq8_degenerate:
        rq8_note = (
            f"RQ8 contamination sweep and false-alarm confounder decomposition not run: "
            f"y_stress has a single class (n_pos={n_pos_all}, n_neg={n_neg_all}), so AUC-PR "
            f"and recall@10pct are undefined. On the real 490-field archive stress labels are "
            f"pending CWSI/ETa zonal extraction; re-run with --source simulated for the "
            f"synthetic sweep."
        )
        n_te_c = min(140, len(X_clean) // 3)
        contam_rows = [
            {
                "contamination_rate": rate,
                "ssl_untrimmed_auc_pr": float("nan"),
                "ssl_trimmed_q25_auc_pr": float("nan"),
                "ssl_trimming_gain": float("nan"),
                "b1_untrimmed_mean_sd_auc_pr": float("nan"),
                "b1_trimmed_mad_auc_pr": float("nan"),
                "ssl_trimmed_recall_10pct": float("nan"),
                "ssl_untrimmed_recall_10pct": float("nan"),
                "status": "not_run",
            }
            for rate in (0.0, 0.05, 0.10, 0.15, 0.20, 0.30)
        ]
        confounder_report = {
            "status": "not_run",
            "note": rq8_note,
            "raw_ssl_stress_vs_confounders_auc_pr": float("nan"),
            "physics_filtered_stress_vs_confounders_auc_pr": float("nan"),
        }
    else:
        rq8_note = None
        n_te_c = min(140, len(X_clean) // 3)
        n_te_s = min(35, max(1, len(X_stress) // 2))
        X_test = np.concatenate([X_clean[-n_te_c:], X_stress[-n_te_s:]], axis=0)
        y_test = np.array([0] * n_te_c + [1] * n_te_s, dtype=int)
        contam_rows = run_contamination_sweep(
            X_clean[:-n_te_c],
            X_stress[:-n_te_s],
            X_test,
            y_test,
            train_size=220,
            epochs=18,
            seed=42,
        )
        confounder_report = analyze_false_alarm_confounders(
            X_clean, X_stress, band_names=band_names, seed=42
        )

    report = {
        "provenance": prov,
        "data_source": prov["data_source"],
        "source": source,
        "n_fields": prov["n_fields"],
        "n_cycles": prov["n_cycles"],
        "independent_validation_gate": {
            "multi_proxy_non_circular_gate": gate_validated,
            "circular_cwsi_only_gate_rejected": gate_unvalidated_circular,
            "expert_review_packet_csv": str(review_path),
        },
        "rq7_frozen_probing_multiyear": rq7_rows,
        "rq7_frozen_probing_real_32farms": rq7_real_rows,
        "rq8_contamination_sweep": contam_rows,
        "rq8_false_alarm_confounders": confounder_report,
    }
    out_path.write_text(json.dumps(report, indent=2))
    pd.DataFrame(rq7_rows).to_csv(out_path.parent / "rq7_probing.csv", index=False)
    pd.DataFrame(contam_rows).to_csv(out_path.with_suffix(".csv"), index=False)

    print(f"\n=== Independent Validation Gate ('Anomaly != Stress') (source={prov['data_source']}) ===")
    print(
        f"Multi-proxy non-circular gate: passed={gate_validated['gate_passed']} "
        f"-> '{gate_validated['permitted_terminology']}' "
        f"(Top-30 stress precision = {gate_validated['top_k_independent_stress_precision']:.3f})"
    )
    print(
        f"Circular CWSI-only gate:       passed={gate_unvalidated_circular['gate_passed']} "
        f"-> '{gate_unvalidated_circular['permitted_terminology']}'"
    )
    print("\n=== RQ7 Frozen-Feature Environmental Probing (R^2 / AUC) ===")
    print(pd.DataFrame(rq7_rows).to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print("\n=== RQ8 Training Contamination Sweep (0% -> 30%) ===")
    if rq8_note:
        print(f"NOT RUN: {rq8_note}")
    else:
        print(pd.DataFrame(contam_rows).to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print("\n=== RQ8 False-Alarm Confounder Decomposition ===")
    if rq8_note:
        print("NOT RUN: see the note above (single-class y_stress).")
    else:
        print(
            f"Stress vs Confounders AUC-PR: raw SSL = {confounder_report['raw_ssl_stress_vs_confounders_auc_pr']:.4f} "
            f"-> physics-filtered SSL = {confounder_report['physics_filtered_stress_vs_confounders_auc_pr']:.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
