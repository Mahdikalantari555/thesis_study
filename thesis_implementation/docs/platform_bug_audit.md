# Platform Bug Audit — AgriAnomaly Visualization Platform

**Scope:** every page of `platform/` (React 19 + Vite 7 + Tailwind 4), the shared
`AnalysisContext`, the `ui.tsx` / `MapView.tsx` components, and the data layer
(`src/data/mock.ts` + the two exported JSON payloads).
**Change:** `openspec/changes/make-platform-bilingual-and-audit-page-bugs`
**Date:** 2026-11-05
**Method:** static review of every view plus a scripted browser pass
(`scripts/capture_platform_screenshots.mjs`) that mounts the production build in
headless Chrome, switches locale, and walks all eight pages — that pass is what
surfaced several of the runtime issues below (TDZ crash, chart re-measure, bidi
digit reversal).

Severity: **P0** = wrong or misleading data / crash, **P1** = broken interaction
or unreachable feature, **P2** = polish or maintainability risk.

Status legend: **Fixed** = changed in this PR · **Deferred** = documented, needs
pipeline work outside the platform · **Won't fix** = intentional.

---

## Audit matrix (one entry per audited page)

| # | Page / module | Bug | Severity | Status |
|---|---|---|---|---|
| BUG-01 | MapExplorer, Temporal, Spectral, Spatial, Validation | Date sliders hard-coded `max={47}` / range presets `[0,47]`,`[12,23]`,`[24,35]`,`[36,47]` | P0 | **Fixed** |
| BUG-02 | Validation | Year robustness panel hard-coded four windows `[0,12]…[36,48]` and a `2021+y` label | P1 | **Fixed** |
| BUG-03 | Overview | “48 monthly obs / field” and “2021–2024” literals independent of the loaded axis | P0 | **Fixed** |
| BUG-04 | Overview (footer) + App shell | Stale region label “Piracicaba, SP, Brazil” and “Demonstration data — not research results” banner on a Khuzestan dataset | P0 | **Fixed** |
| BUG-05 | AnalysisContext | `FIELDS[9]`, `FIELDS[10]`, `FIELDS[18]` unguarded → crash on short/empty datasets | P0 | **Fixed** |
| BUG-06 | Data layer | Exported `series_khuzestan.json` never imported; views rendered a seeded RNG instead | P0 | **Fixed** |
| BUG-07 | `MapView` | Map destroyed and re-created on every dark-mode toggle (zoom/center lost) | P1 | **Fixed** |
| BUG-08 | `MapView` | Hard-coded `min(47, dateIdx)`; `getSeries(nid)[dateIdx]` could be `undefined` | P1 | **Fixed** |
| BUG-09 | Spatial | `FIELDS.findIndex(...)` produced `-1` for unknown neighbours → `values[-1]` inside Moran's I | P1 | **Fixed** |
| BUG-10 | Overview | Overview table cells rendered `NaN` if a year had no observations | P1 | **Fixed** |
| BUG-11 | All views | Charts rendered blank when captured/printed at a new viewport height | P1 | **Fixed** |
| BUG-12 | All views (fa) | Letter-spacing utilities broke Persian glyph joins; numeric minus signs reversed (`0.547-`) | P1 | **Fixed** |
| BUG-13 | App shell | Sidebar/footer claimed “Landsat & METRIC (2013–2026)” while the axis is 2021–2024 | P0 | **Fixed** |
| BUG-14 | Overview | “Completeness” stat divided by zero on empty data (`NaN %`) | P2 | **Fixed** |
| BUG-15 | ModelComparison | 490-series means recomputed on every render inside JSX; matrix labels untranslated | P2 | **Fixed** |
| BUG-16 | Reports | Seeded experiments used ids/fields that could not exist; experiment names not localized | P2 | **Fixed** |
| BUG-17 | Data layer | `downloadCSV` revoked the object URL synchronously → intermittent failed downloads in Chromium | P2 | **Fixed** |
| BUG-18 | Overview / MapExplorer | “Mock stress event” copy and `mock`-tinted captions presented synthetic flags as facts | P2 | **Fixed** |
| BUG-19 | App shell | Language of `<html>` never updated; no `dir` handling at all (single English locale) | P1 | **Fixed** |
| BUG-20 | Fonts | Google-Fonts `@import` failed offline → platform silently fell back to system fonts | P1 | **Fixed** |
| BUG-21 | Data layer | Seeded experiment list shipped as fake “saved” research state | P1 | **Fixed** |
| BUG-22 | Validation | Event-agreement “agreement rate” was labelled `kappaNum` (not a κ) | P2 | **Fixed** |
| BUG-23 | Pipeline | Anomaly scores in `series_khuzestan.json` are proxy formulas, not model inference | P0 | **Fixed** |
| BUG-24 | Pipeline | Farm metadata repeats one block for all 490 fields (`name`/`farm`/`municipality` identical) | P1 | **Deferred** |
| BUG-25 | Pipeline | `planted`/`harvest` hard-coded to `2021/03` / `2024/11` for every field | P2 | **Deferred** |
| BUG-26 | Data layer | 7.7 MB JSON inflates the single-file build to ~8.7 MB | P2 | **Won't fix** |
| BUG-27 | Platform | `N`/`DATES` exported but `DATES.length - 1` re-derived at each call site | P2 | **Fixed** |
| BUG-28 | Temporal | “Full period”/year preset buttons wrote ranges without clamping to the axis | P2 | **Fixed** |
| BUG-29 | MapExplorer | “Field boundaries” toggle only unmounted the map; no state was preserved | P2 | **Fixed** |
| BUG-30 | MapExplorer | Date-comparison panels shared one map state and re-created maps on every date change | P2 | **Fixed** |
| BUG-31 | Export pipeline | Exporter converted raw Kelvin LST to °C and shipped it as `temp` with no `lst` channel; LST above 55 °C was not rejected | P0 | **Fixed** |
| BUG-32 | Export pipeline | `EVI = 0.85 × NDVI`, `ETA = 6.5 × NDVI`, `TVDI = 0.9 × CWSI` were emitted as independent channels but are derivations; no `scoreCollinearity` declared | P0 | **Fixed** |
| BUG-33 | Export pipeline | Precipitation was a constant `45 + sin(step/6) × 35` sine wave identical across all 490 fields; temperature had no weather source | P1 | **Fixed** |
| BUG-34 | Export pipeline | NaN / invalid channel values were replaced by `nan_to_num` defaults instead of `null` with `absent` provenance | P0 | **Fixed** |
| BUG-35 | Export pipeline | Unguarded `np.argmin` on the acquisition-date axis could map to any date without a revisit-tolerance or staleness guard | P0 | **Fixed** |
| BUG-36 | Export pipeline | `planted`/`harvest` hard-coded to `2021/03` / `2024/11` for every field although `farms.parquet` has no planting/harvest columns | P2 | **Fixed** |
| BUG-37 | Export pipeline | Neighbour loop stopped after the first four fields within 1.8 km (order-dependent, not ranked by distance); writes were non-atomic | P1 | **Fixed** |
| BUG-38 | Platform data layer | `Obs` channels were all `number` with constant fallbacks (`ndvi 0.45`, `lst 28.5`, …); `Field.planted`/`harvest` were strings with invented defaults | P0 | **Fixed** |
| BUG-39 | Platform data layer | No provenance map per observation, no staleness reason, no `sampleDate`/`acquisitionDate`; legacy payloads indistinguishable from contract v2 | P0 | **Fixed** |
| BUG-40 | Docs / audit | BUG-29 was marked Fixed while MapExplorer still conditionally unmounted MapView | P1 | **Fixed** |
| BUG-41 | Artifact size | `series_khuzestan.json` (7.7 MB) grows the single-file build to ~8.7 MB; accepted for local thesis demo, document regeneration path | P2 | **Won't fix** |

