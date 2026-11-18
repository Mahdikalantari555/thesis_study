# OVERVIEW — Thesis Study Repository

This repository (`Mahdikalantari555/thesis_study`) is the **umbrella index** for an
MSc thesis on self-supervised anomaly detection of concurrent water-and-salinity
stress in sugarcane (Khuzestan agro-industry, Iran). It does **not** contain the
full thesis code; it vendors the proposal + the key implementation/research files
so future agents can read them quickly.

## Thesis (the only proposal)

- **Title:** "A Self-Supervised and Explainable CNN-Mamba Framework for
  Disentangling Concurrent Water and Salinity Stress from Multi-Temporal
  Satellite Imagery"
- **Site:** Amirkabir Agro-Industrial Unit, Khuzestan, Iran — ~490 sugarcane
  fields, Landsat 8/9 C2 L2 + METRIC (ETaDaily, CWSI_ET, CWSI_LST, …) +
  ERA5, 2013–2026.
- **Core claim:** anomaly detection (not stress labeling) over phenology-aware
  field-level Landsat time series, without labeled stress data. Validation
  ladder L1–L5; "anomaly" ≠ "stress" before L4.
- **The thesis itself is only a Proposal in the SSL domain** — see
  `thesis_research/SSL_Proposal/`.

## Where things live

| Path in this repo | Source repo | Role |
|---|---|---|
| `thesis_research/` | `Mahdikalantari555/thesis_research` | Full research repo (background, literature, proposal framing, data, notebooks, vault) |
| `thesis_implementation/` | `Mahdikalantari555/thesis_implementation` | Full implementation (code, tests, docs, platform dashboard) |

Both are integrated as **git subtrees** (not submodules, not plain copies):

| Remote | Upstream | Subtree prefix |
|---|---|---|
| `thesis_implementation` | `https://github.com/Mahdikalantari555/thesis_implementation.git` | `thesis_implementation/` |
| `thesis_research` | `https://github.com/Mahdikalantari555/thesis_research.git` | `thesis_research/` |

Update a subtree from its upstream:
```bash
git subtree pull --prefix=thesis_implementation thesis_implementation main
git subtree pull --prefix=thesis_research thesis_research main
```
Push local subtree edits back upstream:
```bash
git subtree push --prefix=thesis_implementation thesis_implementation main
```

---

## 1. `thesis_research/` — full research repo (incl. `SSL_Proposal/`)

Key files:
- `README.md` — index of the proposal folder.
- `00_SSL_questionnaire.md` — 21 questions, answered 2026-10-24 (pivot = anomaly
  detection core, label-free ideal).
- `01_vision_and_decisions_2026-10-26.md` — vision & decisions.
- `literature_review_ssl.md` — deep SSL literature review (84 papers, gaps G1–G8,
  RQ1–RQ8).
- `method_design_ssl.md` — SSL method design (pretext, architecture,
  augmentation, evaluation).
- `scalable_config_and_extensions.md` — scalable config (drone→server),
  sub-field, cross-year, ETa/CWSI, expansion roadmap.
- `lit_review/` — 8 deliverables + 84-paper matrix (`00_search_log.md`,
  `01_ssl_foundations.md`, …, `07_verified_bibliography.bib`,
  `05_comparative_evidence_matrix.csv`).
- `papers/` — 157 paper notes (`.md`/`.txt`) + `PAPERS_CATALOG.md`.

## 2. `thesis_implementation/` — full implementation

Python package `ssl_anomaly` (src-layout) + React/TS validation dashboard.

### Layout
```
thesis_implementation/
  src/ssl_anomaly/     # core package
    io/                # Landsat ingest: field mask, zonal bincount, zarr aggregation, ERA5
    phenology/         # Whittaker smoothing, harvest detection, cycles, phase binning, indices
    backends/          # NumPy reference backend; Protocol for future Rust (gate G3)
    baseline/          # robust stratum-aware median/MAD, trimming, scoring, anomaly runs (B0/B1)
    models/            # GRU-AE, masked 1-D Transformer, tokenizer, JEPA, STS-NET, CNN-Mamba
    train/             # PyTorch/Lightning data + training module
    eval/              # synthetic injection, bootstrap CI, Wilcoxon, Holm, Spearman, CV
    export/            # SafeTensors release export/load (no pickle)
    utils/             # BLAS throttling, SQLite manifest, logging, seeds, arrays
    xai/               # attribution, faithfulness
    config.py          # structured Hydra-compatible dataclass configs
    cli.py             # click CLI (ssl-anomaly)
  conf/                # Hydra profiles (laptop / colab) + model/phase-axis/input/xai configs
  scripts/             # thin pipeline CLIs (see below)
  tests/               # unit / regression (golden) / parity (Rust vs NumPy, skipped until G3)
  docs/                # vision, implementation plan, final plan, score methods, bug audit, …
  openspec/            # OpenSpec change specs (changes/ + specs/)
  platform/            # React 19 + Vite + Tailwind validation dashboard (TS)
  AGENTS.md            # binding agent rules for this repo
  README.md            # full quickstart
  pyproject.toml       # deps / entry points
  todo.md              # living task list + open questions
```

