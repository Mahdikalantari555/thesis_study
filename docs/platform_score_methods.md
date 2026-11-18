# Platform scoring & data methods — precise reference

**Date:** 2026-11-14 (contract v5) · Scope: every value the platform displays:
where it comes from, the exact formula that produces it, and its provenance
label. Documentation companion to `wire-platform-to-real-data` and
`train-and-finalize-main-architecture` (§8 platform contract v5); every claim
cites the code that implements it.

## 1. Data lineage (one paragraph)

`Data/Processed/satellite/stats.zarr` (490 fields × 538 Landsat dates,
2013-03-30 → 2026-09-10, bands `blue green red nir swir1 swir2 lst` +
`valid_frac`) → `scripts/export_platform_data.py` computes per-field
spectral indices, builds phenology cycles (both the legacy interpolated tensors
and the v5 masked ones), scores every acquisition date with trained
checkpoints, resolves the causal stress flag, joins ERA5 weather, and writes
`platform/src/data/series_khuzestan.json` (contract v5: one observation per
acquisition date — 538 per field — with RLE-encoded provenance, stress flags
and split tags) + `farms_khuzestan.json` (490 records with registry metadata).
The React platform renders those JSONs verbatim — it computes **no** data
values itself except descriptive statistics (means, correlations) over them.

## 2. The observation axis is every acquisition date

The exporter's observation grid is the **full acquisition axis**: every
Landsat/METRIC date in the cube, first row to last row (538 dates,
2013-03-30 → 2026-09-10). Each observation *is* a real acquisition
(`sampleDate == acquisitionDate`); months with two scenes appear twice; a date
can be invalid per field (low `valid_frac`, out-of-range LST) and stays the
honest "missing" state. No monthly resampling remains (the old hard-coded
2021–2024 48-point monthly grid was removed with the v4 compact payload). The
frontend derives `DATES`, slider bounds and labels from the payload axis
(`platform/src/data/data.ts`, `DATES` / `LAST_IDX`).

## 3. Displayed channels — exact formulas

Computed in `export_platform_data.py` from the per-field, per-date median
statistics (`reader.compute_indices("median")`), then range-validated against
the channel registry (`scripts/platform_channels.py`):

| Channel | Formula as coded | Source bands | Provenance label |
|---|---|---|---|
| NDVI | `(nir − red) / (nir + red)` | red, nir | `observed` |
| EVI | `2.5 (nir − red) / (nir + 6 red − 7.5 blue + 1)` | +blue | `proxy` (derived) |
| SAVI | `1.5 (nir − red) / (nir + red + 0.5)` (i.e. L = 0.5, `stats_zarr.py:114`) | red, nir | `observed` |
| NDMI | `(nir − swir1) / (nir + swir1)` | nir, swir1 | `observed` |
| LST | `lst_band − 273.15` (K→°C), rejected outside 15–55 °C | lst | `observed` |
| CWSI | `clamp((LST − 20) / 25 × (1 − NDVI), 0, 1)` — requires NDVI **and** LST | lst, red, nir | `proxy` (derived) |
| TVDI | `0.9 × CWSI` | — | `proxy` (derived from CWSI) |
| ETa | `clamp(NDVI × 6.5, 0.5, 7.5)` mm/d | red, nir | `proxy` (derived from NDVI) |
| precip | `precipitation_sum` from `weather_aligned.parquet` (ERA5), joined on the observation's `acquisitionDate` | — | `modelled` (reanalysis) |
| temp | `temperature_mean` from the same join (°C, envelope [0, 55]) | — | `modelled` (reanalysis) |

Rules the UI enforces: a `null` channel is **always** labelled `absent` (never
modelled/measured) and renders "—"; a present value keeps the label above.

## 4. Anomaly scores — the 8 detector slots (contract v5)

Every score slot resolves to exactly one of two states per observation:
**`model`** (a real checkpoint produced the number) or **`absent`**
(`score = null`). The CWSI proxy fallback of contracts v3/v4 was **removed in
v5** — see §4.3.

### 4.0 Phenology cycles in plain language

Sugarcane here grows in **multi-ratoon cycles**: one cycle = the span between
two harvests, and the plant's expected state depends on **how many days have
passed since the last harvest (DSH)**, not on the calendar date. A field at
DSH 90 (young, fast-growing) should look very different from one at DSH 300
(mature), and the *same* NDVI value can be normal at one phase and alarming at
the other. That is why "low NDVI = stressed" is wrong as a blanket rule.

The pipeline therefore:

1. **Segments** each field's NDVI time series into cycles (harvest-based
   segmentation: min 180 d, max 540 d, prominence 0.15 —
   `src/ssl_anomaly/phenology/cycles.py`).
