"""RQ5 (Gap G5): Early-Detection Lead-Time Evaluator under Leave-One-Year-Out Validation.

Measures how many days earlier multi-band optical+thermal SSL detects progressive
crop water/canopy stress compared to operational NDVI thresholds and statistical
run filters at an identical calibrated 5% false-alarm budget, benchmarked against
EigenCL's 12-day early-detection reference point.
"""

from __future__ import annotations

import warnings

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

from ..baseline import aggregate_band_scores, cusum_detector, fit_baseline, flag_runs, score_cycle
from ..models.masked_tf import MaskedTransformer
from .stats import bootstrap_ci

EIGENCL_REFERENCE_LEAD_DAYS = 12.0


def simulate_progressive_onset_archive(
    n_cycles: int = 360,
    K: int = 36,
    bin_days: int = 15,
    stress_frac: float = 0.25,
    seed: int = 42,
) -> dict:
    """Create multi-year progressive stress trajectories reflecting stomatal-before-chlorophyll physics.

    Agronomic biophysics (Jackson et al. 1981; Idso et al. 1981):
      - Day ``t_onset`` (bin ``b0``): Irrigation deficit / root-zone salinity begins ->
        stomatal conductance drops immediately -> canopy temperature (``ST_B10``) rises
        by +1.8..+3.5 K and SWIR leaf-water absorption (``SR_B6/B7``) rises within the
        first 0–15 days, while green chlorophyll / ``NDVI`` initially declines by only
        2–5% before accelerating into visible senescence 15–45 days later!
    """
    rng = np.random.default_rng(seed)
    B = 8  # SR_B2..SR_B7, ST_B10, NDVI
    tau = np.linspace(0.0, 1.0, K, dtype=np.float64)
    canopy = np.sin(np.pi * np.clip(tau, 0.02, 0.98)) ** 0.75

    X = np.zeros((n_cycles, K, B), dtype=np.float64)
    years = rng.integers(2015, 2025, size=n_cycles)
    onset_bin = np.full(n_cycles, -1, dtype=np.int64)
    is_stress = np.zeros(n_cycles, dtype=np.int32)

    for i in range(n_cycles):
        c_i = canopy * rng.uniform(0.93, 1.06)
        X[i, :, 0] = 0.08 - 0.03 * c_i + rng.normal(0, 0.007, K)
        X[i, :, 1] = 0.11 - 0.03 * c_i + rng.normal(0, 0.008, K)
        X[i, :, 2] = 0.16 - 0.10 * c_i + rng.normal(0, 0.010, K)  # Red
        X[i, :, 3] = 0.19 + 0.28 * c_i + rng.normal(0, 0.015, K)  # NIR
        X[i, :, 4] = 0.26 - 0.08 * c_i + rng.normal(0, 0.012, K)  # SWIR1
        X[i, :, 5] = 0.19 - 0.09 * c_i + rng.normal(0, 0.011, K)  # SWIR2
        X[i, :, 6] = 301.0 + 10.0 * np.sin(np.pi * tau) - 4.0 * c_i + rng.normal(0, 1.1, K)  # LST

        if rng.random() < stress_frac:
            is_stress[i] = 1
            b0 = int(rng.integers(10, 19))  # mid-season onset (day 150..285)
            onset_bin[i] = b0
            steps = np.arange(K - b0, dtype=np.float64)
            # Immediate thermal + SWIR response; delayed quadratic NDVI/NIR canopy loss
            lst_rise = 2.6 * (1.0 - np.exp(-steps / 1.2)) + 1.6 * np.clip(steps / 8.0, 0, 1)
            swir_rise = 0.035 * (1.0 - np.exp(-steps / 1.5)) + 0.03 * np.clip(steps / 7.0, 0, 1)
            nir_drop_frac = 0.03 * np.clip(steps / 2.0, 0, 1) + 0.32 * np.clip((steps - 1.5) / 5.0, 0, 1) ** 1.4
            red_rise_frac = 0.02 + 0.28 * np.clip((steps - 1.5) / 5.0, 0, 1) ** 1.4

            X[i, b0:, 6] += lst_rise
            X[i, b0:, 4] += swir_rise
            X[i, b0:, 5] += swir_rise * 0.9
            X[i, b0:, 3] *= 1.0 - nir_drop_frac
            X[i, b0:, 2] *= 1.0 + red_rise_frac

        r, n = X[i, :, 2], X[i, :, 3]
        X[i, :, 7] = (n - r) / np.maximum(n + r, 1e-6)

    return {
        "X": X,
        "years": years,
        "is_stress": is_stress,
        "onset_bin": onset_bin,
        "bin_days": bin_days,
    }


