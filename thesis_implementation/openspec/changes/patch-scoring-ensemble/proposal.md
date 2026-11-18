# Change: patch-scoring-ensemble

## Why

The PoC trial (`patch-level-controlled-trial`) scores with the prediction
residual only. The architecture document's §8 defines a full scoring
methodology, and owner feature 10 (notes.md) explicitly requires
**combining reconstruction error, prediction error and temporal
persistence**. Two repo ambiguities also land here: **C1** (severity-unit:
residual MAD vs across-field MAD — agent-resolvable, todo.md §C) and **C2**
(SHAZAM per-DOY score-climatology threshold as a second calibrated rule,
todo.md §C), plus the **M3** standard (event-FAR + POT declustering) as the
reporting norm for all future arms.

## What Changes

- **Reconstruction score `s_rec`** — the masked-reconstruction head at
  inference: random temporal/channel masks, averaged over 8 repeated masks,
  per-pixel z with the same frozen σ tables (document §8).
- **Latent deviation** — Mahalanobis distance of the per-location hidden
  state h(p,t) to a phenophase-binned low-rank Gaussian fitted on train
  latents; per-location ⇒ a map (document §8).
- **Hybrid rank score** — average of the within-phenophase percentile ranks
  of s_pred and s_rec (reduces single-score variance).
- **CUSUM persistence** — C_t = max(0, C_{t−1} + z_f(t) − κ), alarm at h;
  κ,h tuned at 1% and 5% field-cycle FAR on validation only; cycle score =
  max_t C_t; EWMA as the alternative. z_f(t) = robust z of the field score
  against all fields at the same phenophase; the optional date-wise
  cross-field median subtraction (common-mode weather/sensor cancellation)
  is a recorded decision with a default-off fallback (it reads
  contemporaneous cross-field values).
- **C1 resolution** — compute the phenophase-binned residual MAD and the
  across-field MAD side by side on the archive; record the severity-scale
  decision in the findings + model card (unblocks the A1-adjacent
  "final severity-scale" item).
- **C2 threshold rule** — SHAZAM-style per-DOY score-climatology threshold
  (fitted mean + 1.64 SD via circular DOY regression) implemented as a
  second calibration rule; compared against the per-(bin,channel) q95 rule
  at fixed FAR; decision recorded.
- **Aggregation-rule selection** — top-q vs median vs area-fraction field
  aggregation chosen on the synthetic validation set ONLY (document §8);
  maximum-aggregation stays rejected (noise-dominated).
- **M3 standard** — event-FAR with POT declustering (gap ≤ 2) becomes the
  required FAR accounting for every arm report.
- **Explicit non-goals:** no model retraining; no platform changes; no new
  injection families (that is `gradual-severity-shape` / path B); no
  threshold movement after calibration is frozen.
