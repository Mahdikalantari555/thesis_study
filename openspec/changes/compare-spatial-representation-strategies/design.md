## Design — compare-spatial-representation-strategies

### R0.5 mechanics (zonal distribution statistics)

The data ALREADY exists: `scripts/extract_stats.py:33` writes
`STATS = ("mean","median","std","p10","p25","p75","p90","iqr")` per
(field, date, band) into `stats.zarr`, and `StatsZarrReader.get_stat` can
read any of them — but the only consumers today are
`monitor/inputs.py:95`, `scripts/export_platform_data.py:454` and
`scripts/segment_and_export_cycles_490.py:55`, all of which read
`"median"`. So R0.5 costs ZERO extraction.

Construction: for each clean/injected field-cycle, build the channel set
`{median, std, p10, iqr}` per band over the same 36-bin grid
(`nanmedian`/`nanpercentile` per bin exactly as `rebuild_masked_cycles`
does for the median), giving a `(36, 4·B)` tensor. Two scoring paths, both
rule-based (no training, hence no capacity or seed confound):

1. `b1_dist` — `B1PhaseZCausal` fitted on the extra channels (its
   per-(phase-bin, band) median/MAD machinery is channel-agnostic; only
   the channel list changes), scored through the unchanged alarm rule.
2. `b0_dist` — the `b0_calendar` robust-DOY path on the same channels,
   because the "lower quantile reveals what the mean hides" question is
   most credible against a calendar reference.

Additional path-max variant: score only the `p10` channel (the prompt's
literal "lower distribution quantiles" question) so the answer is not
diluted by the joint multivariate score.

R0.5 is deliberately rule-based: the ladder's job is to locate where
information about localized anomalies lives, not to add another learned
arm. If R0.5 closes most of the gap to R1, that is a first-class result —
it would say the final pipeline does not need a patch model at all, and
the adoption rule is written to allow exactly that outcome.

### Heterogeneity battery (mechanics)

