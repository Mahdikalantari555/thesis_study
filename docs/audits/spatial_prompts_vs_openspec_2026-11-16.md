# Audit — the two spatial research prompts vs the written OpenSpec changes

Date: 2026-11-16 · Branch `arena/bfeec0a4-thesis-implementation` (base `8f84bbc`)
Scope: all 13 active changes in `openspec/changes/` (all `PROPOSED`, `.openspec.yaml`
created 2026-11-15), the 8 synced specs in `openspec/specs/`, and the existing code
they build on (`src/ssl_anomaly/io/`, `monitor/`, `baseline/`, `scripts/extract_stats.py`).

**Status legend.** ✅ addressed (a change owns it, spec-level) · 🟡 addressed but
weaker/narrower than the prompt · 🔴 not addressed (gap) · ⚪ addressed by decision,
recorded as a deliberate deviation.

---

## 0. Headline answers

1. **"Considered?" — yes, substantially.** Prompt 1 is the direct ancestor of
   `compare-spatial-representation-strategies`; prompt 2 is distributed across
   `patch-data-pipeline`, `patch-level-controlled-trial`, `patch-scoring-ensemble`,
   `training-holdout-invariant` and `patch-independent-indicators`. Most of both
   prompts is spec'd, not just discussed in prose.
2. **"Applied?" — no.** Every one of the 13 changes is `PROPOSED` with **all tasks
   unchecked**; none of the code exists yet (`scripts/extract_patches.py`,
   `scripts/train_patch.py`, `scripts/bench_spatial_representations.py`,
   `src/ssl_anomaly/io/patches.py`, `src/ssl_anomaly/models/patch_cnn_gru.py`,
   `src/ssl_anomaly/monitor/holdout.py` are absent). "Applied" so far = spec'd and
   pre-registered only.
3. **Two structural gaps matter most.**
   - The **"Spatial Statistics" middle arm** of prompt 1 does not exist as an arm,
     even though its data already sits unused in `stats.zarr` (`std, p10, p25, p75,
     p90, iqr` are computed by `scripts/extract_stats.py`; only `median` is read by
     `monitor/inputs.py`). The prompt's three-way comparison is implemented as a
     *patch/sub-crop/multi-scale ladder* with R0 reused — the intermediate
     representation was dropped.
   - Prompt 2's **"compare each patch against the same farm's own history"** is only
     approximated: scoring uses a *population* σ conditioned on phenophase × sensor.
     There is no per-farm climatology, and `patch-scoring-ensemble` actively adds four
     **cross-field** normalisations (percentile-rank hybrid, `z_f(t)` against all
     fields at the same phenophase, date-wise common-mode subtraction,
     across-field MAD). Three of the four are not gated, and none has an
     independence test.
4. Several smaller but concrete gaps: no **farm-boundary spatial invariance test**,
   no **static within-field heterogeneity control**, no **spatial-extent sweep**
   (only footprint 1.0 / 0.3), no **variety/ratoon strata** in the patch covariates
   even though `cycles_490.parquet` carries them, and the **R0 "reuse, never re-run"**
   rule breaks equal-condition pairing (R0 was never scored on the PoC subset).

---

## 1. Prompt 1 — "Evaluating the Impact of Spatial Aggregation on Anomaly Detection"

Owner change: `compare-spatial-representation-strategies` (design.md, proposal.md,
`specs/spatial-representation/spec.md`), with the patch arm from
`patch-level-controlled-trial` and the decision sink in
`patch-full-run-and-ablations`.

