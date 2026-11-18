# Design

## Context

A 2026-11-07 runtime probe (headless browser + curl, screenshots in `%TEMP%/platform-probe/shots/`) established:

- All 8 views (`overview, map, temporal, spectral, validation, comparison, spatial, reports`) run on the bundled real payloads (`series_khuzestan.json`, `farms_khuzestan.json`, `scenes_index.json`) with **zero console errors**; there are no fetch calls and no leftover synthetic series. `data/mock.ts` is really the typed loader for real JSON — only its name and a few copy strings are stale.
- **Tile layer defect is server-side**: `serve_tiles.py:104-119` hands the same `WarpedVRT`/`WarpedBand` object to every `ThreadingHTTPServer` thread; the lock guards only the dict, not the subsequent `read()` (`:267-275`, `:131-161`). Real Leaflet pans → `500`s → process death (exit 3221225477 / 0xC0000005). The same URLs serially → all 200; 9/9 RGB and NDVI tiles rendered on-map when requests were serialized. Client URL construction in `MapView.tsx:87` is correct.
- Secondary: error paths answer `<img>` requests with JSON (`net::ERR_BLOCKED_BY_ORB`); `do_HEAD` missing (501); no `Cache-Control`; newly mounted raster layer ignores the current opacity until the slider moves (`MapView.tsx:87-101`).
- Payload gaps: `precip`/`temp` 0/23,520 non-null yet declared `provenanceDefault: 'modelled'` (`channels.ts:29-30`) → blue "Modelled" chips on "—" values; farms JSON `farm`/`municipality`/`name` are f-string fabrications (`export_platform_data.py:344-345`) while `Data/Processed/coordinates/farms.parquet` carries real `farm/block/variety/status/management/office/area_ha`; `planted`/`harvest` already null (no source column exists — `age` only).
- `weather_aligned.parquet` (539 rows × 57 cols: `precipitation_sum`, `temperature_mean/min/max`, `et0_sum`, 3/7/14/30d windows) exists but is unwired.

## Goals / Non-Goals

**Goals:**
- Tile server that survives real browser concurrency (P0 blocker for the raster layer).
- Payload and UI in which nothing user-visible is synthesized or mislabelled; weather + farm metadata wired from real artifacts.
- A repeatable headless-browser verification gate (screenshots + console/network) covering all views and tile rendering.

**Non-Goals:**
- Per-pixel interactive views (pixel parquets remain available; no current view needs them).
- Contract v4 (v3 value-set change only), new views, model retraining.
- Production hosting of the tile server (local laptop only, per `add-rgb-ndvi-tile-layer`).

## Decisions

### 1. Thread-safety: per-handle lock held across reads
Give each cached `WarpedBand` its own `threading.Lock`; `_render_tile` holds the band's lock across `read_vrt_window`. Cheapest correct fix; keeps parallelism across *different* bands/dates.
- *Alternative A — global render lock*: trivially safe, serializes all tiles; kept as the documented fallback if GDAL still proves non-reentrant in this env (the burst test is the gate that decides).
- *Alternative B — per-thread dataset open*: highest parallelism, but memory ×N and WarpedVRT rebuild cost per request; rejected for a local laptop server.

### 2. Image-safe error contract
All tile-route failures (unknown date, zoom clamp, missing bands, internal error) return `404`/`500` with `Content-Type: image/png` and a transparent-PNG body; `/scenes` keeps JSON errors (fetched via fetch, not `<img>`). Add `do_HEAD` mirroring GET semantics and `Cache-Control: max-age=3600` on successful tiles.

### 3. Weather wiring at export time
`export_platform_data.py` left-joins `weather_aligned.parquet` on the observation's acquisition date and fills `precip` (from `precipitation_sum`) and `temp` (from `temperature_mean`); unmatched dates stay `null`. Provenance semantics unchanged — reanalysis weather is legitimately `modelled` *when a value exists*; the frontend fix (`normaliseObs`) is to force `provenance: 'absent'` for any `null` channel so the chip can never claim "Modelled" on "—". ET0/wind/windows stay out of scope until a view needs them.

### 4. Farm metadata from the registry, same field names
Map `farms.parquet` real columns into the existing v3 fields (no contract bump): `farm` ← registry `farm`/block composition as actually stored, `municipality` ← `office` (+`management`), keep real `variety`/`areaHa`; `status`/`management` added to the inspector payload only if the existing UI already renders them — otherwise dropped to avoid dead payload. Empty registry values → `""`/`null`, never generated text.

### 5. Verification gate extends the existing CDP script
`scripts/capture_platform_screenshots.mjs` already drives the production build over raw CDP for all 8 nav ids; extend it to also record console messages, page errors and failed requests per view, and add a Map Explorer tile scenario (start tile server → select date+RGB → assert tile responses 200 + screenshot; repeat NDVI; stop server → assert graceful degradation). Acceptance: zero console errors in normal operation (the unavoidable `<img>` `ERR_CONNECTION_REFUSED` lines appear only in the deliberate server-down run), zero page errors everywhere, tile evidence screenshots saved.

### 6. Copy and dead-code cleanup
Banner → dataset-integration wording ("Khuzestan Sugarcane agro-industry dataset — Landsat & METRIC archive 2013–2026, 490 fields"); `DemoDataBadge` → `PipelineDataBadge` wording ("Pipeline output — research validation pending"); delete `stressEvent` plumbing + its i18n strings (payload field is null for all 490 fields); footer cadence copy → "Landsat & METRIC (2013–2026 archive)"; rename `data/mock.ts` → `data.ts` with import updates.

## Risks / Trade-offs

- **[Risk] GDAL may still fault even with per-handle locks** (env-specific reentrancy). *Mitigation*: the 12-thread burst test + headless pan is the acceptance gate; if it faults, fall back to the global render lock (decision 1, alternative A) and re-run the gate.
- **[Risk] Weather row/date alignment** (539 rows vs 538 Landsat dates, duplicate dates possible). *Mitigation*: left-join on exact date; on ambiguity take the first row and log; unmatched → null + `absent`; contract test asserts non-null fraction > 0 and no null-labelled-modelled.
- **[Risk] Registry column semantics are Persian/operational** (`داشت`, `تولید دوم`, `اداره چهارم`). *Mitigation*: pass through verbatim (FA locale renders naturally); no translation layer in this change.
- **[Trade-off] Serializing tile renders (fallback) slows first pan** on large scenes — acceptable for a local single-user server.

## Migration Plan

1. Land server fixes + burst test (no data change). 2. Regenerate payloads (weather + metadata) and land frontend provenance/copy fixes together so chips never mislabel during the transition. 3. Run the verification gate; update `docs/platform_bug_audit.md`. Rollback: payloads are one exporter re-run away; server changes are isolated to `serve_tiles.py`.

## Open Questions

None — badge/banner wording defaults are recorded above and are trivially adjustable after review.
