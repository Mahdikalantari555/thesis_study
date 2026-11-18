# Tasks — patch-level-controlled-trial

## 1. Model + trainer (TDD-first)

- [x] 1.1 Causality and masking tests: x̂_{t+k} depends only on bins ≤ t
      (perturbing future bins changes nothing); state-carry test (GRU state
      unchanged where pixel_valid = 0); NaN safety; GroupNorm regression
      test on degenerate masked batches (no BatchNorm anywhere).
- [x] 1.1b Farm-boundary isolation tests (spec "Farm-boundary isolation of
      patch inputs and scores"): stem input is `concat[X·M_in, M_in]` with
      `M_in = pixel_valid ∧ in_field` (asserted on a patch containing a
      neighbouring field inside the bbox); perturbing out-of-field values
      leaves every in-field per-pixel score byte-identical; the same for
      the R3a dilation variant; in-field pixel count equals the polygon
      mask's count.
- [x] 1.2 `src/ssl_anomaly/models/patch_cnn_gru.py`: stem + per-location
      GRU + k=1–3 prediction heads + masked-recon aux head; param-count
      assertion ≈90k ±20% with a hard ≤500k gate; CNN-off flag =
      `patch_pixelwise` (same interface, no stem).
- [x] 1.3 `src/ssl_anomaly/train/patch_data.py`: Dataset over patches.zarr
      (sample = field-cycle), frozen normalization read, covariate builder
      (sin/cos DOY, cycle age, days-since-last-valid, log1p n_obs, sensor
      one-hot L8/L9), NaN-as-absent masking; holdout filter + fail-closed
      assertion via the shared `monitor/holdout.py` helper
      (`training-holdout-invariant`: holdout farms/dates never reach
      training, even though the store contains them); collate tests.
- [x] 1.4 `scripts/train_patch.py`: hybrid objective (w = 1, 0.5, 0.25 +
      0.3 aux), 8-bin burn-in, trimmed top-5% after 10-epoch warm-up,
      AdamW/cosine/clip; tqdm + progress.jsonl + final wall-time summary;
      --seed/--epochs/--batch-size/--max-fields/--smoke/--resume/
      --estimate-runtime/--device auto-select; per-epoch checkpoint with
      RNG states + config-hash check; run manifest with seeds, data_source,
      split hashes, git sha, device, wall time (AGENTS.md §7 report fields).

## 2. Scoring + eval integration

- [x] 2.1 Patch σ tables: 1.4826 × MAD of dev residuals per (channel,
      2-bin phenophase group, sensor); fit helper and frozen table hash tested
      in isolation. The real table must use calibration, not evaluation or test
      residuals, and must be produced for the corrected checkpoint under 3.x.
- [x] 2.2 `PatchDeepScorer` adapter: per-pixel z² → top-20% aggregation →
      (N, 36, C) interface-compatible with `DeepCausalScorer.loo_batch`;
      alarm machinery (τ/k/q95, 5% FAR) untouched; per-pixel score maps
      exported for localization metrics.
- [x] 2.3 Patch-tensor injection applier in `monitor/perturbations.py`:
      same S1–S6 ladder × {acute, persistent} × {ndvi, savi}, footprint
      1.0 (protocol) / 0.3 (localization probe) — parameterised so the
      extent sweep {0.1, 0.3, 0.6, 1.0} of
      `compare-spatial-representation-strategies` needs no code change; a
      `spatial="white"` diagnostic mode (random in-field pixel subset,
      seed-fixed, same mean footprint) used ONLY by that change's noise
      null and excluded from every severity gate; the existing
      sum-preserving red/nir SAVI solver per pixel; injection-hash equality
      test against the field-level protocol sets.
- [ ] 2.4 eval_dev.py: scorer choices patch_cnn_gru / patch_pixelwise;
      stable cycle join, artifact handoff and MDM80 report exercised with a
      fixture. Full severity/FAR parity, AUPRC, onset-relative delay and
      pixel-localization AUPRC (footprint-0.3 probe) still require completion
      and verification; do not use the plumbing smoke as a PoC verdict.

The input, training and scoring components have fixture coverage:
`tests/unit/test_patch_model.py` (20), `test_patch_data.py` (18),
`test_patch_scores.py` (21), `test_patch_perturbations.py` (34),
`test_train_patch_cli.py` (9, including a real synthetic-store smoke run).

## 3. Subset PoC run (user-executed)

- [ ] 3.1 Pre-register the subset manifest (hashed; default two KMeans
      train blocks ≈100 fields) and freeze the gates in a
      trial_gates-style module BEFORE any training run.
- [ ] 3.2 Agent executes `--smoke` + `--estimate-runtime` +
      overfit-one-batch check; reviews produced files (not console only);
      hands exact user commands (conda env geo, cwd, expected wall time,
      output paths).
- [ ] 3.3 USER runs: subset training seeds {13, 42, 2026} + severity eval.
- [ ] 3.4 Agent reviews produced reports (metrics JSONs, dev_log rows) and
      completes every report field (params, wall time, device, git sha,
      data_source, splits sha, hashes) — missing fields are defects, not
      "done" (AGENTS.md §7).

## 4. Gates + verdict

- [ ] 4.1 Evaluate gates verbatim: G1 smoke · G2 overfit-one-batch (L1) ·
      G3 MDM80 finite AND better than best of {b1, gru_ae_main} (paired
      bootstrap over fields, CI excludes zero; both arms censored ⇒ success
      = any finite MDM80) · G4 CNN kept only if it beats patch_pixelwise on
      MDM80 or localization AUPRC · G5 estimate before run + ≤2×
      gru_ae_main compute. Honest-negative protocol; no goalpost movement
      after the first training run starts.
- [ ] 4.2 Finding 23 (Persian, persian-writing skill): patch-level PoC
      verdict with all gate numbers, n, date ranges, seeds, device, hashes
      and explicit L1–L2 rung labelling; scale-up decision (full train run)
      only if G1–G5 pass; otherwise the floor result is recorded verbatim.

### 2.2 / 2.4 notes (data-free half complete)

`PatchDeepScorer` (2.2) was ticked but absent — it is now written and tested
(42 tests in `test_patch_scores.py`, 21 new):

- `loo_batch` returns the pipeline's exact pair, `scores (N,T)` from
  top-20 % in-field aggregation of per-pixel z² and `pred_z (N,T,C)`.
- The patch model is causal by construction, so there is no LOO withholding;
  the method name is kept for interface compatibility and says why.
- Masking is `pixel_valid ∧ in_field`, resolved from three explicit layouts
  (shared / per-sample / per-field + `idx`) instead of relying on broadcast;
  a per-field mask without `idx` raises rather than silently using field 0.
- `doy_batch` is NOT reinterpreted as covariates: a covariate model must be
  given `covariates=` explicitly and otherwise raises.
- The mask-application bug found while testing is documented in place:
  `field_paths`' `in_field` argument cannot express a per-(sample, bin) mask,
  so out-of-domain pixels are NaN'd first and the aggregation domain is
  "everything not excluded".

**Task 2.4 wiring** — `PatchArmScorer` + `monitor/patch_eval.py` (15 tests in
`test_patch_eval.py`, including a real end-to-end run of
`run_patch_severity_protocol` on a synthetic store):

- **Why an adapter at all:** the patch path (top-20 % mean per-pixel z²) and
  the field path (cell-q95-normalized trailing channel max) have no common
  scale, so a shared τ would be an artefact of units. The patch arm is scored
  through a **one-sided empirical p-value against the CALIBRATION subset's
  clean paths**, p = (1 + #{ref ≥ own}) / (n + 1) per bin — calibrated by
  construction, monotone, bounded away from 0, and locally anchored.
- **The reference is the calibration subset only.** Using the evaluation
  subset as its own reference would make every p-value a rank within the set
  being judged.
- **The join is `(field_id, cycle_id)`** (`<field>:<cycle_id>` keys), never row
  position; a cycle absent from the store aborts the run rather than changing
  the evaluation population between arms.
- Injections happen in the PATCH tensor via `patch_perturbations` with the
  severity table's δ and the frozen persistent duration; the injection hash
  records are carried into the cell result.
- Artifacts may be in the named `--patch-run` directory, or supplied as the
  trainer's `--patch-checkpoint` with its saved `norm_stats.json` and explicit
  `--patch-sigma`. The seed, architecture and input hashes must agree.
  This verifies the handoff; it does not replace the real calibration,
  matched severity/FAR comparison or review for 3.4/4.x.

Still data-blocked: 3.x (the subset PoC run), 4.1/4.2 (gate evaluation and the
Persian finding).

## Audit follow-up

- [x] A.1 Use and record the causal patch input protocol in training and scoring;
      test prefix invariance through the model and reject incompatible resumes.
- [x] A.2 Verify on a synthetic fixture the same-run checkpoint/norm/scoring artifact handoff. Keep
      the real residual-scale calibration, controlled comparison and report
      review in the owner-run PoC; do not reuse σ from legacy inputs.