---

## Details

### BUG-01 — Hard-coded 48-step sliders (P0)

`MapExplorer.tsx`, `Temporal.tsx`, `Spectral.tsx`, `Spatial.tsx`, `Validation.tsx`
all used `max={47}` (and `[0, 47]`, `[12, 23]`, `[24, 35]`, `[36, 47]` presets).
The real axis has 48 points today, but the literal silently desynchronises the
moment the exporter changes cadence — and it is exactly the class of bug that
made the sliders disagree with the 490-field dataset.

**Fix:** `mock.ts` now exports `DATES` (derived from `series_khuzestan.json`),
`N`, `LAST_IDX` and `clampIdx()`; every slider, preset, and caption reads those.

### BUG-02 — Hard-coded year windows (P1)

`Validation.tsx` looped `[0,1,2,3].map(y => getPairs(..., [y*12, y*12+11]))` and
labelled rows `2021+y`. Any change in start year or cadence would silently
report “2021…2024” over the wrong windows.

**Fix:** years are derived from `DATES` (`new Set(DATES.map(d => d.slice(0,4)))`)
and each window is looked up from the axis.

### BUG-03 / BUG-13 — Temporal-coverage claims (P0)

The Overview strip said `value="2021–2024"` / `sub="48 monthly obs / field"`, and
the sidebar footer claimed “Landsat & METRIC (2013–2026)”. Both were literals.
The platform renders the 2021-01 → 2024-12 demonstration subset only.

