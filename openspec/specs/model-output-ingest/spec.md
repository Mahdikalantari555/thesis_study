# model-output-ingest Specification

## Purpose
Defines how trained model checkpoints are loaded and run by `scripts/export_platform_data.py` to produce real anomaly scores per field-month, replacing proxy CWSI formulas.

## Requirements

### Requirement: Checkpoint discovery and loading

The system SHALL discover trained model checkpoints under `checkpoints/` by name (`masked_transformer_main.pt`, `gru_ae_main.pt`, and the legacy `sts_net_490.pt`, `tiny_cnn_mamba_490.pt`, `time2agri_490.pt`) and load each with its JSON sidecar (config, normalization statistics, threshold, persistence k, split hash, ladder rung).

#### Scenario: Checkpoint loads successfully
- **WHEN** `checkpoints/masked_transformer_main.pt` or `checkpoints/gru_ae_main.pt` and its JSON sidecar exist
- **THEN** the exporter scores every observation causally with them and fills `scores.masked_transformer` / `scores.gru_ae` and `stressFlag`

#### Scenario: Checkpoint missing
- **WHEN** a checkpoint for an SSL slot does not exist
- **THEN** that slot is `absent` for every observation and the exporter does not crash

### Requirement: Per-field inference input construction

The system SHALL construct per-field cycle sequence tensors `(phase_bins, bands)` from `stats.zarr` time series, normalized using saved normalization statistics.

#### Scenario: Input tensor shape
- **WHEN** building model input for a field with 48 monthly observations
- **THEN** the tensor shape matches what the model was trained on (per training pipeline contract)

### Requirement: Score provenance tracking

The system SHALL write a per-score provenance map with values `"model"` or `"absent"` for SSL slots (`masked_transformer`, `gru_ae`, `sts_net`, `tiny_cnn_mamba`, `time2agri`). SSL slots SHALL NOT fall back to the CWSI proxy formula. Baseline heuristic slots (`b0_calendar`, `b1_dsh`, `b1_cusum`) MAY keep `"proxy"` only if their formula does not use CWSI.

#### Scenario: All models available
- **WHEN** all SSL checkpoints (main + legacy) load successfully
- **THEN** every SSL score carries `"provenance": "model"` with the formula id from the sidecar (`<id>:causal_bin_mse` for main checkpoints)

#### Scenario: Mixed availability
- **WHEN** only some SSL checkpoints exist
- **THEN** present checkpoints score `"model"` and every other SSL slot is `absent` (null score) — never a proxy value

#### Scenario: Unmapped observation
- **WHEN** an observation cannot be mapped to a cycle bin
- **THEN** its SSL scores are null with provenance `"absent"`

### Requirement: Stress flag in the platform contract

Contract v5 SHALL add per observation `stressFlag` (`normal` | `suspected_stress` | `no_data`), `stressFlagModel` (checkpoint id) and per field `ladderRung`; `scripts/platform_channels.py` and `platform/src/data/channels.ts` SHALL stay mirrored and the contract test SHALL cover the new fields.

#### Scenario: Platform renders flag
- **WHEN** the platform loads a v5 payload
- **THEN** each observation shows its stress flag and the model that produced it, and v4 payloads still load with the flag shown as unavailable
