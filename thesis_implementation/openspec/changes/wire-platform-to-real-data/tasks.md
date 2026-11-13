# Tasks

## 1. Tile server robustness (P0)

- [x] 1.1 Per-handle locking in `scripts/serve_tiles.py`: each cached `WarpedBand` gets a `threading.Lock` held across `read_vrt_window`/render; verify: existing tile checks still pass (RGB + NDVI 200, valid PNG).
- [x] 1.2 Image-safe error contract + HEAD + caching: tile-route failures return 404/500 with `Content-Type: image/png` transparent body; add `do_HEAD` for `/scenes` and tile routes; add `Cache-Control: max-age=3600` on successful tiles. Verify: curl shows image/png 404 for z15 and unknown date, `HEAD /scenes` → 200 with headers, no JSON bodies on tile routes.
- [x] 1.3 Concurrency acceptance gate: script (scratch or `scripts/test_tile_concurrency.py`) fires a 12-thread burst across dates/layers → all responses valid PNG or image-safe 404, process alive, subsequent request succeeds; then repeat a headless-browser Leaflet pan against the live server → zero connection resets, tiles rendered. If the process still faults, switch to the documented global-render-lock fallback and re-run the gate (record which variant shipped).

## 2. Real weather in the payload (P1)

- [x] 2.1 `scripts/export_platform_data.py`: left-join `Data/Processed/weather/weather_aligned.parquet` on acquisition date → fill `precip` (`precipitation_sum`) and `temp` (`temperature_mean`); unmatched dates stay null; log join coverage. Verify: exporter run logs non-null fraction > 0 for both channels (target ≥ 90% of dated observations).
- [x] 2.2 Frontend `platform/src/data/mock.ts` (`normaliseObs`): any null channel gets provenance `absent` (never `modelled`); verify: unit check that a null precip renders the not-measured state, and `channels.ts` defaults no longer mislabel nulls.
- [x] 2.3 Regenerate payloads; extend `tests/unit/test_platform_data_contract.py`: precip/temp non-null fraction > 0, no observation has a null value with `modelled`/`measured` provenance, contract version unchanged (v3). Verify: pytest contract file all pass; `tsc --noEmit` 0 errors.

## 3. Real farm metadata (P1)

- [x] 3.1 `scripts/export_platform_data.py`: populate `farm`/`municipality`/`name` from real `farms.parquet` columns (`farm`, `block`, `office`, `management`); keep real `variety`/`areaHa`; missing registry values → empty/null; drop `status`/`management` from the payload unless an existing view renders them. Verify: regenerated farms JSON contains zero matches for `Khuzestan Unit` / `Amir Kabir / Debal Khazai` synthesized patterns.
- [x] 3.2 Contract test addition: every field's `farm`/`municipality` equals the registry-mapped value for its code (spot-parity on a sample of codes against `farms.parquet`); inspector fields render registry text (code-level check via the normalizer). Verify: pytest passes.

## 4. Honest UI copy and dead-code removal (P2)

- [x] 4.1 Reword dataset banner (`App.tsx`/`AnalysisContext.tsx`/i18n) to dataset-integration wording and `DemoDataBadge` (`ui.tsx` + its 4 call sites) to pipeline-output wording; fix stale footer cadence copy (`i18n/en.ts:178` + `fa.ts` parity). Verify: `tsc --noEmit` 0 errors; bilingual i18n parity test still passes; grep of `platform/src` for "demonstration"/"Mock stress" returns no user-visible copy.
- [x] 4.2 Remove dead `stressEvent` machinery (payload field, normalizer, `MapExplorer.tsx:351-359`, i18n strings en+fa). Verify: grep no references; tsc + build 0 errors.
- [x] 4.3 Rename `platform/src/data/mock.ts` → `data.ts`, update all importers; keep the null-channel provenance fix from 2.2. Verify: `node node_modules/typescript/bin/tsc --noEmit` and `node node_modules/vite/bin/vite.js build` both 0 errors (TMP workaround if esbuild needs it).
- [x] 4.4 Opacity persistence: `MapView.tsx` mounts new raster layers with the current `rasterOpacity` (create-time opacity or `setOpacity` right after add). Verify: code-level + runtime check in 5.2 that a 0.7 opacity survives an RGB→NDVI switch.

