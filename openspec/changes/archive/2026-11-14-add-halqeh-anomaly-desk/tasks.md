# Tasks

## 1. Desk payload from real artifacts (P0)

- [x] 1.1 Branch setup confirmed: work on `add-halqeh-anomaly-desk`; nothing under `D:\RS\Thesis\Halqeh\` is ever `git add`-ed (verify with `git status` after every port step).
- [x] 1.2 `scripts/export_platform_data.py`: add the desk export — read `reports/stage_conditioned_anomaly/stage_conditioned_anomaly.parquet` + `summary.json` + the farm registry source already used for the farms payload; emit `platform/src/data/desk_khuzestan.json` with: per-case `{id "<field>-<cycle>", field, fieldId "F-%03d", code, name, farm, municipality, variety, areaHa, centroid, cycle, lengthDays, censored, start, end, flags, naive, deepest, kind, bins[{i, p, stage, v, lo, hi, med, d, f}]}`; per-stage envelopes + totals (rows/flags/flagRate computed from the parquet; naive counts computed as `ndvi < 0.40`; `validObsReported` from summary.json); `places` (490 registry centroids); provenance block (`git_sha`, `generated_at`, `data_source`, `seed`, `bin_days`, `envelope_k`, `naive_cut`, source paths). Deterministic ordering; NaN never serialized (null). Verify: `--smoke` run then full run; JSON parses; sizes reported.
- [x] 1.3 Contract tests in `tests/unit/test_platform_data_contract.py`: complete replay (case count == parquet (field,cycle) count; every bin appears exactly once, ordered; totals recompute-match the parquet; naive counts == computed; envelopes match summary.json within rounding; every case's registry fields equal the registry row or are null (no generated strings); provenance block present and matching summary.json; no NaN/Infinity anywhere). Verify: `D:\Dev\Miniforge3\envs\geo\python.exe -X utf8 -m pytest tests/unit/test_platform_data_contract.py -q` green.

## 2. View port: AnomalyDesk (P0)

- [x] 2.1 Typed loader `platform/src/data/desk.ts` (import `desk_khuzestan.json?raw`, parse once, export types + accessors mirroring `corpus.ts`); stage display metadata (S1–S4 names/notes, from-progress fractions) moved into the loader/i18n. Verify: `tsc --noEmit` 0 errors.
- [x] 2.2 Port `SeasonRing` (from `ring.tsx`) and `SeasonChart` (from `season-chart.tsx`) into `platform/src/components/` — no zustand/Radix; props-driven; recharts/SVG as in source; accessible names on interactive SVG. Verify: tsc; visual check in dev server.
- [x] 2.3 Port the desk as `platform/src/views/AnomalyDesk.tsx`: case list (all/slip/spared/unread filters + counts), envelope vs. naive mode, stage-rule panel, reading panel, verdict buttons, notes textarea, censored notice, footer with computed published-run vs. replay sentence. State via `useState`/`useMemo` (design D3); persistence via localStorage keys `platform.desk.verdicts` / `platform.desk.notes` / `platform.desk.ui`. Verify: dev-server walk-through of one slip + one spared case in EN and FA.
- [x] 2.4 i18n: all desk copy into `i18n/en.ts` + `fa.ts` under `desk.*` (carrying the honesty copy verbatim in both languages), Persian digit formatting through the platform helpers; desk follows the platform language switcher (no internal toggle); nav entry + `nav.desk`/`nav.deskDesc` keys; i18n parity check (en/fa key sets equal). Verify: `pytest tests/unit/test_platform_bilingual.py -q` green; `tsc --noEmit`.
- [x] 2.5 Scoped theme (design D5): desk palette/typography scoped under the view root; platform fonts only, zero new npm dependencies (if a needed weight is missing, stop and record it instead of adding packages silently). Verify: existing views unaffected (screenshot spot-check of one other view).

## 3. Review annotations: persistence + export (P1)

- [x] 3.1 Verdicts/notes survive reload from localStorage (namespaced keys; corrupt JSON → start clean, no crash); honest label "kept on this device" present in both languages. Verify: manual reload check + code-level test of the load/save helpers.
- [x] 3.2 Export button (design D7): Blob download `halqeh-desk-review-<timestamp>.json` = `{exported_at, payload_provenance, annotations}` with only user-authored state; filename/timestamp ASCII. Verify: exported file parses; contains set verdicts/notes; absent annotations omitted; provenance matches the payload root.

## 4. Raster context: DeskMap (P1)

- [x] 4.1 `platform/src/components/DeskMap.tsx`: Leaflet map, field polygon + centroid from the farms payload (basemap per platform convention); fetch `/scenes` once; nearest-scene selection within ±15 days of the selected bin date (prefer scenes with the requested layer); layer toggle NDVI/RGB + opacity slider; explicit label of the scene date used vs. the bin date. Verify: with `serve_tiles.py --port 8765` running, selecting bins with and without nearby scenes shows overlay / "scene absent" respectively; zero console errors.
- [x] 4.2 Degradation: tile server stopped → basemap + polygon render, raster control shows absent state, no broken-tile widgets or console/page errors (reuse the transparent-PNG 404 contract; do not modify `serve_tiles.py`). Verify: headless run per 5.2.

## 5. Gates, evidence, docs

- [x] 5.1 Extend `scripts/capture_platform_screenshots.mjs` to the 9-view set: desk scenarios (EN + FA, a selected slip case, envelope + naive modes; tile-server-on raster screenshot; tile-server-off degradation run). Verify: script green end-to-end over the production build.
- [x] 5.2 Full gate on this branch, results reported verbatim: (1) `D:\Dev\Miniforge3\envs\geo\python.exe -X utf8 -m pytest tests/unit/test_platform_data_contract.py tests/unit/test_platform_bilingual.py -q`; (2) `node node_modules/typescript/bin/tsc --noEmit` and `TMP/TEMP → platform/.tmpbuild node node_modules/vite/bin/vite.js build` in `platform/`; (3) `serve_tiles.py --port 8765` + capture script (`--locale en`), plus a `--no-tile-server` run; (4) `python scripts/test_tile_concurrency.py` only if tile-serving code changed (expected: no). Evidence committed under `reports/`.
- [x] 5.3 Regenerate + commit the desk payload and all code in conventional single-purpose commits on `add-halqeh-anomaly-desk`; confirm `git status` shows no path from `D:\RS\Thesis\Halqeh\` and no Grok scaffolding anywhere in the diff.
- [x] 5.4 Record validation-ladder framing in the view (footer: run provenance, L2–L3 evidence browsing; verdicts are annotations, not ground truth) — no metric or accuracy claim appears in the desk. Verify: grep the desk + i18n for accuracy/performance phrasing.

## 6. Wrap-up

- [x] 6.1 Update `docs/platform_bug_audit.md` only if gate runs surfaced defects; otherwise note the audit outcome (clean) with the run date.
- [x] 6.2 Summarize for the user: what was ported vs. dropped, payload stats (n cases/bins, size), gate outputs, and the exact remaining manual step (none expected — long-running jobs are not introduced by this change).
