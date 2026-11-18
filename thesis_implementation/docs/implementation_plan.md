# Implementation Plan

Companion to `docs/final_plan.md` (detailed, Persian) and `docs/initial_plan_assumptions.md`. This document is the English, execution-oriented plan and keeps placeholders for future phases (Web GIS labels, knowledge fusion, multi-crop, edge).

## 0. Executive summary

- Unit of analysis: **cycle** (not year); axis: **days-since-harvest** (+ GDD).
- First build a cheap, interpretable robust statistical baseline (B0-B2); add SSL only if it beats it (G2).
- Data layer first: `fields.zarr` (field x time x band) + Parquet metadata; raster cube only in Phase 3.
- Rust is gated behind profiling; interface designed from day 1.
- Everything runs on a laptop (throttled, checkpoint/resume); cloud GPU optional.

## 1. Phase gates

| Phase | Content | Exit gate |
|---|---|---|
| 0 | Data audit, `fields.zarr`, cycle segmentation, QC on 30 fields | G0: harvest detection acceptable; most fields have multiple complete cycles |
| 1 | Phenology-aware statistical baselines B0-B2 + evaluation | G1: B1 beats B0 on synthetic injection and proxies |
| 2 | 1D SSL models on field-level series | G2: SSL beats B1 with CI, else limited to embedding/retrieval |
| 3 | Patch-level, 3D-CAE, XAI, `cube.zarr` | G3 (Rust): only after profiling |

No phase starts before its previous gate passes. Each phase ships as module + tests + thin CLI; notebooks are EDA only.

## 2. Data layer

### Layout

```
data/
  raw/landsat/            # original GeoTIFFs (read-only, DVC)
  geo/fields.gpkg         # field geometries
  geo/fields.parquet      # farm_id, block, variety, region, age/ratoon, ...
  interim/field_mask.tif  # field_id raster on 30 m grid (built once)
  interim/zonal/*.parquet # per-scene zonal output (checkpoint unit)
  processed/fields.zarr   # Phase 1: (field, time, band), float32
  processed/era5.zarr     # daily (time, var)
  processed/cube.zarr     # Phase 3, optional
  manifests/*.sqlite      # per-scene processing state
```

### Key decisions

- Zarr v3 with sharding; store only CRS + affine transform (GeoZarr still stabilizing). No consolidated metadata needed for local store.
- `cube.zarr`: int16 with scale_factor/add_offset from product metadata, zstd level 3 + shuffle. `fields.zarr`: float32.
- Weather in separate store; GDD computed at use time (Tbase is a hyperparameter).
- Metadata only in `fields.parquet`; Zarr attrs keep version, CRS, source hash, band order.
- Spectral indices computed after ingest (not during), to allow input ablations without re-ingest.

### Ingest pipeline (Phase 0)

Build `field_mask.tif` once, then per scene: read bands -> quality mask (cloud/shadow/cirrus/snow from QA_PIXEL, bits verified against product docs) -> zonal stats via `np.bincount` -> atomic parquet write. Aggregate into `fields.zarr`.

Resource rules: throttle BLAS threads (default 2), lower process priority, wait for memory headroom, progress bar + ETA, per-item checkpoint/resume via SQLite Manifest, crash of one scene does not kill the run.

## 3. Phenology-aware core

