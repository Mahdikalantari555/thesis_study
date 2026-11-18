# Tasks — reconstruction-invariance-diagnostic

## 1. Diagnostics module (TDD-first)

- [x] 1.1 `src/ssl_anomaly/monitor/diagnostics.py`: signal-path decomposition
      — per-injection stage quantities (onset residual |r| in σ units, offset
      subtraction, normalized contribution vs cell q95, trailing path vs τ,
      SNR₁/SNR₂), absorption ratio A at post-onset bins against the
      counterfactual natural tensor, and stage-wise AUC-PR (raw onset
      residual vs final path). Unit tests with synthetic residual paths:
      onset context clean ⇒ subtraction ≈ 0; injected post-onset context ⇒
      absorption measurable; waterfall ordering preserved.
      (Done: 14 tests in `tests/unit/test_diagnostics.py`, all green;
      `aucpr_stage` added against matched clean-cycle decompositions.)
- [x] 1.2 `scripts/diagnose_reconstruction.py`: runs the decomposition for
      `gru_ae_main` + `b1_phasez_causal` (masked_transformer opt-in) on the
      dev evaluation subset with the EXISTING severity-table injections
      (deterministic, same subset hash), writes
      `reports/dev/<run_id>/diagnostic_<model>.json` (medians + IQR per cell,
      decision-matrix attribution, provenance: seeds, git sha, splits hash,
      subset hash, severity table hash, wall time) + progress.jsonl. Smoke
      mode. No threshold/model/platform writes.
      (Done: B1 z-space replicated exactly — per-BIN season_group keying of
      its own median/scale, prediction ≡ 0 in that space; savi cells
      decompose on the alarm-driving channel among {red, nir} with per-cell
      channel counts recorded; frozen (τ, k, q95) read from the sweep's
      severity metrics of seed 2026; --smoke green; frozen sidecar verified
      byte-identical at exit.)

## 2. Run + analysis

- [x] 2.1 Run the diagnostic on dev (agent-run; read-only eval, ~minutes):
      gru_ae_main + b1; verify stage cross-checks (stage-4 detection equals
      the sweep's detection at the same cells).
      (Done 2026-11-14: 24 cells × 2 arms, n=68 injections per cell,
      rounds=2 → injection set identical to the sweep; crosscheck
      mismatches = 0 for BOTH arms — stage-4 detection reproduces the sweep
      rates exactly; gru_ae 34.9 s / b1 14.9 s on CPU.)
- [x] 2.2 Decision matrix: attribute the dominant loss per (family, index)
      for each arm; quantify absorption on the persistent family.
      (Done: stage1_residual dominant in 24/24 cells for BOTH arms
      (onset residual 0.36–2.68σ vs the ≈3.5–4.9σ per-bin requirement from
      τ·q95); stages 2–4 exonerated (offset subtraction ~0.25σ
      level-independent; persistent path 2.2× acute — no trailing dilution;
      stage-4 AUC-PR 0.91–0.95 > raw-residual 0.82–0.86 at S6); absorption
      on persistent S4–S6: gru_ae α≈0.38–0.50 (partial absorption confirmed)
      vs B1 0.17–0.29 (frozen climatology, field-offset artifact). Finding
      20 records the verdict + the S1–S2 noise-saturation caveat.)

## 3. Finding + gated follow-ups

- [x] 3.1 Finding 20 (`docs/findings/20_reconstruction_invariance.md`,
      Persian, persian-writing skill): hypothesis verdict with measured
      evidence, waterfall table, decision matrix, explicit scope limit
      (single-index drop family only); + 00_index row.
- [x] 3.2 `todo.md`: record gated follow-ups as open questions — path B
      (multivariate/relational + phenology-shape injection families; design
      informed by this diagnostic) and path C (forecasting/predictive-coding
      objective arm) — no implementation in this change.
      (Done: todo.md §D "Follow-up research paths from finding 20" — D1 path
      B, D2 path C, both design-only until explicit user approval.)

## 4. Gates

- [x] 4.1 Unit tests green; existing severity/bank tests untouched and green.
- [x] 4.2 `openspec validate reconstruction-invariance-diagnostic`; no
      platform impact (diagnostic writes only `reports/`).
