## Design — patch-xai-attribution

### Method choice rationale

Occlusion is the primary method because it needs no gradient path through
the σ standardization (z² involves frozen statistics — differentiable, but
the occlusion estimate is assumption-free and matches the document's
"occlusion-style" scoring checks). Gradient×input is the cheap
per-(bin,band,pixel) dense attribution; integrated gradients is kept from
the 1D suite with the patch tensor substituted, reported for a sample of
events as a cross-check, not for every alarm (cost). KernelSHAP is NOT
ported to patches (coalition count explodes in 3D; the document's budget
discipline applies).

### Baselines for occlusion

Occluded values come from the frozen per-channel train medians (the
normalization artifact) — never zeros (zeros are out-of-distribution in
reflectance space and would manufacture importance). Per-pixel medians are
not used (they would let a pixel explain itself).

### Faithfulness protocol

- Deletion AUC: progressively remove the top-attributed (bin, band, pixel)
  tuples and measure s_pred decay; insertion AUC symmetric. Computed on a
  pre-registered sample of alarms (e.g., 50 events spanning severity
  families) — not all.
- Sanity: weight randomization must collapse attribution structure
  (adapted check).
- Physiology sign-concordance: for events where NDVI dropped, the
  aggregated band attribution must assign majority importance to
  red/swir-family channels consistent with the drop direction; failures
  are reported, not filtered out.

### Interface

`src/ssl_anomaly/xai/patch_attribution.py` mirrors the 1D suite's API
(attribution → aggregation → faithfulness) so the RQ6 documentation and
tests translate; reuses `SUGARCANE_STAGE_BINS` and the faithfulness
primitives where shapes permit. Attribution runs are eval-only on frozen
checkpoints — no retraining, `--estimate-runtime` for the sampled runs.

### Risks

- Occlusion on 8 channels × 36 bins × 1024 pixels per event is expensive —
  band and temporal occlusion are coarse-grained (per band, per bin);
  per-pixel occlusion only for the sampled events.
- Explanations on synthetic events are circular by construction (the
  attribution explains the injected drop) — the honest framing is:
  attributions on NATURAL alarms are the thesis deliverable; synthetic
  events serve only as the faithfulness sanity set.
