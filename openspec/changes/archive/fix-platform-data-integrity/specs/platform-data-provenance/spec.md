# Spec Delta: platform-data-provenance

## Purpose

Makes the origin of every displayed value visible. The previous change labelled the whole
platform “Demonstration data”; that is insufficient because a single response mixes observed
satellite indices, derived proxies, modelled weather, absent channels, and anomaly scores that
may come from either inference or a hand-written formula. This capability expresses provenance
per channel and per score, and surfaces it wherever a number is presented as evidence.

## ADDED Requirements

### Requirement: Four provenance states

Every value SHALL carry exactly one provenance state: `observed`, `modelled`, `proxy`, or
`absent`.

#### Scenario: States are exhaustive and exclusive
- **WHEN** a value is rendered
- **THEN** exactly one of the four states is attached, and no value is rendered without one

#### Scenario: Observed means measured
- **WHEN** a channel is marked `observed`
- **THEN** the value was computed from the satellite archive for that field and acquisition,
  with no synthetic substitution

### Requirement: Provenance is data, not presentation

Provenance SHALL travel with the payload so that every consumer — views, tooltips, and CSV
exports — receives the same classification.

#### Scenario: CSV export is honest
- **WHEN** the user exports a paired sample or a time series
- **THEN** the export contains a provenance column per value (or a provenance header block)
  consistent with what the UI showed

### Requirement: Per-model score provenance

Each anomaly model's score SHALL declare whether it came from model inference or from a proxy
formula.

#### Scenario: Proxy scores are labelled
- **WHEN** a model's scores are formula-derived
- **THEN** the model is presented with a proxy label everywhere it appears, and no comparison
  claim implying independent detectors is offered for it

#### Scenario: Inference scores carry an artefact id
- **WHEN** a model's scores come from inference
- **THEN** the score record references the artefact that produced it

### Requirement: Channel provenance surfaced in the UI

Each view that renders a channel SHALL expose that channel's provenance without requiring a
tooltip hunt.

#### Scenario: Inspector shows provenance
- **WHEN** the field inspector displays an indicator value
- **THEN** the value's provenance state is visible next to it

#### Scenario: Legend explains the states
- **WHEN** a map layer is coloured by an indicator or a score
- **THEN** the legend includes an explanation of the provenance states in the active locale

#### Scenario: Quiet when observed
- **WHEN** a value is `observed`
- **THEN** the provenance indicator does not add visual noise beyond the legend explanation

### Requirement: Staleness surfaced alongside provenance

A value derived from an acquisition that differs from its sample date by more than one revisit
interval SHALL be flagged as stale wherever it is displayed.

#### Scenario: Stale sample warning
- **WHEN** a field-month's acquisition is more than one revisit away from the nominal sample
  date
- **THEN** the tooltip and the inspector state the acquisition date and mark the sample stale

### Requirement: Locale coverage

Every provenance and staleness label SHALL exist in both `en` and `fa`.

#### Scenario: No English leakage in Persian
- **WHEN** the active locale is `fa`
- **THEN** provenance and staleness strings render in Persian, and the dictionary-parity test
  passes
