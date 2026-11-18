## ADDED Requirements

### Requirement: Representation ladder comparison

The system SHALL compare spatial representations under an equal-budget
protocol — R0 zonal mean (reused results, plus an R0-subset re-score on the
identical evaluation panel), R0.5 zonal distribution statistics, R1
full-field 32×32 patch, R2 sub-crop 16×16 with field-level aggregation, R3
multi-scale (multi-dilation stem; two-scale fusion only behind its
pre-registered trigger) — holding objective, bins, channels, seeds,
injection sets, σ tables and alarm machinery constant, with param counts
reported per representation and >±20% capacity deviation flagged. All
representations SHALL be evaluated on the same farms and cycles through the
unchanged severity protocol (3 shapes + secondary shapes),
pixel-localization on partial-footprint injections, and the benchmark
metrics (epoch time, peak RAM, throughput). Any arm whose zonal baseline
was trained or calibrated on a different field set than the patch arms
SHALL be reported with that training-set-size confound stated explicitly
next to its row. The study SHALL publish ONE transparent table + figure
across the four dimensions (detection quality, spatial sensitivity,
temporal consistency, computational efficiency) as finding 24 (Persian),
with every row labelled farm-local or population-ranked, and a 64×64 window
SHALL be excluded from training by default with the geometry memo (median
field side 16.7 px, max 19.6 px) documented, available only behind an
explicit flag.

#### Scenario: Equal budget holds

- **WHEN** two representations are compared
- **THEN** they share farms, cycles, dates, injections, seeds and
  calibration, their param counts appear in the same table, and any
  >±20% capacity deviation is flagged next to the result

#### Scenario: Reused baselines are paired honestly

- **WHEN** an existing R0 result is reused rather than re-run
- **THEN** the row states the field set it was trained and calibrated on,
  the R0-subset re-score on the shared evaluation panel is reported
  alongside, and any residual training-set-size confound is named in the
  table — never left for the reader to infer

#### Scenario: Scale decisions are measured, not assumed

- **WHEN** the study begins
- **THEN** the 64×64 exclusion memo and the lazy-vs-materialized data-access
  decision are recorded from measurements (geometry + the benchmark JSON)
  before any training run

### Requirement: Sub-crop representation mechanics

R2 crops SHALL lie fully inside the field polygon (in-field fraction 1.0),
drawn as fixed seed-hashed sets recorded in the run manifest (per-epoch
resampling = flag, default off); fields admitting fewer than K complete
windows SHALL use a recorded reduced K and fields with no valid window a
recorded padded fallback; field-level scores SHALL aggregate per-crop
scores via top-q mean (primary) and majority vote (comparison variant) into
the unchanged alarm machinery.

#### Scenario: Crop sets are reproducible

- **WHEN** R2 trains or evaluates
- **THEN** the crop sets are byte-identical across runs from the manifest
  hash, and every reduced-K or padded-fallback field is listed in the
  report

### Requirement: Pre-registered adoption rule

A representation SHALL replace R1 only if its MDM80 at 5% cycle-FAR improves
with a paired-bootstrap CI over fields excluding zero at ≤2× R1 compute;
the multi-scale variant SHALL be adopted only if it beats the best single-
scale representation with a CI excluding zero. If no representation beats
R1, the honest negative SHALL be recorded with the full table and R1
continues as the patch representation.

#### Scenario: Adoption is decided verbatim

- **WHEN** the comparison completes
- **THEN** the pre-registered rule is applied to the committed table, the
  winner (or honest negative) is named in finding 24, and the decision
  flows into the final-architecture criterion

### Requirement: Zonal distribution-statistics representation (R0.5)

The system SHALL provide a zonal distribution-statistics representation
for every compared arm's evaluation cycle: per farm per date, the channels
`{median, std, p10, iqr}` per band aggregated onto the same 36-bin grid,
read from the EXISTING `stats.zarr` (`mean/std/p10/p25/p75/p90/iqr` are
already stored for all 490 fields × 538 dates; only `median` has consumers
today) with NO new extraction, NO training and NO GPU use. It SHALL be
scored through the existing rule-based paths (`b1`-style
phenophase-conditioned robust z and the `b0_calendar` DOY reference) plus a
`p10`-only path-max variant, and SHALL be evaluated through the unchanged
severity protocol with the same injections, calibration and alarm
machinery. The three-way structure the study exists to answer —
Zonal Mean / Zonal Distribution Statistics / Patch-based — SHALL be
reported as three named rows (R0, R0.5, R1) in the single comparison
table.

#### Scenario: The middle rung costs no new data

- **WHEN** R0.5 is constructed
- **THEN** its inputs come from the existing frozen `stats.zarr` statistics
  and the locked cycle grid, no extraction or training run is launched, and
  the channel list used per arm is recorded in the run manifest

#### Scenario: Lower quantiles answer their own question

- **WHEN** the prompt's "can lower distribution quantiles reveal
  deterioration hidden by the mean" is evaluated
