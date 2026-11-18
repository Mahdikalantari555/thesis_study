# Proposal: Add the Halqeh Anomaly Desk as a Platform View (`add-halqeh-anomaly-desk`)

## Why

The stage-conditioned anomaly run (findings doc 14, 2026-11-11: 17,143 stage-assigned
bins, 799 field-cycles, 370 fields, 1,774 flags, 9.59% flag rate) currently has no
review surface inside the repo: the numbers exist as parquet + a findings table, but a
reviewer cannot browse the cases behind them. A bilingual (EN/FA) case-review desk —
"Halqeh" (حلقه, "ring") — was built in a Grok app-builder workspace
(`D:\RS\Thesis\Halqeh\6Q1Lwhm26cf8VXbV-grok-workspace`, outside the repo) to replay
exactly this run: a season ring per case, a stage-envelope vs. blunt-NDVI-cut chart,
verdict buttons (stress candidate / phenology delay / cloud-gap / not a slip), and
per-case field notes. That build is not usable as-is:

- Its data is a frozen, hand-curated snapshot (`corpus.json`: **12 of 799 cases**
  hand-picked) whose totals cannot be re-derived from the repo — a provenance defect
  under prime directive 2.
- It depends on Grok sandbox scaffolding (better-auth, pglite, migrations, grok-PWA,
  preview bridge, `.vercel`/`.grok` state) that must never be committed.
- Its locator "map" is an SVG scatter of 490 centroids — no raster context, so a
  reviewer cannot see **what the field actually looked like** on a flagged date.
- It has no test, typecheck, or screenshot gates.

This change ports the desk into the platform as a ninth view, rewrites its data path
onto the real run artifacts, and adds per-flagged-date raster display reusing the
existing tile server. Work proceeds on branch `add-halqeh-anomaly-desk`; nothing from
the Halqeh workspace directory is committed.

## What Changes

- **Desk payload from real artifacts (P0)**: `scripts/export_platform_data.py` gains a
  desk export that joins `reports/stage_conditioned_anomaly/stage_conditioned_anomaly.parquet`
  (all 799 cases, every bin) + `summary.json` (totals, envelopes, run provenance) +
  the farm registry (code/name/farm/municipality/variety/area/centroid) into
  `platform/src/data/desk_khuzestan.json`. The 12-case curation is replaced by the
  complete replay; naive-cut counts (NDVI < 0.40) are computed, not quoted.
- **New platform view (P0)**: `platform/src/views/AnomalyDesk.tsx` (+ `SeasonRing`,
  `SeasonChart` components) ports the desk UI: case list with all/slip/spared/unread
  filters, envelope vs. naive mode, stage rule panel, verdict buttons, field notes,
  censored-cycle marking. Halqeh's paper/ink/cane identity is kept as a **scoped
  theme** inside the view; platform fonts and i18n machinery are used.
- **Verdicts and notes: device-local + export (P1)**: verdicts/notes persist in
  `localStorage` (labelled "kept on this device", as in the original) and a new export
  button downloads the review session (verdicts, notes, case ids, export timestamp,
  payload provenance) as JSON, so a review session can be archived under `reports/`
  as L4 evidence.
- **Raster display in the desk (P1)**: a `DeskMap` Leaflet component shows the
  selected case's field polygon (from the farms payload) with an NDVI/RGB raster
  overlay for the selected bin's date — resolved to the nearest available scene date
  from the tile server's `/scenes` index, with the existing graceful "tile absent"
  degradation when the server is not running. Reuses `serve_tiles.py` unchanged.
- **i18n + honesty copy (P0)**: all desk strings move into `platform/src/i18n/en.ts` /
  `fa.ts` (`desk.*` keys) with Persian digit formatting; the honesty copy survives
  verbatim in both languages: stages are inferred from within-cycle progress (not
  recorded planting dates); "anomaly is not stress" — verdicts are review annotations,
  never ground truth; censored cycles read as incomplete.
- **Gates (P0)**: desk payload contract tests in `tests/unit/test_platform_data_contract.py`;
  `tsc --noEmit`; production build; screenshot capture extended to the desk view
  (zero console/page errors), with a tile-server-off degradation run.

## Capabilities

### New Capabilities
- `platform-anomaly-desk`: A platform view that replays the stage-conditioned anomaly
  run for human case review — complete case data originating from the run's parquet +
  summary artifacts, honest anomaly-vs-stress framing, device-local review annotations
  with export, and per-bin-date raster context via the local tile server.

### Modified Capabilities
- None. `serve_tiles.py`, the payload contracts for farms/series, and existing views
  are untouched.

## Impact

- `scripts/export_platform_data.py` — desk payload export (new section)
- `platform/src/data/desk_khuzestan.json` — new generated payload
- `platform/src/data/desk.ts` — new typed loader (mirrors `data.ts` pattern)
- `platform/src/views/AnomalyDesk.tsx`, `platform/src/components/SeasonRing.tsx`,
  `platform/src/components/SeasonChart.tsx`, `platform/src/components/DeskMap.tsx` — new
- `platform/src/App.tsx`, `platform/src/context/AnalysisContext.tsx` — ninth nav entry + view id
- `platform/src/i18n/en.ts`, `platform/src/i18n/fa.ts` — `desk.*` strings
- `tests/unit/test_platform_data_contract.py` — desk payload contract tests
- `scripts/capture_platform_screenshots.mjs` — desk view in the capture set
- NOT touched: `scripts/serve_tiles.py`, `MapView.tsx`, existing payloads/contracts,
  existing views
- NOT committed, ever: anything under `D:\RS\Thesis\Halqeh\` (Grok workspace; source
  of the port only)

## Out of Scope

- Changing the tile server or adding new raster products (CWSI/LST rasters come later,
  only if requested, as tile-server work)
- Re-running the stage-conditioned job or touching its outputs (the 2026-11-11 run is
  consumed frozen; re-running later just re-emits the payload)
- Server-side persistence of verdicts/notes (device-local + JSON export only; the
  platform is an offline single-file build)
- The remaining Grok-scaffold features (auth, pglite, multiplayer, PWA, preview bridge)
- Any claim upgrade: the desk remains a review tool for stage-conditioned NDVI
  anomalies (validation ladder L2–L3 evidence browsing), not a stress diagnosis —
  L4 evidence accrues only when exported reviews are checked against independent
  agronomic records
