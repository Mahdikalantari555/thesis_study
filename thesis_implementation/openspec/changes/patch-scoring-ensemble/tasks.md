# Tasks — patch-scoring-ensemble

## 1. Component scores (TDD-first)

- [ ] 1.1 Unit tests: s_rec masked-mode determinism (seed-fixed 8 repeats),
      NaN discipline on invalid pixel-bins; s_lat low-rank Mahalanobis
      fitted on train-only latents (leakage test: dev perturbation does not
      change the frozen Gaussian); s_hyb rank statistics dev-only.
- [ ] 1.2 `src/ssl_anomaly/monitor/patch_scores.py`: component implementations
      reading the PoC scorer outputs + frozen σ tables; per-pixel maps AND
      (N, 36, C) field tensors per component.
- [x] 1.3 Persistence: CUSUM + EWMA in `monitor/scoring.py` (or sibling),
      κ/h calibration at 1%/5% field-cycle FAR on validation only; unit
      test: zero alarms on clean dev at the calibrated budget.
      DONE in `monitor/patch_scores.py`: `cusum_path` (state carries through
      unobserved bins — no evidence is not evidence of normality), `ewma_path`,
      `calibrate_cusum_h` (same contract as `calibrate_threshold`, so the two
      rules are comparable at equal FAR). 21 tests in `test_patch_scores.py`.

## 2. Decisions C1 / C2 / M3

- [ ] 2.1 C1 script: phenophase-binned residual MAD vs across-field MAD
      conversion table per channel on the 490-field archive; decision
      recorded in findings + model card; severity-table config updated
      accordingly (config-only change).
- [ ] 2.2 C2: SHAZAM per-DOY climatology threshold (circular DOY regression,
      mean + 1.64 SD) as an alternative rule; comparison at equal 5% FAR on
      dev; exactly one rule frozen; report under reports/.
- [ ] 2.3 M3: POT declustering (gap ≤ 2) event-FAR as a required column in
      every arm report; retrofit to the existing report writers.

## 2b. Scoring basis (delegated from farm-local-anomaly-scoring)

- [x] 2.4 Declare the basis tier of every component (`s_pred`, `s_rec`,
      `s_lat` = locally anchored; `s_hyb`, `z_f(t)`, common-mode subtraction
      = population-ranked) and add `basis` as an axis of the 3.1 selection
      matrix; unit test that a component without a declared basis fails the
      report build.
      DONE: `patch_scores.component_basis()` + `require_basis()`. The declared
      default set is locally anchored only; `s_hyb`, `z_f(t)`, common-mode
      subtraction and indicator z are population-ranked and must be named
      explicitly.
- [ ] 2.5 Enumeration guard: `s_hyb` / `z_f(t)` may only enter the default
      score if the farm-local alternatives lose under the pre-registered
      rule — the comparison is recorded, never implicit.
- [ ] 2.6 Per-field σ arm (`--sigma-basis farmlocal|shrunk`) evaluation is
      owned by `farm-local-anomaly-scoring`; this change only consumes its
      `basis` labels in the reports.

## 3. Selection + reports

- [ ] 3.1 Pre-registered selection matrix (components × aggregation rules ×
      temporal shapes) decided on synthetic validation + dev FAR only.
- [ ] 3.2 Reports: per-arm component table with Wilson CIs, prevalence,
      MDM per component/hybrid, delay for persistence, hashes (σ tables,
      Gaussians, κ/h, chosen rule); dev_log rows complete (AGENTS.md §7).
- [ ] 3.3 Persian finding (persian-writing skill): which components earn
      their place, the C1/C2 decisions, and the honest negatives — every
      claim ladder rung L1–L2.
