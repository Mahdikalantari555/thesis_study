"""Pure analysis helpers for the predictive-SSL controlled trial parts A/C/D
(change predictive-ssl-controlled-trial, tasks 2.1–2.4).

Everything here is dev-side, read-only, and free of I/O so the trial scripts
stay thin orchestrators and the invariants are unit-tested:

- :func:`field_score_distribution` — part A: per-field clean-score
  distribution + alarm-concentration readout (a sensitivity-without-
  specificity failure shows up as a handful of fields carrying all alarms).
- :func:`temporal_stability` — part A: per-cycle temporal profile of the
  clean alarm path (a detector that fires everywhere/all the time is
  distinguishable from one that tracks events).
- :func:`checkpoint_errors` — part C: the finding-20 three-checkpoint error
  profile (before onset / first step after onset / several steps after) on
  the alarm-driving channel, in z units AND forecast-σ units, plus the
  persistence ratio (does the predictive error persist through a sustained
  drop, or decay as the model adapts?).
- :func:`tvdis_from_field_stats` — part D: field-level TVDI from EXISTING
  per-scene LST/NDVI field statistics (Sandholt-style NDVI–LST feature
  space across fields at the same bin); a DERIVED proxy, never ground truth.
"""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Part A — natural-data behavior
# ---------------------------------------------------------------------------
def field_score_distribution(
    paths: np.ndarray,      # (N, T) clean alarm paths (NaN where unscored)
    tau: float,
    field_ids: np.ndarray,  # (N,) field id per cycle
) -> dict:
    """Per-field distribution of the clean path maxima (in τ units) + alarm
    concentration across fields.

    Returns per-field n / median / IQR / max of the clean path max divided by
    τ, the flagged-cycle count per field, and the concentration readout: the
    share of all flagged cycles carried by the top-2 fields (1.0 = all
    alarms sit in two fields — the gate failure mode).
    """
    with np.errstate(invalid="ignore"):
        maxima = np.array([
            np.nanmax(p) if np.isfinite(p).any() else np.nan for p in paths
        ])
    rel = maxima / tau
    per_field: dict[str, dict] = {}
    flagged_total = 0
    for fid in sorted(set(int(f) for f in field_ids)):
        sel = field_ids == fid
        vals = rel[sel]
        vals = vals[np.isfinite(vals)]
        n = int(sel.sum())
        n_flag = int(np.sum(maxima[sel] > tau)) if np.isfinite(maxima[sel]).any() else 0
        flagged_total += n_flag
        per_field[str(fid)] = {
            "n_cycles": n,
            "n_flagged_cycles": n_flag,
            "median_max_over_tau": (float(np.median(vals)) if vals.size else float("nan")),
            "iqr_max_over_tau": ([float(np.percentile(vals, 25)), float(np.percentile(vals, 75))]
                                 if vals.size else [float("nan"), float("nan")]),
            "max_over_tau": (float(vals.max()) if vals.size else float("nan")),
        }
    flag_counts = sorted((v["n_flagged_cycles"] for v in per_field.values()), reverse=True)
    top2_share = (float(sum(flag_counts[:2]) / flagged_total) if flagged_total else float("nan"))
    return {
        "per_field": per_field,
        "n_fields": len(per_field),
        "n_flagged_cycles_total": flagged_total,
        "top2_field_flag_share": top2_share,
        "fields_with_flags": int(sum(1 for c in flag_counts if c > 0)),
    }


def temporal_stability(paths: np.ndarray, tau: float) -> dict:
    """Per-cycle temporal profile of the clean alarm path.

    ``cv_within_cycle``: std/mean of the finite path values per cycle
    (medians reported); ``above_tau_bins_per_cycle``: how many bins sit above
    τ (0 = quiet cycle); ``median_rel_noise``: median |path − median(path)|/τ
    — the typical distance between the null path and its own baseline, in
    threshold units.
    """
    cvs, above, rel_noise = [], [], []
    for p in paths:
        vals = p[np.isfinite(p)]
        if vals.size == 0:
            continue
        m = float(np.median(vals))
        if m > 0:
            cvs.append(float(np.std(vals) / m))
        above.append(int(np.sum(vals > tau)))
        rel_noise.append(float(np.median(np.abs(vals - m)) / tau))
    return {
        "n_cycles_scored": len(cvs),
        "cv_within_cycle_median": float(np.median(cvs)) if cvs else float("nan"),
        "above_tau_bins_per_cycle_median": float(np.median(above)) if above else float("nan"),
        "above_tau_bins_per_cycle_max": int(np.max(above)) if above else 0,
        "median_rel_noise_over_tau": float(np.median(rel_noise)) if rel_noise else float("nan"),
    }


def determinism_check(paths_a: np.ndarray, paths_b: np.ndarray) -> int:
    """Number of differing finite entries between two recomputations of the
    same clean paths (0 = deterministic)."""
    if paths_a.shape != paths_b.shape:
        raise ValueError("shape mismatch in determinism check")
    both = np.isfinite(paths_a) & np.isfinite(paths_b)
    diff = both & (paths_a != paths_b)
    asym = np.isfinite(paths_a) != np.isfinite(paths_b)
    return int(diff.sum() + asym.sum())


