# Spec Delta

## Purpose
Compute phenology-aware anomaly scores by comparing each cycle to a robust multi-year normal baseline built from similar strata.

## ADDED Requirements

### Requirement: Stratum definition
The system SHALL assign each cycle to a stratum based on cycle type and variety group, and SHALL fall back to coarser strata when sample counts are low.

#### Scenario: Sparse bin
- **WHEN** a phase bin has fewer than the configured minimum number of normal cycles
- **THEN** the baseline uses the next coarser stratum

### Requirement: Robust baseline
The system SHALL compute median and MAD per stratum, phase bin, and band, and SHALL apply a shrinkage field offset.

#### Scenario: Field offset
- **WHEN** a field has few observations
- **THEN** its offset is shrunk toward zero

### Requirement: Iterative normal-cycle selection
The system SHALL iteratively remove cycles with the highest anomaly burden and SHALL optionally filter using ETa or yield proxies.

#### Scenario: Trimming
- **WHEN** trimming runs for the configured number of iterations
- **THEN** the top configured percentage of anomalous cycles per stratum is excluded from the baseline

### Requirement: Robust scoring
The system SHALL compute modified z-scores with a floor on the scale and SHALL aggregate bands into a per-bin score while preserving per-band signs.

#### Scenario: Near-zero scale
- **WHEN** MAD is below the configured floor
- **THEN** the floor is used as the denominator

### Requirement: Anomaly runs
The system SHALL flag anomaly runs when the aggregated score exceeds the threshold for at least the configured number of consecutive observed bins.

#### Scenario: Single spike
- **WHEN** only one observed bin exceeds the threshold
- **THEN** no anomaly run is flagged

### Requirement: Circular validation avoidance
The system SHALL NOT use CWSI as a normal-cycle selector and SHALL document circularity when LST is both an input and part of CWSI.

#### Scenario: CWSI proxy
- **WHEN** CWSI is used for validation
- **THEN** an ablation without LST is also reported
