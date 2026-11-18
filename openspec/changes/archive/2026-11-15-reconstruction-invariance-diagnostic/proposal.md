# Change: reconstruction-invariance-diagnostic

## Why

Findings 18/19 established the honest negatives: no model (including B1) reaches
MDM80 ≥ 0.80 at any level of the verified severity ladder, and the normal-bank
arm does not lower MDM80 on the frozen encoder. The owner's research review
(2026-11-14, following the session report) directs the next step: **before any
architecture or loss decision, run a diagnostic that locates WHERE the anomaly
signal is lost** — inside the model's reconstruction (the "reconstruction
invariance" hypothesis: persistent drops absorbed into the learned temporal
structure) or in the score path (offset correction, per-cell q95 normalization
inflated by natural outliers, trailing-window dilution).

A mechanism nuance sharpens the test: in the leave-one-bin-out statistic, bin
b's values are WITHHELD from its own prediction, so absorption is structurally
impossible at the onset bin (its context is clean) and can only affect
post-onset bins. Acute misses therefore must come from the score path; the
diagnostic measures both channels separately and attributes the loss.

## What Changes

- **Diagnostic only (read-only, dev split):** a signal-path decomposition for
  every injection of the existing severity sweep — stage-wise SNR at
  (1) residual formation (LOO prediction vs injected value at onset),
  (2) causal offset correction (what the running median subtracts at onset),
  (3) per-cell q95 normalization, (4) trailing-window aggregation, against
  the calibrated τ — plus a direct **absorption quantification** at
  post-onset bins (does the prediction track the injected level or the
  counterfactual natural level from the pre-injection tensor?).
- **Decision matrix output:** which stage loses the signal → which remedy
  family applies (scoring/normalizer fix vs loss/pretext change vs
  architecture change) — recorded as a finding, NOT implemented in this
  change.
- **Finding 20** (`docs/findings/20_reconstruction_invariance.md`): the
  reconstruction-invariance hypothesis is tested and reported as measured
  evidence, with the explicit scope limit that only the absolute NDVI/SAVI
  drop family is diagnosed (single-index injections; relational/multivariate
  families are future work).
- **Explicit non-goals:** no retraining, no loss/scoring/architecture edits,
  no threshold changes, no test access, no platform impact.

## Impact

- Affected specs: `model-development-protocol` (ADDED requirement:
  signal-path decomposition diagnostic).
- Affected code: new `src/ssl_anomaly/monitor/diagnostics.py`;
  new `scripts/diagnose_reconstruction.py`; tests; docs finding 20;
  `todo.md` open-question entries for the gated follow-up paths
  (B: multivariate/phenology injection families; C: forecasting/predictive-
  coding objectives — both gated on this diagnostic's outcome).
- NOT affected: frozen checkpoints, sidecar, platform payload, locked splits,
  severity table, calibrated thresholds.
