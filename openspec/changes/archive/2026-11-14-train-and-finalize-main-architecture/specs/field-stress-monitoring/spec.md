## ADDED Requirements

### Requirement: Causal per-acquisition status

For every field and every acquisition date with data, the system SHALL output a status in {`normal`, `suspected_stress`, `no_data`} computed only from observations of the current cycle at or before that date.

#### Scenario: Future data does not change the past
- **WHEN** the status for date t is computed and later observations are appended to the cycle
- **THEN** the issued status for t is unchanged

#### Scenario: No observation
- **WHEN** a field has no valid acquisition at a date
- **THEN** no new status is issued for that date, and the platform may show the last status with days since last observation

### Requirement: Threshold calibration

The alarm threshold τ and the persistence k SHALL be calibrated on clean dev cycles so that at most 5 % of them raise any alarm. τ, k and the calibration-set hash SHALL be stored in the checkpoint sidecar.

#### Scenario: Calibration stored
- **WHEN** the main model is frozen
- **THEN** its sidecar JSON contains `threshold`, `persistence_k`, `far_target: 0.05` and `calibration_split_hash`

### Requirement: Honest naming

The positive class SHALL be named "suspected stress (anomaly)" in code, exports and UI until L4 validation is complete, and every export SHALL carry `ladder_rung`.

#### Scenario: Export label
- **WHEN** the exporter writes a flagged observation
- **THEN** the value is `suspected_stress` and the record carries `ladder_rung` from the sidecar

### Requirement: Full archive visible on the platform

The exporter SHALL score and export every field and every acquisition date of the archive (all splits, including censored in-progress cycles), and SHALL tag each observation with `split` in {`train`, `dev`, `test`, `monitoring`} so the platform can mark in-sample (train) scores as optimistic. Split membership SHALL only control which cycles enter metrics, never what is displayed.

#### Scenario: Train-period observation
- **WHEN** the platform shows an observation from a train cycle
- **THEN** its score and flag are displayed with a visible `train (in-sample)` tag
