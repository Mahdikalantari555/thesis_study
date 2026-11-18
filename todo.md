# todo.md — thesis platform & research backlog

Owner-driven requirement list. **Rule:** each numbered item becomes its own
openspec change when we start it (per user, 2026-11-07). Items ✅ are done;
▶ is in progress; everything else is queued by priority.

## Done (2026-11-07, change `wire-platform-to-real-data`, commits b667e5a / 20a28f5)

- ✅ Tile server survives concurrent browser load (per-handle locks; burst + headless-pan gates)
- ✅ Real weather wired (ERA5 join, 100% coverage on the then-monthly grid); null ⇒ `absent`
- ✅ Real farm registry metadata; zero synthesized strings
- ✅ Real model generations exported **with** checkpoints (9,639 model-provenance cells)
- ✅ Honest copy (PipelineDataBadge, banner, footers); stressEvent machinery removed; `mock.ts` → `data.ts`
- ✅ Map Explorer UX: Hide = polygons only; opacity floor 0; **single date slider** drives fields + raster; raster opacity persists
- ✅ No fabricated numbers (score 0.5 fallback removed; complete-case Moran's I; CSV empty cells)
- ✅ Presentation audit (`docs/platform_presentation_audit.md`) + precise methods doc (`docs/platform_score_methods.md`)
- ✅ MSc wording (was PhD) in en/fa
- ✅ RGB tile **seams fixed** — per-scene contrast window (`SceneStretchCache` in `serve_tiles.py`) instead of per-tile stretch; verified on stitched adjacent tiles

## Done (second wave, 2026-11-07)

- ✅ **1. Full-archive observation axis** — every acquisition date (538; 263,620 obs; multi-acquisition months kept). Contract v4 compact payload (292 MB → 29.8 MB, RLE provenance, derived formula ids). Charts: adaptive ticks; scatters stride-sampled for display (stats on full data). Registry envelopes widened for real winter medians (ndvi −0.399 observed). Gates green (up + down).
- ✅ RGB tile seams (per-scene contrast window), compact provenance chips, tick fonts, CDP send-timeout + watchdog in the gate harness.

## In progress

- ▶ **`decomposition-aware-ssl-study`** — isolated runner and [runbook](docs/decomposition_aware_ssl_study.md). Real benchmark/ablation and the architecture-gate decision require the canonical polygon zonal store, locked splits and existing frozen holdout manifest. Smoke is not empirical evidence.
- ▶ **`rerun-rq-suite-on-real-490`** (proposed 2026-11-10) — RQ1–RQ8 + data-scarcity results in findings 11–12 came from `simulate_490_field_archive`, not the real 490-field archive; re-run on real data, fail closed, provenance in every report.
  - ✅ Task 1: real_archive.py loader + hash check + provenance + --source arg (tests/unit/test_real_archive.py 4/6 pass)
  - ✅ Task 2: all 8 run_rq*.py + run_data_scarcity.py refactored with --source {real490,real32,simulated}; simulated → reports/simulated/
  - ✅ Task 3.1: data/processed/splits_490.json built (370 fields, 799 cycles, 20 spatial blocks, SHA-256 recorded)
  - ✅ Task 3.2: proxies absent on real490 (no 32-farm cwsi_et borrow); test passes
  - ✅ Task 4: smoke tests all pass on real490 (run_rq1–rq7_rq8 + run_data_scarcity all EXIT 0)
  - ✅ Task 5: findings 08/10/11/12 updated; real490 status + sim superseded sections added
  - ✅ Task 6: tests added (test_provenance_complete, test_fail_closed, test_no_32farm_borrow, test_sim_output_path); spec R1–R5 verified; change archived to openspec/changes/archive/
  - See `openspec/changes/rerun-rq-suite-on-real-490/`.

## Queued — openspec candidates (one change each, user-approved direction)

1. **`visualize-metric-products`** — wire METRIC products into the platform:
   - ✅ Interim visualization DONE (user, 2026-11-10): `data/interim/metric_interpolation_timeseries.png` — ticked 2026-11-14; platform wiring still pending
   - `Data/Metric/products/ETaDaily/` — 271 scene rasters (mm/day, 30 m, UTM39N, AOI 496×472)
   - `Data/Metric/products/interpolation/{ETaDaily,CWSI_ET}/` — **4,375 daily interpolated rasters each** (2013-03-31 → …)
   - Zonal stats per field per date → new payload channels (ETa_METRIC, CWSI_ET) → Temporal/Map views + raster tile layers
   - Decide: which product feeds which view (daily interpolation for continuous sliders; scene rasters for truth)
2. **`two-cwsi-channels`** — the two CWSI variants as separate channels:
   `CWSI_ET` (energy-balance) vs `CWSI_LST` (thermal) from `products/`; current heuristic CWSI stays labelled `proxy` or is replaced. Use CWSI-ET + ETaDaily as **proxy references for how the anomaly models perform** (agreement view), while stating plainly that magnitude agreement is NOT phase-anomaly validation.
3. **`phenology-cycle-visualization`** — visualize the segmentation:
   - Export cycle spans per field (`t_start/t_end/harvest_day` → real dates) into the payload
   - Temporal view: shaded cycle bands + harvest markers + the 36×15-day phase-binned series (DSH axis) beside the DOY axis
   - Plain-language doc section (what a "cycle" is and why models score per phase) — expand `docs/platform_score_methods.md` §4.1
3b. **`data-and-phenology-readiness`** — ✅ agent tasks complete (literature review findings 13, cycle audit script, data quality report, stage-conditioned anomaly detection script + findings 14, openspec D5 spec + D11 decision record). ✅ User approved task 4.2 — training sections 2–5 of item 4 unblocked.
4. **`retrain-and-improve-models`** → openspec change `train-and-finalize-main-architecture` — ▶ UNBLOCKED (user approved 3b task 4.2) — training sections 2–5 can now start:
   - D11 decision record adopted (R1–R8 + findings 14); sin/cos DOY auxiliary input (R3) applies to all candidate models; outputs/reports must be publication-ready with full provenance.
   - Tooling (new): save per-seed weights for resume, run_manifest.json, run_dev_matrix.py, check_dev_env.py, Data/Scripts/README.md, dev_log schema test, TDD-first causality/mask tests.
   - ML hardening (new): gradient clipping + NaN guard, deterministic seeding, DOY ablation harness, causal-mask test, FAR calibration with bootstrap CI, model card sidecar.
   - Academic/repro (new): scholar-evaluation rubric, literature-review/citation-management, scientific-writing, benchmark-methodology/eval-harness, mle-workflow, install selected skills.
   - Current checkpoints are deliberately small (`d_model=32`, ≤ ~10⁵ params, 15 epochs, single-shot, trained 2026-11-04)
   - More epochs/parameters/time once data wiring is final; re-train on the final cycle export; keep formula-id/versioning so the payload records *which* checkpoint scored it
   - Include masked_transformer (needs a cycle-compatible artifact) and JEPA scoring
5. **`validation-ladder`** — multi-stage validation as the acceptance frame:
   - L1 learns growth patterns → L2 detects controlled deviations → L3 generalizes across years/farms → L4 agrees with independent agronomic evidence → L5 beats baselines
   - Map existing views/tests to rungs; build what's missing (L2 controlled-anomaly injection, L3 year/field holdouts, L4 expert/ground-truth review — ties to the 4 paused growth-validation tasks)
   - **OPEN QUESTION (user will send the full explanation):** the complete 5-level table + criteria — wait for it before writing this spec.
6. **`era5-covariates`** — wire the unused weather columns: `et0_sum`, VPD, soil moisture, solar radiation, wind, 3/7/14/30-day windows (30-day precip = the right drought signal; ET0 enables a water-balance ETa).
7. **`physical-cwsi`** — Idso/Jackson CWSI `(Tc − Ta)/(Tc_upper − Ta_lower)` using the already-joined ERA5 air temperature; replaces the hard-coded (20 °C, 25 °C) heuristic.
8. **`per-pixel-heterogeneity`** — pixel parquets exist; within-field views (deficit-irrigated corners invisible today).
9. **`score-uncertainty`** — per-bin error curves already computed; show score stability/confidence on the inspector + temporal charts.
10. **`literature-benchmark-view`** — surface `reports/literature_models_benchmark.json` (exists, no view).
11. **`registry-aware-neighbors`** — neighbour graphs from block/office/management instead of centroid kNN.

## Open questions & blockers (restructured 2026-11-14 after the severity/objective deep-research)

Full evidence: `D:\RS\Thesis\research\ssl-stress-advantage\REPORT.md` (27 sources) +
`docs/findings/16_development_protocol_results.md`. Blockers grouped by who unblocks them.

### A. Advisor-gated (Dr. Hamzeh) — blocks the model/protocol track (finding-16 follow-ups)

- **A1. OQ6 — realistic stress signatures & magnitudes for Amirkabir sugarcane** (water deficit,
  salinity, waterlogging, pests/disease, early ripening, lodging; sub-questions from findings 13 §3.3:
  pre-harvest irrigation cut-off timing/magnitude; pre-harvest burning NDVI/LST signature; transient vs
  chronic disturbances; typical mid-season NDVI drop; waterlogging occurrence/months).
  **PARTIALLY ANSWERED 2026-11-14 (user): vegetation-index drops (NDVI, SAVI) are the signals that
  matter — other signature categories (LST rise, waterlogging, burning, …) the user cannot answer.**
  Remaining sub-question = drop MAGNITUDE + duration. Fallback if the advisor is also silent (recorded):
  use the deep-research literature table as the interim default — NDVI/SAVI drops −0.05/−0.10/−0.15/−0.25
  (2–6 bins duration), labelled interim/literature-derived in D6 + model card; severity table is config,
  advisor can adjust later without invalidating infrastructure.
  **Blocks:** D6 perturbation-set update; task 6.2 tuning resumption; final severity-scale decision
  (across-field MAD vs model-residual) and FAR level (cycle vs event vs bin).
- **A2. L4 evidence availability** — can irrigation records, per-field yield, rootzone-ECe/salinity
  surveys, or expert review be obtained for even a subset of the 490 fields? **Blocks:** any L4
  validation plan; without it the thesis caps at L2/L3 + proxy agreement (published SSL-EO norm,
  cf. SAED-ViT SPEI r=−0.909; STS-Net's imposed treatments = the gold standard we don't have).
- **A3. Sign-off on the honest-negative framing + the 3-move plan** (M1 severity protocol /
  M2 normal-bank scorer / M3 event-FAR + POT declustering) — **blocks** committing the normal-bank
  arm as the official task-6.2 direction (more reconstruction tuning would optimize noise, finding 16).

### B. User-gated (repo / product / workflow decisions)

- **B1.** METRIC products: which interpolated product is authoritative for daily values (item 1) —
  scene rasters vs `interpolation/` semantics. **Visualization step DONE (user, 2026-11-10):
  `data/interim/metric_interpolation_timeseries.png`**; platform wiring + the authoritative-product
  decision still open. **Blocks:** `visualize-metric-products` (platform part).
- **B2.** Full-archive axis: keep the completeness-stat semantics (invalid acquisitions = missing) as-is? [existing]
- **B3.** `rust/` crate (added by coding-agent commits; `32.7×` claim unreproduced) — keep+verify or remove? [existing]
- **B5.** Tasks 11.1–11.6 (skill adoption: scholar-evaluation, literature-review/citation-management,
  scientific-writing, benchmark-methodology/eval-harness, mle-workflow; 11.6 installs skills locally) — approval pending. [existing]

### C. Technical ambiguities (agent-resolvable; decision recorded here)

- **C1. Severity-unit computation (pairs with A1):** full per-band model-residual distribution
  (residual MAD vs across-field MAD) on the 490-field archive — agent can compute on request; the
  deep-research conversion used sidecar medians only (first-order). **Blocks:** final severity-scale choice.
- **C2. Threshold rule:** adopt SHAZAM's per-DOY score-climatology threshold (fitted mean + 1.64 SD,
  circular DOY regression) as a second calibrated rule alongside the per-(bin,channel) q95 — testable
  in ~1 day; needs a protocol decision.