1. QC per (field, time): median of valid pixels; drop or down-weight observations with low valid fraction; remove point outliers (Hampel) so they are not mistaken for harvest.
2. Smoothing: Whittaker-Eilers on irregular samples (weighted); tune lambda via CV (random observation deletion). Savitzky-Golay on 8-day grid as comparison in Sprint 0.
3. Cycle segmentation: harvest = NDVI trough with sufficient prominence, preceded by high plateau and followed by rise. Cycle = interval between consecutive harvests. First/last cycles marked censored and excluded from baseline (but still scored). Replant detected from long gap with low NDVI or metadata; resets ratoon counter.
4. Phase axis: primary `days-since-harvest` (dsh); bin ~15 days (~28 bins/cycle); three coarse stages for interpretation (establishment/tillering, main growth to plateau start, maturation to harvest). 10-phase scheme replaced by this combination.
5. Strata + baseline: each cycle belongs to stratum (cycle type plant/ratoon-n) x variety group (if available). Baseline per (stratum, bin, band) = median + MAD over normal cycles of all fields in stratum, leave-one-out for scored cycle. Field effect via shrinkage offset: `delta_f = n_f/(n_f+kappa) * median(x - m)`, kappa ~2-3. Fall back to coarser stratum when a bin has fewer than `min_n` cycles.
6. Normal-cycle selection: 3 iterations of trimming (remove top q% anomaly burden per stratum, q~10-20%, sensitivity tested). Add ETa/yield as independent filter if available. Do not use CWSI for normal selection (circularity).
7. Score: `z = (x - m) / max(1.4826*MAD, floor)` per band; aggregate per bin `S = sqrt(mean_k z_k^2)`, keep per-band sign for interpretation. `floor` from low percentile of all MADs.
8. Continuous anomaly (run): flag when S > 3.5 for >=2 consecutive observed bins. CUSUM/EWMA on z as second detector for slow changes.
9. Missing data: no interpolation between bins except +/-1 bin; unobserved bins stay NaN and unscored. Long gap without observation is itself a quality feature (`max_gap_days` per cycle) reported.

## 4. Key experiments

- E-ALIGN: compare DOY+/-15, dsh, GDD-from-harvest (tunable Tbase), landmark registration (piecewise linear alignment of harvest/plateau-start/peak/next-harvest). Metrics: within-bin scatter of normal cycles (lower MAD better), leave-one-out median prediction error (CV), stability under 20-50% random observation deletion. Choose by metrics, not intuition.
- E-SEG: shift harvest dates +/-16 and +/-32 days; if scores unstable, problem is segmentation not model.
- E-INTRA: run algorithm at pixel/sub-field level on 32 Farms_subset fields; report harvest-date scatter within field. If a large fraction exceeds ~2 observation intervals (~30 days), field-mean alone is insufficient and Phase 3 intra-field zoning must be prioritized.
- E-NORM: q in {0,10,20,30}%; report Spearman stability of anomaly ranking across runs.

## 5. SSL models (Phase 2, only after G1)

Input: each cycle is a token sequence (one token per real observation, no imputation): features = bands (robust standardized), valid_frac, delta-t since previous observation; conditioning = dsh and GDD (normalized), sin/cos(DOY), ratoon_no, variety (if available), sensor flag (L8/L9), aggregated weather between observations (total precip, mean temp, ...). Start with bands + LST; indices in ablation.

Pretext: masked observation modeling, 15-30% random tokens plus consecutive blocks of 1-3 tokens mimicking cloud gaps. Huber loss on masked tokens; trim ~10% highest-loss samples per batch for robustness to contaminated training data (anomalies in training). Train only on `active` cycles from trimming.

Architectures in order: (M-A) small GRU autoencoder (CPU); (M-B) 1D Transformer encoder (3-4 layers, d=64, <1M params) with masked modeling (CPU/small GPU) - main Phase 2 model; (M-C) small CNN-Mamba (GPU/Colab) for comparison (verify selective-scan CUDA kernels in Sprint 0); (M-D) 3D-CAE only Phase 3 on patches.

Anomaly score: (1) reconstruction residual with robust per-phase scaling to z units (comparable to Section 3); (2) kNN cosine distance to normal cycles of same stratum, also used for retrieval of similar cycles for interpretation; (3) combine by rank-average only if each individually beats B1. Do not fit learned weights on synthetic data (risk of overfitting to injected anomaly type).

Training/leakage: Farms_subset (32 R11 fields) excluded from training, baseline, model selection, tuning. CV: K=5 block by region on remaining fields; baseline and normalization stats built only from training fields of each fold. Early stopping on validation reconstruction loss (not anomaly metric). 5 seeds per config, report mean + CI. Weather ablation on/off to separate "unusual vs normal cycles" from "unusual given that period's weather".

## 6. Evaluation

No real labels; evidence is multi-source consistency, reported as such (not "accuracy").

Four evidence types: V1 synthetic injection (NDVI drop depth/length/phase, phenology delay, LST increase) -> sensitivity and detection delay; V2 weak proxies (low ETa/ETref, high CWSI, per-cycle yield) -> Spearman and AUC-PR on proxy labels; V3 known events + blind expert review of top-K -> precision@K; V4 stability (random observation deletion, harvest-date shift, q change, seed change).

