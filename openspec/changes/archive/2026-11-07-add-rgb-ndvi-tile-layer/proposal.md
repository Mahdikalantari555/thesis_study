# Proposal: Add RGB/NDVI Tile Serving Layer (`add-rgb-ndvi-tile-layer`)

## Why

The platform currently shows per-field time-series indices (NDVI, EVI, SAVI, etc.) but has no full-extent raster overlay. The user has 607 Landsat scene GeoTIFFs under `D:\RS\Thesis\Data\Metric\scenes\` (each with blue/green/red/nir08/swir16/swir22/lwir11/qa_pixel + MTL.json, dates 2025–2026). A tile serving layer is needed so the map view can render RGB composites and NDVI overlays across the full extent, not just at field centroids.

## What Changes

- **Tile serving pipeline**: convert GeoTIFF scenes into web tiles (PNG/MBTiles or on-the-fly via a local tile server), generating RGB composites (red/green/blue bands) and NDVI (NIR−RED / NIR+RED) per acquisition date.
- **Map tile layer integration**: add Leaflet tile layer(s) to `platform/src/views/MapExplorer.tsx` with date picker / scene selector, opacity control, and layer toggle (RGB vs NDVI vs none).
- **Scene index manifest**: build a JSON index of available scenes (date, path, bounds, bands) so the frontend knows which dates are available.
- **Platform spec update**: add `platform-visualization` spec covering raster overlay, tile layer, and scene index.

## Capabilities

### New Capabilities
- `rgb-ndvi-tile-layer`: Full-extent RGB and NDVI raster tile overlays on the platform map, selectable by acquisition date.
- `scene-index`: JSON manifest of available Landsat scenes with dates, bounds, and band availability.

### Modified Capabilities
- `platform/src/views/MapExplorer.tsx` — adds tile layer controls and scene selector.
- `platform/src/data/` — adds scene index JSON artifact.

## Impact

- `scripts/build_tile_index.py` (new) — scans `Data/Metric/scenes/`, emits scene index JSON
- `scripts/serve_tiles.py` (new) — local tile server for on-the-fly tile generation (or prebuilt MBTiles)
- `platform/src/views/MapExplorer.tsx` — tile layer + scene selector UI
- `platform/src/data/scenes_index.json` (new) — scene manifest

## Out of Scope

- Re-processing raw Landsat Level-2 scenes (GeoTIFFs are already verified and frozen).
- Real model outputs (handled by `integrate-real-model-outputs` change).
- Production tile server infrastructure; local laptop tile serving is sufficient.
