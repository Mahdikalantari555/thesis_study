"""Baseline B3: Tabular outlier detectors (IsolationForest & ECOD) on per-cycle summary features.

Extracts fixed-length per-cycle phenological & spectral summary features from
``(K, B)`` cycle trajectories and scores cycles using:
  - ``IsolationForestDetector`` (scikit-learn IsolationForest)
  - ``ECODDetector`` (Empirical Cumulative-distribution-based Outlier Detection,
    Li et al., IEEE TKDE 2022)
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
from scipy.stats import skew
from sklearn.ensemble import IsolationForest


def extract_cycle_features(
    X_all: np.ndarray,
    durations: np.ndarray | None = None,
    *,
    red_idx: int | None = 2,
    nir_idx: int | None = 3,
) -> np.ndarray:
    """Extract deterministic tabular summary features ``(N, D_feat)`` from ``(N, K, B)`` cycles.

    For each band ``b``, computes:
      - overall mean, std, min, max, amplitude (P90 - P10)
      - early-stage mean (first third), peak-stage mean (middle third), late-stage mean (last third)
      - green-up delta (peak - early) and senescence delta (late - peak)
    Plus NDVI summary statistics (when ``red_idx`` & ``nir_idx`` are valid), valid-bin
    coverage fraction, and optional cycle duration.
    """
    X = np.asarray(X_all, dtype=np.float64)
    if X.ndim != 3:
        raise ValueError(f"Expected 3-D (N, K, B) array, got shape {X.shape}")
    N, K, B = X.shape
    k1 = max(1, K // 3)
    k2 = max(k1 + 1, (2 * K) // 3)

    with warnings.catch_warnings(), np.errstate(all="ignore"):
        warnings.simplefilter("ignore", category=RuntimeWarning)
        mean_v = np.nanmean(X, axis=1)  # (N, B)
        std_v = np.nanstd(X, axis=1)
        min_v = np.nanmin(X, axis=1)
        max_v = np.nanmax(X, axis=1)
        p10, p90 = np.nanpercentile(X, [10, 90], axis=1)
        amp_v = p90 - p10
        e_m = np.nanmean(X[:, :k1, :], axis=1)
        p_m = np.nanmean(X[:, k1:k2, :], axis=1)
        l_m = np.nanmean(X[:, k2:, :], axis=1)

    e_m = np.where(np.isfinite(e_m), e_m, mean_v)
    p_m = np.where(np.isfinite(p_m), p_m, mean_v)
    l_m = np.where(np.isfinite(l_m), l_m, mean_v)
    slope1 = p_m - e_m
    slope2 = l_m - p_m

    # Interleave 10 features per band -> shape (N, B * 10)
    band_block = np.stack(
        [mean_v, std_v, min_v, max_v, amp_v, e_m, p_m, l_m, slope1, slope2], axis=-1
    ).reshape(N, B * 10)

    cols = [band_block]
    if red_idx is not None and nir_idx is not None and red_idx < B and nir_idx < B:
        red = X[:, :, red_idx]
        nir = X[:, :, nir_idx]
        denom = nir + red
        with warnings.catch_warnings(), np.errstate(all="ignore"):
            warnings.simplefilter("ignore", category=RuntimeWarning)
            ndvi = np.where(np.isfinite(denom) & (denom > 0), (nir - red) / np.where(denom > 0, denom, 1.0), np.nan)
            nd_mean = np.nanmean(ndvi, axis=1)
            nd_max = np.nanmax(ndvi, axis=1)
            nd_min = np.nanmin(ndvi, axis=1)
        cols.append(np.column_stack([nd_mean, nd_max, nd_min, nd_max - nd_min]))

    valid_frac = np.any(np.isfinite(X), axis=2).mean(axis=1)[:, None]
    cols.append(valid_frac)
    if durations is not None:
        cols.append(np.asarray(durations, dtype=np.float64)[:, None])

    return np.hstack(cols)


@dataclass
class _FeaturePreprocessor:
    medians: np.ndarray
    scales: np.ndarray

    @classmethod
    def fit(cls, F: np.ndarray) -> _FeaturePreprocessor:
        with np.errstate(all="ignore"):
            med = np.nanmedian(F, axis=0)
            mad = np.nanmedian(np.abs(F - med[None, :]), axis=0) * 1.4826
        med = np.where(np.isfinite(med), med, 0.0)
        scales = np.where(np.isfinite(mad) & (mad > 1e-6), mad, 1.0)
        return cls(medians=med, scales=scales)

    def transform(self, F: np.ndarray) -> np.ndarray:
        F_imp = np.where(np.isfinite(F), F, self.medians[None, :])
        return (F_imp - self.medians[None, :]) / self.scales[None, :]


class IsolationForestDetector:
    """Per-cycle IsolationForest anomaly scorer."""

    def __init__(self, n_estimators: int = 200, contamination: str | float = "auto", seed: int = 42) -> None:
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.seed = seed
        self._prep: _FeaturePreprocessor | None = None
        self._clf: IsolationForest | None = None

    def fit(self, F_train: np.ndarray) -> IsolationForestDetector:
        self._prep = _FeaturePreprocessor.fit(F_train)
        Z = self._prep.transform(F_train)
        self._clf = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=self.seed,
            n_jobs=1,
        )
        self._clf.fit(Z)
        return self

    def score_samples(self, F: np.ndarray) -> np.ndarray:
        if self._prep is None or self._clf is None:
            raise RuntimeError("IsolationForestDetector must be fit before scoring")
        Z = self._prep.transform(F)
        # decision_function is higher for inliers -> negate so higher = more anomalous
        return -np.asarray(self._clf.score_samples(Z), dtype=np.float64)


class ECODDetector:
    """Empirical Cumulative-distribution-based Outlier Detection (Li et al., TKDE 2022).

    Parameter-free, deterministic univariate tail-probability outlier detector:
    for each feature ``j``, computes empirical left-tail ``F_left(x)`` and right-tail
    ``F_right(x)`` probabilities against the reference sample, weights by empirical
    skewness ``gamma_j``, and aggregates ``max(O_left, O_right, O_skew)`` across features.
    """

    def __init__(self) -> None:
        self._prep: _FeaturePreprocessor | None = None
        self._ref_sorted: list[np.ndarray] = []
        self._skew_sign: np.ndarray | None = None

    def fit(self, F_train: np.ndarray) -> ECODDetector:
        self._prep = _FeaturePreprocessor.fit(F_train)
        Z = self._prep.transform(F_train)
        n, d = Z.shape
        self._ref_sorted = [np.sort(Z[:, j]) for j in range(d)]
        sk = np.zeros(d, dtype=np.float64)
        for j in range(d):
            if n >= 3 and np.std(Z[:, j]) > 1e-8:
                val = float(skew(Z[:, j], bias=False))
                sk[j] = np.sign(val) if np.isfinite(val) else 0.0
        self._skew_sign = sk
        return self

    def score_samples(self, F: np.ndarray) -> np.ndarray:
        if self._prep is None or self._skew_sign is None:
            raise RuntimeError("ECODDetector must be fit before scoring")
        Z = self._prep.transform(F)
        m, d = Z.shape
        n_ref = len(self._ref_sorted[0])
        eps = 1.0 / (n_ref + 1.0)

        o_left = np.zeros((m, d), dtype=np.float64)
        o_right = np.zeros((m, d), dtype=np.float64)
        o_auto = np.zeros((m, d), dtype=np.float64)

        for j in range(d):
            ref = self._ref_sorted[j]
            # Empirical CDF with Laplace smoothing in (0, 1) to prevent log(0) on test points
            cnt_le = np.searchsorted(ref, Z[:, j], side="right")
            cnt_ge = n_ref - np.searchsorted(ref, Z[:, j], side="left")
            p_left = np.clip((cnt_le + 0.5) / (n_ref + 1.0), eps * 0.5, 1.0)
            p_right = np.clip((cnt_ge + 0.5) / (n_ref + 1.0), eps * 0.5, 1.0)
            nl_l = -np.log(p_left)
            nl_r = -np.log(p_right)
            o_left[:, j] = nl_l
            o_right[:, j] = nl_r
            if self._skew_sign[j] < 0:
                o_auto[:, j] = nl_l
            elif self._skew_sign[j] > 0:
                o_auto[:, j] = nl_r
            else:
                o_auto[:, j] = 0.5 * (nl_l + nl_r)

        s_left = o_left.sum(axis=1)
        s_right = o_right.sum(axis=1)
        s_auto = o_auto.sum(axis=1)
        return np.maximum(np.maximum(s_left, s_right), s_auto) / max(1, d)
