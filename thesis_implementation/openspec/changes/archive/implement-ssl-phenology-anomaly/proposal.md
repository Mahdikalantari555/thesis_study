# Proposal

## Why

This is the implementation of a master's thesis. Farmers and agronomists need early, field-level plant stress detection, but labeled stress datasets are scarce, expensive, and crop-specific. This change establishes a lightweight, self-supervised, phenology-aware anomaly detection framework that learns normal field behavior from Landsat time series (2013-2026) without requiring labels, while leaving seams for Web GIS expert labels, knowledge fusion, multi-crop support, and edge deployment later. All outputs must be academic, measurable, and impactful to the scientific community.

## What Changes

- Add a Landsat zonal ingest pipeline producing `fields.zarr` (field x time x band) plus Parquet metadata, with checkpoint/resume and resource throttling.
- Add phenology-aware cycle segmentation using days-since-harvest as the primary phase axis, with GDD and landmark registration as comparators.
- Add a robust statistical baseline (median/MAD, iterative trimming) producing per-cycle anomaly scores and runs.
- Add masked self-supervised models (GRU-AE and 1D Transformer) on field-level cycle sequences, gated behind baseline improvement.
- Add an evaluation harness (synthetic injection, weak proxies, stability, statistical comparison).
- Add model export with SafeTensors, config, and normalization stats, plus a backend interface for future Rust acceleration.
- Add documentation, tests, and CI-ready project scaffolding.

## Capabilities

### New Capabilities

- `landsat-ingest`: Ingest Landsat scenes into field-level Zarr stores with quality masks, zonal stats, checkpoint/resume, and resource throttling.
- `phenology-cycles`: Segment harvest-driven crop cycles and align observations by growth stage (days-since-harvest, GDD, landmark registration).
- `anomaly-baseline`: Compute phenology-aware robust anomaly scores and continuous anomaly runs from normal-cycle baselines.
- `self-supervised-model`: Train masked self-supervised models on cycle sequences and produce reconstruction and embedding anomaly scores.
- `evaluation-harness`: Evaluate anomaly methods via synthetic injection, weak proxies, stability tests, and statistical comparison.
- `model-export`: Export trained models with weights, config, and normalization statistics for reproducible loading and future transfer.

### Modified Capabilities

None.

## Impact

- New repository structure under `src/ssl_anomaly/`, `conf/`, `tests/`, `scripts/`.
- New data artifacts under `data/processed/` (Zarr, Parquet, manifests).
- New MLflow-tracked experiments and DVC pipeline stages.
- Documentation in `docs/` and OpenSpec specs in `openspec/specs/`.
- No breaking changes (greenfield project).
