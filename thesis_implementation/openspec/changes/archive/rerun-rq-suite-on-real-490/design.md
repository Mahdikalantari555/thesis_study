# Design

## Context

- Real archive: `Data/Processed/satellite/stats.zarr` — 490 fields × 538 dates × 7 bands (SR_B2..B7 + ST_B10), 8 distribution stats + `valid_frac`; read via `ssl_anomaly.io.stats_zarr.load_stats_zarr` (date range 2013-03-30 → 2026-09-10).
- Real cycles: `scripts/segment_and_export_cycles_490.py` → `data/processed/cycles_490.parquet` and `data/interim/growth_cycles_490.npz` (36 × 15-day bins, ≤540 days, channel 0 = NDVI + 7 bands). `scripts/cycle_inputs.py` reproduces the same tensors for scoring. Verified (task 1.2, 2026-11-10): 1755 total cycles, 956 censored, 799 non-censored; 370 fields with ≥1 non-censored cycle, 223 with ≥2.
- `data/processed/fields.zarr` is the 32-farm R11 subset (539 dates) and is the only file holding `cwsi_et`.
- **Date count reconciliation (task 1.1):** `stats.zarr` contains 538 acquisition dates (2013-03-30–2026-09-10) while the 32-farm `fields.zarr` and the stated METRIC processed-scene count are 539. The specific missing acquisition was not identified from available manifests in this pass; `stats.zarr` is treated as the canonical 490-field archive for this change and the one-date difference is recorded here rather than assumed. All provenance reports the actual `n_dates=538` from `stats.zarr`.

## Goals / Non-Goals

**Goals:** every RQ result cited in the thesis comes from the real archive with its n stated; no silent synthetic fallback anywhere; old simulator numbers are visibly superseded.

**Non-Goals:** improving scores, new pretexts, platform work, Rust.

## Decisions

### 1. One loader, the same tensors as the checkpoints
`real_archive.load_real490_archive()` reads `growth_cycles_490.npz` (+ `cycles_490.parquet` for field/year/censoring metadata) and returns the dict already consumed by `run_loyo_archive_benchmark`. Reusing the training NPZ guarantees the RQ suite and the platform checkpoints see identical inputs. If the NPZ is stale vs `stats.zarr` (hash mismatch), the loader refuses and asks for a rebuild.

### 2. Fail closed
`--source real490` is the default. Missing files → non-zero exit with the path list. `simulate_490_field_archive` stays in the codebase for unit tests and explicit `--source simulated` runs only; those outputs go to `reports/simulated/` and carry `data_source: "simulated"`.

### 3. Labels and proxies
- RQ1 currently builds `y_stress` as top-20% cycle-mean CWSI. That is a **weak proxy**, and with LST in the input it is partly circular (AGENTS.md / vision.md). Keep the label name `weak_proxy_top20pct_mean_cwsi_not_validated_stress` and always report the no-LST ablation next to it.
- For 490 fields, CWSI_ET and ETaDaily must come from METRIC zonal statistics (`Data/Metric/products/`). This is a dependency on todo item 1. Until available, proxy-dependent metrics are emitted as `absent`; synthetic-injection metrics (which need no proxy) run immediately.

### 4. Splits
LOYO by cycle start year plus a spatial hold-out by **block** (20 blocks), not by field id, so neighbouring fields do not leak across folds (Roberts et al. 2017, already cited in `docs/growth_validation.md`). Splits are written once to `data/processed/splits_490.json` with a SHA-256 and fixed before any test score is inspected.

### 5. RQ5 and RQ6 on real data
- RQ5: inject progressive-onset deviations into held-out **real** cycles (same mechanisms as `growth_validation`) and measure lead time vs the NDVI threshold. Reported as a controlled-deviation (ladder L2) result, not field-observed early warning.
- RQ6: compute Integrated Gradients on real held-out cycles; the "physiology agreement" metric is reported only if its reference is real (e.g. phase of ETa deficit); otherwise the agreement number is dropped.

### 6. Rust
The user did not author the `rust/` crate; it was added by coding-agent commits (`d31365c`, `fdb19ba`) and the `32.7×` Whittaker speed-up in findings 10 has not been reproduced on the user's machine. This change does not touch Rust, but findings 10 is updated to mark that claim as unverified, and the keep/remove decision is added to `todo.md` → Open questions.

## Risks / Trade-offs

- **Compute**: 490 fields × multiple seeds × LOYO on a CPU laptop. Mitigation: `limit_threads`, per-fold checkpoints, `--max-loyo-years`, and seeds trimmed to 3 for the first pass with the count reported.
- **Results may get worse than the simulator numbers.** That is the point; findings must report them as they are (prime directive 4).
- **Proxy dependency** on METRIC zonal stats could delay RQ1/RQ3 proxy columns; injection-based metrics are not blocked.
