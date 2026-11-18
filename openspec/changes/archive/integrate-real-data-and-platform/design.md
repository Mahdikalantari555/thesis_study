# Design: Real Data Ingestion, Literature SSL Models, and Platform Customization

## Context

The repository provides baseline algorithms (`B0`, `B1_dsh`, `B1_CUSUM`, `B3_ECOD`), evaluation harnesses with synthetic injection and causal holdout validation, and basic 1D Transformer / GRU-AE models. However:
1. The primary dataset (`Data/Processed/satellite/stats.zarr`, containing 490 sugarcane farms across 538 Landsat acquisitions from 2013 to 2026) has not yet been fully wired into the main training and benchmark pipelines.
2. The extracted UI platform in `platform/` is currently configured with placeholder Brazilian farms and generic models.
3. Advanced self-supervised architectures highlighted in the thesis literature review—specifically STS-Net (3D-CAE), Tiny-CNN-Mamba, and Time2Agri—need formal implementation and benchmark comparison.

## Goals / Non-Goals

**Goals:**
- Provide a clean data adapter to load `Data/Processed/satellite/stats.zarr` directly into cycle segmentation and SSL training routines without re-extracting rasters.
- Implement STS-Net (spatio-temporal convolutional autoencoder), Tiny-CNN-Mamba (lightweight 1D-CNN + Bidirectional State Space Model), and Time2Agri (trajectory contrastive pretext).
- Benchmark all literature models against the B1 DSH baseline under the established prospective holdout protocol.
- Customize the React/Vite dashboard in `platform/` with real Khuzestan farm coordinates, real METRIC products, and actual thesis model results.
- Provide a repeatable export script (`scripts/export_platform_data.py`) to generate static assets for the platform.

**Non-Goals:**
- Real-time live inference backend (static pre-computed evaluation outputs are sufficient and preferred for thesis defense and web hosting).
- Re-processing raw Landsat Level-2 scenes from scratch (METRIC GeoTIFFs and `stats.zarr` are already verified and frozen).
- Heavy GPU-only CUDA kernel compilation requirements (models must maintain a portable pure-PyTorch fallback runnable on CPU/laptop).

## Decisions

### 1. Static JSON Data Bridge for the Platform over Dynamic Backend API
- **Decision**: Serialize farm polygons, time series, and anomaly score tables into static, compressed JSON/GeoJSON files under `platform/src/data/` via `scripts/export_platform_data.py`.
- **Rationale**: Eliminates server-side infrastructure, ensures deterministic client-side rendering, allows instant offline demonstration, and follows lazy senior dev principles (zero server maintenance).
- **Alternative considered**: FastAPI or Flask backend serving Zarr slices on demand. Rejected as over-engineered and unnecessary for 490 farms and 538 time steps.

### 2. Map Projection and Polygon Decimation for Web Leaflet
- **Decision**: Convert `Data/Processed/coordinates/farms.geojson` from UTM 39N (EPSG:32639) to WGS84 (EPSG:4326), computing bounding centers around [31.0°N, 48.3°E], with polygon vertex simplification to keep total geojson under 2 MB.
- **Rationale**: Leaflet natively operates on [lat, lng] WGS84; simplified geometries maintain interactive 60 FPS rendering in the browser.

### 3. Portable Implementation of Tiny-CNN-Mamba
- **Decision**: Implement Tiny-CNN-Mamba using a 1D convolutional spectral-temporal stem followed by a pure PyTorch Bidirectional Selective SSM (State Space Model) with analytical discretization.
- **Rationale**: Hardware-specific Mamba kernels (e.g. `mamba-ssm` / Triton) frequently fail to compile on Windows or CPU-only developer environments. A pure PyTorch implementation ensures identical execution on local Windows Python (conda geo) and WSL GPU environments.
- **Alternative considered**: Requiring `mamba_ssm` C++/CUDA extension. Rejected due to environment friction and Windows build incompatibility.

### 4. STS-Net Spatio-Temporal Convolutional Architecture
- **Decision**: Implement STS-Net using 1D/2D multi-channel convolutional encoder-decoder blocks over `(batch, phase_bins, bands)`. For farm-mean series, spatial dimensions collapse to multi-band channels while preserving temporal kernel receptive fields.
- **Rationale**: Accurately reflects Dalal et al. (2026) while integrating seamlessly with the 1D cycle sequence interfaces in `ssl_anomaly.train`.

### 5. Time2Agri Agricultural Contrastive Pretexts
- **Decision**: Utilize NT-Xent contrastive loss over trajectory augmentations (growing season crop-calendar shifting and cloud dropout) within the `PretextTransformer` framework.
- **Rationale**: Aligns with Gupta & Sobti (2025) and provides direct empirical comparison against masked reconstruction.

## Risks / Trade-offs

- **[Risk] High dimensionality in full 490-farm dataset causes high memory usage during cycle loading**  
  → **Mitigation**: Process and bin cycles in streaming batches or pre-save binned arrays to `growth_cycles_490.npz`.
- **[Risk] Leaflet map sluggish when rendering 490 SVG polygons simultaneously**  
  → **Mitigation**: Use GeoJSON canvas rendering option in Leaflet or simplify polygon coordinates to 5 decimal places.
- **[Risk] Discrepancies between Zarr band indices and platform spectral charts**  
  → **Mitigation**: Strict band mapping schema declared in `export_platform_data.py` (B2=Blue, B3=Green, B4=Red, B5=NIR, B6=SWIR1, B7=SWIR2, B10=LST).
