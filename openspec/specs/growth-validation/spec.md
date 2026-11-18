# growth-validation Specification

## Purpose
TBD - created by archiving change add-rigorous-growth-validation. Update Purpose after archive.

## Requirements

### Requirement: Prospective partitions and field holdout
The system SHALL assign cycles only when their full date interval fits within one predetermined chronological partition; held-out farms SHALL be absent from fitting and threshold calibration. The temporal test SHALL contain only farms seen in training.

#### Scenario: Boundary crossing
- **WHEN** a cycle starts in training and ends in validation
- **THEN** it is excluded rather than leaking across partitions.

#### Scenario: Unseen farm
- **WHEN** a farm is listed as held out
- **THEN** its future complete cycles are spatial test and no cycle from that farm is fitted or calibrated.

### Requirement: Paired controlled perturbations
The system SHALL score unmodified and modified copies of the same test cycle for sudden, gradual, shifted, peak and recovery perturbations, preserving missing values and declaring the tested feature and grid before test evaluation.

#### Scenario: Missing data
- **WHEN** the selected NDVI bin is missing
- **THEN** the perturbation SHALL NOT create an observation or label it modified.

### Requirement: Threshold and metrics
The system SHALL use training-only model fitting and validation-only threshold calibration and report synthetic point AP, ROC-AUC, precision, recall, false-positive rate, per-field event counts, detection delays and original alert fraction without claiming ground truth on original observations.

#### Scenario: No detections
- **WHEN** an injected event has no threshold crossing within it
- **THEN** the event is counted as missed and its delay remains undefined.

### Requirement: Scientific boundaries
The system SHALL identify its injected labels, selected split, baseline and scenario settings and SHALL NOT represent synthetic labels or weather proxy agreement as verified plant stress.

#### Scenario: Retrospective segmentation
- **WHEN** precomputed full-cycle segmentation is used
- **THEN** documentation SHALL state that online/causal detection has not been established.

### Requirement: SSL models under matched partitions
The system SHALL support training the existing GRU-AE and masked Transformer architectures from scratch on the same training tensors, fit feature scales only on training, and use validation-only thresholds. Their full-cycle scores SHALL be described as retrospective.

#### Scenario: Testing SSL
- **WHEN** `--models gru_ae,masked_transformer` is requested
- **THEN** each model is trained only on the train partition and evaluated on the same paired perturbations and validation threshold protocol as the baselines.

### Requirement: Geographic and external evidence support
The system SHALL permit explicitly preselected projected-centroid blocks with a centroid-distance exclusion buffer and provide a separate weather and neighboring-event consistency report without inferring causal stress.

#### Scenario: Buffered neighboring field
- **WHEN** a non-holdout centroid is within the selected buffer of a holdout centroid
- **THEN** its cycles are excluded from train, validation and test.

#### Scenario: Missing weather baseline
- **WHEN** a field-month has insufficient historical observations
- **THEN** the weather difference is null rather than imputed or inferred as zero.

### Requirement: Causal-prefix scoring and preprocessing
The system SHALL allow a fixed-horizon, unsmoothed, explicitly time-known anchor workflow and prefix-only SSL scoring.

#### Scenario: Future observation changes
- **WHEN** observations strictly after a scored bin change
- **THEN** the corresponding causal-prefix score SHALL remain unchanged.

#### Scenario: Late anchor
- **WHEN** an anchor is first known after its declared start
- **THEN** the causal input builder SHALL reject it.

### Requirement: Event affiliation and resource diagnostics
The system SHALL offer affiliation precision and recall on contiguous observed segments using the attributed reference implementation, and sampled process RSS during fitting and scoring.

#### Scenario: Missing observations
- **WHEN** a score is missing
- **THEN** it SHALL split observed segments rather than become a negative observation.
