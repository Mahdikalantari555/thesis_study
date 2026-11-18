## ADDED Requirements

### Requirement: Conditional fallback families (pre-registered)

The system SHALL define two additional injection families, pre-registered
BEFORE any path-C verdict and applied ONLY if both path-C detection gates
fail (gru_pred trial finding 22 AND patch PoC gate G3): (a) relational/
multivariate families — NDVI/SAVI drop without the LST rise the water-stress
relation predicts, and fitted band-relation breaks — with severity in MAD
units of the phenophase-binned relation residual fitted on train cycles
only (frozen + sha); (b) phenology-shape family — green-up delay,
grand-growth compression, early senescence warps relative to the population
phenophase reference, clipped to admitted bins, with the DOY/cycle-age
covariates kept consistent with the warped series. New families SHALL run
through the unchanged severity machinery (per-pixel applier included), the
5% cycle-FAR calibration, MDM censoring and POT event-FAR, with
B0/B1-class references recomputed in the same runs, and the relational
families SHALL report per-pixel localization on patch scorers. Outputs
SHALL keep the anomaly/stress vocabulary ban and the L2 ceiling.

#### Scenario: Pre-registration without shopping

- **WHEN** either path-C trial passes its detection gate
- **THEN** this change is archived unapplied (or machinery-only), recorded
  as pre-registration, and no path-B evaluation run happens

#### Scenario: Families ride the existing machinery

- **WHEN** a relational or phenology-shape injection is evaluated
- **THEN** calibration, FAR budget, censoring and report fields are
  identical to the index-drop protocol, with new injection-set hashes, and
  the pre-registered expectation (deep wins relational, B0 wins gradual)
  is compared against the outcome verbatim
