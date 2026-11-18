# Tasks: data-and-phenology-readiness

## 1. Literature review
- [x] 1.1 Reuse `thesis_research/SSL_Proposal` paper matrix; list what already covers D1 sections 1–4
- [x] 1.2 Search and read new sources for gaps (phenology extraction, time axis, sugarcane stress signatures, SSL on irregular series) — جستجو به درخواست کاربر متوقف شد، 2026-11-11
- [x] 1.3 Write `docs/findings/13_literature_phenology_and_perturbations.md` (per-paper table + implications + crop-generalisation note)
- [x] 1.4 Perturbation catalogue with sources; mark assumptions; link to advisor question (todo OQ6)
- [x] 1.5 Add plain-language sections to `docs/methods_explained.md` for the methods adopted (sections ۱۵–۱۹ added; see finding 13 R3/R4/R5/R6)

## 2. Cycle audit
- [x] 2.1 `scripts/audit_cycles.py`: sanity flags for all cycles, stratified sample (seed recorded), per-cycle plots (plots skipped: matplotlib segfault on this build)
  - 2026-11-14 fix: the earlier run's `overlap_with_neighbour` flag compared cycles of DIFFERENT fields in the same block — design D2 requires the same field's neighbouring cycles. The 96.7 % flag rate and its "BLOCKING" verdict were void; artifacts had been gitignored as "deprioritized". Script rewritten: same-field overlap invariant, D2 stratification (start year × length tercile × block), full-population scan, PIL-rendered plots (matplotlib savefig segfault workaround). Regression tests: `tests/unit/test_cycle_audit_data_quality.py` (8 passed).
- [x] 2.2 Agent pre-labels sampled cycles; user confirms 20 on the platform — DONE 2026-11-14 with waiver: agent pre-labeled all 94 plots (`reports/cycle_audit/pre_labels.csv`: 67 correct / 19 merged / 6 split / 2 shift); the user reviewed the procedure, stated they could not judge the plots, and **delegated confirmation to the agent's labels** (recorded in `docs/findings/14_cycle_audit.md` §6). Limitation (agent-only judgment) is stated in the finding and can be cross-checked later against planting/harvest records (task 2.4).
- [x] 2.3 Write `docs/findings/14_cycle_audit.md`: error rate with Wilson CI, per class, per year; apply D2 decision rule — DONE 2026-11-14: reviewed-set error 28.7 % [20.6, 38.6]; population estimate 7.9 % [4.7, 16.3] → D2 <10 % band → proceed with 38-cycle exclusion list (`reports/cycle_audit/exclusion_cycles.csv`); method write-up for the advisor added as `docs/findings/15_cycle_segmentation_method.md`
- [ ] 2.4 If planting/harvest records become available: segmentation error in days (optional, non-blocking)

## 3. Data quality
- [x] 3.1 `scripts/data_quality_report.py` → `reports/data_quality.json` (observation density, valid fraction, LST range, NaN fractions, 538 vs 539 dates — discrepancy resolved 2026-11-14: 2022-08-07 metadata corrupted, 538 canonical)

## 4. Decision record (gate)
- [x] 4.1 Add the decision record to `train-and-finalize-main-architecture/design.md` (D11: time axis, segmentation params, perturbation set, exclusion rule, stage-conditioned anomaly detection), citing sections of 13/14
- [x] 4.2 User approval of the decision record (approved by user 2026-11-11 — training sections 2–5 of train-and-finalize-main-architecture are now unblocked)

## 5. Stage-conditioned anomaly detection
- [x] 5.1 `scripts/stage_conditioned_anomaly.py`: stage-conditioned thresholds with npphen-style confidence envelope; does not flag natural phenological decline as anomaly
- [x] 5.2 Write `docs/findings/17_stage_conditioned_thresholds.md` (results: 370 fields, 799 cycles, 18,505 valid obs, 1,774 flagged, 9.59% flag rate) — originally `14_stage_conditioned_thresholds.md`; renumbered 14→17 on 2026-11-14 to fix the duplicate finding number (`14_cycle_audit.md` keeps 14)
- [x] 5.3 Add row 14 to `docs/findings/00_index.md` — row now 17 after the renumber
