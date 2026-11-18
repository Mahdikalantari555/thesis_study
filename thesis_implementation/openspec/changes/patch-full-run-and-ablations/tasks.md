# Tasks — patch-full-run-and-ablations

## 1. Plan + plumbing

- [x] 1.1 Pre-registered run plan file: every planned run (factor, seeds,
      venue, estimate, output paths) BEFORE the first launch; pruning rule
      (single-seed screening → 3 seeds for finalists) written in.
- [x] 1.2 Benchmarking fields in train/eval manifests (psutil RAM, CUDA
      VRAM, MACs, per-field-cycle inference); unit test on manifest
      completeness (AGENTS.md §7).
- [ ] 1.3 Scale-up run (user-executed, estimate first): winning PoC config
      on all train fields, seeds ×3; agent reviews produced reports.
- [x] 1.4 TCN challenger module behind a flag (causal dilated conv, kernel
      3, dilations 1/2/4/8, mask-aware) + causality tests — built ONLY if
      the E3 trigger fires (GRU slow/unstable per the plan's criteria).

## 2. Ablations (each: agent smoke → user runs → agent reviews)

- [ ] 2.1 E2 aux-weight {0, 0.3}; decision: keep aux only if MDM improves.
- [ ] 2.2 E6 LST-off checkpoint (feeds patch-independent-indicators).
- [ ] 2.3 E4 covariates ladder (+weather last, conditioned AND
      unconditioned reported). The ladder gains ONE cell for the
      between-farm differences the owner prompt names: ratoon/cycle kind and
      variety group (already present in `cycles_490.parquet` and used by
      `baseline/robust.py` strata, absent from every model covariate set) —
      added to the patch covariates and compared against the no-stratum arm;
      whether the SCALE should depend on ratoon/variety is separately owned
      by `farm-local-anomaly-scoring`.
- [ ] 2.4 E5 inner-buffer + burn-in variants (the scale/representation sweep
      lives in `compare-spatial-representation-strategies`).
- [x] 2.5 Sensor-offset estimation script (near-coincident L8/L9 pairs over
      the AOI) + applied/not-applied comparison.
- [ ] 2.6 E3 challengers if triggered: TCN + TinyCNNMamba; record the
      CNN-Mamba title implication for the advisor discussion.
- [ ] 2.7 SSL-off random-init control (same architecture/scoring) +
      optional One-Class SVM arm next to the existing B3 (IsolationForest +
      ECOD); each method's temporal-information level reported (guide §5
      fairness).

## 3. Final decision

- [ ] 3.1 Comparison table: all arms × {acute, persistent, gradual} MDM80,
      Wilson CIs, prevalence, paired-bootstrap arm-vs-reference
      differences; criterion evaluated verbatim.
- [ ] 3.2 Winner frozen (model card + sidecar + hashes) → hands off to
      patch-generalization-suite (L3 matrix) and patch-xai-attribution.
- [ ] 3.3 Error analysis (guide §9 step 8): FP review with weather/neighbor
      context; FN decomposition by family × severity × phenophase; causes
      recorded.
- [ ] 3.4 Persian finding (persian-writing skill): the decision record —
      criterion result, per-cell decisions, benchmark table, error-analysis
      chapter; honest negative fully written if the criterion fails (the
      floor as the finding), L-rung labelling throughout.

## Implementation notes (data-free half, 2026-11-16)

Built and unit-tested; each item below names what still needs the archive or
the GPU. Nothing here launches a run — the agent never does that.

**1.1 Pre-registered run plan — DONE (machinery).**
`ssl_anomaly/train/run_plan.py` (`build_run_plan`, `plan_sha256`, `save_plan`,
`load_plan`, `amendment`) + `scripts/run_plan.py`
(`--register/--verify/--show/--amend`) + `tests/unit/test_run_plan.py` (23)
and the CLI cases in `tests/unit/test_full_run_cli.py` (9). The plan carries
every cell's factor, seeds, venue, estimate and output path, the pruning rule
as text, the pre-named finalists, and a sha256 over the payload; `load_plan`
refuses a plan whose hash does not match, so an edit-after-registration is
caught instead of being discovered in the write-up. Changing the plan is
`amendment(...)` (reason + approver required, previous hash recorded).
TCN cells are excluded unless `include_tcn=True` / `--include-tcn`, because
pre-allocating them would pre-decide the E3 question.
*Data-blocked:* the owner must run `--register` with the real
seconds/epoch measured on the venue, then review and save the file before the
first launch.

