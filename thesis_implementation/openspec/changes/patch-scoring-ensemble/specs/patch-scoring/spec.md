## ADDED Requirements

### Requirement: Ensemble scoring suite

The system SHALL compute, for every patch arm and where applicable for
field-level arms, the component scores s_pred (prediction z²), s_rec
(masked-reconstruction z² averaged over 8 seed-fixed repeated masks), s_lat
(phenophase-binned low-rank Mahalanobis on per-location latents fitted on
train data only), and s_hyb (within-phenophase percentile-rank hybrid), all
standardized with the frozen σ tables; SHALL provide CUSUM and EWMA
persistence accumulation tuned at 1% and 5% field-cycle FAR on validation
data only; and SHALL select component combination and field-aggregation
rule (top-q / median / area-fraction) on the synthetic validation set only,
with the maximum-aggregation rule rejected. Every persistence result SHALL
report detection delay alongside detection rate.

#### Scenario: Components are calibrated and frozen

- **WHEN** the ensemble is evaluated
- **THEN** latent Gaussians, rank statistics, CUSUM κ/h and the chosen
  aggregation rule are frozen with hashes BEFORE the evaluation run, and no
  component is re-fitted on test or injected data

#### Scenario: Persistence trades delay honestly

- **WHEN** a persistent-family injection is detected by CUSUM
- **THEN** the report shows the detection rate AND the median detection
  delay at the same operating point, next to the non-persistence score

### Requirement: Severity-unit and threshold-rule decisions

The system SHALL compute the phenophase-binned residual MAD and the
across-field MAD side by side on the 490-field archive and record the
severity-scale decision (C1) in the findings and model card; SHALL
implement the SHAZAM per-DOY score-climatology threshold (fitted mean +
1.64 SD, circular DOY regression) as a second calibration rule compared at
the same 5% FAR budget (C2) with exactly one rule active in the frozen
configuration; and SHALL report event-FAR with POT declustering (gap ≤ 2)
as the required FAR accounting for every arm (M3).

#### Scenario: Severity unit decided by measurement

- **WHEN** the two severity units are computed
- **THEN** a conversion table per channel is reported and the recorded
  decision names the unit used by the severity ladder, with the reason

#### Scenario: One threshold rule active

- **WHEN** the two calibration rules are compared on dev at equal FAR
- **THEN** exactly one rule is frozen into the operational configuration,
  the comparison table is committed under reports/, and the loser stays
  available as a reported variant only

### Requirement: Scoring-basis labelling and farm-local default

Every component of the ensemble SHALL carry its scoring basis as declared by
`farm-local-anomaly-scoring`: `s_pred`, `s_rec` and `s_lat` are locally
anchored (a farm's residual divided by frozen pooled scales); `s_hyb`
(within-phenophase percentile ranks over the dev population), the
persistence `z_f(t)` robust z against all fields at the same phenophase, the
date-wise cross-field common-mode subtraction and the indicator across-field
z-unit are population-ranked. The selection matrix SHALL include `basis` as
a pre-registered axis, the frozen final configuration SHALL use a farm-local
basis, and any population-ranked component admitted to a report SHALL state
the cross-farm values it reads. `s_hyb` and `z_f(t)` therefore SHALL NOT be
silently combined into the default score.

#### Scenario: Population ranking is visible, not default

- **WHEN** the component selection matrix is pre-registered
- **THEN** it lists each component with its basis tier, farm-local
  combinations are enumerated separately from population-ranked ones, and a
  component whose score depends on other farms' contemporaneous values is
  never the unflagged default

#### Scenario: Cross-farm dependence is stated

- **WHEN** a report contains a population-ranked component
- **THEN** the report names the cross-farm read (percentile reference
  population, cross-field robust z, or date-wise cross-field median) and the
  independence test that the component is expected to fail
