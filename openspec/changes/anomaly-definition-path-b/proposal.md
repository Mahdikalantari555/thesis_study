# Change: anomaly-definition-path-b

## Why

todo.md §D1 verbatim: "re-examine the anomaly definition: multivariate/
relational and phenology-shape injection families (the current single-index
absolute-drop family is the finding-20 scope limit). Decided as the FALLBACK
path: taken only if the predictive trial's synthetic-detection gate fails."
Owner feature 14's "ناگهانی، تدریجی و پایدار" covers shapes within the
index-drop family (done in `gradual-severity-shape`); path B changes the
FAMILIES themselves.

**This change is PRE-REGISTERED but CONDITIONAL.** It is written BEFORE any
path-C verdict exists — deliberately, so the fallback is designed without
knowledge of the results (no specification-curve shopping). It SHALL NOT be
applied unless BOTH path-C trials fail their detection gates: the gru_pred
trial (`predictive-ssl-controlled-trial`, finding 22) AND the patch PoC
(`patch-level-controlled-trial`, gate G3). If either passes, this change is
archived unapplied. Note for expectations: the deep-research finding stands
— a deep model's plausible advantage is precisely on **relational**
patterns (e.g., NDVI–LST decoupling = the salinity signature), and such
patterns are spatially coherent, so the patch arms may be their best
detectors; path-B families therefore run through BOTH field-level and patch
scorers.

## What Changes

- **Relational/multivariate injection family** — anomalies defined by
  breaking inter-variable relations, not single-index magnitudes:
  (a) NDVI/SAVI drop WITHOUT the LST rise a water-stress relation predicts
  (the decoupling signature); (b) band-relation breaks (e.g., swir1-vs-NDVI
  dryness relation violated). Severity anchored in MAD units of the
  relation residual (the C1 conversion table supplies the unit), not raw δ.
- **Phenology-shape injection family** — per-field temporal warping vs the
  population's phenophase reference: delayed green-up by k bins, compressed
  grand-growth, early senescence — shapes a magnitude-only proxy rule
  CANNOT flag (AGENTS.md §3's phase-vs-magnitude distinction) and that only
  phase-aware checkpoint models can detect; severity = shape deviation in
  bins/MAD of the stage-timing distribution.
- **Same machinery, calibration and FAR budgets** — new families ride the
  existing severity/eval pipeline (per-pixel patch applier included) with
  new injection-set hashes; the 5% cycle-FAR calibration and MDM censoring
  semantics unchanged; B0/B1-class references recomputed in the same runs.
- **Explicit non-goals:** no adoption decision inside this change (the
  verdict is a finding + owner decision); no Normal-Bank re-development
  (standing prohibition); no foundation models; no platform changes.
