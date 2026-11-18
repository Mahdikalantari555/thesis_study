## ADDED Requirements

### Requirement: Generalization matrix (E9)

The matrix SHALL evaluate in-block, held-out fields, held-out periods and
both, with per-fold MDM80/FAR, fold spread and identical injection hashes.
Normalization SHALL be re-fitted only on locked train cycles inside each
fold, respecting the frozen global holdout. Report raw and sensor-stratified
results with the period/sensor confound. Test-block cycles SHALL be read
only by the locked final-test path.

#### Scenario: Folds are spatial and leak-free

- **WHEN** a fold trains and evaluates
- **THEN** the held-out block-pair contributes no training cycles and no
  normalization statistics, and the fold's injection-set hash equals every
  other fold's. Use five contiguous pairs from the ten locked blocks, with
  the temporal holdout defined by `dev_temporal_cutoff`.

#### Scenario: Fold execution prerequisites are incomplete

- **WHEN** the matrix runner lacks verified fold-specific training and
  calibration/evaluation inputs
- **THEN** execution refuses without training or substituting the ordinary dev
  sweep. Planning and dry runs remain available.

#### Scenario: Confound is surfaced, not hidden

- **WHEN** a temporal-axis drop is observed
- **THEN** the sensor-stratified columns show whether the drop tracks the
  L8→L9 era change, and the report states the confound explicitly

#### Scenario: L3 is earned

- **WHEN** an arm's matrix meets the pre-registered acceptance
- **THEN** its claims are upgraded to L3 with the matrix committed under
  reports/. Acceptance requires fold spread within two standard errors of the
  dev estimate, no censoring-status loss in any fold, and a bootstrap CI
  excluding temporal degradation beyond one severity level. Otherwise the
  claim stays at L2 and the failing cells are recorded.
