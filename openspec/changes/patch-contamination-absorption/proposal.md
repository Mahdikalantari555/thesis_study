# Change: patch-contamination-absorption

## Why

Real training data is contaminated: unlabeled field-cycles contain unknown
real anomalies. The architecture document §5 gives six countermeasures and
§9 experiment E7 tests them; owner feature 12 demands resistance to
anomalies in training data. Finding 20 measured the reconstruction arm's
absorption at α ≈ 0.45, and the aerial-MIM evidence (document §2.3) warns
that **extended anomalies are partially reconstructed even with suppression
losses** — at patch level, neighbours inside the same field carry the
anomaly in context, so patch arms may absorb MORE, not less. This must be
measured, not assumed.

## What Changes

- **Absorption ratio for patch arms** — the trial part-C machinery reused:
  model error at three checkpoints (before onset / first step after onset /
  several steps after) on persistent-family patch injections + the
  absorption ratio A_patch = (mean residual on injected anomalies, model
  trained WITH them present) ÷ (same, model trained clean), compared
  against gru_ae_main's α ≈ 0.45 and gru_pred's measured A.
- **Contamination sensitivity (E7)** — inject persistent/ndvi S4 into
  {0%, 5%, 10%} of TRAIN field-cycles × trimmed-loss {on, off} × one
  curation round {on, off}: score the training field-cycles, remove the
  most extreme few percent, retrain; report A_patch and clean MDM80 for
  each cell (clean MDM80 must not degrade — the highest absorption
  resistance at equal clean performance wins, document §9 E7).
- **Operational rule** — the winning contamination configuration becomes
  the default for the full run (`patch-full-run-and-ablations`); the
  absorption ratio becomes a required report field for every future arm.
- **Explicit non-goals:** no new injection families; no MemAE/adversarial
  components (document §4 excludes them from v1 — they are the documented
  NEXT step only if absorption stays high after trimmed loss + curation);
  no platform changes.
