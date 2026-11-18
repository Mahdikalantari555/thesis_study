## ADDED Requirements

### Requirement: Frozen training-holdout manifest

New frozen holdout manifests SHALL use the locked `kmeans.test_block_fields`
as whole-field exclusions and `test_period_start` as the inclusive date cutoff.
Fields unknown at freeze and dates after the declared archive end SHALL also
be held out. The manifest SHALL record SHA-256 and provenance and SHALL NOT be
replaced without `--force` and a recorded reason. The locked split assignment
SHALL NOT be changed.

#### Scenario: Manifest is a pure derivation

- **WHEN** the manifest is built
- **THEN** its farm and date sets are exactly derivable from splits_locked,
  its sha and provenance are recorded, and a rebuild without `--force`
  fails

#### Scenario: Existing freeze differs from its spatial block

- **WHEN** a real training, patch normalization or decomposition study path
  uses an existing freeze with the locked splits
- **THEN** it verifies the source split hash, date cutoff and coverage of the
  spatial block; missing block members or mismatched provenance abort; any
  additional frozen exclusions remain in force, with no manifest rewritten

### Requirement: Fail-closed holdout enforcement in every training path

Every training consumer (including subsets, variants, fold retrains and
contamination runs) SHALL load the hash-verified frozen manifest and reject
training inputs from holdout farms or periods before fitting. Cycle consumers
SHALL check both bounds and reject missing or inverted bounds. A violation
SHALL raise `HoldoutViolationError` naming the offending pairs. Patch stores
MAY contain held-out observations for separate evaluation.

#### Scenario: Holdout leak aborts training

- **WHEN** a training Dataset would include a test-block field's cycle or a
  cycle that starts in or crosses into the held-out period
- **THEN** construction fails with `HoldoutViolationError` naming the
  (field, cycle) pairs, and no training starts

#### Scenario: Clean training passes

- **WHEN** a training Dataset contains only non-holdout farms and
  pre-2024 cycles
- **THEN** the assertion passes and the run records the manifest sha in
  its provenance
