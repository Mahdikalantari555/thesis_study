## Design — patch-generalization-suite

### Fold construction

The 10 KMeans blocks (seed 13, `monitor/splits.py`) are paired into 5 folds
by geographic adjacency of block centroids (nearest-pair greedy, seed-fixed,
hash-recorded) — pairing halves the number of retrainings while keeping
held-out regions contiguous. Per fold: train = train-split cycles of the 8
in-fold blocks (frozen normalization re-fit on in-fold train data ONLY —
the store's per-sensor stats are recomputed per fold to avoid leakage),
evaluate on the held-out block-pair's dev-eligible cycles. All folds reuse
the same injection sets (hash-identical) so fold spread measures
generalization, not protocol noise.

### Temporal axis

Held-out periods use the existing `dev_temporal_cutoff`: train cycles
before the cutoff, evaluate after — reported as a separate column, not
mixed into the spatial folds. The quadrant cell (d) combines one held-out
block-pair with the late period.

### Confound handling

Period and sensor are confounded (L9 appears only late); every temporal-axis
result is therefore reported both raw and sensor-stratified (L8-era dates vs
L9-era dates), and the report states plainly when a temporal drop may be a
sensor change (document §12 #3). The sensor-offset ablation in
`patch-full-run-and-ablations` is the mechanistic follow-up if the
stratification shows a sensor-driven jump.

### Cost control

5 folds × 1 retrain per arm × 3 seeds is 15 runs per arm — restricted to
the arms that passed the PoC/full-run gates (the matrix is a gate for
final claims, not a routine). Single-seed folds for screening, 3 seeds for
the arms that reach the thesis's final claims. `--estimate-runtime` before
each batch; all runs are user-executed.

### Acceptance (pre-registered)

An arm passes L3 if: per-fold MDM80 spread (max − min across folds) ≤ the
dev estimate's two standard errors AND no fold loses censoring status (an
uncensored arm must stay uncensored in every fold) AND the temporal-column
drop vs the in-block estimate has a bootstrap CI excluding material
degradation (pre-registered threshold: MDM80 worsening by more than one
severity level). Otherwise the honest negative is recorded with the
failing cells named.
