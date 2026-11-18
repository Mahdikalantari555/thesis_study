# Decomposition-aware SSL study

## Why

Test two independent hypotheses: (H1) decomposed temporal representations improve learning with the same model budget; (H2) component deviations are useful anomaly signals even without SSL. Neither a redundant representation (`X = T + S + R`) nor a hybrid score is assumed to win.

## What Changes

- Add a CPU-first, read-only Landsat field study with separate optical-band and vegetation-index arms, observation masks, and per-field decomposition.
- Benchmark STL, Robust STL and harmonic regression; compare B1–B7 and C1–C3 with a small shared causal GRU architecture, and D1–D4 independently of any claim about agricultural stress. Include an equal-weight calibrated hybrid and a fixed sensitivity analysis.
- Separate causal detection from retrospective reconstruction. Evaluate on historical development holdout, paired synthetic perturbations, missing-data sensitivity and, where available, observed TVDI/CWSI/ETa and spatial adjacency.
- Keep SSA, wavelets and multi-branch training as follow-up work. Pre-register a gate for the latter; neither a smoke run nor a positive retrospective result can qualify it.

## Capabilities

### New Capabilities

- `decomposition-aware-anomaly-study`: Reproducible decomposition benchmarking, feature ablation and field/date anomaly evidence under the existing holdout invariant.

### Modified Capabilities

None.

## Impact

New study modules, configuration, CLI, tests, and a runbook. No new Python dependencies, raster ingest, production training or checkpoint changes, platform wiring, or locked-split edits. The source archive inventory is 490 fields, 607 Landsat acquisitions (2013–2026), 539 METRIC products and **538 usable dates** (`data/DATA_SUMMARY.md`); actual study coverage is smaller after applying the frozen exclusions and QC. Full real-data execution requires the separately stored zonal statistics and holdout manifest and does not open the thesis's final-test period or holdout fields.
