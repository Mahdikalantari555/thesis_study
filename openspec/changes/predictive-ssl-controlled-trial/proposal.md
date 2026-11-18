# Change: predictive-ssl-controlled-trial

## Why

Owner directive (2026-11-14): do NOT change the GRU-AE architecture blindly
and do NOT shop for architectures. Run ONE controlled experiment that decides
between Reconstruction and Prediction under identical data, splits and
conditions, and answers the thesis-level question:

**"Is predicting the field's future natural behavior more trustworthy than
reconstructing its past for finding fields suspected of stress?"**

The goal is identifying suspected-stress FIELDS — not winning a synthetic
metric. Finding 20 supplies the mechanism motivation: the reconstruction
prediction absorbs ≈half of persistent drops at post-onset bins
(α ≈ 0.38–0.50 at S4–S6), and the σ-unit of a reconstruction objective
(across-cycle phenological spread) puts the realistic severity ladder
0.36–2.68σ against a ≈3.5–4.9σ per-bin requirement. A one-step-ahead
predictive objective re-anchors the residual to temporal predictability, and
a sustained level shift is structurally unpredictable from history — so its
error should PERSIST through the drop instead of being absorbed (finding 20
§3; measured directly in part C of this trial).

## What Changes

- **New training arm `gru_pred`** — the SAME architecture trunk, inputs
  (8 channels + DOY), frozen normalization, splits and parameter/seed budget
  as `gru_ae_main`; the ONLY change is the objective: causal one-step-ahead
  prediction (predict bin o's z from bins < o; masked loss over observed
  bins). Train split only (splits_locked `9aa5eb11…`); seeds {13, 42, 2026};
  ≤500k parameters, ≤15 min/seed laptop budget. No architecture redesign, no
  new features, no weather/extra indices added to the inputs.
- **Three-arm comparison under identical conditions:** B1 (statistical
  baseline) · GRU-AE (current reconstruction) · GRU Predictive — same farms,
  dates, injections, calibration rules and thresholds.
- **Four-part evaluation** (owner's design, kept verbatim in tasks):
  (A) natural-data false-alarm behavior — cycle-FAR, event-FAR, per-field
  score distribution, temporal stability; (B) the severity protocol of
  finding 18 UNCHANGED (S1–S6 × {acute,persistent} × {ndvi,savi}, same
  injection sets; event FAR, detection rate, MDM80, AUPRC, detection delay);
  (C) the absorption experiment for the finding-20 hypothesis (model error at
  three checkpoints: before onset / first step after onset / several steps
  after — does the predictive error persist through a sustained drop?);
  (D) agreement with independent remote-sensing stress indicators
  (CWSI, ETa/ETrF, TVDI, NDVI/SAVI temporal behavior) — corroborating proxy
  evidence, explicitly NOT proof of stress.
- **Pre-registered decision gates** (owner's table): FAR within budget ·
  better than GRU-AE at realistic severities · persistent-error persistence ·
  independent-evidence consistency · generalization (not a few fields / one
  period). Better → the predictive objective becomes the main development
  path. Not better → change the ANOMALY DEFINITION (path B:
  multivariate/relational + phenology-shape families) — not more blind
  architecture trials.
- **Findings 21/22** (Persian): 21 = forecast-unit probe (companion change
  `forecast-unit-probe`, the zero-training upper-bound estimate of this
  trial's mechanism); 22 = this trial's verdict with all four parts.
- **Explicit non-goals:** no Normal-Bank development, no foundation models,
  no parallel architecture families, no platform changes, no spec-target
  edits after the fact, no test access outside the locked final-test path.

## Impact

- Affected specs: `model-development-protocol` (ADDED requirement:
  predictive SSL controlled trial).
- Affected code: `scripts/train_main.py` (+ one-step objective + tests),
  `src/ssl_anomaly/monitor/models.py` (+ predictive scorer path),
  `scripts/eval_dev.py` (+ gru_pred arm), `scripts/freeze_main_model.py`
  (+ gru_pred freeze/final-test), `src/ssl_anomaly/monitor/diagnostics.py`
  (reused unchanged for part C), new part-D agreement analysis script;
  findings 21/22; `todo.md` §D.
- NOT affected: frozen gru_ae_main checkpoint/sidecar, platform payload,
  locked splits, severity table, B1, existing thresholds. Training runs are
  handed to the user as exact commands (agent never launches long jobs).
