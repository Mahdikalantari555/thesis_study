# Proposal — Data-Scarcity & Representation-Quality Diagnostics (`DS1–DS5`)

## Why

Finding 11 (`docs/findings/11_rq1_to_rq8_empirical_framework.md`) answers RQ1–RQ8 with LOYO validation, multi-seed confidence intervals, linear probing, and baseline ladders, but it does **not** answer the advisor's key question: *does the model actually suffer from data scarcity on the 539-date, 32-farm archive, or not?* The literature-standard instruments for that question — **learning curves over training-set fractions**, **train-vs-validation gap**, **cross-fold/cross-seed variance**, **SSL representation-quality metrics** (representation collapse via mean cosine similarity, Wang & Isola **alignment & uniformity**), **few-shot downstream performance** (1%/5%/10% labels), and **embedding visualization** (t-SNE) — are currently missing from the codebase. Without them, any claim that "the model is data-hungry" or "539 dates are enough" is unsubstantiated.

## What Changes

- **New eval module `src/ssl_anomaly/eval/data_scarcity.py`** implementing five diagnostic families:
  1. `DS1` **Learning curve**: train the controlled pretext arm on increasing fractions of the training cycles (`20%→100%`), score a fixed held-out perturbed-vs-clean pool (`AUC-PR`), report mean + 95% bootstrap CI per fraction and per seed.
  2. `DS2` **Train-vs-validation gap**: extend `models/pretexts.py` with a tracked training variant (`train_pretext_arm_tracked`) that records per-epoch train and validation pretext loss on an inner split, reporting final gap, best-val epoch, and whether the gap widens (overfitting signature).
  3. `DS3` **Representation quality (SSL)**: `embedding_quality_report` computes mean pairwise **cosine similarity** (collapse detector; →1 means collapse), **alignment** (mean squared distance of same-field positive pairs; lower = tighter), and **uniformity** (Wang & Isola `log E exp(-2||u−v||²)`; lower = better spread) on frozen cycle embeddings, plus a **t-SNE** projection (scikit-learn; PCA fallback) saved as a figure.
  4. `DS4` **Few-shot downstream**: stratified 1%/5%/10% label fractions on frozen embeddings with `LogisticRegression`, evaluated out-of-sample (`AUC-ROC`/`AUC-PR`), against weak-proxy cycle labels (top-decile mean CWSI as positive, documented as a weak non-claim proxy).
  5. `DS5` **Variance across seeds/folds**: reuse `eval/stats.bootstrap_ci`, `paired_wilcoxon`, and LOYO folds from `eval/cv.py` to report std across seeds and across LOYO years for every DS1–DS4 number.
- **New runner `scripts/run_data_scarcity.py`** (same data-loading pattern as `run_rq2_pretexts.py`: real 32-farm `fields.zarr` + `cycles.parquet`, `--simulate-490-if-missing` fallback via `eval/cv.py`) writing `reports/data_scarcity.json` / `.csv` and `reports/figures/data_scarcity_*.png`.
- **Tests** `tests/unit/test_data_scarcity.py` (synthetic embeddings: collapse=1 for identical vectors, alignment=0 for identical positives, uniformity finite; learning-curve plumbing with a dummy trainer; few-shot shapes; tracked trainer history length).
- **Docs**: new finding `docs/findings/12_data_scarcity_diagnostics.md` (index updated) with the measured numbers on the available archive, and **`docs/eval_protocol_future_models.md`** — the mandatory evaluation protocol for every model trained in the future (which diagnostics, which commands, which thresholds count as "data-scarce").
- **Packaging**: add `matplotlib>=3.8` to `pyproject.toml` dependencies, regenerate `uv.lock`, add root `environment.yaml` (conda env spec), and register a `data_scarcity` stage in `dvc.yaml`.

## Capabilities

### New Capabilities
- `data-scarcity-diagnostics`: Learning-curve, train/val-gap, SSL representation-quality (collapse/alignment/uniformity + t-SNE), few-shot probing, and seed/fold variance diagnostics for any pretext arm, runnable on the real 32-farm archive or the calibrated 490-field simulator, with JSON/CSV/figure reports.
- `future-model-eval-protocol`: A documented, command-level protocol (`docs/eval_protocol_future_models.md`) that every future model must pass before any "enough data" claim is made.

### Modified Capabilities
- `self-supervised-model` (`models/pretexts.py`): gains an optional tracked-training entry point `train_pretext_arm_tracked` (per-epoch train/val loss history). Existing `train_pretext_arm` signature and behavior unchanged.

## Impact

- **Code**: new `src/ssl_anomaly/eval/data_scarcity.py`, new `scripts/run_data_scarcity.py`, small additive change in `src/ssl_anomaly/models/pretexts.py`, new `tests/unit/test_data_scarcity.py`, `eval/__init__.py` export update.
- **Reports**: `reports/data_scarcity.{json,csv}`, `reports/figures/data_scarcity_*.png` (PNGs git-ignored per existing convention).
- **Docs**: `docs/findings/12_data_scarcity_diagnostics.md`, `docs/findings/00_index.md` update, `docs/eval_protocol_future_models.md`.
- **Packaging/pipeline**: `pyproject.toml` (+matplotlib), `uv.lock` regen, new `environment.yaml`, `dvc.yaml` stage `data_scarcity`.
- **Non-goals**: no new model architectures, no patch-level/3D-CAE expansion, no changes to the `Anomaly ≠ Stress` validation gate, no claim that simulated 490-field numbers are real measurements.
