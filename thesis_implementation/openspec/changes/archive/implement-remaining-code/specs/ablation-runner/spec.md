# Spec Delta

## Purpose

Execute multi-seed input channel drop ablations across thermal, meteorological, and spectral inputs and report metric deltas with bootstrap confidence intervals.

## ADDED Requirements

### Requirement: Input drop multirun execution
The ablation runner SHALL support dropping LST, weather features, or individual spectral bands via `input.drop` configurations across 5 random seeds per configuration.

#### Scenario: Thermal and weather ablation
- **WHEN** the ablation script runs with weather on/off and LST on/off configurations
- **THEN** each configuration is evaluated across 5 seeds without re-ingesting the underlying dataset

### Requirement: Metric delta reporting with confidence intervals
The ablation runner SHALL compute and persist metric changes relative to the full-input configuration along with 95 percent bootstrap confidence intervals.

#### Scenario: Circularity check without LST
- **WHEN** LST is dropped from inputs
- **THEN** the report records synthetic injection metrics, proxy correlations, and their 95 percent confidence intervals compared against the LST-enabled run
