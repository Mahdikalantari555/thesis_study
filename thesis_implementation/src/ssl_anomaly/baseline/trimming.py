"""Iterative normal-cycle trimming.

Algorithm per spec:
  1. Start with all non-censored cycles as 'active'.
  2. For each iteration:
     a. Build baseline from active cycles (leave-one-out when scoring each cycle).
     b. Score every cycle against that baseline.
     c. Compute per-cycle anomaly burden = fraction of (bin, band) where |z| > thr.
     d. For each stratum, mark the top q fraction as inactive.
  3. After iters, the remaining active cycles are the "normal" set.

Optionally filters using ETa/yield proxies. Never uses CWSI (circularity).
"""

from __future__ import annotations

import logging

import numpy as np

from .robust import fit_baseline
from .score import score_cycle_loo

log = logging.getLogger("ssl_anomaly.baseline.trimming")


def trimmed_normal_cycles(
    X: dict[str, np.ndarray],  # stratum -> (C_s, bins, bands)  (all non-censored cycles)
    strata_per_cycle: dict[str, np.ndarray],  # stratum key -> per-cycle index into X[stratum], with cycle's stratum label
    X_by_field: dict[int, np.ndarray],
    *,
    min_n: int = 5,
    kappa: float = 2.5,
    floor_pct: float = 5.0,
    q: float = 0.15,
    iters: int = 3,
    threshold: float = 3.5,
    cycle_proxy_bad: dict[str, np.ndarray] | None = None,
    # ^ maps stratum -> bool array (True = anomalous by external proxy like low ETa)
) -> dict[str, np.ndarray]:
    """Iteratively trim anomalous cycles from the normal set.

    Returns active_mask: stratum → boolean array of length C_s, True for cycles
    to keep as "normal".
    """
    active: dict[str, np.ndarray] = {}
    for key, arr in X.items():
        active[key] = np.ones(arr.shape[0], dtype=bool)
        # If an external proxy flags a cycle, start with it excluded.
        if cycle_proxy_bad and key in cycle_proxy_bad:
            active[key] &= ~cycle_proxy_bad[key].astype(bool)

    for it in range(iters):
        # Build baseline from active cycles
        X_act = {k: arr[active[k]] for k, arr in X.items() if active[k].any()}
        if not X_act:
            log.warning("Trimming iteration %d: no active cycles; stopping", it)
            break
        bl = fit_baseline(X_act, X_by_field, min_n=min_n, kappa=kappa, floor_pct=floor_pct)

        # Score each active cycle (leave-one-out for small strata; vectorized for large strata >= 60)
        burden = {k: np.zeros(arr.shape[0], dtype=np.float64) for k, arr in X.items()}
        for key, arr in X.items():
            act = active[key]
            n_act = int(act.sum())
            if n_act >= 60 and key in bl.stats:
                med = bl.stats[key].median[None, :, :]
                denom = np.maximum(bl.stats[key].scale[None, :, :], bl.floor)
                with np.errstate(all="ignore"):
                    z_all = (arr[act] - med) / denom
                fin_all = np.isfinite(z_all)
                hits = np.where(fin_all, (np.abs(z_all) > threshold).astype(np.float64), 0.0)
                cnts = fin_all.sum(axis=(1, 2))
                burden[key][act] = np.where(cnts > 0, hits.sum(axis=(1, 2)) / np.maximum(cnts, 1), 0.0)
            else:
                for i in np.where(act)[0]:
                    z = score_cycle_loo(
                        arr, active=act, index=i, baseline=bl, stratum_for_cycle=key,
                        floor=bl.floor, threshold=threshold,
                    )
                    # Burden = fraction of observed |z| > threshold
                    finite_mask = np.isfinite(z)
                    if finite_mask.any():
                        burden[key][i] = float(np.mean(np.abs(z[finite_mask]) > threshold))
                    else:
                        burden[key][i] = 0.0

        # Trim top q per stratum
        total_trimmed = 0
        for key, arr in X.items():
            act = active[key]
            if act.sum() < max(min_n + 1, int(1 / (1 - q)) + 1):
                continue
            bur = burden[key][act]
            cutoff = np.nanquantile(bur, 1 - q) if bur.size else 0.0
            to_trim = act & (burden[key] > cutoff)
            # Don't trim more than (1 - min_n) cycles
            if act.sum() - to_trim.sum() < min_n:
                # Trim fewer to stay above min_n
                keep_needed = min_n
                n_trim = act.sum() - keep_needed
                if n_trim <= 0:
                    continue
                ranked = np.argsort(-burden[key])  # highest burden first
                trim_mask = np.zeros_like(act)
                trimmed_count = 0
                for idx in ranked:
                    if act[idx]:
                        trim_mask[idx] = True
                        trimmed_count += 1
                        if trimmed_count >= n_trim:
                            break
                to_trim = trim_mask
            active[key] &= ~to_trim
            total_trimmed += int(to_trim.sum())

        log.debug("Trim iter %d: trimmed %d cycles across %d strata", it, total_trimmed, len(X))
        if total_trimmed == 0:
            break
    return active