- **C3. Sugarcane-specific spectral magnitudes:** NDVI/SAVI drop under controlled water stress and
  NDVI-vs-ECe salinity slopes not retrievable from the open web (MDPI/S2 blocked) — row-crop analogues
  (maize/cotton/wheat) + FAO 29 used meanwhile; institutional access to Gómez Flores 2022
  (Remote Sensing 14:3389) would fill the salinity side. **Blocks:** exact salinity-side severity anchoring only.
- **C4. TSB-AD-S injection amplitudes unread** (OpenReview bot-gated; CATS repo 404) — nice-to-have,
  blocks nothing critical.
- **C5. M2 design details** (bank granularity: per-bin vs per-window latents; distance metric;
  fusion rule with the channel-max alarm statistic) — agent's call inside the M2 openspec change,
  flagged here as a recorded decision point.
- **C6. Legacy adapter for deleted `fields.zarr`** (test_ablation) — user-paused 2026-11-07;
  pre-existing failure documented.
- **C7. Environmental 0xc06d007f crashes** (test_daily_anomaly_map / test_eval /
  test_baseline_comparators / test_data_scarcity) — environment/load-order, not code; suite runs with
  `--ignore` for these 5 files → 203 passed 1 failed (=real_archive data-state, C6 family).
- **C8. Temporal selection window (owner validation guide §2, 2026-11-15):** the guide proposes
  train ≤2021 / val 2022–2023 / test 2024–2026; the LOCKED splits (9aa5eb11) use test start
  2024-01-01 with dev cycles cut at that boundary — no 2021/2022 boundary exists. Agent
  recommendation (recorded): KEEP the locked splits for comparability with findings 18/21/22;
  adopt 2022–2023 as the SELECTION sub-window within dev for the final architecture decision IF
  the dev 2022–23 cycle count supports it (counting the dev cycles by period = the decision's
  first task). Changing the locked splits mid-program would break the pre-registered trials.

