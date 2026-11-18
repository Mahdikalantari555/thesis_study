# Tasks — compare-spatial-representation-strategies

## 1. Geometry memo + crop machinery (TDD-first)

- [ ] 1.1 Geometry memo: 64×64 padding/neighbor fractions from the measured
      field-size distribution committed under reports/; exclusion + flag
      recorded.
- [ ] 1.2 Crop sampler: in-polygon-guaranteed 16×16 windows derived from the
      32×32 store (no re-extraction); fixed seed-hashed sets in the
      manifest; reduced-K and padded-fallback recording; unit tests
      (in-polygon invariant, reproducibility, fallback listing).
- [ ] 1.3 R2 Dataset + aggregation: per-crop scoring through the unchanged
      PatchDeepScorer interface (top-q mean primary, majority-vote flag);
      aggregation unit tests against hand-computed values.

## 2. R0.5 zonal distribution statistics (rule-based, no training)

- [x] 2.1 Channel builder: per-(field, cycle, bin) `{median, std, p10, iqr}`
      per band on the 36-bin grid, read from the EXISTING `stats.zarr` via
      `StatsZarrReader.get_stat` (no extraction, no new store); unit tests
      on a synthetic cube (bin aggregation matches `nanpercentile` on
      hand-built input, NaN-as-absent discipline, channel order).
      → `src/ssl_anomaly/monitor/zonal_dist.py` (`channel_specs`,
      `stat_channels`, `bin_cycle`), presets `level` (8 ch, = b1),
      `lower` (8 ch, p10 only), `spread` (14 ch), `dist` (45 ch). No
      std-of-NDVI channel is fabricated (a ratio's std is not the ratio of
      stds) — documented and test-enforced. 27 tests in
      `tests/unit/test_zonal_dist.py`.
- [ ] 2.2 `StatsZarrReader._validate_schema` accepts the extra statistics
      without relaxing the field/date/band assertions; a test proves the
      median path is byte-identical to today after the change.
