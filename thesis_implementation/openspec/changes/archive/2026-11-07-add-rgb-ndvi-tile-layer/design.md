# Design: Add RGB/NDVI Tile Serving Layer

## Context

The platform map (`MapExplorer.tsx`) shows field polygons with per-field time-series indices, but has no full-extent raster overlay. The user has 607 Landsat scene GeoTIFFs under `D:\RS\Thesis\Data\Metric\scenes\`, each scene directory containing `blue.tif`, `green.tif`, `red.tif`, `nir08.tif`, `swir16.tif`, `swir22.tif`, `lwir11.tif`, `qa_pixel.tif`, and `MTL.json`. Dates span 2025–2026.

Two raster products are needed for the platform:
1. **RGB composite** — red/green/blue bands for visual reference.
2. **NDVI** — `(NIR − RED) / (NIR + RED)` for vegetation health overlay.

## Goals / Non-Goals

**Goals:**
- Build a scene index manifest (`platform/src/data/scenes_index.json`) listing available dates, bounds, and bands.
- Serve tiles for RGB and NDVI per acquisition date on the platform map.
- Add Leaflet tile layer controls (date picker, RGB/NDVI toggle, opacity) to `MapExplorer.tsx`.
- Keep the tile pipeline local and simple (no production tile server infrastructure).

**Non-Goals:**
- Re-processing raw Landsat scenes (GeoTIFFs are frozen).
- Real model outputs (separate change).
- MBTiles prebuilding; on-the-fly tile generation is sufficient for 607 scenes.

## Decisions

### 1. Tile Serving Approach

Two options considered:
- **Prebuilt MBTiles**: generate `.mbtiles` files up front; serve as static assets. Larger storage, faster client load.
- **On-the-fly tile server**: a lightweight Python HTTP server that reads GeoTIFFs and renders tiles on request. Smaller storage, slightly slower first render.

**Decision**: Start with on-the-fly tile server (`scripts/serve_tiles.py`) using `rasterio` + `tiletile` or simple NumPy-based tile rendering. If performance is insufficient, switch to prebuilt MBTiles. The scene index tells the frontend which dates are available.

### 2. Scene Index Format

`platform/src/data/scenes_index.json`:
```json
{
  "scenes": [
    {
      "date": "2025-04-17",
      "path": "Data/Metric/scenes/landsat_20250417_165_039/",
      "bounds": [xmin, ymin, xmax, ymax],
      "bands": ["blue","green","red","nir08","swir16","swir22","lwir11","qa_pixel"],
      "has_rgb": true,
      "has_ndvi": true
    }
  ]
}
```

### 3. Tile Coordinate System

Scenes are in UTM 39N (EPSG:32639) per `integrate-real-data-and-platform` design decision. Tiles must be reprojected to Web Mercator (EPSG:3857) for Leaflet. The tile server handles reprojection per tile request.

### 4. Frontend Integration

`MapExplorer.tsx` gains:
- A scene/date selector dropdown (populated from `scenes_index.json`).
- A layer toggle: None / RGB / NDVI.
- An opacity slider (0–1).
- Leaflet `TileLayer.WMS` or custom `TileLayer` pointing at the local tile server.

## Risks / Trade-offs

- **[Risk] 607 scenes × 8 bands is large I/O** — on-the-fly tile server opens GeoTIFFs per tile request. *Mitigation*: cache opened datasets in memory (LRU), render tiles at 256×256, limit to visible zoom levels (z8–z14).
- **[Risk] Tile server not running** — platform must degrade gracefully (show field polygons only, no raster overlay). *Mitigation*: tile layer loads conditionally; connection failure is silent.
- **[Risk] Band naming varies** — some scenes use `nir08`, others `nir`. *Mitigation*: scene index records actual band names; tile server maps to standard names.

## Files Touched

- `scripts/build_tile_index.py` (new) — scans `Data/Metric/scenes/`, emits `scenes_index.json`
- `scripts/serve_tiles.py` (new) — local tile server for RGB/NDVI tiles
- `platform/src/data/scenes_index.json` (new) — scene manifest
- `platform/src/views/MapExplorer.tsx` — tile layer controls + scene selector
- `openspec/changes/add-rgb-ndvi-tile-layer/specs/platform-visualization/spec.md` (new)
