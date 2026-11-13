"""Robust z-scoring, band aggregation, anomaly-run flagging."""

from __future__ import annotations

import numpy as np

from ..utils.arrays import contiguous_runs
from .robust import RobustBaseline, lookup_median_scale


def score_cycle(
    x: np.ndarray,
    baseline: RobustBaseline,
    stratum: str,
    *,
    field_id: int | None = None,
) -> np.ndarray:
    """Compute per-(bin, band) modified z-score for one cycle.

    x: (bins, bands). Returns z: (bins, bands).
    Applies shrinkage field offset if field_id is known.
    """
    med, scale = lookup_median_scale(baseline, stratum, x.shape)
    if field_id is not None and field_id in baseline.field_offset:
        med = med + baseline.field_offset[field_id]
    denom = np.maximum(scale, baseline.floor)
    with np.errstate(all="ignore"):
        z = (x - med) / denom
    return z


def score_cycle_loo(
    X_stratum: np.ndarray,  # (C, bins, bands)
    active: np.ndarray,  # (C,) bool
    index: int,
    baseline: RobustBaseline,
    stratum_for_cycle: str,
    floor: float,
    threshold: float = 3.5,
) -> np.ndarray:
    """Score one cycle leaving it out of the baseline (leave-one-out).

    Used during trimming so a cycle never scores against itself. We rebuild
    the baseline for this stratum with ``index`` excluded.
    """
    from .robust import _median_mad  # local import to avoid cycle

    keep = active.copy()
    keep[index] = False
    if keep.sum() < 2:
        # Fall back to non-LOO
        keep = active
    X_keep = X_stratum[keep]
    med, scale, _ = _median_mad(X_keep, min_n=1)
    denom = np.maximum(scale, floor)
    with np.errstate(all="ignore"):
        z = (X_stratum[index] - med) / denom
    return z


def aggregate_band_scores(z: np.ndarray, *, preserve_sign: bool = True) -> np.ndarray:
    """Aggregate per-band z-scores into a per-bin score S = sqrt(mean z_k^2).

    When preserve_sign is True (per spec), bins where a majority of high-|z|
    bands share a sign (e.g., NDVI negative + LST positive) get signed by
    the majority direction of NDVI-like (negative) or stress-like (positive)
    patterns. For simplicity we return the RMS magnitude here and expose
    per-band signs separately in scoring output.
    """
    finite = np.isfinite(z)
    sq = np.where(finite, z ** 2, 0.0)
    n = finite.sum(axis=-1)
    with np.errstate(invalid="ignore"):
        s = np.sqrt(np.sum(sq, axis=-1) / np.maximum(n, 1))
    s[n == 0] = np.nan
    return s


def flag_runs(
    s: np.ndarray,
    *,
    threshold: float = 3.5,
    min_run_bins: int = 2,
) -> tuple[np.ndarray, list[tuple[int, int]]]:
    """Flag contiguous bins where |S| > threshold for >= min_run_bins observed bins.

    Returns
    -------
    flag : np.ndarray[bool] (bins,)
    runs : list of (start, end) index pairs (end exclusive)
    """
    s = np.asarray(s, dtype=np.float64)
    obs = np.isfinite(s)
    hit = obs & (np.abs(s) > threshold)
    runs = contiguous_runs(hit, min_length=min_run_bins)
    flag = np.zeros_like(s, dtype=bool)
    for a, b in runs:
        flag[a:b] = True
    # Clear flags for bins that weren't observed
    flag &= obs
    return flag, runs


def cycle_anomaly_burden(z: np.ndarray, threshold: float = 3.5) -> float:
    """Fraction of observed (bin, band) pairs with |z| > threshold."""
    finite = np.isfinite(z)
    if finite.sum() == 0:
        return 0.0
    return float(np.mean(np.abs(z[finite]) > threshold))


def cycle_max_score(s: np.ndarray) -> float:
    return float(np.nanmax(np.abs(s))) if np.isfinite(s).any() else 0.0


