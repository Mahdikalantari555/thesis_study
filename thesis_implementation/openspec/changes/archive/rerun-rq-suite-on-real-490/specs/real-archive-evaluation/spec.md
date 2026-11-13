# Spec Delta

## Purpose

Guarantees that research-question benchmarks are computed on the real Khuzestan archive and that every reported number states which data produced it.

## ADDED Requirements

### Requirement: Real archive is the default data source

Every RQ benchmark script (`run_rq1_benchmark.py` … `run_rq7_rq8.py`, `run_data_scarcity.py`) SHALL load the real 490-field archive (`stats.zarr` + `cycles_490.parquet` / `growth_cycles_490.npz`) unless another source is explicitly requested.

#### Scenario: Default run uses the real archive

- **WHEN** a benchmark script is run without `--source`
- **THEN** it reads the real 490-field cycle tensors and its report records `data_source: "real490"` with `n_fields = 490`

#### Scenario: Missing real archive fails closed

- **WHEN** the real archive files are not present
- **THEN** the script exits non-zero listing the missing paths and writes no report
- **AND** it does not call `simulate_490_field_archive`

### Requirement: Synthetic runs are explicit and segregated

A benchmark SHALL use synthetic data only when `--source simulated` is passed, and SHALL write such outputs under `reports/simulated/`.

#### Scenario: Simulated output cannot be mistaken for real

- **WHEN** a script runs with `--source simulated`
- **THEN** the output path is under `reports/simulated/` and the JSON carries `data_source: "simulated"`

### Requirement: Provenance in every report

Every benchmark report SHALL include `data_source`, `n_fields`, `n_cycles`, `n_dates`, first and last acquisition date, SHA-256 of the cycle file, git commit SHA, seeds, and split SHA-256.

#### Scenario: Report is self-describing

- **WHEN** any `reports/rq*.json` or `reports/data_scarcity*.json` is opened
- **THEN** all provenance keys are present and non-empty

### Requirement: Proxies are real or absent

Metrics that depend on CWSI or ETa SHALL use per-field values derived from METRIC products for the fields evaluated, and SHALL be reported as `absent` when such values are not available for those fields.

#### Scenario: No borrowing of subset proxies

- **WHEN** the 490-field archive is evaluated and METRIC zonal CWSI/ETa for 490 fields does not exist yet
- **THEN** proxy-based columns are `absent`, and no value is taken from the 32-farm `fields.zarr`

### Requirement: Findings cite real results only

`docs/findings/` SHALL present as Khuzestan results only numbers produced with `data_source: "real490"` or `"real32"`, each with its n; earlier simulator numbers SHALL be marked superseded and labelled synthetic.

#### Scenario: Superseded numbers are labelled

- **WHEN** findings 11 or 12 are read after this change
- **THEN** every table states its data source, and any simulator-derived table sits in a section titled as synthetic/superseded
