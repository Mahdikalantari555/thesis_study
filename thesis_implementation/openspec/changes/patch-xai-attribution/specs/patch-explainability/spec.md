## ADDED Requirements

### Requirement: Patch-level attribution suite

The system SHALL provide, for frozen patch checkpoints: band occlusion
attribution (occluded values = frozen train medians, never zeros), temporal
bin occlusion aggregated to the sugarcane growth stages, per-pixel spatial
attribution maps (z² and occlusion contribution), and gradient×input dense
attribution; integrated gradients SHALL be reported on a pre-registered
sample of events as a cross-check. All attribution runs SHALL be eval-only
on frozen checkpoints with recorded runtime estimates.

#### Scenario: Occlusion baselines are in-distribution

- **WHEN** a band or bin is occluded
- **THEN** the replacement value is the frozen per-channel train median
  from the normalization artifact, and the attribution map records the
  baseline used

#### Scenario: Temporal windows answer the owner's question

- **WHEN** an alarm's temporal attribution is computed
- **THEN** the effective time windows are reported per bin and aggregated
  to the three agronomic stages, as a table with the event's score
  decomposition

### Requirement: Faithfulness and sanity checks

The system SHALL report deletion/insertion AUC on a pre-registered sample
of alarms, the weight-randomization sanity check, and physiology
sign-concordance (attribution direction consistent with the observed NDVI/
SAVI drop direction); failing sanity checks SHALL be reported verbatim,
never filtered. Attribution outputs SHALL describe score drivers only —
never agronomic causation — with ladder rung L2 wording, and SHALL
distinguish natural-alarm attributions (the deliverable) from
synthetic-event attributions (faithfulness sanity set only).

#### Scenario: Faithfulness is measured, not assumed

- **WHEN** the attribution sample is evaluated
- **THEN** deletion/insertion AUC, randomization sanity and sign
  concordance are reported with the sample definition, and any failure
  appears in the finding