**Fix:** `COVERAGE` (`first`, `last`, `yearStart`, `yearEnd`) and `N` drive the
stat cards, the sidebar, and the footer. The 2013–2026 archive is still the
thesis scope, so the sidebar now says **“(2013–2026 archive)”** and the footer
reports the *rendered* coverage.

### BUG-04 — Stale region + demo banners (P0)

`Overview.tsx` ended with `Region: Piracicaba, SP, Brazil (sugarcane)` (a legacy
placeholder from the synthetic prototype) and a “Demonstration data — not
research results” sentence, while the app banner simultaneously claimed the
Khuzestan dataset was “integrated”.

**Fix:** region is now “Khuzestan, Iran (sugarcane agro-industry)”; the wording
is “Demonstration data — not verified research results”; and a reusable
`<DemoDataBadge/>` marks every view that renders these series (Overview, Map,
Map legend, Validation, Reports). The spec scenario “No stale region labels”
is verified by `grep -r Piracicaba platform/src` returning nothing.

### BUG-05 — Unguarded default selection (P0)

```ts
const [selectedField, setSelectedField] = useState(FIELDS[9].id);          // throws on <10 fields
useState<string[]>([FIELDS[9].id, FIELDS[10].id, FIELDS[18].id]);          // throws on <19 fields
```

**Fix:** defaults are `FIELDS[0]?.id ?? ""` and `FIELDS.slice(0, 3).map(f => f.id)`.
`fieldById()` now returns a placeholder record instead of `undefined`, so
`field.code` in the inspector cannot crash. `hasFields` and
`FIELDS_WITH_SERIES` are exported for data-driven labels.

### BUG-06 — Dead `series_khuzestan.json` (P0)

`scripts/export_platform_data.py` wrote `series_khuzestan.json` (7.7 MB, 490
fields × 48 months) but `mock.ts` generated series with a seeded RNG
(`rng(fidNum * 1013 + 47)`) — so **every number on every page was synthetic**,
even though `farms_khuzestan.json` supplied the real polygons. The two files
could drift forever.

**Fix (documented decision):** `series_khuzestan.json` is now the single data
source. `getSeries()` normalises the exported payload into the typed `Obs` shape;
the RNG generator is deleted. Verified by the spec scenario “No dead data
artifacts”: both JSON files under `platform/src/data/` are imported.

### BUG-07 — MapView recreated on theme toggle (P1)

The mount effect had `[dark]` in its dependency list, so toggling dark mode ran
`map.remove()` and re-created the map at the default center/zoom — losing the
user's position. It also re-registered the tile layer with an outdated closure.

**Fix:** the mount effect is dependency-free (`[]`); a second effect swaps only
the `L.TileLayer` when `dark` changes. Verified visually (zoom level and center
survive the toggle).

### BUG-08 — Unsafe index & undefined observations (P1)

`getSeries(f.id)[Math.max(0, Math.min(47, dateIdx))]` (hard-coded 47) and
`getSeries(nid)[dateIdx]` (no clamp at all, `nid` may not exist) could throw or
produce `undefined` dereferences after any dataset change.

**Fix:** `obsAt()` / `clampIdx()` helpers, optional chaining everywhere, and a
`PLACEHOLDER_FIELD` fallback.

### BUG-09 — Moran's I neighbour index −1 (P1)

```ts
FIELDS.forEach((f, i) => m.set(String(i), f.neighbors.map(n => String(FIELDS.findIndex(x => x.id === n)))));
```

`findIndex` returns `-1` for any neighbour id absent from `FIELDS`; `" -1 "` then
indexes `values[-1]` inside `moransI()` → `undefined` arithmetic → `NaN` Moran's I.

**Fix:** a `Map<fieldId, index>` lookup, filtering unknown neighbours.

### BUG-10 — NaN cells in the field × year table (P1)

`mean([])` returns `0/1 = 0`… but `s.slice(...)` on a short/missing series could
yield `NaN` after `toFixed`, rendering `NaN` chips with an `anomalyColor(NaN)`
fallback. The table also hard-coded `['2021','2022','2023','2024']`, so any
other year range displayed empty columns.

**Fix:** columns come from `stats.years`; cells render `—` when
`Number.isFinite(v)` is false.

### BUG-11 — Blank charts during capture / print (P1)

Recharts' `ResponsiveContainer` measures once on mount and needs a real resize
event afterwards. Capturing with `captureBeyondViewport` (or printing to PDF)
resizes the viewport *after* layout, leaving every chart at Recharts' 14×14 px
minimum — the screenshots for Temporal and Model Comparison came out with empty
plot areas.

**Fix (tooling):** the capture script now resizes the emulated viewport to the
full page height, waits for re-measure, and only then captures. Documented in
`scripts/capture_platform_screenshots.mjs`.

