# Tasks — patch-independent-indicators

## 1. Indicators (TDD-first)

- [x] 1.1 Physical CWSI module: Idso/Jackson formula, ERA5 Ta join at
      scene time, coefficient registry with sources; unit tests on known
      values; `absent` propagation when a coefficient or Ta is missing.
- [x] 1.2 Indicator z-score pipeline: per-bin aggregation, phenophase-matched
      robust z, exceedance threshold; unit tests on synthetic series. Both
      z-units are produced and labelled: across-field (population-referenced,
      current behaviour) AND farm-own (per-field spread, with the pooled
      fallback and tier counts of `farm-local-anomaly-scoring`); a report row
      without the unit label fails the build.
- [x] 1.3 Availability checker: CWSI_ET / TVDI / physical CWSI / ETa-ETrF
      with coverage counts; `absent` semantics test.
- [x] 1.4 External-consistency module: ERA5 event context (precip deficit,
      Tmax anomaly, ET0, VPD vs historical reference) + neighbor/same-block
      deviation share (block adjacency v1; registry graphs when todo item
      11 lands); alarm classification (local-consistent /
      regional-common-mode / local-unexplained) + candidate causes; unit
      tests on synthetic contexts; `absent` propagation.

## 2. Agreement (runs after gated checkpoints exist)

- [ ] 2.1 Patch part-D adapter: flagged (field, bin) events + per-pixel
      event maps vs indicator exceedance maps; Spearman/enrichment/timing
      with CIs; per-arm table incl. LST-on vs LST-off (E6 dependency) with
      the consistency-vs-corroboration labels.
- [ ] 2.2 Reports + dev_log rows complete (provenance, n, CIs, coverage).

## 3. Verdict

- [ ] 3.1 Persian finding (persian-writing skill): agreement/enrichment/
      timing per arm, the shared-input caveat applied, disagreements
      reported as information, ceiling stated (L3 + proxy; L4 gated on A2).

## Implementation notes (data-free half)

`src/ssl_anomaly/monitor/indicators.py`, 35 tests in
`tests/unit/test_indicators.py`.

- **1.1** `cwsi_idso_jackson` with a *measured* wet/dry baseline, or the
  recorded Idso envelope as a labelled fallback (`baseline_source`). The
  coefficient registry carries the citation per coefficient; a missing
  coefficient or Ta returns `ABSENT` (`"absent"`), never NaN-turned-number —
  otherwise a missing input reads downstream as "no stress".
- **1.2** `indicator_z(..., unit="across_field"|"farm_own")` returns an
  `IndicatorZ` carrying unit, history tier, reference count and
  `fallback_used`. The unit travels with the values because a report row
  without the label is exactly the ambiguity this change exists to remove.
- **1.3** `availability_report` with coverage per indicator, `absent_reasons`
  counted separately, and `usable_for_agreement` at `MIN_USABLE_COVERAGE`
  (0.20). An indicator nobody could compute is reported as not usable — a
  finding, not a crash.
- **1.4** `era5_context` (precip deficit against historical windows of the
  EVENT's length — a per-day comparison would understate a 3-day deficit by
  3×; Tmax/ET0/VPD anomalies), `neighbor_deviation_share`, and
  `alarm_classification` into local-consistent / regional-common-mode /
  local-unexplained with named candidate causes. `regional_common_mode` exists
  so a shared weather event can never be sold as a model success.

**Still needs the data:** 2.1 (agreement runs vs indicator exceedance maps),
2.2 (report rows), 3.1 (Persian finding), and the CWSI/TVDI inputs themselves
canopy temperature, dry/wet baselines from the METRIC archive.
