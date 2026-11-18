"""Small array helpers used across the codebase (NaN-safe ops, MAD constants, etc.)."""

from __future__ import annotations

import numpy as np

MAD_K = 1.4826  # 1 / Phi^{-1}(3/4) — MAD consistency constant for normal distribution


def mad(x: np.ndarray, axis: int | None = None, keepdims: bool = False) -> np.ndarray:
    """Median absolute deviation from the median, scaled for normal consistency."""
    med = np.nanmedian(x, axis=axis, keepdims=True)
    m = np.nanmedian(np.abs(x - med), axis=axis, keepdims=keepdims)
    return m * MAD_K


def mad_scale(x: np.ndarray, axis: int = 0, floor_pct: float = 5.0) -> tuple[np.ndarray, np.ndarray, float]:
    """Return (median, mad_scale, floor) where floor is a low percentile of scales.

    Used across baseline scoring and SSL residual scaling to avoid divide-by-zero
    on near-constant bands/bins.
    """
    med = np.nanmedian(x, axis=axis)
    scale = np.nanmedian(np.abs(x - np.expand_dims(med, axis=axis)), axis=axis) * MAD_K
    finite_scales = scale[np.isfinite(scale) & (scale > 0)]
    floor = float(np.percentile(finite_scales, floor_pct)) if finite_scales.size else 1e-6
    return med, scale, floor


def robust_standardize(
    x: np.ndarray, med: np.ndarray, scale: np.ndarray, floor: float
) -> np.ndarray:
    """Robust z-score with scale floor to avoid division by zero."""
    return (x - med) / np.maximum(scale, floor)


def hampel_filter(
    t: np.ndarray, y: np.ndarray, window: int = 5, n_sigma: float = 3.0
) -> np.ndarray:
    """Return a boolean mask of Hampel outlier points (True = outlier).

    Operates on a 1-D series; uses a centered window of ``window`` observations
    to estimate local median/MAD and flags points exceeding ``n_sigma``.
    """
    n = len(y)
    outlier = np.zeros(n, dtype=bool)
    half = window // 2
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        local = y[lo:hi]
        if local.size < 3:
            continue
        m = np.nanmedian(local)
        s = np.nanmedian(np.abs(local - m)) * MAD_K
        if s <= 0:
            continue
        if np.isfinite(y[i]) and np.abs(y[i] - m) > n_sigma * s:
            outlier[i] = True
    return outlier


def contiguous_runs(mask: np.ndarray, min_length: int = 2) -> list[tuple[int, int]]:
    """Return (start, end) index pairs of contiguous True runs of length >= min_length.

    End index is exclusive (Python slicing convention). NaN gaps in *mask* are
    treated as False and break runs.
    """
    m = np.asarray(mask, dtype=bool).copy()
    m[~np.isfinite(mask) if mask.dtype.kind == "f" else np.zeros_like(m, dtype=bool)] = False
    runs: list[tuple[int, int]] = []
    start = None
    for i, v in enumerate(m.tolist() + [False]):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start >= min_length:
                runs.append((start, i))
            start = None
    return runs
