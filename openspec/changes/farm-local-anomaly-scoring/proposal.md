# Change: farm-local-anomaly-scoring

## Why

Owner requirement (2026-11-16, "Farm-Internal Spatial Anomaly Detection",
audited in `docs/audits/spatial_prompts_vs_openspec_2026-11-16.md`, gaps
GAP-9/GAP-10): **the final anomaly assessment must be farm-specific.** Each
patch must be compared with what is normal for *the same farm* at a
comparable phenological stage — not with other farms.

The current program answers a different question. Every patch score is
divided by a σ pooled over dev field-cycles (channel × 2-bin phenophase ×
sensor), and `patch-scoring-ensemble` then adds three **unconditional**
cross-field normalisations:

1. `s_hyb` — the mean of within-phenophase **percentile ranks over the dev
   population** (`proposal.md` §Hybrid rank score);
2. persistence `z_f(t)` — "robust z of the field score **against all fields
   at the same phenophase**";
3. (and, in the validation layer, `patch-independent-indicators` uses
   **across-field spread** as the indicator z-unit).

Only the date-wise common-mode subtraction is correctly default-off. So a
farm's score currently depends on other farms' values in the same period,
which is exactly the comparison the owner forbids, and the conflict is
nowhere labelled.

There is also a hard data fact the program must state rather than
implicitly absorb: **370 fields have ≥1 non-censored cycle but only 223
have ≥2** (`docs/findings/01`). A strictly per-farm distribution is
therefore impossible for most farms — partial pooling is forced, not
chosen. That compromise belongs in the specification, not in a reviewer's
footnotes.

## What Changes

- **Arm classification (the missing label).** Every scored arm and every
  score component SHALL be classified as **farm-local** (the score of a
  farm is a function of that farm's own observations and frozen constants
  only) or **population-ranked** (the score uses other farms'
  contemporaneous values): `s_pred`, `s_rec`, `s_lat`, per-pixel z, and the
  `b1`/`b0` robust-z paths are farm-local *up to* shared frozen constants;
  `s_hyb`, `z_f(t)` and the indicator across-field z are population-ranked.
  Farm-local SHALL be the default for the final configuration; every
  population-ranked component SHALL be a labelled sensitivity variant with
  its cross-farm dependence stated in the report.
- **Per-field standardisation arm (`σ_f`).** A second scoring basis:
  `σ_f(role) = 1.4826 × MAD` of **that farm's own** clean residuals (per
  pixel where the field has enough clean cycles, per field otherwise), with
  hierarchical fallback to the pooled phenophase σ when a farm is
  under-sampled. Modelled directly on the *existing, already-implemented*
  shrinkage mechanism in `baseline/robust.py:173`
  (`offset_f = n_f/(n_f+κ) · median(x − m_stratum)`), extended from a level
  offset to a scale. Reported as an arm-level A/B against the population
  basis, at the same 5% cycle-FAR budget, through the unchanged alarm
  machinery — no retraining (the residuals are already computed).
- **Independence tests (fail-closed).** (a) Perturbing **other farms'**
  observations SHALL leave a farm-local score unchanged; (b) the same for
  permuting farm identity across contemporaneous cycles; (c) a farm-local
  arm SHALL NOT read any cross-field array at scoring time (asserted by a
  spy/instrumentation test). A population-ranked arm SHALL document the
  cross-farm read in its report row.
- **Cold-start / history-sufficiency rule.** The minimum clean cycles for a
  per-field scale (pre-registered), the fallback order (per-pixel → per-field
  → pooled phenophase), and the reporting of how many farms land in each
  tier — so a "farm-local" claim never rests on one or two cycles.
- **Agronomic strata as an optional scoring stratum.** `kind`, `ratoon_no`
  and `variety_group` already exist in `cycles_490.parquet` and are already
  used as strata by `baseline/robust.py:96-106`, but are absent from every
  patch/GRU covariate set. This change adds them as an *optional* σ-stratum
  level (ratoon × phenophase) with the standard fallback, and hands the
  covariate-ablation cell to `patch-full-run-and-ablations` E4 — because
  variety, crop age and planting date are precisely the between-farm
  differences the owner's prompt names.
- **Farm-level anomaly summary object.** Per alarm, a record of the spatial
  distribution of the anomaly inside the farm — affected area fraction,
  number of connected components, largest component extent in pixels and
  hectares, centroid, severity level, persistence length — so the farm-level
  output summarises *spatial distribution, severity and persistence* rather
  than only a scalar score.
- **Explicit non-goals:** no architecture change; no retraining required for
  the A/B (residuals are frozen); no change to the locked splits, the
  severity protocol, the MDM80 censoring semantics or the platform; no
  adoption decision inside this change beyond the pre-registered rule (the
  verdict is a finding + the final-architecture decision in
  `patch-full-run-and-ablations`).

## Impact

- Affected specs: new capability `farm-local-anomaly-scoring`; one added
  requirement each in `patch-scoring` (label + default) and
  `model-development-protocol` (indicator z-unit labelling).
- Affected code: `src/ssl_anomaly/monitor/patch_scores.py` (new module from
  `patch-scoring-ensemble`, extended here), `monitor/scoring.py` (σ-table
  selection + fallback), `monitor/models.py` (`B1PhaseZCausal` optional
  ratoon stratum), a frozen-artifact builder for the per-field tables,
  `scripts/eval_dev.py` (arm names `*_farmlocal`).
- NOT affected: locked splits/holdout manifest, severity table, injection
  sets, B1/B0 numerical results, frozen checkpoints, platform payload.

## Sequencing

Runs after `patch-scoring-ensemble` (it extends that change's component set)
and before `patch-full-run-and-ablations`' final decision, so the winner is
frozen on a farm-local basis. It is independent of
`compare-spatial-representation-strategies` except for the table label that
change consumes.
