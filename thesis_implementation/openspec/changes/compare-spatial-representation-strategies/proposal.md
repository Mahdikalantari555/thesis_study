# Change: compare-spatial-representation-strategies

## Why

Owner proposal (2026-11-15, `compare-spatial-representation-strategies`): a
controlled study of spatial representation strategies — zonal statistics vs
patch sampling vs multi-scale — for the label-free growth-anomaly task, with
the owner's clarification that nothing in the proposal text is definitive
and the ESSENTIAL deliverable is a **transparent comparison of detection
accuracy across spatial scales/representations**. Owner refinement of the
same-day notes.md request; the architecture document's E1/E5 fragments are
elevated from scattered optional ablations to a first-class study.

**What is ALREADY covered elsewhere (no duplication here):** R0 zonal arms
exist and stay (b0_calendar, b1, b3, gru_ae_main, gru_pred); R1 full-field
32×32 patches = `patch-level-controlled-trial` primary; the pixel-vs-patch
question = that trial's E1 CNN-off control; patches-within-polygons, QA
masking, leakage discipline, equal-condition evaluation, farm-level scores +
spatial maps, independent indicators — all owned by the existing program.

**What is genuinely NEW here:** (a) the **zonal distribution-statistics
representation** (R0.5 — `std`, `p10`, `iqr` per farm per date instead of
the mean alone; the intermediate rung between field-level zonal means and
patches), (b) the sub-crop representation (K small crops per farm +
aggregation — the sugar-beet design lineage, absent from the program),
(c) multi-scale representation, (d) the elevation of the scale question
into ONE pre-registered, capacity-matched, transparent comparison with a
single decision table, (e) the **heterogeneity-disambiguation battery**
(static-pattern control, spatially-i.i.d. noise null, per-pixel alarm
frequency) that separates a genuine localized anomaly from chronic
within-field heterogeneity and from noise, (f) the **extent axis** and the
**detectability-crossing table** that make "patches detect what the mean
cannot" a paired per-injection claim instead of an aggregate one, and
(g) measured (not assumed) data-access and patch-size decisions.

**Owner prompt coverage (audit 2026-11-16,
`docs/audits/spatial_prompts_vs_openspec_2026-11-16.md`):** this change now
covers every requirement of the owner's "Evaluating the Impact of Spatial
Aggregation on Anomaly Detection" task, including the previously missing
three-way structure (Zonal Mean / Spatial Statistics / Patch-based) and the
prompt's explicit "distinguish genuine spatial anomalies from natural
spatial heterogeneity, phenological differences and data noise" demand.

## What Changes

