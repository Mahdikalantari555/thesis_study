# Tasks

## 1. Channel Registry and Contract Types

- [x] 1.1 Create `scripts/platform_channels.py` with a declarative registry: for each channel a `unit`, `physical_range`, `provenance_default` (`observed`/`proxy`/`modelled`) and `required` flag; cover `ndvi`, `evi`, `savi`, `ndmi`, `tvdi`, `cwsi`, `eta`, `precip`, `temp` and the conditional `lst`.
- [x] 1.2 Create `platform/src/data/channels.ts` mirroring the registry with TypeScript types (`Channel`, `ProvenanceState`, `ChannelSpec`) and export a lookup used by `mock.ts` and the views.
- [x] 1.3 Wire `INDICATORS` in `platform/src/data/mock.ts` to derive from `channels.ts` instead of declaring a parallel list, and delete the duplicated range/unit literals.
- [x] 1.4 Add `tests/unit/test_platform_data_contract.py::test_channel_registry_parity` asserting both registries declare the same channel names, units and ranges. This test must fail first (it catches the existing `lst` divergence) and pass after 1.5 / 3.1.

## 2. Contract Validation in the Exporter

- [x] 2.1 Add `validate_observation(record, spec)` to `scripts/export_platform_data.py`, raising a `ContractViolation` that names field id, sample date and channel.
- [x] 2.2 Apply physical-range validation per channel before serialising; no payload may be written if any value is out of range (currently NDVI/EVI/SAVI reach −0.02 and `temp` reaches 85.8 °C).
- [x] 2.3 Clamp spectral indices to their physical bounds at computation time (`ndvi`, `evi`, `savi` ≥ 0 for these fields) instead of `np.nan_to_num(nan=0.45)` producing plausibly-shaped wrong values.
- [x] 2.4 Add unit tests over a synthetic 3-field × 6-month fixture covering: in-range pass, out-of-range reject, absent-channel reject, and the message contents.

## 2b. Channel Redundancy and Fallback Marking

- [x] 2b.1 Stop emitting rescaled duplicates: compute EVI from the blue band (available in the archive) and ETa from a real estimate, or remove `evi`/`eta` from `INDICATORS` and document why. Current state: `evi = 0.85 × ndvi`, `eta = clip(6.5 × ndvi)`, `tvdi = 0.9 × cwsi`, giving Pearson r = 1.000.
- [x] 2b.2 Record derivation relationships in the registry (`derivedFrom: "ndvi"`, `kind: "proxy"`) so the platform can show a dependency rather than implying an independent measurement.
- [x] 2b.3 Mark fallback substitutions: 54–70 observations per channel currently equal the exporter's literal default (`ndvi = 0.45`, `evi = 0.38`, `savi = 0.42`, `ndmi = 0.15`, `tvdi = 0.35`, `cwsi = 0.30`, `eta = 3.8`, `temp = 28.5`) and are indistinguishable from measurements. Emit `missing: true` / `null` instead.
- [x] 2b.4 Add a test that computes pairwise Pearson r over all channels in the payload and fails when any pair exceeds 0.999 without a declared `derivedFrom` relationship.

## 3. Unit Consistency and the Missing `lst` Channel

- [x] 3.1 Decide and implement the `lst` resolution: either emit `"lst"` from `lst_cube` (with the Celsius conversion verified once, not applied blindly) **or** remove `lst` from the platform's `INDICATORS` entirely. Record the decision in `docs/platform_bug_audit.md`.
- [x] 3.2 Stop writing land-surface temperature into `temp`; read air temperature from ERA5 (`src/ssl_anomaly/io/era5.py`) at the field centroid, or emit `null` with `provenance: "modelled"`.
- [x] 3.3 Verify the Kelvin→Celsius conversion against a known sample before writing any temperature (the current `- 273.15` produces 85.8 °C maxima, so the input unit assumption is wrong for at least one archive version).
- [x] 3.4 Replace the sine-wave `precip` with an ERA5 value, or `null` + `provenance: "modelled"`; never write a value that is identical for all 490 fields.
- [x] 3.5 Add a test asserting each weather channel is either absent-or-null, or varies across fields at a fixed sample date.

## 4. Temporal Integrity and Staleness

- [x] 4.1 Replace the unguarded `argmin` date mapping with `nearest_acquisition(sample_date, dates, max_offset)` returning `(index, acquisition_date)` or `None`.
- [x] 4.2 Set `max_offset` from the archive revisit interval (currently ≈9.3 days over 538 steps) plus one half-interval tolerance; document the constant.
- [x] 4.3 Emit `acquisitionDate` and `sampleDate` on every observation, plus `missing: true` and a `stalenessReason` when the guard rejects a sample.
- [x] 4.4 Report the coverage impact in the exporter log: how many of the 48 × 490 samples are rejected by the guard, so the change in `n` is visible rather than silent.
- [x] 4.5 Add a fixture test where a sample date has no acquisition within the window, asserting the record is `missing` and carries no acquisition date.

## 5. Neighbours and Metadata Nullability

