# Spec Delta

## Purpose

Benchmarks reconstruction-based SSL against cheap operational index threshold alarms and tree ensembles at equal alert budgets under Leave-One-Year-Out and spatial-block cross-validation on full-scale multi-year archives, including slow-drift detectors and standalone ERA5 weather storage.

## ADDED Requirements

### Requirement: Full-archive Leave-One-Year-Out and spatial-block evaluation at equal alert budgets (RQ1)
The system SHALL evaluate reconstruction-based SSL against `B0–B3`, operational `NDVI`/`CWSI` threshold alarms, and `RF`/gradient-boosted tree baselines at matched alert budgets (`Recall@5%`, `Recall@10%`, `AUC-PR`) under Leave-One-Year-Out and K-fold spatial-block CV on the 490-field, 13.5-year archive (using a deterministic 490-field × 13.5-year simulator fallback when external rasters are absent), reporting field-cluster bootstrap CIs and Holm-corrected paired Wilcoxon tests.

#### Scenario: Leave-One-Year-Out benchmark compares SSL and operational baselines at 5% alert budget
- **WHEN** `run_rq1_benchmark.py` runs across multi-year cycles with Leave-One-Year-Out splits
- **THEN** the system outputs `Recall@5%`, `Recall@10%`, `AUC-PR`, field-cluster 95% CIs, and Holm-adjusted Wilcoxon p-values comparing SSL against NDVI/CWSI alarms, RF/GBT, and B1/B2

### Requirement: Slow-drift CUSUM/EWMA detectors and 8-day Savitzky-Golay comparator
The system SHALL detect gradual sub-threshold multi-bin drift via CUSUM and EWMA z-score statistics alongside run flagging, and SHALL provide an 8-day interpolated Savitzky-Golay comparator against daily Whittaker smoothing.

#### Scenario: Gradual sustained drift triggers CUSUM and EWMA without single-bin spike
- **WHEN** a cycle exhibits a 2.2-sigma deviation sustained across six consecutive observed bins below the 3.5-sigma run cutoff
- **THEN** CUSUM and EWMA flag the drift interval while leaving unobserved NaN bins unflagged

### Requirement: Standalone daily ERA5 Zarr store with dynamic base-temperature GDD
The system SHALL store raw daily meteorological variables in `era5.zarr` without fixed pre-baked GDD and SHALL compute cumulative GDD dynamically for caller-specified `t_base` and `t_cap`.

#### Scenario: Dynamic GDD decreases monotonically as base temperature increases
- **WHEN** daily temperatures stored in `era5.zarr` are queried with `t_base=10` versus `t_base=12`
- **THEN** cumulative GDD at `t_base=12` is finite and never exceeds cumulative GDD at `t_base=10`
