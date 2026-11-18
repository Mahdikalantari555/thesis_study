# Tasks — predictive-ssl-controlled-trial

## 1. Training arm `gru_pred` (TDD-first)

- [ ] 1.1 One-step objective tests: prediction at bin o depends ONLY on
      bins < o (causality invariant test); masked loss over observed
      (bin, channel) pairs; NaN/non-finite safety; loss choice recorded
      BEFORE training (no post-hoc switching).
- [ ] 1.2 `scripts/train_main.py`: add the `gru_pred` arm — SAME trunk,
      inputs (8 channels + DOY), frozen normalization, budget (≤500k params)
      as `gru_ae_main`; objective = causal one-step-ahead masked prediction;
      train split only; `--resume`, progress.jsonl, wall-time summary.
      No existing model/arm behavior changes.
- [ ] 1.3 Train seeds {13, 42, 2026} — USER-RUN (agent hands exact commands
      with conda env, cwd, expected wall time ≤15 min/seed, output paths;
      agent verifies the smoke first and reviews produced files after).
- [ ] 1.4 `scripts/freeze_main_model.py`: extend freeze/final-test to the
      `gru_pred` arm (same sidecar schema: τ, k, per-bin q95, frozen seed,
      hashes); the one locked `--final-test` run remains the ONLY reader of
      test cycles.

## 2. Four-part evaluation (owner's design, verbatim)

- [ ] 2.1 **Part A — natural data:** clean cycle-FAR + event-FAR (POT gap ≤2)
      per arm at its calibrated τ; per-field clean-score distribution;
      temporal stability. Gate: new arm must not exceed the 5% cycle-FAR
      budget and must not concentrate alarms in a few fields.
- [ ] 2.2 **Part B — severity protocol unchanged:** `scripts/eval_dev.py`
      support for the `gru_pred` arm; the finding-18 sweep verbatim
      (S1–S6 × {acute,persistent} × {ndvi,savi}, identical injections,
      rounds=2, eval subset hash `6186edf8a06f82d3`): per-cell detection +
      Wilson CIs, event-FAR, MDM80 (">S6" censoring allowed), AUPRC per
      family with prevalence reported, median detection delay; B1 +
      gru_ae_main recomputed in the SAME run on the same injections.
- [ ] 2.3 **Part C — absorption experiment:** `diagnostics.decompose_injection`
      with the predictive scorer on persistent-family injections: error at
      the three checkpoints (before onset / first step after / several steps
      after) + the absorption ratio A vs gru_ae_main's measured
      α ≈ 0.38–0.50; honest pre-registered caveat for adaptive absorption.
- [ ] 2.4 **Part D — independent indicators:** data-availability check FIRST
      (CWSI_ET/CWSI_LST, ETa/ETrF, TVDI from existing per-scene LST/NDVI
      field stats; anything unavailable = `absent`, never synthesized);
      agreement of each arm's flagged (field, bin) events with the available
      indicators on natural dev cycles, with CIs; dependence structure
      (LST/NDVI shared inputs) stated in the output; corroborating proxy
      evidence only — never "stress" proof, never an L4 claim.

## 3. Decision + findings

- [ ] 3.1 Evaluate the pre-registered decision gates verbatim (FAR budget /
      synthetic detection vs gru_ae_main / persistent-error persistence /
      proxy agreement / generalization across fields, cycles, seeds) and
      record the verdict per gate — no goalpost movement, no spec-target
      edits after the run starts.
- [ ] 3.2 Finding 22 (`docs/findings/22_predictive_ssl_trial.md`, Persian,
      persian-writing skill): the four-part results, gate table, decision
      (main path vs path B), scope limits; + 00_index row. Finding 21
      (companion `forecast-unit-probe`) cross-referenced as the zero-training
      upper-bound estimate.
- [ ] 3.3 `todo.md` §D updated with the trial's outcome and the resulting
      path decision.

## 4. Gates

- [ ] 4.1 Unit tests green (new one-step objective + existing suites);
      smoke green before any training/evaluation hand-over.
- [ ] 4.2 `openspec validate predictive-ssl-controlled-trial`; no platform
      impact; conventional commits (one logical change per commit); training
      commands handed to the user, never launched by the agent.
