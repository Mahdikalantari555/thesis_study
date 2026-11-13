# Spec Delta: platform-data-contract

## Purpose

Defines the contract between `scripts/export_platform_data.py` and the platform: which
channels exist, their units, their physical ranges, their provenance, and the temporal
integrity of each sample. The exporter validates output against this contract before writing;
the platform declares the same contract in types and is tested for parity. Together they make
it impossible for one side to advertise a channel the other does not provide, or to present
an out-of-range or stale value as a measurement.

## ADDED Requirements

### Requirement: Single channel registry

The exporter and the platform SHALL derive their channel list from one registry declaring,
for each channel, a unit, a physical range, and whether it is required.

#### Scenario: No advertised channel without a producer
- **WHEN** the platform advertises an indicator
- **THEN** the exporter emits that channel in every observation record, or the platform does
  not advertise it at all

#### Scenario: Parity is enforced by a test
- **WHEN** the channel registries on the two sides diverge
- **THEN** the data-contract test fails, naming the channel and the side that added it

### Requirement: Physical range enforcement

Every spectral, thermal and weather value SHALL fall inside its declared physical range, or
be explicitly `null`.

#### Scenario: Out-of-range index is rejected
- **WHEN** an exported NDVI, EVI or SAVI value is negative, or any value exceeds its declared
  maximum
- **THEN** the exporter fails the run and reports the field, date and channel

#### Scenario: Impossible temperature cannot ship
- **WHEN** an air-temperature value exceeds the declared maximum (48 °C for this region)
- **THEN** the value is rejected rather than written, because no sample may exceed the
  physical envelope of the site

### Requirement: Absence is represented as null, never as a constant

A channel with no data for a field-month SHALL be `null` and SHALL NOT be replaced by a
default value.

#### Scenario: Missing channel renders as not measured
- **WHEN** a payload omits a channel the platform expects
- **THEN** the platform renders “not measured” for that channel and never a flat series

#### Scenario: No silent constant substitution
- **WHEN** the platform normalises an observation record
- **THEN** it preserves absence as `null` rather than substituting a numeric default

### Requirement: Temporal integrity of each sample

Each observation SHALL carry both the sample date and the acquisition date it was derived
from, and a sample whose nearest acquisition is further away than one revisit interval SHALL
be marked `missing`.

#### Scenario: Stale acquisition is flagged, not relabelled
- **WHEN** a monthly sample's nearest acquisition is more than one revisit interval away
- **THEN** the sample is `missing`, `acquisitionDate` is `null`, and a staleness reason is
  recorded

#### Scenario: Acquisition date is available to the UI
- **WHEN** a sample is valid
- **THEN** its true acquisition date is present in the payload and displayed alongside the
  sample date in field-level tooltips

### Requirement: Weather channels carry real values or are labelled modelled

Precipitation and air temperature SHALL be derived from the ERA5 store at the field centroid,
or be absent and labelled `modelled`.

#### Scenario: No fabricated weather
- **WHEN** the ERA5 store is unavailable
- **THEN** the exporter does not write synthetic weather values as observations, and marks
  the channels `modelled`

#### Scenario: Weather varies across fields
- **WHEN** weather channels are present with provenance `observed`
- **THEN** their values are not identical for every field at a given sample date

### Requirement: Neighbour adjacency is field-specific

The neighbour list SHALL be derived by ranking candidate fields by centroid distance.

#### Scenario: Nearest neighbours, not first matches
- **WHEN** the exporter builds the adjacency list for a field
- **THEN** it selects the nearest fields within the radius, and the selection does not depend
  on the order in which fields appear in the source archive

### Requirement: Unknown metadata is null

Attributes that the source archive does not supply SHALL be `null`, not a plausible constant.

#### Scenario: Planting and harvest dates
- **WHEN** the attribute table has no planting or harvest date for a field
- **THEN** the payload carries `null` for that attribute and the platform displays an unknown
  marker

### Requirement: Channels must carry independent information

A channel SHALL NOT be an exact or near-exact rescaling of another channel, and any channel
that is a documented proxy for another SHALL declare that relationship.

#### Scenario: No rescaled duplicates
- **WHEN** two channels are related by a constant factor or an affine transform over all valid
  observations
- **THEN** the exporter does not present both as independent indicators

#### Scenario: Proxy relationship declared
- **WHEN** a channel is a documented proxy for another (for example ETa from NDVI)
- **THEN** the registry records which channel it derives from, and the platform displays the
  dependency instead of implying an independent measurement

### Requirement: Fallback substitutions are marked

A value that the exporter substitutes for unavailable data SHALL be distinguishable from a
measured value in the payload.

#### Scenario: Substituted value is not indistinguishable from data
- **WHEN** the exporter writes a default because the underlying observation is unavailable
- **THEN** the observation is marked `missing`/`null` with the fallback recorded, and is never
  emitted as an ordinary numeric value

### Requirement: Contract version and graceful degradation

The payload SHALL declare a contract version, and the platform SHALL detect a payload that
predates the current contract.

#### Scenario: Legacy payload is labelled
- **WHEN** the bundled payload declares an older contract version
- **THEN** the platform labels the affected channels as legacy/absent and states that the
  payload predates the contract, without throwing or rendering constants

### Requirement: Payload size decision is recorded

The change SHALL record an explicit decision about payload size (minify, gzip-fetch, or accept
the growth) before regenerating the payload.

#### Scenario: No silent size regression
- **WHEN** the payload grows because provenance and acquisition dates were added
- **THEN** the documented decision explains the resulting artifact size and the loading
  strategy
