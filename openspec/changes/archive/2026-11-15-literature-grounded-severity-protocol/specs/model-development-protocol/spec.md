## MODIFIED Requirements

### Requirement: Fixed development metric

The system SHALL evaluate every candidate on dev with: (primary) the **minimum detectable magnitude
(MDM80)** — the lowest severity level of the literature-grounded NDVI/SAVI table achieving detection
rate ≥ 0.80 at a 5 % cycle-level false-alarm rate — computed per duration family (acute, persistent)
and per index (NDVI, SAVI) with median detection delay in days, alongside the equivalent sweep for
`b1_phasez_causal`; (secondary) per-level detection rates with Wilson CIs at the levels
S1…S6 of the verified severity table, **event-level FAR** with consecutive-alarms declustering,
partial-cycle AUC-PR at 25/50/75 %, masked NRMSE, per-type and per-phase breakdown. Injection
magnitudes SHALL be the absolute index drops of the verified severity table (S1 −0.02 … S6 −0.40),
reported additionally as % of the field's own grand-growth median and as multiples of the
across-field MAD; the SAVI axis SHALL repeat the same absolute deltas as a separate family. The MDM
sweep SHALL use clean dev cycles disjoint from the threshold-calibration subset where dev size
permits, and SHALL record the evaluation-subset hash.

#### Scenario: Metric report
- **WHEN** `scripts/eval_dev.py` finishes for a run
- **THEN** it writes `reports/dev/<run_id>/metrics.json` with the MDM sweep, per-level detection
  rates, event-level FAR, all other metrics per seed and their mean and std, and appends a row to
  `reports/dev_log.csv`

#### Scenario: Severity provenance
- **WHEN** the severity table is loaded for injection
- **THEN** every level carries `source`, `verification` and `confidence` fields, and a level whose
  verification is `rejected` cannot be enabled by configuration

#### Scenario: Event declustering
- **WHEN** the alarm path of a clean or injected cycle contains consecutive or near-consecutive
  alarmed bins (gap ≤ 2 bins)
- **THEN** they count as ONE event for the event-level FAR, and alarms inside an
  already-hit injection window are not counted as false events

## ADDED Requirements

### Requirement: Severity-table provenance and honest labeling

The severity table SHALL be stored as configuration with per-level `source` (citation + DOI),
`verification` ∈ {`verified_full_text`, `verified_abstract`, `design_choice`, `rejected`} and
`confidence`; unverified third-party numbers SHALL NOT enter the table; the frozen sidecar SHALL
record the severity-table hash; every resulting claim SHALL be labeled ladder rung L2 and use the
term "synthetic anomaly", never "stress".

#### Scenario: Unverified claim excluded
- **WHEN** a proposal adds a severity level citing a source that cannot be verified against a
  primary source
- **THEN** the review records it as excluded in the verification document and the level is not added

## MODIFIED Requirements

### Requirement: Target and honest outcome

The target SHALL be evaluated on both axes: (a) the original margin — primary detection-rate metric
at least 0.05 above `b1_phasez_causal` with non-overlapping 3-seed ranges, evaluated at the
pre-registered levels where it is evaluable; and (b) `MDM80(main) ≤ MDM80(b1_phasez_causal)` on the
same sweep. If neither is met at plateau, the result SHALL be reported as a finding without changing
the metric, the severity table or the targets.

#### Scenario: Target missed
- **WHEN** the frozen model does not beat B1 by 0.05 (where evaluable) and its MDM80 is not lower
- **THEN** the findings document states this explicitly with the numbers and the ladder rung
