# Tasks

## 1. Project scaffolding

- [x] 1.1 Create Python package structure under `src/ssl_anomaly/`
- [x] 1.2 Add `pyproject.toml`, lockfile, and base Hydra configuration
- [x] 1.3 Configure pytest, ruff, and pyright
- [x] 1.4 Add DVC pipeline skeleton

## 2. Data ingest

- [x] 2.1 Implement field mask construction
- [x] 2.2 Implement per-scene zonal statistics with quality masks
- [x] 2.3 Implement SQLite manifest checkpoint and resume
- [x] 2.4 Implement resource throttling utilities
- [x] 2.5 Implement Zarr aggregation into `fields.zarr`
- [x] 2.6 Add CLI script and tests

## 3. Phenology and cycles

- [x] 3.1 Implement Whittaker-Eilers smoothing
- [x] 3.2 Implement harvest detection and cycle segmentation
- [x] 3.3 Implement replant detection and ratoon tracking
- [x] 3.4 Implement phase axes and binning
- [x] 3.5 Add synthetic unit tests and golden regression tests

## 4. Anomaly baseline

- [x] 4.1 Implement stratum assignment and fallback
- [x] 4.2 Implement robust baseline statistics
- [x] 4.3 Implement iterative normal-cycle trimming
- [x] 4.4 Implement anomaly scoring and runs
- [x] 4.5 Add ablation support for LST and weather

## 5. Self-supervised models

- [x] 5.1 Implement cycle tokenization and data loading
- [x] 5.2 Implement GRU autoencoder
- [x] 5.3 Implement masked Transformer
- [x] 5.4 Implement trimmed loss and masking strategies
- [x] 5.5 Implement reconstruction and embedding anomaly scores
- [x] 5.6 Add training, checkpointing, and evaluation hooks

## 6. Evaluation

- [x] 6.1 Implement synthetic anomaly injection
- [x] 6.2 Implement proxy-based validation
- [x] 6.3 Implement stability tests
- [x] 6.4 Implement statistical comparison utilities
- [x] 6.5 Add MLflow tracking integration

## 7. Export and interfaces

- [x] 7.1 Implement SafeTensors export and loading
- [x] 7.2 Save config and normalization statistics
- [x] 7.3 Define phenology backend interface
- [x] 7.4 Add model versioning metadata

## 8. Documentation and tests

- [x] 8.1 Document setup and usage
- [x] 8.2 Add golden regression fixtures
- [x] 8.3 Add parity test placeholders for Rust
- [x] 8.4 Validate OpenSpec change