### Key pipeline scripts (`scripts/`)
- Data: `ingest_real.py`, `prepare_processed.py`, `prepare_growth_validation.py`,
  `extract_stats.py`, `extract_pixels.py`, `segment_and_export_cycles_490.py`,
  `build_splits_490.py`, `build_tile_index.py`.
- Baseline/eval: `build_baseline.py`, `evaluate.py`, `compare_baselines.py`,
  `run_rq1_benchmark.py` … `run_rq8`, `run_ablation.py`, `run_data_scarcity.py`,
  `run_eintra.py`.
- Training: `train_ssl.py`, `train_literature_checkpoints.py`.
- SSL RQs: `run_rq2_pretexts.py`, `run_rq3_lst_ssl.py`, `run_rq4_cloud_and_stability.py`,
  `run_rq5_early_detection.py`, `run_rq6_xai.py`, `run_rq7_rq8.py`.
- Export/platform: `export_model.py`, `export_platform_data.py`,
  `export_growth_events.py`, `export_growth_weather.py`, `serve_tiles.py`,
  `capture_platform_screenshots.mjs`.
- Synthetic demo: `generate_synthetic_data.py`.

### How to run (synthetic demo, no real data)
```bash
# conda env "geo": D:\Dev\Miniforge3\envs\geo\python.exe -X utf8
uv venv --python 3.11 && source .venv/bin/activate
uv pip install -e ".[dev]"
python scripts/generate_synthetic_data.py --n-fields 80 --n-years 10 --out data/processed --seed 42
python -m ssl_anomaly.cli segment --zarr data/processed/fields.zarr --out data/processed/cycles.parquet
python scripts/build_baseline.py
python scripts/evaluate.py
cat reports/metrics.json
python scripts/train_ssl.py        # optional
pytest -m "not slow"
```
Real Landsat ingest expects `data/geo/fields.gpkg` + `data/raw/landsat/<scene>/`
(`*_SR_B*.TIF`, `*_ST_B10.TIF`, `*_QA_PIXEL.TIF`).

### Dashboard (platform/)
```bash
cd platform
node node_modules/typescript/bin/tsc --noEmit
TMP=platform/.tmpbuild node node_modules/vite/bin/vite.js build
node node_modules/vite/bin/vite.js   # dev
```

### Verification gates
- `pytest tests/unit/test_platform_data_contract.py tests/unit/test_platform_bilingual.py -q`
- tsc --noEmit then vite build (esbuild temp-dir workaround)
- Runtime: `scripts/serve_tiles.py --port 8765` then
  `node scripts/capture_platform_screenshots.mjs --out reports/screenshots/audit --locale en`
- Tile changes: `python scripts/test_tile_concurrency.py`

### Environment
- Python 3.12 in conda env `geo` (`D:\Dev\Miniforge3\envs\geo\python.exe -X utf8`).
- Node (bun preferred). Headless browser: Edge.
- Data roots: `D:\RS\Thesis\Data\Processed\` and `D:\RS\Thesis\Data\Metric\products\`.

## Conventions for future agents
- Read `thesis_implementation/AGENTS.md` before editing implementation code.
- Nothing user-visible is synthesized; every value must come from a real artifact
  or be `absent`. Proxy formulas are never presented as checkpoint inference.
- Models detect phenology-phase anomalies, not DOY/magnitude alone.
- State the validation-ladder rung (L1–L5) for every model claim.
- Use the `geo` conda env; never system Python.

## Subtrees (integrated)
Both repos are now integrated as **git subtrees** (see the "Where things live"
table above for remotes and pull/push commands). The full trees are vendored
under `thesis_research/` and `thesis_implementation/`; upstream history is
preserved in this repo's log. To refresh from upstream:
`git subtree pull --prefix=thesis_research thesis_research main` and
`git subtree pull --prefix=thesis_implementation thesis_implementation main`.
