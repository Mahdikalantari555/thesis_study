# Proposal: Data and Phenology Readiness (`data-and-phenology-readiness`)

## Why

Before `train-and-finalize-main-architecture` starts, two things decide whether its results mean anything.

1. **Cycle segmentation quality.** Every model input is aligned by days since harvest (DSH). A harvest detected on the wrong date, a cycle split in two, or two cycles merged into one each shifts the phase bins, so the model sees a "phenology anomaly" that is a segmentation error. Nobody has yet measured how often this happens on real490.
2. **Method choices that rest on literature, not habit.** These are:
   - which perturbations are realistic stress signatures for sugarcane
   - how automatic phenology / season extraction is done in the literature
   - how irregular, cloud-gapped satellite time series are represented for self-supervised learning

   The user's long-term vision is a crop-agnostic product, so the review also records which methods would generalise. No crop-agnostic code is written now.

## What Changes

- **Literature review, inside this change**:
  - automatic phenology and season extraction
  - time-axis representation for SSL on irregular satellite time series
  - realistic sugarcane stress signatures for perturbation design
  - short check of SSL architectures for irregular, gappy series
- **Cycle audit**:
  - stratified random sample of real490 cycles, reviewed visually on the platform and with plots
  - an error taxonomy and an estimated segmentation error rate
  - automatic sanity flags (implausible length, missing harvest drop, overlapping cycles)
- **Data quality check**: QA/cloud masking, LST physical range, `valid_frac`, per-year observation density.
- **Decision record**: keep or change the DSH 36×15-day input, the segmentation parameters, and the interim perturbation set. Each decision is written into the `train-and-finalize-main-architecture` design before its code starts.
- **Ratoon vs plant cane**: not modelled separately. If cycle type can be inferred (or the registry has it), errors are reported per type; otherwise cycle length is used as a stand-in.
- **Planting/harvest records**: optional. If the user obtains them for some fields, they are used only to measure segmentation error. Their absence does not block anything.

## Capabilities

### New Capabilities
- `data-readiness`: documented cycle-segmentation error estimate, data-quality report, and literature-backed decisions that gate model training.

## Impact

- New docs:
  - `docs/findings/13_literature_phenology_and_perturbations.md`
  - `docs/findings/14_cycle_audit.md`
  - `docs/findings/14_stage_conditioned_thresholds.md`
  - `docs/methods_explained.md` (new sections)
- New scripts (small, agent-runnable):
  - `scripts/audit_cycles.py` (sampling, sanity flags, plots)
  - `scripts/data_quality_report.py`
  - `scripts/stage_conditioned_anomaly.py` (stage-conditioned thresholds + npphen confidence envelope)
- `reports/cycle_audit/` (plots, CSV of reviewed cycles), `reports/data_quality.json`, `reports/stage_conditioned_anomaly/` (per-bin anomaly results)
- `openspec/changes/train-and-finalize-main-architecture/design.md` (decisions D2/D3/D5/D6 updated)
- `todo.md`

## Out of Scope

- Crop-agnostic abstractions in code (vision only, `docs/vision.md` item 8).
- Re-segmenting cycles or changing the training data, unless the audit shows a blocking error rate (threshold in design). If it does, a separate fix is proposed to the user first.
- Model training of any kind.
