# Tasks

## 1. Inventory and loader

- [ ] 1.1 Reconcile date counts: METRIC products (539 scenes) vs `stats.zarr` (538 dates) vs `fields.zarr` (539). Identify the missing date and record why. Verify: note in design.md Context.
- [ ] 1.2 Verify `cycles_490.parquet` / `growth_cycles_490.npz` are current vs `stats.zarr` (rebuild with `scripts/segment_and_export_cycles_490.py` if not); record n_cycles, censored count, fields with ≥2 complete cycles. Verify: numbers written to `docs/findings/01_data_and_ingest.md`.
- [ ] 1.3 Add `src/ssl_anomaly/eval/real_archive.py::load_real490_archive()` returning the archive dict from the NPZ + parquet, with hash check. Verify: unit test on shapes/keys; refuses on hash mismatch.
- [ ] 1.4 Shared `--source {real490,real32,simulated}` argument + `provenance()` helper (keys per spec). Verify: unit test that every key is filled.

## 2. Fail-closed scripts

- [ ] 2.1 `run_rq1_benchmark.py`: replace `_load_real_32_archive(args.full_zarr, args.cycles)` fallback with `load_real490_archive`; remove silent simulator fallback. Verify: test that missing archive → non-zero exit, no report.
- [ ] 2.2 Same for `run_rq2_pretexts.py`, `run_rq3_lst_ssl.py`, `run_rq4_cloud_and_stability.py`, `run_rq7_rq8.py`, `run_data_scarcity.py`. Verify: `grep simulate_490_field_archive scripts/` only appears behind `--source simulated`.
- [ ] 2.3 Real-data paths for `run_rq5_early_detection.py` (injected progressive onset on real held-out cycles) and `run_rq6_xai.py` (IG on real cycles). Verify: both run with `--source real490` on a 20-field smoke subset.
- [ ] 2.4 Route `--source simulated` outputs to `reports/simulated/`; move existing simulator-derived reports there with `data_source: "simulated"` added. Verify: no top-level report lacks `data_source`.

## 3. Splits and proxies

- [ ] 3.1 Build `data/processed/splits_490.json`: LOYO by start year + spatial hold-out by block (20 blocks); store SHA-256. Fix before any test score is read. Verify: no field appears in two spatial folds; hash recorded.
- [ ] 3.2 Proxy availability check: if METRIC zonal CWSI_ET / ETaDaily for 490 fields exist (todo item 1), wire them; otherwise emit `absent`. Verify: unit test that no 32-farm `cwsi_et` reaches a 490 report.

## 4. Runs

- [ ] 4.1 Smoke run of every script on 20 fields (`--max-fields 20`), CPU-throttled. Verify: all reports written with provenance.
- [ ] 4.2 Full real-490 run: RQ1 (LOYO + block hold-out), RQ2, RQ3 (+ no-LST ablation), RQ4, RQ5, RQ6, RQ7–RQ8, data scarcity DS1–DS5. Seeds 42,43,44 for the first pass. Verify: wall time, seeds and n recorded in each JSON.
- [ ] 4.3 Report failures verbatim (any RQ that cannot be answered on real data is recorded as such, with the reason).

## 5. Documentation

- [ ] 5.1 Rewrite `docs/findings/11_rq1_to_rq8_empirical_framework.md` and `12_data_scarcity_diagnostics.md` with real-490 numbers; move simulator tables to a "Superseded — synthetic" appendix.
- [ ] 5.2 Update `docs/findings/08_honest_assessment.md` (data limits now real 490; remove "SSL not run on 490" statements once true).
- [ ] 5.3 `docs/findings/10_remaining_code_results.md`: mark the Rust `32.7×` claim as not reproduced on the user's machine; add keep/remove decision to `todo.md` → Open questions.
- [ ] 5.4 `todo.md`: add this change to In progress; check off when archived.

## 6. Verification

- [ ] 6.1 `pytest tests/test_rq1_to_rq8_framework.py` + new provenance / no-fallback tests pass.
- [ ] 6.2 Spec scenarios checked one by one; archive the change.
