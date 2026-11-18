# OpenSpec Proposal — Implement Remaining Code

## Summary
Implement the remaining code that is NOT yet written, to complete the initial
version of the proposal. The existing code (ingest, phenology, baseline, SSL,
maps, Rust placeholder) stays as-is. This change adds missing pieces.

## What is missing (gaps identified)
1. **Per-day anomaly in map**: daily_anomaly.parquet exists but map uses cycle-level. Need per-bin z-score mapped to dates.
2. **Rust backend**: only placeholder crate. Need actual PyO3 binding + parity test.
3. **Ablation without LST**: config exists but not run.
4. **E-INTRA**: pixel/sub-field harvest detection on 32 subset farms.
5. **Patch-level (Phase 3)**: cube.zarr + 3D-CAE + XAI (gated).
6. **Full 490-field run**: currently only 32 fields.
7. **B0/B2/B3 baselines**: only B1 implemented.
8. **GRU-AE (M-A)**: code exists but not tested.
9. **CNN-Mamba (M-C)**: not implemented (needs GPU).

## Scope (this change)
- Per-day anomaly scoring and map integration.
- Rust backend (compile in WSL, parity test).
- Ablation runner (weather on/off, LST on/off).
- E-INTRA on subset.
- B0/B2/B3 baseline implementations.

## Non-goals (future)
- Full 490-field run (separate task, needs compute).
- Patch-level / 3D-CAE (Phase 3).
- CNN-Mamba (needs GPU).