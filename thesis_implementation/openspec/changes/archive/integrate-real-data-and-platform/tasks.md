# Tasks

## 1. Real Data Ingestion and Cycle Extraction

- [x] 1.1 Implement `Data/Processed/satellite/stats.zarr` reader adapter in `src/ssl_anomaly/io/` and verify reading 490 fields, 538 dates, and 7 bands.
- [x] 1.2 Run cycle segmentation on all 490 fields across 2013-2026 and verify output `data/processed/cycles_490.parquet` contains valid harvest boundaries.
- [x] 1.3 Export binned cycle arrays to `data/interim/growth_cycles_490.npz` and verify shape and absence of NaN in valid bins.

## 2. Literature SSL Model Implementation

- [x] 2.1 Implement STS-Net spatio-temporal autoencoder in `src/ssl_anomaly/models/sts_net.py` and verify forward/backward pass with a unit test.
- [x] 2.2 Implement portable Tiny-CNN-Mamba in `src/ssl_anomaly/models/cnn_mamba.py` using pure PyTorch Bidirectional SSM and verify forward pass with a unit test.
- [x] 2.3 Add Time2Agri agricultural augmentations and trajectory contrastive head in `src/ssl_anomaly/models/pretexts.py` and verify embedding output shapes.
- [x] 2.4 Add unit tests in `tests/unit/test_literature_models.py` covering parameter counts, reconstruction loss, and tensor dimensions.

## 3. Training and Benchmark Evaluation

- [x] 3.1 Train STS-Net, Tiny-CNN-Mamba, and Time2Agri models on the train partition and save checkpoints under `checkpoints/`.
- [x] 3.2 Run causal growth validation on temporal and spatial holdout sets using `scripts/validate_growth.py` for all literature models.
- [x] 3.3 Generate comparative evaluation report `reports/literature_models_benchmark.json` and verify point AUC-PR, event recall, and delay metrics.

## 4. Platform Data Bridge and Customization

- [x] 4.1 Create `scripts/export_platform_data.py` to extract Khuzestan farm GeoJSON (WGS84), METRIC time series, and model scores into `platform/src/data/`.
- [x] 4.2 Replace Brazilian mock definitions in `platform/src/data/mock.ts` with real Khuzestan farm metadata (CP69-1062, CP73-21, blocks R01–R16, L02–L08).
- [x] 4.3 Update model catalog in `platform/src/data/mock.ts` and `platform/src/views/ModelComparison.tsx` to display thesis baselines and literature SSL models.
- [x] 4.4 Update map view center to [31.0°N, 48.3°E] and verify interactive farm polygon selection in `platform/src/views/MapExplorer.tsx`.
- [x] 4.5 Update spectral and temporal charts to display real Landsat/METRIC indices (NDVI, CWSI, ETa, LST).

## 5. Integration and Delivery Verification

- [x] 5.1 Build the frontend platform with `bun run build` inside `platform/` and verify zero TypeScript or bundler errors.
- [x] 5.2 Verify end-to-end consistency between Python benchmark JSON outputs and the platform's Model Comparison tables.