| # | Prompt requirement | Where it is specified | Status |
|---|---|---|---|
| 1.1 | Design a controlled comparative experiment on spatial representation | `compare-spatial-representation-strategies` proposal §What Changes; spec req. "Representation ladder comparison" | ✅ |
| 1.2 | **Arm 1 — Zonal Mean** (current approach) | R0 = existing arms `b0_calendar`, `b1`, `b3`, `gru_ae_main`, `gru_pred`; "results REUSED, never re-run" | ✅ (see 🟡 2.1 below on reuse) |
| 1.3 | **Arm 2 — Spatial Statistics** (std, quantiles, other distribution stats) | *nowhere* | 🔴 **GAP-1** |
| 1.4 | **Arm 3 — Patch-based** (patches keep their own temporal series) | R1 = full-field 32×32 `patch_cnn_gru`, `patch-data-pipeline` store (F, cycles, 36, 8, 32, 32) | ✅ |
| 1.5 | Start from ~20–30 representative farms | PoC subset ≈100 hashed train fields, 38-field dev eval panel (`patch-level-controlled-trial` design §Subset); R2/R3 screened at single seed on that subset | 🟡 **GAP-2** (superset in size, but no bounded 20–30-farm panel is defined, and R0 reuse means the panel is not shared) |
| 1.6 | Same observations and comparable periods for all representations | Equal-budget protocol: same farms, cycles, dates, injections, seeds {13,42,2026}, σ tables, alarm machinery, "paired" | 🟡 **GAP-2** (holds for R1/R2/R3; R0 comes from earlier runs on all train fields) |
| 1.7 | Keep the comparison fair, control other variables | Capacity-matched param counts in one table, >±20% flagged; same objective/bins/channels; one factor per cell | ✅ |
| 1.8 | Do not assume patch will win | Pre-registered adoption rule (CI excluding zero at ≤2× compute, honest negative), non-goals, "no goalpost movement" | ✅ |
| 1.9 | Distinguish genuine spatial anomaly from **natural spatial heterogeneity** | Not tested. Closest: geometry memo, risk note that crop aggregation can wash out signals, localization AUPRC | 🔴 **GAP-3** (no static within-field heterogeneity control) |
| 1.10 | …from **phenological differences** | 36-bin cycle grid (not calendar), phenophase-binned σ (2-bin groups), DOY + cycle-age covariates, `b0_calendar` phenophase-matched column mandatory on gradual | ✅ |
| 1.11 | …from **data noise** | QA masking reused, per-pixel validity mask, NaN-as-absent, no zero-fill, trimmed loss, top-20% aggregation, coherence argument (pixel noise independent, injections coherent) | 🟡 **GAP-3** (no *spatially i.i.d. noise* null / permutation test proving the gain is coherence-driven) |
| 1.12 | Consider Landsat 30 m when interpreting localized patterns | Geometry memo (median field side 16.7 px, p90 17.0, max 19.6; 64×64 excluded), never resample, LST@30m-from-100m caveat in `patch-data-pipeline` design risks | 🟡 **GAP-4** (recorded as a design risk, not as a required report field in finding 24 / the comparison spec) |
| 1.13 | Can localized anomalies be detected in patches but **not** in zonal means? | G3 (subset floor vs best of {b1, gru_ae_main}), G4 (CNN vs `patch_pixelwise`), pixel-localization AUPRC at footprint 0.3 | 🟡 **GAP-5** (aggregate MDM80 + paired bootstrap over fields; no per-injection detectability *crossing* table "detected by patch, missed by zonal") |
| 1.14 | Does **spatial variability** add information? | — | 🔴 **GAP-1** (this is the Spatial-Statistics arm) |
| 1.15 | Can **lower quantiles** reveal deterioration hidden by the mean? | — | 🔴 **GAP-1** (`p10`/`p25` exist in `stats.zarr`, zero consumers) |
| 1.16 | How do spatial **extent** and **persistence** affect detectability? | Persistence: 3 temporal shapes + `persistent` family + CUSUM (`patch-scoring-ensemble`). Extent: footprint ∈ {1.0, 0.3} only | 🟡 **GAP-6** (extent is a 2-point probe, not a swept axis: no 0.1/0.3/0.6/1.0 × spatial-shape (blob vs stripe vs edge) design) |
| 1.17 | Do detected anomalies produce more **meaningful** patterns? | Spatial attribution maps + faithfulness (`patch-xai-attribution`), enrichment/agreement (`patch-independent-indicators`) | 🟡 (judgment-level; acceptable, but "meaningfulness" is not an operational metric in the comparison table) |
| 1.18 | Consistency with **independent indicators** | `patch-independent-indicators` (physical Idso/Jackson CWSI, TVDI, ETa/ETrF availability-checked, weather + neighbour context), part-D of the predictive trial | ✅ |
| 1.19 | Experimental assessment, **not** a new implementation | Adoption rule + ONE table/figure + finding 24; "no new injection families, no platform changes" | ✅ |
| 1.20 | Deliverable 1 — is Zonal Mean suppressing signal? | G3/G4 + localization AUPRC + adoption rule | ✅ (modulo GAP-5) |
| 1.21 | Deliverable 2 — are **spatial statistics a useful intermediate**? | — | 🔴 **GAP-1** |
| 1.22 | Deliverable 3 — is Patch-based a meaningful improvement? | Adoption rule + `patch-full-run-and-ablations` pre-registered final criterion | ✅ |
| 1.23 | Deliverable 4 — which representation for the final pipeline? | `patch-full-run-and-ablations` §Final architecture decision (pre-registered, frozen winner, honest negative) | ✅ |
| 1.24 | Inspect the existing data structure/pipeline first | Measured geometry memo, one-time lazy-vs-materialized benchmark deciding data access, `--estimate-runtime` gating handover | ✅ |
| 1.25 | No whole-model redesign / no unnecessary complexity | Explicit non-goals; no ConvGRU/VideoMAE/JEPA/foundation models; two-scale fusion behind a trigger | ✅ |

