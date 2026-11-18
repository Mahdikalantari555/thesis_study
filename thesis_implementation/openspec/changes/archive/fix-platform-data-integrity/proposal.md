# Proposal: Fix Platform Data-Integrity and Provenance Defects

## Why

The previous change (`make-platform-bilingual-and-audit-page-bugs`) made the dashboard
bilingual and fixed the page-level defects it could reach, but it explicitly **deferred the
bugs whose root cause lives in the exporter and the data contract** (`docs/platform_bug_audit.md`
→ BUG-23, BUG-24, BUG-25). It also shipped one P2 row (BUG-29) whose claimed fix was never
implemented.

Re-verifying the shipped payload against the exporter source surfaced **seven defects not yet
recorded in the audit**, three of them as severe as BUG-23. The dashboard currently renders
numbers that are absent, out of physical range, or attributed to a month whose acquisition
does not exist:

| Symptom visible in the UI | Verified cause |
|---|---|
| The “LST” indicator is selectable and renders a perfectly flat line | `scripts/export_platform_data.py` never writes an `lst` key; `normaliseObs()` in `mock.ts` silently substitutes the constant `28.5`, so every one of the 23 520 observations is `28.5 °C` |
| “Air Temp.” shows 85.8 °C and 1 334 of 23 520 samples exceed the declared 10–48 °C range | The exporter writes the *land-surface* temperature into `temp` (`"temp": val_lst`), and `lst_cube = indices["lst"] - 273.15` is applied to a value that is already Celsius in some archive versions — a unit error of 273.15 |
| Precipitation is identical for all 490 fields | `"precip": 45.0 + sin(step_i / 6.0) * 35.0` is a function of the step index only; no field, no date, no ERA5 |
| The seven “model” scores rank-correlate ρ ≈ 0.633 with CWSI and with each other | BUG-23, now quantified: all seven are `clip(offset + max(0, cwsi − 0.45) * weight)`, i.e. one signal with seven weights |
| Two NDVI/EVI/SAVI observations are negative (min −0.02) | The exporter applies `np.nan_to_num(..., nan=0.45)` but no physical clamp; Sentinel/Landsat indices cannot be negative for vegetated fields |
| The Validation view's 9×9 indicator correlation matrix looks like two clusters because it *is* only two clusters | Three of the nine channels are rescalings of another channel: `evi = 0.85 × ndvi`, `eta = clip(6.5 × ndvi)`, `tvdi = 0.9 × cwsi`. Pearson r = 1.000 for NDVI/EVI/ETa and 1.000 for TVDI/CWSI over all 23 466 non-missing observations, so “correlate indicator *i* with indicator *j*” is arithmetic on one number wearing nine hats |
| Each “monthly” sample may come from an acquisition years away | `date_indices` uses `argmin(|dates − sample_date|)` with **no maximum-staleness guard**, so a 2021-01 label can be sourced from a 2013 or 2025 acquisition |
| Every field shares `planted = 2021/03` and `harvest = 2024/11` | BUG-25, still open; the exporter hard-codes both |
| “Neighbours” are the four fields that happen to come first in record order within 1.8 km, not the nearest four | BUG-24: the neighbour loop breaks after four appends inside the radius, so 174 of 490 fields share a neighbour list with at least one other field (one list repeats 9×) and the adjacency graph encodes export order |

Shipping this to an advisor would present absent and physically impossible values as
measured data. The bug audit produced a written record but the platform still *displays* the
artefacts, and the demo badge cannot carry that weight on its own.

## What Changes

- **Exporter correctness (`scripts/export_platform_data.py`)** — the single root cause for
  most findings:
  - Emit `lst` (or stop advertising it) and stop using land-surface temperature as `temp`;
    keep units Celsius end-to-end and validate the Kelvin→Celsius conversion.
  - Clamp every spectral index to its physical range instead of defaulting NaN to a
    plausible-looking constant.
  - Stop emitting rescaled duplicates as independent indicators. EVI is currently
    `0.85 × NDVI` and ETa is `clip(6.5 × NDVI)`, so the nine indicators carry four independent
    signals. Either compute EVI from the blue band (available in the archive) and ETa from a
    real energy-balance estimate, or remove them and state why.
  - Mark fallback-substituted observations. 54–70 observations per channel equal the exporter's
    constant (`ndvi = 0.45`, `temp = 28.5`, …) and are indistinguishable from measurements in
    the payload; they must carry the `missing`/`null` flag.
  - Add a **maximum-staleness guard** to the nearest-acquisition mapping: reject a sample
    whose nearest acquisition is further than one revisit interval, mark it `missing`, and
    record the true acquisition date so the UI can show it.
  - Replace the synthetic precipitation/temperature series with ERA5 values
    (`src/ssl_anomaly/io/era5.py`) or, when ERA5 is unavailable, mark the fields as
    `modelled` instead of presenting them as observations.
  - Rank neighbours by centroid distance and keep the nearest *k* within the radius, so the
    adjacency graph reflects geography rather than export record order.
  - Stop fabricating `planted`/`harvest`; emit `null` and let the UI say “unknown”.
