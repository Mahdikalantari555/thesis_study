## Design — farm-local-anomaly-scoring

### What "farm-local" means precisely (three tiers)

The owner's requirement is not "no shared parameters" — a shared encoder and
shared frozen constants are explicitly allowed. It is that the *assessment*
compares a patch with its own farm's normal behaviour. Three tiers are
therefore defined and every arm must declare one:

1. **Strictly local:** the score uses only that farm's observations (and
   per-farm constants fitted on that farm's own clean cycles).
2. **Locally anchored, globally scaled:** the score uses that farm's
   residual but divides by a *global* frozen scale (pooled phenophase σ).
   This is where `s_pred`/`s_rec`/`s_lat`/`b1`/`b0` currently sit — a
   level-shift in one farm does not change another's score, which satisfies
   the letter of the requirement; it does NOT satisfy the spirit when farms
   naturally differ in variance.
3. **Population-ranked:** the score is a function of other farms'
   contemporaneous values (`s_hyb`, `z_f(t)`, indicator across-field z, the
   common-mode subtraction when enabled).

Tier 2 is the current default and is kept; tier 1 is added as an arm (this
change); tier 3 is demoted to labelled sensitivity variants. The report's
arm table gains a `basis` column populated from this tiering, and the
`patch-scoring-ensemble` selection matrix gets `basis` as one of its axes
(pre-registered before any run, as that change already requires).

### Per-field scale mechanics (`σ_f`)

Reuse, do not invent: `baseline/robust.py:173-180` already fits
`offset_f = n_f/(n_f+κ) · median(x − m_stratum)` per field per band — a
shrinkage level adjustment with `κ = 2.5` default. This change adds the
scale analogue:

```
σ_f(c, role) = 1.4826 · MAD( residual(p, t, c) )  over clean dev cycles of farm f
σ_shrunk     = w_f · σ_f + (1 − w_f) · σ_pooled(c, φ, sensor),  w_f = n_f/(n_f + κ_σ)
```

with `κ_σ` pre-registered (default 3, one clean cycle contributes a third of
the weight). The shrink-to-pooled form makes the "farm-specific but
honest under sparse data" behaviour explicit and is the reason the 223/370
data fact is survivable. For pixels with too few valid bins the per-field
scale falls back to the per-field pooled scale, then to the population σ —
the same hierarchical fallback order `B1PhaseZCausal.fit` already uses for
under-sampled season groups.

Nothing is refitted on injected or test data: residuals come from the
frozen clean-dev scoring pass, the tables are frozen with SHA-256, and the
`--force <reason>` rebuild discipline applies as with the other frozen
artifacts.

### Why this is not threshold-shopping

Per-field standardisation changes the *unit* of every score, which changes
what a fixed τ means. Two guards:

1. τ is re-calibrated inside the same 5% cycle-FAR budget on clean dev
   cycles (the calibration rule is unchanged; only its input scale is).
2. Both bases are reported side by side at the same FAR, and the comparison
   is the *detection* difference (MDM80 + crossing table), never a
   post-hoc threshold choice. The decision rule is pre-registered in this
   change before any run: adopt the farm-local basis only if MDM80 improves
   with a paired-bootstrap CI over fields excluding zero AND the FAR budget
   is met AND the false-alarm field distribution is not more concentrated.

### Independence tests

- `test_other_farm_perturbation`: score farm A's cycles, perturb farm B's
  observations by +2σ, re-score → farm A's farm-local per-pixel and field
  scores identical (bitwise). A population-ranked arm is expected to FAIL
  this test — the test therefore doubles as the classification proof.
- `test_identity_permutation`: permute field ids across contemporaneous
  cycles; farm-local scores must be invariant.
- `test_no_cross_field_read`: instrument the scoring path and assert no
  array indexed by a different farm id is touched; a whitelist covers the
  frozen pooled constants (documented as tier-2 anchors).

### Cold start and history sufficiency

Pre-registered before any run: a farm needs `n_f ≥ 3` clean cycles for a
per-field scale, `n_f ≥ 1` for the shrunk form (with `w_f` making the
sparsity explicit), and `n_f = 0` ⇒ population σ with the farm listed as
`insufficient_history`. The report states the tier counts — the honest
framing of the 223/370 fact — and the finding is written so that a claim
like "farm-specific detection" cannot be made about farms in the fallback
tier.

### Farm-level summary object

Per alarm:
`{field_id, cycle, first_alarm_bin, severity_level (S-ladder), persistence_len,
 affected_pixels, affected_area_frac, n_components, max_component_px,
 max_component_ha, centroid_xy, score, basis_tier, phi_bin}` — the
minimum that answers the owner's "summarise spatial distribution, severity
and persistence". Written as a JSONL per run under `reports/`; the platform
payload is untouched (a later platform change consumes it).

### Strata (ratoon / variety)

`build_stratum_table` already produces `kind_ratoon_no` and
`stratum_full` (`kind_ratoon_no|variety_group`); `B1PhaseZCausal` supports
`use_doy` grouping with a min-n fallback but no ratoon stratum. This change
adds an optional `stratum_level ∈ {phenophase, phenophase×ratoon,
phenophase×ratoon×variety}` with the identical min-n fallback, and reports
MDM80 per setting — a one-flag comparison on the frozen residuals, no
retraining. The corresponding *covariate* cell (ratoon/variety fed to the
patch model as inputs) stays in `patch-full-run-and-ablations` E4, so the
two questions stay separable: "should the scale depend on ratoon?" vs
"should the model see ratoon?".

### Risks

- Per-field scales can overfit short histories (a farm with 2 clean cycles
  and one bad bin gets a tiny σ_f and a huge score). Mitigation: the
  shrinkage form, the pre-registered `n_f` thresholds, a floor
  (`σ_f ≥ floor_pct` percentile of pooled σ, mirroring
  `baseline/robust.py::_compute_floor`), and the tier counts in the report.
- Changing the score unit invalidates cross-arm comparability of τ *values*;
  the report always shows FAR-achieved and MDM80, never bare τ across bases.
- If the farm-local basis does not improve MDM80, the honest negative is
  that shared phenophase scaling is sufficient — a legitimate and useful
  thesis result, and the reason this is pre-registered rather than assumed.
