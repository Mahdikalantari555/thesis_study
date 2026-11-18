# Design: Integrate Real Model Outputs into the Platform Data Pipeline

## Context

The platform renders anomaly scores for 7 "models" (`b0_calendar`, `b1_dsh`,
`b1_cusum`, `masked_transformer`, `sts_net`, `tiny_cnn_mamba`, `time2agri`) that were
all derived from a single CWSI proxy rule `clamp(offset + max(0, cwsi - 0.45) * weight)`
in `scripts/export_platform_data.py` (BUG-23, rank-correlated ρ ≈ 0.633 with CWSI).
Trained checkpoints exist — `checkpoints/sts_net_490.pt`, `checkpoints/tiny_cnn_mamba_490.pt`,
`checkpoints/time2agri_490.pt` (from `scripts/train_literature_checkpoints.py`) — but were
never loaded at export time. This change wires real checkpoint inference into the export
while keeping the platform honest about where every number came from.

## Goals / Non-Goals

**Goals:**
- Load the three literature checkpoints and score per-field phenology cycles.
- Record per-score provenance (`model` | `proxy` | `absent`) and a formula id per observation.
- Graceful degradation: missing/broken checkpoints never crash the exporter and never fake scores.
- Contract v3 in `scripts/platform_channels.py` ↔ `platform/src/data/channels.ts` with parity tests.

**Non-Goals:**
- Retraining; only inference from frozen checkpoints.
- A real-time inference backend (scores stay pre-computed static JSON).
- Reconstructing the main SSL pipeline's Lightning `.ckpt`s (different tokenizer,
  `d_in` includes dtime/doy/sensor features — not cycle inputs).

## Decisions

### 1. Model artifact format (already fixed by training)

`scripts/train_literature_checkpoints.py` saves `torch.save` dicts with keys
`architecture`, `state_dict`, `center`, `scale`, `shape`, `n_bands`,
`parameter_count`. `center`/`scale` are the per-channel robust normalization
(median, 1.4826·MAD) fitted on `(N, 36, 8)` cycle tensors — 36 phase bins of 15
days (max 540 days since harvest) × 8 channels `[ndvi, blue, green, red, nir,
swir1, swir2, lst]`. These sidecar stats make the checkpoints self-contained: no
separate config file is needed, `scripts/load_model_checkpoints.py` reconstructs
the bare model from `architecture` + `shape`/`n_bands` using the same constructors
as `ssl_anomaly.eval.growth_ssl.MaskedSSL.fit`, loads the state dict, and reuses
`MaskedSSL.score` verbatim (causal=True, batch 32 — matching training-time
masking). If a checkpoint cannot be reconstructed (corrupt artifact, shape
mismatch), that model's provenance is `absent` with a clear log; scores are never
faked.

### 2. Cycle tensor building must replicate the training distribution

The exporter rebuilds per-field cycles with `segment_cycles` (same parameters as
`scripts/segment_and_export_cycles_490.py`: `min_cycle_days=180`,
`max_cycle_days=540`, `min_prominence=0.15`, `plateau_frac=0.7`, `rise_frac=0.15`),
then bins acquisitions into 15-day bins counted from the harvest that begins the
cycle, NDVI + 7 zarr bands, per-bin medians, and the same interior-gap
interpolation. Censored cycles and cycles with < 3 usable observations are
skipped exactly as in training (`scripts/cycle_inputs.py::build_field_cycles`).

### 3. Inference interface and observation mapping

`LoadedModel.score_cycles(X (n_cycles, 36, 8)) -> (n_cycles, 36)` returns the
per-bin leave-one-time-bin-out reconstruction error in z-space. Each monthly
observation is mapped to `(cycle_row, phase_bin)` by its *acquisition* date
(`lookup_cycle_bin`): find the non-censored cycle with
`t_start <= day < t_end`, then `bin = (day - harvest_day) // 15`. The raw error
is squashed monotonically `score = 1 - exp(-err)` into (0, 1) so platform
colours and the 0.55 anomaly threshold stay meaningful; ranking is preserved.
The squash is applied exactly once — the exporter squashes the full error
matrix (`squash_bin_error`) and `resolve_observation_scores` only rounds the
already-squashed bin value. Days in censored/skipped spans produce no bin and
fall back (see 5).

### 4. Provenance mapping (contract v3)

Every observation gains `scoreProvenance: {score_key: model|proxy|absent}` and
`scoreFormulaId: {score_key: id|null}`:

| Situation | Provenance | score | scoreFormulaId |
|---|---|---|---|
| Checkpoint loaded, bin mapped, finite error | `model` | `1 - exp(-err)` | `<model>_490:bin_mse_1mexp` |
| No artifact for the key (b0/b1 baselines, masked_transformer) or unmapped day / NaN bin | `proxy` | CWSI rule | `cwsi_affine_v1` |
| Artifact exists but reconstruction failed | `absent` | `null` | `null` |
| No acquisition in revisit window (stale) | `absent` | `scores: null` | `null` |
| `--no-models` flag | `proxy` for all 7 | CWSI rule | `cwsi_affine_v1` |

`masked_transformer` deliberately stays `proxy`: its Lightning `.ckpt`s are the
main-pipeline transformer trained on tokenizer tokens (dtime/doy/sensor features,
d_model 64), not on `(36, 8)` growth cycles, so scoring cycles with them would be
unfaithful. The registries (`SCORE_REGISTRY` / `SCORES`) declare which score keys
are expected to be model-backed, and parity tests enforce both sides agree.

### 5. Fallback behaviour

`load_model_checkpoints()` returns per-model status `loaded | missing | failed`;
the exporter logs the plan at startup ("Score provenance plan: model=[...]
proxy=[...] absent=[...]") and a per-provenance tally after the run. Missing
checkpoints or `--no-models` degrade to the unchanged CWSI proxy rule labelled
`proxy`; only an existing-but-unreconstructable artifact yields `absent` for that
key (a null score that the UI renders via its existing `NUMERIC_FALLBACK`), never
a fabricated number.

### 6. Frontend surfacing

`mock.ts::normaliseObs` parses the two new maps (defaults from the score registry
for pre-v3 payloads), `DATA_PROVENANCE.scoresAreProxy` becomes payload-derived,
and the MapExplorer inspector score card gains a `ProvenanceChip` whose tooltip
shows `<model_id>: model|proxy · <formula_id>`. No view logic changes: scores
keep the same 0–1 range and keys.

## Risks / Trade-offs

- **7-min cycle rebuild per export** (Whittaker smoothing per field): accepted for
  a static pipeline; a cache file can be added later if export frequency grows.
- **JSON size grows** (~+3 MB for the two per-observation maps on top of the
  existing 7.7 MB): consistent with BUG-26 ("Won't fix"); single-file build only.
- **Squash choice is a display calibration, not a detector calibration**: the
  threshold 0.55 now means z-space MSE ≈ 0.80; the formula id in the payload keeps
  this auditable. A quantile-calibrated threshold can replace it without schema
  changes.
- **Censored trailing cycles**: observations after the last detected harvest fall
  back to proxy; segmentation is unchanged, so behaviour matches training data
  coverage rather than inventing cycle boundaries.