### Prompt-1 gaps in detail

**GAP-1 — the "Spatial Statistics" arm is missing (highest priority, cheap to fix).**
The prompt asks for three representations; the change ladder is
R0 zonal → R1 patch-32 → R2 sub-crop-16 → R3 multi-scale, i.e. *four* points, all of
which except R0 preserve spatial structure. The distribution-statistics middle ground
(`std`, `p10`, `p25`, `iqr` per field per date — already on disk for all 490 fields ×
538 dates × 7 bands) has no arm, no spec requirement and no task. Consequences:
- Deliverable 2 of the prompt ("whether spatial statistics provide a useful
  intermediate solution") cannot be answered.
- 1.14 and 1.15 (spatial variability; lower quantiles) are unanswerable.
- The ladder loses its cheapest rung — an arm that needs **no new store, no training,
  and no GPU**, which is exactly the kind of arm a thesis wants before arguing for a
  32×32 patch model.

Minimal fix: add **R0.5 "zonal distribution statistics"** to
`compare-spatial-representation-strategies` — the existing `B1PhaseZCausal` / `b1`
scoring path fed with extra channels `{std, p10, iqr}` read from `stats.zarr`
(`reader.get_stat` already supports it; `_validate_schema` must accept the extra
stats), scored through the unchanged severity protocol. One spec requirement + two
tasks; zero new data.

**GAP-2 — panel and pairing.** The prompt's 20–30 farms is not reproduced (the PoC
uses ~100 train fields / 38 dev fields, which is defensible as a superset), but
"R0 reused, never re-run" conflicts with "same farms, cycles and conditions": the
zonal arms were trained/evaluated on **all** train fields, the patch arms on the
subset, so the representation effect is confounded with training-set size. Fix:
require a *subset-restricted* R0 comparison (the existing arms scored on exactly the
38 dev fields with the identical injection sets and σ machinery) and state the
training-set-size confound explicitly in the table.

