# Design: Platform Data Integrity and Provenance

## Context

`platform/src/data/series_khuzestan.json` is the platform's only data source: 490 fields ×
48 monthly samples produced by `scripts/export_platform_data.py`. Every view reads it through
`getSeries()` in `platform/src/data/mock.ts`.

The previous change replaced the synthetic RNG layer with this payload and added a global
“Demonstration data” badge. That was the right first step but it treated provenance as
*global* (whole platform) when the real defect is *per channel*: in a single response the
payload mixes genuinely observed indices (NDVI, NDMI, SAVI), derived proxies (TVDI, ETa,
CWSI), fabricated weather (precip, temp), a missing channel (lst), and seven scores that are
all one proxy signal. A global badge cannot express that, and `normaliseObs()` currently
converts absence into a plausible constant.

Reference: `docs/platform_bug_audit.md` (BUG-23…BUG-26), plus the seven defects added by this
change.

## Goals / Non-Goals

**Goals**

- One contract, expressed in types and enforced by tests, covering units, ranges, provenance
  and temporality for every payload channel.
- The exporter cannot emit a value that violates the contract without failing loudly.
- The platform cannot display a missing channel as a measured constant.
- An advisor can tell, for any number on screen, whether it was measured, derived, or
  modelled — and from which acquisition date.
- Correct the audit row that claims a fix that was not made (BUG-29).

**Non-Goals**

- Fixing the models, retraining, or improving detector quality.
- Inventing the data the archive does not have (planting dates, per-field weather).
- Serving the full 2013–2026 archive.
- A backend API; the artifact stays static JSON.

## Decisions

### 1. Explicit registry of channels with a declared contract

**Decision.** Move the channel metadata out of the platform into a single declarative table
that both sides consume conceptually: for each channel, `unit`, `physicalRange`,
`provenance`, `required`. The exporter validates against it; the platform types are generated
from the same list (hand-maintained mirror, checked by a test).

**Rationale.** The current defect class exists because `INDICATORS` in `mock.ts` and the
`farm_obs.append({...})` dict in the exporter are two independent lists that drifted: the
platform advertises `lst`, the exporter never writes it. A single source with a parity test
kills the whole class rather than one instance.

**Alternative.** Pydantic models shared via JSON Schema generation — rejected: adds a
dependency and a build step for a five-field table, and the TS side would need codegen.

### 2. `null` instead of plausible fallbacks; provenance instead of a global badge

**Decision.** `normaliseObs()` stops substituting constants. A channel that is absent from a
payload becomes `null`, and each observation carries
`provenance: { <channel>: "observed" | "modelled" | "proxy" | "absent" }`. The `Obs` type
becomes `number | null` per channel; every view already has a “—/not measured” path from the
previous change, so this is mostly deleting fallbacks and wiring the chip.

**Rationale.** A flat line at 28.5 °C is indistinguishable from real data at a glance; a gap
labelled “not measured” is not. Provenance-as-data (not as a prop) also makes the CSV exports
honest without extra plumbing.

**Risk.** `Obs` field types widen to `number | null`, touching every arithmetic site.
*Mitigation:* a small `value(obs, channel)` helper returning `NaN` for null keeps the
statistics code (`pearson`, `laggedCorr`, `linReg`) unchanged, since they already treat `NaN`
as “skip”. Views are audited one by one with `tsc --noEmit` as the gate.

**Alternative.** Keep numbers and add a separate `invalid` set — rejected: two parallel
representations are exactly how the current inconsistency arose.

### 3. Staleness guard on the date mapping

**Decision.** For each monthly sample, find the nearest acquisition; if
`|acquisition − sample| > revisit + tolerance` (revisit from the archive cadence, tolerance
one half-revisit), mark the sample `missing` and record `acquisitionDate: null` with a
`stalenessReason`. Otherwise record the true `acquisitionDate`. The platform displays both
dates in tooltips and flags any sample where they differ by more than one revisit.

**Rationale.** An unguarded `argmin` yields a confident-looking month label over an
acquisition that may be years away — the most misleading failure mode in the payload because
nothing in the output looks wrong.

**Alternative.** Drop the monthly resampling and display raw acquisition dates — rejected for
now: it breaks the 48-step shared axis that the whole UI depends on (the previous change just
made that axis dynamic; changing its semantics again is a separate step). The guard preserves
the axis while making the deviation visible.

### 4. Weather from ERA5, or explicitly `modelled`

**Decision.** `precip`/`temp` are read from `era5.zarr` (loader already exists:
`src/ssl_anomaly/io/era5.py`) at the field centroid and the sample month. When the store is
unavailable, the exporter writes `provenance: "modelled"` and refuses to emit
`synthetic-sine` values as observations.

**Rationale.** The current precipitation is a sine wave of the step index, identical for all
490 fields — it carries zero information yet drives the “wet/dry season” filter in the
Spectral view and the `r`-vs-indicator table in Model Comparison.

**Alternative.** Drop the weather channels — rejected: the seasonal split is a legitimate
part of the analysis; labelling is enough to keep it honest when ERA5 is missing.

### 5. Model scores: real inference when available, `proxy` otherwise

