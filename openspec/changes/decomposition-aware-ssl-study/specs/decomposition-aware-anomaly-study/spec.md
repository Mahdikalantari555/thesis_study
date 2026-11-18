## Purpose

Provide a reproducible field-level experiment for testing whether decomposition improves self-supervised learning and whether deviations of its components independently detect unusual temporal behavior.

## ADDED Requirements

### Requirement: Isolated field observations

The study SHALL consume QC-filtered polygon zonal statistics without changing ingest, serving or frozen checkpoints. It SHALL keep optical bands and derived vegetation indices as separate experiments, retain observation and interpolation provenance, and use the frozen holdout manifest to exclude holdout farms and dates before fitting.

#### Scenario: Missing input or insufficient admissible data
- **WHEN** the real-data store, a valid frozen manifest or sufficient development observations are missing
- **THEN** the real run fails with a diagnostic rather than substituting observations, dropping holdout constraints or invoking the simulator

#### Scenario: Gap provenance
- **WHEN** a short gap on the STL grid is interpolated
- **THEN** the grid records the fill distinctly, and no fill counts as a measured acquisition, a reconstruction target or a score

### Requirement: Matched decomposition benchmark

The no-training benchmark SHALL compare STL, Robust STL and harmonic regression by field and variable, with additive Trend, Seasonal and Residual, and report reconstruction error, temporal stability, coverage and runtime on a common observed cohort as well as individual method coverage.

#### Scenario: Insufficient observations
- **WHEN** a series has too little history or too large a gap for the requested estimator
- **THEN** its unsupported values are absent, not estimated from other fields or counted as zero error

### Requirement: Causal and retrospective separation

Causal features and scores SHALL NOT use observations after the score date. Retrospective fits SHALL be marked non-operational, and a training or calibration fit SHALL NOT use the later evaluation partition. Normalizers, learned model weights and historical references SHALL use only the training partition; alarm calibration SHALL use only calibration data.

#### Scenario: Future perturbation
- **WHEN** measurements after a causal scoring date are changed with the fitted training artifacts held fixed
- **THEN** the causal component values, features and score for that date are unchanged

### Requirement: Controlled feature ablation

The study SHALL compare B1–B7 and C1–C3 separately on both branches with the same target mask, capacity, optimizer budget, split and seeds. B1 is raw-only; C1 SHALL NOT contain any decomposition-derived statistics. Historical global and trailing local features SHALL be distinguishable. Random initialization and non-neural references SHALL be reported.

#### Scenario: Identical prediction task
- **WHEN** raw, component-only or combined feature arms are evaluated
- **THEN** the model reconstructs the same withheld raw target channels instead of being rewarded for reconstructing a smoother target

### Requirement: Component and hybrid scores

The study SHALL report D1 (SSL reconstruction error) and D2/D3/D4 (field-local residual, detrended-trend and seasonal deviations) individually. It SHALL compare annual-window references with a separately labeled inferred-phase reference. Hybrid scores SHALL use calibration-only scaling, equal weights as the baseline, and fixed weight-sensitivity arms; missing constituents SHALL NOT count as zero.

#### Scenario: No valid reference
- **WHEN** comparable historical observations or observed targets are insufficient
- **THEN** the affected component or hybrid score is absent, with its reduced coverage reported

### Requirement: Validation without stress ground truth

The study SHALL report historical reconstruction, temporal stability and paired synthetic anomaly sensitivity at field and acquisition levels. Synthetic changes SHALL be made only to held-out observations and SHALL cover abrupt drops, gradual drops, added oscillation, altered seasonality and persistent trend disturbance. It SHALL report missingness robustness and any available indicator agreement or adjacency-based consistency, not stress accuracy.

#### Scenario: Support changes with synthetic dose

- **WHEN** the study summarizes a dose-response trend for one arm and family
- **THEN** every dose uses the same intersection of actually changed,
  finitely scored field-dates with a finite clean baseline; report per-dose
  support lost and leave an unsupported trend absent. Per-dose sensitivity
  metrics retain their native support.

#### Scenario: Indicators unavailable or dependent
- **WHEN** quality-approved TVDI, CWSI or ETa observations are missing or share upstream inputs with the model
- **THEN** the report records missing coverage or the shared-input limitation without using indicators for calibration, selection or ground truth

### Requirement: Reproducible study and architecture gate

The study SHALL record data provenance, splits, support, seeds, budgets, metrics and checkpoints, support smoke execution and resume, and keep outputs isolated. Multi-branch training and adoption SHALL require separate review of real causal ablation evidence; SSA and wavelet arms are follow-ups.

#### Scenario: Smoke or retrospective gains
- **WHEN** only simulated or retrospective evidence supports decomposition
- **THEN** the report does not qualify the multi-branch gate or replace a production artifact
