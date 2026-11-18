# Spec Delta

## Purpose

Quantify within-field harvest-date scatter across the 32 subset farms using pixel or sub-field phenology trajectories to evaluate whether field-mean aggregation suffices before Phase 3.

## ADDED Requirements

### Requirement: Pixel or sub-field harvest detection
The E-INTRA runner SHALL execute harvest detection across pixel or sub-field NDVI time series for each of the 32 subset farms and align sub-field harvest events to field-level harvest cycles.

#### Scenario: Subset farm execution
- **WHEN** `run_eintra.py` runs on the 32 subset farms
- **THEN** sub-field harvest dates are detected per farm and matched against cycle windows

### Requirement: Within-field scatter reporting and Phase 3 gate check
The system SHALL compute within-field harvest-date scatter metrics in days for every evaluated farm and flag whether scatter exceeds two observation intervals (approximately 30 days).

#### Scenario: High intra-field scatter
- **WHEN** a farm's within-field harvest-date scatter exceeds two observation intervals
- **THEN** the report flags that farm in the Phase 3 intra-field heterogeneity summary
