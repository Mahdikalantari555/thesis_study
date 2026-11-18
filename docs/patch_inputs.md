# Locked patch inputs and training handoff

Use this workflow on the authorized archive machine in the `geo` environment,
from the repository root. The v2 patch inputs change the cycle window,
normalization and covariate contract. **Keep the existing frozen manifests,
legacy stores, sidecars and checkpoints.** Use new output paths rather than
migrating any of those artifacts in place.

## 1. Check the existing freeze without writing

```bash
python scripts/build_holdout_manifest.py --audit-existing
```

This verifies both locked cycle files and checks that the frozen holdout refers
to the same split hash, uses the same date cutoff and excludes every field in
`kmeans.test_block_fields`. Additional frozen exclusions remain in force. If
it fails, stop and investigate the mismatch; do not replace the freeze to
recover coverage. `--skip-cycle-file-check` is inspection-only, not this gate.
Only if the holdout was never frozen, inspect `--dry-run` and then freeze once
with the actual declared archive end (`--archive-end 2026-09-10` for the
recorded archive). The locked date cutoff still applies if no end was declared.

## 2. Estimate and verify a fresh export

```bash
# Adjust input locations on the archive machine. Choose a NEW run directory.
splits=data/processed/splits_locked.json
holdout=data/processed/holdout_manifest.json
cycles=data/processed/cycles_490.parquet
mask=data/interim/field_mask.tif
scenes=D:/RS/Thesis/Data/Metric/scenes
work=data/patch_runs/v2_check
store="$work/patches.zarr"
norm="$work/norm_stats.json"

export_args=(--splits "$splits" --cycles "$cycles" --mask "$mask" --scenes-root "$scenes")
python scripts/extract_patches.py "${export_args[@]}" --estimate-runtime
python scripts/extract_patches.py "${export_args[@]}" --smoke 3 --out "$work/smoke/patches.zarr"
```

`--estimate-runtime` prints the estimated window reads and wall time before any
raster is opened. Review the smoke store's shapes, valid pixels and `n_obs` on
known intersecting cycle dates (use `--fields` and `--dates` on a **separate**
smoke output if the first few acquisitions precede the sampled cycles). The
full export is owner-run only, after this review; use the measured estimate as
the planning budget:

```bash
python scripts/extract_patches.py "${export_args[@]}" --out "$store"
# If interrupted, repeat the identical command with --resume.
```

Resume uses the same scene selection, mask, patch size and scale mode, with the
same immutable source rasters. It skips completed fields listed in
`.manifest.jsonl` and writes `provenance.json` in the store. The locked parquet
provides stable IDs and half-open intervals `[t_start, t_end)`. The store records
inclusive offsets `t_start` and `t_end - 1` relative to the verified locked
`base_date`. No scene outside that interval can contribute even if the 36-bin
grid extends farther. The store can contain dev and test cycles; possession
of the store is not permission to train on them.

## 3. Freeze the normalization, then check the trainer

Build the sidecar only once, after the export completes:

```bash
python scripts/build_patch_norm.py --store "$store" --splits "$splits" \
  --holdout-manifest "$holdout" --out "$norm"

python scripts/train_patch.py --store "$store" --splits "$splits" \
  --holdout-manifest "$holdout" --norm "$norm" --out "$work/checkpoints" \
  --device cpu --arch patch_cnn_gru --seed 13 --estimate-runtime
python scripts/train_patch.py --store "$store" --splits "$splits" \
  --holdout-manifest "$holdout" --norm "$norm" --out "$work/checkpoints" \
  --device cpu --arch patch_cnn_gru --seed 13 --smoke --max-fields 8 --max-cycles 1
```

Use only a selection with admissible train cycles. The offline builder reports
progress, admitted cycle count and sidecar SHA-256; an existing sidecar is never
replaced. It fits `stats[sensor][channel]` median/IQR on finite, QA-valid
in-polygon observations from the store's admissible **locked train** cycles.
Training and scoring apply `(x - median) / IQR` when the scale exists, report
channels left in raw units if a sensor/channel scale is unavailable, and carry
the per-channel mask through to the scoring target. Physical-unit challenges
are applied before normalization. The fixed per-bin count covariate is
`log1p(n_obs) / log1p(255)`; no suffix count changes an earlier input.

The smoke checkpoint, frozen copy of `norm_stats.json`, `progress.jsonl` and
`run_manifest.json` are under `$work/checkpoints/patch_cnn_gru_seed13/_smoke/`.
Repeat the identical smoke command with `--resume` to check reuse. The real PoC
still requires the preregistered subset, measured CPU budget and gate review;
`--max-fields` is a smoke/performance throttle, not a preregistration method.

## 4. Score only matching artifacts

Once the approved PoC has a new checkpoint and its **freshly fitted clean dev
calibration** residual scale table, a single-seed locked-dev invocation is:

```bash
run="$work/checkpoints/patch_cnn_gru_seed13"
python scripts/eval_dev.py --run-id patch_inputs_v2_seed13 --model patch_cnn_gru \
  --scorer patch_cnn_gru --seeds 13 --device cpu --patch-store "$store" \
  --holdout-manifest "$holdout" --patch-checkpoint "$run/last.pt" \
  --patch-sigma "$run/patch_sigma.npz"
```

The dev runner uses the canonical locked splits and masked cache. It checks
cycle IDs and bounds, the checkpoint input protocol, seed, holdout and norm.
It defaults to the trainer's adjacent `norm_stats.json`. The separate sigma
preparation is part of the real PoC, not a refit during scoring: use the
`fit_patch_sigma` contract for clean calibration residuals, with `sigma`,
`fallback`, `n`, `min_n`, `sha256`, `model_sha256` (checkpoint file hash),
`norm_sha256` and `input_protocol` recorded in the NPZ. Never attach new hashes
to legacy scales. Use a new `--run-id` for a fresh report. The patch JSON under
`reports/dev/<run-id>/` does not substitute for the pending calibrated FAR,
PoC comparison and dev-log review. Fold-matrix execution also remains blocked
until it can score its actual held-out cohorts rather than the ordinary dev
sweep. No real patch training or release result is implied by fixture passes.
