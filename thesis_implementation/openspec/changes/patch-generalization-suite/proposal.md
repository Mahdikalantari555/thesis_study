# Change: patch-generalization-suite

## Why

Owner feature 13 demands evaluation on unseen farms AND unseen periods; the
architecture document §10 (E9) defines the generalization program: held-out
fields, held-out periods, both, sensor-stratified. The locked splits already
provide real spatial blocking (KMeans on centroids, 10 blocks, test block 8,
dev block 4) and a temporal cutoff (test start 2024-01-01), but no
systematic generalization MATRIX has been computed for any arm — the
finding-18/22 protocol evaluates one dev subset. Document §12 uncertainty
#3 (period/sensor confounding: Landsat 9 appears only late) is also
unaddressed without sensor-stratified reporting.

## What Changes

- **Quadrant matrix** — for each arm: (a) in-block validation (current
  protocol), (b) held-out fields (train on 9 blocks' fields minus one
  block-pair, evaluate on the held-out block-pair's dev-eligible cycles),
  (c) held-out periods (dev cycles cut by `dev_temporal_cutoff`, evaluate
  late-period), (d) both. Test-block cycles remain reachable ONLY through
  the locked final-test path.
- **Blocked CV folds** — the 10 KMeans spatial blocks grouped into 5
  fold-pairs (seed-fixed, hash-recorded); per-fold MDM80 + FAR reported
  with fold-level spread (this is the document's "blocked cross-validation
  over groups of adjacent fields", implemented on the existing blocks —
  no new spatial machinery).
- **Sensor-stratified reporting** — every metric split by dominant sensor
  era (L8-dominated dates vs L9-era) to expose the period/sensor
  confound (document §12 #3).
- **Stability metrics** — seed standard deviation, score drift across years
  (quantile shift of clean cycle scores per year), and threshold-stability
  check (frozen τ/k applied across years without refit; document §12 #9).
- **L3 rung** — passing the matrix without material drop upgrades an arm's
  claims to L3 (generalizes across farms/periods); the matrix result is
  the L2→L3 gate for every arm, patch arms included.
- **Explicit non-goals:** no retraining beyond the fold runs this suite
  requires; no test-split reading outside the locked final-test path; no
  platform changes; no new injection shapes.
