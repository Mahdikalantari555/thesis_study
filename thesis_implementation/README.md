# ssl_anomaly — Phenology-Aware Self-Supervised Anomaly Detection

Self-supervised, phenology-aware anomaly detection for field-level Landsat time
series (sugarcane thesis implementation). The framework learns *normal* crop
phenological behavior from multi-year cycles and flags deviations at field
scale without requiring labeled stress data.

## Status

| Phase | Content | Gate |
|-------|---------|------|
| 0 | Data audit, `fields.zarr`, cycle segmentation, QC | G0: harvest detection acceptable |
| 1 | Phenology-aware robust baselines B0-B1 + evaluation | G1: B1 beats B0 on synthetic + proxies |
| 2 | SSL: GRU-AE & masked 1-D Transformer (gated on G1) | G2: SSL beats B1 with CI |
| 3 | Patch-level / intra-field / Rust acceleration | G3: profiling justifies Rust |

v1 of this code implements scaffolding + ingest utilities + phenology + robust
baseline (B1) + SSL models (masked Transformer / GRU-AE) + evaluation harness
(synthetic injection) + SafeTensors export + a synthetic data generator.

## Project layout

```
src/ssl_anomaly/
  io/            # Landsat ingest: field mask, zonal bincount, zarr aggregation
  phenology/     # Whittaker smoothing, harvest detection, cycles, phase binning, spectral indices
  backends/      # NumPy reference backend; Protocol for future Rust (gate G3)
  baseline/      # Robust stratum-aware median/MAD, iterative trimming, scoring, anomaly runs
  models/        # GRU autoencoder, masked 1-D Transformer, tokenizer
  train/         # PyTorch/Lightning data + training module
  eval/          # Synthetic injection, bootstrap CI, Wilcoxon, Holm, Spearman
  export/        # SafeTensors release export/load (no pickle)
  utils/         # BLAS throttling, SQLite manifest, logging, seeds, array helpers
  config.py      # Structured Hydra-compatible dataclass configs
  cli.py         # click CLI (ssl-anomaly)
conf/            # Hydra profiles (laptop / colab)
scripts/         # Thin pipeline CLIs (generate_synthetic_data, build_baseline, train_ssl, evaluate, export_model)
tests/
  unit/          # Fast unit tests for every module
  regression/    # Golden regression fixtures
  parity/        # Backend parity tests (Rust vs NumPy; skip until G3)
data/            # Raw / interim / processed (DVC tracked, not in repo)
docs/            # Vision, implementation plan, final plan (English/Persian)
openspec/        # OpenSpec change specs
```

## Quickstart (synthetic demo)

This repo can run the baseline workflow without real Landsat data. Use an
isolated scratch directory for synthetic outputs, never your archive's
`data/processed` or the platform's generated payload:

```bash
# 1. Create a venv & install
uv sync --locked --python 3.11 --extra dev
source .venv/bin/activate
repo="$PWD"
cd "$(mktemp -d)"

# 2. Generate a small synthetic dataset in the scratch directory
python "$repo/scripts/generate_synthetic_data.py" --n-fields 80 --n-years 10 --out data/processed --seed 42

# 3. Segment cycles
python -m ssl_anomaly.cli segment --zarr data/processed/fields.zarr --out data/processed/cycles.parquet

# 4. Fit robust baseline B1 and score all cycles
python "$repo/scripts/build_baseline.py"

# 5. Evaluate (synthetic injection benchmark)
python "$repo/scripts/evaluate.py"
cat reports/metrics.json

# 6. (Optional) Train SSL masked Transformer
python "$repo/scripts/train_ssl.py"

# 7. Run checkout-only tests back in the repository
cd "$repo"
pytest -m "not slow and not real_data"
```

## Running on real Landsat data

The ingest pipeline expects:

```
data/geo/fields.gpkg          # field polygons with a field_id column
data/raw/landsat/<scene>/     # unzipped Landsat C2 L2 scenes (one directory per scene)
                               # containing *_SR_B*.TIF, *_ST_B10.TIF, *_QA_PIXEL.TIF
```