## 5. Runtime verification gate & docs

- [x] 5.1 Extend `scripts/capture_platform_screenshots.mjs`: per-view console messages, page errors, failed network requests; Map Explorer tile scenario (server up: select date + RGB, assert tile URLs 200 + on-map render, repeat NDVI; server stopped: graceful degradation). Verify: script runs green end-to-end over the production build.
- [x] 5.2 Run the full gate: all 8 views → zero console errors / zero page errors / screenshots saved (normal operation); RGB and NDVI tile evidence screenshots; server-down run shows no crash. Archive evidence under `reports/` (gitignored figures dir or docs path consistent with repo convention).
- [x] 5.3 Update `docs/platform_bug_audit.md`: record the serve_tiles thread-race finding + fix, weather/meta wiring, copy cleanup; note BUG-24/25 final state (real registry wiring / null-with-no-source). Verify: doc references match shipped behavior.
- [x] 5.4 Commit all changes on the current branch.

## 6. Map Explorer UX (user-requested during apply, 2026-11-07)

- [x] 6.1 "Hide field boundaries" hides only the field-polygon layer: `MapView` gains a `showFields` prop and stays mounted; basemap + raster overlay remain visible. Verify: code + tile-scenario screenshot with polygons hidden but raster rendered.
- [x] 6.2 Remove the 20% opacity floor: fields-layer slider `min` 0.2 → 0 (raster opacity slider already allows 0); at 0 the polygon layer is fully invisible (fill and stroke). Verify: code-level check.
- [x] 6.3 Single date control: remove the "Landsat raster scene" select; the observation-date slider drives both the field series and the raster overlay (raster date = the observation's real `acquisitionDate` from the payload; no scene for that date → raster off). Update the capture-script tile scenario to drive the date slider. Verify: `tsc --noEmit`, build, and the 5.2 gate with RGB + NDVI tiles following the date slider.

## 7. User-requested follow-ups (2026-11-07, second wave — applied under this change)

- [x] 7.1 Full-archive observation axis (contract v4): every acquisition date 2013-03-30 → 2026-09-10 (538 dates, 263,620 observations; multi-acquisition months kept; sampleDate == acquisitionDate; staleness branch removed). Payload compacted 292 MB → 29.8 MB (shared axis, per-field arrays, RLE provenance, derived formula ids); `?raw` + JSON.parse load; contract v4 in both registries. Verify: contract+bilingual tests 35 passed; gate green both runs.
- [x] 7.2 RGB tile seams removed: per-scene contrast window (`SceneStretchCache`) replaces per-tile percent stretch. Verify: stitched adjacent tiles continuous.
- [x] 7.3 Inspector provenance chips compacted to grouped lines (`ProvenanceSummary`); per-channel detail on hover; score chip unchanged.
- [x] 7.4 Readable x-axes on the 538-point axis: adaptive `tickInterval` (~6–16 ticks per chart) + larger tick fonts on all date-axis charts.
- [x] 7.5 Scatter displays downsampled to ≤5,000 points (stride sample) — all statistics computed on the full 263,620 pairs; caption states shown/total. Fixes the 60 s main-thread stall on Model Comparison.
- [x] 7.6 Real envelopes for ndvi/evi/savi ([-0.5,1]/[-0.3,1]/[-0.3,1]) replacing the [0,1] registry ranges that rejected real winter medians.
- [x] 7.7 `AGENTS.md` (assistant charter) + `todo.md` (backlog: METRIC products, two-CWSI, cycles viz, retraining, validation ladder, ERA5 covariates, …) at repo root.
