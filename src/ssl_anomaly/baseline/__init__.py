"""Robust statistical baseline B1: stratum-aware median/MAD, iterative trimming, scoring."""

from __future__ import annotations

from .b0_calendar import (
    bin_by_calendar_doy,
    doy_from_datetime64,
    fit_b0_calendar_baseline,
    score_b0_cycles,
)
from .b2_phenology_axes import (
    bin_by_gdd,
    bin_by_landmarks,
    bin_by_progress,
    detect_cycle_landmarks,
    gdd_progress,
    landmark_progress,
    progress_axis,
)
from .b3_tabular import ECODDetector, IsolationForestDetector, extract_cycle_features
from .operational import (
    CWSIThresholdAlarm,
    GBTBaseline,
    NDVIThresholdAlarm,
    RFBaseline,
    precision_at_alert_budget,
    recall_at_alert_budget,
)
from .robust import RobustBaseline, build_stratum_table, fit_baseline, lookup_median_scale
from .score import (
    aggregate_band_scores,
    cusum_detector,
    cycle_anomaly_burden,
    ewma_detector,
    flag_runs,
    score_all_cycles,
    score_cycle,
)
from .trimming import trimmed_normal_cycles

__all__ = [
    "CWSIThresholdAlarm",
    "ECODDetector",
    "GBTBaseline",
    "IsolationForestDetector",
    "NDVIThresholdAlarm",
    "RFBaseline",
    "RobustBaseline",
    "aggregate_band_scores",
    "bin_by_calendar_doy",
    "bin_by_gdd",
    "bin_by_landmarks",
    "bin_by_progress",
    "build_stratum_table",
    "cusum_detector",
    "cycle_anomaly_burden",
    "detect_cycle_landmarks",
    "doy_from_datetime64",
    "ewma_detector",
    "extract_cycle_features",
    "fit_b0_calendar_baseline",
    "fit_baseline",
    "flag_runs",
    "gdd_progress",
    "landmark_progress",
    "lookup_median_scale",
    "precision_at_alert_budget",
    "progress_axis",
    "recall_at_alert_budget",
    "score_all_cycles",
    "score_b0_cycles",
    "score_cycle",
    "trimmed_normal_cycles",
]