# ---------------------------------------------------------------------------
# Part C — three-checkpoint error profile (finding-20 hypothesis, direct test)
# ---------------------------------------------------------------------------
def checkpoint_errors(
    z_inj: np.ndarray,      # (T, C) injected cycle values (z units)
    pred_inj: np.ndarray,   # (T, C) predictions for the injected cycle
    z_nat: np.ndarray,      # (T, C) natural (counterfactual) values
    pred_nat: np.ndarray,   # (T, C) predictions for the natural cycle
    mask: np.ndarray,       # (T, C) observation mask
    q95: np.ndarray,        # (T, C) per-cell clean-residual normalizer
    onset_bin: int,
    *,
    pre_bins: int = 3,
    post_span: int = 4,     # "several steps after" = bins onset+2 .. onset+1+post_span
) -> dict:
    """Absolute one-step error on ONE channel around a persistent-drop onset.

    Checkpoints (owner's design): (1) before onset — the clean forecast error
    at the same bins of the natural cycle; (2) the first step after onset —
    the error spike at the onset bin; (3) several steps after — the mean
    error at bins onset+2 … onset+1+post_span (does the error persist or
    decay as the prediction adapts?).

    Every quantity is reported in z units and in forecast-σ units
    (divided by sqrt(q95[bin, channel]) per bin, averaged over the used bins).
    ``persistence_ratio`` = post / onset_step (≫0 and non-decaying = the
    error persists through the sustained drop; → 0 = the model absorbed it).
    """
    o = int(onset_bin)
    T, C = z_inj.shape
    pre = [b for b in range(max(0, o - pre_bins), o) if mask[b, 0]]
    post = [b for b in range(o + 2, min(T, o + 1 + post_span)) if mask[b, 0]]
    if not mask[o, 0]:
        return {"usable": False, "reason": "onset bin unobserved"}

    def _abs_err(z, pred, bins) -> list[float]:
        return [abs(float(z[b, 0] - pred[b, 0])) for b in bins]

    pre_err = _abs_err(z_nat, pred_nat, pre)
    onset_err = _abs_err(z_inj, pred_inj, [o])
    post_err = _abs_err(z_inj, pred_inj, post)

    def _fsig(z, pred, bins) -> list[float]:
        out = []
        for b in bins:
            s = float(np.sqrt(q95[b, 0]))
            if s > 0 and np.isfinite(s):
                out.append(abs(float(z[b, 0] - pred[b, 0])) / s)
        return out

    def _mean(v):
        return float(np.mean(v)) if v else float("nan")

    onset_step = _mean(onset_err)
    post_mean = _mean(post_err)
    return {
        "usable": True,
        "n_pre_bins": len(pre), "n_post_bins": len(post),
        "pre_error_z": _mean(pre_err),
        "onset_step_error_z": onset_step,
        "post_steps_error_z": post_mean,
        "pre_error_fsigma": _mean(_fsig(z_nat, pred_nat, pre)),
        "onset_step_error_fsigma": _mean(_fsig(z_inj, pred_inj, [o])),
        "post_steps_error_fsigma": _mean(_fsig(z_inj, pred_inj, post)),
        "persistence_ratio": (post_mean / onset_step
                              if np.isfinite(post_mean) and np.isfinite(onset_step) and onset_step > 0
                              else float("nan")),
    }


