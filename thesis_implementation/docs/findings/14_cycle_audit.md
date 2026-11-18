# Finding 14 — Cycle Audit (D2): segmentation error rate on real490

**Status (2026-11-14, final):** agent pre-labeled all 94 plots. The user
reviewed the confirmation procedure (documented in this file §6), stated they
could not judge the plots themselves, and **explicitly delegated the
confirmation to the agent's pre-labels** (user message, 2026-11-14, Persian).
The labels below therefore stand as **agent-only visual judgment** — a
limitation recorded for the thesis; a future cross-check against planting/
harvest records (optional task 2.4) can validate them independently.
**D2 outcome (population point estimate 7.9 % < 10 %): proceed to training
with the 38 flagged/suspect cycles excluded** (`reports/cycle_audit/exclusion_cycles.csv`);
the CI upper bound (16.3 %) does not exclude the 10–25 % tuning band, so the
winter-harvest tuning fix stays a recommended follow-up. The exclusion list
is applied by `build_locked_splits.py` (train task 1.1).

> **History:** the 2026-11-11 draft of this finding reported a 96.7 %
> `overlap_with_neighbour` rate and a "BLOCKING" verdict. That result was void:
> the flag compared cycles of *different fields* in the same block (staggered
> harvest makes calendar overlap normal), not the field's own neighbouring
> cycle per design D2. The tooling was fixed on 2026-11-14 (commit `37e4187`);
> the artifacts had been gitignored as "deprioritized" (commit `87071cd`) and
> are tracked again as of `b13be3a`. The corrected audit found
> `overlap_with_neighbour` = **0 / 800** — the same-field invariant holds.

## 1. Metadata (corrected --all run)

- Script: `scripts/audit_cycles.py --all` (fixed version), seed `20261111`
- Generated: 2026-11-14, git SHA `b13be3a` at run time
- Data source: `D:\RS\Thesis\Data\Processed\satellite\stats_long.parquet`
  (NDVI computed from red+nir; stats_long carries no `ndvi` band)
- Population: **800 non-censored cycles** from 490 scanned fields
  (0 fields without usable red/nir, 0 segmentation errors)
- Reviewed set: 94 cycles = 60 stratified (start year × length tercile × block)
  + 34 flagged-extra; 94/94 PIL plots rendered (`reports/cycle_audit/plots/`)
- Agent pre-labels: `reports/cycle_audit/pre_labels.csv`

## 2. Cycle-count reconciliation (resolves OQ7 / R8)

| Source | Non-censored | Fields | Note |
|---|---|---|---|
| `docs/findings/02` (2026-10 era) | 1704 | 490 | **superseded** — older segmentation vintage |
| `cycles_490.parquet` / `growth_cycles_490.npz` | 799 | 370 with ≥1 non-censored (478 total incl. censored-only) | the training archive (binned 36×8 tensors) |
| Recount via `data_quality_report.py --all` (fixed) | **800** | 490 scanned | 0 errors, 0 skipped |
| Audit population (`audit_cycles.py --all`) | **800** | 490 scanned | same pipeline, independent run |

**Conclusion:** the 1704 count is stale; the current segmentation yields
800 ≈ 799 (+1 trailing-edge censoring difference between re-segmentation and
the archived file). 93/94 sampled cycles match the archive by
(field, cycle_id) with lengths agreeing within 15 d (91/93); `start_harvest`
differs only by epoch convention (archive: days from series start; audit:
days from 1970-01-01). The training archive covers **370 fields** — the
remaining registry fields contribute censored-only cycles. The locked splits
(train task 1.1) will be built over the archive's 799-cycle population.

## 3. Sanity flags (population 800)

| Flag | Count | Population rate |
|---|---|---|
| `overlap_with_neighbour` (same-field, per D2) | **0** | 0.0 % — invariant holds |
| `length_out_of_range` (<240 d / >480 d) | 35 | 4.4 % (16 short, 19 long) |
| `no_clear_ndvi_drop` / `few_valid_obs` / `peak_ndvi_low` | 0 | 0.0 % |

## 4. Agent pre-label results (94 reviewed cycles)

Labels use the D2 error classes: `correct`, `harvest_shift_gt30d`, `split`,
`merged`, `not_sugarcane_fallow` (none found), `too_sparse` (none found).

| Label | n | Share of reviewed | Wilson 95 % CI |
|---|---|---|---|
| correct | 67 | 71.3 % | — |
| **merged** (two real annual cycles joined by a missed harvest) | **19** | 20.2 % | [13.3 %, 29.4 %] |
| **split** (fragment; boundaries not at troughs / no establishment phase) | **6** | 6.4 % | [3.0 %, 13.2 %] |
| **harvest_shift_gt30d** (boundary not at a trough) | **2** | 2.1 % | — |
| **any segmentation error** | **27** | **28.7 %** | **[20.6 %, 38.6 %]** |

Confidence split of the 27 errors: 17 `merged` confident, 2 `merged` suspect,
6 `split` suspect, 2 `shift` suspect.

**The dominant defect is systematic, not random:** 18 of the 19 long
(>480 d) cycles are `merged` — two real annual cycles joined because the
winter harvest was missed. Signature: an interior NDVI trough to 0.10–0.25
during Dec–Feb followed by full regrowth to ≥0.6 (e.g. `field67_c2`: crash to
0.15 with a 4-month gap mid-cycle; `field53_c1`: trough 0.2 in 2020-02;
`field75_c2`/`field77_c1` also start mid-cycle at NDVI 0.5). Root cause
hypothesis: `detect_harvests` prominence (0.15) / rise rules reject the
shallow winter troughs, so the detector keeps both seasons as one cycle.
The 6 `split` suspects are short fragments whose start boundary sits at
NDVI ≈ 0.25–0.3 (no establishment phase) — the complementary error.