**1.2 Benchmarking fields — DONE (machinery + wiring).**
`run_plan.benchmark_block` records `peak_ram_mb` (psutil, absent → `None`, never
0), `cuda_peak_mb`, `n_parameters`, `macs_per_forward` (dense Conv2d/Linear
estimate via forward hooks, `None` on a shape mismatch), `ms_per_field_cycle`,
`device`, `torch_version`, `recorded_at`, `platform`. `validate_manifest`
encodes the AGENTS.md §7 completeness rule against the keys `train_patch.py`
actually writes, and `attach_benchmark(strict=True)` refuses an incomplete
manifest. `scripts/train_patch.py` now measures the block from a real training
batch (kept as `example` inside `train_one_seed`), writes
`manifest_missing_fields`, and warns on incompleteness; `--no-benchmark` exists
for smoke debugging and stamps `benchmark_absent_reason` so a benchmark-free
manifest is never mistaken for a measured one.
*Data-blocked:* the numbers themselves come from the owner's runs; the
applied-vs-not comparison is an owner run.

**1.4 TCN challenger — DONE (gate + module).**
`ssl_anomaly/models/tcn_challenger.py`. The E3 trigger is now a written rule,
not a judgement: `evaluate_trigger(manifest)` reads the run's OWN epoch history
and benchmark block and fires on either arm — **slow** (any epoch over
`MAX_EPOCH_SECONDS=240`, per-field-cycle inference over
`MAX_MS_PER_FIELD_CYCLE=250`, or inference time never measured) or **unstable**
(`stability_report`: fewer than `MIN_EPOCHS_TO_JUDGE=3` epochs, final epoch
above best + `1.0·sigma`, or a rising second-half slope). An *unjudgeable*
history fires the trigger: that is the fail-closed direction, since the cost of
a false fire is one extra cell while the cost of a false pass is the temporal
claim. `TriggerVerdict.require_built()` raises for a caller who tries to skip
the challenger with a fired trigger, and `decide_temporal_module` returns
`pending` (not "incumbent wins") until the TCN has actually been run; a tie
inside one standard error goes to the simpler/faster variant — the GRU.
The module is `build_tcn` (causal dilated Conv1d stack, kernel 3, dilations
1/2/4/8 → receptive field 31 bins, LEFT-only padding, per-timestep channel
normalization, observed-fraction input so a mostly-empty patch is not a bare
zero). **Both design rules are enforced by tests, not by intent:**
`causality_violations` perturbs each bin and shows no output at `t < t0` moves
(and a deliberately leaky module does fail it); a masked bin's garbage value
cannot change earlier outputs. 22 tests in `tests/unit/test_tcn_challenger.py`.
Note recorded during implementation: `nn.GroupNorm`/`BatchNorm`/time-wise
`LayerNorm` all pool across T and leak the future, so the block normalizes over
the channel axis only — that is why the first GroupNorm draft failed the
causality test.
*Data-blocked:* whether the trigger fires at all, and the GRU-vs-TCN decision,
need the scale-up run's real history.

**2.5 Sensor-offset estimation — DONE (machinery).**
`ssl_anomaly/io/sensor_offset.py` + `scripts/sensor_offset.py` +
`tests/unit/test_sensor_offset.py` (33) and the store-level cases in
`test_full_run_cli.py` (8). Pairs are cross-sensor and within one field, at most
one partner per cycle (closest day), `MAX_GAP_DAYS=3`; the offset is
`median(L8 - L9)` per band with a MAD-derived 95 % CI, and a band is
`resolved` only when it clears `MIN_PAIRS=10` AND its CI excludes zero.
`apply_offsets` converts L8 into the L9 reference frame, leaves NaN pixels NaN,
and REFUSES an unresolved band unless `allow_unresolved=True` is passed
explicitly (and records that it was). The applied-vs-not decision is
pre-registered in `comparison_plan` / `decide_applied`: keep the offsets only if
L8-only FAR does not rise AND the L8/L9 era gap shrinks by at least
`MIN_ERA_GAP_REDUCTION_FRAC=0.25`; both conditions are required. Two contract
details found while wiring the script: the store's `sensor_id` is **per bin**, so
a cycle whose observed bins span both sensors is skipped and counted rather than
used as a pair member; and `estimate_offsets` takes `channel_names` so a band's
offset is read off its own channel row (without it a caller passing all channels
would estimate "red" from row 0 and apply it silently) — both are now tested.
*Data-blocked:* the offsets themselves, the applied-vs-not arms, and their
numbers.
