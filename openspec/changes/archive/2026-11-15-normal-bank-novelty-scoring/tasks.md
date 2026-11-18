# Tasks — normal-bank-novelty-scoring

## 1. Bank module (TDD-first)

- [x] 1.1 `src/ssl_anomaly/monitor/normal_bank.py`: masked encoder embedding extraction (frozen
      model, eval mode), per-(bin, mask-signature-class) bank with robust statistics, pooled
      fallback flag, `bank.json` sidecar (split hash, encoder hash, stats). Unit tests: train-only
      provenance; absent bin handling; class-fallback path; hash stability. DONE: `test_normal_bank.py` 11 tests green (manifest-gated refusal, pooled/global fallback recorded, LOO q95 null, bank.json fields).
- [x] 1.2 Distance scoring: k-NN (k ∈ {1,5}) and per-class robust Mahalanobis; per-cell robust
      normalization of the bank distance to the common null (q95 basis, same convention as the
      reconstruction statistic). Unit tests: injected dev bin scores higher than its clean
      neighbours; causality not required for bank scoring but no future-bin leakage within the
      query window. DONE: level-shifted query scores higher (pinned); encoder causality via `gru_embedding_fn` test (embedding(b) unchanged when future bins change).

## 2. Evaluation integration

- [x] 2.1 `eval_dev.py`: `--scorer {recon_only,bank,fused_max,fused_weighted}`; fusion variants
      recalibrated per variant on clean cycles; full severity sweep + MDM80 + event-level FAR from
      the literature-grounded change for every arm; dev_log row per variant with config hash. DONE: run_id carries the bank variant (sev_bank_knn5/knn1/mahalanobis5); per-variant τ recalibration keeps FAR 0.029.
- [x] 2.2 Comparison run: `recon_only` vs `+bank` vs B1 on the same independent evaluation subset;
      per-family (acute/persistent × ndvi/savi) results with seed spread + Wilson CIs; no test
      access (loader guard tests stay green).

## 3. Decision + docs

- [x] 3.1 Finding 19 (`docs/findings/19_normal_bank_results.md`): does the bank arm lower MDM80 on
      level-shift/relational (persistent) families; honest negative recorded if not. DONE: `docs/findings/19_normal_bank_results.md` (Persian, persian-writing skill) — bank does NOT lower MDM80; measured mechanism documented; +00_index row 19.
- [x] 3.2 Platform-freeze path is a SEPARATE future change, only if the arm wins and the user
      requests adoption; `--no-adoption` default keeps checkpoints/payload byte-identical (test). DONE: `test_normal_bank_platform_untouched.py` green (sidecar/registry/payload digests unchanged through the bank path); no freeze requested.
