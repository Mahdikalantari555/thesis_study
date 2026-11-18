# Change: normal-bank-novelty-scoring

## Why

Finding 16 measured deep ≈ B1 (climatology) and the D6 target was not met at the old severities.
The verified TSB-AD evidence (deep-research F3; `research/ssl-stress-advantage/REPORT.md`) ranks
objective families on multivariate time-series AD: representation + normal-bank novelty 0.48 >
deep forecasting 0.41 > deep reconstruction 0.37 (our family) > matrix profile 0.35 > PCA 0.31 >
Transformer-AD 0.18 — and LEAP's masked-prediction + latent bank-novelty scorer is the documented
state of the art on both TSB-AD tracks, with the deep advantage appearing exactly on
level-shift/relational anomalies (the salinity signature class: concurrent NDVI↓/SWIR↑). The cheap,
evidence-backed next arm is therefore a **latent normal-bank novelty scorer on the frozen
`gru_ae_main` encoder** — no retraining, no platform change.

## What Changes

- **Dev-only scoring arm:** embed clean **train** cycles with the frozen encoder; build a normal
  bank (per-bin latent vectors with robust statistics); score dev/test cycles by latent distance
  (k-NN / robust Mahalanobis) fused with the existing channel-max reconstruction statistic via the
  SAME 5 % cycle-level FAR calibration and the SAME severity sweep as
  `literature-grounded-severity-protocol`. Comparison: `gru_ae_main` (reconstruction-only) vs
  `+normal-bank` vs B1 — same splits, same seeds protocol for the sweep repetitions.
- **No platform impact by default:** the frozen `checkpoints/gru_ae_main.pt` sidecar and the v5
  payload remain untouched unless the arm wins and a follow-up freeze is explicitly requested.
- **Leakage guards:** the bank is built from train cycles only; test access stays locked behind
  `freeze_main_model.py --final-test`; no CWSI/ETa/yield anywhere (existing non-circularity tests
  apply unchanged).

## Impact

- Affected specs: `model-development-protocol` (ADDED requirement: normal-bank novelty scoring arm).
- Affected code: new `src/ssl_anomaly/monitor/normal_bank.py`; `scripts/eval_dev.py` (scorer
  switch + fusion); tests; docs finding 19. Frozen checkpoints, platform contract, splits manifest
  untouched.
