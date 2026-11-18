# Change: patch-level-controlled-trial

## Why

Owner decision (notes.md, 2026-11-15): run a **patch-level training test**
and see whether it produces a good result — first on a subset of farms,
then on the whole dataset only if it does. This trials the primary
architecture recommended by
`research/Architecture_Selection_for_Self_Supervised_Spatiotemporal_Anomaly.md`
(2D CNN stem → per-location GRU; causal multi-horizon prediction primary,
masked reconstruction auxiliary), whose scientific target is the finding-18
honest negative: MDM80 is censored ">S6" for every arm including B1 at 5%
cycle-FAR, while realistic stress magnitudes sit far below that floor. The
document's bet is that three mechanisms lower the floor — spatial coherence
(pixel noise is spatially independent, injections are coherent),
phenophase-conditioned σ standardization (the finding-20 σ-unit fix), and
persistence accumulation — and all three are testable under the EXISTING
severity machinery.

Naming map (the document's labels vs this repo): document "B1 GRU-AE" =
`gru_ae_main` (frozen reconstruction arm); document "B0 climatology" =
`b0_calendar`; this repo's `b1` = the robust-z statistical baseline.
The PoC's comparator is the best existing arm on the finding-18 protocol.

This trial complements, not replaces, `predictive-ssl-controlled-trial`
(`gru_pred`, field-level, awaiting user training): the patch arm is the
spatial extension of the same path-C question. The owner's 2026-11-15
request amends the todo.md prohibition on parallel architecture trials for
THIS controlled trial only (recorded here; todo.md updated at apply time).

## What Changes

- **Model `PatchCNNGRU` (~90k params, document §7.1 adapted to the 36-bin
  cycle grid)** — 2D CNN stem shared across bins (~33k: 3×3 convs,
  GroupNorm, GELU, 32 channels) → one-layer GRU run independently at every
  pixel location (40→96, ~40k; state carried unchanged where the pixel is
  invalid) → causal multi-horizon prediction heads k=1–3 in INPUT space
  (~8k) + masked-reconstruction auxiliary head (~7k). NO pooled latent
  anywhere; field-level information appears only at scoring (document §6).
  Covariates d_u = 7: sin/cos DOY, cycle age, days-since-last-valid-obs,
  log1p(n obs in bin), sensor one-hot L8/L9.
- **Training `scripts/train_patch.py`** — hybrid objective:
  Σ_k w_k·Huber (w = 1, 0.5, 0.25) over valid in-field pixels + 0.3×
  masked-reconstruction Huber; 8-bin burn-in without loss; trimmed loss
  (drop top 5% per batch) after a 10-epoch warm-up; AdamW 2e-3, cosine
  decay, wd 1e-2, clip 1.0; seeds {13, 42, 2026}; ≤500k params.
- **Owner-required operability** — `--estimate-runtime` (timed
  extrapolation printed BEFORE any run: per-epoch, per-seed, total, disk),
  `--resume` (per-epoch checkpoint incl. optimizer/scheduler/RNG states +
  config-hash check), tqdm progress + `progress.jsonl` + final wall-time
  summary, device auto-select (CPU-first: the owner runs training on their
  own system), `--smoke`, `--max-fields` subset mode.
- **Subset-first protocol** — PoC trains on a pre-registered hashed subset
  of locked TRAIN-split fields and evaluates through `scripts/eval_dev.py`
  protocol `severity` UNCHANGED (S1–S6 × {acute, persistent} × {ndvi, savi},
  identical injection sets as findings 18/22, 5% cycle-FAR calibration,
  MDM80 with ">S6" censoring) on the locked dev subset; test split
  untouched. Scale-up to all train fields only if the gates pass.
- **Scoring integration** — per-pixel z-scores with phenophase-binned
  σ(c, φ, sensor) = 1.4826 × MAD of residuals on dev field-cycles (the
  finding-20 unit fix); pixel score = mean z² over k=1–3 and channels;
  field-cycle aggregation = mean of the top 20% valid in-field pixel scores
  (top-q) feeding the EXISTING alarm rule (τ, k consecutive bins) — one
  scorer adapter with the `DeepCausalScorer` interface, so FAR comparability
  with `b1` / `gru_ae_main` / `gru_pred` is exact. Injections applied
  per-pixel on the patch tensors with the same δ ladder and the existing
  sum-preserving red/nir SAVI solver (footprint 1.0 for protocol
  comparability; 0.3 for the localization probe).
- **E1 spatial-value control (document §9)** — `patch_pixelwise` arm:
  pixel-wise GRU predictor (no stem, same objective and budget). The CNN
  stem is kept only if it improves MDM80 or pixel-localization AUPRC;
  otherwise the honest negative is recorded and the pixel-wise variant
  continues.
- **Pre-registered PoC gates** (evaluated verbatim, tasks §4): G1 smoke
  plumbing · G2 overfit-one-batch learning (L1) · G3 subset floor — MDM80
  finite (uncensored ≤S6) AND better than the best of {`b1`, `gru_ae_main`}
  on the same injections with paired bootstrap over fields, CI excluding
  zero (both currently censored ">S6", so success = any finite MDM80) ·
  G4 E1 spatial value · G5 estimate-before-run and ≤2× `gru_ae_main`
  compute. Full-run success criterion (pre-registered, document §Final):
  beats B0 and B1-class references on MDM80 at 5% FAR for ≥2 of 3 temporal
  shapes, CI excluding zero on held-out fields/periods, ≤2× compute.
- **Finding 23 (Persian, persian-writing skill)** — patch-level PoC verdict
  with all gate numbers (finding 22 stays reserved for the gru_pred trial
  verdict). Every claim ladder rung L1–L2 only.
- **Explicit non-goals:** no platform changes; no raw-date/Δt irregular-
  time mode (cycle bins kept for machinery comparability — documented
  deviation from the document §7.3); no LST-off channel ablation in the
  PoC (8 channels match B1; E6 belongs to the later full run); no
  absorption/part-C experiment (deferred to the full run — machinery
  exists); no XAI extension (the 1D `xai/` suite does not apply to patch
  inputs; follow-up change); no 3D convs, ConvLSTM/ConvGRU, VideoMAE-style
  masking, JEPA-style latent prediction, memory/adversarial components,
  weather covariates, foundation models; no test-split access outside the
  locked final-test path.
