# ruff: noqa: E402
#!/usr/bin/env python3
"""RQ1 (Core, Gaps G2 & G7): Full-archive SSL vs. operational baselines under LOYO CV.

Builds standalone ``data/processed/era5.zarr`` and leak-free ``data/processed/splits.json``,
then evaluates Reconstruction SSL (MaskedTransformer) against:
  - Cheap operational threshold alarms: ``NDVI_Threshold_Alarm``, ``CWSI_Threshold_Alarm``
  - Operational tree baselines: ``RF_Baseline``, ``GBT_Baseline`` (XGBoost-class HistGBDT)
  - Phenology-aware statistical baselines: ``B1_PhaseZScore``, ``B1_CUSUM_SlowDrift``, ``B3_ECOD``
at equal alert budgets (``Recall@5%``, ``Recall@10%``) and ``AUC-PR`` under
Leave-One-Year-Out (LOYO) validation, reporting field-cluster 95% bootstrap CIs and
Holm-corrected paired per-field Wilcoxon signed-rank tests.

Runs on BOTH:
  1. Real workspace archive (``data/processed/fields.zarr``, 32 subset farms)
  2. Full 490-field x 13.5-year archive (``--full-zarr`` if mounted, else empirically
     calibrated 490-field x 13.5-year Khuzestan sugarcane simulator, transparently labeled).
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

from ssl_anomaly.utils.throttle import limit_threads

limit_threads(2)

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
import xarray as xr
from sklearn.metrics import average_precision_score
from torch.utils.data import DataLoader, TensorDataset

torch.set_num_threads(2)

from ssl_anomaly.baseline import (
    CWSIThresholdAlarm,
    ECODDetector,
    GBTBaseline,
    NDVIThresholdAlarm,
    RFBaseline,
    aggregate_band_scores,
    build_stratum_table,
    cusum_detector,
    extract_cycle_features,
    fit_baseline,
    recall_at_alert_budget,
    score_cycle,
    trimmed_normal_cycles,
)
from ssl_anomaly.eval import (
    add_source_argument,
    build_provenance,
    cluster_field_ci,
    compare_detectors_wilcoxon_holm,
    generate_splits_dict,
    load_real490_archive,
    save_splits_json,
    simulate_490_field_archive,
    simulated_output_path,
    spearman_correlation,
)
from ssl_anomaly.io import extract_era5_from_fields_zarr
from ssl_anomaly.models.masked_tf import MaskedTransformer
from ssl_anomaly.phenology import add_spectral_indices, phase_bin
from ssl_anomaly.utils.logging import get_logger
from ssl_anomaly.utils.seeds import seed_everything

log = get_logger("ssl_anomaly.scripts.rq1")


def _fit_and_score_ssl_fold(
    X_train_norm: np.ndarray,
    X_eval: np.ndarray,
    *,
    epochs: int = 16,
    batch_size: int = 256,
    lr: float = 2e-3,
    seed: int = 42,
) -> np.ndarray:
    """Train MaskedTransformer on standardized ``(N_tr, K, B)`` normal cycles and score ``X_eval``."""
    seed_everything(seed)
    N_tr, K, B = X_train_norm.shape

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        med = np.nanmedian(X_train_norm, axis=(0, 1))
        mad = np.nanmedian(np.abs(X_train_norm - med[None, None, :]), axis=(0, 1)) * 1.4826
    med = np.where(np.isfinite(med), med, 0.0)
    scale = np.where(np.isfinite(mad) & (mad > 1e-4), mad, 1.0)

    def _to_tokens(X_arr: np.ndarray) -> tuple[torch.Tensor, torch.Tensor]:
        obs = np.any(np.isfinite(X_arr), axis=-1)  # (N, K)
        Z = (X_arr - med[None, None, :]) / scale[None, None, :]
        Z = np.nan_to_num(Z, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
        # Append normalized phase coordinate tau in [0, 1] as conditioning token feature
        tau_feat = np.broadcast_to(
            np.linspace(0.0, 1.0, K, dtype=np.float32)[None, :, None], (len(X_arr), K, 1)
        )
        tok = np.concatenate([Z, tau_feat], axis=-1)
        pamask = ~obs
        return torch.from_numpy(tok), torch.from_numpy(pamask)

    tr_tok, tr_pad = _to_tokens(X_train_norm)
    ev_tok, ev_pad = _to_tokens(X_eval)
    d_in = tr_tok.shape[-1]

    model = MaskedTransformer(
        d_in=d_in, d_model=64, n_heads=4, n_layers=3, d_ff=128, dropout=0.1, max_len=max(64, K + 4)
    )
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    dl = DataLoader(TensorDataset(tr_tok, tr_pad), batch_size=batch_size, shuffle=True)
    rng = np.random.default_rng(seed)

    model.train()
    for _ in range(epochs):
        for b_tok, b_pad in dl:
            bsz = b_tok.shape[0]
            # Random + contiguous block mask over valid observed positions
            m_np = (rng.random((bsz, K)) < 0.28) & (~b_pad.numpy())
            for bi in range(bsz):
                s = int(rng.integers(0, max(1, K - 4)))
                m_np[bi, s : s + 3] = ~b_pad[bi, s : s + 3].numpy()
                if not m_np[bi].any():
                    valid_pos = np.where(~b_pad[bi].numpy())[0]
                    if valid_pos.size:
                        m_np[bi, valid_pos[0]] = True
            m_t = torch.from_numpy(m_np)
            x_in = b_tok.clone()
            x_in[:, :, :B][m_t] = 0.0
            # Never pass all-True key_padding_mask row
            safe_pad = b_pad.clone()
            all_pad = safe_pad.all(dim=1)
            if all_pad.any():
                safe_pad[all_pad, 0] = False

            recon, _ = model(x_in, mask=m_t, key_padding_mask=safe_pad)
            err = F.smooth_l1_loss(recon[:, :, :B], b_tok[:, :, :B], reduction="none", beta=1.0).mean(dim=-1)
            tok_loss = err * m_t.float()
            per_sample = tok_loss.sum(dim=1) / m_t.float().sum(dim=1).clamp(min=1.0)
            # Trimmed loss (drop top 10% contaminated training samples)
            if per_sample.numel() >= 10:
                keep_k = max(1, int(0.9 * per_sample.numel()))
                thr = torch.kthvalue(per_sample, keep_k).values
                loss = per_sample[per_sample <= thr].mean()
            else:
                loss = per_sample.mean()
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()

    model.eval()
    scores = np.zeros(len(X_eval), dtype=np.float64)
    block = 4
    with torch.no_grad():
        safe_ev_pad = ev_pad.clone()
        all_p = safe_ev_pad.all(dim=1)
        if all_p.any():
            safe_ev_pad[all_p, 0] = False

        tok_err_all = np.full((len(X_eval), K), np.nan, dtype=np.float64)
        for s in range(0, K, block):
            e = min(K, s + block)
            m_t = torch.zeros((len(X_eval), K), dtype=torch.bool)
            m_t[:, s:e] = ~ev_pad[:, s:e]
            x_in = ev_tok.clone()
            x_in[:, s:e, :B] = 0.0
            recon, _ = model(x_in, mask=m_t, key_padding_mask=safe_ev_pad)
            diff = (recon[:, s:e, :B] - ev_tok[:, s:e, :B]).numpy()
            rms = np.sqrt(np.mean(diff**2, axis=-1))
            obs_blk = (~ev_pad[:, s:e]).numpy()
            rms[~obs_blk] = np.nan
            tok_err_all[:, s:e] = rms

        for i in range(len(X_eval)):
            fin = np.sort(tok_err_all[i][np.isfinite(tok_err_all[i])])
            scores[i] = float(np.mean(fin[-min(4, fin.size) :])) if fin.size else 0.0
    return scores


def run_loyo_archive_benchmark(
    archive: dict,
    *,
    ssl_epochs: int = 16,
    max_loyo_years: int | None = None,
    seed: int = 42,
) -> dict:
    """Run Leave-One-Year-Out evaluation across all operational & SSL detectors on ``archive``."""
    X = archive["X"]
    bands = archive["bands"]
    fids = archive["field_ids"]
    years = archive["start_years"]
    y_true = archive["y_stress"]
    eta_def = archive["eta_deficit"]

    bmap = {b: i for i, b in enumerate(bands)}
    aliases = archive.get("band_aliases", {})
    r_i = aliases.get("SR_B4", bmap.get("SR_B4"))
    n_i = aliases.get("SR_B5", bmap.get("SR_B5"))
    lst_i = aliases.get("ST_B10", bmap.get("ST_B10"))
    nd_i = aliases.get("NDVI", bmap.get("NDVI"))

    uniq_years = sorted(int(y) for y in np.unique(years))
    valid_years = [
        y for y in uniq_years
        if int((years == y).sum()) >= 5 and int(y_true[years == y].sum()) >= 1 and int((years != y).sum()) >= 15
    ]
    if max_loyo_years is not None and len(valid_years) > max_loyo_years:
        # Uniformly sample across archive span (early L8, mid L8, late L8+L9)
        idx_y = np.linspace(0, len(valid_years) - 1, max_loyo_years).round().astype(int)
        valid_years = [valid_years[i] for i in idx_y]

    # A single-class label vector makes AUC-PR undefined (sklearn returns an
    # IndexError from an empty confusion matrix). On the real 490-field archive
    # y_stress is a placeholder of zeros until the CWSI/ETa zonal extraction
    # lands, so report the detector suite as not-run rather than crashing.
    n_pos = int(np.sum(y_true == 1))
    n_neg = int(np.sum(y_true == 0))
    if n_pos == 0 or n_neg == 0:
        return {
            "status": "not_run",
            "note": (
                "AUC-PR/recall are undefined: y_stress has a single class "
                f"(n_pos={n_pos}, n_neg={n_neg}). On the real 490-field archive "
                "stress labels are pending CWSI/ETa zonal extraction, so the "
                "detector comparison is reported as not-run instead of being "
                "computed on a degenerate label vector."
            ),
            "n_fields": int(len(np.unique(fids))),
            "n_cycles_evaluated": 0,
            "n_loyo_folds": 0,
            "held_out_years": [],
            "detectors": {},
            "paired_wilcoxon_vs_ssl": {},
        }

    detector_names = [
        "SSL_MaskedTransformer",
        "B1_PhaseZScore",
        "B1_CUSUM_SlowDrift",
        "B3_ECOD",
        "NDVI_Threshold_Alarm",
        "CWSI_Threshold_Alarm",
        "RF_Baseline",
        "GBT_Baseline",
    ]
    oof_scores: dict[str, np.ndarray] = {m: np.full(len(X), np.nan, dtype=np.float64) for m in detector_names}
    evaluated_mask = np.zeros(len(X), dtype=bool)

    print(
        f"[RQ1] LOYO setup: {len(valid_years)} folds, years={valid_years}, "
        f"n_cycles={len(X)}, n_fields={len(np.unique(fids))}, "
        f"ssl_epochs={ssl_epochs}",
        flush=True,
    )

    for yi, yr in enumerate(valid_years):
        tr_idx = np.where(years != yr)[0]
        va_idx = np.where(years == yr)[0]
        evaluated_mask[va_idx] = True

        print(
            f"[RQ1] Fold {yi + 1}/{len(valid_years)}: held-out year={yr} "
            f"(train={len(tr_idx)}, eval={len(va_idx)})",
            flush=True,
        )

        X_tr = X[tr_idx]
        f_tr = fids[tr_idx]
        X_va = X[va_idx]
        f_va = fids[va_idx]

        # Trimmed normal subset inside training fold (strictly zero test leakage)
        X_by_f_tr: dict[int, list[np.ndarray]] = {}
        for row, f in zip(X_tr, f_tr):
            X_by_f_tr.setdefault(int(f), []).append(row)
        X_by_f_arr = {f: np.stack(v, axis=0) for f, v in X_by_f_tr.items()}
        act_dict = trimmed_normal_cycles(
            {"all": X_tr},
            strata_per_cycle={"all": np.ones(len(X_tr), dtype=bool)},
            X_by_field=X_by_f_arr,
            min_n=5,
            q=0.15,
            iters=2,
            threshold=3.5,
        )
        norm_tr = act_dict["all"]
        X_tr_norm = X_tr[norm_tr]
        print(f"[RQ1]   trimmed normal train: {len(X_tr_norm)} cycles", flush=True)

        # 1. B1 Phase Z-score + B1 CUSUM slow-drift
        bl = fit_baseline({"all": X_tr_norm}, X_by_f_arr, min_n=5)
        b1_s = np.zeros(len(X_va), dtype=np.float64)
        cus_s = np.zeros(len(X_va), dtype=np.float64)
        for i, (xc, fv) in enumerate(zip(X_va, f_va)):
            z = score_cycle(xc, bl, stratum="all", field_id=int(fv))
            s_bin = aggregate_band_scores(z)
            fin_b = np.sort(s_bin[np.isfinite(s_bin)])
            b1_s[i] = float(np.mean(fin_b[-min(3, fin_b.size) :])) if fin_b.size else 0.0
            _, c_stat = cusum_detector(s_bin, drift_k=1.1, decision_h=4.5)
            cus_s[i] = float(np.nanmax(c_stat)) if np.isfinite(c_stat).any() else 0.0
        oof_scores["B1_PhaseZScore"][va_idx] = b1_s
        oof_scores["B1_CUSUM_SlowDrift"][va_idx] = cus_s

        # 2. B3 ECOD
        F_tr_norm = extract_cycle_features(X_tr_norm, red_idx=r_i, nir_idx=n_i)
        F_va = extract_cycle_features(X_va, red_idx=r_i, nir_idx=n_i)
        oof_scores["B3_ECOD"][va_idx] = ECODDetector().fit(F_tr_norm).score_samples(F_va)

        # 3. Operational threshold alarms (NDVI & CWSI)
        oof_scores["NDVI_Threshold_Alarm"][va_idx] = (
            NDVIThresholdAlarm(ndvi_band_idx=nd_i).fit(X_tr_norm).score_cycles(X_va)
        )
        oof_scores["CWSI_Threshold_Alarm"][va_idx] = (
            CWSIThresholdAlarm(lst_band_idx=lst_i).fit(X_tr_norm).score_cycles(X_va)
        )

        # 4. Operational RF & GBT (XGBoost-class) baselines (self-labeled on X_tr_norm)
        oof_scores["RF_Baseline"][va_idx] = (
            RFBaseline(red_idx=r_i, nir_idx=n_i, lst_idx=lst_i, seed=seed + yi)
            .fit(X_tr_norm)
            .score_cycles(X_va)
        )
        oof_scores["GBT_Baseline"][va_idx] = (
            GBTBaseline(red_idx=r_i, nir_idx=n_i, lst_idx=lst_i, seed=seed + yi)
            .fit(X_tr_norm)
            .score_cycles(X_va)
        )

        # 5. Reconstruction SSL (MaskedTransformer)
        print(f"[RQ1]   training SSL MaskedTransformer ({ssl_epochs} epochs)...", flush=True)
        oof_scores["SSL_MaskedTransformer"][va_idx] = _fit_and_score_ssl_fold(
            X_tr_norm, X_va, epochs=ssl_epochs, seed=seed + yi
        )
        print(f"[RQ1]   fold {yi + 1}/{len(valid_years)} done.", flush=True)

    ev = evaluated_mask
    yt = y_true[ev]
    fev = fids[ev]
    eta_ev = eta_def[ev]

    summary: dict[str, dict] = {}
    per_cycle_concordance: dict[str, np.ndarray] = {}

    # Compute per-field AUC-PR for field-cluster bootstrap & paired Wilcoxon
    uniq_fields = np.unique(fev)
    for m_name in detector_names:
        sc = oof_scores[m_name][ev]
        # Standardize scores across LOYO folds via rank percentile for global pooled budget
        ap_global = float(average_precision_score(yt, sc))
        rec_5 = recall_at_alert_budget(yt, sc, alert_rate=0.05)
        rec_10 = recall_at_alert_budget(yt, sc, alert_rate=0.10)
        rho_eta, p_eta = spearman_correlation(sc, eta_ev)

        # Per-cycle non-parametric loss alignment for paired Wilcoxon across all 490 fields
        ranks = pd.Series(sc).rank(pct=True).to_numpy()
        cycle_align = np.where(yt == 1, ranks, 1.0 - ranks)
        per_cycle_concordance[m_name] = cycle_align
        align_m, align_lo, align_hi = cluster_field_ci(cycle_align, fev, n_boot=500, seed=seed)

        summary[m_name] = {
            "auc_pr": ap_global,
            "recall_at_5pct_alert_budget": rec_5,
            "recall_at_10pct_alert_budget": rec_10,
            "eta_deficit_spearman_rho": rho_eta,
            "eta_deficit_pval": p_eta,
            "field_cluster_concordance_mean": align_m,
            "field_cluster_concordance_ci_95": [align_lo, align_hi],
        }

    wilcoxon_table = compare_detectors_wilcoxon_holm(
        per_cycle_concordance, fev, reference_model="SSL_MaskedTransformer", seed=seed
    )
    return {
        "n_fields": int(len(uniq_fields)),
        "n_cycles_evaluated": int(ev.sum()),
        "n_loyo_folds": len(valid_years),
        "held_out_years": valid_years,
        "detectors": summary,
        "paired_wilcoxon_vs_ssl": wilcoxon_table,
    }


def _load_real_32_archive(zarr_path: Path, cycles_path: Path) -> tuple[dict, dict]:
    """Load real 32-farm subset into archive dict and generate splits.json."""
    ds = xr.open_zarr(zarr_path)
    ds = add_spectral_indices(ds)
    cycles_df = build_stratum_table(pd.read_parquet(cycles_path))
    times = ds.coords["time"].values
    epoch = times[0]
    splits = generate_splits_dict(cycles_df, epoch, n_spatial_folds=5)

    bands = [str(b) for b in ds.coords["band"].values]
    bmap = {b: i for i, b in enumerate(bands)}
    fields = ds.coords["field"].values
    med = ds["median"].values
    cwsi_da = ds["cwsi_et"].values

    X_list, fids, years, cwsi_list = [], [], [], []
    for _, row in cycles_df.iterrows():
        if row["censored"]:
            continue
        fid = int(row["field"])
        fi = int(np.where(fields == fid)[0][0])
        t0 = epoch + np.timedelta64(int(row["t_start"]), "D")
        t1 = epoch + np.timedelta64(int(row["t_end"]), "D")
        sh = epoch + np.timedelta64(int(row.get("start_harvest", row["t_start"])), "D")
        m = (times >= t0) & (times < t1)
        if int(m.sum()) < 4:
            continue
        dsh = (times[m] - sh).astype("timedelta64[D]").astype(int)
        pb = phase_bin({b: med[fi, m, bmap[b]] for b in bands}, dsh, bin_days=15, max_cycle_days=540)
        X_list.append(np.stack([pb[b] for b in bands], axis=-1))
        fids.append(fid)
        years.append(int(t0.astype("datetime64[Y]").astype(int) + 1970))
        cw = cwsi_da[fi, m]
        cwsi_list.append(float(np.nanmean(cw)) if np.any(np.isfinite(cw)) else 0.0)

    cwsi_arr = np.array(cwsi_list, dtype=np.float64)
    # Top 20% evaporative deficit cycles as natural weak-proxy positives on the 32-farm subset
    y_weak = (cwsi_arr >= np.nanpercentile(cwsi_arr, 80)).astype(np.int32)
    real_arch = {
        "X": np.stack(X_list, axis=0),
        "bands": bands,
        "field_ids": np.array(fids, dtype=np.int64),
        "start_years": np.array(years, dtype=np.int64),
        "y_stress": y_weak,
        "eta_deficit": cwsi_arr,
    }
    return real_arch, splits


def main() -> int:
    limit_threads(2)
    ap = argparse.ArgumentParser(description="Run RQ1 LOYO & operational baseline benchmark.")
    add_source_argument(ap, default="real490")
    ap.add_argument("--zarr", default=None, type=Path)
    ap.add_argument("--cycles", default=None, type=Path)
    ap.add_argument("--era5-out", default=None, type=Path)
    ap.add_argument("--splits-out", default="data/processed/splits.json", type=Path)
    ap.add_argument("--out", default="reports/rq1_benchmark.json", type=Path)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--max-fields", type=int, default=None)
    args = ap.parse_args()

    source = args.source
    seed = args.seed

    if source == "real490":
        print("[RQ1] Loading real490 archive...", flush=True)
        archive = load_real490_archive()  # fail-closed
        prov = build_provenance(archive, seeds=[seed])
        if args.max_fields is not None:
            unique_fields = np.unique(archive["field_ids"])
            selected = unique_fields[:args.max_fields]
            mask = np.isin(archive["field_ids"], selected)
            n_cycles_before = len(archive["field_ids"])
            # Snapshot the keys first: mutating the dict while iterating it lets
            # the per-key length test read an already-shrunk field_ids array.
            for k in list(archive.keys()):
                v = archive[k]
                if isinstance(v, np.ndarray) and len(v) == n_cycles_before:
                    archive[k] = v[mask]
            archive["provenance"] = prov
            archive["provenance"]["n_fields"] = len(selected)
            archive["provenance"]["n_cycles"] = int(mask.sum())
        out_path = args.out
        report_source = "real490"
    elif source == "simulated":
        archive = simulate_490_field_archive(n_fields=490, n_years=13.5, seed=seed)
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
        report_source = "simulated"
    elif source == "real32":
        if args.zarr is None or args.cycles is None:
            log.error("--source real32 requires --zarr and --cycles")
            return 1
        extract_era5_from_fields_zarr(args.zarr, args.era5_out or "data/processed/era5.zarr")
        real_arch, splits = _load_real_32_archive(args.zarr, args.cycles)
        save_splits_json(splits, args.splits_out)
        archive = real_arch
        archive["provenance"] = {
            "data_source": "real32",
            "n_fields": len(set(archive["field_ids"])),
            "n_cycles": archive["X"].shape[0],
            "n_dates": 0,
            "first_acquisition_date": "",
            "last_acquisition_date": "",
            "cycle_file_sha256": "real32_fields_zarr",
            "git_sha": "unknown",
            "splits_sha256": splits.get("splits_sha256", "unknown"),
            "seeds": [seed],
            "y_stress_proxy": "top20pct_cwsi",
            "eta_deficit_source": "fields_zarr_cwsi_et",
            "cwsi_source": "fields_zarr_cwsi_et",
        }
        prov = archive["provenance"]
        out_path = args.out
        report_source = "real32"
    else:
        log.error("Unknown source: %s", source)
        return 1

    epochs = 8 if source == "simulated" else 25
    max_loyo = 4 if source == "simulated" else None
    print(
        f"[RQ1] Starting LOYO benchmark (source={report_source}, epochs={epochs}, "
        f"max_loyo_years={max_loyo})...",
        flush=True,
    )
    results = run_loyo_archive_benchmark(archive, ssl_epochs=epochs, max_loyo_years=max_loyo, seed=seed)

    report = {
        "provenance": prov,
        "data_source": prov["data_source"],
        "source": report_source,
        "n_fields": prov["n_fields"],
        "n_cycles": prov["n_cycles"],
        "rq1_results": results,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))

    if results.get("status") == "not_run":
        print(f"\n=== RQ1 Leave-One-Year-Out Benchmark (source={report_source}) ===")
        print(f"NOT RUN: {results['note']}")
        pd.DataFrame([{"archive": report_source, "status": "not_run", "note": results["note"]}]).to_csv(
            out_path.with_suffix(".csv"), index=False
        )
        return 0

    rows = []
    for det, m in results["detectors"].items():
        rows.append(
            {
                "archive": report_source,
                "detector": det,
                "auc_pr": m["auc_pr"],
                "recall_at_5pct": m["recall_at_5pct_alert_budget"],
                "recall_at_10pct": m["recall_at_10pct_alert_budget"],
                "eta_deficit_rho": m["eta_deficit_spearman_rho"],
                "cluster_concordance": m["field_cluster_concordance_mean"],
            }
        )
    csv_path = out_path.with_suffix(".csv")
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)

    print(f"\n=== RQ1 Leave-One-Year-Out Benchmark (source={report_source}) ===")
    print(df.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
