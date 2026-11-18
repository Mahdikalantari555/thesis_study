## ADDED Requirements

### Requirement: Forecast-unit probe (zero-training objective A/B)

The system SHALL provide a read-only probe that evaluates the existing
severity protocol with the model's prediction function replaced by
pre-registered, untrained causal forecasters (persistence, median of the last
≤3 observed bins, robust linear trend on the last 4 observed bins; B1 as the
reference arm), each calibrated ONLY on the clean dev calibration subset
(per-(bin,channel) q95; τ and k at the 5% cycle-level FAR target via the
production calibration rule) and evaluated on the independent evaluation
subset with the identical severity injections. The probe SHALL report per-cell
detection rates with Wilson CIs, event-level FAR, MDM80 per family × index
with censoring allowed, and the stage-1 onset residual in forecast-σ units
(reusing the signal-path decomposition), SHALL evaluate the pre-registered
decision rule verbatim (any untrained arm reaching a non-censored MDM80 ≤ S5
on persistent/ndvi within the FAR budget → the objective/unit remedy is
justified; all arms censored → honest negative), and SHALL NOT retrain, tune
forecaster definitions, change any threshold/model/checkpoint/platform
artifact, or read test cycles. Every claim SHALL be ladder rung L2 and use
the term "synthetic anomaly"; the scope SHALL be limited to the single-index
absolute-drop family.

#### Scenario: Arms compared under identical conditions

- **WHEN** the probe finishes for all arms
- **THEN** each (level × family × index) cell reports per-arm detection
  rates, delays, event-FAR and MDM80 computed on the same evaluation subset,
  same injections and same statistic pipeline, with full provenance
  (git sha, splits hash, subset hash, severity-table hash, wall time)

#### Scenario: Decision rule evaluated

- **WHEN** the sweep completes
- **THEN** the pre-registered rule is applied verbatim and its verdict
  (success with the measured target floor, or honest negative) is recorded
  in finding 21 without goalpost movement or arm tuning

#### Scenario: Probe changes nothing

- **WHEN** the probe runs
- **THEN** no model, threshold, severity table, checkpoint, sidecar or
  platform artifact is modified, no test split is read, and the frozen
  gru_ae_main sidecar is byte-identical before and after