- **Static-pattern control.** For each field, `chronic(p) = nanmedian`
  over its clean dev cycles of the per-pixel per-channel clean value →
  a per-field offset image `o(p)`. Two normalizations are scored:
  (i) the existing population σ; (ii) `σ` with `o(p)` subtracted first
  (score = residual from the field's OWN persistent spatial structure).
  The comparison answers "is the detected anomaly an event or a chronic
  patch?" A large MDM80 drop under (ii) means the arm was largely
  rediscovering chronic heterogeneity — a finding, not a failure.
- **Spatially-i.i.d. noise null.** The patch applier gains
  `spatial="white"`: the same per-bin δ applied to a random subset of
  in-field pixels with the same mean footprint but no spatial
  autocorrelation. Expectation (recorded BEFORE the runs): MDM80 collapses
  for patch arms and is unchanged for R0 (a field mean averages white
  noise to ~δ·√footprint). The coherent−white gap is the *causal* evidence
  that the patch advantage is spatial coherence, and it is the only test in
  the program that isolates noise averaging from signal preservation.
- **Per-pixel alarm frequency.** On clean dev cycles, per-pixel alarm
  counts over the cycle grid: fraction of pixels alarming in >50% of bins
  (chronic), the pixel-ID overlap between the top-20% sets of successive
  cycles (Jaccard), and the entropy of the per-pixel alarm distribution.
  High overlap = the arm reports heterogeneity; low overlap = events.
  Reported for every representation, no retraining.

### Extent axis and the crossing table

Footprint ∈ {0.1, 0.3, 0.6, 1.0} (the applier already takes a footprint;
`patch-level-controlled-trial` uses 1.0 and 0.3) × the S1–S6 ladder ×
{acute, persistent} for both families, on the same frozen checkpoints —
no retraining, no recalibration (σ tables are fitted on clean residuals).
Two outputs: MDM80 per extent (does detectability fall off with extent the
way a spatial arm should while a mean-based arm stays flat?), and the
per-severity crossing table
`{patch-only, zonal-only, both, neither}` with Wilson CIs and a paired
McNemar-style test over fields, which is the direct answer to the prompt's
"can localized anomalies be detected in patches when they are not visible
in farm-level means".

### Resolution arithmetic (fixed, no measurement needed)

30 m GSD ⇒ 1 px = 0.09 ha. Measured field sides (median 16.7 px, p90 17.0,
max 19.6 px) give a median field ≈ 16.7² × 0.09 ≈ 25 ha. Consequences to
state in finding 24, per row: (a) R1's spatial support is a whole field,
so "patch-level" means intra-field, not sub-field-precision; (b) an R2
16×16 crop spans 480 m ≈ 23 ha, i.e. nearly a whole median field — the
"sub-crop" is coarse, and K crops mostly sample different parts of one
field's interior rather than distinct management zones; (c) any anomaly
smaller than ~2 px (0.36 ha) is not resolvable at 30 m regardless of
representation; (d) LST is resampled from ~100 m, so temperature-based
localized claims carry a coarser effective resolution than the NDVI ones.

### Sub-crop mechanics (R2)

Crop origins are sampled where the 16×16 window lies fully inside the
in-field mask (fraction = 1.0); the crop set is drawn ONCE per (field,
cycle-shape) with a seed and hashed into the run manifest — fixed sets give
deterministic evaluation; per-epoch resampling stays a flag (augmentation
mode) default-off. If a field's in-field area admits fewer than K complete
16×16 windows, K is reduced for that field and the reduction is recorded;
fields with NO valid 16×16 window use a padded full-field 16×16 crop and
are flagged. Field-level scoring: per-crop (bin, channel) scores aggregated
by top-q mean over crops (primary) with majority-vote as the comparison
variant — both feed the UNCHANGED alarm machinery.

### Multi-scale mechanics (R3)

R3a replaces the stem's second conv with parallel dilation branches
(3×3, dilations {1, 2, 4}) summed before GroupNorm — receptive-field
ladder at ~+11k params, no new data path. R3b (true two-scale fusion) runs
the 16×16 crop branch and the 32×32 branch as two stems whose features are
concatenated at the GRU input; it is built only behind the pre-registered
trigger (R2 or R3a showing a context benefit with CI excluding zero).
Capacity matching: every representation's param count lands in the same
table; ±20% is the flagging threshold (AGENTS.md §8 unequal-capacity rule).

### Compute honesty

R2 cost ≈ K × 256 px vs R1's 1024 px per field (K=6 ⇒ ~1.5×) — measured,
not estimated, by the benchmark module. All representations train on the
same device class (CPU-first) and report epoch time + peak RAM.

### Benchmark module

`scripts/bench_spatial_representations.py` measures ONCE, before any
training: Zarr lazy random-read throughput (per-patch ms at 16/32),
materialized preload time + resident RAM, epoch forward/backward throughput
per representation, CPU utilization sampling, peak RAM, disk I/O during a
training epoch. Output: one JSON artifact committed under reports/ + the
recorded lazy-vs-materialized decision + per-epoch estimates that gate the
user-run training commands.

### Relationship to the program

- The `training-holdout-invariant` applies to every representation here:
  crops, folds and subsets draw only from the non-holdout pool, with the
  fail-closed assertion inherited through the shared Dataset base.
- R0/R0.5 arms are rule-based and read only frozen statistics + the locked
  splits; nothing here re-trains them.
- R1 checkpoints and machinery come from `patch-level-controlled-trial`;
  this study adds representations, not a new trial protocol.
- Which *scoring basis* each row uses (that farm's own history vs the
  population) is owned by `farm-local-anomaly-scoring`; this table only
  labels the rows and reports both where the change provides both.
- The severity sweep (3 shapes + secondary), localization probe, σ tables
  and alarm calibration are UNCHANGED — only the representation varies.
- The adoption verdict feeds `patch-full-run-and-ablations` (whose E5
  scale sweep is delegated here) and the final architecture decision.

### Risks

- Sub-crop aggregation can wash out localized signals — top-q aggregation
  and the localization AUPRC on partial-footprint injections protect
  against declaring R2 better while it actually blurs.
- R0.5 could win, which invalidates the premise that patches are needed:
  that is a legitimate, pre-registered outcome and the adoption rule is
  written to accept it (the honest negative of the whole patch program).
- The static-pattern control uses clean dev cycles to build `chronic(p)`;
  it is a *normalizer*, never a training input, and the frozen-σ discipline
  still governs calibration. A field with too few clean cycles falls back
  to the population σ and is listed in the report.
- Noise-null injections are deliberately out-of-family (white noise is not
  a plausible agronomic anomaly) — they are a DIAGNOSTIC, never a severity
  protocol member, and never enter any MDM80 gate.
- K choice bias — swept at single seed before finalists.

- R3b complexity — trigger-gated; if never triggered, recorded as unused.
- Fixed crop sets could under-sample a field's informative region — the
  K-sweep and the resampling flag bound this; noted in the finding.
