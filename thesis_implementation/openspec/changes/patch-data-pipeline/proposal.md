# Change: patch-data-pipeline

## Why

Owner decision (notes.md, 2026-11-15): add **patch-level analysis**. The
training path currently has NO spatial dimension — every model consumes
field-mean cycle series `(N cycles, 36 bins, 8 channels)` built from
`stats.zarr` (`src/ssl_anomaly/monitor/inputs.py:29`), so within-field
spatial heterogeneity is invisible to training and scoring. The
architecture-selection review
(`research/Architecture_Selection_for_Self_Supervised_Spatiotemporal_Anomaly.md`)
names spatial coherence as one of three mechanisms that could lower the
detection floor finding 18 measured (MDM80 censored ">S6" for ALL arms
including B1 at 5% cycle-FAR). Nothing can test that mechanism until
per-pixel patch tensors exist.

Measured today from `Data/RoI/Farms.geojson` (reprojected EPSG:32639):
median field 25.2 ha (min 2.27, max 34.6) → median ≈16.7 Landsat pixels
across, p90 17.0, max 19.6. **100% of the 490 fields fit a single 32×32
patch** (only 7.3% are smaller than 16×16). One field-aligned 32×32 patch
per field per date therefore suffices — no tiling machinery, and the
document's tiled S=16 variant is unnecessary on this dataset.

This change is deliberately **objective-independent**: the patch store is a
data foundation reusable by the patch-level trial
(`patch-level-controlled-trial`), by path B (multivariate/relational
injection families), and by any later spatial work. It changes no model, no
scoring, no platform behavior.

## What Changes

- **New exporter `scripts/extract_patches.py`** — per (field, scene, band)
  per-pixel extraction from the same Landsat C2 L2 source
  `scripts/extract_pixels.py` already reads, reusing `io/landsat.py` QA
  masking (`quality_mask`, dilated) and scale handling verbatim.
- **Per-cycle per-bin aggregation** — per-pixel median over the valid
  acquisitions inside each 15-day bin of the existing 36-bin cycle grid
  (`monitor/inputs.py:32-34`, cycles from `cycles_490.parquet`), producing
  patch tensors `(field, cycle, bin, 8, 32, 32)` fp16 ≈ **1.0 GB** plus
  pixel-validity `(field, cycle, bin, 1, 32, 32)`, the static in-field
  polygon mask `(field, 1, 32, 32)`, bbox origins, per-bin observation
  counts and majority sensor ids — written to
  `Data/Processed/satellite/patches.zarr` (canonical root, AGENTS.md §6).
- **Field-aligned geometry** — crop each field's bounding box, pad (never
  resample) to 32×32; the polygon mask excludes neighbouring fields
  (different phenophases must not leak into spatial context).
- **Leakage-free normalization artifact** — per-channel, per-sensor
  robust median/IQR (Landsat 8/9 only; L7 is not in the archive,
  `io/landsat.py:15,33`) computed on **train-split fields × train periods
  only** (splits_locked `9aa5eb11…`), frozen with SHA-256 into the store.
- **Operator ergonomics (owner requirements 16/18/19/20 in notes.md)** —
  `--smoke`, `--estimate-runtime` (timed extrapolation BEFORE any full
  run), `--resume` (per-date incremental writes with a completion
  manifest), CPU-executable, progress output, and a provenance manifest
  (source products, QA bit list, scale factors, hashes).
- **Extraction ≠ training (owner standing invariant, 2026-11-15)** — the
  store covers ALL fields because evaluation needs them; training consumers
  SHALL exclude holdout farms/dates via the fail-closed assertion of
  `training-holdout-invariant` (holdout fixed BEFORE implementation, always).
- **Explicit non-goals:** no METRIC-derived per-pixel products beyond the 8
  B1 channels (ndvi + blue, green, red, nir, swir1, swir2, lst); no
  Landsat 7 support; no model/scoring/platform changes; no ETa/CWSI
  per-pixel extraction; no inner-buffer or patch-size ablations (flags
  recorded, defaults locked).