Baseline ladder: B0 calendar z-score; B1 phase-aware z-score (core); B2 B1 with GDD/landmark axis; B3 IsolationForest/ECOD on per-cycle features; B4 GRU-AE; B5 masked Transformer; B6 CNN-Mamba. If B5/B6 do not beat B1, report it as a finding (G2).

Primary metric: AUC-PR + recall at fixed alert rate (e.g. 5% of cycles) + detection delay + Spearman with proxies. AUC-ROC/F1 secondary. Sample unit is the field (cycles within a field are dependent); cluster bootstrap on fields or region blocks for 95% CI. Pairwise comparison on identical folds; Wilcoxon signed-rank on per-field metric differences with effect size and CI; Holm correction for multiple comparisons. Main CV: block by region; leave-one-year-out only for temporal stability (year defined by cycle start); calendar split (last complete cycle 2025-2026 as temporal test) for drift control. Framework: custom on MLflow with simple model/metric registry; chronobench optional.

## 7. Engineering

Repo layout: `pyproject.toml`, `uv.lock`, `dvc.yaml`; `conf/` (Hydra: base, profile/laptop, profile/colab, data, model, input, experiment); `src/ssl_anomaly/` (io, phenology, baseline, models, train, eval, xai, utils); `tests/` (unit, regression golden, parity); `scripts/` (thin CLI); `notebooks/` (EDA only); `rust/` (after G3).

Decisions: Hydra + structured configs; MLflow local (SQLite backend); DVC for data and stages; Hydra multirun in Phase 1, Optuna after G2 with nested MLflow runs; pytest + pytest-cov with golden regression and parity tests; standard logging + rich; pyright + ruff; uv lockfile.

Tests: unit on synthetic series with known answers (e.g. trapezoidal series with known harvests, tolerance <= one observation interval); golden regression on 3 selected fields (harvest dates, per-bin median, z-scores in small .npz, any code change must preserve or be consciously approved); parity when Rust is added.

Checkpoint/export: Lightning `.ckpt` for training resume; SafeTensors for final release with config + normalization stats (model unusable without `norm_stats.json`); ONNX only when real edge need arises and only for GRU/Transformer (Mamba export usually problematic); quantization (FP16/INT8) only after FP32 accepted with allowed metric drop. Determinism: seed everything, deterministic algorithms warn-only, log git SHA, data version hash, uv.lock, splits.json, seed in MLflow.

Laptop profile: 2 workers, 2 BLAS threads, min 2 GB free, low priority, CPU, batch size 64. Every CLI calls `limit_threads()` before importing numeric libs, lowers priority, shows progress + ETA.

## 8. Rust (gated, not Phase 1)

Principle: reference Python/NumPy implementation with tests first; Rust replaces only profiled bottlenecks with identical output. Phase 1 needs no Rust: one-time `field_mask` + per-scene `bincount` on tens of MBs (verify by measurement).

G3 entry (any): profiling shows one stage >~30% of total time and full run >~30 min; or Phase 3 pixel-level processing infeasible in NumPy (time/memory). Re-tune thresholds after first real profile.

Target order: 1) no Rust (field_mask + bincount); 2) ready libs (`oxidized-rasterstats`, `eo-processor`) - speedup claims unverified, benchmark with parity on one real scene; 3) terrio for I/O (verified pure-Rust, pre-1.0) for cube conversion; 4) custom PyO3 + maturin (batched Whittaker, harvest detection/segmentation, robust baseline on 1e6-1e7 pixel series, phase binning) with rayon and threads = cfg.workers.

Interface from now: `PhenologyBackend` Protocol in `phenology/backends.py` with `whittaker_batch` and `robust_baseline`; `get_backend(name)` returns numpy or rust; config key `backend: numpy|rust`; mandatory parity tests before merge; log real speedup in MLflow. No Rust code before G3.

## 9. XAI

