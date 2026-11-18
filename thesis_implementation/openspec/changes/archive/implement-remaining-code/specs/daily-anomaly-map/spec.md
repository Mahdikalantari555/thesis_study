# Spec Delta

## Purpose

Compute per-field, per-date phenology-aware anomaly scores using phase-bin modified z-scores and render date-specific colors in the interactive time-slider map.

## ADDED Requirements

### Requirement: Per-date phase-bin anomaly scoring
The system SHALL compute a per-field, per-date anomaly score by mapping each observation date to its cycle stratum and 15-day days-since-harvest bin, computing per-band modified z-scores against the baseline with hierarchical stratum fallback, and aggregating across bands via root-mean-square into `daily_anomaly.parquet`.

#### Scenario: Observation inside a cycle bin
- **WHEN** a field has valid band observations on a date belonging to a cycle phase bin
- **THEN** `daily_anomaly.parquet` records the RMS modified z-score `S` computed from that bin's baseline median and scale rather than a constant cycle-level burden

#### Scenario: Sparse stratum fallback
- **WHEN** a cycle's fine stratum has missing or under-sampled statistics in a phase bin
- **THEN** daily scoring falls back to coarser strata and applies the scale floor so scores remain bounded and comparable across fields

### Requirement: Interactive map per-date coloring
The interactive custom map generator SHALL load `daily_anomaly.parquet` and color each field polygon dynamically on each observation date according to that date's anomaly score.

#### Scenario: Time-slider date change
- **WHEN** the user moves the map time slider across distinct observation dates
- **THEN** field polygon fill colors update per date to reflect each field's date-specific anomaly score
