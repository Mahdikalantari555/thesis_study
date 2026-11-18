## ADDED Requirements

### Requirement: Signal-path decomposition diagnostic

The system SHALL provide a read-only diagnostic that, for every injection of
the existing severity sweep on the dev evaluation subset, decomposes the
alarm-signal path into its stages — residual formation (LOO prediction vs
injected value at the onset bin, in σ units), causal offset-correction
subtraction at the onset, per-cell q95 normalization contribution against the
calibrated τ, trailing-window aggregation against τ — and quantifies
prediction absorption at post-onset bins by comparing the prediction against
the injected level and the counterfactual pre-injection level. The diagnostic
SHALL run for `gru_ae_main` and `b1_phasez_causal` on identical injections,
SHALL write per-cell medians + IQR and a stage-attribution decision matrix to
`reports/dev/<run_id>/diagnostic_<model>.json` with full provenance, and
SHALL NOT change any threshold, model, checkpoint, platform artifact or
calibrated target. Every resulting claim SHALL be ladder rung L2 and use the
term "synthetic anomaly"; the scope SHALL be limited to the single-index
absolute-drop family.

#### Scenario: Stage waterfall recorded
- **WHEN** the diagnostic finishes for an arm
- **THEN** each (level × family × index) cell reports the median onset
  residual in σ units, the median offset subtraction, the normalized
  contribution, the path-vs-τ ratio, and the stage-attribution decision
  matrix entry, and the stage-4 detection cross-checks the severity sweep's
  detection rate at the same cells

#### Scenario: Absorption quantified
- **WHEN** a persistent-family injection is diagnosed
- **THEN** the absorption ratio at post-onset bins is reported per cell
  (≈1 = prediction tracks the injected level; ≈0 = prediction stays at the
  counterfactual natural level), using the pre-injection tensor as the
  counterfactual

#### Scenario: Diagnostic changes nothing
- **WHEN** the diagnostic runs
- **THEN** no model, threshold, severity table, checkpoint, sidecar or
  platform artifact is modified, no test split is read, and the frozen
  gru_ae_main sidecar is byte-identical before and after
