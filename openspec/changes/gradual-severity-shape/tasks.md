# Tasks — gradual-severity-shape

## 1. Injection machinery (TDD-first)

- [x] 1.1 Unit tests: ramp profile δ·min(1, t/D) per bin for D∈{3,4,6};
      onset sampled so the full ramp fits inside the cycle; partial-δ SAVI
      solver correctness; field-level AND patch-tensor appliers produce
      identical per-bin δ profiles.
- [x] 1.2 `monitor/perturbations.py` + `monitor/severity_table.py`: gradual
      family registration, new injection-set hashes in the sidecar;
      acute/persistent hashes asserted unchanged (regression test).
- [x] 1.2b Secondary shapes: peak-magnitude + plateau-move appliers and
      failure-to-recover / slow-recovery appliers (parameters per-injection
      recorded; clipped to admitted bins; covariate consistency tests);
      secondary diagnostic columns in the report writers; regression test
      that primary-gate tables and hashes are untouched by these shapes.
- [x] 1.3 eval_dev.py / trial_common.py: MDM table gains the gradual
      column(s) + b0_calendar gradual column; censoring semantics
      unchanged; Wilson CIs + prevalence.

## 2. Run + reports

- [ ] 2.1 Agent smoke: gradual sweep on a tiny injection set (shapes,
      hashes, censoring) — no retraining of any frozen checkpoint.
- [ ] 2.2 User-run (exact commands handed over): gradual sweep for the
      available arms (b1, gru_ae_main, b0_calendar, + trained arms that
      exist at apply time).
- [ ] 2.3 Persian finding (persian-writing skill): three-shape MDM curves,
      the B0-gradual result reported as a first-class outcome (expected
      honest negative for local-state models is a finding, not a failure),
      full provenance fields, L2 rung labelling.

## Implementation note (data-free half complete)

- `monitor/severity_table.py`: `GRADUAL_FAMILY`, `GRADUAL_RAMP_BINS = (3, 4, 6)`,
  `PRIMARY_FAMILIES`, `SECONDARY_FAMILIES`.
- `monitor/perturbations.py`: `inject_index_drop`/`inject_index_drop_dataset`
  accept `family="gradual"` — δ·min(1, (b−onset+1)/D) then held to cycle end,
  the sum-preserving SAVI solver at each bin's partial δ, onset pulled earlier
  so the full ramp fits, and `meta{ramp_bins, ramp_profile, n_bins_active}`
  recorded. `n_bins_window` stays the ramp length so the event-FAR window
  arithmetic is unchanged; acute/persistent metadata is byte-identical
  (regression-tested).
- `monitor/patch_perturbations.py`: the patch-tensor equivalents plus the
  secondary peak/recovery shapes, proven equal to the field-level ramp bin for
  bin.
- `scripts/eval_dev.py`: `--shapes` (default `acute,persistent`) adds gradual
  as EXTRA cells/columns; the acute/persistent sets and hashes are untouched.
  MDM80 and seed aggregation iterate whatever families were run.
- Tests: 11 new in `test_monitor_perturbations.py`, 34 in
  `test_patch_perturbations.py`.