### BUG-12 — Persian typography and bidi digits (P1)

Two distinct problems, both visible in the first Persian screenshots:

1. `tracking-[0.08em]` (stat labels, uppercase headings) breaks the cursive
   joins between Persian letters.
2. In RTL context, `-0.547` renders as `0.547-` because the minus sign is a
   neutral character at the trailing edge of the run.

**Fix:** `body.lang-fa * { letter-spacing: normal !important }` plus an explicit
`unicode-bidi: isolate` rule for `.font-mono`/`<bdi>`/`[dir=ltr]`, and `<bdi>`
wrapping around every numeric interpolation in `Stat`, tables, and score
badges. Charts keep `dir="ltr"` frames so axes never mirror.

### BUG-14 — Divide by zero in completeness (P2)

`100 * (1 - missing / totalObs)` with `totalObs === 0` → `NaN%` in the stat card
and the donut. Now guarded (`totalObs ? … : 0`) and the page short-circuits to
`<EmptyState/>` when the dataset is empty.

### BUG-15 — Recomputation and untranslated labels (P2)

`ModelComparison.tsx` recomputed 490 × models means inside the render body for
the “Field-level consistency” table (≈3 000 `getSeries` calls per keystroke) and
built `pairMatrix` / `indCorr` rows with raw English `m.name`.

**Fix:** both moved into `useMemo` keyed on `compareModels`, and row labels use
`t('model.<id>.name')`.

### BUG-16 / BUG-21 — Experiment registry (P1/P2)

`AnalysisContext` shipped two pre-seeded “experiments” (`exp-1`, `exp-2`) with
fabricated statistics (`r = 0.58 · ρ = 0.54 · n = 72`, `κ = 0.68`) — a reader
would reasonably mistake them for results. The seed also referenced
`FIELDS.slice(0, 12)` at module scope.

**Fix:** the registry starts empty; the empty state explains how to create the
first experiment. Experiment names/notes are localized at save time; CSV export
is unchanged.

### BUG-17 — CSV download revocation race (P2)

`URL.revokeObjectURL(url)` immediately after `a.click()` can cancel the download
in Chromium. Now deferred one tick and the anchor is attached to the DOM.

### BUG-18 — “Mock” language presented as fact (P2)

`MapExplorer` said “Mock stress event: …” and Overview said
“Monthly composite … (mock)”. Now “Test stress event” (translated) and
“demonstration” wording, consistent with the demo badge.

### BUG-19 — `lang` / `dir` never set (P1)

`index.html` hard-coded `lang="en"` with no `dir`; nothing updated it. Screen
readers and hyphenation therefore used English rules for Persian text.

**Fix:** `I18nProvider` writes `lang`, `dir`, `data-locale` and a `lang-fa`
body class on every locale change; `index.html` carries the LTR/EN defaults for
first paint.

### BUG-20 — CDN fonts (P1)

`@import url('https://fonts.googleapis.com/…')` in `index.css` plus a documented
“load Vazirmatn from a CDN” plan. The build is a single-file offline artifact;
on an air-gapped machine the `@import` fails and both Inter and Vazirmatn
silently degrade.

**Fix:** 14 `.woff2` subsets (~336 KB total) are committed under
`src/assets/fonts/` with their OFL licences and declared via `@font-face`.
Persian text is confirmed to render in Vazirmatn by the capture script
(`font=Vazirmatn` assertion).

### BUG-22 — Mislabelled agreement metric (P2)

The event panel computed `(tp+tn)/n` and called it `kappaNum`, printing
“Agreement rate …”. Calling it κ invites a chance-corrected reading it does not
have.

**Fix:** renamed to `agreementRate` and the caption states it is agreement, not κ.
A real Cohen's κ is a follow-up (needs marginal probabilities exposed).

### BUG-23 — Proxy scores presented as model output (P0, Fixed)

`export_platform_data.py` derives anomaly scores from a rule:

```python
stress_sig = max(0.0, val_cwsi - 0.45)
"b1_dsh": clip(0.15 + stress_sig * 0.80, 0.05, 0.95),  # …
```

i.e. all seven “models” are monotone functions of one CWSI proxy. The platform
therefore cannot be used to compare detector behaviour, yet the UI lists
“SSL Masked Transformer”, “STS-Net”, etc. as distinct models.

**Mitigation shipped:** `DATA_PROVENANCE.scoresAreProxy = true`, each per-observation
`Obs.scoreCollinearity` now carries `"cwsi"` so consumers know scores share a single
driver, the demo badge on every page, and the banner text says “literature SSL model
anomaly scores” rather than claiming live inference. **This is the single largest
remaining honesty gap and should be the next change's P0.**

