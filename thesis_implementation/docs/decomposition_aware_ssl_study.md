# Decomposition-aware SSL study

This is an opt-in research runner, not a replacement for `train_main.py`, the frozen `gru_ae_main` checkpoint, or the platform. It tests **H1** (does decomposition help masked raw reconstruction, given identical model capacity and targets?) separately from **H2** (are component deviations useful without a neural network?). Neither feature fusion nor hybrid scoring is presumed better.

OpenSpec change: [`decomposition-aware-ssl-study`](../openspec/changes/decomposition-aware-ssl-study/proposal.md). The [design](../openspec/changes/decomposition-aware-ssl-study/design.md) records the decisions and multi-branch gate.

## Run in order

From this repository, in the existing Python 3.11+ `geo` environment or an installed `.[dev]` virtual environment:

```bash
# Explicit engineering fixture, not Landsat data. Typically under two minutes on CPU.
python scripts/run_decomposition_study.py --smoke

# Real source, no neural training. Both branches and both protocols, all three methods.
python scripts/run_decomposition_study.py --stage benchmark --device cpu

# Matched real B/C/D study for each priority method. Separate directories, same seeds and cuts.
python scripts/run_decomposition_study.py --stage ablation --method harmonic --device cpu --out data/studies/decomposition_aware_ssl/harmonic
python scripts/run_decomposition_study.py --stage ablation --method robust_stl --device cpu --out data/studies/decomposition_aware_ssl/robust_stl

# Optional D2–D4 and the same synthetic validation without any model/checkpoint.
python scripts/run_decomposition_study.py --stage scores --method harmonic
```

Real runs require `../Data/Processed/satellite/stats.zarr`, the existing frozen
`data/processed/holdout_manifest.json`, and its `data/processed/splits_locked.json`.
Override paths with `--stats-zarr`, `--holdout-manifest` and `--splits-path`.
Audit an existing freeze with `python scripts/build_holdout_manifest.py --audit-existing`
on the archive machine before running the study. A missing spatial-block member,
split hash or cutoff mismatch blocks the run; extra frozen exclusions still
apply. Do not re-freeze to increase coverage. If no holdout was ever frozen, use
the first-freeze procedure in the [patch input runbook](patch_inputs.md).

The archive inventory is 490 fields, 607 Landsat scene dates and 539 METRIC
products, of which **538 dates are usable** (2022-08-07 is excluded). Actual
eligible fields, dates and QC-valid cells are measured in `run.json`. The
study's defaults are train before 2021-01-01, calibration in 2021, and evaluation
beginning 2022-01-01, capped by the frozen cutoff (normally 2024-01-01).
Whole-field holdouts and unknown fields are excluded at every date. These runs
say nothing about completely unseen farms or the final-test period.

Use `--resume` with the same command and output directory after interruption. Benchmark fits, epoch checkpoints and completed validation challenges are reused; fingerprint mismatches are rejected. Use a new output directory for changed assumptions. Do not run multiple writers into the same run directory. Default outputs are ignored under `data/studies/decomposition_aware_ssl/`. `--stage all` combines benchmark and one selected ablation; the two separate priority ablations are still required. Real jobs are not smoke-sized: each ablation method attempts 120 model fits (10 arms × 3 seeds × 2 branches × 2 protocols) plus the repeated decomposition/validation. Start with the no-training benchmark; full laptop runtime is not yet measured. Monitor the terminal ETA and `progress.jsonl`. CPU is the development reference; device defaults to CUDA if available for a real neural run and otherwise to CPU.

## Read the results

| Artifact | What to inspect |
| --- | --- |
| `run.json` | Data/source hashes, actual date range, field counts, split membership hash, config, software versions and code revision |
| `benchmark.json` | Paired train-MAD-scaled absolute residuals, per-channel fit errors, temporal stability, individual coverage and fit seconds |
| `decomposition/*.npz` | Measured-date masks, additive components, exclusive fit cutoffs and pre-fit STL grid states (`0` unavailable, `1` observed bin, `2` interpolated). `days` and grid bin zero are relative to 2013-03-30. The grid fills are never SSL targets. |
| `<branch>_<protocol>/summary.json` | Historical reconstruction, seed spread and paired MSE delta versus raw (negative favors candidate); calibration-only thresholds; D1–D4/hybrid comparisons on joint support; per-family/dose AP, matched dose-response support and uplift, gap robustness, evidence availability and architecture gate |
| `protocol_comparison.json` | Retrospective minus causal score contrasts on identical observed target-channel sets, computed **after scoring**. Causal scores and thresholds never use the retrospective mask. |
| `field_date_scores.parquet`, `field_summary.parquet`, `date_summary.parquet` | Observed field/date scores and max/count rollups; null means unavailable. Exceedance counts use the calibrated **acquisition** threshold, not a separate field alarm. |
| `feature_norms.npz`, `*.pt`, checkpoint sidecars | Train-only normalization and seed-specific model/optimizer/RNG state; never imported by production. |