**Decision.** The exporter attempts to load exported model artefacts and compute scores; on
success each score is `provenance: "model"` with a `artifact` id. On failure it emits the
current formula-derived scores but tags them `provenance: "proxy"` and includes the formula
id. The platform renders a per-model chip (Observed / Proxy) next to the model name and
disables “Model Comparison” claims that require independent detectors when all selected
models are proxies.

**Rationale.** BUG-23 is the single largest honesty gap. Full inference infrastructure is out
of scope, but the *distinction* is expressible today, and `export_model.py` already produces a
SafeTensors release that can be loaded for a batch pass.

**Risk.** `export_model.py` defaults `d_in = 12` for synthetic data and writes placeholder
norm stats — it may not produce a runnable artefact for the real archive.
*Mitigation:* the artefact-loading path is attempted behind a feature check that logs and
falls back to `proxy`; the contract change lands either way, so the platform fix is not
blocked on the model work.

### 6. Neighbours and planting dates: emit `null`, do not invent

**Decision.** Neighbour selection ranks all fields by centroid distance and keeps the nearest
*k* within the radius; `planted`/`harvest` are emitted as `null` when the attribute table does
not provide them. The UI already has “—” rendering for unknown metadata.

**Rationale.** The neighbour loop currently appends the first four fields found within 1.8 km
and breaks, so selection depends on record order: 174 of 490 fields share their neighbour list
with at least one other field (one list repeats 9×). The result is defensible-looking but not
a nearest-neighbour graph. Planting/harvest dates are worse — a single constant for all 490
fields reads as authoritative metadata. Absence is the truthful representation of data the
archive does not contain.

### 7. Independent indicators, declared derivations

**Decision.** The registry records `derivedFrom` and `kind` (`measured` | `derived` |
`proxy`) per channel. Channels that are an affine transform of another channel either get a
real computation (EVI from the blue band, which is already in the cube; ETa from an
energy-balance estimate) or are withdrawn from `INDICATORS`.

**Rationale.** `evi = 0.85 × ndvi` and `eta = clip(6.5 × ndvi)` make the Validation view's
correlation matrix an identity check: r = 1.000 for three pairs over all 23 466 non-missing
observations, and the remaining six indicators yield only two independent clusters. Any
scientific claim built on “nine indicators agree” is circular. This is the same failure mode as
BUG-23 (seven models = one signal) and deserves the same treatment: compute it properly or
label it, but never present redundancy as corroboration.

**Alternative.** Keep them as documented proxies without recomputation — acceptable only if
the UI suppresses cross-indicator correlation claims for declared proxies, which is more work
than computing EVI correctly.

### 8. Contract validation runs twice

**Decision.** The exporter validates before writing (fail the run), and a unit test validates
the committed payload (fail CI). The test is skippable with an explicit env flag when the
committed payload is known to predate the contract, and the platform shows that state in the
UI.

**Rationale.** The exporter cannot be executed in this environment (no `stats.zarr`), so the
test is the only enforcement that actually runs here. Making the skip explicit prevents the
“green because untested” failure the audit already produced once.

## Risks / Trade-offs

- **[Risk] The committed payload will not satisfy the new contract until someone with the
  archive re-runs the exporter.** → Mitigation: the platform detects `contractVersion != 2`
  and labels the affected channels `absent`/`legacy` instead of pretending; the contract test
  is skipped with a loud reason, and the PR states the regeneration command.
- **[Risk] Widening `Obs` to nullable propagates through all eight views.** → Mitigation:
  `value()` helper keeps statistics code unchanged; `tsc --noEmit` plus the existing pytest
  guards are the gate; the work is split into per-view commits.
- **[Risk] Provenance chips add visual noise to an already dense UI.** → Mitigation: chips
  appear only where provenance differs from `observed` (the normal case stays quiet), plus a
  legend line explaining the four states.
- **[Risk] Staleness guard turns many samples into `missing`, shrinking n.** → Mitigation:
  report the resulting coverage in the Overview strip (“n valid / n stale”), and treat that as
  a finding rather than a regression — it is the number the advisor needs.
- **[Risk] Payload grows further (provenance + acquisition dates) on top of 7.7 MB.** →
  Mitigation: decision required in tasks: either minify (≈1.5 MB saving for free), or gzip-
  fetch, or keep single-file and accept ~10 MB. Recorded as an explicit task, not a silent
  regression.

## Migration Plan

1. Define the channel registry + TS mirror; add the parity test (no behaviour change).
2. Exporter: units, clamps, `null`s, neighbour ranking, provenance fields, staleness guard.
3. Platform: nullable `Obs`, `value()` helper, provenance chip, staleness display.
4. Views: remove the constant-fallback paths; wire provenance into inspector/legend/CSV.
5. Correct `docs/platform_bug_audit.md` (BUG-29 status + new findings).
6. Decide and implement the payload-size option.
7. Regenerate the payload where the archive is available; until then the UI runs in
   `legacy payload` mode.
8. `npx tsc --noEmit`, `npm run build`, `pytest tests/unit/test_platform_data_contract.py`,
   screenshots (fa + en) to confirm no regression.

## Open Questions

- Should the platform ship the `legacy payload` mode at all, or must the PR block until the
  payload is regenerated? (Proposal assumes shipping, with the state made explicit.)
- Is `export_model.py` able to produce artefacts for the real archive, or does scoring need a
  separate change? Affects only the `model` branch of decision 5.
- Payload-size option: minify / gzip-fetch / accept growth.
