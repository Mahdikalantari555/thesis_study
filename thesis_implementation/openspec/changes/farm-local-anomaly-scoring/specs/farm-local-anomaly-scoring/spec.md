## ADDED Requirements

### Requirement: Farm-local versus population-ranked scoring basis

Every scored arm and every score component SHALL declare one of three bases:
**strictly local** (that farm's observations and per-farm constants only),
**locally anchored, globally scaled** (that farm's residual divided by a
frozen global scale), or **population-ranked** (a function of other farms'
contemporaneous values). The declaration SHALL appear as a `basis` column in
every arm table and SHALL be an axis of the pre-registered component
selection matrix. Farm-local bases SHALL be the default for the final
configuration; `s_hyb`, the persistence `z_f(t)` across-field robust z, the
date-wise cross-field common-mode subtraction (already default off) and the
indicator across-field z-unit SHALL all be labelled population-ranked, and
each SHALL be reported as a sensitivity variant with its cross-farm
dependence stated in the report.

#### Scenario: No component hides a cross-farm read

- **WHEN** an arm table or a component selection matrix is published
- **THEN** every row carries its basis tier and every population-ranked
  component states which cross-farm values it reads and why

#### Scenario: The default is farm-local

- **WHEN** the final configuration is frozen
- **THEN** its scoring basis is farm-local (strictly local or locally
  anchored), and any population-ranked component is either excluded or
  reported as a labelled variant beside the frozen result

### Requirement: Per-field standardised scoring arm

The system SHALL provide a per-field scale basis fitted on each farm's OWN
clean residuals — `σ_f = 1.4826 × MAD` per pixel and per field — combined
with the pooled phenophase σ by pre-registered shrinkage
`w_f = n_f/(n_f + κ_σ)` and floored at a pre-registered percentile of the
pooled scale, with the fallback order per-pixel → per-field → pooled and a
min-n threshold recorded BEFORE any run. The arm SHALL be evaluated against
the population basis at the same 5% cycle-FAR budget through the unchanged
alarm machinery on frozen residuals (no retraining), reporting MDM80,
FAR-achieved and the false-alarm field distribution side by side; adoption
SHALL require MDM80 improvement with a paired-bootstrap CI over fields
excluding zero, the FAR budget met, and no increase in alarm concentration —
otherwise the honest negative SHALL be recorded.

#### Scenario: Sparse history cannot masquerade as farm-local

- **WHEN** the per-field tables are frozen
- **THEN** each farm is assigned a history tier (per-pixel / per-field /
  shrunk / pooled-insufficient), the tier counts are reported, and no claim
  about farm-specific detection is made for farms in the pooled fallback
  tier

#### Scenario: Unit change does not become threshold shopping

- **WHEN** the per-field basis is compared with the population basis
- **THEN** every arm's τ is re-calibrated inside the same 5% FAR budget,
  FAR-achieved and MDM80 are reported for both bases, and τ values are never
  compared across bases

### Requirement: Cross-farm independence tests

The scoring path SHALL be tested such that (a) perturbing another farm's
observations leaves a farm-local arm's scores for a given farm unchanged
bitwise, (b) permuting field identities across contemporaneous cycles leaves
farm-local scores unchanged, and (c) a farm-local scoring path touches no
array indexed by a different farm id beyond its documented frozen pooled
constants. Population-ranked arms SHALL record the cross-farm read that
makes them fail test (a).

#### Scenario: Independence is proven, not asserted

- **WHEN** the independence tests run
- **THEN** every farm-local arm passes all three, any arm that fails is
  reclassified as population-ranked in the same report, and the failing test
  is named next to the arm

### Requirement: Farm-level anomaly summary

Every alarm SHALL produce a farm-level summary record reporting the spatial
distribution of the anomaly within the farm — affected pixel count and area
fraction, number of connected components, largest component extent in
pixels and hectares, centroid — together with its severity level, persistence
length, first-alarm bin, phenophase bin and scoring basis. The record SHALL
be written as a per-run artifact and SHALL NOT alter the existing platform
payload.

#### Scenario: The farm output answers distribution, severity, persistence

- **WHEN** an alarm fires
- **THEN** its record states where inside the farm the anomaly is (area
  fraction, components, extent in ha), how severe it is and how long it
  persisted, so the farm-level output is a summary of internal spatial
  information rather than a scalar score

### Requirement: Optional agronomic stratum for scaling

The scoring σ MAY be stratified by pre-registered agronomic strata —
phenophase, phenophase × ratoon number, phenophase × ratoon × variety group —
using the existing `cycles_490.parquet` columns and the existing min-n
fallback, and each setting SHALL be reported through the unchanged severity
protocol so that "should the scale depend on ratoon/variety?" is answered
separately from "should the model see ratoon/variety as an input" (the latter
being the covariate ablation of `patch-full-run-and-ablations`).

#### Scenario: Strata are measured, not assumed

- **WHEN** the strata settings are compared
- **THEN** MDM80 and FAR-achieved are reported per setting with the same
  budget, the fallback coverage per stratum is listed, and the recorded
  decision names the stratum level used by the frozen configuration
