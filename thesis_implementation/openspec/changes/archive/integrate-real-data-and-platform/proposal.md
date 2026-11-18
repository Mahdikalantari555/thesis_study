# Proposal: Integrate Real Processed Zarr Data, Literature SSL Models, and Custom Visualization Platform

## Why

Existing prototype scripts relied on synthetic curves or staging subsets, and the newly extracted visualization platform (`platform/`) contains placeholder Brazilian farm geometries, generic models, and synthetic dates. To ground the PhD thesis in verified empirical evidence, the pipeline must ingest the primary Khuzestan dataset (`Data/Processed/satellite/stats.zarr`, 490 sugarcane farms across 538 Landsat acquisitions from 2013 to 2026), train and evaluate the specific self-supervised architectures identified in the literature review (STS-Net 3D-CAE, Tiny-CNN-Mamba, and Time2Agri pretext tasks), and customize the web dashboard to enable interactive spatial, temporal, and model-comparative exploration by advisors and agronomists.

## What Changes

- Ingest the primary `Data/Processed/satellite/stats.zarr` dataset (490 fields, 538 dates, 7 bands) and segment growth cycles across 2013-2026 using days-since-harvest (`dsh`) and GDD.
- Implement literature-derived self-supervised model architectures:
  - **STS-Net (3D-CAE / Spatio-Temporal Autoencoder)**: Multi-spectral spatio-temporal reconstruction for label-free anomaly scoring.
  - **Tiny-CNN-Mamba**: Lightweight 1D CNN feature front-end fused with a Bidirectional Selective State Space Model (Mamba) back-end for linear-complexity multi-year phenological modeling.
  - **Time2Agri Pretext Objectives**: Trajectory contrastive learning (NT-Xent) and agricultural masking pretexts.
- Adapt the evaluation harness to run causal-prefix scoring, spatial block holdouts, and event affiliation metrics on these models.
- Customize the extracted visualization platform (`platform/`):
  - Replace Brazilian mock data with 490 Khuzestan sugarcane farm polygons (`Data/Processed/coordinates/farms.geojson` and `farms.parquet`), blocks (R01–R16, L02–L08), and varieties (CP69-1062, CP73-21).
  - Bind real METRIC products (NDVI, CWSI, ETaDaily, LST, NDMI, SAVI) and acquisition dates (2013–2026).
  - Update model comparisons to reflect thesis baselines (`B0_calendar_doy`, `B1_dsh_baseline`, `B1_CUSUM`) and SSL architectures (`SSL_MaskedTransformer`, `STS_Net_CAE`, `Tiny_CNN_Mamba`, `Time2Agri_Contrastive`).
- Add a data export bridge script (`scripts/export_platform_data.py`) to serialize field geometries, time series, and anomaly scores into browser-optimized JSON for the platform.

## Capabilities

### New Capabilities
- `visualization-platform`: Customization and data-binding of the interactive web dashboard for Khuzestan sugarcane farms, real METRIC satellite indices, and multi-model anomaly detection diagnostics.
- `real-data-ingest`: Ingestion, quality filtering, and cycle segmentation directly targeting the complete `Data/Processed/satellite/stats.zarr` store.
- `literature-ssl-models`: Implementation, training, and benchmarking of STS-Net (3D-CAE), Tiny-CNN-Mamba, and Time2Agri pretext tasks on sugarcane multi-temporal series.

### Modified Capabilities
None.

## Impact

- `src/ssl_anomaly/models/`: New model implementations `sts_net.py` (3D/2D spatio-temporal autoencoder) and `cnn_mamba.py` (Tiny-CNN-Mamba); enhancements to `pretexts.py`.
- `src/ssl_anomaly/io/`: Direct Zarr v2 adapter for `Data/Processed/satellite/stats.zarr`.
- `scripts/`: Added `export_platform_data.py`, `train_literature_models.py`, and updated benchmark runners.
- `platform/src/`: Updated `data/`, `views/`, `components/`, and TypeScript definitions to render Khuzestan farm boundaries and actual model runs.
- Dependencies: Standard PyTorch and Lightning modules. No breaking changes to existing baseline CLI or golden regression tests.
