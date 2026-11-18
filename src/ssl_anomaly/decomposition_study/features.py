"""Fixed input schema for the matched feature ablation."""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np

from ssl_anomaly.decomposition_study.decompose import Components

STAT_NAMES = ("median", "mad", "iqr", "q10", "q90", "slope", "lag1_autocorrelation")
ARMS = {
    "B1": ("raw",),
    "B2": ("trend",),
    "B3": ("seasonal",),
    "B4": ("residual",),
    "B5": ("trend", "seasonal", "residual"),
    "B6": ("raw", "residual"),
    "B7": ("raw", "trend", "seasonal", "residual"),
    "C1": ("raw", "global", "local"),
    "C2": ("trend", "seasonal", "residual", "global", "local", "residual_z"),
    "C3": ("raw", "trend", "seasonal", "residual", "global", "local", "residual_z"),
}
MAD_SCALE = 1.4826


def quantiles(x: np.ndarray, qs: tuple[float, ...]) -> np.ndarray:
    """Vectorized linear order statistics along time for (field, date, channel)."""
    if not x.shape[1]:
        return np.full((len(qs), x.shape[0], x.shape[2]), np.nan)
    count = np.isfinite(x).sum(axis=1, keepdims=True)
    ordered = np.sort(np.where(np.isfinite(x), x, np.nan), axis=1)
    out = []
    for q in qs:
        rank = q * np.maximum(0, count - 1)
        lo = rank.astype(int)
        hi = np.ceil(rank).astype(int)
        left = np.take_along_axis(ordered, lo, axis=1)
        right = np.take_along_axis(ordered, hi, axis=1)
        out.append((left + (right - left) * (rank - lo))[:, 0])
    return np.stack(out)


def masked_mean(a: np.ndarray, axis=None) -> np.ndarray:
    a = np.asarray(a)
    keep = np.isfinite(a)
    count = keep.sum(axis=axis)
    total = np.where(keep, a, 0).sum(axis=axis, dtype=np.float64)
    return np.divide(total, count, out=np.full(total.shape, np.nan), where=count > 0)


@dataclass(frozen=True)
class Normalizer:
    center: np.ndarray  # (field, 1, channel)
    scale: np.ndarray

    @classmethod
    def fit(cls, x: np.ndarray, train_end: int, *, floor: float = 1e-3) -> Normalizer:
        train = x[:, :train_end]
        # Entirely missing fields/channels stay missing, not silently centered at zero.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", "All-NaN slice encountered", RuntimeWarning)
            center = np.nanmedian(train, axis=1, keepdims=True)
            mad = np.nanmedian(np.abs(train - center), axis=1, keepdims=True)
        usable = np.isfinite(train).sum(axis=1, keepdims=True) >= 5
        return cls(
            np.where(usable, center, np.nan),
            np.where(usable, np.maximum(floor, MAD_SCALE * mad), np.nan),
        )

    def apply(self, x: np.ndarray) -> np.ndarray:
        return ((x - self.center) / self.scale).astype(np.float32)


def _slope(days: np.ndarray, x: np.ndarray) -> np.ndarray:
    seen = np.isfinite(x)
    d = days[None, :, None].astype(float)
    centered = d - masked_mean(np.where(seen, d, np.nan), axis=1)[:, None, :]
    y = x - masked_mean(x, axis=1)[:, None, :]
    top = np.nansum(centered * y, axis=1)
    bottom = np.where(seen, centered**2, 0).sum(axis=1)
    return np.divide(top, bottom, out=np.full_like(top, np.nan), where=bottom > 0)


def _lag1(days: np.ndarray, x: np.ndarray) -> np.ndarray:
    pair = np.isfinite(x[:, :-1]) & np.isfinite(x[:, 1:])
    pair &= np.diff(days)[None, :, None] <= 60
    left, right = np.where(pair, x[:, :-1], np.nan), np.where(pair, x[:, 1:], np.nan)
    left -= masked_mean(left, axis=1)[:, None, :]
    right -= masked_mean(right, axis=1)[:, None, :]
    numerator = np.nansum(left * right, axis=1)
    denominator = np.sqrt(np.nansum(left**2, axis=1) * np.nansum(right**2, axis=1))
    return np.divide(
        numerator,
        denominator,
        out=np.full_like(numerator, np.nan),
        where=(denominator > 0) & (pair.sum(axis=1) >= 3),
    )