- [x] 2.3 Scoring paths: `b1_dist` (`B1PhaseZCausal` on the extended
      channel set), `b0_dist` (`b0_calendar` on the same channels) and the
      `p10`-only path-max variant; each scored through the unchanged alarm
      rule; unit test that the median-only configuration reproduces the
      current `b1` numbers exactly (regression guard).
      DONE: `fit_score_b1` (b1 reproduction, asserted by the `level`-preset
      identity test and the CLI's `--self-check`), `fit_score_calendar`
      (`b0_calendar` calendar-DOY reference on the same channels), and
      `pathmax_scores` + `channel_z2` (the p10-only path-max, reported
      separately so the lower-quantile answer cannot be diluted).
      `calendar_doy_bins` maps cycle bins to calendar bins.
- [ ] 2.4 Evaluation: R0.5 arms on the identical evaluation panel,
      injection sets and calibration budgets as the patch arms; MDM80 per
      temporal shape + event-FAR + delay reported in the comparison table.
      The calibration half is done (`scripts/run_zonal_dist_study.py`:
      τ at the 5 % cycle-FAR budget on dev clean cycles through the
      unchanged alarm rule, alarm concentration, one markdown table, and a
      `--self-check` that records `max|Δscore|` between the `level` arm and
      the reference `b1` path). **Still open:** the severity/MDM80 sweep,
      which needs the locked evaluation panel + injection machinery (user
      data).
- [ ] 2.5 R0-subset re-score: existing R0 arms scored on exactly the PoC
      evaluation panel with the identical injections, so the representation
      effect is not confounded with training-set size; confound stated next
      to any row that still reuses an all-train-field result.
      **Precondition landed:** `build_distribution_cycles(..., reference_keys=)`
      refuses to build unless the R0.5 cycle population equals the reference
      arm's, cycle for cycle — the pairing the re-score depends on.

## 3. Heterogeneity + noise battery (analysis only, no retraining)

- [ ] 3.1 Static-pattern control: per-field per-pixel clean climatology over
      that field's own clean cycles → chronic-offset normalizer; scored
      alongside population σ for every representation; fallback to
      population σ for fields with too few clean cycles (listed in the
      report); unit test that the offset is leave-one-cycle-out safe.
- [ ] 3.2 White-noise null: `spatial="white"` mode in the patch applier
      (matched mean footprint, random in-field pixel subset, seed-fixed),
      applied to the same δ ladder; MDM80 reported as a diagnostic column
      and excluded from every severity gate (asserted by a test).
- [ ] 3.3 Per-pixel alarm-frequency diagnostic on clean dev cycles:
      share of pixels alarming in >50% of bins, successive-cycle top-q pixel
      set Jaccard overlap, per-pixel alarm entropy; reported per
      representation.
- [ ] 3.4 Summary: a single "chronic vs event vs noise" table per
      representation, with the coherent-minus-white MDM gap and the
      MDM-under-chronic-offset drop stated as numbers.

## 4. Extent axis + detectability crossing

- [ ] 4.1 Footprint sweep {0.1, 0.3, 0.6, 1.0} on frozen checkpoints (no
      retraining, no recalibration): MDM80 and localization AUPRC per
      extent per representation; unit test that footprint 1.0 reproduces
      the existing protocol numbers exactly.
- [ ] 4.2 Crossing table per severity: {patch-only, zonal-only, both,
      neither} counts with Wilson CIs and a paired test over fields;
      committed under reports/ with the paired field list.

## 5. Benchmark module (TDD-first)

- [ ] 5.1 `scripts/bench_spatial_representations.py`: Zarr random-read,
      preload time/RAM, per-representation epoch throughput, CPU util,
      peak RAM, disk I/O → one JSON artifact; runs on CPU.
- [ ] 5.2 Run the benchmark ONCE; record the lazy-vs-materialized decision
      + per-epoch estimates (gates the user-run commands).

## 6. Representations

- [ ] 6.1 R2 config end-to-end (smoke on CPU: shapes, NaN discipline,
      aggregation, estimates).
- [ ] 6.2 R3a multi-dilation stem (flag) + param count check (≈+11k);
      smoke.
- [ ] 6.3 R3b two-scale fusion — built ONLY if the pre-registered trigger
      fires (R2 or R3a context benefit with CI excluding zero).

## 7. Runs (user-executed, estimates first)

- [ ] 7.1 Single-seed screening: R2 K ∈ {4, 6, 8} + R3a; review produced
      reports; pick finalists.
- [ ] 7.2 Finalists × seeds {13, 42, 2026}: full severity sweep (3 shapes +
      secondary) + localization probe + extent sweep + benchmark fields per
      run.

## 8. Verdict

- [ ] 8.1 The ONE transparent table + figure (four dimensions, R0 / R0.5 /
      R1 / R2 / R3 rows, farm-local vs population-ranked labels) committed
      under reports/; pre-registered adoption rule applied verbatim.
- [ ] 8.2 Resolution arithmetic stamped into the table and the finding
      (1 px = 30 m = 0.09 ha; R2 crop = 480 m ≈ 23 ha; LST from ~100 m) —
      a missing support column is a defect.
- [ ] 8.3 Finding 24 (Persian, persian-writing skill): scale-accuracy
      differences stated plainly (the owner's core ask), capacity and
      compute columns beside every accuracy column, the chronic-vs-event
      and coherent-vs-white results, the crossing table, honest negatives
      explicit, L-rung labelling; decision handed to
      patch-full-run-and-ablations.

## Implementation notes (data-free half)

- `monitor/spatial_study.py` — the pure analysis half of finding 24:
  `spatial_support` (30 m ⇒ 1 px = 0.09 ha, 16×16 = 480 m ≈ 23 ha),
  `geometry_memo` (32 px default; 64 px excluded, 3.83× the median field),
  `capacity_flag` (median-referenced ±20 %), `crossing_table` +
  `sign_test` (the PAIRED four-cell detectability table with Wilson CIs and
  an exact binomial test — misaligned arrays are a hard error),
  `alarm_frequency_diagnostic` (per-pixel frequency, successive-cycle top-q
  Jaccard, alarm-count entropy), `static_pattern_normalizer` (a field's own
  clean climatology, floored), `noise_null_gap` (hard-coded
  `gate_eligible=False`), and `render_comparison_table` (one table across
  the four dimensions, with the support column, the basis label and the
  stated confound). 32 tests in `test_spatial_study.py`.
- `scripts/bench_spatial_representations.py` — measures lazy Zarr reads vs a
  materialized preload, records the lazy-vs-materialized decision with its
  rule, times ONE forward+backward per representation (R1 32 px, R2 16 px,
  R3 multi-scale, R1_pixelwise) and extrapolates per-epoch/total hours,
  peak RAM, CPU utilization and the capacity flags into
  `reports/bench/spatial_<stamp>.json`. 7 tests in `test_bench_spatial.py`.
  **Owner command:** `python scripts/bench_spatial_representations.py
  --store data/processed/patches.zarr` (on the data machine).