2. **Bins** each cycle into **36 phase bins of 15 DSH days** (≤ 540 days),
   taking the median observation per bin, channel 0 = NDVI + the 7 spectral
   bands (`scripts/cycle_inputs.py::build_field_cycles` legacy /
   `::build_field_cycles_masked` v5).
3. **Scores per phase**: the trained models reconstruct each bin from the
   *preceding bins of the same cycle* (causal leave-one-bin-out). An anomaly
   score thus means "this field deviates from what normally happens at this
   **phase** of the cycle" — the phase-aware reading the thesis claims.

### 4.1 Causal main checkpoints (`masked_transformer`, `gru_ae`) — v5 path

Checkpoints: `checkpoints/masked_transformer_main.pt` / `gru_ae_main.pt` +
JSON sidecars, saved by `scripts/train_main.py` (format `causal_monitor_v1`)
and frozen by `scripts/freeze_main_model.py` (best seed by dev primary metric,
τ/k calibrated, ladder rung recorded). They may not exist yet — the exporter
degrades to `absent` for these slots when they do not
(`scripts/load_model_checkpoints.py::discover_checkpoints`, line 271: a causal
stem requires BOTH the `.pt` and the `.json` sidecar). Scoring pipeline
(`scripts/load_model_checkpoints.py::LoadedCausalModel`, line 153):

1. **Masked cycle tensors** (`scripts/cycle_inputs.py::build_field_cycles_masked`,
   line 187): the same segmentation / 15-day DSH binning / per-bin nanmedian /
   admission rules (≥ 3 observations, ≥ 3 valid-DSH observations, ≥ 3
   NDVI-observed bins) as the legacy builder, but **without interior-gap
   interpolation** — a bin/band with no finite observation stays NaN with mask
   False. This mirrors exactly the tensors the checkpoints were trained on
   (`src/ssl_anomaly/monitor/inputs.py::rebuild_masked_cycles`, line 60).
   Censored in-progress cycles are included (`include_censored=True`) for
   display and split tagging; they never enter metrics.
2. **Robust normalization inside the loaded object** (sidecar `normalization`:
   median / MAD×1.4826 scale per phase bin × band, train-split only —
   `scripts/load_model_checkpoints.py::_load_causal_one`, line 232;
   `src/ssl_anomaly/monitor/inputs.py::apply_norm`, line 353). Unobserved
   cells are zeroed together with mask 0 and never contribute to the error.
3. **Leave-one-bin-out causal scoring**
   (`src/ssl_anomaly/monitor/models.py::DeepCausalScorer.loo_batch`, line 123,
   called from `LoadedCausalModel.score_cycles`, line 173): for every observed
   bin *b*, bin *b*'s value channels are withheld and predicted causally from
   bins ≤ *b* (causal attention / unidirectional GRU; per-bin DOY sin/cos
   covariates are always present as inputs, never reconstruction targets). The
   score is the **observed-mask-weighted MSE in z-space** between prediction
   and truth of bin *b*; NaN at unobserved bins. These are the RAW scores —
   thresholds live on this axis.
4. **Display squash**
   (`scripts/load_model_checkpoints.py::squash_bin_error`, line 96):
   `score_display = 1 − exp(−raw)` — monotone `[0, ∞) → (0, 1)`, applied by the
   exporter for the 0–1 charts/colours only. The stress flag compares RAW
   scores against τ (never the squashed value).
5. **Mapping to observations**
   (`scripts/cycle_inputs.py::resolve_observation_scores_v5`, line 401 via
   `::lookup_masked_cycle_bin`, line 316): an observation gets the score of the
   masked bin containing its acquisition day; an unmapped day → `absent`.
   Formula id per observation: `<stem>:causal_bin_mse` (e.g.
   `masked_transformer_main:causal_bin_mse` —
   `scripts/load_model_checkpoints.py::score_formula_id`, line 83).

### 4.2 Causal stress flag, τ/k, ladder rung, split tags (the v5 fields)

- **stressFlag** ∈ {`normal`, `suspected_stress`, `no_data`} — computed only
  from observations of the current cycle **at or before** the acquisition date:
  the RAW score prefix of the cycle up to the acquisition's bin is compared
  against the sidecar threshold τ with persistence *k*; the flag is
  `suspected_stress` exactly when the run of *k* consecutive **observed** bins
  ending at that bin is entirely above τ (`scripts/cycle_inputs.py::resolve_stress_flag`,
  line 460; wiring in `scripts/export_platform_data.py`, lines 437–451).
  Appending later observations never changes an already-issued status.