def _summary(days: np.ndarray, x: np.ndarray) -> np.ndarray:
    q10, q25, median, q75, q90 = quantiles(x, (0.1, 0.25, 0.5, 0.75, 0.9))
    mad = quantiles(np.abs(x - median[:, None, :]), (0.5,))[0]
    summary = np.stack((median, mad, q75 - q25, q10, q90, _slope(days, x), _lag1(days, x)), axis=-1)
    summary[np.isfinite(x).sum(axis=1) < 3] = np.nan
    return summary.reshape(x.shape[0], -1).astype(np.float32)


def statistics(
    days: np.ndarray,
    raw: np.ndarray,
    train_end: int,
    *,
    local_days: int = 90,
    local_baseline: np.ndarray | None = None,
    changed_from: int = 0,
    global_baseline: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Expanding past-only global summaries, and earlier observations in day windows."""
    shape = (*raw.shape[:2], raw.shape[2] * len(STAT_NAMES))
    history = np.empty(shape, dtype=np.float32) if global_baseline is None else global_baseline
    local = np.empty(shape, dtype=np.float32) if local_baseline is None else local_baseline.copy()
    if global_baseline is None:
        for t in range(train_end):
            history[:, t] = _summary(days[:t], raw[:, :t])
        history[:, train_end:] = _summary(days[:train_end], raw[:, :train_end])[:, None]
    starts = np.searchsorted(days, days - local_days)
    for t in range(changed_from, len(days)):
        s = starts[t]
        local[:, t] = _summary(days[s:t], raw[:, s:t])
    return history, local


def residual_local_z(
    days: np.ndarray, residual: np.ndarray, *, start: int = 0, baseline: np.ndarray | None = None
) -> np.ndarray:
    """Signed residual z-score against earlier residuals in a 90-day window."""
    result = np.full_like(residual, np.nan) if baseline is None else baseline.copy()
    starts = np.searchsorted(days, days - 90)
    for t in range(start, len(days)):
        prior = residual[:, starts[t] : t]
        median = quantiles(prior, (0.5,))[0]
        mad = quantiles(np.abs(prior - median[:, None]), (0.5,))[0]
        z = (residual[:, t] - median) / np.maximum(MAD_SCALE * mad, 1e-3)
        result[:, t] = np.where(np.isfinite(prior).sum(axis=1) >= 3, z, np.nan)
    return result


def feature_groups(
    raw: np.ndarray, comp: Components, stats: tuple[np.ndarray, np.ndarray], residual_z: np.ndarray
) -> dict:
    return {
        "raw": raw,
        "trend": comp.trend,
        "seasonal": comp.seasonal,
        "residual": comp.residual,
        "global": stats[0],
        "local": stats[1],
        "residual_z": residual_z,
    }


def fit_feature_norms(groups: dict[str, np.ndarray], train_end: int) -> dict[str, Normalizer]:
    return {
        k: Normalizer.fit(v, train_end, floor=1e-6 if k in ("local", "global") else 1e-3)
        for k, v in groups.items()
    }


def feature_tokens(groups: dict[str, np.ndarray], norms: dict[str, Normalizer]) -> np.ndarray:
    # residual_z and residual have different slots so C1 never sees a decomposition statistic.
    ordered = [norms[k].apply(v) for k, v in groups.items()]
    return np.concatenate(ordered, axis=-1)


def arm_slots(arm: str, groups: dict[str, np.ndarray]) -> np.ndarray:
    return np.concatenate(
        [np.full(v.shape[-1], k in ARMS[arm], dtype=bool) for k, v in groups.items()]
    )
