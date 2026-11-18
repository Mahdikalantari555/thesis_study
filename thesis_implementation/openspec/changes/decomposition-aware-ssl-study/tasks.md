## 1. Observations and benchmark

- [x] 1.1 Add a read-only, frozen-manifest-aware zonal input adapter and separate band/index views; test QC, holdout exclusion, and fail-closed real input handling.
- [x] 1.2 Benchmark STL, Robust STL and harmonic regression in both protocols; test gap provenance, additive components, partition isolation and causal prefix invariance.

## 2. Features, scoring and validation

- [x] 2.1 Add B1–B7 and C1–C3 with global/local statistics and a matched masked GRU; test common raw targets, feature isolation and train-only normalization.
- [x] 2.2 Add D1–D4, annual/inferred-phase comparators, calibrated hybrids and field/date aggregation; test historical references, missing values, calibration isolation and sensitivity weights.
- [x] 2.3 Evaluate the historical holdout, all five synthetic families, missingness and optional indicator/spatial evidence; test that perturbations do not modify past observations and evidence cannot select a model or threshold.

## 3. Execution and review

- [x] 3.1 Wire a staged, resumable CLI with isolated outputs, checkpoints, progress, runbook and provenance; run the explicit end-to-end smoke and verify output and resume.
- [ ] 3.2 Run and review the benchmark and ablation on the authorized canonical Landsat development archive; record source coverage, real paired results and architecture-gate outcome (requires external Zarr and frozen manifest; never satisfied by smoke).

Task 3.2 is blocked in this checkout: `../Data/Processed/satellite/stats.zarr`, the locked splits and the frozen
holdout files under `data/processed/` are absent. Use the [runbook](../../../docs/decomposition_aware_ssl_study.md) against the authorized local archive.

## Workflow follow-up

- Keep the change active until real runs are available for review. Keep any multi-branch, auxiliary loss, SSA or wavelet study in a separately reviewed follow-up. Review indicator availability and shared-input limitations before increasing the validation claim.

## Audit follow-up

- [x] A.1 Use the common changed and scored rows for dose-response summaries,
      report support loss, and verify challenged-score resume and empty support.
