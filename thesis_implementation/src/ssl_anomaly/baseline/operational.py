"""Operational & weak-supervision baselines for RQ1 (Literature Gaps G2 & G7).

Implements cheap operational threshold alarms and supervised/self-labeled tree
ensembles demanded by the literature synthesis:
  - ``NDVIThresholdAlarm``: Operational mid-season NDVI deficit z-score alarm.
  - ``CWSIThresholdAlarm``: Operational thermal/evaporative stress threshold alarm.
  - ``RFBaseline``: RandomForest classifier trained on training-fold cycle features
    against weak/self-degraded targets (zero test leakage).
  - ``GBTBaseline``: Histogram Gradient-Boosted Trees (XGBoost-class GBDT) trained
    on the same training-fold protocol.
  - Equal-alert-budget evaluation helpers (``recall_at_alert_budget``,
    ``precision_at_alert_budget``).
"""

from __future__ import annotations

import warnings

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier

from .b3_tabular import _FeaturePreprocessor, extract_cycle_features


def recall_at_alert_budget(
    y_true: np.ndarray,
    y_score: np.ndarray,
    alert_rate: float = 0.05,
) -> float:
    """Fraction of true positives captured when alerting on top ``alert_rate`` of cycles."""
    yt = np.asarray(y_true, dtype=np.int32)
    ys = np.asarray(y_score, dtype=np.float64)
    fin = np.isfinite(ys)
    yt, ys = yt[fin], ys[fin]
    n_pos = int(yt.sum())
    if n_pos == 0 or yt.size == 0:
        return 0.0
    k_alerts = max(1, int(np.ceil(float(alert_rate) * yt.size)))
    top_idx = np.argsort(-ys)[:k_alerts]
    return float(yt[top_idx].sum() / n_pos)


def precision_at_alert_budget(
    y_true: np.ndarray,
    y_score: np.ndarray,
    alert_rate: float = 0.05,
) -> float:
    """Positive predictive value among top ``alert_rate`` alerted cycles."""
    yt = np.asarray(y_true, dtype=np.int32)
    ys = np.asarray(y_score, dtype=np.float64)
    fin = np.isfinite(ys)
    yt, ys = yt[fin], ys[fin]
    if yt.size == 0:
        return 0.0
    k_alerts = max(1, int(np.ceil(float(alert_rate) * yt.size)))
    top_idx = np.argsort(-ys)[:k_alerts]
    return float(yt[top_idx].mean())


