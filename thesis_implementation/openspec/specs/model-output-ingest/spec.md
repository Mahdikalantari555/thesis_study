# model-output-ingest Specification

## Purpose
Defines how trained model checkpoints are loaded and run by `scripts/export_platform_data.py` to produce real anomaly scores per field-month, replacing proxy CWSI formulas.

## Requirements

### Requirement: Checkpoint discovery and loading

The system SHALL discover trained model checkpoints under `checkpoints/` by name pattern (`sts_net_490.pt`, `tiny_cnn_mamba_490.pt`, `time2agri_490.pt`) and load them with their config + normalization statistics sidecar files.

#### Scenario: Checkpoint loads successfully
- **WHEN** `checkpoints/sts_net_490.pt` exists with valid weights and config
- **THEN** the exporter loads the model and uses it for STS-Net score inference

#### Scenario: Checkpoint missing
- **WHEN** `checkpoints/time2agri_490.pt` does not exist
- **THEN** the exporter emits Time2Agri score with `"provenance": "proxy"` and does not crash

### Requirement: Per-field inference input construction

The system SHALL construct per-field cycle sequence tensors `(phase_bins, bands)` from `stats.zarr` time series, normalized using saved normalization statistics.

#### Scenario: Input tensor shape
- **WHEN** building model input for a field with 48 monthly observations
- **THEN** the tensor shape matches what the model was trained on (per training pipeline contract)

### Requirement: Score provenance tracking

The system SHALL write a per-score provenance map alongside each observation's scores, with values `"model"` (checkpoint inference), `"proxy"` (CWSI formula fallback), or `"absent"` (no data).

#### Scenario: All models available
- **WHEN** all three checkpoints load successfully
- **THEN** all scores carry `"provenance": "model"`

#### Scenario: Mixed availability
- **WHEN** only STS-Net checkpoint exists
- **THEN** STS-Net score is `"model"`, others are `"proxy"` with formula id recorded
