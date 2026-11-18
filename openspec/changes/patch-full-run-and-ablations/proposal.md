# Change: patch-full-run-and-ablations

## Why

The PoC (`patch-level-controlled-trial`) proves the patch arm on a subset;
this change is the road from PoC to the thesis's final architecture
decision. It implements the architecture document's experiment program —
E2 (objective weights), E3 (temporal-module challenger), E4 (covariates),
E5 (patch/window variants), E6 (channels) — on the FULL train set, with
owner features 6/16/17/19/20 completed (multi-band ablation support,
runtime estimation, RAM/VRAM benchmarking, config-driven variants, full
reproducibility). The pre-registered final criterion is the document's:
**beat B0 and the best prior arm on MDM80 at 5% field-cycle FAR for ≥2 of
3 temporal shapes, paired-bootstrap CI over fields excluding zero, on
held-out fields and periods, at ≤2× the compute of gru_ae_main.** If the
criterion fails, the honest thesis finding is the detection floor itself
plus the conditions under which learned models do and do not help
(document §Final, "where this could turn out wrong").

## What Changes

- **Scale-up run** — the winning PoC configuration on ALL locked
  train-split fields (447 cycles), seeds {13, 42, 2026}, GPU/CPU
  auto-select, `--estimate-runtime` before launch, checkpoints/resume.
- **E2 objective ablation** — auxiliary masked-reconstruction weight
  {0, 0.3}: the aux term is dropped unless the minimum detectable
  magnitude improves (document §5 hybrid rule).
- **E3 temporal-module challengers** — causal dilated TCN (kernel 3,
  dilations 1/2/4/8) on a regular bin grid with masks, AND TinyCNNMamba
  (module already in `models/cnn_mamba.py`) as challengers to the per-
  location GRU; simpler-or-faster wins ties (within one standard error).
  **Thesis-title dependency:** the "CNN-Mamba" title stays honest only if
  the Mamba challenger earns its place here; otherwise the title/architecture
  wording goes to the advisor discussion (recorded, not silently changed).
- **SSL-off control (AGENTS.md §8 requirement)** — random-init encoder of
  the SAME architecture with the same scoring, as the "does self-supervised
  pretraining help at all" reference (owner validation guide §6-F).
- **Classical-baseline comparison set** — B3 (IsolationForest + ECOD on
  per-cycle summary features, already implemented) IS the windowed
  multivariate classical arm (owner guide §5 fairness satisfied); One-Class
  SVM added as the optional boundary-based arm; every comparison reports
  each method's temporal-information level (owner guide §5 note).
- **Error analysis (owner validation guide §9 step 8)** — FP: the top
  clean-dev alarms reviewed against the weather/neighbor context of
  `patch-independent-indicators`; FN: missed injections decomposed by
  family × severity × phenophase; causes recorded in the Persian finding —
  the analysis that turns the final runs into a defensible error chapter.
- **E4 covariate ablation** — DOY baseline → +cycle age → +sensor →
  weather aggregates LAST (ERA5 30-day precipitation etc., todo item 6),
  each kept only if it cuts false alarms at fixed recall; weather-
  conditioned AND unconditioned both reported (conditioning can explain
  away regionally-driven anomalies — document §9 E4).
- **E5 patch/window variants** — inner buffer on/off (1 px; removes ~22%
  of a median field's pixels but most mixed edge pixels); burn-in length
  {4, 8, 12}. The patch-SIZE/representation scale sweep (S=16 tiled, sub-
  crops, multi-scale) is DELEGATED to
  `compare-spatial-representation-strategies` — not duplicated here.
- **E6 channel ablation** — LST-off (7 channels) vs 8-channel; the LST-off
  checkpoint is ALSO the input-independence arm required by
  `patch-independent-indicators` (E10).
- **Sensor-offset ablation** — per-band L8↔L9 linear offsets estimated
  from near-coincident acquisitions over the AOI (Roy et al. logic
  re-estimated locally, not imported), applied vs not applied.
- **Benchmarking (owner feature 17)** — params, MACs, minutes/epoch, peak
  RAM (psutil), peak VRAM (torch.cuda.max_memory_allocated), seconds per
  field-cycle inference — recorded in the run manifest and reports.
- **Final architecture decision** — the pre-registered criterion applied
  verbatim; the winning configuration is frozen (model card + sidecar),
  and the L2→L3 generalization matrix (`patch-generalization-suite`) runs
  on it. Failure ⇒ honest-negative finding; no goalpost movement.
- **Explicit non-goals:** no new injection families here (path B is a
  separate conditional change); no architecture families beyond E3's
  challenger (no ConvGRU/VideoMAE/JEPA/foundation models — document
  exclusions stand); no platform changes.