# ---------------------------------------------------------------------------
# Part D — TVDI from existing per-scene LST/NDVI field statistics
# ---------------------------------------------------------------------------
def tvdis_from_field_stats(
    ndvi: np.ndarray,     # (N, T) per-field per-bin NDVI (raw units, NaN=unobserved)
    lst: np.ndarray,      # (N, T) per-field per-bin LST (raw units, NaN=unobserved)
    *,
    n_ndvi_bins: int = 10,
    edge_quantile: float = 0.9,
    min_points: int = 8,
) -> tuple[np.ndarray, dict]:
    """Field-level TVDI from the across-field NDVI–LST feature space.

    For each bin b: collect the observed (NDVI, LST) pairs of all fields at
    that bin (the same acquisition → one feature space); split the NDVI range
    into ``n_ndvi_bins`` quantile bins; the DRY edge is the ``edge_quantile``
    upper LST per NDVI bin and the WET edge is the ``1−edge_quantile`` lower
    LST (edges linearly interpolated across NDVI bins; global min/max where a
    bin has < ``min_points`` points);

        TVDI = (LST − LST_wet(NDVI)) / (LST_dry(NDVI) − LST_wet(NDVI))

    clipped to [0, 1]; NaN where the envelope is degenerate (dry ≤ wet) or
    the pair is unobserved. This is Sandholt-style feature-space scaling
    computed from EXISTING per-scene per-field statistics — a DERIVED proxy
    sharing the LST/NDVI inputs of the models (disclosed dependence), never
    ground truth and never an L4 claim.
    """
    ndvi = np.asarray(ndvi, dtype=np.float64)
    lst = np.asarray(lst, dtype=np.float64)
    N, T = ndvi.shape
    out = np.full((N, T), np.nan)
    envelope_info = {"n_bins_with_envelope": 0, "degenerate_bins": 0}
    for b in range(T):
        nd_b = ndvi[:, b]
        ls_b = lst[:, b]
        ok = np.isfinite(nd_b) & np.isfinite(ls_b)
        if ok.sum() < min_points:
            envelope_info["degenerate_bins"] += 1
            continue
        nd_o, ls_o = nd_b[ok], ls_b[ok]
        qs = np.quantile(nd_o, np.linspace(0, 1, n_ndvi_bins + 1))
        centers, dry, wet = [], [], []
        for i in range(n_ndvi_bins):
            lo, hi = qs[i], qs[i + 1]
            sel = (nd_o >= lo) & (nd_o <= hi if i == n_ndvi_bins - 1 else nd_o < hi)
            if sel.sum() >= min_points:
                centers.append(float(np.median(nd_o[sel])))
                dry.append(float(np.quantile(ls_o[sel], edge_quantile)))
                wet.append(float(np.quantile(ls_o[sel], 1.0 - edge_quantile)))
        if len(centers) < 2:
            envelope_info["degenerate_bins"] += 1
            continue
        centers_a = np.asarray(centers)
        # Enforce a non-degenerate envelope: dry edge above wet edge.
        dry_a = np.asarray(dry)
        wet_a = np.asarray(wet)
        bad = dry_a <= wet_a
        if bad.any():
            pad = max(1e-6, 0.05 * float(np.nanmedian(dry_a - wet_a[np.isfinite(wet_a) & ~bad]))
                      if np.isfinite(wet_a[~bad]).any() else 1e-6)
            dry_a = np.where(bad, wet_a + pad, dry_a)
        dry_i = lambda x: float(np.interp(x, centers_a, dry_a))  # noqa: E731
        wet_i = lambda x: float(np.interp(x, centers_a, wet_a))  # noqa: E731
        for n in range(N):
            if not (np.isfinite(ndvi[n, b]) and np.isfinite(lst[n, b])):
                continue
            d, w = dry_i(ndvi[n, b]), wet_i(ndvi[n, b])
            if d <= w:
                continue
            out[n, b] = float(np.clip((lst[n, b] - w) / (d - w), 0.0, 1.0))
        envelope_info["n_bins_with_envelope"] += 1
    return out, envelope_info


def indicator_agreement(
    indicator: np.ndarray,   # (N, T) per-field per-bin proxy value (NaN=unobserved)
    paths: np.ndarray,       # (N, T) clean alarm paths
    tau: float,
    *,
    threshold_quantile: float = 0.75,
) -> dict:
    """Agreement of flagged (field, bin) events with an independent-ish
    indicator, as an above-chance readout with a Wilson CI.

    Flagged = finite path > τ; the indicator "high" cut is its own
    ``threshold_quantile`` over all observed entries. Reports the high-
    indicator rate among flagged bins vs unflagged bins (rate difference +
    Wilson CIs) — CORROBORATING proxy agreement only, never proof of stress.
    """
    flagged = np.isfinite(paths) & (paths > tau)
    observed = np.isfinite(indicator)
    cut = np.nanquantile(indicator[observed], threshold_quantile) if observed.any() else np.nan
    hi = observed & (indicator > cut)
    n_flag = int((flagged & observed).sum())
    n_flag_hi = int((flagged & hi).sum())
    n_unflag = int((~flagged & observed).sum())
    n_unflag_hi = int((~flagged & hi).sum())
    from ssl_anomaly.monitor.scoring import wilson_ci

    lo_f, hi_f = wilson_ci(n_flag_hi, n_flag) if n_flag else (float("nan"), float("nan"))
    lo_u, hi_u = wilson_ci(n_unflag_hi, n_unflag) if n_unflag else (float("nan"), float("nan"))
    rate_flag = n_flag_hi / n_flag if n_flag else float("nan")
    rate_unflag = n_unflag_hi / n_unflag if n_unflag else float("nan")
    return {
        "indicator_high_cut": float(cut),
        "threshold_quantile": threshold_quantile,
        "n_flagged_bins_observed": n_flag,
        "n_flagged_high": n_flag_hi,
        "n_unflagged_bins_observed": n_unflag,
        "n_unflagged_high": n_unflag_hi,
        "high_rate_flagged": rate_flag,
        "high_rate_flagged_wilson95": [lo_f, hi_f],
        "high_rate_unflagged": rate_unflag,
        "high_rate_unflagged_wilson95": [lo_u, hi_u],
        "rate_difference": (rate_flag - rate_unflag
                            if np.isfinite(rate_flag) and np.isfinite(rate_unflag) else float("nan")),
        "n_flagged_cycles": 0,  # filled by the caller if needed
    }
