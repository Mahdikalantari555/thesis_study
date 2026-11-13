# Design

## Context

This is a greenfield repository. Existing project documents define the desired system: `docs/vision.md`, `docs/implementation_plan.md`, `docs/final_plan.md`, and `docs/initial_plan_assumptions.md`. The implementation must run on a laptop by default, use field-level Landsat time series first, and leave seams for future Web GIS labels, knowledge fusion, multi-crop support, and edge deployment.

## Goals / Non-Goals

**Goals:**
- Establish a reproducible, testable pipeline from Landsat ingest to phenology-aware anomaly scores.
- Keep models small and CPU-friendly by default.
- Make all heavy stages resumable and resource-throttled.
- Define stable interfaces for future crop-specific segmentation, Rust acceleration, and knowledge fusion.

**Non-Goals:**
- No production service, web application, or real-time inference.
- No patch-level or 3D models in this change.
- No Rust implementation before profiling.
- No ONNX or quantization until the FP32 model is accepted.
- No claim of cross-crop generalization; only interface readiness.

## Decisions

- Use Zarr v3 with sharding for `fields.zarr`; store only CRS and affine transform.
- Use days-since-harvest as the primary phase axis, with GDD and landmark registration as comparators.
- Use median and MAD baselines with iterative trimming rather than deep models first.
- Gate SSL training behind a measurable baseline improvement.
- Use Lightning checkpoints for resume and SafeTensors for release artifacts.
- Define a `PhenologyBackend` protocol so Rust can be added later without rewriting callers.
- Keep spectral indices out of ingest so input ablations do not require re-ingest.

## Risks / Trade-offs

- Harvest detection errors can distort baselines; mitigated by visual QC, sensitivity tests, and harvest record comparison.
- Field-mean analysis may hide intra-field variation; mitigated by an intra-field experiment and a later patch-level phase.
- CWSI validation can be circular with LST; mitigated by ablations and preference for ETa and yield proxies.
- Lack of real labels limits claims; mitigated by synthetic injection, proxies, event review, and stability tests.
- Laptop constraints may slow experimentation; mitigated by throttling, resume, and optional cloud GPU.
