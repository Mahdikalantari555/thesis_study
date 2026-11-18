# Tasks

## 1. i18n Foundation

- [x] 1.1 Create `platform/src/i18n/types.ts` defining the `Locale` type (`'en' | 'fa'`) and the `Dictionary` type as `Record<string, string>`, and verify `tsc --noEmit` passes.
- [x] 1.2 Create `platform/src/i18n/en.ts` with a complete flat dictionary of all user-facing strings (nav labels, view titles, panel titles, stat labels, footer, demo banner, map tooltips) and verify it compiles.
- [x] 1.3 Create `platform/src/i18n/fa.ts` with Persian translations for every key in `en.ts`, and add a compile-time check (`satisfies Record<keyof typeof en, string>`) verifying no missing keys.
- [x] 1.4 Create `platform/src/i18n/context.tsx` with `I18nProvider`, `useLocale()`, and `useT()` hooks; restore locale from `localStorage` on mount; persist on change; set `document.documentElement.dir` and `lang` accordingly; verify a test component renders translated text.

## 2. Language Switcher and Topbar

- [x] 2.1 Add an EN/FA toggle button group to the topbar in `App.tsx` wired to `useLocale().setLocale`, and verify clicking switches the active locale.
- [x] 2.2 Wrap the app in `I18nProvider` in `main.tsx` (or `App.tsx`) and verify the provider is available to all views.
- [x] 2.3 Add Vazirmatn font link in `index.html` and apply Persian font stack via a `lang-fa` body class; verify Persian text renders in the browser.

## 3. String Extraction — App Shell and Shared UI

- [x] 3.1 Replace all hardcoded strings in `App.tsx` (NAV labels/descs, sidebar footer, demo banner, topbar) with `t(...)` calls and verify build passes.
- [x] 3.2 Replace all hardcoded strings in `components/ui.tsx` (EmptyState defaults, SigBadge labels) with `t(...)` calls and verify build passes.
- [x] 3.3 Replace hardcoded tooltip text in `components/MapView.tsx` with `t(...)` calls and verify build passes.

## 4. String Extraction — Views (batch 1: Overview, MapExplorer, Temporal)

- [x] 4.1 Extract all user-facing strings in `views/Overview.tsx` into dictionary keys and verify the page renders in both locales.
- [x] 4.2 Extract all user-facing strings in `views/MapExplorer.tsx` into dictionary keys and verify the page renders in both locales.
- [x] 4.3 Extract all user-facing strings in `views/Temporal.tsx` into dictionary keys and verify the page renders in both locales.

## 5. String Extraction — Views (batch 2: Spectral, Validation, ModelComparison)

- [x] 5.1 Extract all user-facing strings in `views/Spectral.tsx` into dictionary keys and verify the page renders in both locales.
- [x] 5.2 Extract all user-facing strings in `views/Validation.tsx` into dictionary keys and verify the page renders in both locales.
- [x] 5.3 Extract all user-facing strings in `views/ModelComparison.tsx` into dictionary keys and verify the page renders in both locales.

## 6. String Extraction — Views (batch 3: Spatial, Reports)

- [x] 6.1 Extract all user-facing strings in `views/Spatial.tsx` into dictionary keys and verify the page renders in both locales.
- [x] 6.2 Extract all user-facing strings in `views/Reports.tsx` into dictionary keys and verify the page renders in both locales.

## 7. RTL Layout and Chart Stability

- [x] 7.1 Audit all Tailwind utility classes in `App.tsx` and views for physical left/right margins (`ml-*`, `mr-*`, `pl-*`, `pr-*`, `left-*`, `right-*`) and convert layout-critical ones to logical properties (`ms-*`, `me-*`, `ps-*`, `pe-*`, `start-*`, `end-*`); verify visual layout under `dir="rtl"`.
- [x] 7.2 Test all 8 Recharts-based views under Persian locale and fix any clipped axes, legends, or tooltips; verify screenshots show no overflow.
- [x] 7.3 Test Leaflet `MapView` under RTL and verify zoom controls and tooltips render correctly.

## 8. Page Bug Audit — P0/P1 Fixes

- [x] 8.1 Fix hardcoded `max={47}` date sliders in `MapExplorer.tsx`, `Temporal.tsx`, `Spectral.tsx`, `Spatial.tsx`, and `Validation.tsx` to use `DATES.length - 1`; verify sliders span the full date range.
- [x] 8.2 Fix "All 48 fields" / "48 monthly obs" labels to be data-driven (`FIELDS.length`, `DATES.length`); verify labels match actual counts.
- [x] 8.3 Remove or replace "Piracicaba, SP, Brazil" and "Demonstration data — not research results" banners: keep an explicit "Demonstration data" badge where synthetic data is used; verify no stale region labels remain.
- [x] 8.4 Fix `MapView` recreation on dark-mode toggle: preserve zoom/center by only swapping the tile layer; verify map position is unchanged after toggle.
- [x] 8.5 Guard `selectedField` default in `AnalysisContext.tsx` against empty `FIELDS` array; verify no runtime error when data is empty.
- [x] 8.6 Resolve the `series_khuzestan.json` disconnection: either import and use it in `mock.ts` or remove the unused export and document the decision in `docs/platform_bug_audit.md`; verify no dead data files remain.

## 9. Bug Report and Screenshot Evidence

- [x] 9.1 Create `docs/platform_bug_audit.md` with a table of every logical bug and disconnection found per page, including severity (P0/P1/P2), description, and fix status; verify the file exists and has at least one entry per audited page.
- [x] 9.2 Create `scripts/capture_platform_screenshots.py` (or a Playwright script) that builds the platform, serves it, switches locale to `fa`, and captures PNGs of all 8 pages into `reports/screenshots/fa/`; verify the script runs without errors (or document manual capture steps if no browser is available).
- [x] 9.3 Generate and commit Persian screenshots for all 8 pages under `reports/screenshots/fa/`; verify files exist.

## 10. Build Verification

- [x] 10.1 Run `node node_modules/vite/bin/vite.js build` (or `bun run build`) in `platform/` and verify it completes with zero errors.
- [x] 10.2 Run `tsc --noEmit` and verify zero type errors across the platform.
