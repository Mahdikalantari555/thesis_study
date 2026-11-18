"""Per-field STL and irregular harmonic regression with explicit fit boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

import numpy as np
from statsmodels.tsa.seasonal import STL

from ssl_anomaly.decomposition_study.data import Split

METHODS = ("stl", "robust_stl", "harmonic")
PROTOCOLS = ("causal", "retrospective")
GRID_DAYS = 15
PERIOD = 24
MAX_GAP_BINS = 3
REFRESH_DAYS = 60
MAX_CAUSAL_AGE_DAYS = 105
YEAR = 365.2425


@dataclass
class Components:
    trend: np.ndarray
    seasonal: np.ndarray
    residual: np.ndarray
    fit_before: np.ndarray  # exclusive input day cutoff for each requested date
    grid_states: np.ndarray  # (fit, field, bin, channel); 0 absent / 1 acquired / 2 filled
    grid_fit_before: np.ndarray


def regular_grid(
    days: np.ndarray,
    values: np.ndarray,
    n_bins: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Median within bins; interpolate only short, bounded runs of missing bins."""
    seen = np.isfinite(values)
    bins, y = days[seen] // GRID_DAYS, values[seen]
    grid = np.full(n_bins, np.nan)
    anchors, start, count = np.unique(bins, return_index=True, return_counts=True)
    grid[anchors] = y[start]
    for i in np.flatnonzero(count > 1):
        grid[anchors[i]] = np.median(y[start[i] : start[i] + count[i]])
    state = np.zeros(n_bins, dtype=np.uint8)
    state[anchors] = 1
    for left, right in pairwise(anchors):
        if 1 < right - left <= MAX_GAP_BINS + 1:
            ix = np.arange(left + 1, right)
            grid[ix] = np.interp(ix, [left, right], grid[[left, right]])
            state[ix] = 2
    return grid, state


