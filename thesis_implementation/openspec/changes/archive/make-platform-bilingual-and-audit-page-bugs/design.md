# Design: Bilingual Platform (EN/FA) and Page-Level Bug Audit

## Context

The platform is a React 19 + Vite 7 + Tailwind 4 SPA with 8 views, a shared `AnalysisContext`, and a mock data layer (`data/mock.ts`) that generates synthetic Khuzestan-like series. `export_platform_data.py` already produces `farms_khuzestan.json` and `series_khuzestan.json`, but only the former is imported. See `proposal.md` for motivation; specs in `specs/` define the behavioral contract.

## Goals / Non-Goals

**Goals:**
- In-house i18n with zero new runtime dependencies.
- Full EN/FA dictionary coverage for every user-facing string.
- RTL layout that mirrors sidebar and text alignment without breaking charts/maps.
- A documented, per-page bug audit with fixes for logical defects and disconnected data paths.

**Non-Goals:**
- Server-side rendering or a backend API.
- Machine translation or automatic string extraction tooling.
- Replacing the synthetic data layer with real Zarr data (out of scope; honesty badges suffice).
- Full Persian localization of chart axis labels beyond month names.

## Decisions

### 1. In-house i18n context over a library (react-i18next)
- **Decision**: Implement a small `I18nProvider` + `useT()` hook with two typed dictionaries.
- **Rationale**: Avoids adding a dependency; the string surface is small (~200 keys); full control over RTL and Persian digits.
- **Alternative**: `react-i18next` — rejected for dependency weight and bundle size on a static thesis demo.

### 2. Dictionary shape: flat dotted keys
- **Decision**: Flat `Record<string, string>` with keys like `"nav.overview"`, `"overview.stat.fields"`.
- **Rationale**: Simplest lookup, easy to diff, no nested typing overhead.
- **Alternative**: Nested objects — rejected as over-engineered for this scope.

### 3. RTL via `dir` attribute + Tailwind logical properties
- **Decision**: Set `dir` on `<html>` from locale; use Tailwind `ms-*`/`me-*`/`ps-*`/`pe-*` logical utilities instead of `ml-*`/`mr-*` where layout must mirror; keep physical utilities only where direction is fixed (e.g., chart margins).
- **Rationale**: Tailwind 4 supports logical properties natively; minimal CSS changes.
- **Alternative**: Separate RTL stylesheet — rejected as maintenance burden.

### 4. Persian font via CDN with system fallback
- **Decision**: Load Vazirmatn from Google Fonts in `index.html` when locale is `fa`; apply `font-family: 'Vazirmatn', system-ui, sans-serif` on body.
- **Rationale**: No build step changes; graceful fallback to system Persian fonts.
- **Alternative**: Self-hosted font files — rejected for repo size.

### 5. Date/number formatting strategy
- **Decision**: Keep ISO dates (`YYYY-MM`) in charts for both locales (unambiguous); translate only prose month names in the dictionary; use `toLocaleString('fa-IR')` only for stat counts when locale is `fa`.
- **Rationale**: Mixed Persian/ISO keeps data readable; avoids breaking Recharts axis parsers.

### 6. Bug audit scope and fixes
- **Decision**: Audit all 8 views + App + ui + MapView + mock data layer; fix P0/P1 bugs (data honesty, hardcoded 48, dead `series_khuzestan.json`, MapView recreation, empty-FIELDS guard); document P2 items in `docs/platform_bug_audit.md`.
- **Rationale**: Balances scope with the planning-only boundary; defers deep refactors.

### 7. Screenshot capture via Playwright (optional)
- **Decision**: Provide a Playwright script that builds the platform, serves it, switches to `fa`, and captures each route; fall back to manual screenshots if Playwright is unavailable.
- **Rationale**: Reproducible PR evidence; optional dependency.

## Risks / Trade-offs

- **[Risk] RTL breaks Recharts layouts** → Mitigation: test each chart under `dir="rtl"`; use physical margins where needed; keep `ResponsiveContainer`.
- **[Risk] Dictionary drift as views evolve** → Mitigation: TypeScript `satisfies` check ensuring `fa` has all `en` keys; CI lint (future).
- **[Risk] Persian font load latency** → Mitigation: `font-display: swap`; system fallback.
- **[Risk] Screenshot capture environment (no browser)** → Mitigation: script is optional; manual screenshots acceptable for PR.
- **[Risk] Large diff, review fatigue** → Mitigation: split commits by capability (i18n layer first, then per-view string extraction, then bug fixes).

## Migration Plan

1. Add i18n layer + dictionaries (no view changes yet).
2. Add language switcher to topbar.
3. Extract strings view-by-view, verifying build after each.
4. Apply RTL CSS and test under `fa`.
5. Fix P0/P1 bugs from audit.
6. Generate screenshots and write `docs/platform_bug_audit.md`.
7. Run `npm run build` (via `node node_modules/vite/bin/vite.js build`) to verify.

## Open Questions

None blocking; screenshot tooling choice (Playwright vs manual) is deferrable.
