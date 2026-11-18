# Tasks — patch-generalization-suite

## 1. Fold + matrix machinery (TDD-first)

- [x] 1.1 Unit tests: fold-pair construction (contiguity, seed-fixed,
      hash-recorded; every block in exactly one fold); per-fold
      normalization re-fit from in-fold train data only (leakage test);
      quadrant-cell cycle selection respects dev_temporal_cutoff and
      dev-eligibility.
- [ ] 1.2 `scripts/run_generalization_matrix.py`: per arm × cell × fold
      training/eval driver with --estimate-runtime, --resume, progress
      output; reuses train_main/train_patch checkpoints where folds permit
      (in-block cell) and retrains for held-out cells.
- [x] 1.3 Sensor stratification: date→sensor-era mapping (from scene
      metadata); stratified report columns; year-drift quantile-shift
      metric; threshold-stability check (frozen τ/k across years, no refit).

## 2. Runs (user-executed)

- [ ] 2.1 Screening pass: single seed × 5 folds for gated arms; review
      produced reports; 3-seed runs only for arms reaching final claims.
- [ ] 2.2 Matrix report: cells × folds × sensor eras with Wilson CIs,
      prevalence, MDM censoring; committed under reports/.

## 3. Verdict

- [ ] 3.1 Pre-registered L3 acceptance applied verbatim per arm; failing
      cells named; findings updated.
- [ ] 3.2 Persian finding (persian-writing skill): the matrix, the confound
      analysis, and which arms earn L3 — honest negatives explicit.

## Implementation notes (1.1/1.3 complete; 1.2 planning and reporting only)

`monitor/generalization.py` (28 tests), `monitor/generalization_matrix.py`
(21 tests), `scripts/run_generalization_matrix.py` (11 tests).

- **1.1** `pair_blocks_by_adjacency` pairs the 10 k-means blocks by nearest
  centroid (greedy, deterministic, hash-recorded); `build_folds` refuses a
  field held out by two folds, a block with no fields, and a fold count that
  does not partition the fields. `refit_norm_in_fold` re-fits the transform
  from in-fold train cycles only, and `norm_uses_only_in_fold` exists so the
  leakage claim is CHECKED (excluding an in-fold row must change the fit;
  a planted holdout-looking cycle must not).
- **1.2** the CLI plans cells, estimates cost and aggregates artifacts with NO
  store: `--plan`, `--estimate-runtime`, `--report`, `--execute`. Cells: 5
  spatial folds + 5 quadrants + 1 temporal column, and the temporal cell's
  retrain decision follows the cutoff (so a reusable in-block checkpoint is
  used instead of re-training). `--execute --dry-run` prints the plan; actual
  execution is blocked until fold-aware calibration and evaluation are wired.
  The report tooling can scan artifact records; the runtime estimate separates the 1-seed screening pass from
  the 3-seed final pass (6×1 vs 2×3 — the design's cost control made numeric).
- **1.3** `sensor_era` (contiguous runs, `unknown` never attributed to a
  neighbour), `era_shares`, `year_drift` (quantile shift vs the first year) and
  `threshold_stability` — the frozen τ/k are re-used per year, NOT refitted,
  and the production `alarm_per_cycle` rule is used verbatim (an earlier draft
  used a moving average, which would have changed what "stable" means).
  `aggregate_matrix` reports the era-stratified columns beside the raw one, and
  the report states the period/sensor confound explicitly.

The acceptance function (`apply_acceptance`) is a transcription of the
pre-registered rule: spread ≤ 2·SE, no NEW censoring, temporal drop ≤ 1 level,
computed against hand-worked cases in the tests.

Still data-blocked: 2.1 (screening runs), 2.2 (matrix report from real runs),
3.1/3.2 (verdict + Persian finding).


## Holdout audit follow-up

- [ ] A.1 Wire fold-aware locked dev calibration/evaluation and per-fold
      artifacts before enabling execution. The previous `--execute` path
      attempted ordinary locked-dev evaluation, not the requested held-out
      fold/dates, and had no complete checkpoint/σ/norm handoff. Keep planning,
      estimates, historical reports, and dry runs available; do not start
      expensive retrains from this incomplete driver. Fold definitions cannot
      override the global holdout or locked train membership.