### D. Follow-up research paths from finding 20 (user-directed; changes CREATED 2026-11-14, awaiting execution)

Evidence: `docs/findings/20_reconstruction_invariance.md` (signal-path decomposition + absorption,
2026-11-14). Owner approval 2026-11-14: both changes below were written and validated; execution is
the next step. Owner prohibitions recorded verbatim: do NOT re-develop Normal Bank, do NOT bring
foundation models into the main path, do NOT trial multiple architectures in parallel — only these
two experiments.

- **D1. Path B — re-examine the anomaly definition:** multivariate/relational and phenology-shape
  injection families (the current single-index absolute-drop family is the finding-20 scope limit).
  Decided as the FALLBACK path: taken only if the predictive trial's synthetic-detection gate fails
  (see `predictive-ssl-controlled-trial` decision gates). No implementation exists yet.
- **D2. Path C — forecasting/predictive-coding objective (finding-20 decision-matrix remedy).**
  Two changes created and validated 2026-11-14, to run in order:
  1. **`forecast-unit-probe`** (zero-training, agent-runnable in minutes): pre-registered untrained
     causal forecasters (persist/med3/trend4) inside the exact production statistic; same eval
     subset + injections; MDM80 + event-FAR + waterfall. Success = non-censored MDM80 ≤ S5 on
     persistent/ndvi → path C justified with a measured target floor; all censored → honest negative.
     → finding 21.
     **OUTCOME (2026-11-14, run complete): honest negative — ALL FOUR ARMS censored ">S6" on
     persistent/ndvi** (persist/med3/trend4 + B1 reference recomputed in-harness; B1 crosscheck
     vs finding-18 = 0 mismatches). Mechanism: the clean one-step residual scale is NOT small —
     σ_forecast ≈ 0.23 NDVI (≈1.3× the across-cycle spread; the design's 0.01–0.02 estimate was
     ~10× off) — so the S6 drop is only 1.2–1.7 forecast-σ vs a ~3.6–4.0σ per-bin requirement;
     no untrained arm even reaches gru_ae's requirement ratio (best persist 0.44 vs gru_ae 0.48);
     carry-forward forecasters absorb the level (A ≈ 0.75–0.81) — the naive-forecaster unit
     upside is disproven. Evidence: `docs/findings/21_forecast_unit_probe.md`,
     `reports/dev/forecast_probe_20261114/probe_summary.json`. The trained `gru_pred` trial
     below still runs with its own five gates (a trained model could shrink σ_forecast); weight
     shifts toward path B unless it passes.
  2. **`predictive-ssl-controlled-trial`** (trains ONE new arm `gru_pred` — same trunk/inputs/budget
     as gru_ae_main, one-step-ahead objective only; seeds {13,42,2026}; user runs training from
     agent-provided commands): four parts — A natural-data FAR behavior, B the unchanged finding-18
     severity protocol vs B1+gru_ae_main, C the absorption experiment (error at three checkpoints +
     A ratio vs gru_ae's α≈0.45), D agreement with independent indicators (CWSI/ETa/ETrF/TVDI —
     proxy evidence, never stress proof; unavailable sources = `absent`). Pre-registered decision
     gates decide: predictive = main path, or fall back to D1. → finding 22.
     **STATUS (2026-11-14, implementation COMPLETE, awaiting user-run training):** gru_pred arm
     implemented + smoke-green (commit 60fc792: `DeepPredictiveScorer` — naturally causal single
     pass, per-(bin,channel) masked smooth-L1 β=1.0 pre-registered in
     `train_main.PREDICTIVE_OBJECTIVE`; 174,008 params = gru_ae's exact count; 10 unit tests).
     Parts A–D scripts built + smoke-green (commit 521bb94: `trial_part_{a,b,c,d}_*.py` via
     `trial_common.py`; part B recomputes all three arms on trial-scoped artifact copies and
     crosschecks B1/gru_ae vs the recorded finding-18 rates at 0-mismatch; part D availability
     runtime-verified — **CWSI_ET PRESENT as a 32-field subset in
     `Data/Processed/satellite/stats_current.zarr` (cwsi_et, field×539 dates)**, CWSI_LST/ETa/ETrF
     absent as processed field stats, TVDI derived proxy from existing per-scene LST/NDVI stats).
     Five-gate evaluator ready (commit 5ee5feb, `scripts/trial_gates.py` — operationalizations
     recorded before the full run). NEXT: user runs the three training commands (~1–2 min/seed,
     handed off 2026-11-14) → `trial_part_b_severity.py` → A/C/D → `trial_gates.py` → finding 22.
  Advisor OQ6/A3 sign-off still applies before any retraining decision beyond this trial's scope.

- **D3. Patch-level program (created 2026-11-15; 11 changes PROPOSED, all valid, NONE applied;
  2026-11-16 audit added `farm-local-anomaly-scoring` and extended the comparison study).**
  Owner directive (notes.md 2026-11-15 + validation guide same day): add patch-level analysis,
  subset-first, with runtime estimation + checkpoint/resume built in; the owner request AMENDS the
  "no parallel architecture trials" prohibition for THIS program only. Architecture source:
  `research/Architecture_Selection_for_Self_Supervised_Spatiotemporal_Anomaly.md` (2D CNN stem →
  per-location GRU, prediction primary + masked-recon aux, ~90k params, no pooled latent).
  Progress 2026-11-16: **R0.5 zonal distribution arm IMPLEMENTED**
  (`monitor/zonal_dist.py` + `scripts/run_zonal_dist_study.py`): the three-way
  prompt structure Zonal Mean / Zonal Distribution Statistics / Patch now has
  its middle rung, built from the statistics already in `stats.zarr` with no
  training and no extraction (presets level=8ch ≡ b1 / lower=8ch p10-only /
  spread=14ch / dist=45ch; the `level` arm is proven to reproduce `b1`
  exactly). 27 tests. NEXT for this arm: the severity/MDM80 sweep on the locked
  evaluation panel (user data), the `b0_calendar` DOY variant and the
  `p10`-only path-max scorer.
  The audit follow-up verifies locked patch extraction, the train-only norm
  sidecar and causal train/scoring inputs on fixtures. See the
  [patch input runbook](docs/patch_inputs.md). Next: audit the **existing**
  freeze on the archive machine, then verify a fresh bound export and review
  the preregistered patch PoC; do not refreeze or recompute frozen checkpoints.
  Fold-matrix execution stays blocked until fold-aware calibration and scoring
  are wired. The checkout suite does not certify the strict real-data gate.
  Execution order: 0 `training-holdout-invariant` (STANDING invariant, owner
  2026-11-15: holdout farms/dates frozen BEFORE implementation, fail-closed in
  every training path, pixel-level included) → 1 `patch-data-pipeline` (patches.zarr) → 2 `patch-level-controlled-trial`
  (subset PoC, gates G1–G5, finding 23) → 3 `compare-spatial-representation-strategies`
  (representation ladder R0 zonal mean / **R0.5 zonal distribution statistics (std, p10, iqr —
  already in stats.zarr, no training)** / R1 patch-32 / R2 sub-crops / R3 multi-scale, plus the
  heterogeneity battery (static-pattern control, white-noise null, per-pixel alarm frequency), the
  extent sweep {0.1,0.3,0.6,1.0}, the paired detectability-crossing table and required 30 m
  resolution arithmetic; gated on PoC gates; owns the scale sweep delegated from E5; finding 24) +
  `patch-scoring-ensemble` (E8 + C1/C2/M3; basis labels) +
  `farm-local-anomaly-scoring` (NEW 2026-11-16: farm-local vs population-ranked basis labelling,
  per-field shrunk σ arm, cross-farm independence tests, ratoon/variety scale strata, farm-level
  anomaly summary; answers the owner's "compare each patch with the same farm's own history"
  requirement) +
  `gradual-severity-shape` (3rd temporal shape + secondary peak/recovery shapes) → 4
  `patch-contamination-absorption` (E7) +
  `patch-full-run-and-ablations` (scale-up + E2–E6 + TCN/Mamba challengers + SSL-off control +
  classical baselines + error analysis + pre-registered final criterion) → 5
  `patch-generalization-suite` (L3 matrix) + `patch-independent-indicators` (E10 + physical CWSI +
  weather/neighbor external consistency) + `patch-xai-attribution` (patch-level XAI, new
  capability). Conditional fallback: `anomaly-definition-path-b` — pre-registered, applies ONLY if
  BOTH path-C trials fail their detection gates.

### Resolved

- **2026-11-16 — spatial prompts audited against the written changes (agent):** the owner's two
  spatial research prompts (controlled representation comparison; farm-internal detection) were
  mapped requirement-by-requirement in `docs/audits/spatial_prompts_vs_openspec_2026-11-16.md`.
  Outcome: prompt 1 ≈80% covered, prompt 2 ≈60% covered, nothing implemented (all changes open).
  Amendments applied the same day: `compare-spatial-representation-strategies` gained R0.5
  distribution statistics, the heterogeneity/noise battery, the extent axis, the crossing table,
  honest R0 pairing and the resolution-report requirement; `patch-level-controlled-trial` gained
  the farm-boundary input-masking requirement + invariance tests; `patch-scoring-ensemble` gained
  basis labelling with a farm-local default; `patch-independent-indicators` gained the
  population-referenced indicator-z label and a farm-own variant; `patch-full-run-and-ablations`
  E4 gained the ratoon/variety cell; and the new change `farm-local-anomaly-scoring` owns the
  per-field σ arm, independence tests and farm-level summary. Remaining known limits recorded in
  the audit (223/370 fields have ≥2 cycles ⇒ partial pooling is forced, not chosen).
- **2026-11-15 — B6 (five-shape protocol) DECIDED (user):** recommendation adopted —
  peak-disruption + recovery-disruption promoted as pre-registered SECONDARY diagnostic shapes
  (folded into `gradual-severity-shape`; primary gates stay on the index-drop family, no
  goalpost movement); growth-delay stays inside path-B gating (D1 unchanged). With the three
  primary shapes + two secondary shapes, the validation guide's five synthetic types are fully
  mapped.
- **2026-11-15 — A4 (validation-ladder write-up) DELIVERED (user):** the full validation guide
  arrived and is mapped onto the existing L1–L5 ladder (identical levels): claims weighted L1–L3
  primary + L4 external consistency + L5 benchmark; synthetic detection = sensitivity evidence,
  never stress proof; External Consistency Analysis (weather + neighbors) added to
  `patch-independent-indicators`; model selection without GT = sensitivity/stability/FAR-burden
  balance; novelty = the COMBINATION, held as hypothesis (queued item 12). Guide content stored
  in agent memory (validation-guide-2026-11-15); operational pieces landed in the D3 changes.
- **2026-11-14 — OQ5 / B4 (date count) RESOLVED (user):** one date's metadata was corrupted —
  `data/DATA_SUMMARY.md` §5 names it: **2022-08-07 metadata GeoJSON missing** → **538 usable dates is
  the canonical count** (539 scene files on disk). Counts updated in data/README.md,
  data/DATA_SUMMARY.md, docs/KNOWLEDGE_BASE.md §13, docs/findings/01, docs/findings/14,
  docs/final_plan.md, and the data-and-phenology-readiness change notes (archived change docs left as
  historical record).
- **2026-11-14 — product vision recorded (user):** the pipeline must accept newly added data
  (future acquisitions/fields) without redesign — new data will be reserved for validation; keep the
  current 538-date archive fixed. Any future openspec change must keep the ingest path
  data-refresh-friendly (manifest-driven, no hard-coded date counts).
- **2026-11-14 — desk implemented + archived:** `add-halqeh-anomaly-desk` implemented as the ninth
  platform view (commits 136028c / 9fbde4f / 871e0f1 / a0b1dfb incl. payload export + gate evidence)
  and archived (7e00f17, spec `platform-anomaly-desk`); the working branch was merged — history now on
  `main`.
- **2026-11-14 — `wire-platform-to-real-data` archived** (ff3ccd6; specs: `platform-real-data` created,
  `platform-visualization` updated). Carried reminder cleared.
- **2026-11-14 — pushed:** `main` == `origin/main` (0 ahead / 0 behind); the 2026-11-13/14 session
  commits (contract v5, finding 16, archive, desk) are all on origin. GitHub default branch: verify
  `main` is default after the push (was `kilo/noble-drum-b7o`).
- **2026-11-14 (was: 1704 vs 799 cycle-count discrepancy):** recount (fixed `data_quality_report.py
  --all`) = 800 non-censored cycles, matching the archive 799 within 1 trailing-censoring cycle;
  findings-02 count is stale. Segmentation decision rule applied via the cycle audit — see finding 14
  (exclusion list `reports/cycle_audit/exclusion_cycles.csv`) and finding 15 (method write-up).
  Remaining follow-up: optional winter-harvest segmentation tuning.

### Not blocked (startable on user approval alone)

- M2 normal-bank scorer as an *experimental* arm (openspec change; final adoption gated on A1/A3).
- M3 event-FAR + POT declustering re-computation of finding-16 metrics (analysis-only, no retraining).
- Items 1–3, 6–11 openspec candidates once their user-gated questions (B1) are answered.
- **Item 12 `novelty-positioning-verification`** (owner guide §10, 2026-11-15): the claim "first
  unsupervised agricultural anomaly detection" is NOT defensible — 2017 unsupervised RS anomaly
  paper, 2024 aerial-MIM AD (already in corpus: Shikhar & Sobti 2404.08931), Oct-2026
  Mediterranean water-use screening (Scientific Reports). Verify the 2017 + 2026 papers against
  the 84-paper matrix, then phrase novelty as the COMBINATION (long-term per-farm Landsat +
  per-farm historical pattern learning + phenology-cycle awareness + SSL temporal representation +
  label-free growth-deviation detection + multi-level validation) — hypothesis pending
  verification, not a proven claim — in method_design_ssl.md and the thesis text.

## Thesis-level reminders

- **Standing holdout invariant (owner, 2026-11-15):** farms and dates completely
  excluded from training are identified and frozen BEFORE any implementation —
  holdout = test-block farms (whole-field, all periods) + post-2024 dates + all
  future acquisitions/fields; fail-closed enforcement in EVERY training path,
  pixel-level included (`training-holdout-invariant`). Always observed.
- Platform = research validation dashboard for pipeline output; claims must match the validation-ladder rung.
- **Claims weighting (owner validation guide, 2026-11-15):** main thesis claims on L1–L3; L4 =
  external consistency evidence (weather + neighbors + indicators); L5 = benchmark comparison.
  Synthetic detection is sensitivity evidence, never stress proof — the thesis deliverable is a
  trustworthy GROWTH-ANOMALY detection system, not a stress classifier.
- Models must detect **phenology-phase anomalies** — the proxy rule is magnitude-only (CWSI affine); only checkpoint models are phase-aware. Keep this distinction in every validation claim.
- ~~`openspec archive wire-platform-to-real-data` pending~~ — archived 2026-11-14 (ff3ccd6).
8. **After the OQ6 advisor answer (carried over from the archived `2026-11-14-train-and-finalize-main-architecture`):**
   — the authoritative, expanded list of open questions/blockers now lives in
   **"Open questions & blockers" above (A1–A4 / B1–B8 / C1–C7)**; this item tracks the execution side only.
   - Update the interim perturbation set (design D6) per the answer; the extended-severity diagnostic in finding 16 says detectable anomalies start at ~6–8×MAD at cycle-level FAR 5% — decide severity scale (across-field MAD vs model-residual scale) and whether FAR stays cycle-level or moves to bin-level.
   - Resume task 6.2 (single-change model tuning until plateau) — paused because the primary metric had no dynamic range at 1×MAD; tuning on it optimizes noise.
   - Tasks 11.1–11.6 (skill adoption: scholar-evaluation, literature-review/citation-management, scientific-writing, benchmark-methodology/eval-harness, mle-workflow) — pending user approval (11.6 installs skills locally).
   - Optional: winter-harvest segmentation tuning (findings 14/15 follow-up); `openspec archive wire-platform-to-real-data` still pending after its item 1 lands.
