# Proposal: Integrate Real Model Outputs into Platform Data Pipeline (`integrate-real-model-outputs`)

## Why

The platform currently renders anomaly scores from **proxy CWSI formulas** (`scripts/export_platform_data.py:193-202`), not from the trained SSL models. All seven scores are `clamp(offset + max(0, cwsi - 0.45) * weight)` — one signal with seven weights, rank-correlated ρ ≈ 0.633 with CWSI. The trained checkpoints exist (`checkpoints/sts_net_490.pt`, `checkpoints/tiny_cnn_mamba_490.pt`, `checkpoints/time2agri_490.pt` plus Lightning `.ckpt` files) but are never loaded by the exporter. The `integrate-real-data-and-platform` change was marked complete (17/17 tasks) but only wired mock data — real model outputs were never connected.

## What Changes

- **Real checkpoint inference in `scripts/export_platform_data.py`**: load exported SafeTensors/`.pt` model checkpoints for STS-Net, Tiny-CNN-Mamba, and Time2Agri; run inference on per-field cycle sequences; write real anomaly scores into `series_khuzestan.json` instead of proxy formulas.
- **Per-score provenance flag**: each score carries `"provenance": "model"` when computed from a loaded checkpoint, `"proxy"` when falling back to the CWSI formula (with formula id recorded), and `"absent"` when the checkpoint is unavailable.
- **Model-output spec**: define the model artifact layout (weights + config + normalization stats per `implement-ssl-phenology-anomaly` model-export spec), the inference interface, and the mapping from checkpoint → platform model ID.
- **Contract update**: `scripts/platform_channels.py` and `platform/src/data/channels.ts` add score provenance metadata; `tests/unit/test_platform_data_contract.py` gains parity checks for model vs proxy scores.
- **Graceful degradation**: if checkpoints are missing, exporter emits proxy scores with `"provenance": "proxy"` and does not crash; platform labels them accordingly.

## Capabilities

### New Capabilities
- `real-model-scores`: Platform displays anomaly scores from trained checkpoints (STS-Net, Tiny-CNN-Mamba, Time2Agri) with per-score provenance ("model" vs "proxy").
- `model-output-artifact`: Defined layout for exported model artifacts (weights + config + normalization stats) consumable by the exporter.

### Modified Capabilities
- `platform-data-contract`: Extends contract version to v3; adds score provenance and formula-id fields per observation.
- `scripts/export_platform_data.py`: Replaces proxy score block with checkpoint-backed inference + fallback.

## Impact

- `scripts/export_platform_data.py` — load checkpoints, run per-field inference, write real scores
- `scripts/platform_channels.py` — add score provenance registry fields
- `platform/src/data/channels.ts` — mirror registry fields for TS parity
- `platform/src/data/*.json` — regenerated series with real scores + provenance map
- `tests/unit/test_platform_data_contract.py` — model vs proxy score parity tests
- `docs/platform_bug_audit.md` — add BUG for proxy-vs-real score distinction

## Out of Scope

- Retraining models; only inference from existing checkpoints.
- Real-time inference backend (static pre-computed scores per `integrate-real-data-and-platform` decision).
- RGB/NDVI raster tile serving (handled by `add-rgb-ndvi-tile-layer` change).