## 5. Error-rate bases and the D2 decision rule

The design D2 rule uses the segmentation error rate:
<10 % proceed (flagged cycles excluded) / 10–25 % tune parameters first /
>25 % blocking.

| Basis | Rate | Wilson 95 % CI | D2 band |
|---|---|---|---|
| Reviewed set (94; enriched with flagged cycles — NOT a population estimate) | 28.7 % | [20.6 %, 38.6 %] | >25 % |
| Stratified sample only (60) | 6.7 % | [2.6 %, 15.9 %] | <10 % |
| **Population estimate** (19 long-flag × 94.7 % + 16 short-flag × 37.5 % + 765 unflagged × 5.1 %) | **7.9 %** | **[4.7 %, 16.3 %]** | **<10 % (point), crosses 10–25 % at upper bound** |

Conditional rates: P(error \| long flag) = 18/19 = 94.7 % [75.4 %, 99.1 %];
P(error \| short flag) = 6/16 = 37.5 % [18.5 %, 61.4 %];
P(error \| unflagged) = 3/59 = 5.1 % [1.7 %, 13.9 %].

**Reading (agent recommendation, pending user confirmation):** the point
estimate (7.9 %) falls in the <10 % band → training may proceed **with the
flagged/suspect cycles excluded from dev/test metrics**. The exclusion list =
all 35 sanity-flagged cycles + the 4 unflagged suspect-error cycles
(`413_c2`, `453_c1`, `157_c1`, plus `99_c4` kept with a note) ≈ 39/800
(4.9 %). Two honest caveats: (a) the CI upper bound reaches 16.3 %, so the
10–25 % band cannot be excluded; (b) the merged-cycle defect is systematic
(winter-harvest misses) and corrupts the DSH phase bins of every affected
cycle — exclusion is mandatory, and a segmentation-tuning follow-up
(prominence/plateau rules for winter troughs) is recommended as a separate
change proposal regardless. The user confirms 20 cycles before this reading
is final; if the confirmation contradicts the pre-labels, the rates and this
recommendation are recomputed.

## 6. User confirmation set (task 2.2) — 20 cycles

**Waived 2026-11-14:** the user delegated confirmation to the agent's
pre-labels after receiving the explanation of the procedure. The set below is
kept as the reference subset for any future independent cross-check (e.g.
against planting/harvest records, optional task 2.4). The judgment criterion
for each plot: a correct cycle rises from bare-soil NDVI (~0.1–0.2) to a
single plateau and falls to a trough at the end boundary; a merged cycle
contains a full interior crash-and-regrow; a split fragment starts or ends
away from any trough.

| # | field_cycle | len | pre-label | plot |
|---|---|---|---|---|
| 1 | 53_c1 | 501 | merged (confident) | `field53_cycle1.png` |
| 2 | 67_c2 | 485 | merged (confident) | `field67_cycle2.png` |
| 3 | 75_c2 | 484 | merged (confident) | `field75_cycle2.png` |
| 4 | 77_c1 | 484 | merged (confident) | `field77_cycle1.png` |
| 5 | 112_c1 | 485 | merged (confident) | `field112_cycle1.png` |
| 6 | 148_c4 | 503 | merged (confident) | `field148_cycle4.png` |
| 7 | 183_c1 | 495 | merged (confident) | `field183_cycle1.png` |
| 8 | 340_c3 | 532 | merged (confident) | `field340_cycle3.png` |
| 9 | 371_c2 | 497 | merged (suspect) | `field371_cycle2.png` |
| 10 | 157_c1 | 432 | merged (suspect) | `field157_cycle1.png` |
| 11 | 99_c5 | 215 | split (suspect) | `field99_cycle5.png` |
| 12 | 385_c2 | 185 | split (suspect) | `field385_cycle2.png` |
| 13 | 437_c1 | 186 | split (suspect) | `field437_cycle1.png` |
| 14 | 413_c2 | 315 | harvest_shift (suspect) | `field413_cycle2.png` |
| 15 | 453_c1 | 339 | harvest_shift (suspect) | `field453_cycle1.png` |
| 16 | 321_c2 | 187 | correct (short) | `field321_cycle2.png` |
| 17 | 60_c4 | 219 | correct (short) | `field60_cycle4.png` |
| 18 | 99_c4 | 346 | correct (mid-dip note) | `field99_cycle4.png` |
| 19 | 370_c1 | 414 | correct | `field370_cycle1.png` |
| 20 | 47_c1 | 397 | correct | `field47_cycle1.png` |

## 7. Outcome and follow-ups

1. **D2 outcome recorded (2026-11-14):** proceed to training; exclusion list =
   `reports/cycle_audit/exclusion_cycles.csv` (38 cycles: 35 sanity-flagged +
   3 unflagged agent-labeled errors). Applied by `build_locked_splits.py`
   (train task 1.1), which must join on (field, cycle_id) against the archive
   population and log the actual dropped count (799-cycle NPZ vs 800 re-segmented).
2. **Recommended follow-up (separate change proposal):** tune winter-harvest
   detection (prominence/plateau rules for shallow Dec–Feb troughs; see
   `docs/findings/15_cycle_segmentation_method.md` §7), then re-run
   `audit_cycles.py --all`.
3. `data_quality.json` full re-run recorded the recount (800) — OQ7 resolved;
   OQ5 resolved 2026-11-14 (2022-08-07 metadata corrupted → 538 usable dates canonical).
4. Method write-up for the advisor: `docs/findings/15_cycle_segmentation_method.md`.
