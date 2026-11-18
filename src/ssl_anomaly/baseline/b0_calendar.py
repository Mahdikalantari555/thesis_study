"""Baseline B0: Calendar day-of-year (DOY) robust modified z-score without cycle alignment.

Bins multi-band observations by calendar day-of-year into K bins across [1, 366],
fits the same two-tier empirical-Bayes shrunk median/MAD baseline as B1, and scores
each cycle over the calendar bins spanned by its observations. Isolates the value of
harvest-based cycle alignment (B1) versus raw calendar seasonality (B0).
"""

from __future__ import annotations

import numpy as np

from .robust import RobustBaseline, fit_baseline
from .score import (
    aggregate_band_scores,
    cycle_anomaly_burden,
    cycle_max_score,
    flag_runs,
    score_cycle,
)


def doy_from_datetime64(times: np.ndarray) -> np.ndarray:
    """Convert ``datetime64`` array to 1-based day-of-year in ``[1, 366]``."""
    days = times.astype("datetime64[D]")
    years = times.astype("datetime64[Y]").astype("datetime64[D]")
    return ((days - years).astype(np.int64) + 1).clip(1, 366)


def bin_by_calendar_doy(
    obs_times: np.ndarray,
    values: np.ndarray,
    K: int = 36,
    agg: str = "median",
    max_interp_adjacent: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    """Bin a ``(T, B)`` or ``(T,)`` series into ``K`` calendar DOY bins over ``[1, 366]``."""
    v = np.asarray(values, dtype=np.float64)
    squeeze = v.ndim == 1
    if squeeze:
        v = v[:, None]
    doy = doy_from_datetime64(np.asarray(obs_times))
    B = v.shape[1]
    binned = np.full((K, B), np.nan, dtype=np.float64)
    counts = np.zeros(K, dtype=np.int32)
    idx = np.clip(((doy - 1.0) / 366.0 * K).astype(int), 0, K - 1)
    for k in range(K):
        sel = idx == k
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


def fit_b0_calendar_baseline(
    X_doy_all: np.ndarray,
    field_ids: np.ndarray,
    *,
    min_n: int = 5,
    kappa: float = 2.5,
    floor_pct: float = 5.0,
    normal_mask: np.ndarray | None = None,
) -> RobustBaseline:
    """Fit B0 robust baseline on calendar-DOY-binned observations ``(N, K, B)``."""
    arr = np.asarray(X_doy_all, dtype=np.float64)
    fids = np.asarray(field_ids, dtype=np.int64)
    act = np.ones(len(arr), dtype=bool) if normal_mask is None else np.asarray(normal_mask, dtype=bool)
    X_active = {"all": arr[act]}
    X_by_field: dict[int, list[np.ndarray]] = {}
    for row, fid, is_act in zip(arr, fids, act):
        if is_act:
            X_by_field.setdefault(int(fid), []).append(row)
    X_by_field_arr = {fid: np.stack(rows, axis=0) for fid, rows in X_by_field.items() if rows}
    return fit_baseline(X_active, X_by_field_arr, min_n=min_n, kappa=kappa, floor_pct=floor_pct)


def score_b0_cycles(
    baseline: RobustBaseline,
    X_doy_all: np.ndarray,
    field_ids: np.ndarray,
    *,
    min_run_len: int = 2,
    z_thresh: float = 3.5,
) -> list[dict]:
    """Score calendar-DOY-binned cycle matrices ``(N, K, B)`` against B0 baseline."""
    results: list[dict] = []
    for X_c, fid in zip(X_doy_all, field_ids):
        z = score_cycle(X_c, baseline, stratum="all", field_id=int(fid))
        s = aggregate_band_scores(z)
        flag, runs = flag_runs(s, threshold=z_thresh, min_run_bins=min_run_len)
        results.append(
            {
                "z": z,
                "S": s,
                "max_score": cycle_max_score(s),
                "burden": cycle_anomaly_burden(z, threshold=z_thresh),
                "flag": flag,
                "runs": runs,
            }
        )
    return results
