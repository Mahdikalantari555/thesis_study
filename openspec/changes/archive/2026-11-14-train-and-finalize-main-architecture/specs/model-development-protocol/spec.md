## ADDED Requirements

### Requirement: Locked split manifest

The system SHALL build the train/dev/test/monitoring-only split once from the real490 archive and store it in `data/processed/splits_locked.json` with cycle ids, SHA-256 of the cycle file, the manifest hash, git SHA and creation date. Test SHALL contain all uncensored cycles starting on or after 2024-01-01 plus all cycles of one spatially contiguous field block; train cycles SHALL end before 2024-01-01.

#### Scenario: No overlap
- **WHEN** the split manifest is built
- **THEN** a unit test asserts train, dev, test and monitoring-only are pairwise disjoint by cycle id and test-block fields appear in no other split

#### Scenario: Manifest drift
- **WHEN** a training or evaluation script finds a manifest or cycle-file hash different from the recorded one
- **THEN** it exits with an error and does not train or evaluate

### Requirement: Test isolation during development

The system SHALL NOT load test cycles in any training, tuning, threshold-calibration or dev-evaluation code path. Only `scripts/freeze_main_model.py --final-test` MAY read them.

#### Scenario: Accidental test access
- **WHEN** a dev script requests cycles of split `test`
- **THEN** the loader raises an error naming the allowed entry point

### Requirement: Mask-aware inputs and train-only normalization

Model inputs SHALL carry an observation mask per band; missing values SHALL NOT be treated as observed zeros, and reconstruction loss SHALL be computed only on observed entries. Normalization statistics SHALL be computed from train cycles only and stored with the checkpoint.

#### Scenario: Missing bin
- **WHEN** a bin has no observation for a band
- **THEN** its mask is 0 and it contributes nothing to the loss or to the score

### Requirement: Fixed development metric

The system SHALL evaluate every candidate on dev with: (primary) detection rate at a 5 % cycle-level false-alarm rate on injected perturbations at 1×MAD with median detection delay in days; (secondary) partial-cycle AUC-PR at 25/50/75 %, masked NRMSE, severity curve 0.5–2×MAD, per-type and per-phase breakdown. Perturbation severity SHALL be scaled by the train MAD of the affected band and phase bin.

#### Scenario: Metric report
- **WHEN** `scripts/eval_dev.py` finishes for a run
- **THEN** it writes `reports/dev/<run_id>/metrics.json` with all metrics per seed and their mean and std, and appends a row to `reports/dev_log.csv`

### Requirement: Non-circular development

Model selection, early stopping, threshold calibration and hyper-parameter choice SHALL NOT use CWSI, ETa, `y_stress`, yield or test data. Early stopping SHALL use dev masked reconstruction loss.

#### Scenario: Forbidden target
- **WHEN** a config or script references CWSI, ETa, `y_stress` or yield as a selection criterion in the development phase
- **THEN** a unit test fails

### Requirement: Seeds, comparison and plateau

Every configuration SHALL be trained with seeds `[13, 42, 2026]`. Candidate architectures SHALL be compared at parameter counts within ±20 % of each other; if their primary metric differs by less than the seed spread, the simpler model SHALL be chosen. The model SHALL be frozen after three consecutive single-change experiments each improving the primary metric by less than max(0.01, seed std).

#### Scenario: Plateau reached
- **WHEN** the last three rows of `dev_log.csv` for the main model each improve by less than the plateau threshold
- **THEN** `freeze_main_model.py` may be run and records the frozen config, checkpoint and sidecar

### Requirement: Target and honest outcome

The target SHALL be a primary metric at least 0.05 above `b1_phasez_causal` with non-overlapping 3-seed ranges. If the target is not met at plateau, the result SHALL be reported as a finding without changing the metric or the target.

#### Scenario: Target missed
- **WHEN** the frozen model does not beat B1 by 0.05
- **THEN** the findings document states this explicitly with the numbers and the ladder rung

### Requirement: Compute budget and execution rules

Training SHALL run on CPU within 15 minutes per seed for models up to 500 k parameters and SHALL auto-select CUDA when available. Training SHALL show progress (epoch, losses, ETA), write `progress.jsonl`, and support `--resume`. A `--smoke` mode SHALL finish in under 2 minutes. AI agents SHALL run only smoke and unit tests; full runs are handed to the user as exact commands.

#### Scenario: Smoke run
- **WHEN** `python scripts/train_main.py --model masked_transformer --smoke` is run
- **THEN** it completes in under 2 minutes on CPU and writes a checkpoint and a progress file

### Requirement: Incremental-training placeholder

The system SHALL expose `ssl_anomaly.train.incremental.fine_tune` as a documented stub raising `NotImplementedError`.

#### Scenario: Stub call
- **WHEN** `fine_tune` is called
- **THEN** it raises `NotImplementedError` with a message pointing to `docs/vision.md`