- **Anomaly-score provenance (`scripts/export_platform_data.py` + platform)** — BUG-23:
  - Write scores from real checkpoint inference when the exported model artefacts exist,
    and
  - otherwise emit an explicit per-score provenance flag
    (`"provenance": "proxy" | "model"`) plus the formula id, so the platform can label each
    score instead of relying on a global badge.
- **Platform data contract (`platform/src/data/mock.ts`, `types`, views)**:
  - Introduce a typed `IndicatorProvenance` (`observed` | `modelled` | `proxy` | `absent`)
    per indicator per field-month, carried into the inspector, the legend and the CSV
    exports.
  - Surface `acquisitionDate` vs `sampleDate` in the map tooltip and the Temporal hover, and
    render a staleness warning when they differ by more than one revisit.
  - Replace the silent `num(key, fallback)` constant substitution with an explicit
    `null` + “not measured” rendering so a missing channel can never masquerade as a flat
    series.
  - Remove the LST/“Air Temp.” indicator definitions if the exporter still cannot supply
    them, rather than offering a control that produces a constant line.
- **Audit honesty (`docs/platform_bug_audit.md`)**:
  - Correct BUG-29, whose “Fixed” status is wrong (`MapExplorer` still unmounts `MapView`
    via `{showFields ? <MapView/> : …}`).
  - Add the newly found defects with the same severity rubric and the evidence used here.
- **Regression gates**:
  - Extend `tests/unit/test_platform_bilingual.py` (or add `test_platform_data_contract.py`)
    to assert the contract: no indicator outside its declared range, `lst` either present or
    absent from `INDICATORS`, precipitation varies across fields, no score pair with
    ρ > 0.99, and every non-missing sample carries an acquisition date within the staleness
    limit.
- **Payload size** — record the decision on the 7.7 MB JSON (BUG-26): pretty-printed? gzip?
  fetch-on-demand? Either way the plan must state it, because the contract changes above
  will grow the payload.

## Capabilities

### New Capabilities

- `platform-data-contract`: A validated contract between the exporter and the platform —
  per-indicator ranges, units, provenance, acquisition-vs-sample dates, and the guarantees
  the UI may rely on. Includes the exporter-side validation that enforces it.
- `platform-data-provenance`: Per-indicator and per-score provenance surfaced throughout the
  UI (inspector, legend, tooltips, CSV exports) so an advisor can tell measured from
  modelled from proxy at a glance.

### Modified Capabilities

- `platform-page-bug-audit`: Extends the audited surface from the eight views to the
  exporter and the JSON payload, and requires that a defect be marked “Fixed” only when the
  shipped artifact has been re-verified against the code path.

## Impact

- `scripts/export_platform_data.py` — substantial rewrite of the record-building loop
  (units, clamps, staleness, neighbours, provenance, no fabricated planting dates).
- `platform/src/data/mock.ts` — typed provenance, `null`-safe accessors, no silent fallback.
- `platform/src/views/*` — MapExplorer, Temporal, Validation, Spatial, Overview consume
  provenance and staleness; `components/ui.tsx` gains a provenance chip.
- `platform/src/i18n/en.ts`, `fa.ts` — new keys for provenance, staleness, “not measured”,
  correct BUG-29 copy.
- `platform/src/data/*.json` — regenerated payload (shape gains `provenance` and
  `acquisitionDate`).
- `docs/platform_bug_audit.md` — corrected statuses plus new findings.
- `tests/unit/` — data-contract tests.
- **Dependency / data requirement:** regenerating the payload needs
  `Data/Processed/satellite/stats.zarr` and, for the weather channels, `era5.zarr`. Neither is
  in this checkout. The exporter changes therefore land with unit tests over a synthetic
  fixture, and the committed JSON in this repo remains the old one until a maintainer with
  the archive runs the regeneration; the platform must degrade gracefully in that window
  (`absent` provenance, explicit “payload predates contract v2” state) rather than crash.
- No changes to model training, the evaluation harness, or the Rust backend.

## Out of Scope

- Retraining or re-evaluating the SSL models; this change only makes the *display* honest
  about what those scores are.
- Real per-field planting/harvest dates (needs the ratoon attribute table): the change emits
  `null` and shows “unknown”, it does not invent values.
- Restoring the full 2013–2026 archive in the platform (still a 2021–2024 subset).
- Wiring complete inference-service infrastructure; scoring from exported checkpoints is the
  minimum viable path and may itself be split out if `export_model.py` proves insufficient.
