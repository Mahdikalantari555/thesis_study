# Proposal: Wire the Platform Completely to Real Data (`wire-platform-to-real-data`)

## Why

The platform's bundled series/polygon payloads are real pipeline output (contract v3, verified in a 2026-11-07 runtime probe), but user-visible non-real content remains: `precip`/`temp` are 100% null (0/23,520 non-null) yet render "Modelled" chips; farm metadata (`farm`/`municipality`/`name`) is synthesized via f-strings instead of the real `farms.parquet` columns; demo banner/badge copy still says "Demonstration data"; and the raster tile layer is unusable in a real browser session because `scripts/serve_tiles.py` crashes with a native access violation (0xC0000005) under the concurrent tile requests Leaflet actually fires (shared GDAL VRT handles across `ThreadingHTTPServer` threads). The user requires the platform to display only real data from `Data/Processed/` (band means/stats and pixel values from which indices are reproducible).

## What Changes

- **Tile server robustness (P0)**: `scripts/serve_tiles.py` — per-handle locking so concurrent tile requests cannot crash the process; image-safe error responses (transparent PNG instead of ORB-blocked JSON) for unknown date/zoom/layer; `do_HEAD` support; `Cache-Control` headers. Verified by a 12-thread burst test + headless-browser Leaflet pan with the server alive.
- **Real weather in the payload (P1)**: `scripts/export_platform_data.py` joins `Data/Processed/weather/weather_aligned.parquet` on acquisition date so `precip`/`temp` observations carry real values; null channels get provenance `absent` (never "Modelled") in the frontend normalizer.
- **Real farm metadata (P1)**: exporter maps the real `farms.parquet` columns (`farm`, `block`, `office`, `management`, `status`, `variety`, `area_ha`) into the farms JSON instead of synthesized "Khuzestan Unit L08" / "Amir Kabir / Debal Khazai …" strings; unknown/missing values stay empty rather than invented.
- **Honest UI copy (P2)**: dataset banner reworded from "demo" to dataset-integration wording; `DemoDataBadge` reworded to pipeline-output wording; dead mock-stress machinery (`stressEvent` + i18n strings) removed; stale "Sentinel-2 / Landsat-like cadence (demonstration)" footer fixed to Landsat/METRIC 2013–2026; `data/mock.ts` renamed to `data.ts` (it is the typed loader for real JSON, not mock data).
- **Overlay opacity persistence (P2)**: switching scene/layer no longer resets raster opacity to 1.
- **Runtime verification gate**: extend `scripts/capture_platform_screenshots.mjs` with console + network capture; every one of the 8 views must render with zero console errors, and Map Explorer must show RGB and NDVI tiles on-map with the tile server alive.

## Capabilities

### New Capabilities
- `platform-real-data`: The platform payload contains only values originating from real `Data/Processed/` artifacts (stats.zarr band statistics, weather_aligned.parquet, farms.parquet, real geometry), and every displayed channel/score carries an honest provenance label (`model`/`proxy`/`modelled`/`absent`); no synthesized or demo-only fields remain in user-visible payloads.

### Modified Capabilities
- `platform-visualization`: Tile serving must survive concurrent browser load (thread-safety), respond to error conditions with image-compatible bodies, support HEAD and cache headers, and preserve the selected raster opacity across scene/layer changes.

## Impact

- `scripts/serve_tiles.py` — locking, error paths, HEAD, cache headers
- `scripts/export_platform_data.py` — weather join, real farm metadata mapping
- `platform/src/data/series_khuzestan.json`, `farms_khuzestan.json` — regenerated (values only; contract stays v3)
- `platform/src/data/mock.ts` → `platform/src/data/data.ts` (+ all importers) — null-channel provenance fix
- `platform/src/components/MapView.tsx` — opacity persistence; `platform/src/components/ui.tsx` — badge copy; `platform/src/App.tsx`, `AnalysisContext.tsx`, `platform/src/i18n/en.ts`/`fa.ts` — banner/copy/dead-machinery removal
- `scripts/capture_platform_screenshots.mjs` — console/network audit extension
- `tests/unit/test_platform_data_contract.py` — real-weather + real-metadata parity checks
- `docs/platform_bug_audit.md` — record resolutions

## Out of Scope

- Per-pixel interactive views (pixel parquets stay available for future views; all current views consume field-level statistics, which are real)
- Contract version bump (v3 field set is sufficient; only values change)
- Retraining models or new scores (already `"model"`-provenance from `integrate-real-model-outputs`)
- New platform views/routes