**Resolution (change `integrate-real-model-outputs`, contract v3):** the exporter now
loads the trained checkpoints (`checkpoints/sts_net_490.pt`, `tiny_cnn_mamba_490.pt`,
`time2agri_490.pt`) via `scripts/load_model_checkpoints.py`, rebuilds per-field cycle
tensors `(36 phase bins × 8 channels)` with the exact training pipeline
(`scripts/cycle_inputs.py` reusing `ssl_anomaly.phenology.segment_cycles`), and scores
each observation from the leave-one-time-bin-out reconstruction error of the cycle bin
containing its acquisition date, squashed monotonically to (0, 1) via `1 - exp(-err)`.
Every observation carries `scoreProvenance` (`model` | `proxy` | `absent`) and
`scoreFormulaId` (checkpoint id or `cwsi_affine_v1`), mirrored in
`platform/src/data/channels.ts::SCORES` and surfaced as a provenance badge on the
inspector score card. Fallbacks are honest and per-cause: no artifact for a score key
(b0/b1 baselines, masked_transformer — whose Lightning `.ckpt`s use the main-pipeline
tokenizer, not cycle inputs) → proxy formula labelled `proxy`; artifact fails to load →
`absent` with a null score (never a faked number); no acquisition → `absent`;
`--no-models` forces the all-proxy path for deterministic tests. `DATA_PROVENANCE.
scoresAreProxy` is now derived from the payload instead of hard-coded.

**v5 update (change `train-and-finalize-main-architecture`, contract v5):** the proxy
fallback is fully removed — every score slot resolves `model` or `absent`; the CWSI
formula `cwsi_affine_v1` appears nowhere in the payload. `masked_transformer`/`gru_ae`
score causally from `masked_transformer_main`/`gru_ae_main` (+ JSON sidecars) via
`scripts/load_model_checkpoints.py::LoadedCausalModel` on masked (never-interpolated)
cycle tensors (`scripts/cycle_inputs.py::build_field_cycles_masked`), and the payload
adds `stressFlag`/`stressFlagModel`/`split` per observation and `ladderRung` per field;
without a main checkpoint the flag is `null` everywhere (never fabricated). Current
provenance semantics: `scripts/platform_channels.py::SCORE_REGISTRY`.

### BUG-24 — Farm metadata collapse (P1, Fixed — wire-platform-to-real-data)

All 490 records used to share synthesized labels (`farm = "Khuzestan Unit L08"`,
`municipality = "Amir Kabir / Debal Khazai Agro-Industry (Block L08)"`,
`variety` defaulted to `CP69-1062`, `areaHa` to 25). The exporter now maps the
real `farms.parquet` registry columns verbatim — `farm` ← registry `block`,
`municipality` ← `office · management`, `name` ← `code · office`, real
`variety`/`areaHa` — and empty registry values stay empty (the inspector renders
the not-recorded state "—"). `status` is not shipped (no view renders it).
Contract test `test_farm_metadata_matches_registry` spot-checks 30 codes against
the registry; `test_no_synthesized_farm_strings` asserts zero matches for the
old patterns. Re-exported 2026-11-07: 0 synthesized strings, 87 fields with a
genuinely null variety (registry has no value).

### BUG-25 — Hard-coded planting/harvest dates (P2, Fixed — null with no source)

The exporter no longer invents planting/harvest dates: since contract v3 the
payload carries `null` for both (no registry source column exists — only
`age`, which is empty for all 490 fields), the contract test asserts
`planted is None and harvest is None`, and the inspector renders the
not-recorded state "—" instead of a false date. Ratoon-date attributes remain a
data-collection item, not a UI concern.

### BUG-26 — Bundle size (P2, Won't fix)

`series_khuzestan.json` is 7.7 MB and `farms_khuzestan.json` 278 KB; importing both
grows the single-file Vite build to ~8.7 MB (1.26 MB gzipped). Acceptable for a
locally opened thesis demo; the platform now imports the exported JSON directly
(see BUG-06) so nothing is synthetic. If this ever ships over a network, switch to
fetching `series_khuzestan.json` with a compressed payload (the exporter writes
plain JSON; `contractVersion: 2` lets consumers detect legacy files).

### BUG-31 — LST shipped as air temperature (P0, Fixed)

`export_platform_data.py` computed `lst_cube = indices["lst"] - 273.15` (raw
Kelvin → °C) and emitted it as `temp`, with no `lst` channel at all. Sampled LST
spans 282.76–373.0 K, so subtracting 273.15 yields 9.6–99.8 °C — physically
implausible for air temperature.

**Fix:** `lst` is now emitted as its own channel (null when outside 15–55 °C).
`temp` comes from `weather_aligned.parquet` (`temperature_mean`) or is `null`
with provenance `modelled` when no per-acquisition weather row exists.

