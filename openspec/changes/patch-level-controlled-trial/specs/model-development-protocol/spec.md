## ADDED Requirements

### Requirement: Patch-level controlled PoC

The system SHALL first train `patch_cnn_gru` and its matched CNN-off
`patch_pixelwise` control on a preregistered hashed subset of locked train
fields. Evaluation SHALL use the locked dev subset and unchanged severity
protocol. Test-split data SHALL be read only by the locked final-test path.

#### Scenario: Matched architecture and evaluation

- **WHEN** the two patch arms are compared
- **THEN** both use the same objective and parameter budget (about 90k),
  per-location GRU, causal multi-horizon prediction k=1–3, masked auxiliary
  reconstruction, covariates and validity masks, without pooled latents.
  The CNN arm uses a 2D GroupNorm stem; the control has no spatial stem.
  Evaluation uses S1–S6 × {acute, persistent} × {ndvi, savi}, identical
  finding 18/22 injection sets, 5% cycle-FAR calibration, MDM80 with `>S6`
  censoring, per-pixel phenophase-binned σ, top-20% field aggregation, and
  the existing alarm rule.

#### Scenario: Owner runs training on own hardware

- **WHEN** the user launches train_patch.py on CPU or another machine
- **THEN** `--estimate-runtime` prints per-epoch, per-seed, total wall-time
  and disk BEFORE training, `--resume` restores model/optimizer/scheduler/
  RNG with a config-hash check, progress.jsonl and a final wall-time
  summary are written, with a checkpoint each epoch. Training uses device
  auto-selection and smoke mode;
  there is no agent-launched long job.

#### Scenario: Subset-first scale gate

- **WHEN** the PoC subset run finishes
- **THEN** all five preregistered gates must pass before any full-train run:
  G1 smoke plumbing, G2 overfit-one-batch, G3 finite MDM80 better than the best
  of {b1, gru_ae_main} with a paired field-bootstrap CI excluding zero (or
  finite MDM80 when both controls are censored), G4 improvement in MDM80 or
  localization AUPRC over patch_pixelwise for keeping the CNN, and G5
  estimate-before-run and ≤2× gru_ae_main compute. Record the verdict in
  finding 23 (Persian), label claims L1–L2, and apply the honest-negative
  protocol to every gate.

#### Scenario: Spatial value decided, not assumed

- **WHEN** patch_cnn_gru and patch_pixelwise are compared at equal budget
- **THEN** the CNN stem is kept only if MDM80 or pixel-localization AUPRC
  improves, and otherwise the pixel-wise variant continues with the
  negative recorded

### Requirement: Farm-boundary isolation of patch inputs and scores

Patch inputs and scores SHALL be farm-local. The stem SHALL see
`concat[X·M_in, M_in]` with `M_in = pixel_valid ∧ in_field`; no masked-out
observation or neighbouring farm SHALL influence an in-field score. Retain
GroupNorm without cross-field state and per-location temporal processing.

#### Scenario: Out-of-field pixels cannot influence an in-field score

- **WHEN** the values of pixels with `in_field = 0` are perturbed, or a
  synthetic neighbouring field is placed inside the patch's bounding box
- **THEN** the per-pixel scores of all in-field pixels are byte-identical,
  and a regression test enforces this for the stem, the multi-horizon heads
  and the R3a dilation variant. Enable the dilation variant only after this
  invariance test. GroupNorm avoids mixing batch statistics across fields,
  and the temporal unit has no spatial coupling. Adjacent farms remain
  separate even where their boundaries touch.

#### Scenario: The mask is the boundary

- **WHEN** a patch contains a neighbouring field's pixels inside the stored
  bounding box
- **THEN** those values never reach any model computation (masked, not
  zero-as-observed), and the in-field pixel count reported per patch equals
  the polygon mask's pixel count

#### Scenario: Identical-condition comparability

- **WHEN** the severity protocol runs for the patch arms and the existing
  arms
- **THEN** all arms share the same injections (same δ ladder, families,
  hashes), the same calibration rules and the same alarm machinery, and
  results are reported in one table with Wilson CIs and MDM80 censoring
  semantics

### Requirement: Causal patch preprocessing

The patch input path SHALL compute each acquisition-count covariate as
`log1p(n_obs) / log1p(255)` using only the current bin. It SHALL share the
normalization and covariate rules with patch scoring. Perturbations defined in
physical units SHALL be applied before normalization. New runs SHALL record the
input protocol and reject resume or scoring with incompatible artifacts.

#### Scenario: A later acquisition count changes

- **WHEN** only later bins are changed with frozen model and preprocessing
  artifacts kept fixed
- **THEN** earlier covariates and predictions are unchanged, including when
  the later acquisition count becomes the maximum over the cycle


#### Scenario: A new patch checkpoint is scored

- **WHEN** the locked dev sweep loads a patch checkpoint
- **THEN** it joins cycle IDs and bounds, checks the run's input protocol,
  seed, frozen splits, holdout and norm, and requires the matching residual
  scale table. Missing channel values do not become observed residuals.
  Legacy weights or residual scales cannot be relabelled as corrected runs.
