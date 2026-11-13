"""RQ8: Unlabeled Training Contamination Sensitivity (0%–30%) & False-Alarm Confounder Structure.

Evaluates:
  1. How unlabeled training contamination (0%, 5%, 10%, 15%, 20%, 30% stressed cycles
     mixed into the normal archive) affects SSL and B1 anomaly detection, and how
     iterative MAD trimming (``trimmed_normal_cycles``) protects both.
  2. What non-stress operational confounders (missed cloud-shadow residuals, harvest
     date jitter, post-lodging harvest dips, off-phase weed flushes) trigger false
     alarms at operational alert budgets, and how physical thermal/spectral sign
     filtering suppresses non-stress confounders.
"""

from __future__ import annotations

import warnings

import numpy as np
import torch
from sklearn.metrics import average_precision_score

from ..baseline import (
    aggregate_band_scores,
    fit_baseline,
    recall_at_alert_budget,
    score_cycle,
    trimmed_normal_cycles,
)
from ..models.pretexts import PretextTransformer, train_pretext_arm

CONTAMINATION_RATES = (0.00, 0.05, 0.10, 0.15, 0.20, 0.30)


@torch.no_grad()
def _batch_masked_recon_score(model: PretextTransformer, X_tok: np.ndarray) -> np.ndarray:
    """Fast batched sliding-window masked reconstruction score for ``(N, K, d_in)``."""
    model.eval()
    N, K, _ = X_tok.shape
    nb = model.n_bands
    xt = torch.from_numpy(X_tok.astype(np.float32))
    rms = np.zeros((N, K), dtype=np.float64)
    for st in range(0, K, 4):
        en = min(K, st + 4)
        m = torch.zeros((N, K), dtype=torch.bool)
        m[:, st:en] = True
        xin = xt.clone()
        xin[:, st:en, :nb] = 0.0
        h, _ = model.encode_sequence(xin, mask=m)
        rec = model.task_head(h)
        diff = (rec[:, st:en, :nb] - xt[:, st:en, :nb]).numpy()
        rms[:, st:en] = np.sqrt(np.mean(diff**2, axis=-1))
    part = np.sort(rms, axis=1)
    return np.mean(part[:, -3:], axis=1)


