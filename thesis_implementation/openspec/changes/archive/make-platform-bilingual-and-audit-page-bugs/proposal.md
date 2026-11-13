# Proposal: Make the AgriAnomaly Platform Bilingual (EN/FA) and Audit Page-Level Bugs

## Why

The web dashboard (`platform/`) is the primary surface for thesis advisors and agronomists, yet every label, tooltip, and narrative string is hard-coded in English, so Persian-speaking stakeholders cannot use it without translation. At the same time, a page-by-page review of the platform surfaced logical defects and disconnected data paths that make the current dashboard misrepresent the Khuzestan dataset (synthetic 2021–2024 series shown as if they were the 2013–2026 real data, exported `series_khuzestan.json` never consumed, hardcoded 48-observation sliders against 490 farms, "Piracicaba/Brazil" and "demonstration data" banners still present, dark-mode map recreation, etc.). Shipping bilingual support without fixing these defects would ship a translated but still misleading product. This change makes the platform genuinely bilingual (English + Persian/Farsi, with RTL, Persian typography, and a language switcher) and, in the same pass, audits every page, fixes the logical bugs and missing connections it finds, and documents them. Persian screenshots of each page are attached to the pull request so reviewers can approve the bilingual rendering before merge.

## What Changes

- **Bilingual platform (new capability)**:
  - Add a lightweight i18n layer (locale state `en`/`fa`, context provider, `t(key)` hook) with no new runtime dependency.
  - Extract all user-facing strings from `App.tsx`, the 8 views, `ui.tsx`, and `MapView.tsx` into two locale dictionaries (`locales/en.ts`, `locales/fa.ts`).
  - Add a language switcher in the topbar and persist the choice in `localStorage`.
  - Apply `dir="rtl"` and Persian font stack when `fa` is active; mirror layout utilities (flex row order, text alignment, sidebar) for RTL.
  - Format numbers/dates per locale (Persian digits in `fa` where appropriate, ISO dates otherwise).
  - Ensure charts, maps, and tables render correctly under RTL (no clipped axes, no mirrored legends).
- **Page bug audit & fixes (new capability)**:
  - Consume the already-exported `series_khuzestan.json` instead of the synthetic `getSeries` RNG, or remove the unused export; resolve which is authoritative and document the decision.
  - Reconcile temporal coverage: platform claims 2013–2026 Khuzestan but renders 2021–2024 / 48 monthly observations; either extend the date axis to real acquisitions or relabel honestly as "demonstration subset".
  - Remove stale "Piracicaba, SP, Brazil" and "Demonstration data — not research results" banners once real data is wired; keep an explicit "demo/synthetic" badge while data is still synthetic.
  - Fix hardcoded 48-step sliders (`max={47}`) and "All 48 fields" labels to be data-driven (490 farms, N acquisitions).
  - Fix `MapView` recreation on dark-mode toggle (preserve zoom/position).
  - Fix `selectedField` default (`FIELDS[9]`) to be guarded against empty data.
  - Report every additional logical bug/disconnection found during the audit in a `docs/platform_bug_audit.md` file.
- **PR evidence**:
  - Add a screenshot capture script (`scripts/capture_platform_screenshots.py` or Playwright) that renders each of the 8 pages in Persian and saves PNGs under `reports/screenshots/fa/`.
  - Reference the screenshot folder in the PR description template.

## Capabilities

### New Capabilities
- `platform-bilingual-i18n`: Bilingual (English/Persian) UI layer with locale state, dictionaries, switcher, RTL support, and Persian typography for the React/Vite platform.
- `platform-page-bug-audit`: Audit of every platform page for logical bugs and missing connections, plus fixes and a written bug report.

### Modified Capabilities
None (no existing specs live under `openspec/specs/`; the prior `visualization-platform` spec remains in its change folder).

## Impact

- `platform/src/`: new `i18n/` module (context, provider, dictionaries), edits to `App.tsx`, all 8 views, `components/ui.tsx`, `components/MapView.tsx`, `context/AnalysisContext.tsx`, `data/mock.ts`.
- `platform/index.html`: lang/dir attributes, Persian font (Vazirmatn or system) via CDN or local.
- `platform/tailwind`/CSS: RTL-aware utilities, `dir` attribute handling.
- `scripts/`: new screenshot capture helper; possible update to `export_platform_data.py` to actually feed `series_khuzestan.json` into the platform.
- `docs/`: new `platform_bug_audit.md`.
- `reports/screenshots/fa/`: 8+ PNG artifacts for PR review.
- Dependencies: none new (i18n implemented in-house); Playwright optional for screenshots.
- No breaking changes to Python pipeline, model training, or evaluation harness.