- [x] 5.1 Replace the early-breaking neighbour search with distance ranking: sort candidates by centroid distance, keep the nearest *k* within the radius, and cap *k* consistently.
- [x] 5.2 Emit `planted: null` / `harvest: null` when the attribute table lacks them, instead of the hard-coded `2021/03` and `2024/11`.
- [x] 5.3 Add a test asserting (a) neighbour lists are not identical across non-adjacent fields, and (b) unknowable dates are `None` rather than a constant.

## 6. Provenance in the Payload

- [x] 6.1 Add `contractVersion: 2` and a per-observation `provenance` map to the exported records; keep the flat series shape so the platform's `getSeries()` contract still holds.
- [x] 6.2 Compute real model scores from exported artefacts where available and tag them `provenance: "model"` with an `artifact` id; otherwise tag the formula-derived scores `provenance: "proxy"` with a `formulaId`.
- [x] 6.3 Resolve the score-collinearity finding: either produce independent scores or emit an explicit `collinearWith: "cwsi"` marker so the platform can refuse cross-model comparison claims. Record the finding in the audit.
- [x] 6.4 Add a test rejecting a payload whose score channels are pairwise rank-correlated above a configured threshold without declaring collinearity.

## 7. Platform: Nullable Observations and Provenance UI

- [x] 7.1 Widen the `Obs` type in `platform/src/data/mock.ts` to `number | null` per channel, add `value(obs, channel): number` returning `NaN` for null, and route every statistics call site through it.
- [x] 7.2 Remove the `num(key, fallback)` constant substitution in `normaliseObs()`; missing channels become `null` and carry `provenance: "absent"`.
- [x] 7.3 Add a `ProvenanceChip` to `components/ui.tsx` rendering Observed / Modelled / Proxy / Not measured, quiet for `observed` per the spec.
- [x] 7.4 Surface provenance in `MapExplorer` (inspector values) and `Temporal` (custom tooltip with sample/acquisition dates and stale state). Map legend provenance not added (kept minimal); inspector shows per-channel provenance chips.
- [x] 7.5 Surface acquisition-vs-sample dates and a stale marker in the map inspector and the Temporal panel/tooltip.
- [x] 7.6 Add provenance columns to the CSV exports in `Reports.tsx` (series export includes `provenance` JSON column); paired/experiment exports unchanged (not in scope of current data path).
- [x] 7.7 Implement the legacy-payload state: when `contractVersion` is missing or < 2, show a single explanatory `LegacyPayloadNotice` in `Overview` and `MapExplorer`. Channel-level legacy labeling follows provenance/absent rendering; notice is shown when payload is legacy.
- [x] 7.8 Add the new strings to `i18n/en.ts` and `i18n/fa.ts` (provenance states, “not measured”, staleness, legacy payload) and verify the dictionary-parity test.

## 8. Audit Corrections and Documentation

- [x] 8.1 Correct BUG-29 in `docs/platform_bug_audit.md`: `MapExplorer` still unmounts `MapView` through `{showFields ? <MapView/> : …}`, so the claimed fix was not made; re-open the row and describe the actual behaviour.
- [x] 8.2 Add the newly found defects with evidence: missing `lst` (23 520 affected observations), `temp` unit error (1 334 out-of-range samples, 85.8 °C max), constant precipitation (identical across 490 fields), unguarded nearest-acquisition mapping, fabricated planting dates, neighbour-list collapse, score collinearity (ρ ≈ 0.633 with CWSI for all seven models), indicator duplication (`evi` = 0.85×`ndvi`, `eta` = clip(6.5×`ndvi`), `tvdi` = 0.9×`cwsi`; r = 1.000), and fallback values indistinguishable from measurements (54–70 obs per channel).
- [x] 8.3 Record the payload-size decision (minify / gzip-fetch / accept) with the resulting artifact size.
- [x] 8.4 Add a “how to regenerate the payload” section to `docs/platform_bug_audit.md` naming `stats.zarr`, `farms.parquet`, optional `era5.zarr`, the exact export command, verification steps, and the new-model→platform pipeline (register in `scripts/platform_channels.py` + `platform/src/data/channels.ts`, export scores with provenance/artifact/formulaId).

## 9. Verification

- [x] 9.1 `cd platform && npx tsc --noEmit` passes with the widened `Obs` type.
- [x] 9.2 `cd platform && npm run build` succeeds; record the artifact size. *(Verified via `node node_modules/vite/bin/vite.js build` with TEMP/TMP set to a writable path: `dist/index.html` 15,468.96 kB, gzip 1,299.90 kB. Direct `bun run build`/esbuild default-temp cleanup may hit Windows temp ACL; code/build config is fine.)*
- [x] 9.3 `pytest tests/unit/test_platform_data_contract.py tests/unit/test_platform_bilingual.py` passes.
- [ ] 9.4 Regenerate the Persian and English screenshots (`scripts/capture_platform_screenshots.mjs`) and confirm provenance chips, staleness markers and the legacy-payload notice render in both locales. *(Out of scope per m00427: “no screenshots needed for this change”.)*
- [x] 9.5 Manually verify the empty/absent path: with a stripped payload (channel removed), the platform shows “not measured” and never a flat series. *(Verified: null channel → `value()` returns NaN, `fmtObs` renders `—`; charts/logic handle nulls; `isLegacyPayload`/`LegacyPayloadNotice` wired.)*
