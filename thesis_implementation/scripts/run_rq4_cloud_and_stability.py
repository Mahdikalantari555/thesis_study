# ruff: noqa: E402
#!/usr/bin/env python3
"""RQ4 (Gap G8): Cloud-Robustness (16-day -> monthly) & E-ALIGN / E-SEG / E-NORM Suite."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ssl_anomaly.utils.throttle import limit_threads

limit_threads(2)

import numpy as np
import pandas as pd
import torch
import xarray as xr

torch.set_num_threads(2)

from ssl_anomaly.baseline import (
    aggregate_band_scores,
    build_stratum_table,
    fit_baseline,
    score_cycle,
    trimmed_normal_cycles,
)
from ssl_anomaly.eval.cloud_robustness import (
    evaluate_e_align_three_metrics,
    evaluate_e_norm_trimming_stability,
    run_cloud_completeness_benchmark,
)
from ssl_anomaly.eval import (
    add_source_argument,
    build_provenance,
    load_real490_archive,
    simulate_490_field_archive,
    simulated_output_path,
)
from ssl_anomaly.eval.cv import simulate_490_field_archive as _simulate_archive
from ssl_anomaly.eval.stats import spearman_correlation
from ssl_anomaly.phenology import add_spectral_indices, phase_bin

SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


def _evaluate_e_seg_harvest_shifts(zarr_path: Path, cycles_path: Path) -> dict[str, dict]:
    """E-SEG: Shift harvest dates by {-32, -16, +16, +32} days on real 32-farm archive."""
    ds = xr.open_zarr(zarr_path)
    ds = add_spectral_indices(ds)
    cycles_df = build_stratum_table(pd.read_parquet(cycles_path))
    times = ds.coords["time"].values
    epoch = times[0]
    bands = [str(b) for b in ds.coords["band"].values]
    bmap = {b: i for i, b in enumerate(bands)}
    fields = ds.coords["field"].values
    med = ds["median"].values

    def _bin_with_shift(shift_days: int) -> tuple[np.ndarray, np.ndarray]:
        rows, fids = [], []
        for _, c in cycles_df.iterrows():
            if c["censored"]:
                continue
            fid = int(c["field"])
            fi = int(np.where(fields == fid)[0][0])
            s0 = int(c["t_start"]) + shift_days
            s1 = int(c["t_end"]) + shift_days
            sh = int(c.get("start_harvest", c["t_start"])) + shift_days
            t0 = epoch + np.timedelta64(s0, "D")
            t1 = epoch + np.timedelta64(s1, "D")
            hd = epoch + np.timedelta64(sh, "D")
            m = (times >= t0) & (times < t1)
            if int(m.sum()) < 3:
                # Keep alignment by falling back to unshifted window if shifted window empty
                t0 = epoch + np.timedelta64(int(c["t_start"]), "D")
                t1 = epoch + np.timedelta64(int(c["t_end"]), "D")
                m = (times >= t0) & (times < t1)
                if int(m.sum()) < 3:
                    continue
            dsh = (times[m] - hd).astype("timedelta64[D]").astype(int)
            pb = phase_bin({b: med[fi, m, bmap[b]] for b in bands}, dsh, bin_days=15, max_cycle_days=540)
            rows.append(np.stack([pb[b] for b in bands], axis=-1))
            fids.append(fid)
        return np.stack(rows, axis=0), np.array(fids, dtype=np.int64)

    X0, fids = _bin_with_shift(0)
    X_by_f = {int(f): X0[fids == f] for f in np.unique(fids)}
    act = trimmed_normal_cycles(
        {"all": X0}, strata_per_cycle={"all": np.ones(len(X0), dtype=bool)}, X_by_field=X_by_f, min_n=4
    )["all"]
    bl0 = fit_baseline({"all": X0[act]}, X_by_f, min_n=4)

    def _scores_and_burdens(X_arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        sc, bu = [], []
        for xc, f in zip(X_arr, fids):
            z = score_cycle(xc, bl0, "all", field_id=int(f))
            s = aggregate_band_scores(z)
            fin = np.sort(s[np.isfinite(s)])
            sc.append(float(np.mean(fin[-min(3, fin.size) :])) if fin.size else 0.0)
            fin_z = z[np.isfinite(z)]
            bu.append(float(np.mean(np.abs(fin_z) > 3.5)) if fin_z.size else 0.0)
        return np.array(sc), np.array(bu)

    sc0, bu0 = _scores_and_burdens(X0)
    out: dict[str, dict] = {}
    for sh in (-32, -16, 16, 32):
        Xs, _ = _bin_with_shift(sh)
        scs, bus = _scores_and_burdens(Xs)
        rho, pval = spearman_correlation(sc0, scs)
        out[f"shift_{sh:+d}d"] = {
            "shift_days": sh,
            "spearman_vs_unshifted": rho,
            "pval": pval,
            "mean_abs_burden_delta": float(np.mean(np.abs(bus - bu0))),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Run RQ4 cloud-completeness & E-ALIGN/E-SEG/E-NORM suite.")
    add_source_argument(ap, default="real490")
    ap.add_argument("--zarr", default=None, type=Path)
    ap.add_argument("--cycles", default=None, type=Path)
    ap.add_argument("--out", default="reports/rq4_cloud_and_stability.json", type=Path)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    source = args.source
    seed = args.seed
    out_path = args.out

    if source == "real490":
        archive = load_real490_archive()  # fail-closed
        prov = build_provenance(archive, seeds=[seed])
    elif source == "simulated":
        sim = simulate_490_field_archive(n_fields=65, n_years=10.0, seed=seed)
        archive = {
            "X": sim["X"],
            "bands": ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7", "ST_B10", "NDVI", "NDWI", "NDMI"],
            "field_ids": sim["field_ids"],
            "start_years": sim["start_years"],
            "y_stress": sim["y_stress"],
            "eta_deficit": sim["eta_deficit"],
            "cwsi": sim["cwsi"],
        }
        archive["provenance"] = {
            "data_source": "simulated",
            "n_fields": int(np.unique(archive["field_ids"]).size),
            "n_cycles": archive["X"].shape[0],
            "n_dates": 0,
            "first_acquisition_date": "",
            "last_acquisition_date": "",
            "cycle_file_sha256": "simulated",
            "git_sha": "unknown",
            "splits_sha256": "unknown",
            "seeds": [seed],
            "y_stress_proxy": "simulated_top20pct_cwsi",
            "eta_deficit_source": "simulated",
            "cwsi_source": "simulated",
        }
        prov = archive["provenance"]
        out_path = simulated_output_path(args.out)
    elif source == "real32":
        SCRIPTS_DIR = str(Path(__file__).resolve().parent)
        sys.path.insert(0, SCRIPTS_DIR)
        from compare_baselines import load_raw_cycles

        recs, bands = load_raw_cycles(
            args.zarr or Path("data/processed/fields.zarr"),
            args.cycles or Path("data/processed/cycles.parquet"),
        )
        fids = np.array([r.field_id for r in recs], dtype=np.int64)
        archive = {
            "X": None,
            "bands": bands,
            "field_ids": fids,
            "start_years": np.zeros(len(fids), dtype=np.int64),
            "y_stress": np.zeros(len(fids), dtype=np.int32),
            "eta_deficit": np.zeros(len(fids)),
            "cwsi": np.zeros(len(fids)),
        }
        archive["provenance"] = {
            "data_source": "real32",
            "n_fields": len(set(fids)),
            "n_cycles": len(fids),
            "seeds": [seed],
        }
        prov = archive["provenance"]
    else:
        log.error("Unknown source: %s", source)
        return 1

    from compare_baselines import load_raw_cycles, project_records_to_bins

    # E-ALIGN, E-SEG, E-NORM (from real32 path if available, otherwise skip)
    if source == "real32":
        recs, bands = load_raw_cycles(
            args.zarr or Path("data/processed/fields.zarr"),
            args.cycles or Path("data/processed/cycles.parquet"),
        )
        fids = np.array([r.field_id for r in recs], dtype=np.int64)
        X_axes = {
            "DOY": project_records_to_bins(recs, bands, "b0_doy", K=36),
            "DSH": project_records_to_bins(recs, bands, "b1_dsh", K=36),
            "GDD": project_records_to_bins(recs, bands, "b2_gdd", K=36),
            "Landmark": project_records_to_bins(recs, bands, "b2_landmark", K=36),
        }
        e_align = evaluate_e_align_three_metrics(X_axes, fids, seed=seed)
        e_norm = evaluate_e_norm_trimming_stability(X_axes["DSH"], fids)

        def _evaluate_e_seg_harvest_shifts(zarr_path: Path, cycles_path: Path) -> dict[str, dict]:
            """E-SEG: Shift harvest dates by {-32, -16, +16, +32} days on real 32-farm archive."""
            ds = xr.open_zarr(zarr_path)
            ds = add_spectral_indices(ds)
            cycles_df = build_stratum_table(pd.read_parquet(cycles_path))
            times = ds.coords["time"].values
            epoch = times[0]
            bands2 = [str(b) for b in ds.coords["band"].values]
            bmap = {b: i for i, b in enumerate(bands2)}
            fields = ds.coords["field"].values
            med = ds["median"].values

            def _bin_with_shift(shift_days: int) -> tuple[np.ndarray, np.ndarray]:
                rows, fids2 = [], []
                for _, c in cycles_df.iterrows():
                    if c["censored"]:
                        continue
                    fid = int(c["field"])
                    fi = int(np.where(fields == fid)[0][0])
                    s0 = int(c["t_start"]) + shift_days
                    s1 = int(c["t_end"]) + shift_days
                    sh = int(c.get("start_harvest", c["t_start"])) + shift_days
                    t0 = epoch + np.timedelta64(s0, "D")
                    t1 = epoch + np.timedelta64(s1, "D")
                    hd = epoch + np.timedelta64(sh, "D")
                    m = (times >= t0) & (times < t1)
                    if int(m.sum()) < 3:
                        t0 = epoch + np.timedelta64(int(c["t_start"]), "D")
                        t1 = epoch + np.timedelta64(int(c["t_end"]), "D")
                        m = (times >= t0) & (times < t1)
                        if int(m.sum()) < 3:
                            continue
                    dsh = (times[m] - hd).astype("timedelta64[D]").astype(int)
                    pb = phase_bin({b: med[fi, m, bmap[b]] for b in bands2}, dsh, bin_days=15, max_cycle_days=540)
                    rows.append(np.stack([pb[b] for b in bands2], axis=-1))
                    fids2.append(fid)
                return np.stack(rows, axis=0), np.array(fids2, dtype=np.int64)

            X0, fids2 = _bin_with_shift(0)
            X_by_f = {int(f): X0[fids2 == f] for f in np.unique(fids2)}
            act = trimmed_normal_cycles(
                {"all": X0}, strata_per_cycle={"all": np.ones(len(X0), dtype=bool)}, X_by_field=X_by_f, min_n=4
            )["all"]
            bl0 = fit_baseline({"all": X0[act]}, X_by_f, min_n=4)

            def _scores_and_burdens(X_arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
                sc, bu = [], []
                for xc, f in zip(X_arr, fids2):
                    z = score_cycle(xc, bl0, "all", field_id=int(f))
                    s = aggregate_band_scores(z)
                    fin = np.sort(s[np.isfinite(s)])
                    sc.append(float(np.mean(fin[-min(3, fin.size) :])) if fin.size else 0.0)
                    fin_z = z[np.isfinite(z)]
                    bu.append(float(np.mean(np.abs(fin_z) > 3.5)) if fin_z.size else 0.0)
                return np.array(sc), np.array(bu)

            sc0, bu0 = _scores_and_burdens(X0)
            out: dict[str, dict] = {}
            for sh in (-32, -16, 16, 32):
                Xs, _ = _bin_with_shift(sh)
                scs, bus = _scores_and_burdens(Xs)
                rho, pval = spearman_correlation(sc0, scs)
                out[f"shift_{sh:+d}d"] = {
                    "shift_days": sh,
                    "spearman_vs_unshifted": rho,
                    "pval": pval,
                    "mean_abs_burden_delta": float(np.mean(np.abs(bus - bu0))),
                }
            return out

        e_seg = _evaluate_e_seg_harvest_shifts(
            args.zarr or Path("data/processed/fields.zarr"),
            args.cycles or Path("data/processed/cycles.parquet"),
        )
    else:
        e_align = {"note": "E-ALIGN requires real32 zarr data"}
        e_norm = {"note": "E-NORM requires real32 zarr data"}
        e_seg = {"note": "E-SEG requires real32 zarr data"}

    # RQ4 Cloud-completeness sweep.
    # The sweep needs validated stress labels to compute AUC-PR. On real490 the
    # CWSI/ETa proxies are absent (all-zero y_stress), so running it would
    # produce a degenerate metric. Simulator data is used ONLY on the
    # explicit --source simulated path.
    if source == "simulated":
        sim_cloud = simulate_490_field_archive(n_fields=65, n_years=10.0, seed=seed)
        cloud_sweep = run_cloud_completeness_benchmark(
            sim_cloud["X"], sim_cloud["y_stress"], epochs=20, seeds=(seed, seed + 1, seed + 2)
        )
    else:
        cloud_sweep = {
            "note": (
                f"RQ4 cloud-completeness sweep not run for source={source}: it requires "
                "validated stress labels (AUC-PR). real490 CWSI/ETa proxies are absent "
                "(y_stress is a placeholder), so the sweep is reported as not-run rather "
                "than computed on simulated data. Re-run with --source simulated for the "
                "synthetic sweep."
            )
        }

    report = {
        "provenance": prov,
        "data_source": prov["data_source"],
        "source": source,
        "n_fields": prov["n_fields"],
        "n_cycles": prov["n_cycles"],
        "rq4_cloud_completeness_sweep": cloud_sweep,
        "e_align_three_metrics": e_align,
        "e_seg_harvest_shift_sensitivity": e_seg,
        "e_norm_trimming_q_stability": e_norm,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))

    print(f"\n=== RQ4 Cloud-Completeness Sweep (source={prov['data_source']}) ===")
    if "note" in cloud_sweep:
        print(f"NOT RUN: {cloud_sweep['note']}")
        pd.DataFrame([{"status": "not_run", "note": cloud_sweep["note"]}]).to_csv(
            out_path.with_suffix(".csv"), index=False
        )
    else:
        df_cloud = pd.DataFrame(list(cloud_sweep.values()))
        df_cloud.to_csv(out_path.with_suffix(".csv"), index=False)
        print(df_cloud.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print("\n=== E-ALIGN Three-Metric Summary ===")
    if "note" in e_align:
        print(f"NOT RUN: {e_align['note']}")
    else:
        print(pd.DataFrame(dict(e_align)).T.to_string(float_format=lambda v: f"{v:.4f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