def cusum_detector(
    s: np.ndarray,
    *,
    drift_k: float = 1.0,
    decision_h: float = 4.5,
) -> tuple[np.ndarray, np.ndarray]:
    """Page's tabular CUSUM along observed phase bins for gradual slow-drift detection.

    Accumulates ``C_t = max(0, C_{t-1} + |s_t| - drift_k)`` solely across finite
    observed bins so unobserved NaN bins neither accumulate nor reset the statistic.
    Returns ``(flag_bool, cusum_stat)`` of shape ``(bins,)``, where unobserved bins
    have ``flag_bool=False`` and ``cusum_stat=NaN``.
    """
    arr = np.asarray(s, dtype=np.float64)
    stat = np.full_like(arr, np.nan, dtype=np.float64)
    flag = np.zeros(arr.shape, dtype=bool)
    c_pos = 0.0
    for idx in range(arr.size):
        val = arr[idx]
        if not np.isfinite(val):
            continue
        c_pos = max(0.0, c_pos + abs(float(val)) - float(drift_k))
        stat[idx] = c_pos
        if c_pos > decision_h:
            flag[idx] = True
    return flag, stat


def ewma_detector(
    s: np.ndarray,
    *,
    alpha: float = 0.35,
    L_sigma: float = 2.8,
    baseline_mu: float = 1.0,
    baseline_sigma: float = 0.65,
) -> tuple[np.ndarray, np.ndarray]:
    """EWMA control-chart slow-drift detector over observed phase bins.

    Updates ``E_t = alpha * |s_t| + (1 - alpha) * E_{t-1}`` across observed bins and
    flags bins exceeding exact finite-step upper control limit
    ``mu + L_sigma * sigma * sqrt((alpha / (2 - alpha)) * (1 - (1 - alpha)**(2*m)))``.
    """
    arr = np.asarray(s, dtype=np.float64)
    ewma = np.full_like(arr, np.nan, dtype=np.float64)
    flag = np.zeros(arr.shape, dtype=bool)
    a = float(np.clip(alpha, 0.05, 0.95))
    e_val = float(baseline_mu)
    step_m = 0
    for idx in range(arr.size):
        val = arr[idx]
        if not np.isfinite(val):
            continue
        step_m += 1
        e_val = a * abs(float(val)) + (1.0 - a) * e_val
        ewma[idx] = e_val
        asymp = (a / (2.0 - a)) * (1.0 - (1.0 - a) ** (2 * step_m))
        ucl = float(baseline_mu) + float(L_sigma) * float(baseline_sigma) * float(np.sqrt(max(asymp, 1e-8)))
        if e_val > ucl:
            flag[idx] = True
    return flag, ewma


def score_all_cycles(
    X: dict[str, np.ndarray],
    cycle_info: dict[str, np.ndarray],
    baseline: RobustBaseline,
    *,
    field_offsets: dict[int, np.ndarray] | None = None,
    threshold: float = 3.5,
    min_run_bins: int = 2,
) -> dict[str, dict]:
    """Score all cycles. Returns dict with per-cycle arrays.

    cycle_info: for each stratum, a dict with keys:
        'field_ids': (C_s,) int
    """
    out = {"z": {}, "S": {}, "burden": {}, "max_score": {}, "runs": {}, "flags": {}}
    for key, arr in X.items():
        C = arr.shape[0]
        z_arr = np.full_like(arr, np.nan)
        S_arr = np.full(arr.shape[:2], np.nan, dtype=np.float64)
        bur = np.zeros(C, dtype=np.float64)
        mx = np.zeros(C, dtype=np.float64)
        flags = np.zeros(arr.shape[:2], dtype=bool)
        runs_list: list[list[tuple[int, int]]] = []
        fids = cycle_info[key]["field_ids"] if key in cycle_info else np.full(C, -1, dtype=np.int64)
        for i in range(C):
            fid = int(fids[i]) if i < len(fids) else -1
            z_i = score_cycle(arr[i], baseline, stratum=key, field_id=fid if fid > 0 else None)
            z_arr[i] = z_i
            s_i = aggregate_band_scores(z_i)
            S_arr[i] = s_i
            bur[i] = cycle_anomaly_burden(z_i, threshold=threshold)
            mx[i] = cycle_max_score(s_i)
            f, runs = flag_runs(s_i, threshold=threshold, min_run_bins=min_run_bins)
            flags[i] = f
            runs_list.append(runs)
        out["z"][key] = z_arr
        out["S"][key] = S_arr
        out["burden"][key] = bur
        out["max_score"][key] = mx
        out["flags"][key] = flags
        out["runs"][key] = runs_list
    return out
