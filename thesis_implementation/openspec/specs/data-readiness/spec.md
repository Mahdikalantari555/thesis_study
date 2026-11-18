# data-readiness Specification

## Purpose
TBD - created by archiving change data-and-phenology-readiness. Update Purpose after archive.

## Requirements

### Requirement: Literature-backed method decisions

The project SHALL hold a literature review covering automatic phenology/season extraction, time-axis representation for SSL, realistic sugarcane stress signatures, and SSL for irregular satellite series. Each method decision for model training SHALL cite it.

#### Scenario: Perturbation catalogue
- **WHEN** the perturbation set for the dev metric is finalised
- **THEN** each perturbation type lists its bands, phase, duration and magnitude with at least one source, or is marked as an assumption

### Requirement: Measured segmentation error

The project SHALL estimate the cycle-segmentation error rate on a stratified sample of real490 cycles, with a 95 % confidence interval and an error taxonomy, and SHALL compute automatic sanity flags for all cycles.

#### Scenario: Audit output
- **WHEN** `scripts/audit_cycles.py` runs
- **THEN** it writes `reports/cycle_audit/flags.csv`, one plot per sampled cycle, and the sample definition with its seed

#### Scenario: Blocking error rate
- **WHEN** the estimated error rate exceeds the decision threshold in design D2
- **THEN** model training does not start until the user approves a segmentation fix

### Requirement: Readiness gate for training

`train-and-finalize-main-architecture` SHALL NOT start its training code until the decision record (design D4) is written and approved by the user.

#### Scenario: Gate
- **WHEN** the decision record is missing or unapproved
- **THEN** tasks in sections 2–5 of the training change stay unchecked

### Requirement: Stage-conditioned anomaly detection

The project SHALL implement stage-conditioned anomaly detection that distinguishes stress-induced NDVI decline from natural phenological decline (senescence, pre-harvest drying, dormancy). Natural within-stage decline that stays inside the stage's confidence envelope SHALL NOT be flagged as anomalous.

#### Scenario: Phenology stage assignment by normalized progress

- **WHEN** a non-censored cycle has valid NDVI observations in its 15-day bins
- **THEN** each cycle-bin is assigned a phenology stage by normalized progress = (bin_index × bin_days) / cycle_length_days:
  - S1 establishment/growth: progress 0.00–0.25
  - S2 vegetative/reproductive: progress 0.25–0.60
  - S3 maturity/senescence: progress 0.60–0.85
  - S4 harvest/dormancy: progress 0.85–1.00

#### Scenario: Confidence envelope per stage

- **WHEN** NDVI values are pooled per stage across all non-censored cycles
- **THEN** the lower envelope for each stage is median − 2 × MAD (median absolute deviation)
- **AND** the upper envelope is median + 2 × MAD

#### Scenario: Anomaly flag rule

- **WHEN** a cycle-bin has valid NDVI below the stage's lower envelope
- **THEN** the cycle-bin is flagged as anomalous
- **WHEN** a cycle-bin's NDVI is within the stage's envelope (including natural decline during senescence)
- **THEN** the cycle-bin is NOT flagged as anomalous

#### Scenario: Script output

- **WHEN** `scripts/stage_conditioned_anomaly.py` runs with `--all`
- **THEN** it writes `reports/stage_conditioned_anomaly/stage_conditioned_anomaly.parquet` (per-bin results), `.../anomalies_only.parquet` (flagged anomalies), and `.../summary.json` (envelopes, counts, wall time, git SHA)
- **AND** it runs in under 15 minutes per seed on laptop hardware

#### Scenario: Smoke test

- **WHEN** `scripts/stage_conditioned_anomaly.py` runs with `--smoke`
- **THEN** it processes 20 randomly selected fields and completes in under 2 minutes
