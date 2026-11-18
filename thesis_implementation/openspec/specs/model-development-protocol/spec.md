# model-development-protocol Specification

## Purpose
TBD - created by archiving change train-and-finalize-main-architecture. Update Purpose after archive.

## Requirements

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

The system SHALL evaluate every candidate on dev with: (primary) the **minimum detectable magnitude
(MDM80)** — the lowest severity level of the literature-grounded NDVI/SAVI table achieving detection
rate ≥ 0.80 at a 5 % cycle-level false-alarm rate — computed per duration family (acute, persistent)
and per index (NDVI, SAVI) with median detection delay in days, alongside the equivalent sweep for
`b1_phasez_causal`; (secondary) per-level detection rates with Wilson CIs at the levels
S1…S6 of the verified severity table, **event-level FAR** with consecutive-alarms declustering,
partial-cycle AUC-PR at 25/50/75 %, masked NRMSE, per-type and per-phase breakdown. Injection
magnitudes SHALL be the absolute index drops of the verified severity table (S1 −0.02 … S6 −0.40),
reported additionally as % of the field's own grand-growth median and as multiples of the
across-field MAD; the SAVI axis SHALL repeat the same absolute deltas as a separate family. The MDM
sweep SHALL use clean dev cycles disjoint from the threshold-calibration subset where dev size
permits, and SHALL record the evaluation-subset hash.

#### Scenario: Metric report
- **WHEN** `scripts/eval_dev.py` finishes for a run
- **THEN** it writes `reports/dev/<run_id>/metrics.json` with the MDM sweep, per-level detection
  rates, event-level FAR, all other metrics per seed and their mean and std, and appends a row to
  `reports/dev_log.csv`

#### Scenario: Severity provenance
- **WHEN** the severity table is loaded for injection
- **THEN** every level carries `source`, `verification` and `confidence` fields, and a level whose
  verification is `rejected` cannot be enabled by configuration

#### Scenario: Event declustering
- **WHEN** the alarm path of a clean or injected cycle contains consecutive or near-consecutive
  alarmed bins (gap ≤ 2 bins)
- **THEN** they count as ONE event for the event-level FAR, and alarms inside an
  already-hit injection window are not counted as false events

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

The target SHALL be evaluated on both axes: (a) the original margin — primary detection-rate metric
at least 0.05 above `b1_phasez_causal` with non-overlapping 3-seed ranges, evaluated at the
pre-registered levels where it is evaluable; and (b) `MDM80(main) ≤ MDM80(b1_phasez_causal)` on the
same sweep. If neither is met at plateau, the result SHALL be reported as a finding without changing
the metric, the severity table or the targets.

#### Scenario: Target missed
- **WHEN** the frozen model does not beat B1 by 0.05 (where evaluable) and its MDM80 is not lower
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

### Requirement: Forecast-unit probe (zero-training objective A/B)

The system SHALL provide a read-only probe that evaluates the existing
severity protocol with the model's prediction function replaced by
pre-registered, untrained causal forecasters (persistence, median of the last
≤3 observed bins, robust linear trend on the last 4 observed bins; B1 as the
reference arm), each calibrated ONLY on the clean dev calibration subset
(per-(bin,channel) q95; τ and k at the 5% cycle-level FAR target via the
production calibration rule) and evaluated on the independent evaluation
subset with the identical severity injections. The probe SHALL report per-cell
detection rates with Wilson CIs, event-level FAR, MDM80 per family × index
with censoring allowed, and the stage-1 onset residual in forecast-σ units
(reusing the signal-path decomposition), SHALL evaluate the pre-registered
decision rule verbatim (any untrained arm reaching a non-censored MDM80 ≤ S5
on persistent/ndvi within the FAR budget → the objective/unit remedy is
justified; all arms censored → honest negative), and SHALL NOT retrain, tune
forecaster definitions, change any threshold/model/checkpoint/platform
artifact, or read test cycles. Every claim SHALL be ladder rung L2 and use
the term "synthetic anomaly"; the scope SHALL be limited to the single-index
absolute-drop family.

#### Scenario: Arms compared under identical conditions

- **WHEN** the probe finishes for all arms
- **THEN** each (level × family × index) cell reports per-arm detection
  rates, delays, event-FAR and MDM80 computed on the same evaluation subset,
  same injections and same statistic pipeline, with full provenance
  (git sha, splits hash, subset hash, severity-table hash, wall time)

#### Scenario: Decision rule evaluated

- **WHEN** the sweep completes
- **THEN** the pre-registered rule is applied verbatim and its verdict
  (success with the measured target floor, or honest negative) is recorded
  in finding 21 without goalpost movement or arm tuning

#### Scenario: Probe changes nothing

