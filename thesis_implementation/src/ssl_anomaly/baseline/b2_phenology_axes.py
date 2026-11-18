"""Baseline B2: Alternative phenological progress axes (GDD thermal time & Landmarks).

Implements normalized progress binning ``bin_by_progress`` plus two non-linear
phenological progress parameterizations replacing linear tau / days-since-harvest:
  1. ``gdd_progress``: Cumulative Growing Degree Days (max(0, T_mean - T_base))
     normalized across each harvest-to-harvest cycle.
  2. ``landmark_progress``: Three-piece linear registration anchoring green-up onset
     and peak canopy NDVI to canonical reference landmarks (tau_green*, tau_peak*).
"""

from __future__ import annotations

import numpy as np


def progress_axis(obs_days: np.ndarray, start_day: int, end_day: int) -> np.ndarray:
    """Normalized linear cycle progress ``tau in [0, 1]`` over ``[start_day, end_day]``."""
    obs_d = np.asarray(obs_days, dtype=np.float64)
    dur = float(end_day - start_day)
    if dur <= 0:
        return np.zeros_like(obs_d, dtype=np.float64)
    return np.clip((obs_d - float(start_day)) / dur, 0.0, 1.0)


def bin_by_progress(
    tau: np.ndarray,
    values: np.ndarray,
    *,
    K: int = 36,
    agg: str = "median",
    max_interp_adjacent: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    """Bin a ``(T, B)`` or ``(T,)`` series along normalized progress ``tau in [0, 1]`` into ``K`` bins."""
    t = np.asarray(tau, dtype=np.float64)
    v = np.asarray(values, dtype=np.float64)
    squeeze = v.ndim == 1
    if squeeze:
        v = v[:, None]
    B = v.shape[1]
    binned = np.full((K, B), np.nan, dtype=np.float64)
    counts = np.zeros(K, dtype=np.int32)
    valid_t = np.isfinite(t) & (t >= 0.0) & (t <= 1.0)
    idx = np.clip((t * K).astype(int), 0, K - 1)
    for k in range(K):
        sel = valid_t & (idx == k)
        if not np.any(sel):
            continue
        sub = v[sel]
        counts[k] = int(np.any(np.isfinite(sub), axis=1).sum())
        if counts[k] == 0:
            continue
        with np.errstate(all="ignore"):
            binned[k] = np.nanmedian(sub, axis=0) if agg == "median" else np.nanmean(sub, axis=0)

    if max_interp_adjacent > 0:
        for b in range(B):
            obs = ~np.isnan(binned[:, b])
            for j in range(1, K - 1):
                if not obs[j] and obs[j - 1] and obs[j + 1]:
                    binned[j, b] = 0.5 * (binned[j - 1, b] + binned[j + 1, b])

    if squeeze:
        return binned[:, 0], counts
    return binned, counts


def gdd_progress(
    obs_days: np.ndarray,
    start_day: int,
    end_day: int,
    weather_days: np.ndarray,
    temp_c: np.ndarray,
    *,
    t_base_c: float = 12.0,
) -> np.ndarray:
    """Compute thermal-time progress ``tau_gdd in [0, 1]`` for observations in ``[start_day, end_day]``."""
    obs_d = np.asarray(obs_days, dtype=np.float64)
    linear_tau = progress_axis(obs_d, start_day, end_day)
    if end_day <= start_day:
        return linear_tau

    w_d = np.asarray(weather_days, dtype=np.float64)
    w_t = np.asarray(temp_c, dtype=np.float64)
    fin = np.isfinite(w_d) & np.isfinite(w_t)
    if int(fin.sum()) < 2:
        return linear_tau

    w_d = w_d[fin]
    w_t = w_t[fin]
    order = np.argsort(w_d)
    w_d = w_d[order]
    w_t = w_t[order]

    daily_grid = np.arange(int(start_day), int(end_day) + 1, dtype=np.float64)
    daily_temp = np.interp(daily_grid, w_d, w_t)
    daily_gdd = np.maximum(0.0, daily_temp - float(t_base_c))
    cum_gdd = np.cumsum(daily_gdd)
    cum_gdd = cum_gdd - cum_gdd[0]
    total_gdd = float(cum_gdd[-1])
    if total_gdd <= 1e-6:
        return linear_tau

    obs_cum = np.interp(np.clip(obs_d, float(start_day), float(end_day)), daily_grid, cum_gdd)
    return np.clip(obs_cum / total_gdd, 0.0, 1.0)


def detect_cycle_landmarks(
    obs_days: np.ndarray,
    ndvi: np.ndarray,
    start_day: int,
    end_day: int,
    *,
    greenup_rel_frac: float = 0.25,
) -> tuple[float, float]:
    """Identify ``(t_greenup, t_peak)`` within ``(start_day, end_day)`` from cycle NDVI."""
    dur = float(end_day - start_day)
    default_g = float(start_day) + 0.20 * dur
    default_p = float(start_day) + 0.55 * dur
    if dur <= 10:
        return default_g, default_p

    d = np.asarray(obs_days, dtype=np.float64)
    y = np.asarray(ndvi, dtype=np.float64)
    fin = np.isfinite(d) & np.isfinite(y) & (d >= start_day) & (d <= end_day)
    if int(fin.sum()) < 5:
        return default_g, default_p

    d = d[fin]
    y = y[fin]
    order = np.argsort(d)
    d = d[order]
    y = y[order]

    grid = np.linspace(float(start_day), float(end_day), 200)
    yg = np.interp(grid, d, y)
    kernel = np.ones(9, dtype=np.float64) / 9.0
    ys = np.convolve(np.pad(yg, 4, mode="edge"), kernel, mode="valid")

    i_lo = int(0.15 * len(grid))
    i_hi = max(i_lo + 1, int(0.90 * len(grid)))
    peak_rel = int(np.argmax(ys[i_lo:i_hi])) + i_lo
    t_peak = float(grid[peak_rel])
    peak_val = float(ys[peak_rel])
    init_min = float(np.min(ys[: max(1, peak_rel + 1)]))
    amp = peak_val - init_min
    if amp < 0.08:
        return default_g, default_p

    thresh = init_min + float(greenup_rel_frac) * amp
    pre_peak = np.where(ys[: peak_rel + 1] >= thresh)[0]
    t_green = float(grid[int(pre_peak[0])]) if pre_peak.size > 0 else default_g

    min_gap = 0.05 * dur
    t_green = float(np.clip(t_green, float(start_day) + min_gap, float(end_day) - 2 * min_gap))
    t_peak = float(np.clip(t_peak, t_green + min_gap, float(end_day) - min_gap))
    return t_green, t_peak


def landmark_progress(
    obs_days: np.ndarray,
    ndvi: np.ndarray,
    start_day: int,
    end_day: int,
    *,
    canon_greenup: float = 0.20,
    canon_peak: float = 0.55,
) -> np.ndarray:
    """Piecewise-linear landmark warping of cycle days onto ``[0, 1]``."""
    obs_d = np.asarray(obs_days, dtype=np.float64)
    dur = float(end_day - start_day)
    if dur <= 0:
        return np.zeros_like(obs_d, dtype=np.float64)
    t_green, t_peak = detect_cycle_landmarks(obs_d, ndvi, start_day, end_day)
    knots_x = np.array([float(start_day), t_green, t_peak, float(end_day)], dtype=np.float64)
    knots_y = np.array([0.0, float(canon_greenup), float(canon_peak), 1.0], dtype=np.float64)
    warped = np.interp(np.clip(obs_d, float(start_day), float(end_day)), knots_x, knots_y)
    return np.clip(warped, 0.0, 1.0)


def bin_by_gdd(
    obs_days: np.ndarray,
    values: np.ndarray,
    start_day: int,
    end_day: int,
    weather_days: np.ndarray,
    temp_c: np.ndarray,
    *,
    K: int = 36,
    t_base_c: float = 12.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Bin cycle observations ``(T_c, B)`` into ``K`` thermal-time GDD progress bins."""
    tau = gdd_progress(obs_days, start_day, end_day, weather_days, temp_c, t_base_c=t_base_c)
    return bin_by_progress(tau, values, K=K)


def bin_by_landmarks(
    obs_days: np.ndarray,
    values: np.ndarray,
    ndvi: np.ndarray,
    start_day: int,
    end_day: int,
    *,
    K: int = 36,
    canon_greenup: float = 0.20,
    canon_peak: float = 0.55,
) -> tuple[np.ndarray, np.ndarray]:
    """Bin cycle observations ``(T_c, B)`` into ``K`` landmark-registered progress bins."""
    tau = landmark_progress(
        obs_days,
        ndvi,
        start_day,
        end_day,
        canon_greenup=canon_greenup,
        canon_peak=canon_peak,
    )
    return bin_by_progress(tau, values, K=K)