class NDVIThresholdAlarm:
    """Operational mid-season NDVI drop alarm relative to training-fold normal canopy."""

    def __init__(self, ndvi_band_idx: int = 7) -> None:
        self.ndvi_band_idx = ndvi_band_idx
        self._bin_med: np.ndarray | None = None
        self._bin_scale: np.ndarray | None = None

    def fit(self, X_train: np.ndarray) -> NDVIThresholdAlarm:
        nd = np.asarray(X_train[:, :, self.ndvi_band_idx], dtype=np.float64)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            med = np.nanmedian(nd, axis=0)
            mad = np.nanmedian(np.abs(nd - med[None, :]), axis=0) * 1.4826
        g_med = float(np.nanmedian(nd)) if np.isfinite(nd).any() else 0.5
        g_mad = float(np.nanmedian(np.abs(nd - g_med)) * 1.4826) if np.isfinite(nd).any() else 0.1
        self._bin_med = np.where(np.isfinite(med), med, g_med)
        self._bin_scale = np.where(np.isfinite(mad) & (mad > 1e-3), mad, max(g_mad, 0.02))
        return self

    def score_cycles(self, X: np.ndarray) -> np.ndarray:
        """Higher score = larger downward NDVI deficit during active canopy bins."""
        if self._bin_med is None or self._bin_scale is None:
            raise RuntimeError("NDVIThresholdAlarm must be fit first")
        nd = np.asarray(X[:, :, self.ndvi_band_idx], dtype=np.float64)
        K = nd.shape[1]
        k_lo, k_hi = max(0, K // 6), min(K, int(0.85 * K))
        # Downward canopy anomaly: (median - observed) / scale
        deficit_z = (self._bin_med[None, k_lo:k_hi] - nd[:, k_lo:k_hi]) / self._bin_scale[None, k_lo:k_hi]
        out = np.zeros(len(X), dtype=np.float64)
        for i in range(len(X)):
            fin = np.sort(deficit_z[i][np.isfinite(deficit_z[i])])
            out[i] = float(np.mean(fin[-min(3, fin.size) :])) if fin.size else 0.0
        return out


class CWSIThresholdAlarm:
    """Operational thermal / evaporative stress threshold alarm."""

    def __init__(self, lst_band_idx: int = 6) -> None:
        self.lst_band_idx = lst_band_idx
        self._med: float = 0.5
        self._scale: float = 0.1

    def fit(
        self,
        X_train: np.ndarray,
        cwsi_train: np.ndarray | None = None,
    ) -> CWSIThresholdAlarm:
        if cwsi_train is not None and np.isfinite(cwsi_train).sum() >= 3:
            c = np.asarray(cwsi_train, dtype=np.float64)
            self._med = float(np.nanmedian(c))
            mad = float(np.nanmedian(np.abs(c - self._med)) * 1.4826)
            self._scale = max(mad, 0.02)
        else:
            lst = np.asarray(X_train[:, :, self.lst_band_idx], dtype=np.float64)
            self._med = float(np.nanmedian(lst))
            mad = float(np.nanmedian(np.abs(lst - self._med)) * 1.4826)
            self._scale = max(mad, 0.5)
        return self

    def score_cycles(
        self,
        X: np.ndarray,
        cwsi: np.ndarray | None = None,
    ) -> np.ndarray:
        if cwsi is not None and np.isfinite(cwsi).any():
            c = np.asarray(cwsi, dtype=np.float64)
            return np.where(np.isfinite(c), (c - self._med) / self._scale, 0.0)
        lst = np.asarray(X[:, :, self.lst_band_idx], dtype=np.float64)
        out = np.zeros(len(X), dtype=np.float64)
        for i in range(len(X)):
            fin = np.sort(lst[i][np.isfinite(lst[i])])
            top = float(np.mean(fin[-min(3, fin.size) :])) if fin.size else self._med
            out[i] = (top - self._med) / self._scale
        return out


def _synthesize_self_degraded_negatives(
    X_clean: np.ndarray,
    red_idx: int,
    nir_idx: int,
    lst_idx: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Create self-supervised degraded training cycles so RF/GBT train strictly without test labels."""
    N, K, _ = X_clean.shape
    X_deg = X_clean.copy()
    for i in range(N):
        mode = int(rng.integers(0, 3))
        s = int(rng.integers(K // 5, max(K // 5 + 1, int(0.7 * K))))
        L = min(5, K - s)
        if mode == 0:
            X_deg[i, s : s + L, nir_idx] *= 0.72
            X_deg[i, s : s + L, red_idx] *= 1.18
        elif mode == 1:
            X_deg[i, s : s + L, lst_idx] += 4.5
        else:
            X_deg[i] = np.roll(X_deg[i], shift=4, axis=0)
    return X_deg


class RFBaseline:
    """Operational RandomForest baseline trained on self-labeled / weak proxy fold features."""

    def __init__(self, red_idx: int = 2, nir_idx: int = 3, lst_idx: int = 6, seed: int = 42) -> None:
        self.red_idx = red_idx
        self.nir_idx = nir_idx
        self.lst_idx = lst_idx
        self.seed = seed
        self._prep: _FeaturePreprocessor | None = None
        self._clf: RandomForestClassifier | None = None

    def fit(self, X_train: np.ndarray, y_weak: np.ndarray | None = None) -> RFBaseline:
        rng = np.random.default_rng(self.seed)
        if y_weak is not None and len(np.unique(y_weak)) >= 2:
            F = extract_cycle_features(X_train, red_idx=self.red_idx, nir_idx=self.nir_idx)
            y = np.asarray(y_weak, dtype=np.int32)
        else:
            X_deg = _synthesize_self_degraded_negatives(
                X_train, self.red_idx, self.nir_idx, self.lst_idx, rng
            )
            F = extract_cycle_features(
                np.concatenate([X_train, X_deg], axis=0),
                red_idx=self.red_idx,
                nir_idx=self.nir_idx,
            )
            y = np.array([0] * len(X_train) + [1] * len(X_deg), dtype=np.int32)

        self._prep = _FeaturePreprocessor.fit(F)
        Z = self._prep.transform(F)
        self._clf = RandomForestClassifier(
            n_estimators=150, max_depth=6, random_state=self.seed, n_jobs=1
        )
        self._clf.fit(Z, y)
        return self

    def score_cycles(self, X: np.ndarray) -> np.ndarray:
        if self._prep is None or self._clf is None:
            raise RuntimeError("RFBaseline must be fit first")
        F = extract_cycle_features(X, red_idx=self.red_idx, nir_idx=self.nir_idx)
        Z = self._prep.transform(F)
        return self._clf.predict_proba(Z)[:, 1].astype(np.float64)


class GBTBaseline:
    """Operational Gradient-Boosted Trees (XGBoost-class HistGBDT) baseline."""

    def __init__(self, red_idx: int = 2, nir_idx: int = 3, lst_idx: int = 6, seed: int = 42) -> None:
        self.red_idx = red_idx
        self.nir_idx = nir_idx
        self.lst_idx = lst_idx
        self.seed = seed
        self._prep: _FeaturePreprocessor | None = None
        self._clf: HistGradientBoostingClassifier | None = None

    def fit(self, X_train: np.ndarray, y_weak: np.ndarray | None = None) -> GBTBaseline:
        rng = np.random.default_rng(self.seed + 17)
        if y_weak is not None and len(np.unique(y_weak)) >= 2:
            F = extract_cycle_features(X_train, red_idx=self.red_idx, nir_idx=self.nir_idx)
            y = np.asarray(y_weak, dtype=np.int32)
        else:
            X_deg = _synthesize_self_degraded_negatives(
                X_train, self.red_idx, self.nir_idx, self.lst_idx, rng
            )
            F = extract_cycle_features(
                np.concatenate([X_train, X_deg], axis=0),
                red_idx=self.red_idx,
                nir_idx=self.nir_idx,
            )
            y = np.array([0] * len(X_train) + [1] * len(X_deg), dtype=np.int32)

        self._prep = _FeaturePreprocessor.fit(F)
        Z = self._prep.transform(F)
        self._clf = HistGradientBoostingClassifier(
            max_iter=100, max_depth=4, learning_rate=0.06, random_state=self.seed
        )
        self._clf.fit(Z, y)
        return self

    def score_cycles(self, X: np.ndarray) -> np.ndarray:
        if self._prep is None or self._clf is None:
            raise RuntimeError("GBTBaseline must be fit first")
        F = extract_cycle_features(X, red_idx=self.red_idx, nir_idx=self.nir_idx)
        Z = self._prep.transform(F)
        return self._clf.predict_proba(Z)[:, 1].astype(np.float64)