- **WHEN** the probe runs
- **THEN** no model, threshold, severity table, checkpoint, sidecar or
  platform artifact is modified, no test split is read, and the frozen
  gru_ae_main sidecar is byte-identical before and after

### Requirement: Signal-path decomposition diagnostic

The system SHALL provide a read-only diagnostic that, for every injection of
the existing severity sweep on the dev evaluation subset, decomposes the
alarm-signal path into its stages — residual formation (LOO prediction vs
injected value at the onset bin, in σ units), causal offset-correction
subtraction at the onset, per-cell q95 normalization contribution against the
calibrated τ, trailing-window aggregation against τ — and quantifies
prediction absorption at post-onset bins by comparing the prediction against
the injected level and the counterfactual pre-injection level. The diagnostic
SHALL run for `gru_ae_main` and `b1_phasez_causal` on identical injections,
SHALL write per-cell medians + IQR and a stage-attribution decision matrix to
`reports/dev/<run_id>/diagnostic_<model>.json` with full provenance, and
SHALL NOT change any threshold, model, checkpoint, platform artifact or
calibrated target. Every resulting claim SHALL be ladder rung L2 and use the
term "synthetic anomaly"; the scope SHALL be limited to the single-index
absolute-drop family.

#### Scenario: Stage waterfall recorded
- **WHEN** the diagnostic finishes for an arm
- **THEN** each (level × family × index) cell reports the median onset
  residual in σ units, the median offset subtraction, the normalized
  contribution, the path-vs-τ ratio, and the stage-attribution decision
  matrix entry, and the stage-4 detection cross-checks the severity sweep's
  detection rate at the same cells

#### Scenario: Absorption quantified
- **WHEN** a persistent-family injection is diagnosed
- **THEN** the absorption ratio at post-onset bins is reported per cell
  (≈1 = prediction tracks the injected level; ≈0 = prediction stays at the
  counterfactual natural level), using the pre-injection tensor as the
  counterfactual

#### Scenario: Diagnostic changes nothing
- **WHEN** the diagnostic runs
- **THEN** no model, threshold, severity table, checkpoint, sidecar or
  platform artifact is modified, no test split is read, and the frozen
  gru_ae_main sidecar is byte-identical before and after

### Requirement: Severity-table provenance and honest labeling

The severity table SHALL be stored as configuration with per-level `source` (citation + DOI),
`verification` ∈ {`verified_full_text`, `verified_abstract`, `design_choice`, `rejected`} and
`confidence`; unverified third-party numbers SHALL NOT enter the table; the frozen sidecar SHALL
record the severity-table hash; every resulting claim SHALL be labeled ladder rung L2 and use the
term "synthetic anomaly", never "stress".

#### Scenario: Unverified claim excluded
- **WHEN** a proposal adds a severity level citing a source that cannot be verified against a
  primary source
- **THEN** the review records it as excluded in the verification document and the level is not added

### Requirement: Normal-bank novelty scoring arm

The system SHALL provide a dev-only scoring arm that computes a latent novelty score for each
observed bin as the distance of the frozen `gru_ae_main` encoder embedding to a normal bank built
exclusively from train-split cycles, comparable only against bank bins with the same
band-mask-signature class (pooled fallback with a recorded flag where a class is too sparse), fused
with the existing channel-max reconstruction statistic and calibrated with the SAME 5 %
cycle-level FAR rule and the SAME severity sweep as the literature-grounded protocol. The arm SHALL
be evaluated against `recon_only` and `b1_phasez_causal` under identical splits, metrics and seeds
protocol; the frozen checkpoint sidecar and the platform payload SHALL NOT change unless a
follow-up freeze change explicitly replaces them.

#### Scenario: Bank provenance
- **WHEN** the normal bank is built
- **THEN** every bank entry records its cycle id and split, a unit test asserts all entries come
  from the `train` split, and a `bank.json` sidecar stores the split hash, encoder checkpoint hash
  and bank statistics

#### Scenario: Mask-class comparison
- **WHEN** a dev bin with a given observed-band mask signature is scored
- **THEN** its distance is computed only against bank bins of the same signature class (or the
  recorded pooled fallback), and fully-unobserved bins score `absent` rather than 0

#### Scenario: Fusion recalibration
- **WHEN** a fusion variant (max or weighted sum) is evaluated
- **THEN** its alarm threshold is re-calibrated on clean cycles for that variant so the 5 %
  cycle-level FAR budget holds by construction, and the calibration hash is stored with the result

#### Scenario: No platform drift
- **WHEN** this change completes without an adoption decision
- **THEN** `checkpoints/gru_ae_main.json`, the registry versions and the exported payload are
  byte-identical to their pre-change state