- **Representation ladder (pre-registered):**
  - **R0 — zonal mean** (existing arms; results REUSED, never re-run) and
    **R0-subset** — the same existing arms re-scored on exactly the PoC dev
    panel with the identical injection sets, because reusing all-train-field
    R0 results against subset-trained patch results would confound the
    representation effect with training-set size (that confound is stated in
    the table regardless).
  - **R0.5 — zonal distribution statistics** (`std`, `p10`, `iqr` per farm
    per date, read from the EXISTING `stats.zarr`, which already stores
    mean/std/p10/p25/p75/p90/iqr for all 490 fields × 538 dates and whose
    only current consumer is the median): the SAME `B1PhaseZCausal` /
    `b1` scoring path with those channels added — **no new store, no
    training, no GPU**. Also scored as a `b0`-calendar and a path-max
    variant so the "do lower quantiles reveal deterioration the mean hides"
    question is answered with a rule-based reference, not only with a model.
  - **R1 — full-field patch 32×32** (the PoC's `patch_cnn_gru`).
  - **R2 — sub-crop representation**: K pre-drawn 16×16 crops fully inside
    the field polygon (default fixed hashed crop sets; K ∈ {4, 6, 8} swept
    at single seed first), same PatchCNNGRU trunk at 16×16 input, field
    score = aggregation over crops (top-q mean; majority-vote variant as
    flag). Crops are DERIVED by cropping the materialized 32×32 store — no
    re-extraction. Fields smaller than 16×16 (measured 7.3%) get a recorded
    fallback, not silence.
  - **R3 — multi-scale, two variants in cost order**: (a) multi-dilation
    stem at 32×32 (dilation branches 1/2/4 — broader context, zero extra
    data, ~+11k params); (b) true two-scale fusion (16-crop branch + 32
    branch) built ONLY if R2 or R3a shows broader context matters.
- **Heterogeneity-disambiguation battery (NEW)** — the prompt's demand to
  separate genuine localized anomalies from natural spatial heterogeneity,
  phenology and noise, made operational:
  - **Static-pattern control** — a per-field per-pixel clean climatology
    (long-run median image over clean cycles) defines each field's OWN
    persistent spatial structure; a "localized anomaly" is a departure from
    that structure, not a departure from the field mean. Reported as an
    alternative per-pixel normalizer (score / chronic-offset), so chronic
    low-yield patches cannot win the top-q aggregation by being chronically
    low.
  - **Spatially-i.i.d. noise null** — the same δ ladder injected as
    white noise over the field instead of a coherent footprint: the patch
    arm's advantage must survive coherent injections and shrink under the
    noise null; the coherent-vs-noise MDM gap is the evidence that the gain
    is spatial signal rather than noise averaging.
  - **Per-pixel alarm frequency** — for clean dev cycles, the per-pixel
    alarm rate: a detector firing every cycle on the same pixels is
    reporting heterogeneity, not events; reported per representation.
  - Phenology is already controlled (36-bin cycle grid + phenophase-binned
    σ + DOY/cycle-age covariates + the mandatory `b0_calendar` reference);
    data noise is controlled by the QA mask, the NaN-as-absent policy and
    this battery.
- **Extent axis + detectability crossing (NEW)** — injection footprint
  swept over {0.1, 0.3, 0.6, 1.0} with the existing applier, reported as
  MDM80 + localization AUPRC per extent for every representation; and a
  per-severity 2×2 crossing table (detected by the patch arm only / by the
  zonal arm only / by both / by neither), which is the actual evidence for
  "localized anomalies are invisible in farm-level means".
- **Geometry-first scale memo** — 64×64 measured against the real field
  geometry (median side 16.7 px, max 19.6 px ⇒ a 64×64 window is ~93%
  padding/other fields for the median farm): excluded from training by
  default, available behind one flag if the owner still wants it, decision
  documented with the numbers.
- **Data-access decision by measurement, not assumption** — one-time
  micro-benchmark: Zarr lazy random-read throughput vs materialized-store
  preload (the store is ≈1.0 GB fp16, RAM-preloadable). The proposal's lazy
  loading is adopted ONLY if the measurement favors it; recommendation on
  record: materialized, for CPU-bound training.
- **Equal-budget protocol** — same objective (prediction primary + masked
  aux), bins, channels, seeds {13, 42, 2026}, injection sets, σ tables and
  alarm machinery across all representations; capacity-matched (param count
  in every table; >±20% deviation flagged); same farms/cycles (paired).
- **Transparent deliverable (owner's core ask)** — ONE table + figure:
  representation × {MDM80 per temporal shape, event-FAR, detection delay,
  pixel-localization AUPRC, MDM80 at each footprint extent, noise-null
  MDM80, per-pixel alarm frequency, params, epoch time, peak RAM} —
  detection quality, spatial sensitivity, temporal consistency and
  computational efficiency side by side; each row labelled **farm-local**
  or **population-ranked** (see `farm-local-anomaly-scoring`) and stamped
  with the ground sampling distance arithmetic. → finding 24 (Persian).
- **Resolution arithmetic is a REQUIRED report field (NEW)** — every row
  states its spatial support in metres and hectares (1 px = 30 m = 0.09 ha;
  a 16×16 R2 crop = 480 m ≈ 23 ha, i.e. comparable to a whole median
  field — R2 is far less "local" than "sub-crop" sounds) and the smallest
  anomaly it can resolve in pixels; the LST-at-30-m-from-100-m caveat and
  the Landsat-30-m interpretation limit travel into finding 24, not only
  into `patch-data-pipeline`'s design risks.
- **Pre-registered adoption rule** — a representation replaces R1 only if
  MDM80 improves with a paired-bootstrap CI (over fields) excluding zero at
  ≤2× compute; multi-scale is adopted only if it beats the best single
  scale with CI excluding zero. Honest negative otherwise.
- **Explicit non-goals:** no 64×64 training by default; no lazy-pipeline
  rewrite unless the benchmark favors it; no supervised objectives; no
  platform changes; no new injection families; no re-running of R0 arms.

## Sequencing

Gated on the PoC gates (G1–G5) — it consumes patches.zarr and the trained
R1 checkpoints. Feeds the `patch-full-run-and-ablations` final criterion:
that change's E5 scale sweep is delegated HERE (inner-buffer/burn-in
ablations stay there).
