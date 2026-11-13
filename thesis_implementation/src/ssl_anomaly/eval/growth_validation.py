"""Forward-only, paired synthetic growth-anomaly evaluation primitives.

This module does not infer physiological causes or assume unmodified cycles are healthy.
All cycle intervals are inclusive. Models and calibration must be fitted separately.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.svm import OneClassSVM


def temporal_split(starts, ends, fields, *, train_end='2021-12-31', val_end='2023-12-31',
                   test_end='2026-12-31', holdout_fields=(), excluded_fields=()):
    """Partition complete cycles; discard boundary crossings and held-out training farms."""
    s = np.asarray(starts, dtype='datetime64[D]')
    e = np.asarray(ends, dtype='datetime64[D]')
    f = np.asarray(fields).astype(str)
    if s.ndim != 1 or e.shape != s.shape or f.shape != s.shape:
        raise ValueError('starts, ends and fields must be aligned one-dimensional arrays')
    a, b, c = [np.datetime64(x, 'D') for x in (train_end, val_end, test_end)]
    if np.isnat(s).any() or np.isnat(e).any() or np.any(s > e) or not a < b < c:
        raise ValueError('invalid dates or split boundaries')
    held = np.isin(f, np.asarray(list(holdout_fields)).astype(str))
    excluded_field = np.isin(f, np.asarray(list(excluded_fields)).astype(str))
    if np.any(held & excluded_field):
        raise ValueError('held-out and excluded field lists overlap')
    train = (e <= a) & ~held & ~excluded_field
    seen = np.isin(f, f[train])
    val = (s > a) & (e <= b) & ~held & ~excluded_field & seen
    future = (s > b) & (e <= c)
    temporal = future & ~held & ~excluded_field & seen
    spatial = future & held
    return {'train': train, 'validation': val, 'temporal_test': temporal,
            'spatial_test': spatial,
            'excluded': ~(train | val | temporal | spatial)}


def inject_growth(cycle, *, kind, start, duration, magnitude, band=0, shift=1):
    """Return copy and exact modified-observation mask, only for the selected index band.

    Shift is in bins; no wrapping or interpolation across missing values. Recovery is a
    sustained attenuation following an initial drop, not a biological stress simulator.
    """
    x = np.asarray(cycle, dtype=float)
    if x.ndim != 2 or not 0 <= band < x.shape[1] or not 0 <= start < len(x):
        raise ValueError('invalid cycle, band or start')
    if duration < 1 or not 0 < magnitude <= 1 or shift < 1:
        raise ValueError('duration, magnitude or shift out of range')
    if kind not in {'sudden', 'gradual', 'delay', 'peak', 'recovery'}:
        raise ValueError('unknown anomaly kind')
    y = x.copy()
    end = min(len(x), start + duration)
    idx = np.arange(start, end)
    v = x[:, band]
    if kind == 'delay':
        # Only use earlier observed bins; unobserved pairs are not invented.
        idx = idx[idx >= shift]
        good = np.isfinite(v[idx]) & np.isfinite(v[idx - shift])
        idx = idx[good]
        y[idx, band] = v[idx] + magnitude * (v[idx - shift] - v[idx])
    else:
        idx = idx[np.isfinite(v[idx])]
        if kind == 'peak' and idx.size:
            # Operate on the highest finite observation in the requested interval.
            idx = idx[[int(np.argmax(v[idx]))]]
        if kind == 'gradual':
            weights = (idx - start + 1) / (end - start)
        elif kind == 'recovery':
            # initial perturbation followed by a persistent suppressed recovery
            weights = np.where(idx == start, 1.0, 0.7)
        else:
            weights = np.ones(len(idx))
        y[idx, band] = v[idx] - magnitude * weights
    mask = np.zeros(len(x), dtype=bool)
    mask[idx] = np.isfinite(y[idx, band]) & (y[idx, band] != v[idx])
    return y, mask


class PhaseMAD:
    """Global phase-wise median/MAD, fitted exclusively on training cycles."""
    def fit(self, X):
        x = np.asarray(X, dtype=float)
        with np.errstate(all='ignore'):
            self.median = np.nanmedian(x, axis=0)
            self.scale = 1.4826 * np.nanmedian(np.abs(x - self.median), axis=0)
        self.scale = np.maximum(np.where(np.isfinite(self.scale), self.scale, 0), 0.02)
        return self

    def score(self, X):
        z = np.abs((np.asarray(X, dtype=float) - self.median) / self.scale)
        # Avoid treating all-missing bins as zeros.
        finite = np.isfinite(z)
        return np.divide(np.where(finite, z, 0).sum(axis=2), finite.sum(axis=2),
                         out=np.full(z.shape[:2], np.nan), where=finite.sum(axis=2) > 0)


class FieldPhaseMAD(PhaseMAD):
    """Train-only phase baseline with shrunk field-specific offsets and global fallback."""
    def __init__(self, shrinkage=3.0):
        if shrinkage < 0:
            raise ValueError('shrinkage must be nonnegative')
        self.shrinkage = shrinkage

    def fit(self, X, fields):
        x = np.asarray(X, float)
        ids = np.asarray(fields).astype(str)
        if ids.shape != (len(x),):
            raise ValueError('field IDs must align')
        super().fit(x)
        self.offsets = {}
        for fid in np.unique(ids):
            subset = x[ids == fid]
            count = np.isfinite(subset).sum(axis=0)
            with np.errstate(all='ignore'):
                local = np.nanmedian(subset, axis=0)
            difference = np.where(np.isfinite(local - self.median), local - self.median, 0)
            weight = np.divide(count, count + self.shrinkage,
                               out=np.zeros_like(count, dtype=float), where=(count + self.shrinkage) > 0)
            self.offsets[fid] = difference * weight
        return self

    def score(self, X, fields):
        x = np.asarray(X, float)
        ids = np.asarray(fields).astype(str)
        if ids.shape != (len(x),):
            raise ValueError('field IDs must align')
        med = np.stack([self.median + self.offsets.get(fid, 0) for fid in ids])
        z = np.abs((x-med)/self.scale)
        finite = np.isfinite(z)
        return np.divide(np.where(finite,z,0).sum(axis=2), finite.sum(axis=2),
                         out=np.full(z.shape[:2], np.nan), where=finite.sum(axis=2)>0)


class WindowIsolationForest:
    """Causal multivariate trailing windows, with imputation fitted on train only."""
    def __init__(self, window=3, seed=42):
        if window < 1:
            raise ValueError('window must be positive')
        self.window, self.seed = window, seed

    def _windows(self, X):
        X = np.asarray(X, dtype=float)
        n, k, b = X.shape
        out = np.full((n, k, self.window, b), np.nan)
        for lag in range(self.window):
            if lag < k:
                out[:, lag:, self.window - lag - 1, :] = X[:, :k-lag, :]
        return out.reshape(n * k, -1), np.isfinite(X).any(axis=2)

    def fit(self, X):
        a, valid = self._windows(X)
        with np.errstate(all='ignore'):
            self.fill = np.nanmedian(a[valid.ravel()], axis=0)
        self.fill = np.where(np.isfinite(self.fill), self.fill, 0)
        a = np.where(np.isfinite(a), a, self.fill)
        if not valid.any():
            raise ValueError('no observed training bins')
        self.model = IsolationForest(n_estimators=100, random_state=self.seed, n_jobs=1).fit(a[valid.ravel()])
        return self

    def score(self, X):
        a, valid = self._windows(X)
        a = np.where(np.isfinite(a), a, self.fill)
        result = -self.model.score_samples(a).reshape(valid.shape)
        result[~valid] = np.nan
        return result


class WindowOneClassSVM(WindowIsolationForest):
    """One-class SVM on identical causal windows, with train-only imputation/scaling."""
    def __init__(self, window=3, nu=.05):
        super().__init__(window=window)
        if not 0 < nu <= 1:
            raise ValueError('nu must be in (0, 1]')
        self.nu = nu

    def fit(self, X):
        a, valid = self._windows(X)
        if not valid.any():
            raise ValueError('no observed training bins')
        with np.errstate(all='ignore'):
            self.fill = np.nanmedian(a[valid.ravel()], axis=0)
        self.fill = np.where(np.isfinite(self.fill), self.fill, 0)
        a = np.where(np.isfinite(a), a, self.fill)
        self.center = np.median(a[valid.ravel()], axis=0)
        self.scale = np.median(np.abs(a[valid.ravel()] - self.center), axis=0) * 1.4826
        self.scale = np.where(self.scale > 1e-6, self.scale, 1.0)
        self.model = OneClassSVM(nu=self.nu, gamma='scale').fit(((a-self.center)/self.scale)[valid.ravel()])
        return self

    def score(self, X):
        a, valid = self._windows(X)
        a = np.where(np.isfinite(a), a, self.fill)
        scores = -self.model.decision_function((a-self.center)/self.scale).reshape(valid.shape)
        scores[~valid] = np.nan
        return scores


def calibrate(scores, quantile=0.95):
    """Validation quantile; alert burden is not a verified false-positive rate."""
    if not 0 < quantile < 1:
        raise ValueError('quantile must be between 0 and 1')
    s = np.asarray(scores, float)
    s = s[np.isfinite(s)]
    if not len(s):
        raise ValueError('no finite validation scores')
    return float(np.quantile(s, quantile))


def point_metrics(labels, scores, threshold):
    y = np.asarray(labels, bool).ravel()
    s = np.asarray(scores, float).ravel()
    if y.shape != s.shape:
        raise ValueError('labels and scores must align')
    ok = np.isfinite(s)
    y, s = y[ok], s[ok]
    pred = s > threshold
    tp = int(np.sum(pred & y)); fp = int(np.sum(pred & ~y))
    fn = int(np.sum(~pred & y)); tn = int(np.sum(~pred & ~y))
    div = lambda a, b: float(a / b) if b else None
    both = len(np.unique(y)) == 2
    return {'n': len(y), 'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn,
            'average_precision': float(average_precision_score(y, s)) if both else None,
            'roc_auc': float(roc_auc_score(y, s)) if both else None,
            'precision': div(tp, tp + fp), 'recall': div(tp, tp + fn),
            'false_positive_rate': div(fp, fp + tn)}


def event_metrics(mask, scores, threshold, times=None):
    """One cycle: contiguous known modified bins, first alert within each event.

    Missing scores break observation continuity and count as misses, not false negatives
    with known normality. Delays are in bins or elapsed days for datetime64 times.
    """
    m, s = np.asarray(mask, bool), np.asarray(scores, float)
    if m.ndim != 1 or s.shape != m.shape:
        raise ValueError('mask and scores must be aligned 1D arrays')
    if times is not None:
        t = np.asarray(times, dtype='datetime64[D]')
        if t.shape != m.shape or np.isnat(t).any() or np.any(t[1:] < t[:-1]):
            raise ValueError('times must be valid and sorted')
    starts = np.flatnonzero(m & ~np.r_[False, m[:-1]])
    ends = np.flatnonzero(m & ~np.r_[m[1:], False]) + 1
    delays = []
    for a, b in zip(starts, ends):
        hits = np.flatnonzero(np.isfinite(s[a:b]) & (s[a:b] > threshold))
        if hits.size:
            h = a + int(hits[0])
            delays.append(int((t[h] - t[a]) / np.timedelta64(1, 'D')) if times is not None else int(hits[0]))
        else:
            delays.append(None)
    return {'events': len(starts), 'detected': sum(d is not None for d in delays),
            'missed': sum(d is None for d in delays), 'delays': delays,
            'delay_unit': 'days' if times is not None else 'bins'}


def event_overlap_counts(mask, scores, threshold):
    """Count predicted runs overlapping known injected runs, no point adjustment.

    Precision refers to the synthetic label only; pre-existing natural anomalies and
    later post-event effects may count as unmatched alarms.
    """
    mask, scores = np.asarray(mask, bool), np.asarray(scores, float)
    if mask.ndim != 1 or scores.shape != mask.shape:
        raise ValueError('mask and scores must align')
    pred = np.isfinite(scores) & (scores > threshold)
    starts = np.flatnonzero(pred & ~np.r_[False, pred[:-1]])
    ends = np.flatnonzero(pred & ~np.r_[pred[1:], False]) + 1
    matched = sum(bool(mask[a:b].any()) for a, b in zip(starts, ends))
    return {'predicted_runs': len(starts), 'matched_runs': matched,
            'unmatched_runs': len(starts) - matched}


def field_bootstrap_ratio(numerator, denominator, *, seed=42, n_boot=500):
    """Bootstrap whole fields, resampling paired per-field counts together."""
    n = np.asarray(numerator, dtype=float)
    d = np.asarray(denominator, dtype=float)
    if n.ndim != 1 or d.shape != n.shape or np.any(n < 0) or np.any(d < n):
        raise ValueError('invalid per-field counts')
    if len(n) < 2 or d.sum() == 0 or n_boot < 1:
        return None
    rng = np.random.default_rng(seed)
    ix = rng.integers(0, len(n), size=(n_boot, len(n)))
    denom = d[ix].sum(axis=1)
    ratios = np.divide(n[ix].sum(axis=1), denom, out=np.full(n_boot, np.nan), where=denom > 0)
    ratios = ratios[np.isfinite(ratios)]
    return [float(x) for x in np.quantile(ratios, [.025, .975])] if len(ratios) else None


def geographic_holdout(field_ids, x, y, *, block_size, origin_x, origin_y, holdout_blocks, buffer=0):
    """Deterministic square blocks and point-distance buffer in caller's projected CRS.

    Centroid distances do not guarantee polygon-to-polygon separation. Blocks are
    chosen by the caller before outcome inspection; x/y units and CRS are caller's duty.
    """
    ids = np.asarray(field_ids).astype(str)
    x, y = np.asarray(x, float), np.asarray(y, float)
    if ids.ndim != 1 or x.shape != ids.shape or y.shape != ids.shape or len(set(ids)) != len(ids):
        raise ValueError('fields must be unique, aligned 1D arrays')
    if (not np.isfinite(x).all() or not np.isfinite(y).all()
            or not np.isfinite([block_size, origin_x, origin_y, buffer]).all()
            or block_size <= 0 or buffer < 0):
        raise ValueError('invalid coordinates or geographic parameters')
    bx = np.floor((x-origin_x)/block_size).astype(int)
    by = np.floor((y-origin_y)/block_size).astype(int)
    blocks = {tuple(map(int, block)) for block in holdout_blocks}
    if not blocks:
        raise ValueError('must specify at least one holdout block')
    selected = np.array([(int(a), int(b)) in blocks for a,b in zip(bx,by)])
    if not selected.any():
        raise ValueError('no field in selected blocks')
    near = np.zeros(len(ids), dtype=bool)
    if buffer > 0:
        for ix in np.flatnonzero(selected):
            near |= (x-x[ix])**2 + (y-y[ix])**2 <= buffer**2
    near &= ~selected
    return {'holdout_fields': sorted(ids[selected].tolist()),
            'excluded_fields': sorted(ids[near].tolist()),
            'field_blocks': {str(i): [int(a), int(b)] for i,a,b in zip(ids,bx,by)}}


def affiliation_by_observed_segment(mask, scores, threshold):
    """Affiliation metrics on finite contiguous segments containing injected labels.

    Missing scores are unknown, so they split the timeline rather than becoming
    artificial negative labels. Metrics are computed independently per segment.
    """
    import importlib
    import importlib.util
    from pathlib import Path
    import sys
    package = '_ssl_growth_affiliation'
    if package not in sys.modules:
        folder = Path(__file__).resolve().parents[1] / '_vendor' / 'affiliation'
        spec = importlib.util.spec_from_file_location(package, folder / '__init__.py',
                                                       submodule_search_locations=[str(folder)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[package] = module
        spec.loader.exec_module(module)
    gen = importlib.import_module(package + '.generics')
    metrics = importlib.import_module(package + '.metrics')
    mask, scores = np.asarray(mask, bool), np.asarray(scores, float)
    if mask.ndim != 1 or mask.shape != scores.shape:
        raise ValueError('mask and scores must be aligned')
    valid = np.isfinite(scores)
    starts = np.flatnonzero(valid & ~np.r_[False, valid[:-1]])
    ends = np.flatnonzero(valid & ~np.r_[valid[1:], False]) + 1
    results = []
    for a, b in zip(starts, ends):
        if not mask[a:b].any():
            continue
        pred = gen.convert_vector_to_events((scores[a:b] > threshold).astype(int).tolist())
        truth = gen.convert_vector_to_events(mask[a:b].astype(int).tolist())
        r = metrics.pr_from_events(pred, truth, (0, int(b-a)))
        results.append({'start_bin': int(a), 'end_bin_exclusive': int(b),
                        'precision': float(r['precision']) if np.isfinite(r['precision']) else None,
                        'recall': float(r['recall']) if np.isfinite(r['recall']) else None})
    return results
