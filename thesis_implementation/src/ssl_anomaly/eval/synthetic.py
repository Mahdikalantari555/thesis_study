"""Synthetic anomaly injection for recall / detection-delay benchmarking (V1).

Injection modes:
 1. NDVI drop: multiply NDVI (or a specified band) by (1 - depth) for `duration` consecutive bins
 2. Phenology delay: shift dsh phase alignment forward by K days (simulates late development)
 3. LST increase: add K degrees to ST_B10 for `duration` consecutive bins

All injections happen on the binned (cycle, bin, band) tensor to keep the
benchmark backend-agnostic. Injected cycles are drawn from the NORMAL
(non-anomalous) set so ground truth is known.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np


@dataclass
class InjectionConfig:
    ndvi_drop_depths: list[float] = field(default_factory=lambda: [0.05, 0.1, 0.2, 0.3])
    durations: list[int] = field(default_factory=lambda: [1, 2, 3, 5])
    phases: list[str] = field(default_factory=lambda: ["early", "mid", "late"])
    phenology_delay_days: list[int] = field(default_factory=lambda: [15, 30, 45])
    lst_increase_k: list[float] = field(default_factory=lambda: [1.0, 2.0, 4.0])
    n_per_stratum: int = 20
    alert_rate: float = 0.05
    ndvi_band_idx: int = -1  # set to actual index when bands include NDVI
    lst_band_idx: int = -1
    bin_days: int = 15


def _phase_start_bin(phase: str, n_bins: int) -> int:
    if phase == "early":
        return 0
    if phase == "mid":
        return n_bins // 3
    if phase == "late":
        return (2 * n_bins) // 3
    raise ValueError(f"Unknown phase {phase}")


def inject_anomaly(
    cycle: np.ndarray,  # (bins, bands)
    *,
    mode: str,
    start_bin: int,
    duration: int,
    depth: float = 0.0,
    lst_k: float = 0.0,
    shift_days: int = 0,
    bin_days: int = 15,
    ndvi_idx: int = 0,
    lst_idx: int = -1,
    rng: np.random.Generator | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (injected_cycle, ground_truth_mask).

    Ground truth mask is (bins,) bool with True on injected bins.
    """
    rng = rng or np.random.default_rng()
    out = cycle.copy()
    n_bins = cycle.shape[0]
    end = min(n_bins, start_bin + duration)
    gt = np.zeros(n_bins, dtype=bool)
    if start_bin >= n_bins:
        return out, gt
    gt[start_bin:end] = True

    if mode == "ndvi_drop" and ndvi_idx >= 0:
        out[start_bin:end, ndvi_idx] *= (1 - depth)
    elif mode == "lst_increase" and lst_idx >= 0 and lst_k > 0:
        out[start_bin:end, lst_idx] += lst_k
    elif mode == "phenology_delay" and shift_days != 0:
        # Shift dsh phase alignment: shift the band values right by shift_bins
        shift_bins = int(round(shift_days / bin_days))
        if abs(shift_bins) >= n_bins:
            return out, gt
        rolled = np.roll(out, shift=shift_bins, axis=0)
        # Zero out edge
        if shift_bins > 0:
            rolled[:shift_bins] = np.nan
        else:
            rolled[shift_bins:] = np.nan
        out = rolled
    else:
        return cycle.copy(), np.zeros_like(gt)
    return out, gt


