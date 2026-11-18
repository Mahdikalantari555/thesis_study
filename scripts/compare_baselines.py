#!/usr/bin/env python3
"""Compare baseline anomaly detectors B0, B1, B2 (GDD & Landmark), and B3 (IsolationForest & ECOD).

Evaluates all six baseline comparators on the real non-censored sugarcane cycles from the
32-farm subset along two axes:
  1. Synthetic perturbation detection (AUC-PR & AUC-ROC across 4 stress types × 5 seeds,
     injected at the raw observation level prior to each method's binning/feature pipeline).
  2. Real-world agronomic concordance: Spearman correlation (with 95% bootstrap CI)
     against independent METRIC evapotranspiration water-stress index (CWSI).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score, roc_auc_score

from ssl_anomaly.baseline import (
    ECODDetector,
    IsolationForestDetector,
    aggregate_band_scores,
    bin_by_calendar_doy,
    bin_by_gdd,
    bin_by_landmarks,
    bin_by_progress,
    build_stratum_table,
    extract_cycle_features,
    fit_b0_calendar_baseline,
    fit_baseline,
    progress_axis,
    score_cycle,
    trimmed_normal_cycles,
)
from ssl_anomaly.baseline.score import cycle_anomaly_burden, cycle_max_score
from ssl_anomaly.eval.stats import bootstrap_ci
from ssl_anomaly.phenology import add_spectral_indices, phase_bin
from ssl_anomaly.utils.logging import get_logger
from ssl_anomaly.utils.throttle import limit_threads

log = get_logger("ssl_anomaly.scripts.compare_baselines")

PERTURB_TYPES = ("ndvi_drop", "lst_spike", "phase_shift", "early_senescence")


@dataclass
class RawCycleRecord:
    field_id: int
    cycle_id: int
    stratum: str
    start_day: int
    end_day: int
    start_harvest: int
    duration_days: int
    obs_times: np.ndarray   # datetime64[ns] (T_c,)
    obs_days: np.ndarray    # int64 (T_c,) days since epoch
    dsh: np.ndarray         # int64 (T_c,) days since harvest
    values: np.ndarray      # float64 (T_c, B)
    weather_days: np.ndarray
    temp_c: np.ndarray
    mean_cwsi: float


def load_raw_cycles(
    zarr_path: Path,
    cycles_path: Path,
    min_obs: int = 5,
) -> tuple[list[RawCycleRecord], list[str]]:
    ds = xr.open_zarr(zarr_path)
    ds = add_spectral_indices(ds)
    cycles_df = build_stratum_table(pd.read_parquet(cycles_path))

    times = ds.coords["time"].values
    epoch = times[0]
    t_days = (times - epoch).astype("timedelta64[D]").astype(np.int64)
    fields = ds.coords["field"].values
    bands = [str(b) for b in ds.coords["band"].values]
    med = ds["median"].values
    cwsi_da = ds["cwsi_et"].values if "cwsi_et" in ds.data_vars else None
    temp_all = (
        ds["weather_tmean"].values
        if "weather_tmean" in ds.data_vars
        else np.full(t_days.size, 25.0, dtype=np.float64)
    )

    records: list[RawCycleRecord] = []
    for _, row in cycles_df.iterrows():
        if bool(row.get("censored", False)):
            continue
        fid = int(row["field"])
        fi_arr = np.where(fields == fid)[0]
        if fi_arr.size == 0:
            continue
        fi = int(fi_arr[0])
        s_day = int(row["t_start"])
        e_day = int(row["t_end"])
        s_harv = int(row.get("start_harvest", s_day))
        t_start_dt = epoch + np.timedelta64(s_day, "D")
        t_end_dt = epoch + np.timedelta64(e_day, "D")
        harv_dt = epoch + np.timedelta64(s_harv, "D")

        in_cyc = (times >= t_start_dt) & (times < t_end_dt)
        if int(in_cyc.sum()) < min_obs:
            continue
        vals = med[fi, in_cyc, :].astype(np.float64)
        if int(np.any(np.isfinite(vals), axis=1).sum()) < min_obs:
            continue

        t_cyc = times[in_cyc]
        dsh = (t_cyc - harv_dt).astype("timedelta64[D]").astype(np.int64)
        cwsi_m = np.nan
        if cwsi_da is not None:
            sub_cw = cwsi_da[fi, in_cyc]
            if np.any(np.isfinite(sub_cw)):
                cwsi_m = float(np.nanmean(sub_cw))

        records.append(
            RawCycleRecord(
                field_id=fid,
                cycle_id=int(row["cycle_id"]),
                stratum=str(row.get("stratum_full", "all")),
                start_day=s_day,
                end_day=e_day,
                start_harvest=s_harv,
                duration_days=int(row.get("length_days", e_day - s_day)),
                obs_times=t_cyc,
                obs_days=t_days[in_cyc],
                dsh=dsh,
                values=vals,
                weather_days=t_days,
                temp_c=temp_all.astype(np.float64),
                mean_cwsi=cwsi_m,
            )
        )
    return records, bands


def _recompute_derived_indices(vals: np.ndarray, bands: list[str]) -> np.ndarray:
    """Keep NDVI / NDWI / NDMI consistent with perturbed SR bands."""
    out = vals.copy()
    bmap = {b: i for i, b in enumerate(bands)}
    eps = 1e-6
    if "SR_B4" in bmap and "SR_B5" in bmap and "NDVI" in bmap:
        r = out[:, bmap["SR_B4"]]
        n = out[:, bmap["SR_B5"]]
        out[:, bmap["NDVI"]] = (n - r) / np.where(np.abs(n + r) > eps, n + r, np.nan)
    if "SR_B3" in bmap and "SR_B5" in bmap and "NDWI" in bmap:
        g = out[:, bmap["SR_B3"]]
        n = out[:, bmap["SR_B5"]]
        out[:, bmap["NDWI"]] = (g - n) / np.where(np.abs(g + n) > eps, g + n, np.nan)
    if "SR_B5" in bmap and "SR_B6" in bmap and "NDMI" in bmap:
        n = out[:, bmap["SR_B5"]]
        sw1 = out[:, bmap["SR_B6"]]
        out[:, bmap["NDMI"]] = (n - sw1) / np.where(np.abs(n + sw1) > eps, n + sw1, np.nan)
    return out


def perturb_raw_cycle(
    rec: RawCycleRecord,
    bands: list[str],
    kind: str,
    rng: np.random.Generator,
) -> RawCycleRecord:
    """Inject synthetic agronomic anomaly at the raw observation level before binning."""
    vals = rec.values.copy()
    tau = progress_axis(rec.obs_days, rec.start_day, rec.end_day)
    bmap = {b: i for i, b in enumerate(bands)}
    r_idx = bmap["SR_B4"]
    n_idx = bmap["SR_B5"]
    lst_idx = bmap["ST_B10"]

    if kind == "ndvi_drop":
        t0 = float(rng.uniform(0.25, 0.65))
        sel = (tau >= t0) & (tau <= t0 + 0.18)
        if not np.any(sel):
            sel[len(tau) // 2] = True
        vals[sel, n_idx] *= 0.68
        vals[sel, r_idx] *= 1.18
        vals = _recompute_derived_indices(vals, bands)
    elif kind == "lst_spike":
        t0 = float(rng.uniform(0.25, 0.70))
        sel = (tau >= t0) & (tau <= t0 + 0.15)
        if not np.any(sel):
            sel[len(tau) // 2] = True
        vals[sel, lst_idx] += 5.0
    elif kind == "phase_shift":
        shift_steps = max(2, int(round(len(rec.obs_days) * (45.0 / max(180.0, rec.duration_days)))))
        vals = np.roll(vals, shift=shift_steps, axis=0)
    elif kind == "early_senescence":
        sel = tau >= 0.65
        if np.any(sel):
            ramp = (tau[sel] - 0.65) / 0.35
            vals[sel, n_idx] *= 1.0 - 0.42 * ramp
            vals = _recompute_derived_indices(vals, bands)
    else:
        raise ValueError(f"Unknown perturbation {kind!r}")

    return RawCycleRecord(
        field_id=rec.field_id,
        cycle_id=rec.cycle_id,
        stratum=rec.stratum,
        start_day=rec.start_day,
        end_day=rec.end_day,
        start_harvest=rec.start_harvest,
        duration_days=rec.duration_days,
        obs_times=rec.obs_times,
        obs_days=rec.obs_days,
        dsh=rec.dsh,
        values=vals,
        weather_days=rec.weather_days,
        temp_c=rec.temp_c,
        mean_cwsi=rec.mean_cwsi,
    )


def project_records_to_bins(
    records: list[RawCycleRecord],
    bands: list[str],
    axis_mode: str,
    K: int = 36,
) -> np.ndarray:
    """Project raw cycle records onto ``(N, K, B)`` for B0, B1, B2-GDD, or B2-Landmark."""
    bmap = {b: i for i, b in enumerate(bands)}
    rows: list[np.ndarray] = []
    for rec in records:
        if axis_mode == "b0_doy":
            binned, _ = bin_by_calendar_doy(rec.obs_times, rec.values, K=K)
        elif axis_mode == "b1_dsh":
            vdict = {b: rec.values[:, bmap[b]] for b in bands}
            pb = phase_bin(vdict, rec.dsh, bin_days=15, max_cycle_days=15 * K)
            binned = np.stack([pb[b] for b in bands], axis=-1)
        elif axis_mode == "b1_linear_tau":
            tau = progress_axis(rec.obs_days, rec.start_day, rec.end_day)
            binned, _ = bin_by_progress(tau, rec.values, K=K)
        elif axis_mode == "b2_gdd":
            binned, _ = bin_by_gdd(
                rec.obs_days,
                rec.values,
                rec.start_day,
                rec.end_day,
                rec.weather_days,
                rec.temp_c,
                K=K,
                t_base_c=12.0,
            )
        elif axis_mode == "b2_landmark":
            ndvi = rec.values[:, bmap["NDVI"]]
            binned, _ = bin_by_landmarks(
                rec.obs_days, rec.values, ndvi, rec.start_day, rec.end_day, K=K
            )
        else:
            raise ValueError(f"Unknown axis_mode={axis_mode!r}")
        rows.append(binned)
    return np.stack(rows, axis=0)


def _fit_zscore_baseline(
    X_bin: np.ndarray,
    field_ids: np.ndarray,
    axis_mode: str,
    min_n: int = 4,
):
    X_dict = {"all": X_bin}
    X_by_f_list: dict[int, list[np.ndarray]] = {}
    for row, fid in zip(X_bin, field_ids):
        X_by_f_list.setdefault(int(fid), []).append(row)
    X_by_f = {fid: np.stack(v, axis=0) for fid, v in X_by_f_list.items()}

    active_dict = trimmed_normal_cycles(
        X_dict,
        strata_per_cycle={"all": np.ones(len(X_bin), dtype=bool)},
        X_by_field=X_by_f,
        min_n=min_n,
        q=0.15,
        iters=3,
        threshold=3.5,
    )
    normal_mask = active_dict["all"]
    if axis_mode == "b0_doy":
        bl = fit_b0_calendar_baseline(X_bin, field_ids, min_n=min_n, normal_mask=normal_mask)
    else:
        bl = fit_baseline({"all": X_bin[normal_mask]}, X_by_f, min_n=min_n)
    bl.band_names = [f"b{i}" for i in range(X_bin.shape[-1])]
    return bl, normal_mask


def _score_zscore_continuous(bl, X_bin: np.ndarray, field_ids: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(rms_cycle_score, burden)`` arrays for ``(N, K, B)`` cycles."""
    scores = np.zeros(len(X_bin), dtype=np.float64)
    burdens = np.zeros(len(X_bin), dtype=np.float64)
    for i, (xc, fid) in enumerate(zip(X_bin, field_ids)):
        z = score_cycle(xc, bl, stratum="all", field_id=int(fid))
        s = aggregate_band_scores(z)
        # Top-3 bin RMS mean captures transient 2-4 bin stress more stably than single-bin max
        fin_s = np.sort(s[np.isfinite(s)])
        if fin_s.size > 0:
            top_k = fin_s[-min(3, fin_s.size) :]
            scores[i] = float(np.mean(top_k))
        else:
            scores[i] = cycle_max_score(s)
        burdens[i] = cycle_anomaly_burden(z, threshold=3.5)
    return scores, burdens


