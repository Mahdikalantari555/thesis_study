# platform-real-data Specification

## Purpose
Guarantees that every value the platform displays originates from a real artifact under `Data/Processed/` (band statistics, weather records, farm registry, geometry) or is explicitly absent, with provenance labels that never overstate what is real.

## Requirements

### Requirement: Payload values originate from real data artifacts

The platform data payload SHALL contain channel values only from real sources — band statistics from `stats.zarr`, weather from `weather_aligned.parquet` joined on acquisition date, farm attributes from `farms.parquet`, geometry from `farms.geojson` — and SHALL NOT contain synthesized, placeholder, or demo-only values.

#### Scenario: Weather channels carry real records

- **WHEN** an observation date exists in `weather_aligned.parquet`
- **THEN** the `precip`/`temp` channels for that observation carry the real weather values from the file, not null

#### Scenario: No weather record means absent, not invented

- **WHEN** an observation date has no matching weather row
- **THEN** the weather channel stays `null` and its provenance is `absent`

#### Scenario: No synthesized strings in the payload

- **WHEN** the farms payload is scanned for previously synthesized patterns (e.g. `Khuzestan Unit`, `Amir Kabir / Debal Khazai`)
- **THEN** zero matches are found; farm/block/office text comes from `farms.parquet` columns

### Requirement: Real farm metadata

The farms payload SHALL populate farm descriptive fields from the real `farms.parquet` registry columns (farm code, block, office, management, status, variety, area) and SHALL leave a field empty when the registry has no value for it.

#### Scenario: Inspector shows registry attributes

- **WHEN** a field is inspected on the map
- **THEN** the displayed farm/block/office information matches the corresponding `farms.parquet` row for that field code

#### Scenario: Missing registry value renders empty

- **WHEN** a registry column is null for a field
- **THEN** the corresponding platform field is empty (or a labelled "not recorded" state) rather than a generated value

### Requirement: Honest provenance for every displayed channel

The frontend SHALL label every channel and score chip according to payload provenance, and a `null` value SHALL never be labelled `modelled` or `measured`.

#### Scenario: Null channel is labelled absent

- **WHEN** a channel value is `null` in the payload
- **THEN** the UI shows the absent/not-measured state, not a "Modelled" chip

#### Scenario: Provenance labels track the payload

- **WHEN** the payload marks a score `model`, `proxy`, or `absent`
- **THEN** the UI chip shows the same label

### Requirement: No demo or placeholder content in the production UI

The built platform SHALL NOT display demonstration/disclaimer copy that misrepresents real data as demo data, SHALL NOT include dead mock-event machinery, and SHALL state the true data source (Landsat/METRIC 2013–2026) wherever acquisition provenance is shown.

#### Scenario: Data panels describe pipeline output honestly

- **WHEN** any data panel is rendered
- **THEN** its caption/badge describes the payload as pipeline output over the real archive, not "demonstration data"

#### Scenario: No dead mock-event strings ship

- **WHEN** the production bundle is searched for mock-stress-event strings
- **THEN** none are present and no view references them
