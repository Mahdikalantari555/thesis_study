## ADDED Requirements

### Requirement: Gradual temporal shape in the severity protocol

The severity protocol SHALL support a third temporal shape `gradual`: a
linear ramp over D ∈ {3, 4, 6} bins to the severity δ, then held to cycle
end, for families {ndvi, savi} at the existing S1–S6 absolute ladder, using
the sum-preserving red/nir SAVI solver per bin at the bin's partial δ.
Ramp duration and onset SHALL be recorded per injection with the constraint
that the full ramp fits inside the cycle. Every arm report SHALL include
MDM80(gradual) per family with unchanged ">S6" censoring, alongside the
existing acute/persistent columns, and SHALL include the `b0_calendar`
column for the gradual shape (the phenophase-matched climatology is the
expected gradual-case reference). Existing acute/persistent injection sets
and their recorded results SHALL NOT be regenerated.

#### Scenario: Ramp is physically consistent per bin

- **WHEN** a gradual injection is applied to a field-cycle
- **THEN** each ramp bin's NDVI/SAVI drop equals δ·min(1, t/D) exactly, the
  red/nir adjustment uses the same sum-preserving solver at the partial
  magnitude, and the injection hash records D and onset

#### Scenario: Three-shape headline is decidable

- **WHEN** the extended protocol runs for any arm
- **THEN** the report contains one MDM table with acute, persistent and
  gradual columns plus the b0_calendar gradual column, with Wilson CIs and
  prevalence, so the "≥2 of 3 shapes" criterion can be evaluated verbatim

### Requirement: Secondary diagnostic shapes (peak disruption, recovery disruption)

The severity protocol SHALL additionally support, as pre-registered
SECONDARY diagnostic shapes that never enter the primary trial gates:
(a) peak-disruption — peak NDVI/SAVI magnitude reduced by δ, or the peak
plateau shifted later by k ∈ {2, 3} bins (clipped to admitted bins, with
the moved series' covariates consistent); (b) recovery-disruption — after
an acute drop (depth δ over d bins), failure-to-recover (dropped level held
r ∈ {3, 6} bins) or slow-recovery (ramp back at half the natural slope).
Both SHALL run through the unchanged machinery with recorded per-injection
parameters and SHALL be reported as separate diagnostic columns next to the
three primary shapes.

#### Scenario: Secondary shapes stay secondary

- **WHEN** peak or recovery shapes are evaluated for any arm
- **THEN** they appear as diagnostic columns only, the primary-gate tables
  are unchanged, and the pre-registration (recorded before any such result)
  is cited in the report

#### Scenario: Locked trial results preserved

- **WHEN** the extended protocol is adopted
- **THEN** the acute/persistent injection-set hashes and the recorded
  findings 18/21/22 numbers are byte-identical before and after the change