def evaluate_all_baselines(
    records: list[RawCycleRecord],
    bands: list[str],
    *,
    K: int = 36,
    seeds: tuple[int, ...] = (42, 43, 44, 45, 46),
) -> dict:
    field_ids = np.array([r.field_id for r in records], dtype=np.int64)
    durations = np.array([r.duration_days for r in records], dtype=np.float64)
    cwsi = np.array([r.mean_cwsi for r in records], dtype=np.float64)

    X_b0 = project_records_to_bins(records, bands, "b0_doy", K=K)
    X_b1 = project_records_to_bins(records, bands, "b1_dsh", K=K)
    X_b2_gdd = project_records_to_bins(records, bands, "b2_gdd", K=K)
    X_b2_lm = project_records_to_bins(records, bands, "b2_landmark", K=K)

    bl_b0, _ = _fit_zscore_baseline(X_b0, field_ids, "b0_doy")
    bl_b1, norm_b1 = _fit_zscore_baseline(X_b1, field_ids, "b1_dsh")
    bl_gdd, _ = _fit_zscore_baseline(X_b2_gdd, field_ids, "b2_gdd")
    bl_lm, _ = _fit_zscore_baseline(X_b2_lm, field_ids, "b2_landmark")

    bmap = {b: i for i, b in enumerate(bands)}
    r_idx = bmap["SR_B4"]
    n_idx = bmap["SR_B5"]
    F_clean = extract_cycle_features(X_b1, durations=durations, red_idx=r_idx, nir_idx=n_idx)
    det_ecod = ECODDetector().fit(F_clean[norm_b1])

    methods_real_scores: dict[str, tuple[np.ndarray, float]] = {}
    for name, bl, Xm in [
        ("B0_calendar_doy", bl_b0, X_b0),
        ("B1_dsh_baseline", bl_b1, X_b1),
        ("B2_gdd_axis", bl_gdd, X_b2_gdd),
        ("B2_landmark_axis", bl_lm, X_b2_lm),
    ]:
        sc, burd = _score_zscore_continuous(bl, Xm, field_ids)
        methods_real_scores[name] = (sc, float(np.mean(burd)))

    if_scores_seeds = [
        IsolationForestDetector(n_estimators=200, seed=s).fit(F_clean[norm_b1]).score_samples(F_clean)
        for s in seeds
    ]
    methods_real_scores["B3_isolation_forest"] = (np.mean(if_scores_seeds, axis=0), np.nan)
    methods_real_scores["B3_ecod"] = (det_ecod.score_samples(F_clean), np.nan)

    normal_indices = np.where(norm_b1)[0]
    normal_recs = [records[i] for i in normal_indices]
    normal_fids = field_ids[normal_indices]
    normal_durs = durations[normal_indices]

    synth_metrics: dict[str, dict[str, list[float]]] = {
        m: {k: [] for k in (*PERTURB_TYPES, "mean_auc_pr", "mean_auc_roc")}
        for m in methods_real_scores
    }

    for seed in seeds:
        rng = np.random.default_rng(seed)
        det_if = IsolationForestDetector(n_estimators=200, seed=seed).fit(F_clean[norm_b1])

        per_kind_pr: dict[str, list[float]] = {m: [] for m in methods_real_scores}
        per_kind_roc: dict[str, list[float]] = {m: [] for m in methods_real_scores}

        for kind in PERTURB_TYPES:
            pert_recs = [perturb_raw_cycle(rec, bands, kind, rng) for rec in normal_recs]
            all_recs = normal_recs + pert_recs
            all_fids = np.concatenate([normal_fids, normal_fids])
            all_durs = np.concatenate([normal_durs, normal_durs])
            y_true = np.array([0] * len(normal_recs) + [1] * len(pert_recs), dtype=np.int32)

            for m_name, mode, bl in [
                ("B0_calendar_doy", "b0_doy", bl_b0),
                ("B1_dsh_baseline", "b1_dsh", bl_b1),
                ("B2_gdd_axis", "b2_gdd", bl_gdd),
                ("B2_landmark_axis", "b2_landmark", bl_lm),
            ]:
                Xp = project_records_to_bins(all_recs, bands, mode, K=K)
                y_score, _ = _score_zscore_continuous(bl, Xp, all_fids)
                ap = float(average_precision_score(y_true, y_score))
                roc = float(roc_auc_score(y_true, y_score))
                synth_metrics[m_name][kind].append(ap)
                per_kind_pr[m_name].append(ap)
                per_kind_roc[m_name].append(roc)

            X_b1_all = project_records_to_bins(all_recs, bands, "b1_dsh", K=K)
            F_all = extract_cycle_features(
                X_b1_all, durations=all_durs, red_idx=r_idx, nir_idx=n_idx
            )
            for m_name, det in [("B3_isolation_forest", det_if), ("B3_ecod", det_ecod)]:
                y_score = det.score_samples(F_all)
                ap = float(average_precision_score(y_true, y_score))
                roc = float(roc_auc_score(y_true, y_score))
                synth_metrics[m_name][kind].append(ap)
                per_kind_pr[m_name].append(ap)
                per_kind_roc[m_name].append(roc)

        for m_name in methods_real_scores:
            synth_metrics[m_name]["mean_auc_pr"].append(float(np.mean(per_kind_pr[m_name])))
            synth_metrics[m_name]["mean_auc_roc"].append(float(np.mean(per_kind_roc[m_name])))

    fin_cw = np.isfinite(cwsi)
    summary: dict[str, dict] = {}
    for m_name, (real_sc, mean_burd) in methods_real_scores.items():
        ok = fin_cw & np.isfinite(real_sc)
        rho, pval = spearmanr(real_sc[ok], cwsi[ok])

        rng_b = np.random.default_rng(42)
        n_ok = int(ok.sum())
        sc_ok = real_sc[ok]
        cw_ok = cwsi[ok]
        boot_rhos = []
        for _ in range(1000):
            idx_b = rng_b.integers(0, n_ok, size=n_ok)
            r_b, _ = spearmanr(sc_ok[idx_b], cw_ok[idx_b])
            if np.isfinite(r_b):
                boot_rhos.append(float(r_b))
        rho_ci = (
            [float(np.percentile(boot_rhos, 2.5)), float(np.percentile(boot_rhos, 97.5))]
            if boot_rhos
            else [float(rho), float(rho)]
        )

        pr_arr = np.array(synth_metrics[m_name]["mean_auc_pr"], dtype=np.float64)
        roc_arr = np.array(synth_metrics[m_name]["mean_auc_roc"], dtype=np.float64)
        pr_m, pr_lo, pr_hi = bootstrap_ci(np.mean, pr_arr, n_boot=1000, seed=42)
        roc_m, roc_lo, roc_hi = bootstrap_ci(np.mean, roc_arr, n_boot=1000, seed=42)

        summary[m_name] = {
            "mean_auc_pr": pr_m,
            "mean_auc_pr_ci_95": [pr_lo, pr_hi],
            "mean_auc_roc": roc_m,
            "mean_auc_roc_ci_95": [roc_lo, roc_hi],
            "per_perturbation_auc_pr": {
                k: float(np.mean(synth_metrics[m_name][k])) for k in PERTURB_TYPES
            },
            "cwsi_spearman_rho": float(rho),
            "cwsi_spearman_pval": float(pval),
            "cwsi_spearman_ci_95": rho_ci,
            "mean_cycle_burden": mean_burd,
        }

    return {
        "n_cycles": len(records),
        "n_normal_reference_cycles": int(norm_b1.sum()),
        "K": K,
        "seeds": list(seeds),
        "baselines": summary,
    }


