# Platform scoring & data methods — precise reference

**Date:** 2026-11-07 · Scope: every value the platform displays: where it comes
from, the exact formula that produces it, and its provenance label. This is the
documentation companion to `wire-platform-to-real-data`; every claim cites the
code that implements it.

## 1. Data lineage (one paragraph)

`Data/Processed/satellite/stats.zarr` (490 fields × 538 Landsat dates,
2013-03-30 → 2026-09-10, bands `blue green red nir swir1 swir2 lst` +
`valid_frac`) → `scripts/export_platform_data.py` computes per-field
spectral indices, builds phenology cycles, scores cycles with trained
checkpoints, joins ERA5 weather, and writes
`platform/src/data/series_khuzestan.json` (48 monthly observations per field)
+ `farms_khuzestan.json` (490 records with registry metadata). The React
platform renders those JSONs verbatim — it computes **no** data values itself
except descriptive statistics (means, correlations) over them.

## 2. Why the time axis is 2021-01 … 2024-12 (not 2013)

The **archive** is 2013–2026 (538 dates; all of it is used by *training* and by
the raster tile server, which serves every scene date). The **observation grid**
is different: the exporter samples 48 fixed monthly dates

```python
sample_dates = [f"{y}-{m:02d}-15" for y in range(2021, 2025) for m in range(1, 13)]  # export_platform_data.py:143-148
```

and maps each to the nearest Landsat acquisition within ±13.95 days
(`MAX_OFFSET_DAYS = 1.5 × 9.3-day revisit`, `export_platform_data.py:37-38`).
Each observation's *actual* satellite date is stored in `acquisitionDate`
(which is why the raster overlay can follow the slider). This 2021–2024 grid
was a hard-coded choice of the original platform commit (`69f9fbe`) and was
never derived from data availability — **it is not a data limitation**. The
2013–2020 and 2025–2026 portions of the archive flow into the platform only
indirectly (cycle tensors, checkpoint training, per-year baselines), not as
slider-selectable observations.

**Extension path (not in scope yet):** widen `range(2021, 2025)` to the cube's
date span (e.g. 48 → ~168 monthly samples) and regenerate. Everything
downstream (weather join, staleness guard, provenance, UI) is already
axis-length-agnostic — the frontend derives `DATES`, slider bounds and labels
from the payload (`data/data.ts: deriveDates`, `LAST_IDX`).

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

Rules the UI enforces (`data/data.ts::normaliseObs`): a `null` channel is
**always** labelled `absent` (never modelled/measured) and renders "—"; a
present value keeps the label above. Missing observations (no acquisition
within the ±14 d window) carry all-null channels + `absent`.

## 4. Anomaly scores — the 7 detectors

### 4.1 Shared scoring pipeline for checkpoint models (`model` provenance)

Applies to `sts_net`, `tiny_cnn_mamba`, `time2agri` (checkpoints
`checkpoints/<id>_490.pt`, trained 2026-11-04 by
`scripts/train_literature_checkpoints.py` on `data/interim/growth_cycles_490.npz`,
train partition of 799 cycles × 36 bins × 8 channels):

1. **Cycle tensors** (`scripts/cycle_inputs.py::build_field_cycles`): the
   harvest-based segmentation `segment_cycles` (min 180 d, max 540 d,
   prominence 0.15) cuts each field's NDVI series into non-censored growing
   cycles; observations are binned into **36 phase bins of 15 days** counted
   from the harvest date (DSH — days since harvest), each bin = median of the
   observations inside it; isolated interior gaps are linearly interpolated.
   Channel 0 = NDVI, channels 1–7 = the zarr bands → tensor `(36, 8)`. Censored
   cycles or cycles with < 3 observations are skipped (799 buildable today —
   the same count as the training export).
2. **Tokenisation** (`src/ssl_anomaly/eval/growth_ssl.py::_tokens`): robust
   z-score per channel with median center and MAD×1.4826 scale (stored in the
   checkpoint); each of the 36 time steps becomes a token
   `[z-values (8), observed-mask (8), phase index (1)]` → `d_in = 17`.
3. **Leave-one-time-bin-out masked scoring** (`MaskedSSL.score`, `causal=True`
   — exactly the training-time masking): for every observed bin *b*, bin *b*'s
   band values are zeroed (and all *future* bins, because causal) and the model
   must predict bin *b* from bins `< b` only; the error is the MSE between the
   predicted and true band channels of bin *b*, in z-space.
4. **Squash** (`load_model_checkpoints.squash_bin_error`):
   `score = 1 − exp(−MSE)` — a monotone map of `[0, ∞) → (0, 1)` that preserves
   ranking and keeps the shared 0–1 display, colours and the
   `ANOMALY_THRESHOLD = 0.55` meaningful. Higher = more anomalous (the cycle
   deviates from what the model — trained on normal phenology — expects).
   Formula id recorded per observation: `<model>_490:bin_mse_1mexp`.
5. **Mapping to observations** (`resolve_observation_scores`): an observation
   gets a `model` score only when its acquisition day falls inside a built
   cycle at a finite bin; otherwise rule 4.3 below applies.

Architectures (all small by design, `d_model = 32`, reconstructed in
`load_model_checkpoints._build_model`):
- **STS-Net 3D-CAE** — convolutional autoencoder over (bins × channels),
  latent 16.
- **Tiny-CNN-Mamba** — CNN stem + 2 Mamba (selective-SSM) layers, `d_state` 8,
  latent 16.
- **Time2Agri (contrastive/masked-reconstruction arm)** — Transformer encoder
  (2 layers, 4 heads, `d_ff` 64) + task head; scoring uses
  `encode_sequence` → `task_head` reconstruction.

