# Spec Delta

## Purpose
Segment harvest-driven crop cycles from field-level time series and align observations by growth stage so multi-year comparisons are phenology-aware rather than calendar-based.

## ADDED Requirements

### Requirement: Irregular smoothing
The system SHALL smooth irregular time series using weighted Whittaker-Eilers smoothing and SHALL tune the smoothing parameter by cross-validation.

#### Scenario: Missing observations
- **WHEN** a field has gaps in its time series
- **THEN** unobserved dates receive zero weight and do not force interpolation

### Requirement: Harvest detection
The system SHALL detect harvest candidates as NDVI troughs with sufficient prominence preceded by a high plateau and followed by a rise.

#### Scenario: False trough
- **WHEN** a single low observation does not recover
- **THEN** it is treated as an outlier rather than a harvest

### Requirement: Cycle segmentation
The system SHALL define a cycle as the interval between consecutive detected harvests and SHALL mark the first and last cycles as censored.

#### Scenario: Censored cycle
- **WHEN** a cycle is first or last in a field series
- **THEN** it is excluded from normal baseline construction but may still be scored

### Requirement: Replant handling
The system SHALL detect replanting from long gaps with low NDVI or metadata and SHALL reset the ratoon counter.

#### Scenario: Replant event
- **WHEN** a long gap with low NDVI is detected
- **THEN** the next cycle is labeled as a plant cycle with ratoon number zero

### Requirement: Primary phase axis
The system SHALL use days-since-harvest as the primary phase axis and SHALL support GDD and landmark registration as alternative axes.

#### Scenario: Compare axes
- **WHEN** evaluation runs
- **THEN** DOY, days-since-harvest, GDD, and landmark alignment are compared using within-bin scatter, prediction error, and stability metrics

### Requirement: Phase binning
The system SHALL bin observations into approximately 15-day intervals and SHALL leave unobserved bins as missing rather than interpolating beyond one adjacent bin.

#### Scenario: Long gap
- **WHEN** a phase bin has no observation
- **THEN** it remains missing and is not scored
