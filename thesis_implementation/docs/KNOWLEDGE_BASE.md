# KNOWLEDGE_BASE — thesis_implementation

> **Persistent codebase knowledge base.** Human-readable companion to the `mnemon` memory
> store (`thesis`) and the Qoder Repo Wiki plan (`.qoder/repowiki/wiki_plan.yaml`).
> **Keep this current every session** — see [Maintenance](#maintenance).
> Last updated: 2026-11-11 · git baseline: `87071cd`

## Table of contents
1. [What this is](#1-what-this-is)
2. [Two-repo workspace & data roots](#2-two-repo-workspace--data-roots)
3. [Phase gates & validation ladder](#3-phase-gates--validation-ladder)
4. [Architecture & end-to-end data flow](#4-architecture--end-to-end-data-flow)
5. [Module map (`src/ssl_anomaly`)](#5-module-map-srcssl_anomaly)
6. [SSL models & training](#6-ssl-models--training)
7. [Evaluation & research questions](#7-evaluation--research-questions)
8. [Validation dashboard (platform)](#8-validation-dashboard-platform)
9. [Pipeline→UI bridge & tiles](#9-pipelineui-bridge--tiles)
10. [Config, CLI & scripts](#10-config-cli--scripts)
11. [Testing & verification gates](#11-testing--verification-gates)
12. [Provenance & scientific invariants](#12-provenance--scientific-invariants)
13. [Open questions & known discrepancies](#13-open-questions--known-discrepancies)
14. [Maintenance](#maintenance)
15. [Changelog](#changelog)

## 1. What this is

`ssl_anomaly` (v0.1.0) is the implementation of an MSc thesis: **self-supervised,
phenology-aware anomaly detection** on field-level Landsat time series for sugarcane
water-and-salinity stress (Amirkabir agro-industry, Khuzestan, Iran; ~490 fields;
Landsat/METRIC 2013–2026 + ERA5). It learns *normal* multi-year crop phenology and flags
deviations **without labeled stress data**. Owner: Mahdi Kalantari; Shahid Beheshti
University, Remote Sensing & Geoinformatics.

Core stance: detect **phenology-phase anomalies** (deviation from the normal curve *at the
same growth phase*), not day-of-year or raw magnitude. The CWSI affine proxy is
magnitude-only; only checkpoint models are phase-aware.

Sources: `README.md:1-19`, `AGENTS.md:1-45`, `pyproject.toml:5-12`.

## 2. Two-repo workspace & data roots

| Repo | Role |
|------|------|
| `thesis_implementation` (this) | ML pipeline, Rust backend, eval harness, React dashboard |
| `thesis_research` | literature review, Obsidian vault, proposals, memory logs |

Real data is **outside both repos**, DVC-tracked / gitignored, never committed:
- `D:\RS\Thesis\Data\Processed\` — canonical (e.g. `satellite/stats.zarr`, `growth_cycles_490.npz`, `cycles_490.parquet`, `splits_490.json`).
- `D:\RS\Thesis\Data\Metric\products\` — METRIC suite (ETaDaily, CWSI_ET, CWSI_LST, ETinst, ETrF, … + `interpolation/` daily rasters).

Remotes: `github.com/Mahdikalantari555/thesis_implementation` and `…/thesis_research`.
Sources: `AGENTS.md:80-86`, `src/ssl_anomaly/eval/real_archive.py:29-33`.

## 3. Phase gates & validation ladder

Gated development — a phase may not proceed until its gate passes:

| Phase | Content | Gate |
|-------|---------|------|
| 0 | data audit, `fields.zarr`, cycle segmentation, QC | G0 harvest detection acceptable |
| 1 | robust baselines B0–B1 + eval | G1 B1 beats B0 on synthetic + proxies |
| 2 | SSL: GRU-AE & masked 1-D Transformer | G2 SSL beats B1 with CI |
| 3 | patch/intra-field + Rust acceleration | G3 profiling justifies Rust |

SSL training is gated on the baseline; `scripts/train_ssl.py:220-227` refuses to run
without a passing baseline gate.

**Validation ladder** (every claim states its rung): L1 learns growth patterns → L2 detects
controlled deviations → L3 generalizes across years/farms → L4 agrees with independent
agronomic evidence → L5 beats baselines. "anomaly" ≠ "stress" before L4.
Sources: `README.md:9-19,107-111`, `AGENTS.md:35-40`, `docs/methods_explained.md` §13.

## 4. Architecture & end-to-end data flow

```
Landsat scenes
  → io.load_scene + quality_mask (QA_PIXEL) + SR/ST scaling
  → field_mask + zonal_scene (per-field bincount)
  → aggregate_to_zarr  ⇒ fields.zarr / stats.zarr
  → add_spectral_indices + Whittaker smoothing
  → detect_harvests / segment_cycles  ⇒ cycles.parquet
  → phase_bin (days-since-harvest, 36×15-day bins)
  → trimmed_normal_cycles + fit_baseline  ⇒ baseline.npz
  → score_all_cycles  ⇒ scores.parquet
  → gated SSL training (CycleTokenizer → SSLLitModule)
  → eval (synthetic injection, LOYO/spatial CV, RQ1–RQ8, XAI)
  → export_release (SafeTensors)  ⇒ releases/
  → export_platform_data + serve_tiles  ⇒ dashboard
```

Backend abstraction: `PhenologyBackend` Protocol (`backends/__init__.py:18`) with a NumPy
reference and a Rust implementation; `get_backend` (`:38`) loads `ssl_anomaly_rs` at
runtime, parity enforced at `rtol=1e-6`. DVC stages mirror this flow (`dvc.yaml`).

## 5. Module map (`src/ssl_anomaly`)

- **`config.py`** — Hydra structured dataclasses. `PhaseAxis` (doy/dsh/gdd/landmark, `:18`),
  `Backend` (`:25`), `IngestCfg` SR scale 0.0000275/−0.2, ST 0.00341802/+149 (`:112`),
  `PhenologyCfg` Whittaker λ=100, 180–540-day cycles, DSH, 15-day bins (`:136`),
  `BaselineCfg` min_n=5, κ=2.5, threshold 3.5, `use_cwsi_for_selection=False` "never True
  (circularity)" (`:159`), `SSLCfg` mask 0.25, Huber δ=1.0 (`:209`).
- **`io/`** — `landsat.py` (`parse_scene_id:36`, `quality_mask:45`, `load_scene:83`),
  `field_mask.py` (`build_field_mask:25`), `zonal.py` (`zonal_scene:19`,
  `zonal_scene_from_paths:108`), `zarr_store.py` (`aggregate_to_zarr:49`),
  `stats_zarr.py` (`StatsZarrReader:26`, 8 statistics), `era5.py` (GDD `:79`).
- **`phenology/`** — `smoothing.py` (`whittaker_smooth:17`, `to_daily_grid:61`),
  `cycles.py` (`Cycle:25`, `detect_harvests:60`, `segment_cycles:133`), `align.py`
  (`compute_dsh:17`, `phase_bin:89`, strata `:157`), `indices.py` (NDVI/EVI/NDWI).
- **`baseline/`** — `robust.py` (`fit_baseline:133` per-stratum median/MAD×1.4826 +
  shrinkage offset n/(n+κ); `lookup_median_scale:196` coarse fallback), `trimming.py`
  (`trimmed_normal_cycles:27`, never CWSI), `score.py` (`score_cycle:11`, `flag_runs:79`
  ≥2 consecutive bins > 3.5, CUSUM/EWMA). Comparators: `b0_calendar.py`,
  `b2_phenology_axes.py`, `b3_tabular.py` (iForest/ECOD), `operational.py` (NDVI/CWSI
  alarms, RF, HistGBDT, recall/precision@alert-budget).
- **`backends/`** — Protocol + NumPy reference; Rust wheel loaded at runtime (G3).
- **`export/`** — `safetensors_io.py` `export_release:43` writes `model.safetensors` +
  `model_config.json` + `norm_stats.json` + `meta.json` (git SHA, uv.lock hash, seed). No pickle.
- **`utils/`** — `throttle.py` (BLAS threads, priority, RAM headroom), `seeds.py`,
  `manifest.py` (SQLite resumable ingest), `tracking.py` (local MLflow SQLite), `arrays.py`
  (MAD, Hampel, contiguous runs).

## 6. SSL models & training

- `models/tokenizer.py` — `CycleTokenizer:17` robust standardization + Δt/DSH/DOY/sensor/
  ratoon/weather channels; `mask_tokens:155` random + cloud-block masking.
- `models/gru_ae.py` — `GRUAutoencoder:15` bidirectional encoder, masked Huber loss (`:108`).
- `models/masked_tf.py` — `MaskedTransformer:73` MAE-style masking (`:149`).
- `models/pretexts.py` — `PretextTransformer:24`; RQ2 arms `masked_recon, traj_contrastive,
  anomaly_degradation, time2agri` (`:22`); InfoNCE (`:111`); `Time2AgriModel:455`.
- Literature comparators: `sts_net.py`, `cnn_mamba.py` (pure-PyTorch selective scan),
  `jepa.py` (latent prediction).
- `train/data.py` (`CycleDataset:23`, `cycle_collate:40`), `train/lit_module.py`
  `SSLLitModule:18` — trimmed masked-Huber loss (`:62`), AdamW + ReduceLROnPlateau.

Current released checkpoints are deliberately small (`d_model=32`, ~1e5 params, 15 epochs,
single-shot, trained 2026-11-04); retraining is tracked in OpenSpec
`train-and-finalize-main-architecture`.

## 7. Evaluation & research questions

`eval/` is the largest subpackage:
- `synthetic.py` — `inject_anomaly:45` (NDVI drop / phase delay / LST rise), benchmark `:93`.
- `stats.py` — bootstrap CI, paired Wilcoxon, Holm, Spearman.
- `cv.py` — `generate_splits_dict:24` leak-free LOYO + spatial-block + temporal-drift with
  SHA256 fingerprints.
- `real_archive.py` — `load_real490_archive:280` hash-validated loader with provenance;
  fail-closed; no 32-farm proxy borrow.
- RQ suites: `cloud_robustness.py` (RQ4), `early_detection.py` (RQ5), `probing.py` (RQ7),
  `contamination.py` (RQ8), `data_scarcity.py` (DS1–DS5), `growth_validation.py`,
  `validation_gate.py` ("anomaly ≠ stress" gate + expert review packet).
- `eval/xai/` (RQ6) — IG, Temporal Grad-CAM, occlusion, Temporal SHAP + faithfulness
  (deletion/insertion AUC, weight-randomization sanity, physiology sign concordance).

Scripts: `run_rq1_benchmark.py` … `run_rq7_rq8.py`, `run_data_scarcity.py`, all with
`--source {real490,real32,simulated}`; simulated outputs segregated to `reports/simulated/`.

## 8. Validation dashboard (platform)

React 19 + TypeScript 5.9 + Vite 7 + Tailwind 4 + **Leaflet 1.9** + Recharts; builds to a
single offline `dist/index.html` (`vite-plugin-singlefile`). **Research validation
dashboard, NOT production** (`docs/vision.md:64-69`).
- Shell/state: `platform/src/App.tsx` (8 views), `context/AnalysisContext.tsx` (default
  model `b1_dsh`; experiments start empty — no seeded fakes).
- Data layer: `data/data.ts` typed loader; `farms_khuzestan.json` (490) +
  `series_khuzestan.json` (**contract v4**, full 538-acquisition axis, RLE provenance).
- Contract registry: `data/channels.ts` mirrors `scripts/platform_channels.py`
  (`CONTRACT_VERSION=4`; proxy id `cwsi_affine_v1`; model slots `*_490`). Parity enforced
  by `tests/unit/test_platform_data_contract.py`.
- i18n: `i18n/en.ts` + `fa.ts` (compile-time parity), Vazirmatn font, RTL. Provenance chips:
  observed/modelled/model/proxy/absent (`components/ui.tsx`).

## 9. Pipeline→UI bridge & tiles

- `scripts/export_platform_data.py` — `stats.zarr` + farms + `weather_aligned.parquet` →
  `farms_khuzestan.json` + v4 `series_khuzestan.json`; `valid_frac ≥ 0.5` gate; registry text
  verbatim; `ContractViolation` aborts on out-of-range; atomic writes.
- `scripts/load_model_checkpoints.py` — discovers `checkpoints/<id>_490.pt`, causal
  leave-one-bin-out scoring, squash `1−exp(−MSE)`; status loaded/missing/failed →
  model/proxy/**absent**.
- `scripts/serve_tiles.py` — stdlib ThreadingHTTPServer + rasterio WarpedVRT
  (UTM39N→EPSG:3857) 256px tiles; per-handle locks avoid concurrent-GDAL crash; per-scene
  contrast stretch kills seams; errors return transparent PNG; zoom 8–14; port 8765.
- `scripts/build_tile_index.py` → `scenes_index.json`; `capture_platform_screenshots.mjs`
  headless Edge audit; `test_tile_concurrency.py` 12-thread burst gate.

## 10. Config, CLI & scripts

- `conf/` Hydra: `base.yaml` (profile=laptop, phase_axis=dsh, model=ssl_masked_recon,
  eval=loyo); `profile/laptop.yaml` (2 threads, CPU) vs `profile/colab.yaml` (CUDA).
- `src/ssl_anomaly/cli.py` — click group; **`ingest` and `segment` are real; `baseline`,
  `train`, `evaluate`, `export` are placeholders** that warn and delegate to `scripts/`.
  Console scripts `ssl-anomaly`, `ssl-ingest`, … (`pyproject.toml:130-137`).
- `scripts/` (~48): synthetic demo (`generate_synthetic_data.py`, `build_baseline.py`,
  `train_ssl.py`, `evaluate.py`, `export_model.py`), real-data (`extract_stats.py`,
  `segment_and_export_cycles_490.py`, `build_splits_490.py`), RQ suites, figures/maps.
- `rust/` — real PyO3 0.22 + ndarray extension (`src/lib.rs`), maturin build;
  `robust_baseline` + exact pentadiagonal Whittaker solver; gated G3.

## 11. Testing & verification gates

`tests/unit` (~28 files, every module), `tests/regression/test_golden.py` (golden
segmentation fixture), `tests/parity` (NumPy vs Rust, skipped without wheel).
Tooling: pytest (+cov, markers slow/golden/parity/integration), ruff (line 100, py311),
pyright basic.

**Gates before "done"** (`AGENTS.md:52-65`), conda env `geo`
(`D:\Dev\Miniforge3\envs\geo\python.exe -X utf8`):
1. `pytest tests/unit/test_platform_data_contract.py tests/unit/test_platform_bilingual.py -q`
2. platform `tsc --noEmit` then vite build (esbuild temp-dir workaround).
3. runtime: `serve_tiles.py --port 8765` + headless screenshot audit, zero console/page errors.
4. tile changes: `python scripts/test_tile_concurrency.py`.

Long jobs (full training/sweeps/RQ/exporter) are **never launched by the agent** — handed to
the user as exact commands after unit + `--smoke` pass; scripts auto-select cuda/cpu, support
`--resume`, emit `progress.jsonl`. Laptop budget ≤15 min/seed, ≤500k params.

## 12. Provenance & scientific invariants

Binding (`AGENTS.md` §1–2, §7):
- Nothing user-visible is synthesized; missing ⇒ `absent` (dash), never 0.5 / nan-fill,
  never labelled "modelled".
- Proxy formulas are never presented as checkpoint inference (`cwsi_affine_v1` vs
  `<model>_490:bin_mse_1mexp`). Failed checkpoints ⇒ absent, not fake scores.
- Observation ≠ derivation ≠ reanalysis ≠ model inference.
- No CWSI-for-selection (circularity); no temporal/spatial leakage; AUC-PR on imbalance;
  every result carries n, dates, seeds, git SHA, and its ladder rung.
- OpenSpec drives features (one change per feature); evidence committed under `reports/`.

## 13. Open questions & known discrepancies

- Rust crate `32.7×` speedup claim is **unreproduced** — verify or remove (todo OQ4).
- METRIC **539 scenes vs `stats.zarr` 538 dates** — which date is missing (OQ5).
- **1704 non-censored cycles** (findings 02) vs **799 cycles** (`splits_490.json`) — recount
  before the 10%/25% segmentation rule (OQ7).
- Final perturbation set awaits advisor (Dr. Hamzeh) input on realistic Amirkabir stress
  signatures (OQ6). Validation-ladder full write-up pending from user (OQ1).
- `docs/platform_score_methods.md` §2 still describes the old 48-month grid; code uses the
  538-acquisition axis (contract v4).

Full backlog: `todo.md`. Empirical findings index: `docs/findings/00_index.md`.

## Maintenance

This file is a **living knowledge base**. Every session:
1. **Start** — read this file and recall memory: `mnemon recall "<task query>" --limit 10`
   (store `thesis`). Read `todo.md` and the latest `docs/findings/`.
2. **After a meaningful change** (new module, decision, result, gate, or discrepancy) —
   update the relevant section here, bump *Last updated* + git baseline, add a Changelog
   line, and store the durable fact: `mnemon remember "<fact>" --cat <decision|insight|fact|context> --imp <1-5> --entities "…" --source agent`.
3. Keep this file, the `mnemon` store, and `.qoder/repowiki/wiki_plan.yaml` consistent.
   Do not store secrets or short-lived noise. Prefer pointers to source-of-truth over copies.

## Changelog
- 2026-11-11 — Initial knowledge base authored from a full read of both repos (baseline `87071cd`).