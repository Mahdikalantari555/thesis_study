# Spec: Real Data Ingest

## Purpose

Enables automated loading, quality filtering, and phenological cycle segmentation directly from the primary farm-level multi-band Zarr store for downstream statistical baselines and self-supervised models.

## ADDED Requirements

### Requirement: Direct Zarr v2 dataset ingestion
The system SHALL ingest the full farm-level dataset from `Data/Processed/satellite/stats.zarr`, reading arrays for 490 fields, 538 acquisition dates, and 7 spectral/thermal bands alongside associated weather covariates.

#### Scenario: Array dimension verification
- **WHEN** the ingest module opens `stats.zarr`
- **THEN** it validates that the fields coordinate has length 490, the time coordinate has 538 dates ranging from 2013-03-30 to 2026-09-10, and the expected statistical summaries (median, mean, std) are accessible.

### Requirement: Quality and cloud-mask filtering
The system SHALL apply scene and field-level quality screening using `valid_frac` and pixel-level QA flags, masking observations where the usable pixel fraction falls below a configurable threshold.

#### Scenario: Low valid pixel fraction
- **WHEN** a field observation has a `valid_frac` less than 0.50
- **THEN** that observation is flagged as masked and excluded from baseline fitting and normal cycle reference pools.

### Requirement: Days-since-harvest cycle segmentation
The system SHALL segment multi-year field series into distinct sugarcane growth cycles using Whittaker-smoothed NDVI troughs and register observations along the days-since-harvest (DSH) and GDD axes.

#### Scenario: Sugarcane harvest detection
- **WHEN** a smoothed NDVI curve exhibits a sharp trough below the emergence threshold followed by sustained regrowth
- **THEN** the timestamp is recorded as a harvest event boundary and a new growth cycle is initialized.

### Requirement: Farm metadata alignment
The system SHALL associate each farm time series with its static attributes from `farms.parquet`, including block identifier, sugarcane variety, age class, and management division.

#### Scenario: Stratum attribute lookup
- **WHEN** fitting stratum-specific baseline curves
- **THEN** the system groups cycles according to variety (e.g. CP69-1062) and block category to establish the appropriate normal reference distribution.