### BUG-32 — Derivative channels emitted as independent (P0, Fixed)

EVI was `0.85 × NDVI`, ETA was `6.5 × NDVI`, TVDI was `0.9 × CWSI`. All three
are derivations of other channels but were emitted as if they were independent
observations, and no collinearity was declared.

**Fix:** EVI is now computed from the blue band
`2.5 × (nir − red) / (nir + 6 × red − 7.5 × blue + 1)`. ETA remains an NDVI
proxy and TVDI a CWSI proxy (per `platform_channels.py` registry). Each
observation's `scoreCollinearity` is `"cwsi"` so consumers know scores share a
single driver.

### BUG-33 — Synthetic weather identical across fields (P1, Fixed)

Precipitation was `45 + sin(step/6) × 35` — a sine wave identical for every
field and every month. No ERA5 zarr exists under the repo, so weather data can
never be per-field observed.

**Fix:** `temp` and `precip` read `weather_aligned.parquet`
(`temperature_mean`, `precipitation_sum`) matched by acquisition date, or are
`null` with provenance `modelled` when no row exists for that date.

### BUG-34 — NaN replaced by defaults instead of null (P0, Fixed)

`np.nan_to_num` replaced invalid channel values with constants (`ndvi 0.45`,
`lst 28.5`, `temp 28.5`, …), so the platform displayed fabricated measurements
where data was missing.

**Fix:** invalid / missing channels are `null` with provenance `absent`; the
platform's `Obs` interface types every channel as `number | null` and
`value(obs, channel)` returns `NaN` for null so statistics helpers never
substitute constants.

### BUG-35 — Unguarded date mapping with no staleness (P0, Fixed)

`np.argmin(np.abs(dates - target))` could map any target date to the nearest
archive date regardless of offset (sampled offsets reach 28 days). There was no
revisit tolerance and no staleness marker.

**Fix:** `nearest_acquisition()` requires `|offset| ≤ MAX_OFFSET_DAYS (13.95)`
relative to the 9.3-day revisit; observations outside the window get
`missing: true` plus `stalenessReason`. Acquisitions and sample dates are
emitted as `acquisitionDate` / `sampleDate`.

### BUG-36 — Hard-coded planting/harvest dates (P2, Fixed)

`farms.parquet` has no `planted` / `harvest` columns, yet the exporter wrote
`"2021/03"` / `"2024/11"` for every field.

**Fix:** `planted` / `harvest` are now `null` everywhere. The platform types
them `string | null` and the inspector renders `—` when null.

### BUG-37 — Order-dependent neighbour search + non-atomic writes (P1, Fixed)

The neighbour loop stopped after the first four fields within 1.8 km, so results
depended on field iteration order. Exporter wrote both JSON files directly
(non-atomic), so a crash left a partial payload.

**Fix:** neighbours are ranked by distance and capped at `k=4` within 1.8 km.
Exporter writes to `.tmp` files then `os.replace()` for atomic publication.

### BUG-38 — Obs channels all numbers with constant fallbacks (P0, Fixed)

`Obs` typed every channel as `number`; `normaliseObs()` substituted constants
for missing values. `Field.planted`/`harvest` were strings with invented
defaults (`2021/03` / `2024/11`).

**Fix:** `Obs` channels are `number | null`; `normaliseObs` maps null channels
to provenance `absent`; `Field.planted`/`harvest` are `string | null` mapped
from `f.planted ?? null` / `f.harvest ?? null`. `value(obs, channel)` returns
`NaN` for null/missing.

### BUG-39 — No provenance / staleness on observations (P0, Fixed)

`Obs` had no `provenance`, no `stalenessReason`, no `sampleDate` /
`acquisitionDate`. Legacy payloads were indistinguishable from contract v2.

**Fix:** `Obs` now carries `sampleDate`, `acquisitionDate: string | null`,
`missing`, `stalenessReason: string | null`, `provenance: ObsProvenance | null`,
and `scoreCollinearity: string | null`. `mock.ts` exports `ObsProvenance`
union type and `ProvenanceChip` renders each channel's state. The exporter sets
`contractVersion: 2` on farms and per-channel provenance on observations.

### BUG-40 — Audit table mis-stated BUG-29 (P1, Fixed)

BUG-29 was marked Fixed while MapExplorer still conditionally unmounted MapView.

**Fix:** `MapView.tsx` mount effect now runs once (`[]` deps); tile layer is
swapped without map recreation; field-boundary state survives across all control
changes. Audit table corrected.


### BUG-27 / BUG-29 / BUG-30 — Smaller consistency fixes (P2)

