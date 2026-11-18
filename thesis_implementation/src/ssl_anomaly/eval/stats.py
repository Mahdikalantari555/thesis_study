"""Statistical utilities: bootstrap CI, Wilcoxon signed-rank, Holm, Spearman."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from scipy import stats


def spearman_correlation(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Spearman rank correlation + p-value, handling NaN pairwise."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 3:
        return (np.nan, np.nan)
    res = stats.spearmanr(x[mask], y[mask])
    return float(res.statistic), float(res.pvalue)


def bootstrap_ci(
    metric_fn,
    *arrays: np.ndarray,
    n_boot: int = 1000,
    alpha: float = 0.05,
    seed: int = 0,
    cluster_by: np.ndarray | None = None,
) -> tuple[float, float, float]:
    """Cluster bootstrap CI for a metric (default: IID over samples; if cluster_by
    is given, resample clusters to respect field-level dependence).

    Returns (point_estimate, ci_low, ci_high).
    """
    rng = np.random.default_rng(seed)
    arrays = [np.asarray(a) for a in arrays]
    n = len(arrays[0])
    point = float(metric_fn(*arrays))
    if cluster_by is not None:
        clusters = np.unique(cluster_by)
        cluster_idx = {c: np.where(cluster_by == c)[0] for c in clusters}
        samples = []
        for _ in range(n_boot):
            chosen = rng.choice(clusters, size=clusters.size, replace=True)
            idx = np.concatenate([cluster_idx[c] for c in chosen])
            try:
                samples.append(metric_fn(*[a[idx] for a in arrays]))
            except Exception:
                continue
    else:
        samples = []
        for _ in range(n_boot):
            idx = rng.integers(0, n, size=n)
            try:
                samples.append(metric_fn(*[a[idx] for a in arrays]))
            except Exception:
                continue
    if not samples:
        return point, point, point
    lo = float(np.nanpercentile(samples, 100 * alpha / 2))
    hi = float(np.nanpercentile(samples, 100 * (1 - alpha / 2)))
    return point, lo, hi


def paired_wilcoxon(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    """Paired Wilcoxon signed-rank test (two-sided). Returns (statistic, p_value)."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    mask = np.isfinite(a) & np.isfinite(b)
    if mask.sum() < 5:
        return (np.nan, np.nan)
    res = stats.wilcoxon(a[mask], b[mask], alternative="two-sided")
    return float(res.statistic), float(res.pvalue)


def holm_correction(p_values: Sequence[float]) -> np.ndarray:
    """Holm-Bonferroni multiple-comparison correction. Returns adjusted p-values."""
    p = np.asarray(p_values, dtype=np.float64)
    n = p.size
    order = np.argsort(p)
    adjusted = np.empty(n, dtype=np.float64)
    prev = 0.0
    for i, idx in enumerate(order):
        val = p[idx] * (n - i)
        val = max(val, prev)
        val = min(val, 1.0)
        adjusted[idx] = val
        prev = val
    return adjusted
