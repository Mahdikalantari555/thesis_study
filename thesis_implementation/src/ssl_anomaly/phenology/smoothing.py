"""Weighted Whittaker-Eilers smoothing for irregular time series.

Reference: Eilers, P.H.C. (2003). "A perfect smoother." Anal. Chem. 75(14), 3631-3636.
"""

from __future__ import annotations

import logging

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

log = logging.getLogger("ssl_anomaly.phenology.smoothing")


def whittaker_smooth(
    y: np.ndarray,
    w: np.ndarray | None = None,
    lam: float = 10.0,
    d: int = 2,
) -> np.ndarray:
    """Whittaker-Eilers smoother.

    Parameters
    ----------
    y:
        1-D signal (regular grid). NaNs are treated as missing (w=0).
    w:
        Optional per-point weights (0 = missing). Length matches y.
    lam:
        Smoothing penalty; larger → smoother.
    d:
        Order of the difference penalty (2 = common default).
    """
    y = np.asarray(y, dtype=np.float64)
    n = y.size
    if n == 0:
        return y.copy()

    if w is None:
        w = np.ones(n, dtype=np.float64)
        w[~np.isfinite(y)] = 0.0
    else:
        w = np.asarray(w, dtype=np.float64)
        w = np.where(np.isfinite(y), w, 0.0)

    y_filled = np.where(np.isfinite(y), y, 0.0)

    # Build d-th order difference matrix
    D = sparse.eye(n, format="csr", dtype=np.float64)
    for _ in range(d):
        D = D[1:, :] - D[:-1, :]

    W = sparse.diags(w, format="csr", dtype=np.float64)
    A = (W + lam * (D.T @ D)).tocsc()
    z = spsolve(A, w * y_filled)
    return z


def to_daily_grid(
    t_days: np.ndarray,
    y: np.ndarray,
    quality: np.ndarray | None = None,
    lam: float = 10.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Place irregular observations onto a daily grid and smooth.

    Parameters
    ----------
    t_days:
        1-D integer day indices (e.g., days since epoch).
    y:
        Observed values at those times.
    quality:
        Optional weights (e.g., valid_frac). Defaults to ones for finite obs.
    lam:
        Smoothing parameter.

    Returns
    -------
    grid:
        Daily day indices (int64), shape (T,) covering [min, max] of t_days.
    smoothed:
        Smoothed daily values, shape (T,).
    """
    t_days = np.asarray(t_days, dtype=np.int64)
    y = np.asarray(y, dtype=np.float64)
    order = np.argsort(t_days)
    t_days, y = t_days[order], y[order]

    if quality is not None:
        quality = np.asarray(quality, dtype=np.float64)[order]
    else:
        quality = np.ones_like(y)
    quality = quality * np.isfinite(y)

    t0 = int(t_days.min())
    t1 = int(t_days.max())
    grid = np.arange(t0, t1 + 1, dtype=np.int64)
    yy = np.zeros(grid.size, dtype=np.float64)
    ww = np.zeros(grid.size, dtype=np.float64)
    idx = (t_days - t0).astype(np.int64)
    # Average duplicates (e.g., two overpasses same day)
    np.add.at(yy, idx, y * quality)
    np.add.at(ww, idx, quality)
    valid = ww > 0
    yy[valid] /= ww[valid]
    yy[~valid] = 0.0  # filled before solve
    smoothed = whittaker_smooth(yy, w=ww, lam=lam)
    return grid, smoothed


def whittaker_tune_lambda(
    t_days: np.ndarray,
    y: np.ndarray,
    quality: np.ndarray | None = None,
    candidates: np.ndarray | None = None,
    cv_folds: int = 5,
    seed: int = 0,
) -> tuple[float, dict]:
    """Choose lambda by leave-out cross-validation on a daily grid.

    We randomly hold out 20% of the *observed* days, smooth on the rest with
    each candidate lambda, and pick the lambda with lowest weighted RMSE on
    held-out days. Returns (best_lambda, diagnostics).
    """
    rng = np.random.default_rng(seed)
    t_days = np.asarray(t_days, dtype=np.int64)
    y = np.asarray(y, dtype=np.float64)
    if candidates is None:
        candidates = np.logspace(1, 6, 12)

    # Project to daily grid first for consistent holdout
    t0 = int(t_days.min())
    t1 = int(t_days.max())
    grid = np.arange(t0, t1 + 1, dtype=np.int64)
    ww = np.zeros(grid.size, dtype=np.float64)
    yy = np.zeros(grid.size, dtype=np.float64)
    if quality is None:
        quality = np.ones_like(y)
    order = np.argsort(t_days)
    t_days, y, quality = t_days[order], y[order], quality[order]
    idx = (t_days - t0).astype(np.int64)
    np.add.at(yy, idx, y * quality)
    np.add.at(ww, idx, quality)
    valid = ww > 0
    yy[valid] /= ww[valid]
    obs_idx = np.where(valid)[0]
    if obs_idx.size < cv_folds * 2:
        log.debug("Too few points to tune lambda; using default 100")
        return 100.0, {"grid_mse": {}, "best_idx": 0}

    rng.shuffle(obs_idx)
    folds = np.array_split(obs_idx, cv_folds)
    scores: dict[float, float] = {}
    for lam in candidates:
        errs = []
        for k in range(cv_folds):
            held = folds[k]
            w_train = ww.copy()
            w_train[held] = 0.0
            yy_in = yy.copy()
            yy_in[held] = 0.0
            z = whittaker_smooth(yy_in, w=w_train, lam=float(lam))
            err = np.nanmean((yy[held] - z[held]) ** 2)
            errs.append(err)
        scores[float(lam)] = float(np.mean(errs))
    best = float(min(scores, key=scores.get))  # type: ignore[arg-type]
    return best, {"grid_mse": scores, "best_idx": int(np.argmin(list(scores.values())))}


def savitzky_golay_8day(
    t_days: np.ndarray,
    y: np.ndarray,
    *,
    step_days: int = 8,
    window_length: int = 7,
    polyorder: int = 2,
) -> tuple[np.ndarray, np.ndarray]:
    """Sprint-0 regular-grid comparator: interpolate onto an 8-day grid + Savitzky-Golay filter.

    Included per ``docs/final_plan.md`` §4.2.2 as a baseline smoothing comparator against
    weighted daily Whittaker-Eilers smoothing on irregular cloud-gapped Landsat series.
    """
    from scipy.signal import savgol_filter

    t_arr = np.asarray(t_days, dtype=np.int64)
    y_arr = np.asarray(y, dtype=np.float64)
    fin = np.isfinite(t_arr) & np.isfinite(y_arr)
    if int(fin.sum()) < 2:
        return t_arr.copy(), np.nan_to_num(y_arr, nan=0.0)

    t_fin = t_arr[fin]
    y_fin = y_arr[fin]
    order = np.argsort(t_fin)
    t_fin, y_fin = t_fin[order], y_fin[order]

    grid = np.arange(int(t_fin[0]), int(t_fin[-1]) + 1, int(step_days), dtype=np.int64)
    y_interp = np.interp(grid.astype(np.float64), t_fin.astype(np.float64), y_fin)
    if grid.size < 3:
        return grid, y_interp

    win = min(int(window_length), int(grid.size))
    if win % 2 == 0:
        win = max(3, win - 1)
    if win > grid.size:
        return grid, y_interp
    poly = min(int(polyorder), win - 1)
    smoothed = savgol_filter(y_interp, window_length=win, polyorder=poly, mode="interp")
    return grid, np.asarray(smoothed, dtype=np.float64)