### Interpret the controls correctly

- **B1–B7 and C1–C3** compare input representations, not different targets. `D1_B1` is the raw-only causal GRU of this study; it is not historical inference from the frozen production weights. Normalized MSE is compared on the same masked raw targets within each branch and protocol. Missing contextual features remain distinguishable. C1 has no residual feature. C2/C3 add a local residual z-score; their other statistics are based on raw earlier observations. The raw comparator includes an untrained network, an annual reference and a separate phase reference.
- **D2, D3 and D4** use field-local historical median/MAD, a minimum of five prior comparable observations per active channel and no cross-field fallback. D3 first removes the training trend line. The inferred phase is a lagged greenness heuristic (NIR in the spectral branch, NDVI in the index branch), not measured crop stage. A lack of phase support is not converted to an annual comparison. D1 is masked squared reconstruction error, so its raw numerical scale is not directly comparable with the component RMS scores. The hybrid combines D1 from the pre-registered B7 arm and D2–D4; the other D1 feature arms remain separate. Compare equal weights against both single scores and the fixed sensitivity weights; no winner is applied to production.
- **Causal** evaluation uses earlier observations and freezes model weights, normalization and alarm calibration. **Retrospective** fitting can see later observations within the permitted partition, so lower fit error is not evidence of better historical alerting. STL on a 15-day grid approximates a 360-day cycle and extrapolates only across supported bounded gaps; harmonic regression uses actual elapsed days and a 365.2425-day annual period. Different fit support is reported rather than imputed into results.
- **Historical holdout** is unlabeled and can include real events. Alarm fractions on it are not ground-truth false-alarm rates. Synthetic AP uses the unmodified counterfactual and the affected field-dates in evaluation-only NIR interventions, not confirmed stress events. Field AP compares perturbed fields to their own clean counterfactuals using maximum scores; its deliberately paired class balance differs from field-date AP. Prefer dose-by-family results with support counts, not a single pooled ranking. Missingness removes 20% of eligible acquisition dates per field (rounding down) and evaluates only shared scored dates.
- **Dose response** uses only field-dates that actually changed and have finite
  clean and challenged scores at **every** dose for that arm and family.
  `dose_response` reports the matched field/date counts and the rows each dose
  lost to matching. Without shared support the medians and trend are `null`;
  the per-dose metrics in `synthetic_sensitivity` still use their native paired
  support. On resume, the stored challenge uplift arrays preserve the cohort.
- **Multi-branch and optional decomp methods:** an eligible gate starts a review, not another training job. Do not use smoke numbers to choose the study method or architecture. SSA, wavelets, the auxiliary component-target loss, and a matched comparison to the frozen architecture remain follow-ups.

## Optional observed evidence (no training use)

- `--indicators evidence.parquet` (or CSV): columns `field_id`, `date` (`YYYY-MM-DD`), `indicator` (`tvdi`, `cwsi`, or `eta`), `value`, `observed`, `source`. Give the specific QC-approved polygon-zonal product and units in `source`. Keys are unique per product/field/date. Only `observed=true`/`1` is joined; do not use daily interpolated products as observed evidence. ETa is correlated in its supplied units, not silently converted into an evaporative deficit. TVDI, CWSI and ETa can share Landsat optical inputs, scene effects or weather; this is agreement only, even with thermal removed from model input.
- `--adjacency edges.csv` (or Parquet): `field_id`, `neighbor_id`, `source`, one undirected polygon-derived edge per pair. Same-date neighbor association is descriptive; shared weather/operations and spatial autocorrelation can create agreement without diagnostic skill. This does not validate a spatial holdout.
- Absent or unmatched evidence is reported as `absent` with counts, never zero evidence or generated labels. No results from these inputs enter model training, thresholds, or the architecture gate.

## Verification and current blocker

The audit CPU smoke fixture (4 fields, 169 acquisitions) completed all four
branch/protocol cases in 37 seconds, writing 120 checkpoints and 60 support
arrays (15 family/dose challenges per case). A completed resume added no epochs.
A partial-case resume regenerated a deliberately missing challenge support file
and reproduced both native and matched summaries without retraining. The
standalone Robust STL score check from the original study produced no neural
checkpoints. This is engineering evidence only, not a thesis validation rung.

The mounted checkout does not include the canonical `stats.zarr`, frozen holdout manifest, locked splits, or observed indicator tables. Real mode stops at `Canonical polygon zonal stats.zarr not found` and does not create a substitute report. The real benchmark, ablation and agronomic review remain open in OpenSpec.

The baseline platform files were not changed. Its TypeScript check passes; Vite reports `Could not resolve "./series_khuzestan.json?raw" from "src/data/data.ts"`. The runtime capture cannot start without the build. The strict real-data selection reports missing artifacts, including the series,
registry, cycle files and locked splits. The checkout selection does not replace
that gate. No generated placeholders were added.
