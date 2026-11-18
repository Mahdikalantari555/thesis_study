## Design — patch-independent-indicators

### Indicator pipeline

Per indicator: per-(field, scene) value → per-bin aggregation (median of
scene values in bin, same 36-bin grid) → phenophase-matched z (2-bin
groups, robust MAD) → exceedance threshold (z ≤ −1.64 for drop-type
indicators; the threshold rule mirrors the frozen C2 decision where
applicable). Availability is checked and recorded BEFORE any agreement
statistic; missing sources are `absent` in every report.

### Physical CWSI

Idso/Jackson form with ERA5 Ta at scene time; Idso's empirical upper/lower
baseline coefficients for the local climate are taken from the literature
table (C3 fallback row-crop analogues where sugarcane coefficients are
unavailable) and recorded per coefficient in the model card with their
source. If neither sugarcane nor defensible analogue baselines exist for a
term, the indicator is `absent`. The heuristic CWSI stays in the platform
but is never used as an agreement indicator under this change.

### Statistics and honesty

- Spearman ρ with 95% CI (field-cycle level, n reported).
- Enrichment: P(indicator exceedance | top-5% model-flagged) ÷
  P(indicator exceedance | all) with Wilson CI.
- Timing: for matched events, the bin offset between model alarm and
  indicator exceedance — distribution reported (lead/coincide/lag), never
  a single average that hides bimodality.
- Agreement is computed per arm; the LST-independence comparison is the
  gate for calling agreement "corroboration" (shared-input indicators
  against an LST-bearing arm are labelled "consistency", not corroboration
  — document §10 caution #1).
- Disagreement is reported as information: the model flags departures from
  the learned population pattern, not water status (AGENTS.md §3; the
  "anomaly = stress" naming ban applies to every output).

### Risks

- The 32-field CWSI_ET subset limits power (n=32; CIs will be wide —
  reported, not hidden).
- ERA5 Ta is gridded reanalysis, not station data: a recorded caveat on
  the physical CWSI.
- Indicator z-scores use across-field spread as their unit (same unit
  question as C1) — the C1 conversion table from `patch-scoring-ensemble`
  is reused so model and indicator z-scores are comparable.
