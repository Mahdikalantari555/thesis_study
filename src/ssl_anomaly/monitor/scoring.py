"""Causal scoring, alarm rule and FAR calibration (design D5, spec §Threshold).

- Per-bin score: causal prediction error of the current bin from earlier bins
  (observed-mask-weighted MSE in z-space for deep models, mean z² for B1).
- Alarm rule: ``suspected_stress`` when the score exceeds τ at k consecutive
  observed bins, k ∈ {1, 2} chosen on dev.
- Threshold: τ calibrated on CLEAN dev cycles so at most 5 % of them raise any
  alarm over their whole length (cycle-level false-alarm rate).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

FAR_TARGET = 0.05


@dataclass
class Threshold:
    tau: float
    k: int
    far_target: float
    far_achieved: float
    calibration_n_cycles: int
    per_bin_q95: np.ndarray | None = None  # (T,) clean-dev normalizer
    statistic: str = "channel_max"

    def to_dict(self) -> dict:
        return {
            "tau": float(self.tau), "persistence_k": int(self.k),
            "far_target": float(self.far_target), "far_achieved": float(self.far_achieved),
            "calibration_n_cycles": int(self.calibration_n_cycles),
            "statistic": self.statistic,
            "per_bin_q95": (None if self.per_bin_q95 is None
                            else [round(float(v), 6) for v in self.per_bin_q95]),
        }


def channel_max_from_pred(
    pred: np.ndarray,   # (N, T, C) withheld-bin predictions (z-space or raw)
    truth: np.ndarray,  # (N, T, C)
    mask: np.ndarray,   # (N, T, C) bool
) -> np.ndarray:
    """Per-bin alarm statistic: MAX over observed channels of the squared
    prediction error.

    Dev-loop change #1 (2026-11-14): the mean-over-channels MSE (D5's L1
    statistic, still reported for NRMSE) dilutes band-specific anomalies by
    the channel count — a 1×MAD single-band shift moves the 8-channel mean by
    only ~0.02–0.1 while the null cycle-max sits at 2.5–6. Anomalies in this
    catalogue are band-specific by construction (D6), so the alarm statistic
    is the max-marginal; the mean statistic is kept as a reported secondary.
    """
    err = (pred - truth) ** 2
    err = np.where(mask, err, -np.inf)
    with np.errstate(all="ignore"):
        s = err.max(axis=-1)
    s[~mask.any(axis=-1)] = np.nan
    return s


def per_bin_q95_normalizer(
    clean_scores: np.ndarray,  # (N, T) alarm statistic on clean cycles
    *,
    floor_at_median: bool = True,
) -> np.ndarray:
    """Per-bin q95 of the clean-dev scores; bins whose null scale differs by
    10× (residual variance ≠ across-field dispersion) otherwise make a single
    global τ meaningless. Floored at the cross-bin median so a badly
    under-sampled bin cannot become over-permissive."""
    T = clean_scores.shape[1]
    q = np.full(T, np.nan)
    for b in range(T):
        col = clean_scores[:, b]
        col = col[np.isfinite(col)]
        if col.size >= 5:
            q[b] = float(np.percentile(col, 95))
    med = float(np.nanmedian(q))
    if floor_at_median and np.isfinite(med) and med > 0:
        q = np.where(np.isfinite(q), np.maximum(q, med), med)
    q = np.where(np.isfinite(q) & (q > 0), q, 1.0)
    return q


def normalize_scores(scores: np.ndarray, per_bin_q95: np.ndarray) -> np.ndarray:
    """Divide per-bin scores by the clean-dev per-bin q95 (NaN bins stay NaN)."""
    out = np.array(scores, dtype=np.float64, copy=True)
    ok = np.isfinite(out)
    out[ok] = out[ok] / np.broadcast_to(per_bin_q95[None, :], out.shape)[ok]
    return out


# ---------------------------------------------------------------------------
# Dev-loop change #2: causal cumulative channel-max statistic
# ---------------------------------------------------------------------------
def causal_offset_correct(
    resid: np.ndarray,     # (N, T, C) signed z-space residuals (value − prediction)
    mask: np.ndarray,      # (N, T, C) bool
    *,
    window: int = 6,
) -> np.ndarray:
    """Subtract a causal running-median FIELD offset from the residuals.

    The measured null tails are field-level offsets: a field running above or
    below the across-field train median produces residuals of many MADs at
    tight-scale (bin, channel) cells, which buries any 1×MAD injection under a
    5 % cycle-level FAR (diagnostic 2026-11-14: clean S-path q95 ≈ 11.7 while
    injections move paths by < 0.1). The fix measures deviation from the
    FIELD's own recent baseline:

        r'(n, b, c) = r(n, b, c) − median{ r(n, b', c) : b' among the last
                                            `window` observed bins < b }

    This is causal (past bins of the same cycle only), per channel, and
    standard monitoring practice (BFAST-Monitor-style history model /
    npphen-style baseline). A persistent anomaly becomes the field's new
    baseline after ~`window` observed bins — the detector intentionally
    measures the TRANSITION, not the level. Cells with no past observed bin
    keep r' = r (nothing to correct against).
    """
    N, T, C = resid.shape
    out = resid.copy()
    for n in range(N):
        for c in range(C):
            obs_bins = np.where(mask[n, :, c])[0]
            if obs_bins.size == 0:
                continue
            vals = resid[n, obs_bins, c]
            med_running = np.zeros(obs_bins.size)
            for j in range(obs_bins.size):
                lo = max(0, j - window)
                if j == 0:
                    med_running[j] = 0.0  # no history → no correction
                    continue
                med_running[j] = np.median(vals[lo:j])
            out[n, obs_bins, c] = vals - med_running
    return out


def cell_q95_normalizer(
    z2_clean: np.ndarray,  # (N, T, C) squared z residuals on clean dev (0 where unobserved)
    mask: np.ndarray,      # (N, T, C) bool
    *,
    min_cells: int = 8,
) -> np.ndarray:
    """Per-(bin, channel) q95 of the clean-dev squared z residuals, floored at
    the per-channel cross-bin median (under-sampled cells must not become
    over-permissive). Cells without enough observations get the floor."""
    T, C = z2_clean.shape[1], z2_clean.shape[2]
    q = np.full((T, C), np.nan)
    for c in range(C):
        for b in range(T):
            vals = z2_clean[:, b, c][mask[:, b, c]]
            if vals.size >= min_cells:
                q[b, c] = float(np.percentile(vals, 95))
        med = np.nanmedian(q[:, c])
        if np.isfinite(med) and med > 0:
            col = q[:, c]
            col[~np.isfinite(col) | (col <= 0)] = med
            q[:, c] = np.maximum(col, med)
        else:
            q[:, c] = 1.0
    return q


def cumulative_channel_max(
    z2: np.ndarray,     # (N, T, C) squared z residuals (any scale)
    mask: np.ndarray,   # (N, T, C) bool observation mask
    q95: np.ndarray,    # (T, C) cell normalizer
    *,
    window: int = 3,
    min_history: int = 3,
) -> np.ndarray:
    """Causal trailing-window alarm paths: (N, T) with

        S(n, t) = max_c [ mean over the last `window` bins b ≤ t (calendar
                          bins; unobserved gaps contribute nothing)
                          of z²(n, b, c)/q95(b, c) ]

    Why trailing-window (dev-loop change #2, refined): a leave-one-bin-out
    scorer conditions on injected history, so a persistent shift is absorbed
    into the prediction after its onset — the detectable signal is the
    *transition* (onset + the bins before the prediction adapts). An expanding
    mean dilutes that to noise over ~30 bins (measured: AUC-PR 0.12 <
    prevalence); a trailing window of `window` bins accumulates the transition
    while the null stays a mean of ≤ window draws (bounded). The max over
    channels keeps the detector channel-agnostic without the 8-channel mean
    dilution. Causal (bins ≤ t) and per-acquisition → platform-compatible.

    ``min_history``: no alarm before `min_history` observed bins total.
    NaN where not yet scored.
    """
    N, T, C = z2.shape
    zn = z2 / q95[None, :, :]
    zn = np.where(mask, zn, 0.0)
    mf = mask.astype(np.float64)
    csum = np.cumsum(zn, axis=1)          # (N, T, C)
    ccnt = np.cumsum(mf, axis=1)          # (N, T, C)
    # Trailing sums over the last `window` observed bins: cs(t) - cs(t - w_obs).
    # Bins without observations contribute zero to the sums, so a plain fixed
    # lag of `window` BINS approximates "last ≤ window observed bins" (long
    # unobserved gaps dilute — the honest causal behaviour: no data, no alarm).
    lag = min(window, T - 1)
    trailing_sum = csum - np.concatenate(
        [np.zeros((N, lag, C)), csum[:, :-lag, :]], axis=1,
    ) if lag > 0 else csum
    trailing_cnt = ccnt - np.concatenate(
        [np.zeros((N, lag, C)), ccnt[:, :-lag, :]], axis=1,
    ) if lag > 0 else ccnt
    with np.errstate(invalid="ignore", divide="ignore"):
        trailing_mean = trailing_sum / np.maximum(trailing_cnt, 1e-9)
    trailing_mean = np.where(trailing_cnt > 0, trailing_mean, -np.inf)
    with np.errstate(invalid="ignore"):
        S = trailing_mean.max(axis=-1)        # (N, T)
    S[np.isinf(S)] = np.nan
    total_obs = np.cumsum(mask.any(axis=-1).astype(np.int64), axis=1)
    S[total_obs < min_history] = np.nan
    return S


def alarm_per_cycle(
    scores: np.ndarray,      # (T,) per-bin scores, NaN where unobserved
    tau: float,
    k: int,
) -> bool:
    """True when k consecutive observed bins exceed τ anywhere in the cycle."""
    s = np.asarray(scores, dtype=np.float64)
    obs = np.isfinite(s)
    above = obs & (s > tau)
    if k <= 1:
        return bool(above.any())
    run = 0
    for a in above:
        run = run + 1 if a else 0
        if run >= k:
            return True
    return False


def first_alarm_bin(
    scores: np.ndarray,
    tau: float,
    k: int,
    onset_bin: int = 0,
) -> int:
    """First bin whose alarm run (k consecutive observed bins > τ) completes,
    searching from ``onset_bin``; -1 when no alarm."""
    s = np.asarray(scores, dtype=np.float64)
    obs = np.isfinite(s)
    above = obs & (s > tau)
    T = len(s)
    for b in range(max(0, onset_bin), T):
        if k <= 1:
            if above[b]:
                return b
        else:
            if b + k <= T and bool(above[b:b + k].all()):
                return b
    return -1


def calibrate_threshold(
    clean_scores: list[np.ndarray],  # per-cycle (T,) score arrays
    k: int,
    far_target: float = FAR_TARGET,
) -> tuple[float, float]:
    """Find the smallest τ with cycle-level FAR ≤ far_target, by binary search
    over the observed score values (alarm monotone decreasing in τ)."""
    if not clean_scores:
        raise ValueError("No clean scores for calibration")
    candidates = np.unique(np.concatenate([s[np.isfinite(s)] for s in clean_scores]))
    if candidates.size == 0:
        raise ValueError("All clean scores are NaN")
    lo, hi = 0, candidates.size - 1

    def far_at(tau: float) -> float:
        flags = [alarm_per_cycle(s, tau, k) for s in clean_scores]
        return float(np.mean(flags))

    # Smallest τ (from the candidate score values) achieving FAR ≤ target.
    best_tau = float(candidates[hi]) + 1e-9  # beyond max → FAR 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if far_at(float(candidates[mid])) <= far_target:
            best_tau = float(candidates[mid])
            hi = mid - 1
        else:
            lo = mid + 1
    achieved = far_at(best_tau)
    return best_tau, achieved


def choose_threshold(
    clean_scores: list[np.ndarray],
    injected_scores: list[np.ndarray],
    injected_onsets: list[int],
    far_target: float = FAR_TARGET,
) -> tuple[Threshold, dict]:
    """Pick k ∈ {1, 2} by detection rate at FAR ≤ target on injected dev cycles.

    Tie (equal detection rate) → smaller k (simpler). The second dict carries
    the per-k diagnostics for the metrics report.
    """
    per_k: dict[str, dict] = {}
    best: Threshold | None = None
    for k in (1, 2):
        tau, achieved = calibrate_threshold(clean_scores, k, far_target)
        detected = [
            first_alarm_bin(s, tau, k, onset) >= 0
            for s, onset in zip(injected_scores, injected_onsets)
        ]
        det_rate = float(np.mean(detected)) if detected else 0.0
        delays = [
            (first_alarm_bin(s, tau, k, onset) - onset) * 15
            for s, onset in zip(injected_scores, injected_onsets)
            if first_alarm_bin(s, tau, k, onset) >= 0
        ]
        per_k[f"k{k}"] = {
            "tau": float(tau), "far_achieved": float(achieved),
            "detection_rate": det_rate,
            "median_delay_days": float(np.median(delays)) if delays else None,
        }
        if best is None or det_rate > per_k[f"k{best.k}"]["detection_rate"]:
            best = Threshold(
                tau=tau, k=k, far_target=far_target, far_achieved=achieved,
                calibration_n_cycles=len(clean_scores),
            )
    assert best is not None
    return best, per_k


def masked_nrmse_per_band(
    pred: np.ndarray,   # (N, T, C) predictions at every bin
    truth: np.ndarray,  # (N, T, C) normalized (or raw) values
    mask: np.ndarray,   # (N, T, C) bool
    robust_range: np.ndarray,  # (C,) raw-unit denominator (or ones in z-space)
) -> np.ndarray:
    """Masked NRMSE per band: RMSE over observed bins ÷ robust range."""
    N, T, C = truth.shape
    out = np.full(C, np.nan)
    for c in range(C):
        sel = mask[:, :, c]
        if not sel.any():
            continue
        err = (pred[:, :, c] - truth[:, :, c])[sel]
        rmse = float(np.sqrt(np.mean(err ** 2)))
        denom = float(robust_range[c]) if robust_range is not None else 1.0
        out[c] = rmse / max(denom, 1e-9)
    return out


def partial_auc_pr(
    clean_max_scores: np.ndarray,    # (N_clean,) ranking scores
    injected_max_scores: np.ndarray,  # (N_inj,)
) -> float:
    """AUC-PR (average precision) for the injected class from max-score ranking.

    Standard step-wise average precision: sort by score descending, then
    AUC-PR = Σ_i (recall_i − recall_{i−1}) · precision_i. AUC-PR (not ROC) is
    required by the dev protocol because injected:clean is class-imbalanced.
    """
    y = np.concatenate([np.zeros(len(clean_max_scores)), np.ones(len(injected_max_scores))])
    s = np.concatenate([clean_max_scores, injected_max_scores])
    n_pos = float(y.sum())
    if n_pos == 0 or n_pos == len(y):
        return float("nan")
    order = np.argsort(-s, kind="stable")
    y_sorted = y[order]
    tp = np.cumsum(y_sorted)
    fp = np.cumsum(1.0 - y_sorted)
    precision = tp / np.maximum(tp + fp, 1.0)
    recall = tp / n_pos
    recall_prev = np.concatenate([[0.0], recall[:-1]])
    return float(np.sum((recall - recall_prev) * precision))


# ---------------------------------------------------------------------------
# Event-level FAR + Wilson CI (change literature-grounded-severity-protocol)
# ---------------------------------------------------------------------------
def decluster_events(alarm_bins: list[int], gap: int = 2) -> list[tuple[int, int]]:
    """Merge alarmed bins into events (POT declustering precedent).

    Two consecutive alarmed bins belong to the same event when their
    bin-index distance is ≤ ``gap`` (spec scenario 'Event declustering':
    'gap ≤ 2 bins' → one event); a larger separation starts a new event.
    Returns ``(first_bin, last_bin)`` spans in time order.
    """
    if not alarm_bins:
        return []
    bins = sorted(int(b) for b in alarm_bins)
    spans: list[tuple[int, int]] = [(bins[0], bins[0])]
    for b in bins[1:]:
        first, last = spans[-1]
        if b - last <= gap:
            spans[-1] = (first, b)
        else:
            spans.append((b, b))
    return spans


def event_far_from_paths(
    paths: np.ndarray,                 # (N, T) per-bin alarm statistic, NaN = unscored
    injection_windows: list,           # per cycle: None (clean) or [(onset, end_excl), …]
    tau: float,
    *,
    gap: int = 2,
) -> dict:
    """Event-level false-alarm rate over a set of cycles (sktime
    ``FalseAlarmRate`` semantics).

    Per cycle: alarmed bins (finite score > τ) are declustered into events
    (:func:`decluster_events`); an event is FALSE when it hits no injection
    window of its cycle. Extra alarms inside an already-hit window are not
    double-counted — an event overlapping any window is simply not false.
    The denominator is the number of SCORED bins (finite statistic) summed
    over cycles, i.e. FAR is in false events per scored 15-day bin.

    ``injection_windows[i]`` entries are ``(onset, end_exclusive)`` bin-index
    half-open intervals; ``None`` marks a clean cycle (every event false).
    """
    if len(injection_windows) != paths.shape[0]:
        raise ValueError("one injection-window entry per cycle required")
    n_events = n_false = n_scored = 0
    for i in range(paths.shape[0]):
        row = paths[i]
        alarmed = [int(b) for b in np.where(np.isfinite(row) & (row > tau))[0]]
        n_scored += int(np.isfinite(row).sum())
        windows = injection_windows[i]
        events = decluster_events(alarmed, gap=gap)
        n_events += len(events)
        for first, last in events:
            hit = False
            if windows:
                for onset, end in windows:
                    # Inclusive event span [first, last] vs half-open window
                    # [onset, end): overlap = hit (not double-counted).
                    if first <= end - 1 and last >= onset:
                        hit = True
                        break
            if not hit:
                n_false += 1
    return {
        "event_far": (n_false / n_scored) if n_scored else 0.0,
        "n_events": n_events,
        "n_false_events": n_false,
        "n_scored_bins": n_scored,
        "gap_bins": int(gap),
    }


def wilson_ci(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion (per-level detection
    rates are cells of n≈10–70 — asymptotic-normal CIs would be dishonest).

    Returns (nan, nan) for n = 0; clamps to [0, 1].
    """
    if n <= 0:
        return float("nan"), float("nan")
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = z * np.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denom
    return float(max(0.0, center - half)), float(min(1.0, center + half))
