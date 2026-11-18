# Design — normal-bank-novelty-scoring

## Context

Objective-family ranking evidence (TSB-AD, LEAP) says representation + distance-to-normal-bank
scoring beats full-window reconstruction — our current family — and wins precisely on level-shift
and cross-channel (relational) anomalies. The salinity signature (NDVI↓ with SWIR↑/LST↑) is
relational; water-deficit steps are level shifts. The arm is therefore expected to help most on the
persistent/index-drop variants — evaluated under the severity protocol change, not the retired 1×MAD
metric.

## Bank construction

- Encoder: frozen `checkpoints/gru_ae_main.pt` (174k params). No fine-tuning anywhere in this change.
- Bank source: **train-split cycles only** (manifest-gated; `assert_no_test_cycles` enforced).
  Embeddings: encoder hidden state at each observed bin (mask-aware; unobserved bins contribute
  nothing). Bank keys: (bin index, band-mask signature class) so a query bin is compared only to
  bank bins with comparable observation patterns.
- Distance: robust z of latent distance per bin class (median/MAD over the bank), k-NN (k ∈ {1,5})
  and per-class robust Mahalanobis variants evaluated on dev; the choice is a single-change
  experiment logged in `reports/dev_log.csv`.
- Score fusion: `alarm = max(alarm_recon, alarm_bank)` after per-statistic normalization to the
  common null (per-cell q95), OR a weighted sum — both variants evaluated; selection on dev only.

## Evaluation

- Same severity sweep and FAR calibration as `literature-grounded-severity-protocol` (MDM80
  primary, per-level detection + event-level FAR secondary). Three arms compared:
  `recon_only` (frozen behaviour), `+bank`, `b1_phasez_causal`.
- Plateau rule unchanged: freeze only after three consecutive single-change experiments with
  improvement < max(0.01, seed std) — applied to the MDM axis.
- Statistical honesty: dev = 69 cycles; report seed spread and Wilson CIs; no test access during
  development; a locked `--final-test` run happens only after a freeze request.

## Risks

- Small dev → bank-distance normalization may overfit; mitigated by per-class robust statistics and
  the disjoint evaluation subset from the severity change.
- Bank-class sparsity (many mask-signature classes × 36 bins) → fall back to pooled class with a
  recorded flag, mirroring the B1 pooled-fallback pattern.
- Fusion can inflate FAR; the calibration is redone per fusion variant on clean cycles so the 5 %
  budget holds by construction.

## Non-goals

- No platform contract/payload change; no retraining; no JEPA/Mamba architecture work; no CWSI/ETa
  proxies (non-circularity tests unchanged).
