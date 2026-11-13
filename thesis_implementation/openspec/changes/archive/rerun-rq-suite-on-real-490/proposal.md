# Proposal: Re-run the RQ1–RQ8 Suite on the Real 490-Field Archive (`rerun-rq-suite-on-real-490`)

## Why

The thesis has a real archive for **all 490 fields × 538 Landsat acquisitions** (`Data/Processed/satellite/stats.zarr`, 2013-03-30 → 2026-09-10) and real segmented cycles for all 490 fields (`data/processed/cycles_490.parquet`, `data/interim/growth_cycles_490.npz`, built by `scripts/segment_and_export_cycles_490.py`). The platform is already wired to it.

The RQ1–RQ8 and data-scarcity results reported in `docs/findings/11_*.md` and `12_*.md`, however, were **not** computed on that archive. The "490-field" numbers come from `simulate_490_field_archive` (`src/ssl_anomaly/eval/cv.py:185`), a calibrated synthetic generator used as a fallback when the archive was not mounted in the environment that ran them. `reports/rq1_benchmark.json` records this explicitly (`full_490_field_loyo_source: "simulated_490_field_13_5yr_calibrated_fallback"`). Several scripts call the simulator unconditionally:

| Script | Data actually used |
|---|---|
| `run_rq1_benchmark.py` | real 32-farm subset + simulator for "490" (fallback; `--full-zarr` path also reuses the 32-farm `cycles.parquet` — a bug) |
| `run_rq2_pretexts.py` | real 32-farm subset |
| `run_rq3_lst_ssl.py` | 32-farm subset + simulator (80 fields) |
| `run_rq4_cloud_and_stability.py` | 32-farm subset + simulator (65 fields) |
| `run_rq5_early_detection.py` | `simulate_progressive_onset_archive` only |
| `run_rq6_xai.py` | simulator only (55 fields) |
| `run_rq7_rq8.py` | simulator (65 fields) |
| `run_data_scarcity.py` | 32-farm subset; `data_scarcity_sim490.json` = simulator |

On the 32-farm subset (35 usable cycles) all detectors reach AUC-PR = 1.0, so that benchmark is saturated and cannot rank methods. Per AGENTS.md prime directives 1–3, no simulator-derived number may be presented as a result about the Khuzestan farms. The thesis needs every RQ answered on real data, or honestly reported as not answerable.

## What Changes

- **Single real-archive loader**: one function that builds the RQ archive dict (`X`, `bands`, `field_ids`, `start_years`, proxies) from `stats.zarr` + `cycles_490.parquet` / `growth_cycles_490.npz`, reusing the exact cycle tensors the platform checkpoints were trained on. Fixes the RQ1 `--full-zarr` bug.
- **Real-first, simulator-never-silent**: every `run_rq*.py` / `run_data_scarcity.py` gets `--source {real490,real32,simulated}` with default `real490`. If the real archive is missing the script **fails** instead of falling back. Simulator runs remain possible only when requested, and their outputs are written under `reports/simulated/` with `data_source` in every JSON.
- **Provenance in every report**: each report JSON carries `data_source`, `n_fields`, `n_cycles`, `n_dates`, date range, cycle-file SHA-256, git SHA, seeds.
- **Real validation proxies for 490 fields**: weak-proxy labels / ETa-deficit correlations need CWSI and ETa per field for all 490; these come from METRIC zonal stats (shared with todo item 1 `visualize-metric-products`). Until those exist, RQs that need them report `proxy: absent` rather than reusing the 32-farm `cwsi_et`.
- **Re-run and re-document**: run the suite on real 490, regenerate `reports/*.json|csv`, rewrite findings 10–12 with real numbers, and mark the previous simulator numbers as superseded (kept in an appendix, clearly labelled synthetic).
- **RQ5 / RQ6 on real data**: RQ5 early detection and RQ6 XAI currently have no real-data path; define one (injected-onset on real cycles for RQ5; IG/attribution on real cycles for RQ6) or record them as not supported by real data.

## Capabilities

### New Capabilities
- `real-archive-evaluation`: Research-question benchmarks run on the real 490-field archive by default, never fall back to synthetic data silently, and record their data source and provenance in every output.

### Modified Capabilities
- (none — growth-validation and model-output-ingest specs are untouched)

## Impact

- `src/ssl_anomaly/eval/cv.py` (+ new `src/ssl_anomaly/eval/real_archive.py`)
- `scripts/run_rq1_benchmark.py` … `run_rq7_rq8.py`, `scripts/run_data_scarcity.py`
- `reports/` (regenerated; simulator outputs moved to `reports/simulated/`)
- `docs/findings/10_remaining_code_results.md`, `11_rq1_to_rq8_empirical_framework.md`, `12_data_scarcity_diagnostics.md`, `08_honest_assessment.md`
- `tests/test_rq1_to_rq8_framework.py` (+ provenance/no-fallback tests)
- `todo.md`

## Out of Scope

- New models or architectures; retraining beyond what each RQ protocol already specifies (todo item 4 stays separate).
- Platform UI changes.
- The validation-ladder spec (todo item 5, blocked on the user's write-up).
- Rust backend work (see design §6).