- **Threshold calibration**: τ and *k* ∈ {1, 2} are chosen on CLEAN dev cycles
  so that at most **5 %** of them raise any alarm (cycle-level FAR ≤ 0.05,
  `src/ssl_anomaly/monitor/scoring.py::choose_threshold`), then frozen into the
  sidecar (`threshold: {tau, k, far_target, far_achieved, calibration_n_cycles}`,
  `persistence_k`). Without a main checkpoint (or without a calibrated τ) the
  flag is `null` for every observation — **never fabricated as "normal"**.
- **Main model**: `masked_transformer_main` if loaded, else `gru_ae_main`
  (`scripts/export_platform_data.py`, line 297); the checkpoint id is exported
  per observation as `stressFlagModel`.
- **Honest naming**: the positive class is **"suspected stress (anomaly)"** in
  code, export and UI (Persian: «تنش مشکوک») until L4 validation. The exported
  `ladderRung` (per field, from the sidecar `ladder_rung`, `"L2"`/`"L3"`)
  states the validation-ladder rung every flag claim is bounded by; without a
  checkpoint it is `null`.
- **Split tags**: every observation carries `split` ∈ {`train`, `dev`, `test`,
  `monitoring`} — the split of the cycle containing the acquisition date,
  mapped from `data/processed/cycles_490.parquet` +
  `data/processed/splits_locked.json` (`scripts/cycle_inputs.py::build_cycle_split_map`,
  line 343; unmapped → `monitoring`, never an in-sample claim). Split
  membership only controls which cycles enter metrics, never what is displayed;
  the platform marks `train` observations as **"Train (in-sample)"** so their
  optimistic scores/flags are readable as such.

### 4.3 The removed CWSI proxy rule (history)

Contracts v3/v4 substituted an affine CWSI formula
(`clamp(offset + max(0, CWSI − 0.45) × weight)`, formula id `cwsi_affine_v1`)
for every slot without a checkpoint and for unmapped days. **Removed in v5**:
the rule is circular — CWSI is derived from the same LST/NDVI the models see,
so a "proxy stress score" is a function of the model's own inputs, not
independent evidence (spec `model-output-ingest`: proxy allowed only with a
non-CWSI formula; none exists). Since v5, all eight slots resolve **`model`**
or **`absent`**; the baseline slots (`b0_calendar`, `b1_dsh`, `b1_cusum`) keep
the `proxy` registry *kind* only as a label of what they would need (a non-CWSI
formula artifact) — without one they are `absent` everywhere.

### 4.4 `absent`

A missing checkpoint, a sidecar-less `.pt`, a failed reconstruction, or an
observation outside every built cycle yields `score = null` + provenance
`absent` — never a substituted number, never a crash.

### 4.5 Legacy literature checkpoints (`sts_net`, `tiny_cnn_mamba`, `time2agri`)

Checkpoints `checkpoints/<id>_490.pt`, trained 2026-11-04 by
`scripts/train_literature_checkpoints.py` on `data/interim/growth_cycles_490.npz`
(train partition of 799 non-censored cycles × 36 bins × 8 channels). Pipeline
(unchanged from v4):

1. **Interpolated cycle tensors** (`scripts/cycle_inputs.py::build_field_cycles`):
   harvest-based segmentation, 36 × 15-day DSH bins, per-bin median, isolated
   interior gaps linearly interpolated; censored cycles skipped.
2. **Tokenisation** (`src/ssl_anomaly/eval/growth_ssl.py::_tokens`): robust
   z-score with checkpoint-stored center/scale; token = `[z-values (8),
   observed-mask (8), phase index (1)]` → `d_in = 17`.
3. **Leave-one-time-bin-out masked scoring** (`MaskedSSL.score`, `causal=True`):
   for every observed bin *b*, bin *b*'s values are zeroed and predicted from
   bins < *b*; error = MSE in z-space.
4. **Squash** `1 − exp(−MSE)` and formula id `<model>_490:bin_mse_1mexp`
   (`scripts/load_model_checkpoints.py::model_formula_id`).

Architectures (all small by design, `d_model = 32`, reconstructed in
`scripts/load_model_checkpoints.py::_build_model`):
- **STS-Net 3D-CAE** — convolutional autoencoder over (bins × channels), latent 16.
- **Tiny-CNN-Mamba** — CNN stem + 2 Mamba (selective-SSM) layers, `d_state` 8, latent 16.
- **Time2Agri (contrastive/masked-reconstruction arm)** — Transformer encoder
  (2 layers, 4 heads, `d_ff` 64) + task head.

## 5. Reading the field inspector (the chip row)

