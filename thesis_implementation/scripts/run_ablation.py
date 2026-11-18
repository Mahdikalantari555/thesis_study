#!/usr/bin/env python3
"""Input channel & conditioning ablation runner (Hydra-style input.drop multirun).

Evaluates weather on/off, LST (ST_B10) on/off, and individual spectral band drops
across multiple seeds (default: 5 seeds), reporting metric changes with 95%
bootstrap confidence intervals for both B1 statistical baseline and SSL.

Usage::

    # Full default multirun (none, lst, weather, lst+weather, SR_B2..SR_B7) x 5 seeds
    python scripts/run_ablation.py

    # Specific Hydra-style multirun override
    python scripts/run_ablation.py -m input.drop=none,lst,weather,lst+weather seeds=5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
import xarray as xr
from sklearn.metrics import average_precision_score

from ssl_anomaly.baseline import (
    aggregate_band_scores,
    build_stratum_table,
    fit_baseline,
    flag_runs,
    score_cycle,
    trimmed_normal_cycles,
)
from ssl_anomaly.config import SSLCfg
from ssl_anomaly.eval.stats import bootstrap_ci, spearman_correlation
from ssl_anomaly.eval.synthetic import InjectionConfig, _phase_start_bin, inject_anomaly
from ssl_anomaly.models.masked_tf import MaskedTransformer
from ssl_anomaly.models.tokenizer import CycleTokenizer, mask_tokens
from ssl_anomaly.phenology.align import phase_bin
from ssl_anomaly.utils.logging import get_logger
from ssl_anomaly.utils.seeds import seed_everything
from ssl_anomaly.utils.throttle import limit_threads

log = get_logger("ssl_anomaly.scripts.ablation")

DEFAULT_DROPS = [
    "none",
    "lst",
    "weather",
    "lst+weather",
    "SR_B2",
    "SR_B3",
    "SR_B4",
    "SR_B5",
    "SR_B6",
    "SR_B7",
]
WEATHER_KEYS = ["tmean", "et0", "rad", "rh", "gdd"]
WEATHER_VAR_MAP = {
    "tmean": "weather_tmean",
    "et0": "weather_et0",
    "rad": "weather_rad",
    "rh": "weather_rh",
    "gdd": "weather_gdd",
}


def parse_drop_spec(spec: str) -> tuple[set[str], bool]:
    """Parse a single drop token (e.g. 'lst+weather', 'SR_B4', 'none') -> (dropped_bands, include_weather)."""
    parts = [p.strip() for p in spec.split("+") if p.strip()]
    dropped_bands: set[str] = set()
    include_weather = True
    for p in parts:
        low = p.lower()
        if low in ("none", "full", "baseline"):
            continue
        if low in ("lst", "st_b10"):
            dropped_bands.add("ST_B10")
        elif low == "weather":
            include_weather = False
        else:
            dropped_bands.add(p)
    return dropped_bands, include_weather


def extract_binned_cycles(
    ds: xr.Dataset,
    cycles_df: pd.DataFrame,
    bands: list[str],
    *,
    bin_days: int = 15,
    max_cycle_days: int = 540,
) -> list[dict]:
    """Extract non-censored binned cycles with band arrays, weather, and CWSI proxy."""
    med = ds["median"].values
    times = ds.coords["time"].values
    ds_bands = list(ds.coords["band"].values)
    fields = ds.coords["field"].values
    band_idx = {b: ds_bands.index(b) for b in bands}
    has_cwsi = "cwsi_et" in ds.data_vars
    cwsi_all = ds["cwsi_et"].values if has_cwsi else None
    has_weather = all(v in ds.data_vars for v in WEATHER_VAR_MAP.values())

    cycles_df = build_stratum_table(cycles_df)
    epoch = times[0]
    out: list[dict] = []

    for fid in fields:
        fi = int(np.where(fields == fid)[0][0])
        fc = cycles_df[cycles_df["field"] == fid].sort_values("cycle_id")
        for _, c in fc.iterrows():
            if c["censored"]:
                continue
            t_start_dt = epoch + np.timedelta64(int(c["t_start"]), "D")
            t_end_dt = epoch + np.timedelta64(int(c["t_end"]), "D")
            start_h = int(c.get("start_harvest", c["t_start"]))
            harvest_dt = epoch + np.timedelta64(start_h, "D")
            tmask = (times >= t_start_dt) & (times < t_end_dt)
            if int(tmask.sum()) < 3:
                continue
            t_c = times[tmask]
            b_c = med[fi][tmask]
            dsh = (t_c - harvest_dt).astype("timedelta64[D]").astype(int)
            binned = phase_bin(
                {b: b_c[:, band_idx[b]] for b in bands},
                dsh,
                bin_days=bin_days,
                max_cycle_days=max_cycle_days,
            )
            arr = np.stack([binned[b] for b in bands], axis=-1)  # (bins, B)
            obs_mask = ~np.isnan(arr[:, 0])
            if int(obs_mask.sum()) < 3:
                continue

            if has_weather:
                w_raw = {wk: ds[WEATHER_VAR_MAP[wk]].values[tmask] for wk in WEATHER_KEYS}
                w_bin = phase_bin(w_raw, dsh, bin_days=bin_days, max_cycle_days=max_cycle_days)
                w_arr = np.stack([w_bin[wk] for wk in WEATHER_KEYS], axis=-1).astype(np.float32)
            else:
                w_arr = np.zeros((arr.shape[0], len(WEATHER_KEYS)), dtype=np.float32)

            cwsi_mean = np.nan
            if cwsi_all is not None:
                cw_vals = cwsi_all[fi][tmask]
                if np.isfinite(cw_vals).any():
                    cwsi_mean = float(np.nanmean(cw_vals))

            sensors = ds.coords["sensor"].values[tmask] if "sensor" in ds.coords else np.array(["L8"])
            out.append(
                {
                    "field": int(fid),
                    "field_idx": fi,
                    "cycle_id": int(c["cycle_id"]),
                    "stratum": str(c.get("stratum_full", "all")),
                    "ratoon_no": int(c.get("ratoon_no", 0)),
                    "harvest_dt": harvest_dt,
                    "sensor": str(sensors[0]) if sensors.size else "L8",
                    "binned_bands": arr.astype(np.float64),
                    "binned_weather": np.nan_to_num(w_arr, nan=0.0),
                    "cwsi_mean": cwsi_mean,
                }
            )
    return out


def _evaluate_synthetic_and_auc(
    X_normal: np.ndarray,
    score_fn,
    bands: list[str],
    seed: int,
    alert_rate: float = 0.05,
) -> dict[str, float]:
    """Evaluate cycle anomaly scorer on seeded synthetic injections (AUC-PR & Recall@5%)."""
    rng = np.random.default_rng(seed)
    n_norm, n_bins, _ = X_normal.shape
    if n_norm == 0:
        return {"auc_pr": 0.0, "recall_at_5pct": 0.0, "non_thermal_auc_pr": 0.0}

    veg_idx = bands.index("SR_B5") if "SR_B5" in bands else 0
    lst_idx = bands.index("ST_B10") if "ST_B10" in bands else -1
    inj_cfg = InjectionConfig(n_per_stratum=min(15, n_norm), alert_rate=alert_rate)

    norm_scores = np.array([float(np.nanmean(score_fn(X_normal[i])[0])) for i in range(n_norm)])
    norm_scores = np.nan_to_num(norm_scores, nan=0.0)

    all_recalls: list[float] = []
    all_ap: list[float] = []
    non_thermal_ap: list[float] = []

    scenarios = []
    for depth in [0.15, 0.30]:
        for dur in [2, 4]:
            for ph in ["early", "mid"]:
                scenarios.append(("ndvi_drop", depth, dur, ph, 0.0, 0))
    for k in [2.0, 4.0]:
        scenarios.append(("lst_increase", 0.0, 3, "mid", k, 0))
    for delay in [30, 45]:
        scenarios.append(("phenology_delay", 0.0, 3, "mid", 0.0, delay))

    for mode, depth, dur, phase, lst_k, delay in scenarios:
        n_inj = min(inj_cfg.n_per_stratum, n_norm)
        idx_sel = rng.choice(n_norm, size=n_inj, replace=False)
        inj_scores = []
        for idx in idx_sel:
            start = _phase_start_bin(phase, n_bins)
            injected, _ = inject_anomaly(
                X_normal[idx],
                mode=mode,
                start_bin=start,
                duration=dur,
                depth=depth,
                lst_k=lst_k,
                shift_days=delay,
                bin_days=15,
                ndvi_idx=veg_idx,
                lst_idx=lst_idx,
                rng=rng,
            )
            s_bins, _ = score_fn(injected)
            inj_scores.append(float(np.nanmean(s_bins)) if np.isfinite(s_bins).any() else 0.0)

        y_true = np.concatenate([np.zeros(n_norm, dtype=int), np.ones(n_inj, dtype=int)])
        y_score = np.concatenate([norm_scores, np.nan_to_num(np.array(inj_scores), nan=0.0)])
        ap = float(average_precision_score(y_true, y_score))
        all_ap.append(ap)
        if mode != "lst_increase":
            non_thermal_ap.append(ap)

        alert_n = max(1, int(np.ceil(alert_rate * len(y_score))))
        top_idx = np.argsort(-y_score)[:alert_n]
        all_recalls.append(float(y_true[top_idx].sum() / max(1, n_inj)))

    return {
        "auc_pr": float(np.mean(all_ap)),
        "non_thermal_auc_pr": float(np.mean(non_thermal_ap)),
        "recall_at_5pct": float(np.mean(all_recalls)),
    }


def _train_and_eval_ssl_single_seed(
    cycle_items: list[dict],
    kept_bands: list[str],
    include_weather: bool,
    seed: int,
    *,
    bin_days: int = 15,
    epochs: int = 15,
) -> dict[str, float]:
    """Train MaskedTransformer for one seed and evaluate val loss, synthetic AUC-PR, and CWSI corr."""
    seed_everything(seed)
    rng = np.random.default_rng(seed)

    all_fields = sorted({c["field"] for c in cycle_items})
    val_fields = set(all_fields[-6:]) if len(all_fields) >= 6 else set()

    tok = CycleTokenizer(
        n_bands=len(kept_bands),
        band_names=kept_bands,
        include_valid_frac=True,
        include_dtime=True,
        include_dsh=True,
        include_doy=True,
        include_sensor=True,
        include_ratoon=True,
        include_weather=include_weather,
        n_weather_vars=len(WEATHER_KEYS) if include_weather else 0,
    )

    raw_tokens: list[np.ndarray] = []
    obs_indices_list: list[np.ndarray] = []
    is_val_list: list[bool] = []
    cwsi_list: list[float] = []

    for item in cycle_items:
        arr = item["binned_bands"]
        obs_idx = np.where(~np.isnan(arr[:, 0]))[0]
        b_obs = arr[obs_idx].astype(np.float32)
        dsh_obs = (obs_idx * bin_days).astype(np.int64)
        times_obs = item["harvest_dt"] + dsh_obs.astype("timedelta64[D]")
        w_obs = item["binned_weather"][obs_idx] if include_weather else None
        sensors = np.array([item["sensor"]] * obs_idx.size, dtype=object)
        t_mat = tok.tokenize(
            bands=b_obs,
            times=times_obs,
            dsh=dsh_obs,
            valid_frac=np.ones(obs_idx.size, dtype=np.float32),
            sensor=sensors,
            ratoon_no=item["ratoon_no"],
            weather=w_obs,
        )
        raw_tokens.append(np.nan_to_num(t_mat, nan=0.0))
        obs_indices_list.append(obs_idx)
        is_val_list.append(item["field"] in val_fields)
        cwsi_list.append(item["cwsi_mean"])

    train_toks = [t for t, is_v in zip(raw_tokens, is_val_list) if not is_v]
    tok.fit(train_toks or raw_tokens)
    std_tokens = [tok.standardize(t).astype(np.float32) for t in raw_tokens]

    ssl_cfg = SSLCfg()
    model = MaskedTransformer(
        d_in=tok.d_feature,
        d_model=ssl_cfg.transformer.d_model,
        n_heads=ssl_cfg.transformer.n_heads,
        n_layers=ssl_cfg.transformer.n_layers,
        d_ff=ssl_cfg.transformer.d_ff,
        dropout=ssl_cfg.transformer.dropout,
        max_len=ssl_cfg.transformer.max_len,
    )
    opt = torch.optim.AdamW(model.parameters(), lr=ssl_cfg.lr, weight_decay=ssl_cfg.weight_decay)

    train_idx = [i for i, v in enumerate(is_val_list) if not v] or list(range(len(std_tokens)))
    val_idx = [i for i, v in enumerate(is_val_list) if v] or train_idx

    def make_batch(indices: list[int], batch_rng: np.random.Generator) -> tuple[torch.Tensor, ...]:
        lengths = [std_tokens[i].shape[0] for i in indices]
        t_max = max(lengths)
        d = tok.d_feature
        b_sz = len(indices)
        x_masked = np.zeros((b_sz, t_max, d), dtype=np.float32)
        x_orig = np.zeros((b_sz, t_max, d), dtype=np.float32)
        m_arr = np.zeros((b_sz, t_max), dtype=bool)
        pad_arr = np.ones((b_sz, t_max), dtype=bool)
        for bi, idx in enumerate(indices):
            t_i = std_tokens[idx]
            L_i = t_i.shape[0]
            x_orig[bi, :L_i] = t_i
            pad_arr[bi, :L_i] = False
            mt, mb = mask_tokens(t_i, mask_ratio=0.25, block_max=3, block_p=0.3, rng=batch_rng)
            x_masked[bi, :L_i] = mt
            m_arr[bi, :L_i] = mb
        return (
            torch.from_numpy(x_masked),
            torch.from_numpy(x_orig),
            torch.from_numpy(m_arr),
            torch.from_numpy(pad_arr),
        )

    model.train()
    for _ in range(epochs):
        perm = rng.permutation(train_idx).tolist()
        xm, xo, mm, pm = make_batch(perm, rng)
        opt.zero_grad()
        loss, _ = model.masked_reconstruction_loss(
            xm, mm, key_padding_mask=pm, delta=1.0, trim_frac=0.10, target=xo
        )
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()

    model.eval()
    val_rng = np.random.default_rng(seed + 1000)
    n_bands_eval = len(kept_bands)
    with torch.no_grad():
        xm, xo, mm, pm = make_batch(val_idx, val_rng)
        val_loss_t, _ = model.masked_reconstruction_loss(
            xm, mm, key_padding_mask=pm, delta=1.0, trim_frac=0.0, target=xo
        )
        recon, _ = model(xm, mask=mm, key_padding_mask=pm)
        # Band-only masked Huber loss (comparable across weather on/off)
        band_err = F.smooth_l1_loss(
            recon[:, :, :n_bands_eval], xo[:, :, :n_bands_eval], reduction="none", beta=1.0
        ).mean(dim=-1)
        eff_mask = mm & ~pm
        val_band_loss = float(
            (band_err * eff_mask.float()).sum() / eff_mask.sum().clamp(min=1)
        )

    def ssl_score_cycle_array(cycle_arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        n_bins_local = cycle_arr.shape[0]
        s_out = np.full(n_bins_local, np.nan, dtype=np.float64)
        obs = np.where(np.isfinite(cycle_arr[:, 0]))[0]
        if obs.size < 3:
            return s_out, np.zeros(n_bins_local, dtype=bool)
        dsh_o = (obs * bin_days).astype(np.int64)
        times_o = np.datetime64("2020-01-01") + dsh_o.astype("timedelta64[D]")
        w_zero = np.zeros((obs.size, len(WEATHER_KEYS)), dtype=np.float32) if include_weather else None
        t_raw = tok.tokenize(
            bands=cycle_arr[obs].astype(np.float32),
            times=times_o,
            dsh=dsh_o,
            valid_frac=np.ones(obs.size, dtype=np.float32),
            sensor=np.array(["L8"] * obs.size, dtype=object),
            ratoon_no=1,
            weather=w_zero,
        )
        t_std = tok.standardize(np.nan_to_num(t_raw, nan=0.0)).astype(np.float32)
        # 4 complementary deterministic block masks covering every token once
        L_o = obs.size
        tok_errs = np.zeros(L_o, dtype=np.float64)
        with torch.no_grad():
            for fold in range(min(4, L_o)):
                m_fold = np.zeros(L_o, dtype=bool)
                m_fold[fold::4] = True
                x_in = t_std.copy()
                x_in[m_fold] = 0.0
                xt = torch.from_numpy(x_in[None, :, :])
                mt = torch.from_numpy(m_fold[None, :])
                rec_t, _ = model(xt, mask=mt)
                err = (
                    F.smooth_l1_loss(
                        rec_t[0, :, :n_bands_eval],
                        torch.from_numpy(t_std[:, :n_bands_eval]),
                        reduction="none",
                    )
                    .mean(dim=-1)
                    .numpy()
                )
                tok_errs[m_fold] = err[m_fold]
        s_out[obs] = tok_errs * 5.0
        flags, _ = flag_runs(s_out, threshold=3.5, min_run_bins=2)
        return s_out, flags

    # Cycle scores on observed dataset for CWSI proxy correlation
    ssl_cycle_scores = []
    for item in cycle_items:
        s_bins, _ = ssl_score_cycle_array(item["binned_bands"])
        ssl_cycle_scores.append(float(np.nanmean(s_bins)) if np.isfinite(s_bins).any() else np.nan)
    rho_cwsi, _ = spearman_correlation(np.array(ssl_cycle_scores), np.array(cwsi_list))

    X_stack = np.stack([c["binned_bands"] for c in cycle_items], axis=0)
    syn = _evaluate_synthetic_and_auc(X_stack, ssl_score_cycle_array, kept_bands, seed=seed)

    return {
        "ssl_val_loss": float(val_loss_t.item()),
        "ssl_val_band_loss": val_band_loss,
        "ssl_auc_pr": syn["auc_pr"],
        "ssl_non_thermal_auc_pr": syn["non_thermal_auc_pr"],
        "ssl_recall_at_5pct": syn["recall_at_5pct"],
        "ssl_cwsi_spearman": float(rho_cwsi) if np.isfinite(rho_cwsi) else 0.0,
    }


def run_ablation_suite(
    zarr_path: str | Path = "data/processed/fields.zarr",
    cycles_path: str | Path = "data/processed/cycles.parquet",
    drops: list[str] | None = None,
    seeds: list[int] | None = None,
    epochs: int = 15,
) -> dict:
    """Run multi-seed input.drop ablation suite and compute deltas + 95% bootstrap CIs."""
    drops = drops or list(DEFAULT_DROPS)
    if "none" not in [d.lower() for d in drops]:
        drops = ["none"] + list(drops)
    seeds = seeds or [42, 43, 44, 45, 46]

    ds = xr.open_zarr(zarr_path)
    cycles_df = pd.read_parquet(cycles_path)
    raw_bands = [str(b) for b in ds.coords["band"].values]

    per_run_rows: list[dict] = []

    for drop_spec in drops:
        dropped_bands, include_weather = parse_drop_spec(drop_spec)
        kept_bands = [b for b in raw_bands if b not in dropped_bands]
        if not kept_bands:
            log.warning("Drop spec %r removes all bands; skipping", drop_spec)
            continue

        cycle_items = extract_binned_cycles(ds, cycles_df, kept_bands)
        # Fit B1 baseline once on active cycles for this band subset
        X_by_stratum: dict[str, list[np.ndarray]] = {}
        X_by_field: dict[int, list[np.ndarray]] = {}
        for item in cycle_items:
            X_by_stratum.setdefault(item["stratum"], []).append(item["binned_bands"])
            X_by_field.setdefault(item["field"], []).append(item["binned_bands"])
        X_dict = {k: np.stack(v, axis=0) for k, v in X_by_stratum.items()}
        X_dict["all"] = np.concatenate(list(X_dict.values()), axis=0)
        X_field_dict = {fid: np.stack(v, axis=0) for fid, v in X_by_field.items()}
        active = trimmed_normal_cycles(
            X_dict,
            strata_per_cycle={k: np.ones(v.shape[0], dtype=bool) for k, v in X_dict.items()},
            X_by_field=X_field_dict,
            min_n=5,
            q=0.15,
            iters=3,
            threshold=3.5,
        )
        X_act = {k: v[active[k]] for k, v in X_dict.items() if active[k].any()}
        if "all" not in X_act:
            X_act["all"] = X_dict["all"]
        bl = fit_baseline(X_act, X_field_dict, min_n=5, kappa=2.5, floor_pct=5.0)
        bl.band_names = kept_bands

        # B1 CWSI Spearman correlation
        b1_means = []
        cwsi_vals = []
        for item in cycle_items:
            z = score_cycle(item["binned_bands"], bl, stratum=item["stratum"], field_id=item["field"])
            s = aggregate_band_scores(z)
            b1_means.append(float(np.nanmean(s)) if np.isfinite(s).any() else np.nan)
            cwsi_vals.append(item["cwsi_mean"])
        b1_cwsi_rho, _ = spearman_correlation(np.array(b1_means), np.array(cwsi_vals))
        b1_cwsi_rho = float(b1_cwsi_rho) if np.isfinite(b1_cwsi_rho) else 0.0

        X_norm_eval = X_act["all"]

        def b1_score_fn(cyc: np.ndarray, _bl=bl):
            z = score_cycle(cyc, _bl, stratum="all")
            s = aggregate_band_scores(z)
            f, _ = flag_runs(s, threshold=3.5, min_run_bins=2)
            return s, f

        for seed in seeds:
            b1_syn = _evaluate_synthetic_and_auc(X_norm_eval, b1_score_fn, kept_bands, seed=seed)
            ssl_metrics = _train_and_eval_ssl_single_seed(
                cycle_items,
                kept_bands=kept_bands,
                include_weather=include_weather,
                seed=seed,
                epochs=epochs,
            )
            row = {
                "drop": drop_spec,
                "seed": int(seed),
                "include_lst": "ST_B10" in kept_bands,
                "include_weather": bool(include_weather),
                "n_bands": len(kept_bands),
                "b1_auc_pr": b1_syn["auc_pr"],
                "b1_non_thermal_auc_pr": b1_syn["non_thermal_auc_pr"],
                "b1_recall_at_5pct": b1_syn["recall_at_5pct"],
                "b1_cwsi_spearman": b1_cwsi_rho,
                **ssl_metrics,
            }
            per_run_rows.append(row)
        log.info("Finished ablation input.drop=%s across %d seeds", drop_spec, len(seeds))

    runs_df = pd.DataFrame(per_run_rows)
    ref_df = runs_df[runs_df["drop"] == "none"].sort_values("seed")

    metric_cols = [
        "b1_auc_pr",
        "b1_non_thermal_auc_pr",
        "b1_recall_at_5pct",
        "b1_cwsi_spearman",
        "ssl_val_loss",
        "ssl_val_band_loss",
        "ssl_auc_pr",
        "ssl_non_thermal_auc_pr",
        "ssl_recall_at_5pct",
        "ssl_cwsi_spearman",
    ]

    summary_configs: dict[str, dict] = {}
    summary_rows: list[dict] = []

    for drop_spec in drops:
        sub = runs_df[runs_df["drop"] == drop_spec].sort_values("seed")
        if sub.empty:
            continue
        cfg_entry: dict[str, dict | bool | int] = {
            "include_lst": bool(sub["include_lst"].iloc[0]),
            "include_weather": bool(sub["include_weather"].iloc[0]),
            "n_bands": int(sub["n_bands"].iloc[0]),
            "n_seeds": int(len(sub)),
            "metrics": {},
        }
        flat_row: dict = {
            "drop": drop_spec,
            "include_lst": cfg_entry["include_lst"],
            "include_weather": cfg_entry["include_weather"],
            "n_bands": cfg_entry["n_bands"],
        }
        for mc in metric_cols:
            vals = sub[mc].to_numpy(dtype=np.float64)
            pt, lo, hi = bootstrap_ci(np.mean, vals, n_boot=1000, seed=0)
            ref_vals = ref_df[mc].to_numpy(dtype=np.float64)
            diffs = vals - ref_vals if len(vals) == len(ref_vals) else vals - float(np.mean(ref_vals))
            d_pt, d_lo, d_hi = bootstrap_ci(np.mean, diffs, n_boot=1000, seed=1)
            cfg_entry["metrics"][mc] = {  # type: ignore[index]
                "mean": pt,
                "ci_95": [lo, hi],
                "delta_vs_none": d_pt,
                "delta_ci_95": [d_lo, d_hi],
            }
            flat_row[f"{mc}_mean"] = pt
            flat_row[f"{mc}_delta"] = d_pt
            flat_row[f"{mc}_delta_ci_low"] = d_lo
            flat_row[f"{mc}_delta_ci_high"] = d_hi
        summary_configs[drop_spec] = cfg_entry
        summary_rows.append(flat_row)

    return {
        "seeds": seeds,
        "drops": drops,
        "configs": summary_configs,
        "per_seed_runs": per_run_rows,
        "summary_table": summary_rows,
    }


def _parse_cli_args(argv: list[str]) -> tuple[list[str], int, int, Path]:
    ap = argparse.ArgumentParser(description="Run multi-seed input.drop ablations with 95% CI.")
    ap.add_argument("-m", "--multirun", action="store_true", help="Hydra-compatible multirun flag.")
    ap.add_argument("--drops", default=None, help="Comma-separated input.drop specs.")
    ap.add_argument("--n-seeds", default=5, type=int)
    ap.add_argument("--epochs", default=15, type=int)
    ap.add_argument("--out", default=Path("reports/ablation.json"), type=Path)
    args, unknown = ap.parse_known_args(argv)

    drops = [d.strip() for d in args.drops.split(",") if d.strip()] if args.drops else list(DEFAULT_DROPS)
    n_seeds = args.n_seeds
    epochs = args.epochs
    # Support Hydra-style positional overrides: input.drop=none,lst,weather seeds=5
    for tok in unknown:
        if tok.startswith("input.drop="):
            val = tok.split("=", 1)[1]
            drops = [d.strip() for d in val.split(",") if d.strip()]
        elif tok.startswith("seeds=") or tok.startswith("train.n_seeds="):
            n_seeds = int(tok.split("=", 1)[1])
        elif tok.startswith("ssl.max_epochs="):
            epochs = int(tok.split("=", 1)[1])
    return drops, n_seeds, epochs, args.out


def main(argv: list[str] | None = None) -> int:
    limit_threads(2)
    drops, n_seeds, epochs, out_path = _parse_cli_args(sys.argv[1:] if argv is None else argv)
    seeds = [42 + i for i in range(n_seeds)]

    report = run_ablation_suite(drops=drops, seeds=seeds, epochs=epochs)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))

    csv_path = out_path.with_name("ablation_summary.csv")
    pd.DataFrame(report["summary_table"]).to_csv(csv_path, index=False)

    log.info("Wrote ablation report to %s and %s", out_path, csv_path)
    print("\n=== Ablation Summary (5 seeds, 95% Bootstrap CI) ===")
    for cfg_name, info in report["configs"].items():
        m = info["metrics"]
        print(
            f"  input.drop={cfg_name:<12} | "
            f"B1 AUC-PR={m['b1_auc_pr']['mean']:.3f} (Δ={m['b1_auc_pr']['delta_vs_none']:+.3f} "
            f"[{m['b1_auc_pr']['delta_ci_95'][0]:+.3f}, {m['b1_auc_pr']['delta_ci_95'][1]:+.3f}]) | "
            f"B1 CWSI rho={m['b1_cwsi_spearman']['mean']:+.3f} | "
            f"SSL BandLoss={m['ssl_val_band_loss']['mean']:.3f} (Δ={m['ssl_val_band_loss']['delta_vs_none']:+.3f} "
            f"[{m['ssl_val_band_loss']['delta_ci_95'][0]:+.3f}, {m['ssl_val_band_loss']['delta_ci_95'][1]:+.3f}]) | "
            f"SSL AUC-PR={m['ssl_auc_pr']['mean']:.3f} (Δ={m['ssl_auc_pr']['delta_vs_none']:+.3f})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
