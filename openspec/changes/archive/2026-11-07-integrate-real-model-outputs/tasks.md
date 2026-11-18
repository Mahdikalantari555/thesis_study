# Tasks — Integrate Real Model Outputs into Platform Data Pipeline

## 1. Checkpoint loading & inference
- [x] 1.1 Implement `scripts/load_model_checkpoints.py` — discover `.pt`/`.ckpt` checkpoints under `checkpoints/`, load config + normalization stats sidecar files, return model + normalizer or `None` per model ID
- [x] 1.2 Build per-field cycle input tensor `(phase_bins, bands)` from `stats.zarr` time series (reuse `src/ssl_anomaly/io/` cycle adapter)
- [x] 1.3 Run inference per field per model; write real anomaly scores into observation `scores` map
- [x] 1.4 Add per-score `score_provenance` (`"model"`/`"proxy"`/`"absent"`) and `score_formula_id` to each observation

## 2. Exporter integration
- [x] 2.1 Replace proxy CWSI score block (`export_platform_data.py:193-202`) with checkpoint-backed inference + fallback
- [x] 2.2 When checkpoints missing, emit proxy scores with `"provenance": "proxy"` (do not crash)
- [x] 2.3 Log which models loaded as `"model"` vs `"proxy"` at export time
- [x] 2.4 Re-run exporter; regenerate `platform/src/data/series_khuzestan.json` with real scores

## 3. Contract & parity
- [x] 3.1 Bump contract version to v3 in `scripts/platform_channels.py` and `platform/src/data/channels.ts`
- [x] 3.2 Add score provenance registry fields to both channel registries
- [x] 3.3 Add tests to `tests/unit/test_platform_data_contract.py`: provenance values are `model`|`proxy`|`absent`; when checkpoints present scores are `"model"`, when absent `"proxy"`
- [x] 3.4 Run `tsc --noEmit` → 0 errors; run pytest → all pass

## 4. Docs & commit
- [x] 4.1 Add proxy-vs-real score finding to `docs/platform_bug_audit.md`
- [x] 4.2 Commit all changes on current branch
- [x] 4.3 Verify platform renders real scores with provenance labels

## Deviation notes
- Provenance granularity is per score key inside each observation (`scoreProvenance`/`scoreFormulaId` maps), not a single per-observation flag; stale samples (no acquisition) carry per-key `absent` with null scores/formulas.
- `masked_transformer` stays `proxy` by design: its Lightning `.ckpt`s tokenize (dtime/doy/sensor) inputs, not `(36, 8)` growth cycles — scoring cycles with them would be unfaithful (design.md decision 4).
- 1.2/1.3 reuse `ssl_anomaly.phenology.segment_cycles` + `ssl_anomaly.eval.growth_ssl.MaskedSSL.score` directly rather than the `src/ssl_anomaly/io/` cycle adapter; cycle building lives in `scripts/cycle_inputs.py` and matches the training exporter (`scripts/segment_and_export_cycles_490.py`).
