# Change: training-holdout-invariant

## Why

Owner directive (2026-11-15): a STANDING invariant — **farms and dates that
are completely excluded from training must be identified and separated
BEFORE implementation, always**, and this must hold explicitly for
pixel-level training too. The locked splits already embody it structurally
(`monitor/splits.py:201-208`: all uncensored cycles of the 51 test-block
fields → test regardless of period; every cycle starting ≥ 2024-01-01 →
test; train = other fields' pre-2024 cycles only), and the product vision
(2026-11-14) reserves future acquisitions and new fields for validation.
What is missing is the formal statement, a FROZEN holdout manifest, and
fail-closed enforcement in every training path — including the patch
program, whose per-pixel store legitimately contains holdout fields (needed
for evaluation) and therefore MUST exclude them at the training consumer,
not by convention.

## What Changes

- **Frozen holdout manifest** — derived from splits_locked `9aa5eb11…`
  (no new split invention): `holdout_farms` = `kmeans.test_block_fields` plus any
  field added to the registry after the archive freeze (future fields are
  holdout by default, per the product vision); `holdout_date_start` =
  2024-01-01 plus every acquisition after the 538-date archive end (future
  scenes are holdout by default). Frozen with SHA-256; changes require the
  same `--force <reason>` discipline as the locked splits.
- **Fail-closed enforcement helper** — `monitor/holdout.py`:
  `assert_train_only(field_ids, cycle_keys/periods)` raises on ANY holdout
  farm or holdout-period cycle reaching a training consumer. Wired into
  `train_main.py` now and REQUIRED (spec'd) for every future training path:
  `train_patch.py`, R2/R3 representation variants, fold retrains, and the
  contamination-training runs.
- **Extraction ≠ training, explicitly** — `patches.zarr` SHALL contain all
  fields (evaluation needs them); the invariant applies at the training
  consumer. The patch Dataset spec gains the fail-closed holdout filter.
- **Subset manifests draw from the non-holdout pool only** — the PoC subset,
  generalization folds, and contamination-fraction selections are all
  validated against the holdout manifest before use.
- **Explicit non-goals:** no re-splitting; no change to the locked splits'
  semantics; no evaluation-path changes (dev/test reading rules stay as
  locked); no platform changes.
