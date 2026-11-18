# Tasks — farm-local-anomaly-scoring

## 1. Basis classification + independence tests (TDD-first)

- [x] 1.1 Arm/component basis registry: a single table declaring the basis
      tier (strictly local / locally anchored / population-ranked) for
      `b0_*`, `b1`, `b3`, `gru_ae_main`, `gru_pred`, `patch_cnn_gru`,
      `patch_pixelwise`, `R0.5` arms, and the components `s_pred`, `s_rec`,
      `s_lat`, `s_hyb`, `z_f(t)`, common-mode subtraction, indicator z;
      unit test that every arm name used in `eval_dev.py` has a declaration
      and that a missing declaration fails the report build.
- [x] 1.2 Independence tests: (a) other-farm perturbation invariance
      (bitwise), (b) field-id permutation invariance, (c) no cross-field
      read (instrumented spy with a whitelist of frozen pooled constants);
      a synthetic population-ranked component is planted to prove the tests
      actually FAIL for it (negative controls).
- [ ] 1.3 Report writers: `basis` column in every arm table
      (`eval_dev.py` reports, `reports/dev/<run>/`); a population-ranked
      component without a stated cross-farm read fails the build.

## 2. Per-field scale tables + arm

- [x] 2.1 Frozen artifact builder: per-field per-pixel and per-field
      `1.4826 × MAD` of clean dev residuals, shrink weights
      `w_f = n_f/(n_f + κ_σ)`, floor percentile, history tier per farm;
      provenance (residual source run ids, git sha, splits sha, own sha256);
      rebuild requires `--force <reason>`. Unit tests: shrinkage identity
      (`n_f = 0` ⇒ pooled σ), floor behaviour, no injected/test data
      touched, deterministic hashes.
- [ ] 2.2 Scoring integration: `σ` basis switch
      (`--sigma-basis {pooled,farmlocal,shrunk}`) in the patch scorer and
      the `b1`/`b0` paths; τ re-calibrated inside the same 5% cycle-FAR
      budget on clean dev; unit test that `--sigma-basis pooled` reproduces
      the current numbers byte-identically (regression guard).
- [x] 2.3 Pre-register the comparison rule in a gates module BEFORE any
      run: adopt farm-local only on MDM80 improvement with paired-bootstrap
      CI over fields excluding zero, FAR budget met, and no increase in
      alarm concentration; no goalpost movement.
- [ ] 2.4 Agent smoke on a tiny set of farms (both bases, fallback tiers,
      FAR accounting) — no retraining, residuals frozen; hand the user the
      exact evaluation commands.

## 3. Strata (ratoon / variety)

- [ ] 3.1 `stratum_level` flag on the σ tables
      (`phenophase` / `×ratoon` / `×ratoon×variety`) reusing
      `build_stratum_table` columns and the existing min-n fallback; unit
      tests on fallback coverage and on the untouched default (current
      numbers reproduced).
- [ ] 3.2 Report MDM80 + FAR-achieved per stratum level with coverage per
      stratum; record the decision for the frozen configuration.

## 4. Farm-level anomaly summary

- [x] 4.1 Summary-record writer: per alarm
      `{field_id, cycle, first_alarm_bin, severity_level, persistence_len,
      affected_pixels, affected_area_frac, n_components, max_component_px,
      max_component_ha, centroid_xy, score, basis_tier, phi_bin}` written as
      per-run JSONL; connected components computed on the in-field mask only
      (unit test: an alarm touching two fields counts components within one
      field only); platform payload asserted unchanged.
- [x] 4.2 Summary table in the run report: distribution of affected area
      fraction, component counts and extents by severity and phenophase.

## 5. Verdict

- [ ] 5.1 Apply the pre-registered rule verbatim; both bases reported at the
      same FAR with FAR-achieved, MDM80, crossing counts and alarm
      concentration; tier counts stated.
- [ ] 5.2 Hand the decision to `patch-full-run-and-ablations` (the frozen
      final configuration's basis) and label the rows consumed by
      `compare-spatial-representation-strategies`.
- [ ] 5.3 Persian finding (persian-writing skill): is the farm's own history
      a better comparison basis than the population at equal FAR — with the
      honest negative fully written if it is not; the 223/370 history
      limitation and the tier counts stated plainly; L2 rung labelling;
      `00_index.md` row; `todo.md` §D updated.

## Implementation notes (data-free half)

`monitor/farm_local.py`:

- **1.1** `ARM_BASIS` declares all 11 arms (`b0_calendar`/`b1`/`b3`,
  `gru_ae_main`/`gru_pred`, `patch_cnn_gru`/`patch_pixelwise`, the four R0.5
  arms) and all components; `require_declarations` fails a report using an
  undeclared name; `report_header` returns the bases plus the CROSS-FARM READ
  each population-ranked component performs, so locality is visible.
- **1.2** `other_farm_perturbation_is_invariant`, `field_id_permutation_is_invariant`
  (the scorer takes `(field_id, values)` — omitting the id would make the test
  unable to see id-dependence) and `no_cross_field_read` (an access record with
  a pooled-constant whitelist). Both have NEGATIVE CONTROLS in the tests:
  `planted_population_ranked_component` and an id-keyed scorer must FAIL them.
- **2.1** `build_field_sigma_table` with `basis ∈ {pooled, farmlocal, shrunk}`,
  `w_f = n_f/(n_f+κ)` (κ = 10), the floor percentile, history tiers, a
  self-hash and provenance. `pooled` reproduces today's numbers (the regression
  guard the task requires); `n_f = 0` is exactly pooled.
- **2.3** `ADOPTION_RULE` + `apply_adoption_rule` (three criteria, applied
  verbatim; the failure default is "pooled stays frozen").
- **4.1/4.2** `connected_components` (4-connected, area in ha, centroid),
  `alarm_summary_record` (every required field; components computed WITHIN one
  field — the two-fields → two-components case is tested) and
  `alarm_summary_table` (by severity and phenophase).

**Still needs the data:** 1.3 (report-writer wiring into `eval_dev`), 2.2
(scoring integration + τ re-calibration), 2.4 (smoke on real farms), 3.x
(strata), 5.x (verdict). 39 tests in `test_farm_local.py`.
