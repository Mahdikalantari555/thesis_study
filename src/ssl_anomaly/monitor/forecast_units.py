"""Untrained causal forecasters for the forecast-unit probe (change
forecast-unit-probe; finding-20 path-C pre-test).

These arms replace gru_ae_main's LOO prediction with PRE-REGISTERED,
zero-training one-step-ahead forecasts inside the otherwise IDENTICAL
production statistic (causal offset correction → per-(bin, channel) q95 →
trailing-3 channel-max → τ at 5 % cycle-FAR). The measured quantity is the
UNIT: a one-step-ahead residual lives in "temporal predictability" units —
the field's own short-term variability — rather than the reconstruction
objective's across-cycle phenological spread (finding 20's binding
constraint).

Arms (fixed a priori, no tuning):
    persist  last observed value (a gap of ≤ 2 bins is bridged by the
             previous observed value; a larger gap → NaN)
    med3     median of the last ≤3 observed values in the gap-connected window
    trend4   OLS linear fit on the last 4 observed bins of the window,
             extrapolated one step

All forecasters are CAUSAL (bin o is predicted from observed bins < o of the
SAME channel only), respect the observation mask, and return NaN where
history is insufficient or broken — the bin does not score ("absent"
semantics, same as an unobserved bin in the production statistic).

Gap rule (pre-registered): a history window is the maximal run of observed
bins < o in which consecutive observed bins are ≤ ``MAX_HISTORY_GAP`` apart;
the window is empty when the distance from o to the last observed bin
exceeds ``MAX_HISTORY_GAP``. A forecaster never extrapolates across a broken
window.
"""

from __future__ import annotations

import numpy as np

FORECAST_ARMS = ("persist", "med3", "trend4")
MAX_HISTORY_GAP = 2        # observed-bin distance > 2 breaks the history window
TREND_MIN_HISTORY = 4      # trend4 fits OLS on the last 4 observed bins


def history_bins(
    mask_ch: np.ndarray,   # (T,) bool observation mask of ONE channel
    o: int,
    *,
    max_gap: int = MAX_HISTORY_GAP,
) -> np.ndarray:
    """Observed bin indices < o connected to o by gaps ≤ ``max_gap``.

    Walks back from the last observed bin before o while consecutive observed
    bins are ≤ ``max_gap`` apart; stops at the first break. Empty when no
    observed bin exists before o or the bridge from o to the last observed
    bin exceeds ``max_gap``.
    """
    obs = np.where(mask_ch[:o])[0]
    if obs.size == 0:
        return obs
    if int(o) - int(obs[-1]) > max_gap:
        return obs[:0]
    out = [int(obs[-1])]
    for b in obs[::-1][1:]:
        if out[-1] - int(b) > max_gap:
            break
        out.append(int(b))
    return np.array(out[::-1], dtype=np.int64)


def _forecast_channel(arm: str, z_ch: np.ndarray, mask_ch: np.ndarray) -> np.ndarray:
    """(T,) one-step-ahead predictions for ONE channel (NaN where unscored)."""
    T = z_ch.shape[0]
    pred = np.full(T, np.nan)
    if arm == "persist":
        for o in range(1, T):
            win = history_bins(mask_ch, o)
            if win.size:
                pred[o] = z_ch[win[-1]]
        return pred
    if arm == "med3":
        for o in range(1, T):
            win = history_bins(mask_ch, o)
            if win.size:
                pred[o] = float(np.median(z_ch[win[-3:]]))
        return pred
    if arm == "trend4":
        for o in range(TREND_MIN_HISTORY, T):
            win = history_bins(mask_ch, o)
            if win.size < TREND_MIN_HISTORY:
                continue
            xi = win[-TREND_MIN_HISTORY:]
            x = xi.astype(np.float64)
            y = z_ch[xi]
            xm = x.mean()
            denom = float(((x - xm) ** 2).sum())
            if denom <= 0:
                continue
            slope = float(((x - xm) * (y - y.mean())).sum()) / denom
            intercept = float(y.mean() - slope * xm)
            pred[o] = intercept + slope * float(o)
        return pred
    raise ValueError(f"unknown forecast arm: {arm!r} (expected one of {FORECAST_ARMS})")


def forecast_batch(
    arm: str,
    z: np.ndarray,      # (N, T, C) normalized values (0 where unobserved)
    mask: np.ndarray,   # (N, T, C) bool observation mask
) -> np.ndarray:
    """(N, T, C) one-step-ahead predictions in the same z-space as ``z``.

    Every prediction at bin o is a function of observed bins < o of the same
    channel only (causality invariant; see tests). NaN where the bin is
    unobserved or its history is insufficient/broken — the bin does not score.
    """
    if arm not in FORECAST_ARMS:
        raise ValueError(f"unknown forecast arm: {arm!r} (expected one of {FORECAST_ARMS})")
    z = np.asarray(z, dtype=np.float64)
    mask = np.asarray(mask, dtype=bool)
    N, T, C = z.shape
    out = np.full((N, T, C), np.nan)
    for n in range(N):
        for c in range(C):
            out[n, :, c] = _forecast_channel(arm, z[n, :, c], mask[n, :, c])
    return out
