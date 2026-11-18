"""Signal-path decomposition diagnostics (change reconstruction-invariance-diagnostic).

Locates WHERE the injected anomaly signal is lost between the model residual
and the alarm decision, using the EXACT production statistic (causal offset
correction → per-cell q95 → trailing-window channel-max → τ) so every stage
quantity is consistent with the severity sweep:

    stage 1  residual formation   r(onset) = z − pred_z  (σ units; LOO context
             at the onset is clean, so a small onset residual means the model
             itself fails to represent the step — loss/pretext issue)
    stage 2  offset correction    what the causal running median subtracts at
             the onset (a large subtraction means history residuals eat the
             transient — scoring fix)
    stage 3  normalization        r′²/q95 vs τ (an outlier-inflated per-cell
             q95 destroys SNR — scoring fix, finding 16 §8)
    stage 4  aggregation          trailing-3 mean dilution (a 1-bin spike is
             divided by the window; persistent drops survive — scoring fix)

plus the absorption ratio at post-onset bins (does the prediction track the
injected level ≈1, or the counterfactual pre-injection level ≈0) — the direct
test of the reconstruction-invariance hypothesis for the persistent family.

Read-only: nothing here writes artifacts or changes thresholds/models.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ssl_anomaly.monitor.scoring import (
    causal_offset_correct,
    cumulative_channel_max,
)

ONSET_RESIDUAL_BORN_SIGMA = 3.0   # ≥3σ onset residual counts as "signal born"
OFFSET_DOMINANCE_FRAC = 0.5       # subtraction ≥ 50 % of the onset residual → stage 2


@dataclass
class StageDecomposition:
    """Stage quantities for ONE injection (see module docstring)."""

    onset_residual_sigma: float        # |z(onset,c) − pred_z(onset,c)| in σ units
    offset_subtraction: float          # amount subtracted by the history median at the onset
    residual_after_correction: float   # r′ at the onset
    cell_q95: float                    # q95(onset, c) actually used
    normalized_contribution: float     # r′² / q95
    tau: float
    snr1: float                        # normalized_contribution / τ
    path_max_window: float             # max production path over [onset, onset+duration+2]
    snr2: float                        # path_max_window / τ
    detected: bool                     # production first_alarm completes from the onset (search to T)
    first_alarm_bin: int               # production first-alarm bin from the onset (−1 = none)
    absorption: float | None = None    # post-onset absorption ratio (None when no post-onset bins)


def decompose_injection(
    z_inj: np.ndarray,      # (T, C) normalized values OF THE INJECTED cycle
    pred_z: np.ndarray,     # (T, C) LOO predictions for the injected cycle (z units;
                            # B1's climatology "prediction" is 0 in its own z-space)
    z_natural: np.ndarray,  # (T, C) normalized values of the PRE-INJECTION cycle (counterfactual)
    mask: np.ndarray,       # (T, C) observation mask
    q95: np.ndarray,        # (T, C) frozen per-cell normalizer from the sweep calibration
    tau: float,
    k: int,
    onset_bin: int,
    duration: int,
    channel: int,
) -> StageDecomposition:
    """Decompose one injection through the production statistic stages."""
    T = z_inj.shape[0]
    r = (z_inj - pred_z) * mask
    r_corr = causal_offset_correct(r[None], mask[None])[0]
    z2 = (r_corr * r_corr) * mask
    path = cumulative_channel_max(z2[None], mask[None], q95)[0]

    o = int(onset_bin)
    r_onset = float(z_inj[o, channel] - pred_z[o, channel])
    r_prime = float(r_corr[o, channel])
    sub = r_onset - r_prime
    q = float(q95[o, channel])
    contribution = (r_prime * r_prime) / q if q > 0 else float("nan")

    end = min(T, o + int(duration) + 2)  # +2: trailing window tail after the drop
    window = path[o:end]
    finite = window[np.isfinite(window)]
    path_max = float(finite.max()) if finite.size else float("nan")
    # Detection uses the PRODUCTION rule (search from the onset to the end of
    # the cycle) so `detected` cross-checks the severity sweep exactly.
    fb = _first_alarm_in_window(path, tau, k, o, T)

    post_bins = list(range(o + 1, min(T, o + int(duration))))
    absorp = None
    if post_bins:
        absorp = absorption_ratio(pred_z, z_inj, z_natural, mask, post_bins, channel)

    return StageDecomposition(
        onset_residual_sigma=r_onset,
        offset_subtraction=sub,
        residual_after_correction=r_prime,
        cell_q95=q,
        normalized_contribution=contribution,
        tau=float(tau),
        snr1=contribution / float(tau),
        path_max_window=path_max,
        snr2=path_max / float(tau),
        detected=fb >= 0,
        first_alarm_bin=int(fb),
        absorption=absorp,
    )


def _first_alarm_in_window(path: np.ndarray, tau: float, k: int, onset: int, end: int) -> int:
    """Production-consistent first-alarm bin: k consecutive observed bins > τ,
    searching from `onset` to `end` (mirrors scoring.first_alarm_bin)."""
    s = np.asarray(path, dtype=np.float64)
    obs = np.isfinite(s)
    above = obs & (s > tau)
    for b in range(max(0, onset), min(end, len(s))):
        if k <= 1:
            if above[b]:
                return b
        elif b + k <= len(s) and bool(above[b:b + k].all()):
            return b
    return -1


def absorption_ratio(
    pred_z: np.ndarray,       # (T, C) predictions for the injected cycle
    z_injected: np.ndarray,   # (T, C)
    z_natural: np.ndarray,    # (T, C) counterfactual pre-injection values
    mask: np.ndarray,         # (T, C)
    bins: list[int],          # post-onset injected bins to measure
    channel: int,
) -> float:
    """Absorption ratio A at post-onset bins (reconstruction-invariance test),
    defined as a convex weight on [0, 1]:

        A = MAE(pred, natural) / (MAE(pred, natural) + MAE(pred, injected))

    A ≈ 1 → the prediction tracks the INJECTED level (the drop is absorbed
    into the learned temporal structure); A ≈ 0 → the prediction stays at the
    counterfactual natural level; 0.5 → halfway. NaN when the injected and
    natural levels coincide (nothing to absorb) or no usable bins.
    """
    d_inj, d_nat = [], []
    for b in bins:
        if not mask[b, channel]:
            continue
        delta = float(z_injected[b, channel] - z_natural[b, channel])
        if delta == 0.0:
            continue
        d_inj.append(abs(float(pred_z[b, channel] - z_injected[b, channel])))
        d_nat.append(abs(float(pred_z[b, channel] - z_natural[b, channel])))
    if not d_inj:
        return float("nan")
    denom = float(np.mean(d_nat)) + float(np.mean(d_inj))
    if denom <= 0:
        return float("nan")
    return float(np.mean(d_nat)) / denom


def attribute_stage(d: StageDecomposition) -> str:
    """Dominant-loss attribution for one undetected injection (design.md
    decision matrix; the first failing stage in causal order)."""
    if d.detected:
        return "detected"
    if abs(d.onset_residual_sigma) < ONSET_RESIDUAL_BORN_SIGMA:
        return "stage1_residual"
    if abs(d.offset_subtraction) >= OFFSET_DOMINANCE_FRAC * abs(d.onset_residual_sigma):
        return "stage2_offset"
    if d.snr1 >= 1.0:
        return "stage4_aggregation"  # contribution ≥ τ but the path is not → dilution
    return "stage3_normalization"


def aucpr_stage(pos_scores: list[float], neg_scores: list[float]) -> float:
    """AUC-PR (average precision) of one stage's score: injected decompositions
    as positives vs matched clean-cycle decompositions as negatives. The gap
    between the stage-1 (raw onset residual) and stage-4 (final path) values
    localizes ranking power lost by stages 2–4. NaN when either class is
    empty (no ranking problem is defined there)."""
    y = [1] * len(pos_scores) + [0] * len(neg_scores)
    s = [float(v) for v in pos_scores] + [float(v) for v in neg_scores]
    if not pos_scores or not neg_scores:
        return float("nan")
    from sklearn.metrics import average_precision_score  # local: heavy import

    return float(average_precision_score(y, s))


def _med_iqr(values: list[float]) -> dict:
    arr = np.asarray([v for v in values if np.isfinite(v)], dtype=np.float64)
    if arr.size == 0:
        return {"median": float("nan"), "iqr": [float("nan"), float("nan")], "n": 0}
    q25, q75 = np.percentile(arr, [25, 75])
    return {"median": float(np.median(arr)), "iqr": [float(q25), float(q75)], "n": int(arr.size)}


def summarize_cells(cells: dict[str, list[StageDecomposition]]) -> dict:
    """Per-cell medians + IQR, detection fraction, absorption medians and the
    decision-matrix attribution (majority vote of per-injection attributions)."""
    out: dict[str, dict] = {}
    for key, ds in cells.items():
        if not ds:
            continue
        attrs = [attribute_stage(d) for d in ds]
        counts: dict[str, int] = {}
        for a in attrs:
            counts[a] = counts.get(a, 0) + 1
        out[key] = {
            "n": len(ds),
            "detection_rate": float(np.mean([d.detected for d in ds])),
            # magnitudes (the signed values live on the per-injection records)
            "onset_residual_sigma": _med_iqr([abs(d.onset_residual_sigma) for d in ds]),
            "offset_subtraction": _med_iqr([abs(d.offset_subtraction) for d in ds]),
            "normalized_contribution": _med_iqr([d.normalized_contribution for d in ds]),
            "snr1": _med_iqr([d.snr1 for d in ds]),
            "path_max_window": _med_iqr([d.path_max_window for d in ds]),
            "snr2": _med_iqr([d.snr2 for d in ds]),
            "absorption_ratio": (_med_iqr([d.absorption for d in ds if d.absorption is not None])
                                 if any(d.absorption is not None for d in ds) else None),
            "attributed_stage": max(counts, key=counts.get),
            "attribution_counts": counts,
        }
    return out
