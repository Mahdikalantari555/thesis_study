"""Robust field-local anomaly scores, without a dependency on the network."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ssl_anomaly.decomposition_study.decompose import YEAR, Components
from ssl_anomaly.decomposition_study.features import (
    MAD_SCALE,
    Normalizer,
    _slope,
    masked_mean,
    quantiles,
)

REFERENCES = ("annual", "inferred_phase")
WEIGHTS = {"equal": (0.25,) * 4} | {
    f"emphasize_D{i + 1}": tuple(0.5 if j == i else 1 / 6 for j in range(4)) for i in range(4)
}


def reference_groups(
    days: np.ndarray, greenness: np.ndarray, train_end: int
) -> dict[str, np.ndarray]:
    annual = np.floor(days % YEAR * 12 / YEAR).astype(np.int8)
    annual = np.broadcast_to(annual, greenness.shape)
    estimated = np.full(greenness.shape, -1, dtype=np.int8)
    train = greenness[:, :train_end]
    low, high = quantiles(train[..., None], (0.25, 0.75))[..., 0]
    qualified = (np.isfinite(train).sum(axis=1) >= 10) & ((high - low) > 0.05)
    for f in np.flatnonzero(qualified):
        seen = np.flatnonzero(np.isfinite(greenness[f]))
        for t, day in enumerate(days):
            n = np.searchsorted(seen, t)
            previous = seen[max(n - 3, 0) : n]
            if previous.size < 3 or day - days[previous[0]] > 90:
                continue
            a, b = previous[[0, -1]]
            last = greenness[f, b]
            if last <= low[f]:
                estimated[f, t] = 0
            elif last >= high[f]:
                estimated[f, t] = 2
            elif greenness[f, b] > greenness[f, a]:
                estimated[f, t] = 1
            elif greenness[f, b] < greenness[f, a]:
                estimated[f, t] = 3
    return {"annual": annual, "inferred_phase": estimated}


def trend_drift(days: np.ndarray, trend: np.ndarray, train_end: int) -> np.ndarray:
    """Remove persistent drift relative to a line fitted only in training."""
    fit = trend[:, :train_end]
    slope = _slope(days[:train_end], fit)
    center = masked_mean(np.where(np.isfinite(fit), days[None, :train_end, None], np.nan), axis=1)
    level = masked_mean(fit, axis=1)
    return (level[:, None] + slope[:, None] * (days[None, :, None] - center[:, None])).astype(
        np.float32
    )


def score_inputs(raw: np.ndarray, comp: Components, drift: np.ndarray) -> dict[str, np.ndarray]:
    return {"raw": raw, "D2": comp.residual, "D3": comp.trend - drift, "D4": comp.seasonal}


@dataclass(frozen=True)
class HistoricalBank:
    center: np.ndarray  # field x matched group x channel
    scale: np.ndarray

    @classmethod
    def fit(cls, x: np.ndarray, reference: np.ndarray, train_end: int, kind: str) -> HistoricalBank:
        train, g = x[:, :train_end], reference[:, :train_end]
        centers, scales = [], []
        for i in range(12 if kind == "annual" else 4):
            if kind == "annual":
                match = ((g - i + 1) % 12) <= 2  # adjacent bins incl. wraparound
            else:
                match = g == i
            stat = Normalizer.fit(np.where(match[..., None], train, np.nan), train_end)
            centers.append(stat.center[:, 0])
            scales.append(stat.scale[:, 0])
        return cls(np.stack(centers, axis=1), np.stack(scales, axis=1))

    def score(self, x: np.ndarray, reference: np.ndarray, target_mask: np.ndarray) -> np.ndarray:
        f = np.arange(len(x))[:, None]
        z = (x - self.center[f, reference]) / self.scale[f, reference]
        # Compare the same active channels as D1, or record an absent score.
        known = (reference >= 0) & (~target_mask | np.isfinite(z)).all(axis=-1)
        z = np.where(known[..., None] & target_mask, z, np.nan)
        return np.sqrt(masked_mean(z**2, axis=-1))


def fit_banks(inputs: dict, groups: dict, train_end: int) -> dict:
    return {
        (name, ref): HistoricalBank.fit(x, groups[ref], train_end, ref)
        for name, x in inputs.items()
        for ref in REFERENCES
    }


def component_scores(inputs: dict, groups: dict, target_mask: np.ndarray, banks: dict) -> dict:
    return {
        f"{name if name != 'raw' else ('B0' if ref == 'annual' else 'phase_reference')}_{ref}": bank.score(
            inputs[name], groups[ref], target_mask
        )
        for (name, ref), bank in banks.items()
    }


def finite_vector(values: np.ndarray) -> np.ndarray:
    return values[np.isfinite(values)]


@dataclass(frozen=True)
class HybridCalibration:
    center: tuple[float, ...]
    scale: tuple[float, ...]

    @classmethod
    def fit(cls, scores: list[np.ndarray], block: slice) -> HybridCalibration | None:
        joint = np.stack([s[:, block] for s in scores], axis=-1)
        joint = joint[np.isfinite(joint).all(axis=-1)]
        if len(joint) < 5:
            return None
        med = np.median(joint, axis=0)
        mad = np.median(np.abs(joint - med), axis=0)
        return cls(tuple(map(float, med)), tuple(map(float, np.maximum(1e-3, MAD_SCALE * mad))))

    def apply(self, scores: list[np.ndarray]) -> dict[str, np.ndarray]:
        joint = np.stack(scores, axis=-1)
        norm = np.maximum(0, (joint - self.center) / self.scale)
        return {name: norm @ np.asarray(weights) for name, weights in WEIGHTS.items()}


def alarm_threshold(scores: np.ndarray, block: slice) -> float | None:
    v = finite_vector(scores[:, block])
    return float(np.quantile(v, 0.95, method="higher")) if len(v) >= 5 else None


def maxima(x: np.ndarray, axis: int) -> np.ndarray:
    have = np.isfinite(x)
    return np.where(have.any(axis=axis), np.max(np.where(have, x, -np.inf), axis=axis), np.nan)