- `LAST_IDX` / `clampIdx` / `monthAt` / `dateAt` centralise index maths (BUG-27).
- The “Field boundaries” toggle now hides the layer without unmounting the map,
  so date/selection state survives (BUG-29).
- The two comparison maps get independent instances (the previous code created
  and destroyed Leaflet maps on every date change, which leaked tiles) (BUG-30).
- `Temporal`'s preset buttons clamp through `setRange()`, so reversed or
  out-of-range values cannot enter the shared context (BUG-28).

---

## Verification performed

| Check | Command | Result |
|---|---|---|
| Type check | `cd platform && npx tsc --noEmit` | 0 errors |
| Production build | `cd platform && npm run build` | ✅ 8.7 MB single file |
| Both dictionaries complete | `satisfies Record<keyof typeof en, string>` in `fa.ts` | compile-time enforced |
| No dead data files | both JSONs imported from `mock.ts` | ✅ |
| No stale region labels | `grep -rn "Piracicaba" platform/src` | no matches |
| No hard-coded 48 | `grep -rn "max={47}" platform/src` | no matches |
| Locale persistence | capture script sets `localStorage` before load | `dir=rtl, lang=fa, font=Vazirmatn` |
| All 8 pages render (fa) | `scripts/capture_platform_screenshots.mjs` | 8 PNGs in `reports/screenshots/fa/` |
| Charts not clipped under RTL | visual review of the 8 screenshots | ✅ |

## Known limitations (explicit non-goals)

- Persian translations cover the UI chrome; **data values** (field codes, farm
  names, model names) intentionally stay Latin.
- Chart x-axes keep ISO `YYYY-MM` in both locales (design decision §5); Persian
  month names appear in prose/tooltips only.
- The Leaflet basemap needs network access for tiles; the app itself does not.
- No automated RTL screenshot diffing in CI yet (the capture script is manual).

## Regenerating the platform data payload

The platform consumes `platform/src/data/farms_khuzestan.json` and `platform/src/data/series_khuzestan.json`, produced by `scripts/export_platform_data.py`. Regenerate after changing the channel registry, contract, or upstream data.

**Prerequisites (Windows, conda `geo`):**
- Source archive: `D:\RS\Thesis\Data\Processed\satellite\stats.zarr` (fields × dates × bands: blue, green, red, nir, swir1, swir2, lst).
- Field geometries/attributes: `D:\RS\Thesis\Data\Processed\farm_gis\farms.parquet` (or the path configured in the exporter).
- Optional ERA5: `D:\RS\Thesis\Data\Processed\weather\era5.zarr` (if present). When absent, `temp`/`precip` are exported as `null` with `provenance: "modelled"`/absent and the staleness guard still applies to satellite channels.

**Command (from repo root `D:\RS\Thesis\thesis_implementation`):**
```powershell
& "D:\Dev\Miniforge3\envs\geo\python.exe" scripts\export_platform_data.py
```

**What to verify after regeneration:**
1. `pytest tests/unit/test_platform_data_contract.py tests/unit/test_platform_bilingual.py -q` passes.
2. The payload has `contractVersion: 2` and per-observation `provenance`/`sampleDate`/`acquisitionDate`/`missing` fields.
3. No channel value violates its `physicalRange` (the exporter raises `ContractViolation` and writes no partial payload).
4. Coverage is logged (samples rejected by the staleness guard vs total).
5. If adding a new model output to the platform, export its scores into the `scores` map with an explicit `provenance`/`artifact` or `formulaId`, and register the channel/model in `scripts/platform_channels.py` + `platform/src/data/channels.ts` before wiring the UI.

## wire-platform-to-real-data (2026-11-07) — tile-server thread race, real-data wiring, copy

### BUG-27 — serve_tiles.py native crash under concurrent browser load (P0, Fixed)

**Finding:** `scripts/serve_tiles.py` handed the same `WarpedVRT`/`WarpedBand`
object to every `ThreadingHTTPServer` thread; the cache lock guarded only the
dict, not the subsequent GDAL `read()`. A real Leaflet pan (a dozen parallel
tile requests) reproducibly killed the process with exit 3221225477
(0xC0000005, native access violation); the same URLs serially returned 200.
Secondary defects on the same routes: error paths answered `<img>` requests
with JSON (`net::ERR_BLOCKED_BY_ORB`), `do_HEAD` was missing (501), no
`Cache-Control`, and a newly mounted raster layer ignored the current opacity
until the slider moved.

**Fix (per-handle locking shipped):** each cached `WarpedBand` owns a
`threading.Lock` held across `read_vrt_window`; cache eviction takes the band
lock before closing (lock order is always cache → band, so no deadlock). Tile
route failures return 404/500 with `Content-Type: image/png` and a transparent
256×256 body; `do_HEAD` mirrors GET on every route; successful tiles carry
`Cache-Control: max-age=3600`; layers mount with the current raster opacity
(`opacity` option) and keep it across scene/layer switches.