def _causal_ssl_step_scores(
    X_train_clean: np.ndarray,
    X_eval: np.ndarray,
    *,
    epochs: int = 18,
    seed: int = 42,
) -> np.ndarray:
    """Train MaskedTransformer on clean cycles and compute CAUSAL online step-k scores ``(N, K)``.

    At each phase bin ``k``, only observations ``0..k`` are revealed (bins ``>k`` are
    padding-masked, and bin ``k`` itself is masked and predicted from causal history ``0..k-1``!).
    """
    torch.manual_seed(seed)
    _, K, B = X_train_clean.shape
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        med = np.nanmedian(X_train_clean, axis=(0, 1))
        mad = np.nanmedian(np.abs(X_train_clean - med[None, None, :]), axis=(0, 1)) * 1.4826
    scale = np.where(np.isfinite(mad) & (mad > 1e-4), mad, 1.0)

    def _tok(arr: np.ndarray) -> torch.Tensor:
        z = np.nan_to_num((arr - med[None, None, :]) / scale[None, None, :], nan=0.0).astype(np.float32)
        tau_f = np.broadcast_to(np.linspace(0.0, 1.0, K, dtype=np.float32)[None, :, None], (len(arr), K, 1))
        return torch.from_numpy(np.concatenate([z, tau_f], axis=-1))

    tr_t = _tok(X_train_clean)
    ev_t = _tok(X_eval)
    d_in = tr_t.shape[-1]

    model = MaskedTransformer(d_in=d_in, d_model=64, n_heads=4, n_layers=3, d_ff=128, max_len=K + 4)
    opt = torch.optim.AdamW(model.parameters(), lr=1.8e-3, weight_decay=1e-4)
    dl = DataLoader(TensorDataset(tr_t), batch_size=64, shuffle=True)
    rng = np.random.default_rng(seed)

    model.train()
    for _ in range(epochs):
        for (bx,) in dl:
            bsz = bx.size(0)
            # Causal-prefix training: truncate future after random cutoff c_k and mask step c_k
            pad = torch.zeros((bsz, K), dtype=torch.bool)
            m = torch.zeros((bsz, K), dtype=torch.bool)
            for bi in range(bsz):
                ck = int(rng.integers(5, K))
                if ck + 1 < K:
                    pad[bi, ck + 1 :] = True
                m[bi, ck] = True
                # Also random historical mask
                hm = rng.random(ck) < 0.20
                m[bi, :ck] = torch.from_numpy(hm)
            xin = bx.clone()
            xin[:, :, :B][m] = 0.0
            loss, _ = model.masked_reconstruction_loss(xin, m, key_padding_mask=pad, target=bx)
            opt.zero_grad()
            loss.backward()
            opt.step()

    model.eval()
    N_ev = len(X_eval)
    step_scores = np.zeros((N_ev, K), dtype=np.float64)
    with torch.no_grad():
        for k in range(4, K):
            pad = torch.zeros((N_ev, K), dtype=torch.bool)
            if k + 1 < K:
                pad[:, k + 1 :] = True
            m = torch.zeros((N_ev, K), dtype=torch.bool)
            m[:, k] = True
            xin = ev_t.clone()
            xin[:, k, :B] = 0.0
            recon, _ = model(xin, mask=m, key_padding_mask=pad)
            diff = (recon[:, k, :B] - ev_t[:, k, :B]).numpy()
            # Two-step causal smoothing (0.65 * err_k + 0.35 * err_{k-1}) to suppress single-scene noise
            rms_k = np.sqrt(np.mean(diff**2, axis=-1))
            step_scores[:, k] = 0.65 * rms_k + 0.35 * step_scores[:, k - 1] if k > 4 else rms_k
    return step_scores


