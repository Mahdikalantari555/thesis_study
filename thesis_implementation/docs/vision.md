# Vision

## One-line goal

A **transferable, incremental, lightweight, self-supervised framework** that detects plant stress/anomalies at field scale **without labeled data**, starting from Landsat time series (2013-2026) and growing into a crop-agnostic system fused with expert labels and textual crop knowledge.

## Problem

Farmers and agronomists need early, field-level (and intra-field) stress detection. Labeled stress datasets are scarce, expensive, and crop/region specific. We instead learn the *normal* phenological behavior of a field over multiple growing cycles and flag deviations.

## Core idea: phenology-aware anomaly

An observation is not compared to a calendar date (DOY). It is compared to **the same growth stage in other normal cycles of the same field/stratum**. For crops with harvest-driven cycles (e.g. sugarcane) the axis is **days since last harvest** (+ GDD), not calendar DOY. The unit of analysis is a **cycle**, not a year.

## Scope

### Now (v1, this repository)

- Data: Landsat 8/9 L2, 2013-2026, ~490 fields, 30 m, EPSG:32639; ERA5 daily weather; METRIC products (ETaDaily, CWSI, LST, NDVI, ...).
- Geography: one small industrial farm area (and optionally any scale for prototyping).
- Level: field-mean (zonal) time series first; patch-level is a later phase.
- Crop: primary implementation for sugarcane (harvest-driven cycles). Interface must allow other crops.
- Compute: runs on a personal laptop (CPU, throttled, checkpoint/resume). Cloud GPU optional for DL phases.

### Later (placeholders, not implemented now)

1. **Web GIS expert labeling**: collect expert stress labels spatially; ingest as weak supervision / validation, never as the sole training signal.
2. **Knowledge fusion**: combine self-supervised embeddings/anomaly scores with crop knowledge (articles, books, Q&A) for interpretation and decision support.
3. **Multi-crop**: crop-specific `CycleSegmenter` and `phase_axis` implementations behind a common interface.
4. **Intra-field**: patch-level 3D models and intra-field zoning when field-mean is insufficient.
5. **Edge / drone (Frugal AI)**: benchmark ONNX/quantized models for drone/edge inference after the FP32 model is accepted.
6. **Incremental / transferable learning**: update models with new seasons/fields without full retraining; transfer across farms and crops.
7. **Active learning from farmers (2026-11-10)**: the self-supervised monitoring output (per-acquisition suspected-stress flag) becomes the input of an active-learning loop. Farmers report where and when stress actually happened, and those reports become real labels. Planting/harvest records, when available, are used for validation of cycle segmentation only and must not block development.
8. **Crop-agnostic product (2026-11-10)**: the long-term product is crop-independent. For now this stays a vision item only. The code keeps the sugarcane implementation (harvest segmentation, DSH bins), and no abstraction work is required until a second crop is added. The literature review in `data-and-phenology-readiness` records which phenology/time-axis methods would generalise.

## Key requirements

- **Self-supervised & label-free**: training uses masked observation modeling and normal-cycle baselines; labels only for validation.
- **Phenology-aware**: alignment by growth stage (days-since-harvest, GDD, landmark registration), compared empirically.
- **Multi-year comparison**: compare the same growth stage across years/cycles of the same field and stratum.
- **Intra-field awareness**: design must not assume spatial uniformity; field-mean first, patch-level later.
- **Multi-crop ready**: `CycleSegmenter` and `phase_axis` are replaceable.
- **Lightweight**: small models (<1M params where possible), CPU-friendly, deterministic, reproducible.
- **Efficient**: throttled CPU, resume-safe, ETA-visible; Rust acceleration gated behind profiling.
- **Transferable**: exportable weights + config + normalization stats; versioned datasets/splits.
- **Frugal-AI ready**: keep a path to quantization/ONNX/edge benchmarking.

## Feasibility question (current focus)

> Can anomalies be discovered using **only Landsat 2013-2026** for a small industrial farm area, via self-supervised learning?

This is answered empirically in Phase 1-2:

- Baseline B1 (phenology-aware robust z-score) vs B0 (calendar z-score) on synthetic injection (V1) and proxies (V2: ETa, yield).
- SSL (GRU-AE / masked Transformer) only if it beats B1 with confidence intervals.
- If SSL does not beat B1, its role is limited to embedding/retrieval.

## Use of derived indices (ETaDaily, CWSI)

- ETa/ETref and yield are preferred validation proxies.
- CWSI can be used as a proxy **but with caution**: if CWSI is derived from LST (as in METRIC), using LST as model input and CWSI as validation is partly circular. Mitigation: ablation without LST; primary validation on ETa and yield.
- The user's METRIC Python library is an asset; its outputs feed both features and validation, with circularity documented.

## Non-goals (v1)

- No production service, no web app, no real-time inference.
- No claim of cross-crop generalization (only interface readiness).
- No Rust in Phase 1.
- No ONNX/quantization until FP32 model is accepted.

## Success criteria

- G0: harvest detection acceptable on QC fields; most fields have multiple complete cycles.
- G1: phase-aware baseline beats calendar baseline on synthetic injection and proxies.
- G2: SSL beats B1 with CI, or its role is honestly limited to embedding/retrieval.
- G3: Rust only after profiling justifies it.
- Reproducibility: deterministic runs, MLflow tracking, DVC data versioning, golden regression tests.