**Acceptance gate (recorded):** `scripts/test_tile_concurrency.py` fired
12-thread bursts (18 and 60 requests across dates/layers, exercising LRU
eviction) — all responses valid PNG, process alive, subsequent request 200.
`capture_platform_screenshots.mjs` then drove a headless-browser Leaflet
session: date-slider-driven RGB and NDVI overlays rendered on-map, two live
drag-pans, 28/28 tile responses 200, zero transport failures. The
global-render-lock fallback (design alternative A) was **not** needed.

### Real-data wiring in the same change

- **Weather (BUG-precip/temp-null):** `export_platform_data.py` left-joins
  `Data/Processed/weather/weather_aligned.parquet` on the observation's
  acquisition date (`precip` ← `precipitation_sum`, `temp` ← `temperature_mean`).
  Coverage 21070/21070 dated observations (100%). Unmatched dates stay null and
  are labelled `absent`; a null channel can never render a "Modelled" chip
  (frontend normalizer forces `absent` on null; contract test enforces it).
  The `temp` physical envelope widened to [0, 55] °C — the old (10, 48) range
  rejected real ERA5 daily means (observed 7.3–44.0 °C).
- **Model scores = real generations:** the payload was re-exported **with**
  checkpoint inference — `sts_net_490.pt`, `tiny_cnn_mamba_490.pt`,
  `time2agri_490.pt` scored 799 cycles; 9,639 observation×score cells now carry
  provenance `model` (checkpoint formula ids), baselines stay honestly `proxy`,
  stale samples `absent`. The previous payload had been exported with
  `--no-models`, so the platform was showing proxy values under SSL model names.
- **No fabricated numbers in the frontend:** absent anomaly scores are `null`
  (the old `0.5` fallback polluted Overview means, ModelComparison distributions
  and Moran's I); Spatial's Moran's I and variogram are complete-case; CSV
  exports write empty cells, never `0.0000`, for absent channels.
- **Copy:** "Demonstration data" → "Pipeline output" badge (`DemoDataBadge` →
  `PipelineDataBadge`), banner reworded to dataset-integration wording, footer
  cadence corrected to "Landsat & METRIC · 2013–2026 archive", dead
  `stressEvent` machinery and its i18n strings removed, `data/mock.ts` renamed
  to `data.ts`.
- **Map Explorer UX:** "Hide field boundaries" removes only the polygon layer
  (basemap + raster stay); the field-opacity slider floor is 0 (was 0.2) with
  stroke opacity following the slider; the separate "Landsat raster scene"
  select was removed — the single observation-date slider drives both the field
  series and the raster overlay (raster date = that observation's real
  acquisition date).

**Verification:** `pytest tests/unit/test_platform_data_contract.py` (19 passed)
and `test_platform_bilingual.py` (16 passed); `tsc --noEmit` clean; production
build green; screenshot/console/network gate green for all 8 views with the
server up (evidence: `reports/screenshots/audit/`) and gracefully degraded with
it stopped (`reports/screenshots/audit-serverdown/`). Presentation-focused
findings: `docs/platform_presentation_audit.md`.

---

## Addendum — add-halqeh-anomaly-desk (2026-11-14)

Audit outcome for the ninth view (`AnomalyDesk.tsx` + `SeasonRing` / `SeasonChart` /
`DeskMap`, data `desk_khuzestan.json`): one defect surfaced by the screenshot
gate and fixed before commit.

- **Fixed — unbounded case list on the full replay.** The source Halqeh build
  rendered its 12 hand-picked cases as a plain column; the desk payload replays
  all 799 cases, so the desktop aside stacked ~53 k px of chips and the
  09_anomaly-desk.png gate capture measured a 58,208 px page. The case list is
  now internally scrollable on desktop (`lg:max-h-[38rem] lg:overflow-y-auto`),
  which also cut the gate run under the watchdog.
- **Fixed — bin-date label truncated to month.** `DeskMap` reused `fmtDate`
  (YYYY-MM, designed for the monthly axis) for the scene-vs-bin label; bin dates
  are now shown at full ISO precision because the label exists to expose
  scene-vs-bin day drift.

No other console/page errors across the 9 views (server-up and `--no-tile-server`
runs); the desk degrades to basemap + polygon + explicit "scene absent" copy with
the tile server stopped, reusing the transparent-PNG 404 contract unchanged.
Evidence: `reports/screenshots/audit/` (EN server-up, 9 views + desk scenarios) —
see the run's `audit.json` for per-view tallies.