**GAP-3 — heterogeneity vs anomaly vs noise.** The prompt explicitly asks to
"distinguish genuine spatial anomalies from natural spatial heterogeneity". Nothing
in the program defines the nuisance term. Missing pieces:
- a **static-pattern control**: per-pixel per-field clean climatology (or the
  field's own long-run spatial pattern) as a baseline image, so that a "localized
  anomaly" means *departure from the field's own persistent spatial structure* —
  otherwise the detector's top-20% aggregation will systematically fire on the same
  chronically-low patches (soil/management zones), which is exactly the failure the
  prompt warns about;
- a **spatially-i.i.d. noise null** (inject the same δ as white noise instead of a
  coherent footprint): if the patch arm's advantage survives only coherent
  injections, that is the evidence that the gain is spatial signal and not noise
  averaging;
- an explicit **"same patch flags every cycle?" persistence-of-rank** diagnostic
  (per-pixel alarm frequency) — cheap, and directly separates chronic heterogeneity
  from event-like anomalies. (The alarm-concentration check in
  `predictive-ssl-controlled-trial` part A is field-level and only for `gru_pred`.)

**GAP-4 — 30 m caveat is a note, not a requirement.** `patch-data-pipeline` design
records the LST caveat; the comparison spec's deliverable requirements do not demand
the resolution arithmetic. Fix: one scenario in
`specs/spatial-representation/spec.md` requiring finding 24 to state, per
representation, the ground sampling distance and the smallest resolvable anomaly
(1 px = 30 m = 0.09 ha; a 16×16 R2 crop = 480 m ≈ 23 ha, i.e. comparable to a whole
median field — worth saying out loud, since it makes R2 much less "local" than it
sounds).

**GAP-5 — no detectability crossing.** The prompt's core question ("can patches
detect what the mean cannot?") is mechanistically a *paired per-injection* claim. The
changes only compare aggregate MDM80 with a paired bootstrap over fields. Fix: add a
2×2 crossing table per severity (detected by R1 only / R0 only / both / neither) —
free, since both arms are scored on the same injections.

**GAP-6 — extent axis.** Only footprint 1.0 and 0.3 exist, both as a *localization
probe* on the patch scorer. The prompt asks how extent affects detectability. Fix:
sweep footprint ∈ {0.1, 0.3, 0.6, 1.0} (the applier already takes a footprint) and
report MDM80 + localization AUPRC per extent for R0 (unchanged score) vs R1.

---

## 2. Prompt 2 — "Farm-Internal Spatial Anomaly Detection"

| # | Prompt requirement | Where it is specified | Status |
|---|---|---|---|
| 2.1 | Study area: ~490 heterogeneous Amirkabir farms (variety, age, planting date, phenology, management, soil, history) | Recognised: 490 fields throughout; per-field cycles from `cycles_490.parquet`; DOY/cycle-age covariates; phenophase conditioning | 🟡 **GAP-7** (variety/ratoon/kind exist in `cycles_490.parquet` and are used by `baseline/robust.py:96-106` strata, but are **not** in the patch covariates `d_u = 7` and not used by B1/GRU/patch paths) |
| 2.2 | **Core: detection operates independently within each farm polygon** | `patch-data-pipeline` (field bbox, own patch per field, static `in_field` mask), R2 crops fully inside the polygon, field-level scores from internal pixels only | ✅ structurally, but see 2.4–2.6 |
| 2.3 | Patches generated/evaluated inside farm boundaries | bbox crop + pad, never resample; polygon mask excludes neighbouring fields; `in_field` fraction 1.0 enforced for R2 crops (spec "Crop sets are reproducible") | ✅ |
| 2.4 | Adjacent farms must **not** be treated as spatially connected | Mask excludes neighbours; but **no invariance test** exists | 🔴 **GAP-8** |
| 2.5 | No spatial neighbourhood / convolution / attention / aggregation may mix farms | GroupNorm chosen, "no BatchNorm anywhere" (justified by *masked-batch statistics*, not by farm independence); per-location GRU, no attention; no spatial pooling; R3a dilations {1,2,4} widen the receptive field | 🟡 **GAP-8** + ⚪ (GroupNorm/GRU choices are right; the *reason* recorded is not the prompt's reason) |
| 2.6 | Farm-level scores = aggregation of that farm's internal pixel/patch anomalies | top-20% mean (`patch-level-controlled-trial`); aggregation rule selected on synthetic validation only (`patch-scoring-ensemble`) | ✅ |
| 2.7 | Each farm primarily compared against **its own historical observations** | Not implemented. Scores are per-pixel residuals ÷ population σ(channel, 2-bin phenophase, sensor), calibrated on dev field-cycles | 🔴 **GAP-9** (the largest conceptual gap) |
| 2.8 | Learn farm-specific normal growth over time | Shared model + shared σ; no per-farm baseline; closest existing mechanism is the **shrinkage per-field offset** in `baseline/robust.py:173` (partial pooling), which exists only for the field-level baselines | 🔴 **GAP-9** |
| 2.9 | Comparisons account for **phenology**, not calendar dates | 36-bin cycle grid anchored at cycle start; phenophase-binned σ; cycle age; `b0_calendar` shown side-by-side as the calendar reference | ✅ |
| 2.10 | Cross-farm learning allowed, but shared params must not assume identical normal distributions | Partially: shared trunk + phenophase/sensor-conditioned σ is a stated mitigation; but no requirement that a field's *score* be insensitive to its own natural level/scale | 🟡 **GAP-9/10** |
| 2.11 | Final anomaly assessment must remain **farm-specific** | Contradicted in three places by `patch-scoring-ensemble` (see 2.12) and one by `patch-independent-indicators` | 🔴 **GAP-10** |
| 2.12 | No farm's score should depend on other farms | (a) `s_hyb` = within-phenophase **percentile ranks over the dev population**; (b) persistence `z_f(t)` = robust z of the field score **against all fields at the same phenophase**; (c) date-wise cross-field median subtraction (**default off** — good); (d) indicator z-scores use **across-field spread** as their unit. (a), (b), (d) are unconditional; the spec has no independence clause | 🔴 **GAP-10** (most consequential finding of this audit) |
| 2.13 | Farm-level output summarises spatial distribution, severity, persistence | Severity ladder ✅, CUSUM/EWMA persistence + delay ✅, pixel maps via `patch-xai-attribution` ✅; but no field-level *summary object* (affected area fraction, connected-component extent, "which sub-region") | 🟡 **GAP-11** (minor, presentational) |
| 2.14 | Inspect the existing architecture for violations (conv, attention, normalization, neighbourhood, calibration) | Partly done implicitly by design choices; **no audit artifact and no tests** targeting farm independence | 🔴 **GAP-8** (no test) + this document (the audit) |

### Prompt-2 gaps in detail

**GAP-8 — no farm-boundary invariance test (cheap, high value).**
`patch-level-controlled-trial` tasks 1.1 test temporal causality, GRU state carry on
invalid pixels, and GroupNorm on masked batches — but nothing asserts that a pixel
**outside** the `in_field` mask cannot influence an in-field score. Also unresolved in
writing: `pixel_valid` and `in_field` are separate arrays, and the stem consumes
`concat[X·M, M]`. If `M = pixel_valid` only, real values of a *neighbouring field*
that happens to fall inside the 32×32 bbox **enter the convolutions**. Fix (two
lines of spec + one test):
- Spec: "values of pixels with `in_field = 0` SHALL be excluded from every model
  input (masked, never passed as values), and the score of an in-field pixel SHALL be
  invariant to any change in out-of-field or other-field pixels."
- Test: perturb out-of-field values (and a synthetic neighbouring field inside the
  bbox) → in-field per-pixel scores byte-identical.
- Also required for R3a: dilation 4 reaches ~9 px, and 7.3% of fields are smaller than
  16 px — the invariance test is what makes that safe rather than lucky.

**GAP-9 — "the same farm's own history" is not actually the comparison basis.**
The prompt's expected answer is *"is this patch abnormal for this farm at this
phenological stage?"*. The implemented statistic answers *"is this patch's residual
large relative to the dev population's residual spread for this phenophase bin?"*.
The difference is real, not semantic: a farm whose clean residuals are systematically
wider (or whose NDVI level is naturally lower) will produce inflated scores for
reasons unrelated to anomaly. Mitigations that exist: the predictive/reconstruction
residual is partly self-referential (the model predicts the *field's own* series), and
part A of the predictive trial checks alarm concentration across fields (symptom
detection, not a fix).
Missing:
- a **per-field (or per-field-per-pixel) robust climatology / offset** arm modelled on
  the existing `field_offset` shrinkage in `baseline/robust.py`, extended to the patch
  scorer — i.e. `σ_f = 1.4826·MAD` of *this field's* clean residuals, with a
  population fallback when the field has too few cycles;
- an honest **data-limitation statement**: 370 fields have ≥1 non-censored cycle and
  only **223 have ≥2** (`docs/findings/01`), so a strictly per-farm distribution is
  impossible for most farms — partial pooling is not a convenience, it is forced.
  This belongs in the spec/finding as a *stated* compromise, not an implicit one;
- a **decision rule** on whether per-field standardisation is allowed (it changes
  FAR accounting and threshold comparability across arms).

**GAP-10 — cross-field normalisation contradicts the prompt's core requirement.**
`patch-scoring-ensemble` introduces, unconditionally:
1. `s_hyb` — mean of **within-phenophase percentile ranks** computed over the dev
   population (a farm's score literally depends on other farms' scores in the same bin);
2. persistence `z_f(t)` — "robust z of the field score **against all fields** at the same
   phenophase" (`proposal.md` §CUSUM);
3. date-wise cross-field median subtraction — correctly **default off** and labelled as
   reading contemporaneous cross-field values;
4. (`patch-independent-indicators` design) indicator z-scores with **across-field
   spread** as unit.
The prompt explicitly forbids the question "is this location different from other
farms?". Items 1, 2 and 4 answer exactly that question. They are not necessarily wrong
— they may be the most sensitive statistics available — but the program has no clause
making the conflict visible, and no arm-level choice between "farm-local score" and
"population-ranked score".
Fix: add a requirement to `patch-scoring-ensemble` (and echo it in
`compare-spatial-representation-strategies`):
> Every scored arm SHALL be classifiable as **farm-local** (score a function of that
> farm's own observations and frozen constants only) or **population-ranked** (score
> uses other farms' contemporaneous values). The comparison table SHALL label each
> arm, farm-local SHALL be the default for the final configuration, and each
> population-ranked component SHALL be reported as a labelled sensitivity variant with
> its cross-farm dependence stated in the report.
Plus the corresponding invariance test: permute/perturb *other* farms' data → a given
farm's farm-local score must be unchanged (this single test catches all three cases).

**GAP-7 — variety/ratoon strata are available and unused.**
`cycles_490.parquet` carries `kind`, `ratoon_no`, `variety_group` (consumed by
`build_stratum_table`, `baseline/robust.py:96-106`), i.e. the heterogeneity the prompt
opens with is *observable*, but the patch covariates are
`{sin/cos DOY, cycle age, days-since-last-valid, log1p n_obs, sensor one-hot}` and
neither B1 nor the GRU nor the patch arm stratifies by ratoon/variety. Two of the
prompt's stated non-comparabilities (crop age / planting date, variety) are therefore
ignored even though the columns exist. Fix: add variety/ratoon as a covariate
ablation cell in `patch-full-run-and-ablations` E4 (one flag, one run) and/or as a
σ-binning level; report whether it moves MDM80.

**GAP-11 — no field-level summary object.** "The farm-level output should summarize
the spatial distribution, severity, and persistence." Severity and persistence are
spec'd; spatial distribution is only available as raw XAI maps. Fix: one small
requirement — per alarm, a record `{affected area fraction, n connected components,
max component extent in px and ha, centroid, severity level, persistence length}`.
This is also what makes the platform/figures later trivially satisfiable.

### Existing-code components that could violate prompt 2 (the "inspect the architecture" ask)

| Component | Behaviour | Verdict |
|---|---|---|
| `io/zonal.py::zonal_scene` | `np.bincount` over one label raster; field 0 dropped; per-field mean/median/std… | Safe — no cross-field mixing |
| `io/field_mask.py` | rasterises polygons to `uint32` labels | Safe (overlaps resolved by rasterise order — worth one assertion that no field id is duplicated/overwritten) |
| `io/stats_zarr.py` + `scripts/extract_stats.py` | per-(field, date, band) stats incl. `std, p10, p25, p75, p90, iqr` | Safe; **but only `median` is consumed** → the unused stats are the ready-made GAP-1 arm |
| `monitor/inputs.py::fit_normalization` | median/MAD per (phase bin, band) pooled over **all train fields** | Cross-farm **input scale** — defensible for a shared encoder, but currently unstated as a bounded exception |
| `baseline/robust.py::fit_baseline` | pooled stratum median/MAD + **shrinkage per-field offset** (partial pooling), strata by `kind_ratoon_no` and `variety_group` | The only existing farm-adaptive mechanism — the natural template for GAP-9; also the only place variety/ratoon is used |
| `baseline/b0_calendar.py` | calendar-DOY keyed, pooled + per-field offset | Farm-adaptive at field level; the right B0 reference to show next to a farm-local claim |
| `monitor/scoring.py::calibrate_threshold`, `cell_q95_normalizer`, `per_bin_q95_normalizer` | τ and q95 calibrated on the **dev population** at 5 % cycle-FAR | Population-level **calibration** (unavoidable for FAR accounting) — must be labelled as such, not confused with a farm-local score |
| `patch-level-controlled-trial` stem | 32×32 patch incl. padded/neighbour pixels, `concat[X·M, M]` | ⚠️ GAP-8 — needs the `in_field` masking guarantee + invariance test |
| `patch-cnn-gru` temporal module | per-location GRU, state carried where invalid | Safe — no cross-pixel mixing |
| `compare-spatial...` R3a | dilations {1,2,4} (receptive field ~9 px) | Safe **only if** GAP-8 is closed |
| `patch-scoring-ensemble` `s_hyb`, `z_f(t)`, common-mode subtraction | population percentile ranks / across-field z / date-wise median | ⚠️ GAP-10 |
| `patch-independent-indicators` indicator z | across-field spread as unit | ⚠️ GAP-10 (acceptable for a *validation* indicator, must be labelled) |
| `patch-full-run-and-ablations` E4 weather join | per-field weather at field centroid | Safe (weather is exogenous and physically shared — not a "farm comparison") |

---

## 3. What is genuinely covered well (do not re-litigate)

- Phenology-aware comparison instead of calendar dates (cycle grid + phenophase bins +
  DOY/cycle-age covariates, `b0_calendar` as the mandatory calendar reference).
- Fairness machinery: equal budget, capacity-matched params, one factor per cell,
  paired bootstrap over fields, pre-registration with honest negatives everywhere.
- Leakage discipline: frozen splits `9aa5eb11…`, `training-holdout-invariant`
  fail-closed holdout (`scripts/build_holdout_manifest.py`, `monitor/holdout.py`),
  train-only normalisation, dev-only calibration, test only via the locked path.
- QA/NaN discipline: no zero-fill, per-pixel validity, no resampling.
- Evaluation integration: patch scores feed the **unchanged** severity protocol and
  alarm machinery, so FAR/MDM80 comparability with the zonal arms is real.
- Independent indicators, weather/neighbour external consistency, and XAI spatial
  attribution — prompt 1's "consistency with independent indicators" is well served.
- Operability: `--estimate-runtime`, `--resume`, `--smoke`, agent-never-launches-long-jobs.

---

## 4. Recommended minimal amendments (in priority order)

| # | Amendment | Change to touch | Cost |
|---|---|---|---|
| A1 | Add **R0.5 zonal-distribution-statistics arm** (`std`, `p10`, `iqr` channels → existing `b1`/`B1PhaseZCausal` path, no training) + one spec requirement + one table row | `compare-spatial-representation-strategies` | S — no new data (stats already in `stats.zarr`), no GPU |
| A2 | Add **farm-independence requirement + invariance tests**: (a) out-of-field/neighbour invariance of in-field scores, with the `in_field`-ANDed masking stated; (b) "other farms' data must not change a farm-local score"; (c) arm labelling farm-local vs population-ranked, farm-local the default | `patch-level-controlled-trial` (1.1), `patch-scoring-ensemble` (spec), `compare-spatial-representation-strategies` (table column) | S — spec text + 2 unit tests |
| A3 | Add **per-field (partial-pooled) score standardisation** arm + the data-limitation statement (223/370 fields have ≥2 cycles; per-farm climatology is impossible without pooling) | `patch-scoring-ensemble` (or a small new change) | M — one scoring variant, no retraining |
| A4 | Add **heterogeneity control + i.i.d. noise null + per-pixel alarm-frequency diagnostic** | `compare-spatial-representation-strategies` | S–M — analysis only |
| A5 | Add **subset-restricted R0 comparison** and state the training-size confound | `compare-spatial-representation-strategies` | S |
| A6 | Add **extent sweep** {0.1, 0.3, 0.6, 1.0} and the **detectability-crossing table** (R0-only / R1-only / both / neither per severity) | `compare-spatial-representation-strategies`, `patch-level-controlled-trial` | S — applier already parameterised |
| A7 | Add **30 m resolution arithmetic as a required report field** in finding 24 (30 m px = 0.09 ha; R2 crop = 480 m ≈ 23 ha ≈ a whole median field) | `specs/spatial-representation/spec.md` | S |
| A8 | Add **variety/ratoon covariate cell** to E4 and/or σ-binning (columns already exist in `cycles_490.parquet`) | `patch-full-run-and-ablations` | S (one flag) / M (one run) |
| A9 | Add **field-level anomaly summary object** (area fraction, components, extent in ha, severity, persistence) | `patch-scoring-ensemble` or `patch-xai-attribution` | S |

A1, A2 and A7 are pure specification work and close the two headline gaps; A3–A6 are
analysis-only additions to arms that are not built yet, so they cost nothing in code
that already exists.

---

## 5. Bottom line

- Prompt 1: **~80 % covered**. Missing: the Spatial Statistics arm (and with it
  deliverables 1.2/1.3 of the prompt), the heterogeneity/noise controls, the extent
  axis, the 30 m report requirement, and honest R0 pairing.
- Prompt 2: **~60 % covered structurally, weaker on the core principle**. Boundaries,
  masking, aggregation and no-attention design are right; "compare each patch against
  the same farm's own history" and "the final assessment must stay farm-specific" are
  *not* implemented as written, and `patch-scoring-ensemble` adds three unconditional
  cross-field normalisations that answer the question the prompt forbids.
- Neither prompt is "applied" in code: all 13 changes are proposals, all tasks open.
  Fixing A1–A3 in the specs **before** implementation is cheap; fixing them after the
  PoC runs is not, because they change what the first comparison table means.

---

## 6. Amendments applied (2026-11-16, same session)

All amendments below are **specification-only** — no code, no runs, no
change of any recorded number. Nothing has been applied to code.

| Amendment | Where it landed | Gap closed |
|---|---|---|
| **A1** R0.5 zonal distribution statistics (`std`, `p10`, `iqr`, existing `stats.zarr`; `b1_dist`, `b0_dist`, `p10`-only path-max; regression guard that median-only reproduces today's `b1`) + the three-row R0/R0.5/R1 structure | `compare-spatial-representation-strategies`: proposal, design §R0.5, spec req. "Zonal distribution-statistics representation (R0.5)", tasks §2 | GAP-1 (+1.14, 1.15, 1.21) |
| **A2a** Farm-boundary isolation requirement + tests (`M_in = pixel_valid ∧ in_field`; out-of-field perturbation invariance; GroupNorm/dilation justified under the invariance test) | `patch-level-controlled-trial`: spec req. "Farm-boundary isolation of patch inputs and scores", tasks 1.1b | GAP-8 |
| **A2b** Basis labelling (farm-local vs population-ranked) + farm-local default + independence tests | new change `farm-local-anomaly-scoring`; `patch-scoring-ensemble` spec req. "Scoring-basis labelling and farm-local default" + tasks 2.4–2.6 | GAP-10 |
| **A3** Per-field shrunk σ arm (`w_f = n_f/(n_f+κ_σ)`, floor, fallback order, history tiers), no retraining; the 223/370 limitation stated in-spec | `farm-local-anomaly-scoring` spec req. "Per-field standardised scoring arm", tasks §2 | GAP-9 |
| **A4** Heterogeneity battery: static-pattern control, white-noise null (diagnostic only, excluded from every gate), per-pixel alarm frequency | `compare-spatial-representation-strategies` spec req. "Heterogeneity and noise disambiguation battery", design, tasks §3 | GAP-3 (1.9, 1.11) |
| **A5** R0-subset re-score on the shared evaluation panel + explicit training-set-size confound | `compare-spatial-representation-strategies` spec (ladder req. + scenario "Reused baselines are paired honestly"), tasks 2.5 | GAP-2 |
| **A6** Extent sweep {0.1, 0.3, 0.6, 1.0} + per-severity detectability-crossing table | `compare-spatial-representation-strategies` spec req. "Extent axis and detectability crossing", tasks §4; applier parameterised in `patch-level-controlled-trial` task 2.3 | GAP-6, GAP-5 |
| **A7** Resolution arithmetic as a required report field | `compare-spatial-representation-strategies` spec req. "Spatial resolution is a reported quantity", design §Resolution arithmetic, task 8.2 | GAP-4 |
| **A8** Ratoon/variety cell in E4; scale-stratum question separated into the new change | `patch-full-run-and-ablations` tasks 2.3 + spec; `farm-local-anomaly-scoring` spec req. "Optional agronomic stratum for scaling", tasks §3 | GAP-7 |
| **A9** Farm-level anomaly summary object (area fraction, components, extent in ha, centroid, severity, persistence) | `farm-local-anomaly-scoring` spec req. "Farm-level anomaly summary", tasks §4 | GAP-11 |
| — | Indicator z-unit labelled population-referenced + farm-own variant | `patch-independent-indicators` spec + task 1.2 | GAP-10 (item 4) |
| — | Missing `.openspec.yaml` for `predictive-ssl-controlled-trial` added (it was the only change without one) | `openspec/changes/predictive-ssl-controlled-trial/.openspec.yaml` | hygiene |

### Structural validation performed

No `openspec` CLI is available offline in this environment (`npx
@openspec/cli` cannot resolve), so the delta format was validated with a
script: every active change has `proposal.md`, `design.md`, `tasks.md`,
`.openspec.yaml` and at least one `specs/<capability>/spec.md` beginning
with `## ADDED Requirements`; every requirement has at least one scenario;
every scenario has `WHEN` and `THEN`; every `tasks.md` uses numbered
`- [ ]` items. Result: **0 problems across 14 changes**.

### What was deliberately NOT changed

- No task was checked off, no change archived, no code written — the
  program is still specification-only, and A1–A9 all attach to work that has
  not started, so nothing is re-done.
- The `predictive-ssl-controlled-trial` gates, the severity protocol, the
  locked splits/holdout manifest, the injection sets and every recorded
  finding number are untouched.
- Prompt-1 requirement 1.5 (a 20–30-farm panel) is **not** reproduced
  literally: the PoC's ~100-field subset / 38-field dev panel is kept, now
  with the confound stated and the R0-subset pairing added. Recorded as a
  deliberate deviation rather than silently narrowed.