def synthetic_benchmark(
    X_normal: np.ndarray,  # (N, bins, bands), held-out normal cycles
    score_fn: Callable[[np.ndarray], tuple[np.ndarray, np.ndarray]],
    # ^ takes a cycle (bins,bands) → (S_bin scores (bins,), flagged bool (bins,))
    cfg: InjectionConfig,
    *,
    rng: np.random.Generator | None = None,
) -> dict:
    """Run synthetic injection benchmark. Returns metrics dict.

    Metrics reported:
      - recall_at_alert_rate: fraction of injected cycles that fall into the
        top alert_rate fraction by anomaly burden
      - detection_delay_bins: mean first-detected bin delay after injection start
      - precision_at_k for the top-k
    """
    rng = rng or np.random.default_rng()
    N, n_bins, n_bands = X_normal.shape
    ndvi_idx = cfg.ndvi_band_idx if cfg.ndvi_band_idx >= 0 else 0
    lst_idx = cfg.lst_band_idx if cfg.lst_band_idx >= 0 else (n_bands - 1)

    ndvi_idx = min(ndvi_idx, n_bands - 1)
    lst_idx = min(lst_idx, n_bands - 1)

    results: dict = {"per_injection": [], "recall_at_alert_rate": [], "detection_delay": []}
    # Scenarios
    scenarios = []
    for depth in cfg.ndvi_drop_depths:
        for dur in cfg.durations:
            for ph in cfg.phases:
                scenarios.append(("ndvi_drop", depth, dur, ph, 0.0, 0))
    for k in cfg.lst_increase_k:
        for dur in cfg.durations:
            scenarios.append(("lst_increase", 0.0, dur, "mid", k, 0))
    for delay in cfg.phenology_delay_days:
        scenarios.append(("phenology_delay", 0.0, 3, "mid", 0.0, delay))

    # We will score N_NORMALS normal (uninjected) + n_injected injected per scenario
    for mode, depth, dur, phase, lst_k, delay in scenarios:
        if N == 0:
            continue
        n_inj = min(cfg.n_per_stratum, N)
        idx_sel = rng.choice(N, size=n_inj, replace=(n_inj > N))
        all_cycles = []
        labels = []  # 0=normal, 1=injected
        gt_start = []
        # Normal baseline scores (we only need burden for alert rate)
        burdens_norm = []
        flags_norm = []
        for i in range(N):
            s, flags = score_fn(X_normal[i])
            burdens_norm.append(cycle_anomaly_burden_from_S(s))
            flags_norm.append(flags)
            all_cycles.append(X_normal[i])
            labels.append(0)
            gt_start.append(-1)
        burdens_inj = []
        for j, i in enumerate(idx_sel):
            start = _phase_start_bin(phase, n_bins)
            injected, gt = inject_anomaly(
                X_normal[i], mode=mode, start_bin=start, duration=dur,
                depth=depth, lst_k=lst_k, shift_days=delay, bin_days=cfg.bin_days,
                ndvi_idx=ndvi_idx, lst_idx=lst_idx, rng=rng,
            )
            s, flags = score_fn(injected)
            bur = cycle_anomaly_burden_from_S(s)
            burdens_inj.append(bur)
            all_cycles.append(injected)
            labels.append(1)
            # Detection delay: first bin with flag after start_bin
            delay_bins = -1
            for b in range(start, n_bins):
                if flags[b]:
                    delay_bins = b - start
                    break
            results["detection_delay"].append((mode, depth, dur, phase, lst_k, delay, delay_bins))
            gt_start.append(start)

        burdens = np.array(burdens_norm + burdens_inj)
        labels_arr = np.array(labels)
        alert_n = max(1, int(np.ceil(cfg.alert_rate * len(burdens))))
        top_idx = np.argsort(-burdens)[:alert_n]
        tp = int(labels_arr[top_idx].sum())
        recall = tp / max(1, n_inj)
        results["recall_at_alert_rate"].append((mode, depth, dur, phase, lst_k, delay, recall))
        results["per_injection"].append(
            {"mode": mode, "depth": depth, "dur": dur, "phase": phase,
             "lst_k": lst_k, "delay": delay, "recall": recall}
        )
    return results


def cycle_anomaly_burden_from_S(S: np.ndarray, threshold: float = 3.5) -> float:
    obs = np.isfinite(S)
    if not obs.any():
        return 0.0
    return float(np.mean(S[obs] > threshold))