Run the field mask + zonal pipeline via the CLI or per-scene using
`ssl_anomaly.io.zonal.zonal_scene_from_paths` (per-scene checkpointing uses
the SQLite `Manifest` in `data/manifests/ingest.sqlite`). For locked patch
exports and the train-only normalization handoff, see the
[patch input runbook](docs/patch_inputs.md).

## Decomposition-aware SSL research study

Run `python scripts/run_decomposition_study.py --smoke` to verify the isolated
study with an explicitly simulated fixture. For Landsat benchmarking, feature
ablation, and independent component scores, see the
[study runbook](docs/decomposition_aware_ssl_study.md). The study does not modify
the main training, checkpoint, or platform pipeline.

## Design decisions

- **Phenology axis**: days-since-harvest (dsh) is primary; DOY, GDD, and
  landmark registration are implemented as comparators.
- **Cycle segmentation**: Whittaker-Eilers smoothing + scipy peak detection
  of NDVI troughs with plateau/rise filters; Hampel filter removes single
  cloud-missed points.
- **Baseline**: per-stratum median + MAD (×1.4826) with shrinkage field
  offset; 3 iterations of trimming (top 15% anomalous cycles per stratum);
  hierarchical stratum fallback when bins have <5 normal cycles.
- **Scoring**: modified z-scores with scale floor; RMS band aggregation;
  anomaly runs require ≥2 consecutive observed bins above threshold 3.5.
- **SSL**: masked reconstruction (15-30% random tokens + 1-3 token blocks
  mimicking cloud gaps); Huber loss; 10% trimmed loss per batch to reduce
  contamination by anomalous training cycles. Two architectures:
  - `gru_ae`: bidirectional GRU encoder → GRU decoder (CPU baseline)
  - `transformer`: 1-D encoder-only Transformer with MAE-style masking
- **Gate**: SSL training is gated on the baseline producing valid strata;
  SSL scores are combined only if each beats the baseline.
- **Backend protocol**: `PhenologyBackend` Protocol with NumPy reference;
  Rust backend stub raises `NotImplementedError` until gate G3.
- **Export**: SafeTensors weights + `model_config.json` + `norm_stats.json`
  + `meta.json` (git SHA, lock hash, seed). No pickle in releases.
- **Evaluation**: synthetic injection (NDVI drop, phenology delay, LST
  increase), cluster-bootstrap CI, paired Wilcoxon signed-rank with Holm
  correction, Spearman with weak proxies.

## Testing

```bash
pytest -m "not slow and not real_data"   # clean checkout, including source-only platform checks
pytest -m real_data                     # strict archive/export checks; missing inputs fail
pytest                                  # both gates (also includes slow tests)
pytest tests/regression -m golden        # golden regression
pytest tests/parity                      # backend parity (skipped until Rust)
```

Mark new tests that need untracked archive artifacts `@pytest.mark.real_data`;
fixture-based and committed-artifact checks belong in the checkout gate. Do not
skip or supply substitute data in the strict gate. It needs the authorized
zonal/cycle files, frozen splits, masked cycle cache, farm registry, and a real
`platform/src/data/series_khuzestan.json` export. Passing checkout tests or
TypeScript checking does not verify the platform bundle or runtime: the original
contract, build and screenshot gates in [AGENTS.md](AGENTS.md) still apply.

## Linting / type checking

```bash
ruff check src tests
pyright src
```

## References

- Eilers, P.H.C. (2003). "A perfect smoother." Anal. Chem. 75(14), 3631-3636.
- Joshi N. et al. (2024). Automating sugarcane growth stages from EO time series. Remote Sensing 16(22), 4244.
- Tseng G. et al. (2023). Presto: Lightweight pre-trained transformers for remote sensing timeseries.
- STS-NET (2025). Spatio-Temporal Stress Network for self-supervised crop stress detection.

## Forward-only growth validation

A separate paired-perturbation benchmark (statistical, one-class and SSL models) and honest data/claim boundaries are
available in [docs/growth_validation.md](docs/growth_validation.md). It is a
retrospective sensitivity experiment, not validated stress or an online
benchmark. Its proposed protocol is tracked in
[OpenSpec](openspec/changes/add-rigorous-growth-validation/).