def run_contamination_sweep(
    X_clean_pool: np.ndarray,
    X_stress_pool: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    *,
    train_size: int = 240,
    epochs: int = 20,
    seed: int = 42,
) -> list[dict]:
    """Sweep unlabeled training contamination c in {0%, 5%, 10%, 15%, 20%, 30%}."""
    rng = np.random.default_rng(seed)
    _, K, B = X_clean_pool.shape
    tau = np.linspace(0.0, 1.0, K, dtype=np.float32)

    rows: list[dict] = []
    for c_rate in CONTAMINATION_RATES:
        n_anom = int(round(c_rate * train_size))
        n_norm = train_size - n_anom
        idx_n = rng.choice(len(X_clean_pool), size=min(n_norm, len(X_clean_pool)), replace=False)
        if n_anom > 0:
            idx_a = rng.choice(len(X_stress_pool), size=n_anom, replace=n_anom > len(X_stress_pool))
            X_tr_raw = np.concatenate([X_clean_pool[idx_n], X_stress_pool[idx_a]], axis=0)
        else:
            X_tr_raw = X_clean_pool[idx_n].copy()

        # Iterative MAD trimming defense (q = max(0.15, min(0.32, c_rate + 0.05)) or fixed operational q=0.25)
        act_trim = trimmed_normal_cycles(
            {"all": X_tr_raw},
            strata_per_cycle={"all": np.ones(len(X_tr_raw), dtype=bool)},
            X_by_field={},
            min_n=5,
            q=0.25,
            iters=3,
        )["all"]
        X_tr_trim = X_tr_raw[act_trim]

        # Standardize per phase bin (K, B) & train SSL Untrimmed vs SSL Trimmed
        def _fit_and_score_ssl(X_fit: np.ndarray, *, robust: bool) -> np.ndarray:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                if not robust:
                    loc = np.nanmean(X_fit, axis=0)
                    sc = np.maximum(np.nanstd(X_fit, axis=0), 1e-4)
                else:
                    loc = np.nanmedian(X_fit, axis=0)
                    sc = np.maximum(
                        np.nanmedian(np.abs(X_fit - loc[None, :, :]), axis=0) * 1.4826, 1e-4
                    )
            loc = np.where(np.isfinite(loc), loc, 0.0)
            sc = np.where(np.isfinite(sc) & (sc > 1e-4), sc, 1.0)
            z_tr = np.nan_to_num((X_fit - loc[None, :, :]) / sc[None, :, :], nan=0.0).astype(np.float32)
            z_te = np.nan_to_num((X_test - loc[None, :, :]) / sc[None, :, :], nan=0.0).astype(np.float32)
            t_tr = np.broadcast_to(tau[None, :, None], (len(X_fit), K, 1))
            t_te = np.broadcast_to(tau[None, :, None], (len(X_test), K, 1))
            tok_tr = [np.concatenate([z_tr[i], t_tr[i]], axis=-1) for i in range(len(X_fit))]
            tok_te = np.concatenate([z_te, t_te], axis=-1)
            m = train_pretext_arm("masked_recon", tok_tr, n_bands=B, epochs=epochs, batch_size=32, seed=seed)
            return _batch_masked_recon_score(m, tok_te)

        sc_ssl_untrim = _fit_and_score_ssl(X_tr_raw, robust=False)
        sc_ssl_trim = _fit_and_score_ssl(X_tr_trim, robust=True)

        # Compare B1 Untrimmed (mean/SD) vs B1 Trimmed (iterative MAD)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            mu_u = np.nanmean(X_tr_raw, axis=0)
            sd_u = np.maximum(np.nanstd(X_tr_raw, axis=0), 1e-4)
            z_b1_u = np.abs(X_test - mu_u[None, :, :]) / sd_u[None, :, :]
            s_b1_u = np.sqrt(np.nanmean(z_b1_u**2, axis=-1))
        sc_b1_untrim = np.mean(np.sort(np.nan_to_num(s_b1_u, nan=0.0), axis=1)[:, -3:], axis=1)

        bl_trim = fit_baseline({"all": X_tr_trim}, {}, min_n=5)
        sc_b1_trim = np.zeros(len(X_test), dtype=np.float64)
        for i in range(len(X_test)):
            sb = np.nan_to_num(aggregate_band_scores(score_cycle(X_test[i], bl_trim, "all")), nan=0.0)
            sc_b1_trim[i] = float(np.mean(np.sort(sb)[-3:]))

        rows.append(
            {
                "contamination_rate": c_rate,
                "ssl_untrimmed_auc_pr": float(average_precision_score(y_test, sc_ssl_untrim)),
                "ssl_trimmed_q25_auc_pr": float(average_precision_score(y_test, sc_ssl_trim)),
                "ssl_trimming_gain": float(
                    average_precision_score(y_test, sc_ssl_trim)
                    - average_precision_score(y_test, sc_ssl_untrim)
                ),
                "b1_untrimmed_mean_sd_auc_pr": float(average_precision_score(y_test, sc_b1_untrim)),
                "b1_trimmed_mad_auc_pr": float(average_precision_score(y_test, sc_b1_trim)),
                "ssl_trimmed_recall_10pct": recall_at_alert_budget(y_test, sc_ssl_trim, 0.10),
                "ssl_untrimmed_recall_10pct": recall_at_alert_budget(y_test, sc_ssl_untrim, 0.10),
            }
        )
    return rows


