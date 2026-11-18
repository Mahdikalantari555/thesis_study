# Tasks — Add RGB/NDVI Tile Serving Layer

## 1. Scene index & tile pipeline
- [x] 1.1 Implement `scripts/build_tile_index.py` — scan `Data/Metric/scenes/`, parse MTL.json for date/bounds/bands, emit `platform/src/data/scenes_index.json` (607 scenes, 2013-03-30 → 2026-09-10, sorted; ~32 s full run; header-only reads per scene)
- [x] 1.2 Implement `scripts/serve_tiles.py` — lightweight HTTP tile server; open GeoTIFFs with `rasterio`, render 256×256 RGB/NDVI tiles, reproject to Web Mercator (stdlib `ThreadingHTTPServer` + `WarpedVRT` EPSG:3857 + LRU band cache + /scenes endpoint; z clamped 8–14; note: `rasterio.windows.from_bounds` segfaults in this env, so tile windows are computed manually)
- [x] 1.3 Verify tile server responds with valid PNG tiles for at least one RGB and one NDVI scene (18/18 checks passed: PNG magic, 256×256, 404 outside z8–14, transparent for out-of-extent tiles; RGB 138 474 B, NDVI 86 575 B)

## 2. Platform integration
- [x] 2.1 Add scene/date selector dropdown to `MapExplorer.tsx` (populated from `scenes_index.json` — statically imported like the other data JSONs)
- [x] 2.2 Add layer toggle (None / RGB / NDVI) + opacity slider (0–1) to map controls (separate raster opacity from the existing polygon-fill opacity; options filtered by the scene's has_rgb/has_ndvi)
- [x] 2.3 Wire Leaflet tile layer to local tile server URL; conditional load (degrades gracefully if server unavailable) (`http://127.0.0.1:8765/tiles/{date}/{layer}/{z}/{x}/{y}.png` via a `TileLayer` in `MapView.tsx`, `minNativeZoom` 8 / `maxNativeZoom` 14, empty `errorTileUrl`, layer mounted only when scene+layer selected)
- [x] 2.4 Verify map renders field polygons with optional RGB/NDVI overlay (code-level: `tsc --noEmit` + `vite build` clean, tile URL and raster i18n keys present in `dist/index.html`; visual check: run `scripts/serve_tiles.py --port 8765` then `npm run dev` and pick a date in Map Explorer)

## 3. Tests & verification
- [x] 3.1 Add unit test for scene index generation (validates JSON structure, band flags, date parsing) (`tests/unit/test_build_tile_index.py`, 7 tests on a synthetic tmp_path scene tree; all pass)
- [x] 3.2 Run `tsc --noEmit` → 0 errors
- [x] 3.3 Build frontend (`bun run build` or `node node_modules/vite/bin/vite.js build`) → 0 errors (note: esbuild's default %TEMP% cleanup failed under this shell; build passes with `TMP/TEMP` pointed at a repo-local temp dir)

## 4. Docs & commit
- [x] 4.1 Add tile layer spec to `openspec/changes/add-rgb-ndvi-tile-layer/specs/platform-visualization/spec.md` (ADDED Requirements: scene index manifest, on-the-fly tile serving, frontend controls, graceful degradation — each with scenarios; `openspec validate add-rgb-ndvi-tile-layer` → valid)
- [x] 4.2 Commit all changes on current branch (kept `platform/src/data/scenes_index.json` tracked — the frontend statically imports that manifest and a fresh clone cannot build without it)
