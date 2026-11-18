# Tasks — patch-xai-attribution

## 1. Attribution modules (TDD-first)

- [x] 1.1 Unit tests: band occlusion (median baseline, Δ map shape/values
      on a synthetic checkpoint), temporal occlusion, gradient×input vs
      finite-difference gradient agreement on a tiny case.
- [x] 1.2 `src/ssl_anomaly/xai/patch_attribution.py`: the four methods +
      stage aggregation (SUGARCANE_STAGE_BINS reuse); artifact writers
      (band table, temporal table, spatial arrays).
- [x] 1.3 Faithfulness adapter: deletion/insertion AUC on the patch grid,
      randomization sanity, sign concordance — adapted from
      `xai/faithfulness.py`; pre-registered sample definition (50 events,
      stratified by family/severity, hash-recorded).

## 2. Runs (eval-only, user-executed with estimates)

- [ ] 2.1 Agent smoke on a tiny event set; review; hand over the sampled
      attribution runs (natural alarms from gated checkpoints).
- [ ] 2.2 Attribution artifacts per event + summary tables under reports/.

## 3. Deliverable

- [ ] 3.1 Persian finding (persian-writing skill): which bands/windows/
      spatial patterns drive the scores, faithfulness results (including
      failures), the synthetic-vs-natural framing, L2 wording only.

## Implementation notes (data-free half)

`xai/patch_attribution.py`:

- **1.1/1.2** `band_occlusion` (per-band median baseline — occluding to zero
  would create an impossible reflectance), `temporal_occlusion` and
  `spatial_occlusion` (both with `baseline ∈ {zero, median}` and a documented
  reason: a per-bin median cancels a bin-wise signal, so windows/blocks default
  to zero in the model's standardized units), `spatial_pattern_summary`
  (concentration at the top-20 %, Gini, and `n_effective` = 1/Σp² so "one
  bright pixel" is distinguishable from "a coherent patch"), and
  `gradient_x_input`, which returns the GRADIENT and the grad×input
  ATTRIBUTION separately.
- **1.3** `gradient_finite_difference_agreement` compares the GRADIENT (not the
  attribution — they differ by the input factor, and the tests pin both against
  the closed form 2x·s/N and 2x²·s/N). Probe sampling defaults to informative
  cells, because a uniform sample can land entirely on channels the score does
  not read, leaving both sides constant zero and the check undefined; the
  `probe="uniform"` strict variant is kept.
- `deletion_insertion_curves` on the patch grid with the random-order control,
  and an inverted attribution must LOSE its advantage (tested).
- `attribution_sample_plan`: stratified by family × severity, seeded and
  hash-recorded, so the sample cannot be revised after seeing results.
- Stage aggregation reuses `SUGARCANE_STAGE_BINS`; `band_table` /
  `temporal_table` are the artifact writers.

37 tests in `test_patch_attribution.py`. **Still needs the data:** 2.1/2.2
(smoke + the sampled attribution runs on natural alarms).
