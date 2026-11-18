## Design — anomaly-definition-path-b

### Conditionality mechanism

The change carries a gate file (trial_gates pattern): applying its tasks
beyond §1 (machinery, which is verdict-independent) requires the recorded
failure of BOTH path-C detection gates. §1 (family definitions + injection
appliers + unit tests) MAY be built early because it touches no arm and no
report; §2 (evaluation runs) is hard-gated. If either path-C trial passes,
the change is archived with §1 unexecuted or executed-but-unused, recorded
as pre-registration.

### Relational family mechanics

(a) NDVI/SAVI drop δ with LST held (or lowered by a small ε ≤ 0.5 K to keep
the joint perturbation physical): the NDVI–LST water-stress relation is
broken while both marginals stay in-distribution. (b) band-relation breaks:
perturb one band (e.g., swir1) by δ_swir along the direction that violates
the fitted swir1|NDVI relation, keeping NDVI fixed. The relation model is a
phenophase-binned robust linear fit on TRAIN cycles only (frozen + sha);
severity levels = {1, 2, 4, 6} × MAD of the relation residual (mapped to
the S1–S6 naming for table compatibility, labelled relational).

### Phenology-shape family mechanics

Warping: take the field-cycle's per-bin series and shift/compress stages
relative to the population reference (median green-up onset, grand-growth
span from `cycles_490` + phenology stage bins). Implementations: green-up
delay k ∈ {2, 4} bins; grand-growth compression by 20/40%; early senescence
k bins. The warp moves values across bins (so the DOY/cycle-age covariates
stay consistent with the warped reality — the model must detect the shape,
not a timestamp inconsistency); applied at field level and per-pixel.

### Evaluation design (gated)

Same protocol skeleton: 5% cycle-FAR calibration on clean dev, MDM per
family with censoring, event-FAR (POT), AUPRC with prevalence, delay; all
arms in one table; the relational families additionally report per-pixel
localization on the patch scorers (coherence is their mechanism). The
pre-registered expectation — deep arms win on relational, B0 wins on
gradual index drops — is written down BEFORE the runs; confirming or
refuting it is the finding.

### Risks

- Relation-residual severity units are a new scale — the C1 conversion
  table keeps them interpretable next to the index-drop ladder.
- Warping can interact with the cycle segmentation (a large green-up delay
  may push bins outside the admitted cycle window) — warps are clipped to
  admitted bins and recorded.
- The biggest risk is interpretive: path-B anomalies are, by construction,
  "departures from learned relations/shapes", NOT validated stress — the
  outputs keep the anomaly/stress vocabulary ban and L2 ceiling.