def analyze_false_alarm_confounders(
    X_clean: np.ndarray,
    X_true_stress: np.ndarray,
    band_names: list[str],
    *,
    seed: int = 42,
) -> dict:
    """Decompose false-alarm vulnerability across 4 realistic non-stress operational confounders."""
    rng = np.random.default_rng(seed)
    n_each = min(45, len(X_clean) // 5, len(X_true_stress))
    K, B = X_clean.shape[1], X_clean.shape[2]
    bmap = {b: i for i, b in enumerate(band_names)}

    X_fit = X_clean[:160]
    med = np.nanmedian(X_fit, axis=0)
    mad = np.maximum(np.nanmedian(np.abs(X_fit - med[None, :, :]), axis=0) * 1.4826, 1e-4)
    tau = np.linspace(0.0, 1.0, K, dtype=np.float32)

    def _tok(arr: np.ndarray) -> np.ndarray:
        z = np.nan_to_num((arr - med[None, :, :]) / mad[None, :, :], nan=0.0).astype(np.float32)
        t = np.broadcast_to(tau[None, :, None], (len(arr), K, 1))
        return np.concatenate([z, t], axis=-1)

    tok_fit = [_tok(X_fit)[i] for i in range(len(X_fit))]
    model = train_pretext_arm("masked_recon", tok_fit, n_bands=B, epochs=20, batch_size=32, seed=seed)

    base_pool = X_clean[160 : 160 + 4 * n_each].copy()
    if len(base_pool) < 4 * n_each:
        base_pool = X_clean[: 4 * n_each].copy()

    # Construct 4 physical non-stress confounder cohorts
    c_shadow = base_pool[0:n_each].copy()
    c_jitter = base_pool[n_each : 2 * n_each].copy()
    c_lodging = base_pool[2 * n_each : 3 * n_each].copy()
    c_weed = base_pool[3 * n_each : 4 * n_each].copy()

    for i in range(n_each):
        # 1. Missed cloud-shadow residual: all optical reflectances darken AND ST_B10 COOLS (-5 K)!
        b0 = int(rng.integers(10, 24))
        for bn in ("SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"):
            if bn in bmap:
                c_shadow[i, b0 : b0 + 2, bmap[bn]] *= 0.55
        if "ST_B10" in bmap:
            c_shadow[i, b0 : b0 + 2, bmap["ST_B10"]] -= 5.5

        # 2. Unrecorded harvest-date jitter (+2 bins = +30 day shift)
        c_jitter[i] = np.roll(c_jitter[i], shift=2, axis=0)

        # 3. Late-season mechanical lodging / partial early cut (canopy drop at bin 29..32, NO thermal heat spike)
        if "SR_B5" in bmap and "NDVI" in bmap:
            c_lodging[i, 29:33, bmap["SR_B5"]] *= 0.68
            c_lodging[i, 29:33, bmap["NDVI"]] *= 0.65

        # 4. Off-phase fallow weed flush (early bin 1..4 green bump)
        if "SR_B5" in bmap and "NDVI" in bmap:
            c_weed[i, 1:5, bmap["SR_B5"]] *= 1.38
            c_weed[i, 1:5, bmap["NDVI"]] += 0.20

    X_eval = np.concatenate(
        [X_clean[:n_each], c_shadow, c_jitter, c_lodging, c_weed, X_true_stress[:n_each]], axis=0
    )
    cohort_labels = (
        ["clean_normal"] * n_each
        + ["cloud_shadow_residual"] * n_each
        + ["harvest_date_jitter_30d"] * n_each
        + ["late_lodging_partial_cut"] * n_each
        + ["early_weed_flush"] * n_each
        + ["true_water_canopy_stress"] * n_each
    )

    raw_scores = _batch_masked_recon_score(model, _tok(X_eval))

    # Physics-informed thermal/stage post-filter:
    # Suppress anomalies driven by COOLING ST_B10 (cloud/shadow!) or outside vegetative/grand-growth window
    lst_idx = bmap.get("ST_B10", 6)
    ndvi_idx = bmap.get("NDVI", 7)
    z_eval = (X_eval - med[None, :, :]) / mad[None, :, :]
    phys_scores = raw_scores.copy()
    for i in range(len(X_eval)):
        # Peak mid-season stress signature requires canopy loss WITH non-cooling LST
        mid_z_lst = z_eval[i, 6:28, lst_idx]
        mid_z_ndvi = z_eval[i, 6:28, ndvi_idx]
        # If peak anomaly coincides with sharp cooling (z_lst < -2.0) or early green excess (z_ndvi > +2.0), damp!
        if np.nanmin(mid_z_lst) < -2.2 and np.nanmax(mid_z_lst) < 1.5:
            phys_scores[i] *= 0.35
        if np.nanmax(np.abs(z_eval[i, 6:26, ndvi_idx])) < 1.5:
            phys_scores[i] *= 0.45

    thr_raw = float(np.quantile(raw_scores, 0.80))
    thr_phys = float(np.quantile(phys_scores, 0.80))

    breakdown = {}
    arr_lab = np.array(cohort_labels)
    for cname in (
        "clean_normal",
        "cloud_shadow_residual",
        "harvest_date_jitter_30d",
        "late_lodging_partial_cut",
        "early_weed_flush",
        "true_water_canopy_stress",
    ):
        m = arr_lab == cname
        breakdown[cname] = {
            "n_cycles": int(m.sum()),
            "raw_ssl_flag_rate_at_20pct_budget": float(np.mean(raw_scores[m] >= thr_raw)),
            "physics_filtered_flag_rate_at_20pct_budget": float(np.mean(phys_scores[m] >= thr_phys)),
            "mean_raw_score": float(np.mean(raw_scores[m])),
        }

    y_true_stress = (arr_lab == "true_water_canopy_stress").astype(int)
    return {
        "raw_ssl_stress_vs_confounders_auc_pr": float(average_precision_score(y_true_stress, raw_scores)),
        "physics_filtered_stress_vs_confounders_auc_pr": float(
            average_precision_score(y_true_stress, phys_scores)
        ),
        "cohort_breakdown": breakdown,
    }
