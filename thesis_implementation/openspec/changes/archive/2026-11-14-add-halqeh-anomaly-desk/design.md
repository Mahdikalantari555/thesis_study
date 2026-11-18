# Design: `add-halqeh-anomaly-desk`

## Context

Source of the port: `D:\RS\Thesis\Halqeh\6Q1Lwhm26cf8VXbV-grok-workspace` (Grok
app-builder workspace, stays outside the repo and is never committed). App-relevant
files there: `src/components/desk.tsx` (516 L), `src/components/ring.tsx` (157 L),
`src/components/season-chart.tsx` (174 L), `src/data/corpus.ts` + `corpus.json`
(12-case snapshot), `src/lib/desk-store.ts` (zustand + persist), `src/styles.css`.
Everything else (better-auth, pglite, migrations, multiplayer, grok-PWA, preview
bridge, `.vercel`, `.grok`, screenshots, `package-lock.json`) is sandbox scaffolding
and is discarded.

Target stack (already in the platform): React 19 + Vite + Tailwind 4, Leaflet,
recharts, i18n context with EN/FA + Persian digit helpers, payloads imported from
`platform/src/data/*.json` and guarded by `tests/unit/test_platform_data_contract.py`.

Real artifacts consumed (frozen 2026-11-11 run, `summary.json` git_sha `41f87f1…`):

- `reports/stage_conditioned_anomaly/stage_conditioned_anomaly.parquet` — 17,143 rows ×
  14 cols (`field, cycle_id, bin_index, progress, stage, ndvi, cycle_length_days,
  censored, envelope_median, envelope_mad, envelope_lower, envelope_upper, is_anomaly,
  bin_date`); 799 cases, 370 fields, stages `S1_establishment_growth` …
  `S4_harvest_dormancy`
- `reports/stage_conditioned_anomaly/summary.json` — totals, per-stage envelopes,
  `n_valid_obs` 18,505, seed, bin_days 15, envelope_k 2.0, git_sha, data_source
- farm registry already flowing into `platform/src/data/farms_khuzestan.json`
  (`id: "F-001"` … `"F-490"`, `code`, `name`, `farm`, `municipality`, `variety`,
  `areaHa`, `centroid`, `polygon`) — the parquet's integer `field` maps to `"F-%03d"`

## Decisions

### D1 — Full replay replaces the 12-case curation

The Grok build hand-picked 12 cases into `corpus.json` (57 KB). The desk payload
instead contains all 799 cases / 17,143 bins. Estimated size ~2–3 MB (rounded floats,
short keys) — acceptable next to the ~86 MB series payload the platform already
imports, and it removes a silent selection bias: a reviewer must be able to reach any
case, including "spared" ones that show the envelope keeping quiet. The desk's case
list already filters/scrolls; the sampler just gets bigger.

### D2 — Payload is generated only by the exporter, then committed

Follow the established pattern (`farms_khuzestan.json`, `series_khuzestan.json`):
`scripts/export_platform_data.py` gains a `--desk` export path (runs by default with
the rest, smoke-testable) that reads the parquet + summary + registry and writes
`platform/src/data/desk_khuzestan.json` deterministically (sorted case ids, rounded
floats). Totals that cannot be recomputed from the parquet (`n_valid_obs`) are copied
from `summary.json`; naive-cut counts are computed from `ndvi < naive_cut`. The view
imports the JSON (`?raw` + one-time parse, same as the series payload) and never
computes case data itself. If the run is ever re-generated, re-running the exporter
re-emits the payload; the view has no independent data path.

### D3 — No zustand; platform state idioms

Halqeh's `desk-store.ts` (zustand + persist) is replaced by local React state inside
`AnomalyDesk.tsx`; persistence uses a tiny `localStorage` helper namespaced
`platform.desk.*` (verdicts, notes, last case/mode/filter — locale stays owned by the
platform i18n context, so the desk has no separate language toggle; it follows the
platform switcher). Verdict semantics unchanged: `stress | delay | gap | clear` per
case id (`"<field>-<cycle>"`).

### D4 — DeskMap is a new focused component, not MapView