def main() -> int:
    limit_threads(2)
    ap = argparse.ArgumentParser(description="Compare B0, B1, B2 (GDD/Landmark), and B3 (IF/ECOD).")
    ap.add_argument("--zarr", default="data/processed/fields.zarr", type=Path)
    ap.add_argument("--cycles", default="data/processed/cycles.parquet", type=Path)
    ap.add_argument("--K", default=36, type=int)
    ap.add_argument("--seeds", default="42,43,44,45,46", type=str)
    ap.add_argument("--out", default="reports/baseline_comparison.json", type=Path)
    args = ap.parse_args()

    seeds = tuple(int(s.strip()) for s in args.seeds.split(",") if s.strip())
    records, bands = load_raw_cycles(args.zarr, args.cycles)
    report = evaluate_all_baselines(records, bands, K=args.K, seeds=seeds)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))

    rows = []
    for name, m in report["baselines"].items():
        rows.append(
            {
                "baseline": name,
                "mean_auc_pr": m["mean_auc_pr"],
                "auc_pr_ci_lo": m["mean_auc_pr_ci_95"][0],
                "auc_pr_ci_hi": m["mean_auc_pr_ci_95"][1],
                "mean_auc_roc": m["mean_auc_roc"],
                "ndvi_drop_pr": m["per_perturbation_auc_pr"]["ndvi_drop"],
                "lst_spike_pr": m["per_perturbation_auc_pr"]["lst_spike"],
                "phase_shift_pr": m["per_perturbation_auc_pr"]["phase_shift"],
                "early_senescence_pr": m["per_perturbation_auc_pr"]["early_senescence"],
                "cwsi_spearman_rho": m["cwsi_spearman_rho"],
                "cwsi_pval": m["cwsi_spearman_pval"],
                "mean_cycle_burden": m["mean_cycle_burden"],
            }
        )
    csv_path = args.out.with_suffix(".csv")
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)

    log.info("Wrote baseline comparison to %s and %s", args.out, csv_path)
    print("\n=== Baseline Comparison Summary (non-censored real cycles, 5 seeds) ===")
    print(df.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
