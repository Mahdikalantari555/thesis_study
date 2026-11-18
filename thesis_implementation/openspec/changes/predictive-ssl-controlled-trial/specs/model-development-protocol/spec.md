## ADDED Requirements

### Requirement: Predictive SSL controlled trial

The system SHALL train a GRU one-step-ahead predictive arm (`gru_pred`) with
the same architecture trunk, inputs (8 channels + DOY), frozen
normalization, locked splits, parameter budget (≤500k) and seed set
{13, 42, 2026} as `gru_ae_main` — the objective being the ONLY design
difference — and SHALL evaluate the three arms (B1, gru_ae_main, gru_pred)
under identical conditions (same farms, dates, injections, calibration rules)
across four parts: (A) natural-data false-alarm behavior (cycle-level and
event-level FAR, per-field score distribution, temporal stability);
(B) the unchanged severity protocol (S1–S6 × {acute,persistent} × {ndvi,savi},
identical injection sets; event FAR, detection rate with Wilson CIs, MDM80
with ">S6" censoring, AUPRC with prevalence, detection delay); (C) the
absorption experiment (model error before onset, at the first step after
onset, and several steps after, plus the absorption ratio A compared against
the reconstruction arm's measured value); and (D) agreement with independent
remote-sensing stress indicators (CWSI, ETa/ETrF, TVDI when computable from
existing statistics, NDVI/SAVI behavior) reported as corroborating proxy
evidence — never as proof of stress. Thresholds SHALL be calibrated only on
the dev calibration subset at the 5% cycle-level FAR target; test cycles
SHALL be read only by the locked final-test path; training runs SHALL be
handed to the user as exact commands. The pre-registered decision gates (FAR
within budget; better-than-gru_ae_main detection at realistic severities with
MDM80(persistent/ndvi) as the primary; persistent-error persistence; proxy
agreement; generalization across fields/cycles/seeds) SHALL be evaluated
verbatim and SHALL decide whether the predictive objective becomes the main
development path or the anomaly-definition path is taken; the honest-negative
protocol applies (no goalpost movement, no spec-target edits after the run
starts). Every synthetic-anomaly claim SHALL be ladder rung L2; the finding
SHALL answer the owner's question: whether predicting the field's future
natural behavior is more trustworthy than reconstructing its past for finding
fields suspected of stress.

#### Scenario: Trial trains under budget

- **WHEN** the gru_pred arm trains on seeds {13, 42, 2026}
- **THEN** each run stays within the ≤15 min/seed laptop budget and ≤500k
  parameters, uses the train split only, supports --resume and
  progress.jsonl, and is launched by the user from agent-provided commands

#### Scenario: Identical-condition comparison

- **WHEN** the severity protocol runs for the three arms
- **THEN** all arms are scored on the same evaluation subset, same
  injections, same statistic pipeline and same calibration rules, and each
  arm's per-cell detection rates, event-FAR, MDM80, AUPRC and delays are
  reported in one table with Wilson CIs

#### Scenario: Absorption measured

- **WHEN** a persistent-family injection is diagnosed for gru_pred
- **THEN** the error at the three checkpoints (before onset, first step
  after, several steps after) and the absorption ratio A are reported and
  directly compared with gru_ae_main's measured absorption, with the
  adaptive-absorption caveat recorded

#### Scenario: Independent evidence with honest caveats

- **WHEN** part D runs
- **THEN** each indicator's availability is checked first (unavailable =
  `absent`, never synthesized), agreement is reported with confidence
  intervals as corroborating proxy evidence, the shared-input dependence
  structure is stated, and no claim is worded as stress proof or beyond the
  validation ladder

#### Scenario: Decision gates recorded

- **WHEN** all four parts complete
- **THEN** the five pre-registered gates are evaluated verbatim, the
  resulting path decision (predictive objective as main path, or anomaly-
  definition path B on synthetic-detection failure) is recorded in finding
  22, and a failing outcome is recorded as an honest negative without
  goalpost movement or further architecture trials