Phase 1: statistical baseline is inherently interpretable (per-band, per-bin contribution, aggregated to three coarse stages). Phase 2-3: Captum (Integrated Gradients) + temporal occlusion window; aggregate to bins/stages; specialized time-series XAI (tint, tsCaptum) and meteors optional (unverified here). Faithfulness: deletion/insertion AUC at phase level + sanity check (randomizing model weights must destroy attribution). Channel dropping via Hydra multirun over `input.drop` (each band, LST, weather) with 5 seeds, report metric change with CI.

## 10. Risks

| Risk | Mitigation |
|---|---|
| Wrong harvest detection | visual QC on 30 fields, E-SEG, compare with harvest records |
| Too few normal cycles | hierarchical pooling, shrinkage offset, min_n |
| Contaminated normal cycles | iterative trimming, trimmed loss |
| Circular validation (LST vs CWSI) | ablation without LST; rely on ETa/yield |
| Distribution shift (L8->L9, variety, management, climate) | sensor flag, temporal test, stability reporting |
| Label-free overclaiming | combine V1-V4, state limits explicitly |
| Laptop overheating | throttle, low priority, resume |
| Immature tools (terrio, GeoZarr) | fallback to rasterio+xarray, pin versions |
| Scope creep | gates G0-G3 |

## 11. Future hooks (placeholders)

These are **not implemented now** but the design must leave seams:

- **Web GIS expert labels**: define an ingestion interface (`labels/` module) that accepts spatial expert annotations as weak supervision/validation; never make labels the sole training signal.
- **Knowledge fusion (next phase)**: keep self-supervised outputs (embeddings, anomaly scores, per-phase attributions) as a stable API so a later module can fuse them with crop knowledge (articles, books, Q&A). Store embeddings in a retrievable form (kNN index) from Phase 2.
- **Multi-crop**: `CycleSegmenter` and `phase_axis` are replaceable; only sugarcane implementation ships in v1.
- **Intra-field**: keep a path from field-mean to patch-level (cube.zarr, 3D-CAE) gated by E-INTRA.
- **Incremental/transfer learning**: model export includes config + norm stats; design training to support fine-tuning on new fields/seasons without full retrain.
- **Frugal AI / edge**: track model size, latency, memory; keep ONNX/quantization as a later, measured step; benchmark on drone-class hardware only after FP32 acceptance.
- **Transferability**: version datasets and splits; export weights as SafeTensors; document normalization stats.

## 12. Inputs needed from user (before Sprint 0)

1. Any harvest/planting date records (even partial/subset).
2. Variety, field age, ratoon metadata.
3. Per-cycle yield (if available).
4. List of known events (flood, frost, salinity, irrigation cut) and an available expert for top-K review.

## 13. Sprint 0

1. Data audit: dates, per-field valid fraction, number of possible cycles, confirm whether CWSI is derived from LST.
2. Ingest: field_mask + zonal with resume + fields.zarr.
3. Segmentation: run + visual QC on 30 fields; compare with harvest records; output G0.
4. B0 and B1: calendar and phase-aware baselines + synthetic injection + E-ALIGN; output G1.
5. Low priority: chunking benchmark and terrio trial for Phase 3.

## 14. Open questions (answered or to be answered)

| Question | Status |
|---|---|
| Phenology method | Whittaker + harvest rules (scipy); TIMESAT comparison only; no DL yet |
| Normal cycles | data-driven iterative trimming + ETa/yield filter; expert for validation; no CWSI |
| Zarr chunking | Phase 1 single chunk sufficient; Phase 3 cube: benchmark C1-C3 |
| Model format | .ckpt for resume, SafeTensors for release; ONNX later |
| Orchestrator | DVC pipeline + Manifest (item-level); no Prefect/Airflow |
| terrio trial | yes, timeboxed, only for cube conversion in Phase 3; rasterio+xarray fallback |

## 15. References

- Joshi N., Simms D.M., Burgess P.J. (2024). Automating the derivation of sugarcane growth stages from Earth observation time series. Remote Sensing 16(22), 4244.
- EOPF Explorer: GeoZarr standards status.
- Pangeo showcase: GeoZarr sharding in GDAL (2026-03-04).
- terrio (PyPI).
- Eilers P.H.C. (2003). A perfect smoother. Analytical Chemistry 75(14), 3631-3636.
