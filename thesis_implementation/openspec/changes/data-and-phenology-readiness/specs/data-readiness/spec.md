## ADDED Requirements

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