### 4.2 The proxy rule (`proxy` provenance) — what "جانشین" means

Four of the seven detector slots have **no faithful checkpoint artifact**:
`b0_calendar`, `b1_dsh`, `b1_cusum` are *baseline heuristics* by design, and
`masked_transformer`'s saved checkpoints tokenise a different input schema
(dtime/doy/sensor, not the 36×8 cycles) so they cannot score cycle tensors
honestly (BUG-23). For those slots — and for any observation the checkpoint
models cannot map — the exporter substitutes a **deterministic formula of CWSI**
(`cycle_inputs.py::proxy_scores`):

```
stress = max(0, CWSI − 0.45)
score(m) = clamp( offset(m) + stress × weight(m), 0.05, 0.95 )
```

| slot | offset | weight |
|---|---|---|
| b0_calendar | 0.18 | 0.65 |
| b1_dsh | 0.15 | 0.80 |
| b1_cusum | 0.12 | 0.85 |
| masked_transformer | 0.14 | 0.92 |
| sts_net (unmapped days) | 0.11 | 0.94 |
| tiny_cnn_mamba (unmapped days) | 0.10 | 0.96 |
| time2agri (unmapped days) | 0.12 | 0.90 |

The banner sentence **"Scores labelled Proxy are formula-based baselines, not
checkpoint inference"** means exactly this: a Proxy chip = the number came from
the affine CWSI rule above (formula id `cwsi_affine_v1`), NOT from a neural
network. The differing offsets/weights only *spread the seven curves apart so
they are visually distinguishable in comparison charts* — they encode no
modelling claim. Anywhere you need "the model's opinion", read the chips
labelled **Model** (purple).

### 4.3 `absent`

A checkpoint that exists but fails to load, or an observation outside every
cycle, yields `score = null` + `absent` — never a substituted number.

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
   `src/ssl_anomaly/phenology/cycles.py`); censored/incomplete spans are
   dropped. 799 buildable cycles across 490 fields today.
2. **Bins** each cycle into **36 phase bins of 15 DSH days** (≤ 540 days),
   taking the median observation per bin, channel 0 = NDVI + the 7 spectral
   bands (`scripts/cycle_inputs.py::build_field_cycles`).
3. **Scores per phase**: the trained models reconstruct each bin from the
   *preceding bins of the same cycle* (causal leave-one-bin-out). An anomaly
   score thus means "this field deviates from what normally happens at this
   **phase** of the cycle" — the phase-aware reading the thesis claims. The
   CWSI proxy rule (§4.2) has **no phase awareness** — it only reads the
   magnitude of CWSI that day — which is exactly why model-provenance scores
   are the scientifically meaningful ones and proxy scores are labelled as
   such.

A visualization of the segmentation (shaded cycle spans + harvest markers on
the temporal charts, and the binned DSH-axis curve) is queued as openspec
candidate `phenology-cycle-visualization` in `todo.md`.

## 5. Reading the field inspector (the chip row)

For field L08-13 the inspector shows, per chip, the provenance of that
observation's channels in registry order:

`ndvi` Observed · `evi` Proxy · `savi` Observed · `ndmi` Observed ·
`tvdi` Proxy · `cwsi` Proxy · `eta` Proxy · `lst` Observed ·
`precip` Modelled · `temp` Modelled

- **مشاهدات‌شده (Observed)** — direct band math on real Landsat pixels
  (NDVI, SAVI, NDMI, LST).
- **پروکسی (Proxy)** — deterministic derivation *from* observed channels
  (EVI needs blue + coefficients; CWSI/TVDI/ETa are the formulas in §3), not a
  direct measurement. For the **score card** (امتیاز), Proxy means §4.2.
- **مدل‌سازی‌شده (Modelled)** — ERA5 reanalysis values interpolated to the
  acquisition date (precip, temp). Real records, but modelled origin, which is
  precisely why the label distinguishes them from satellite observations.
- The score value itself (e.g. ۰.۰۲۵) carries its own chip: **Model** (trained
  checkpoint inference) or **Proxy** (CWSI rule) or **Absent**. L08-13's 0.025
  at the inspected date was a Proxy observation — that day does not fall inside
  a checkpoint-scored cycle bin (or the score predates cycle coverage), so the
  honest number shown is the formula value.

## 6. Model freshness — honest status

- **Training data**: checkpoints were trained 2026-11-04 on cycles segmented
  from the *full* 2013–2026 archive (799 cycles). Today's scoring rebuild
  produces the identical 799 cycles with unchanged segmentation code — no
  train/serve skew in the pipeline itself.
- **Single-shot training**: one run, 15 epochs, no re-training loop, no
  drift monitoring, no evaluation-gated promotion. The platform renders
  whatever the November artifacts produce.
- **Scale**: all three are *small* reproductions (`d_model` 32, ≤ ~100k
  parameters) written for this thesis — not the original authors' released
  implementations and not tuned to their papers' full hyper-parameters.
- **Not wired**: `masked_transformer` (artifact schema mismatch), `gru_ae`
  (trained but not registered as a platform score), JEPA (architecture added
  2026-11-07, no platform scoring yet).
- **No labels**: platform "validation" is unsupervised agreement (score vs
  indicator correlations, split-half, Moran's I). There is no ground-truth
  stress label set, hence no ROC/AUC/precision-recall against reality anywhere
  in the UI.

## 7. Unused opportunities (honest list)

1. **2013–2020 + 2025–2026 as observations** — the archive supports a ~3.5×
   longer slider (§2); currently only cycle-building and training see those
   years.
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
