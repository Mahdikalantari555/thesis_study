# Change: patch-xai-attribution

## Why

Owner feature 11 demands explainability — band importance, feature
importance, effective time windows — and XAI is IN the thesis title. The
existing `src/ssl_anomaly/xai/` suite (RQ6/G6: integrated gradients,
1D temporal Grad-CAM, window occlusion, KernelSHAP, faithfulness checks)
is built for 1D field-level `(T, n_bands)` inputs and **does not apply to
patch inputs** `(bins, channels, 32, 32)`. The architecture document is
silent on XAI — this change fills that gap with methods that match the
patch model's per-pixel scoring: attribution maps in space, bands, and
time.

## What Changes

- **Band occlusion attribution** — replace channel c with its frozen train
  median per pixel → Δ(s_pred) map per band; aggregated per sugarcane stage
  (reuses `SUGARCANE_STAGE_BINS`).
- **Temporal-bin occlusion** — occlude bin t's input → Δ(field-cycle
  score) per bin → "effective time windows" as the owner's feature 11
  words it; aggregated to the three agronomic stages.
- **Spatial attribution maps** — per-pixel z² maps (already produced by the
  PoC scorer) + occlusion-derived per-pixel contribution maps; exported as
  GeoTIFF-able arrays for the platform/figures later.
- **Gradient×input** — s_pred (mean z²) is differentiable w.r.t. the
  normalized inputs; gradient×input gives per-(bin, band, pixel)
  attribution in one backward pass (the 1D suite's integrated-gradients
  machinery adapted to the patch tensor).
- **Faithfulness + sanity (adapted from faithfulness.py)** —
  deletion/insertion AUC on the patch grid; weight-randomization sanity
  check; physiology sign-concordance (a water-stress-consistent
  attribution must put positive importance on bands driving the NDVI/SAVI
  drop direction).
- **Outputs** — per-alarm attribution artifacts (band table, temporal
  window table, spatial maps) + a Persian finding; explanations are
  descriptions of what drives the SCORE, never claims about agronomic
  causation; ladder rung L2 wording only.
- **Explicit non-goals:** no platform UI for attributions (separate
  platform change later); no post-hoc XAI for field-level arms (the 1D
  suite already covers them); no attention-rollout claims for the GRU (no
  attention to roll out); no L4 physiological validation (A2-gated).
