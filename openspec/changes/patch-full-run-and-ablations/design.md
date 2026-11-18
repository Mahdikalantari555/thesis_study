## Design — patch-full-run-and-ablations

### Run order and pruning

Document §9's principle: climb the simplicity ladder, let each component
earn its place; prune by single-seed screening, add seeds only for
finalists. Order: scale-up base → E2 aux-weight → E6 channels → E4
covariates → E5 variants → E3 challenger (only if triggered) → sensor
offsets → final decision. Each ablation changes ONE pre-registered factor
(config hash per cell); everything runs through the unchanged severity
machinery + the extended three-shape protocol (`gradual-severity-shape`).

### Compute budgeting

The scale-up estimate decides the venue BEFORE launch (owner runs it):
if the full run exceeds the laptop budget at acceptable wall time, the
lab GPU / Colab path is used with checkpoint-and-resume to Drive/local —
the device portability requirement (AGENTS.md §7) makes the same command
valid on both. Benchmark fields are collected on the run venue actually
used and reported as such (no cross-venue MAC comparisons).

### Final-decision machinery

Pre-registered comparison set: {b0_calendar, b1, gru_ae_main, gru_pred
(if its gates passed), patch_pixelwise, patch_cnn_gru winner}. Paired
bootstrap over fields (not pixels) for every arm-vs-reference MDM
difference; three seeds; Wilson CIs on rates; prevalence reported. The
criterion's "held-out fields and periods" reading = the
`patch-generalization-suite` matrix columns, which run on the winner only.

### Config-driven variants (owner feature 19)

All ablation factors are flags on the existing scripts (no YAML layer
introduced mid-thesis — argparse is the repo convention; the full factor
matrix is enumerated in the pre-registered plan file, and every run's
manifest records the complete configuration + hashes, satisfying owner
feature 20 without a config-format migration).

### Risks

- Ablation count × seeds × shapes is the biggest compute item of the
  thesis so far — the pruning rule (single-seed screening) and the
  explicit "not on the critical path" mark on E5/S=16 keep it bounded;
  the plan file lists every planned run with its estimate BEFORE the
  first one launches.
- Weather covariates (E4 last step) add an ERA5 join dependency at patch
  granularity (field-level weather is already joined; per-field weather
  is uniform within the AOI's ERA5 cells — the join is per field centroid,
  recorded as such).
- The final criterion can fail honestly — that outcome is pre-written
  into the decision record (the floor itself as the finding), which
  protects the thesis timeline from invisible goalpost drift.
