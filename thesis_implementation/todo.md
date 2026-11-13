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

## Open questions (waiting on user)

1. **Validation ladder full write-up** (the 5 levels) — send whenever ready; blocks item 5's spec.
2. METRIC products: confirm which interpolated product is authoritative for daily values (item 1) — scene rasters vs `interpolation/` semantics.
3. For the full-archive axis: keep the completeness stat semantics (invalid acquisitions count as missing) as-is?
4. `rust/` crate was added by coding-agent commits, not by the user; its `32.7×` claim is unreproduced. Keep (and verify) or remove?
5. Date count: METRIC 539 scenes vs `stats.zarr` 538 dates — which date is missing and why?
6. **For the advisor (Dr. Hamzeh):** which stress signatures and magnitudes are realistic for Amirkabir sugarcane in Landsat time series (water deficit, salinity, waterlogging, pests/disease, early ripening, lodging)? Decides the final perturbation set of `train-and-finalize-main-architecture` (design D6; interim set used until then). Five sub-questions from findings 13 §3.3:
   - pre-harvest irrigation cut-off — timing and magnitude?
   - pre-harvest burning — does it occur and what is its NDVI/LST signature?
   - which disturbances are transient vs chronic?
   - typical NDVI drop magnitude in mid-season water stress?
   - waterlogging occurrence and which months?
   Literature review task 0.3 runs in parallel.
7. **1704 vs 799 cycle-count discrepancy:** `docs/findings/02_phenology_cycles.md` reports 1704 non-censored cycles, but real490 stats show 799 cycles (`splits_490.json`). Recount needed (finding 13 R8) before the 10%/25% segmentation decision rule can be applied.

## Thesis-level reminders

- Platform = research validation dashboard for pipeline output; claims must match the validation-ladder rung.
- Models must detect **phenology-phase anomalies** — the proxy rule is magnitude-only (CWSI affine); only checkpoint models are phase-aware. Keep this distinction in every validation claim.
- `openspec archive wire-platform-to-real-data` pending after item 1 lands.