def run_loyo_early_detection(archive: dict, false_alarm_budget: float = 0.05, seed: int = 42) -> dict:
    """Evaluate causal detection delay (days) at matched 5% false-alarm rate across LOYO folds."""
    X = archive["X"]
    years = archive["years"]
    is_stress = archive["is_stress"]
    onset_bin = archive["onset_bin"]
    bin_days = int(archive["bin_days"])
    N, K, _ = X.shape
    ndvi_idx = 7

    uniq_years = sorted(int(y) for y in np.unique(years))
    # Limit to 5 evenly spaced LOYO folds for fast CPU turnaround
    if len(uniq_years) > 5:
        sel = np.linspace(0, len(uniq_years) - 1, 5).round().astype(int)
        eval_years = [uniq_years[i] for i in sel]
    else:
        eval_years = uniq_years

    methods = ("SSL_Causal_OpticalThermal", "B1_CUSUM_Causal", "B1_PhaseZ_Causal", "NDVI_Index_Threshold")
    delays_days: dict[str, list[float]] = {m: [] for m in methods}
    detected_flags: dict[str, list[int]] = {m: [] for m in methods}
    paired_lead_vs_ndvi: list[float] = []

    for yi, yr in enumerate(eval_years):
        tr = np.where((years != yr) & (is_stress == 0))[0]
        va = np.where(years == yr)[0]
        if tr.size < 20 or va.size < 5:
            continue

        # Calibrate thresholds on held-out portion of clean training cycles for exact 5% FAR
        n_cal = max(15, tr.size // 4)
        cal_idx = tr[-n_cal:]
        fit_idx = tr[:-n_cal]

        X_fit = X[fit_idx]
        X_cal_and_va = X[np.concatenate([cal_idx, va])]

        # 1. Causal SSL step scores
        ssl_steps_all = _causal_ssl_step_scores(X_fit, X_cal_and_va, epochs=16, seed=seed + yi)

        # 2. B1 Phase Z & Causal CUSUM step scores + 3. NDVI Threshold step scores
        bl = fit_baseline({"all": X_fit}, {}, min_n=5)
        nd_med = np.nanmedian(X_fit[:, :, ndvi_idx], axis=0)
        nd_mad = np.maximum(
            np.nanmedian(np.abs(X_fit[:, :, ndvi_idx] - nd_med[None, :]), axis=0) * 1.4826, 0.02
        )

        b1_steps = np.zeros_like(ssl_steps_all)
        cus_steps = np.zeros_like(ssl_steps_all)
        ndvi_steps = np.zeros_like(ssl_steps_all)

        for i, xc in enumerate(X_cal_and_va):
            z = score_cycle(xc, bl, "all")
            s_bin = np.nan_to_num(aggregate_band_scores(z), nan=0.0)
            # Causal 2-step moving min/mean for B1 run-equivalent online score
            for k in range(4, K):
                b1_steps[i, k] = 0.5 * (s_bin[k] + s_bin[k - 1])
            _, c_stat = cusum_detector(s_bin, drift_k=1.15, decision_h=4.0)
            cus_steps[i] = np.nan_to_num(c_stat, nan=0.0)
            ndvi_def = (nd_med - xc[:, ndvi_idx]) / nd_mad
            for k in range(4, K):
                ndvi_steps[i, k] = 0.5 * (ndvi_def[k] + ndvi_def[k - 1])
            _ = flag_runs

        step_map = {
            "SSL_Causal_OpticalThermal": ssl_steps_all,
            "B1_CUSUM_Causal": cus_steps,
            "B1_PhaseZ_Causal": b1_steps,
            "NDVI_Index_Threshold": ndvi_steps,
        }

        # Calibrate cycle-max threshold on clean calibration cycles at (1 - false_alarm_budget) quantile
        thresholds: dict[str, float] = {}
        for m_name, st_arr in step_map.items():
            cal_cycle_max = np.max(st_arr[:n_cal, 6:], axis=1)
            thresholds[m_name] = float(np.quantile(cal_cycle_max, 1.0 - false_alarm_budget))

        # Measure first-alarm bin >= onset_bin on stressed validation cycles
        for loc_j, glob_idx in enumerate(va):
            if is_stress[glob_idx] != 1:
                continue
            b0 = int(onset_bin[glob_idx])
            row_idx = n_cal + loc_j
            det_bin: dict[str, int | None] = {}
            for m_name, st_arr in step_map.items():
                hits = np.where(st_arr[row_idx, b0:] > thresholds[m_name])[0]
                if hits.size > 0:
                    first_b = b0 + int(hits[0])
                    det_bin[m_name] = first_b
                    delays_days[m_name].append(float((first_b - b0) * bin_days))
                    detected_flags[m_name].append(1)
                else:
                    det_bin[m_name] = None
                    detected_flags[m_name].append(0)

            # Paired lead time when NDVI eventually detects (or censoring at cycle end K)
            b_ssl = det_bin["SSL_Causal_OpticalThermal"]
            b_ndvi = det_bin["NDVI_Index_Threshold"]
            if b_ssl is not None:
                eff_ndvi = b_ndvi if b_ndvi is not None else K
                paired_lead_vs_ndvi.append(float((eff_ndvi - b_ssl) * bin_days))

    out_methods: dict[str, dict] = {}
    for m_name in methods:
        d_arr = np.array(delays_days[m_name], dtype=np.float64)
        det_rate = float(np.mean(detected_flags[m_name])) if detected_flags[m_name] else 0.0
        if d_arr.size >= 2:
            dm, dlo, dhi = bootstrap_ci(np.mean, d_arr, n_boot=1000, seed=seed)
            med_d = float(np.median(d_arr))
        else:
            dm = dlo = dhi = med_d = np.nan
        out_methods[m_name] = {
            "detection_rate_at_5pct_far": det_rate,
            "mean_delay_days_from_onset": dm,
            "delay_days_ci_95": [dlo, dhi],
            "median_delay_days_from_onset": med_d,
        }

    lead_arr = np.array(paired_lead_vs_ndvi, dtype=np.float64)
    lm, llo, lhi = (
        bootstrap_ci(np.mean, lead_arr, n_boot=1000, seed=seed)
        if lead_arr.size >= 2
        else (0.0, 0.0, 0.0)
    )
    return {
        "false_alarm_budget": false_alarm_budget,
        "eigencl_reference_lead_days": EIGENCL_REFERENCE_LEAD_DAYS,
        "ssl_lead_time_vs_ndvi_mean_days": lm,
        "ssl_lead_time_vs_ndvi_ci_95": [llo, lhi],
        "ssl_lead_time_vs_ndvi_median_days": float(np.median(lead_arr)) if lead_arr.size else 0.0,
        "exceeds_eigencl_12d_reference": bool(lm >= EIGENCL_REFERENCE_LEAD_DAYS),
        "methods": out_methods,
    }