- **THEN** the `p10`-only path-max result is reported separately from the
  joint median+std+p10+iqr score, so a negative or positive answer cannot be
  diluted by the multivariate aggregate

#### Scenario: A rule-based win is a legitimate outcome

- **WHEN** R0.5 matches or beats R1 within the adoption rule's CI criterion
- **THEN** the table states it plainly as the honest negative of the patch
  program (a patch model is not required for localization) and the decision
  flows to the final-architecture criterion without goalpost movement

### Requirement: Heterogeneity and noise disambiguation battery

The system SHALL separate genuine localized anomalies from natural
within-field heterogeneity, phenological differences and data noise by
reporting, for every representation: (a) a **static-pattern control** — a
per-field per-pixel clean climatology over that field's own clean cycles
used as an alternative per-pixel normalizer, with arms whose MDM80 collapses
under it identified as chronic-heterogeneity detectors; (b) a
**spatially-i.i.d. white-noise null** — the same δ ladder applied to a
random in-field pixel subset of matched mean footprint, reported as a
diagnostic MDM80 that never enters a severity gate, whose gap against the
coherent-footprint result is the causal evidence that a patch advantage
comes from spatial coherence rather than noise averaging; and (c) a
**per-pixel alarm-frequency diagnostic** on clean dev cycles (share of
pixels alarming in most bins, Jaccard overlap of the top-q pixel sets
between successive cycles, entropy of the per-pixel alarm distribution).
Phenology is controlled by the cycle-bin grid, phenophase-binned σ, the
DOY/cycle-age covariates and the mandatory `b0_calendar` reference.

#### Scenario: Chronic patches cannot masquerade as events

- **WHEN** the static-pattern control is applied
- **THEN** the arm's MDM80 under the field's own chronic-offset normalizer
  is reported next to the population-σ value, and a large drop is written
  up as a chronic-heterogeneity finding rather than an anomaly result

#### Scenario: Noise null is diagnostic only

- **WHEN** white-noise injections are evaluated
- **THEN** their MDM80 is reported as a diagnostic column, is excluded from
  every severity gate and censoring decision, and the coherent-minus-white
  gap is stated in the finding

#### Scenario: Chronicity is measured, not assumed

- **WHEN** clean dev cycles are scored for any representation
- **THEN** the per-pixel alarm frequency and the successive-cycle top-q
  pixel-set overlap are reported, so a detector that flags the same pixels
  every cycle is identified as reporting heterogeneity

### Requirement: Extent axis and detectability crossing

The system SHALL sweep the injection footprint over {0.1, 0.3, 0.6, 1.0}
through the existing patch applier on frozen checkpoints (no retraining and
no recalibration), and SHALL report, per representation and per extent, the
MDM80 and the pixel-localization AUPRC; and SHALL report per severity level
a four-cell detectability crossing table — detected by the patch
representation only, by the zonal representation only, by both, by neither
— with Wilson confidence intervals and a paired test over fields.

#### Scenario: Extent changes detectability

- **WHEN** the footprint is swept for a patch arm and a zonal arm
- **THEN** MDM80 and localization AUPRC are tabulated per extent, showing
  whether detectability decays with extent for one representation while
  staying flat for the other

#### Scenario: The localized-anomaly claim is paired

- **WHEN** the crossing table is committed
- **THEN** each severity level has counts for patch-only / zonal-only /
  both / neither detections over the same injections and fields, so the
  claim "search patches detect what farm-level means cannot" rests on
  paired per-injection evidence, not on two aggregate MDM80 numbers

### Requirement: Spatial resolution is a reported quantity

Every row of the comparison table SHALL state its spatial support in metres
and hectares and the smallest anomaly it can resolve, using the fixed
arithmetic 30 m GSD ⇒ 1 px = 0.09 ha, a 16×16 crop = 480 m ≈ 23 ha, and
the measured field-size distribution (median side 16.7 px ≈ 25 ha); and
finding 24 SHALL carry the Landsat-30-m interpretation limit and the
LST-resampled-from-~100-m caveat rather than leaving them in a design-risk
note.

#### Scenario: Localized means measured, not suggested

- **WHEN** the comparison table is published
- **THEN** each representation's spatial support in ha and its minimum
  resolvable anomaly are in the table, and the finding states plainly that
  a 30 m pixel bounds every localization claim regardless of model

A reusable benchmark module SHALL measure, before any training run: Zarr
lazy random-read throughput, materialized preload time and resident RAM,
per-representation epoch forward/backward throughput, CPU utilization,
peak RAM and disk I/O, and SHALL emit per-epoch and total runtime estimates
that gate the user-run training commands. Results SHALL be committed as a
JSON artifact with the recorded data-access decision.

#### Scenario: Estimates precede training

- **WHEN** a representation's training is handed to the user
- **THEN** its per-epoch and total estimates come from the measured
  benchmark artifact, not assumptions, and the lazy-vs-materialized decision
  cites the same artifact
