## ADDED Requirements

### Requirement: Patch-arm independent-indicator agreement

The system SHALL run the availability check FIRST (CWSI_ET 32-field
subset, derived TVDI, new physical CWSI; ETa/ETrF absent → `absent`, never
synthesized), convert every available indicator to phenophase-matched
z-scores on the same 36-bin grid, and report for each patch arm (and gated
field-level arms): Spearman rank correlation with CI, top-5% enrichment
with Wilson CI, and event timing (lead/coincide/lag distribution) against
indicator exceedance. Agreement with an indicator that shares the arm's
inputs (LST/NDVI-derived) SHALL be labelled "consistency" unless the
comparison arm excludes those inputs (E6 LST-off checkpoint); only
input-independent agreement MAY be labelled "corroborating proxy evidence".
No output SHALL name anomalies "stress" or claim L4.

#### Scenario: Availability precedes agreement

- **WHEN** the indicator comparison runs
- **THEN** every indicator's availability (with coverage counts, e.g. the
  32-field CWSI_ET subset) is recorded first, and unavailable indicators
  appear as `absent` in every table

#### Scenario: Timing is a distribution

- **WHEN** matched model/indicator events are compared
- **THEN** the lead/coincide/lag bin-offset distribution is reported, not
  only a mean

### Requirement: External consistency context (weather + neighbors)

For every analyzed alarm the system SHALL report event-level weather
context from the joined ERA5 record (precipitation deficit vs the
historical reference for that farm/period, unusual Tmax, ET0 rise, VPD
rise) and neighbor/regional context (share of adjacent or same-block
fields deviating in the same period), classifying each alarm as
local-with-consistent-weather, regional-common-mode, or
local-unexplained, with candidate non-stress causes (disease, salinity,
pest, management) recorded where the context does not support water
stress. Weather and neighbor context SHALL be descriptive covariates —
never labels — and their unavailability SHALL be `absent`, never
synthesized.

#### Scenario: An alarm carries its context

- **WHEN** a field-cycle alarm is reviewed
- **THEN** the report shows the weather-context flags, the
  neighbor-deviation share, the classification, and the candidate causes —
  e.g., "local anomaly with water-stress-consistent weather; cause
  undetermined"

### Requirement: Physical CWSI indicator

The system SHALL compute Idso/Jackson CWSI (Tc − Ta)/(Tc_upper − Ta_lower)
from per-scene LST and ERA5 air temperature, with every baseline
coefficient cited and recorded in the model card; where defensible
coefficients are unavailable the indicator SHALL be `absent`. The
hard-coded heuristic CWSI SHALL NOT be used as an agreement indicator
under this change.

#### Scenario: Coefficients are traceable

- **WHEN** the physical CWSI is computed
- **THEN** each baseline coefficient's source (sugarcane or recorded
  row-crop analogue) is in the model card, and missing terms yield
  `absent`, not a substituted default

### Requirement: Indicator z-unit is labelled as population-referenced

Indicator z-scores use the across-field spread at the same phenophase as
their unit; they are therefore **population-referenced** measurements, not
farm-local ones. Every report SHALL label them as such, SHALL additionally
report the per-field (farm-own) indicator z where sufficient history exists,
and SHALL NOT use a population-referenced indicator to make a claim about
within-farm abnormality unless the farm-own variant agrees. The labelling
follows the basis tiers of `farm-local-anomaly-scoring`.

#### Scenario: Indicator basis is stated

- **WHEN** indicator agreement is reported for an arm
- **THEN** each indicator row states whether its z-unit is across-field or
  farm-own, the farm-own variant is present where history suffices, and
  disagreement between the two is surfaced rather than averaged away