def _stl(
    days: np.ndarray,
    y: np.ndarray,
    query: np.ndarray,
    *,
    n_bins: int,
    causal: bool,
    robust: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    grid, state = regular_grid(days, y, n_bins)
    trend = np.full(len(query), np.nan)
    seasonal = trend.copy()
    # A finite segment never crosses an unsupported long gap.
    edges = np.flatnonzero(np.diff(np.r_[False, state > 0, False]))
    spans = [
        (a, b)
        for a, b in zip(edges[::2], edges[1::2])
        if b - a >= 2 * PERIOD and np.count_nonzero(state[a:b] == 1) >= PERIOD
    ]
    if causal:
        spans = spans[-1:]
    q = query // GRID_DAYS
    for a, b in spans:
        if causal:
            # Age measured from final *actual input acquisition*, not end of its bin.
            end_days = days[(days // GRID_DAYS == b - 1) & np.isfinite(y)]
            take = (q >= b - 1) & (query - end_days[-1] <= MAX_CAUSAL_AGE_DAYS)
        else:
            take = (q >= a) & (q < b)
        if not take.any():
            continue
        model = STL(
            grid[a:b],
            period=PERIOD,
            seasonal=13,
            trend=47,
            robust=robust,
            seasonal_jump=3,
            trend_jump=5,
            low_pass_jump=3,
        )
        result = model.fit(inner_iter=2 if robust else 5, outer_iter=5 if robust else 0)
        if causal:
            slope = np.diff(result.trend[-4:]).mean()
            trend[take] = result.trend[-1] + slope * (q[take] - (b - 1))
            seasonal[take] = result.seasonal[-PERIOD:][(q[take] - b) % PERIOD]
        else:
            trend[take], seasonal[take] = result.trend[q[take] - a], result.seasonal[q[take] - a]
    return trend, seasonal, state


def _harmonic_design(days: np.ndarray, center: float) -> np.ndarray:
    phase = 2 * np.pi * days / YEAR
    return np.column_stack(
        (
            np.ones(len(days)),
            (days - center) / YEAR,
            np.sin(phase),
            np.cos(phase),
            np.sin(2 * phase),
            np.cos(2 * phase),
        )
    )


def _harmonic(days: np.ndarray, y: np.ndarray, query: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ok = np.isfinite(y)
    d, v = days[ok], y[ok]
    null = np.full(len(query), np.nan)
    if d.size < 18 or d[-1] - d[0] < 1.5 * YEAR:
        return null, null.copy()
    center = float(d.mean())
    basis = _harmonic_design(d, center)
    coef, _, rank, singular = np.linalg.lstsq(basis, v, rcond=None)
    if rank != basis.shape[1] or singular[-1] < 0.02 * singular[0]:
        return null, null.copy()
    design = _harmonic_design(query, center)
    return design[:, :2] @ coef[:2], design[:, 2:] @ coef[2:]


def _fit_windows(days: np.ndarray, split: Split, protocol: str):
    if protocol == "causal":
        groups = days // REFRESH_DAYS
        for group in np.unique(groups):
            cutoff = int(group * REFRESH_DAYS)
            begin = max(0, cutoff - 4 * PERIOD * GRID_DAYS)
            yield np.flatnonzero(groups == group), begin, cutoff
    else:
        for block in split.blocks:
            yield np.arange(block.start, block.stop), 0, int(days[block.stop - 1] + 1)


def decompose(
    days: np.ndarray,
    x: np.ndarray,
    split: Split,
    method: str,
    protocol: str,
    *,
    baseline: Components | None = None,
    capture_grid: bool = True,
) -> Components:
    """Fit each field/channel independently. Baseline reuse is for eval-only changes."""
    if method not in METHODS or protocol not in PROTOCOLS:
        raise ValueError(f"Unknown method or protocol: {method}/{protocol}")
    trend = np.full_like(x, np.nan)
    seasonal = np.full_like(x, np.nan)
    limits = np.empty(len(days), dtype=int)
    grid_masks, grid_limits = [], []
    n_bins = int(days[-1] // GRID_DAYS) + 1
    for target, begin, cutoff in _fit_windows(days, split, protocol):
        limits[target] = cutoff
        if baseline is not None:
            before = target[target < split.cal_end]
            trend[:, before], seasonal[:, before] = (
                baseline.trend[:, before],
                baseline.seasonal[:, before],
            )
            target = target[target >= split.cal_end]
            if not target.size:
                continue
        lo, hi = np.searchsorted(days, (begin, cutoff))
        fit_days, query = days[lo:hi], days[target]
        save = capture_grid and method != "harmonic"
        if save:
            grids = np.zeros((x.shape[0], n_bins, x.shape[2]), dtype=np.uint8)
        for f in range(x.shape[0]):
            for c in range(x.shape[2]):
                y = x[f, lo:hi, c]
                if method == "harmonic":
                    t, s = _harmonic(fit_days, y, query)
                    if protocol == "causal" and np.isfinite(y).any():
                        stale = query - fit_days[np.isfinite(y)][-1] > MAX_CAUSAL_AGE_DAYS
                        t[stale], s[stale] = np.nan, np.nan
                else:
                    t, s, state = _stl(
                        fit_days,
                        y,
                        query,
                        n_bins=n_bins,
                        causal=protocol == "causal",
                        robust=method == "robust_stl",
                    )
                    if save:
                        grids[f, :, c] = state
                # Components at unobserved dates aren't model targets or measurements.
                seen = np.isfinite(x[f, target, c])
                trend[f, target, c] = np.where(seen, t, np.nan)
                seasonal[f, target, c] = np.where(seen, s, np.nan)
        if save:
            grid_masks.append(grids)
            grid_limits.append(cutoff)
    return Components(
        trend,
        seasonal,
        x - trend - seasonal,
        limits,
        np.stack(grid_masks) if grid_masks else np.empty(0, dtype=np.uint8),
        np.asarray(grid_limits, dtype=int),
    )
