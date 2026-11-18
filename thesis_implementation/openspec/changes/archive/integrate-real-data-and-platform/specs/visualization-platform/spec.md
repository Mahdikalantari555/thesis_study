# Spec: Visualization Platform

## Purpose

Provides an interactive geospatial and time-series dashboard for domain agronomists and researchers to inspect farm-level anomalies, compare baseline and self-supervised model behaviors, and explore multi-spectral sugarcane trajectories.

## ADDED Requirements

### Requirement: Real farm geospatial visualization
The dashboard SHALL load and render the 490 sugarcane farm polygons from the Khuzestan region of interest using EPSG:4326 coordinates, displaying farm management attributes, blocks, sugarcane varieties, and areas on an interactive Leaflet map.

#### Scenario: Farm polygon selection
- **WHEN** a user clicks on an individual farm polygon on the map
- **THEN** the system highlights the farm and displays its field ID, block name (e.g., R11), variety (e.g., CP69-1062), area in hectares, and historical anomaly summary.

### Requirement: Multi-spectral and METRIC indicator inspection
The dashboard SHALL visualize temporal trajectories for real Landsat and METRIC products, including NDVI, CWSI, ETaDaily, LST, NDMI, and SAVI across acquisition dates from 2013 to 2026.

#### Scenario: Switching indicator view
- **WHEN** a user selects an indicator such as CWSI or ETaDaily from the indicator selector
- **THEN** the system re-renders the temporal chart and heatmaps displaying the corresponding historical trajectory and bounds for the active farm.

### Requirement: Multi-model anomaly comparison
The dashboard SHALL present comparative metrics and time-series anomaly scores across the implemented models: B0 calendar DOY, B1 DSH baseline, B1 CUSUM, SSL Masked Transformer, STS-Net CAE, Tiny-CNN-Mamba, and Time2Agri.

#### Scenario: Model score overlay
- **WHEN** a user toggles between different models in the Model Comparison view
- **THEN** the chart overlays the anomaly scores with respect to the decision threshold and displays comparative point AUC-PR, event recall, and detection latency.

### Requirement: Static data bridge and offline bundling
The platform SHALL load farm metadata, time series, and evaluation scores from static pre-generated JSON artifacts without requiring an active backend service during client execution.

#### Scenario: Platform initial load
- **WHEN** the web application is loaded in a standard web browser
- **THEN** all 490 farm boundaries, overview statistics, and model comparison metrics initialize within 2 seconds using pre-exported static assets.