`MapView.tsx` is coupled to the model/indicator/date-slider machinery of the map
explorer. The desk gets `DeskMap.tsx`: given a case (polygon + centroid from the farms
payload) and the selected bin date, it (1) fetches `/scenes` from the tile server
once, (2) picks the nearest scene date within ±15 days (the run's `bin_days`) of the
bin date — preferring NDVI-capable scenes, (3) overlays
`/tiles/<scene-date>/<ndvi|rgb>/{z}/{x}/{y}.png` with an opacity slider, (4) shows the
scene date actually used, and (5) degrades to basemap + polygon with an explicit
"scene absent" state when the fetch fails, no scene qualifies, or both layer types are
missing. All the tile-server contract rules (transparent-PNG 404s, zoom clamp 8–14,
cache headers) already exist and are reused unchanged. The original SVG centroid
scatter is dropped — with rasters available it would be a regression.

### D5 — Scoped theme, platform fonts

The desk keeps its editorial identity (paper/ink/cane/slip palette, serif display
headings, rounded-2xl cards) via Tailwind arbitrary values + a `desk-theme` CSS block
scoped under the view's root element; no global stylesheet or `App` shell changes
beyond the nav entry. Fonts stay the platform's existing stacks (the FA font stack
already covers the desk's Persian text); the Grok build's fontsource packages
(Newsreader/Outfit/Vazirmatn) are not added unless the platform lacks a needed weight
— check during implementation, prefer zero new dependencies.

### D6 — i18n keys, not a COPY map

All strings from Halqeh's `COPY` (en/fa) plus stage metadata (`STAGES` en/fa notes)
move into `platform/src/i18n/en.ts` / `fa.ts` under `desk.*`, reusing the platform's
`t()` and `formatNumber`/`toPersianDigits` helpers. The desk's own EN/FA toggle is
removed — the platform language switcher drives it. The honesty copy (stage
inference, anomaly ≠ stress, censored reading) is carried over verbatim in both
languages and covered by the spec scenarios.

### D7 — Export format for review sessions

`GET desk-review.json` (download via Blob): `{ exported_at, payload_provenance,
annotations: { "<case-id>": { verdict, note, updated_at } } }` — only user-authored
state plus provenance; reviewers save it under `reports/expert_reviews/` by hand
(no auto-write from the browser). This is the hook that later turns desk sessions
into L4 evidence; it is not yet an analysis input, and nothing in the platform reads
these files back yet.

### D8 — Honesty guardrails carried from the source

Kept verbatim in EN/FA copy and enforced in the payload: stages "guessed from
progress inside the cycle, not from recorded planting dates"; "nothing here is a
confirmed stress label"; censored-cycle notice; the footer distinguishes the published
run (summary.json totals) from the replay. The comparison sentence (naive-only vs
envelope-only counts) is computed, not quoted. The desk makes no L4+ claim anywhere.

## Risks / Trade-offs

- **Payload size (~2–3 MB) in the single-file build** — accepted; the series payload
  is already ~86 MB and parsed once via `?raw`. Desk payload uses the same pattern.
- **Bin dates vs scene dates rarely coincide** (15-day bins, 9.3-day revisit, clouds)
  — mitigated by the nearest-scene window + explicit scene-date label; never relabels
  a bin as the scene date.
- **localStorage fragility** (cleared by browser, device-bound) — accepted and
  labelled in the UI; export is the durability path.
- **799-row case list render cost** — the list is plain DOM with SVG sparklines like
  the source build (which rendered its subset the same way); if profiling shows a
  problem, cap to filter-matched cases (the filters already do this). No virtualizer
  dependency unless needed.

## Migration Plan

1. Exporter change + contract tests + payload regeneration (nothing user-visible yet).
2. View/components/i18n port behind the new nav entry (view renders from payload).
3. DeskMap + raster wiring.
4. Gates: contract tests, tsc, build, screenshots (tile server on + off).
5. Docs: note the desk in `docs/platform_presentation_audit.md`'s scope via the
   screenshot audit output; no legacy migration (new surface).

## Open Questions

- None blocking. (Deferred by out-of-scope: CWSI/LST raster layers; server-side
  annotation storage; reading exported reviews back into any analysis.)
