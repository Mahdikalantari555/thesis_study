# platform-anomaly-desk Specification

## Purpose
Defines the platform's anomaly review desk: a view that replays the stage-conditioned
anomaly run (findings doc 14) for human case review, with case data originating solely
from the run's artifacts, honest anomaly-vs-stress framing, device-local review
annotations with export, and per-bin-date raster context.

## Requirements

### Requirement: Desk payload originates from the stage-conditioned run artifacts

The desk payload (`platform/src/data/desk_khuzestan.json`) SHALL be produced only by
`scripts/export_platform_data.py` from `reports/stage_conditioned_anomaly/stage_conditioned_anomaly.parquet`,
`reports/stage_conditioned_anomaly/summary.json`, and the farm registry, and SHALL
contain every case of the run (not a curated subset). Synthesized, hand-picked, or
stale-snapshot data is a defect.

#### Scenario: Complete replay, no curation

- **WHEN** the payload is generated and the parquet is read
- **THEN** the payload contains exactly one case per (field, cycle) pair in the
  parquet (799 for the 2026-11-11 run) and every bin row of the parquet appears in
  exactly one case, in bin order

#### Scenario: Totals recompute from the payload

- **WHEN** the payload totals (rows, flags, flag rate, naive-cut counts, per-stage
  bin counts) are compared against the parquet and `summary.json`
- **THEN** they match (flags 1,774; rows 17,143; flag rate 9.59% for the 2026-11-11
  run), and the naive-cut counts equal the count of bins with `ndvi < 0.40`
  computed from the parquet, not a quoted constant

#### Scenario: Envelopes match the run summary

- **WHEN** the payload's per-stage envelope (median, MAD, lower, upper, n) is compared
  with `summary.json`
- **THEN** values match within the payload's rounding precision

#### Scenario: Case metadata comes from the registry or is empty

- **WHEN** a case's farm code, name, municipality, variety, area, or centroid is
  rendered or exported
- **THEN** each value equals the corresponding farm-registry row for that field id,
  or is null when the registry has no value; no generated strings

#### Scenario: Provenance is embedded

- **WHEN** the payload root is inspected
- **THEN** it records the run's `git_sha`, `generated_at`, `data_source`, `seed`,
  `bin_days`, `envelope_k`, `naive_cut`, and the source file paths, exactly as in
  `summary.json`

### Requirement: Honest anomaly framing

The desk SHALL present flagged bins as stage-conditioned NDVI anomalies under review —
never as confirmed stress — and SHALL keep the run's honesty statements visible:
stages are inferred from within-cycle progress, not recorded planting dates; natural
senescence inside the envelope is not flagged; censored cycles are read as incomplete.

#### Scenario: Verdicts are annotations, not labels

- **WHEN** a reviewer sets a verdict (stress candidate / phenology delay / cloud-gap /
  not a slip) on a case
- **THEN** the UI stores it as a review annotation and the desk copy states that no
  verdict or flag is a confirmed stress label

#### Scenario: Censored cycle is marked

- **WHEN** a case with `censored = true` is displayed
- **THEN** the desk shows the incomplete-cycle notice alongside its scores

#### Scenario: Stage-inference disclosure stays visible

- **WHEN** the desk is opened in either language
- **THEN** the source/lede copy discloses that stages are guessed from progress inside
  the cycle and nothing shown is a confirmed stress label

### Requirement: Device-local review annotations with export

Verdicts and notes SHALL persist locally in the browser (`localStorage`, namespaced,
surviving reloads) and the desk SHALL export the review session as a JSON download
containing case ids, verdicts, notes, export timestamp, and the payload provenance
block. Nothing user-authored is silently invented or lost on export.

#### Scenario: Annotations survive reload

- **WHEN** verdicts or notes are set and the page is reloaded
- **THEN** the desk restores them for the same case ids from localStorage

#### Scenario: Export is complete and honest

- **WHEN** the export button is used
- **THEN** the downloaded JSON contains every non-empty verdict/note keyed by case id,
  the export timestamp, and the payload provenance block, and contains no fields the
  user did not author (no fabricated review state)

### Requirement: Raster context for the reviewed case

The desk SHALL render the selected case's field on a Leaflet map with the field
polygon from the farms payload, and SHALL offer an NDVI/RGB raster overlay for the
selected bin's date resolved to the nearest available scene date from the tile
server's `/scenes` index, degrading gracefully when the tile server is absent.

#### Scenario: Raster overlay follows the selected bin

- **WHEN** a bin is selected in a case and a scene exists within the configured
  nearest-date window of that bin's date
- **THEN** the desk map overlays that scene's NDVI (or RGB) tiles for the field's
  extent and labels the actual scene date used, which may differ from the bin date

#### Scenario: No scene means absent, not blank-stretch

- **WHEN** no scene is available for the selected bin's date window, or the tile
  server is not running
- **THEN** the raster control shows an explicit "scene absent" state and the map
  still renders basemap + field polygon; no broken tiles or console errors

#### Scenario: Tile-server-off degradation is clean

- **WHEN** the desk is exercised with the tile server stopped
- **THEN** the view renders fully except the raster layer, with zero console errors
  and zero page errors

### Requirement: Desk is bilingual and gated

The desk SHALL render in EN and FA using the platform i18n dictionaries and Persian
digit formatting, and SHALL pass the platform verification gates: payload contract
tests, `tsc --noEmit`, production build, and screenshot capture with zero console and
page errors (tile server on and off).

#### Scenario: Persian rendering

- **WHEN** the platform locale is FA
- **THEN** all desk strings, numerals (Persian digits), and reading direction follow
  the platform's established bilingual behaviour

#### Scenario: Gates hold

- **WHEN** the verification gates run on this branch
- **THEN** the desk contract tests pass, typecheck and build succeed, and the
  screenshot audit reports zero console/page errors across all views including the desk
