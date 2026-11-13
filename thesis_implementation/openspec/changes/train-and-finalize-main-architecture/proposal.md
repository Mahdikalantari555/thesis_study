# Proposal: Train and Finalize the Main Architecture (`train-and-finalize-main-architecture`)

## Why

The real490 review (`consideration.md`, 2026-11-10) found that no current model result can be cited: RQ2 trained for 2 epochs with 1 seed, `nan_to_num` filled 35.7 % of `X` with zeros, the platform's `masked_transformer` slot shows a CWSI formula (circular), and there is no fixed, non-circular development metric. The agreed order is **model-first**: bring one main architecture to a plateau on a frozen dev protocol, then run validation (RQ1–RQ8) once on a locked test set.

The thesis vision is **field monitoring**: for every Landsat acquisition date of every field, the system says whether the field is in a *suspected stress* state, using only observations up to that date (early warning). Stress type is not required at this stage. Later (not in this change) the self-supervised output will feed an active-learning loop in which farmers report where and when stress actually happened.

## What Changes

- **Frozen data protocol**: one locked test set (cycles starting on or after 2024-01-01 plus one spatially contiguous block of fields), one dev set, one train set. A split manifest with hashes; tests assert no overlap. Normalization statistics come from train only.
- **Causal monitoring task**: each model scores a cycle step by step using only bins at or before the current acquisition. The output per (field, acquisition date) is `normal | suspected_stress | no_data`.
- **Missing data handled with an observation mask**, never by zero filling.
- **Two candidate architectures + references**: causal Masked Transformer (main), causal GRU-AE (cheap deep baseline), B1 PhaseZ causal (reference), B0 calendar. Masked Transformer is also trained without LST as an ablation. Mamba, JEPA and 3D-CAE are deferred to the pixel-level extension.
- **Development metric agreed with the user**:
  - Primary: detection rate at a 5 % cycle-level false-alarm rate on injected perturbations of 1×MAD severity in dev, with median detection delay in days.
  - Secondary: AUC-PR on partial cycles (25 / 50 / 75 %), masked NRMSE, and a severity curve from 0.5 to 2×MAD.
  - Target: at least +0.05 detection rate over B1 PhaseZ causal, with the 3-seed ranges not overlapping.
  - Plateau: three consecutive single changes that each add less than 0.01, or less than the seed standard deviation.
- **No tuning on CWSI, ETa or `y_stress`** during development (they are reserved for L4 validation).
- **Platform-ready outputs**: the frozen model writes per-observation scores and a binary flag with `model` provenance into the existing exporter contract (bumped to v5), so the platform shows them directly. Without a checkpoint, SSL slots become `absent` instead of a CWSI proxy.
- **Laptop-first execution rules**:
  - At most 15 min per seed and at most 500 k parameters on CPU; the same code runs on CUDA (lab GPU or Colab).
  - Visible progress during training.
  - The agent runs only smoke tests and hands long training commands to the user.
- **Incremental training: placeholder only** (interface and documentation, no implementation).
- **Realistic sugarcane perturbations**: an interim set is used now. A literature review task and an open question for the advisor decide the final set.

## Capabilities

### New Capabilities
- `model-development-protocol`: frozen splits, dev metric, perturbation set, plateau rule, seeds, experiment log, compute budget, execution rules.
- `field-stress-monitoring`: causal per-acquisition stress status per field, its threshold calibration, and its output artifact.

### Modified Capabilities
- `model-output-ingest`:
  - Checkpoint registry gains `masked_transformer_main` and `gru_ae_main`.
  - SSL slots never fall back to a CWSI proxy.
  - The contract adds per-observation `stressFlag`.

## Impact

- `src/ssl_anomaly/eval/real_archive.py`, `src/ssl_anomaly/eval/synthetic.py` (MAD-scaled injection, new perturbation types), `src/ssl_anomaly/eval/growth_ssl.py`, `src/ssl_anomaly/models/masked_tf.py`, `gru_ae.py`, `src/ssl_anomaly/baseline/` (causal B1)
- New: `scripts/build_locked_splits.py`, `scripts/train_main.py`, `scripts/eval_dev.py`, `scripts/freeze_main_model.py`
- `scripts/platform_channels.py`, `scripts/cycle_inputs.py`, `scripts/load_model_checkpoints.py`, `scripts/export_platform_data.py`, `platform/src/data/channels.ts`, `data.ts` (contract v5)
- `reports/dev_log.csv`, `reports/dev/`, `checkpoints/`
- `docs/methods_explained.md`, `docs/platform_score_methods.md`, `todo.md`, `AGENTS.md`

## Out of Scope

- Running RQ1–RQ8 / data-scarcity validation (after plateau, separate change), and the code fixes listed in `consideration.md` §2 that concern only validation scripts (RQ7 synthetic probes, RQ1 PermissionError, stale reports).
- Any tuning against CWSI, ETa, `y_stress`, or yield.
- Stress type classification; pixel-level models; Mamba/JEPA/3D-CAE.
- Implementing incremental/continual training or active learning.