For one field the inspector shows, per chip, the provenance of that
observation's channels in registry order (e.g. L08-13):

`ndvi` Observed · `evi` Proxy · `savi` Observed · `ndmi` Observed ·
`tvdi` Proxy · `cwsi` Proxy · `eta` Proxy · `lst` Observed ·
`precip` Modelled · `temp` Modelled

- **مشاهدات‌شده (Observed)** — direct band math on real Landsat pixels
  (NDVI, SAVI, NDMI, LST).
- **پروکسی (Proxy)** — deterministic derivation *from* observed channels
  (EVI needs blue + coefficients; CWSI/TVDI/ETa are the formulas in §3). This
  applies to CHANNELS only — for SCORES there is no proxy state anymore (§4.3).
- **مدل‌سازی‌شده (Modelled)** — ERA5 reanalysis values interpolated to the
  acquisition date (precip, temp). Real records, but modelled origin.
- The score value carries its own chip: **Model** (checkpoint inference) or
  **Absent** (v5 has no Proxy state for scores). Below the score card, the
  **stress-flag row** shows the causal flag (برچسب وضعیت تنش: عادی / تنش
  مشکوک / بدون داده / ناموجود) plus the observation's split tag — a train-split
  observation is labelled **دوره آموزش (درون‌نمونه) / Train (in-sample)**: its
  scores and flags are in-sample and optimistic by construction.

## 6. Model freshness — honest status

- **Causal main checkpoints (`masked_transformer_main`, `gru_ae_main`)**: the
  platform slots are wired in v5 and show real checkpoint inference **if the
  frozen artifacts exist** under `checkpoints/`; otherwise the slots are
  `absent` (null scores, `stressFlag: null`, `ladderRung: null`) — the absence
  is the honest state, never filled with a formula.
- **Legacy checkpoints** were trained 2026-11-04 on cycles segmented from the
  *full* 2013–2026 archive (799 non-censored cycles). Today's scoring rebuild
  reproduces the identical cycles with unchanged segmentation code — no
  train/serve skew in the pipeline itself. The v5 masked tensors intentionally
  drop the interior-gap interpolation the legacy artifacts were trained with,
  which is why the two checkpoint families keep separate tensor builders.
- **Single-shot training**: one run, no re-training loop, no drift monitoring,
  no evaluation-gated promotion. The platform renders whatever the artifacts
  produce.
- **Scale**: all are *small* reproductions written for this thesis — not the
  original authors' released implementations and not tuned to their papers'
  full hyper-parameters.
- **No labels**: platform "validation" is unsupervised agreement (score vs
  indicator correlations, split-half, Moran's I). There is no ground-truth
  stress label set, hence no ROC/AUC/precision-recall against reality anywhere
  in the UI; the stress flag is a calibrated-FAR anomaly signal, named
  "suspected stress" until L4.

## 7. Unused opportunities (honest list)

1. **2013–2020 + 2025–2026 as observations** — SOLVED in v4: the axis is every
   acquisition date (§2).
2. **ERA5 covariates beyond precip/temp** — `weather_aligned.parquet` has 57
   columns: `et0_sum`, VPD, solar radiation, wind, soil moisture and 3/7/14/30-day
   rolling windows. None are wired. Concretely: ET0 would turn the ETa proxy
   into a water-balance-informed estimate; the 30-day precipitation window is
   the agronomically right drought signal, not the daily sum.
3. **A physically-based CWSI** — the current CWSI is a linear LST/NDVI heuristic
   with hard-coded constants (20 °C, 25 °C). With ERA5 air temperature already
   joined, an Idso/Jackson-style `CWSI = (Tc − Ta) / (Tc_upper − Ta_lower)`
   is implementable today.
4. **Real METRIC ETa** — the archive is advertised as Landsat & METRIC, but the
   platform's ETa is `NDVI × 6.5` clamped. If the METRIC ETa rasters (or the
   processing chain) are available, wiring them would replace the weakest
   displayed channel with an actual remote-sensing product.
5. **Per-pixel views** — pixel parquets exist; all views consume field-median
   statistics. Within-field heterogeneity (e.g. deficit-irrigated corners) is
   invisible.
6. **Uncertainty display** — scores carry no confidence; a committee question
   like "how stable is this score across neighbouring bins?" has no on-screen
   answer (the data for it exists: the per-bin error curves).
7. **Baseline comparison against the literature numbers** —
   `reports/literature_models_benchmark.json` exists but no view surfaces it.
8. **Neighbour definition** — kNN by centroid distance (1.8 km, ≤4), ignoring
   the registry's block/office structure which is now available in the payload.
