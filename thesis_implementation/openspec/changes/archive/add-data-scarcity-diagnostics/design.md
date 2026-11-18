# Design — Data-Scarcity & Representation-Quality Diagnostics

## Context

`docs/findings/11_rq1_to_rq8_empirical_framework.md` (Finding 11) established RQ1–RQ8 results, but the advisor's core question — *is 539 dates / 32 farms enough data, i.e. does the model actually suffer from data scarcity?* — needs dedicated instruments. Locally available data: `data/processed/fields.zarr` = 32-farm Khuzestan subset, **539 Landsat dates (2014–2025)**, plus `cycles.parquet` (produced by `python -m ssl_anomaly.cli segment`). The calibrated 490-field × 13.5-year simulator in `eval/cv.py` remains the drop-in full-archive fallback (`--simulate-490-if-missing`).

Mapping to the literature checklist (from the advisor message):

| Advisor checklist item | Diagnostic | Implementation |
|---|---|---|
| Learning curve (20%→100% of training data) | `DS1` | `learning_curve()` in `eval/data_scarcity.py` |
| Train vs validation gap | `DS2` | `train_pretext_arm_tracked()` in `models/pretexts.py` |
| Cross-validation / seed variance | `DS5` | `eval/stats.bootstrap_ci`, `paired_wilcoxon`, LOYO from `eval/cv.py` |
| Representation collapse (cosine) | `DS3a` | `mean_cosine_similarity()` |
| Alignment & Uniformity (Wang & Isola) | `DS3b` | `alignment_uniformity()` |
| k-NN / linear probing on embeddings | (exists) + `DS4` few-shot | `eval/probing.py` + new `few_shot_probe()` |
| Few-shot (1%/5%/10% labels) | `DS4` | `few_shot_probe()` with `LogisticRegression` |
| t-SNE/UMAP of embeddings | `DS3c` | `tsne_projection()` (sklearn TSNE, PCA fallback) → PNG |
| Leave-One-Year-Out | (exists) | `eval/cv.py` LOYO, reused |
| Comparison vs simple baselines | (exists) | RQ1 ladder (`run_rq1_benchmark.py`) |

## Goals / Non-Goals

**Goals:**
- Give an honest, quantitative answer to "does the model suffer from data scarcity?" on the available archive: learning-curve slope at 100%, train/val gap trend, collapse/alignment/uniformity of frozen embeddings, few-shot degradation, seed/LOYO variance.
- Provide `docs/eval_protocol_future_models.md` so every future model runs the same diagnostics before any data-sufficiency claim.

**Non-Goals:**
- No new architectures; no patch/3D-CAE; no changes to the `Anomaly ≠ Stress` gate; no ONNX/edge work.
- Few-shot labels use a **weak proxy** (top-decile mean CWSI per cycle) — reported as representation usefulness, never as validated stress (gate still required).
- Simulated 490-field numbers are labeled as simulated scaling checks, not real measurements.

## Decisions

1. **`eval/data_scarcity.py` (new)** — pure functions + orchestration helpers:
   - `mean_cosine_similarity(emb, max_pairs=20000, seed=42)`: sampled mean of pairwise cosine sim; 1.0 = full collapse.
   - `alignment_uniformity(emb, groups=None)`: alignment = mean `||z_i − z_j||²` over same-group pairs (positives = same field, different cycles; if `groups` is None, nearest-neighbor pairs); uniformity = `log mean_{i≠j} exp(−2||z_i−z_j||²)` (Wang & Isola 2020, t=2). Normalize embeddings to unit norm first (cosine geometry).
   - `embedding_quality_report(emb, groups)`: returns dict with `n`, `dim`, `mean_cosine_sim`, `alignment`, `uniformity`, `effective_rank` (participation ratio of singular values — extra collapse guard).
   - `learning_curve(train_fn, eval_fn, fractions, seeds)`: generic — `train_fn(fraction, seed)` returns a model, `eval_fn(model)` returns a float metric; returns per-fraction mean/CI over seeds plus the raw per-seed values. Keeps the module model-agnostic so future models plug in.
   - `few_shot_probe(emb, labels, fractions=(0.01,0.05,0.10), n_repeats=20, seed=42)`: repeated stratified subsampling of labels, `LogisticRegression(max_iter=1000)` on frozen embeddings, out-of-sample `AUC-ROC` + `AUC-PR` on the held-out remainder; returns mean/CI per fraction.
   - `tsne_projection(emb, labels=None, seed=42)`: sklearn `TSNE(n_components=2, init="pca", learning_rate="auto")` with `PCA` fallback if TSNE fails; returns 2-D coords (also embedded into the JSON report, figure drawn by the runner).
2. **`models/pretexts.py`** — additive only: new `train_pretext_arm_tracked(arm, train_tokens, n_bands, *, val_tokens=None, epochs, batch_size, lr, seed) -> (model, history)` where `history = {"train_loss": [...], "val_loss": [...]}` per epoch. Implemented by extracting the per-batch arm loss into `_arm_batch_loss(model, arm, bx, bp, n_bands, rng)` shared with `train_pretext_arm` so the two never drift. Existing `train_pretext_arm` keeps its exact signature/return.
3. **`scripts/run_data_scarcity.py`** — mirrors `run_rq2_pretexts.py` data loading (`compare_ssl_models._load_records_and_cwsi`); for each arm in `--arms` (default `anomaly_degradation,masked_recon`) and each seed in `--seeds` (default `42,43,44`):
   - full-data model → frozen embeddings of all cycles → `DS3` quality report + t-SNE coords (+ PNG colored by weak-proxy label);
   - `DS2` tracked train on an 85/15 inner split → train/val curves, final gap, best-val epoch;
   - `DS1` learning curve at `--fractions` (default `0.2,0.4,0.6,0.8,1.0`) with downstream `AUC-PR` on the fixed perturbed-vs-clean pool (reuses `run_rq2_pretexts._perturb_tokens`);
   - `DS4` few-shot on frozen embeddings vs weak-proxy labels (top 20% mean-CWSI cycles = positive);
   - `DS5` aggregates seed std + LOYO-year std (via `eval/cv.generate_splits_dict` on cycles) for the full-data AUC-PR.
   - writes `reports/data_scarcity.json` + `reports/data_scarcity.csv`; figures under `reports/figures/` (git-ignored).
4. **Weak-proxy labels** come from `cwsi_et` inside `fields.zarr` (mean over cycle window), top 20% = positive — same construction as RQ1's natural weak-proxy positives, explicitly labeled `weak_proxy_not_validated_stress` in the report.
5. **Packaging**: `matplotlib>=3.8` added to `pyproject.toml`; `uv.lock` regenerated with `uv lock`; root `environment.yaml` mirrors pyproject (conda channels: conda-forge/pytorch defaults, pip section) for non-uv users; `dvc.yaml` gains a `data_scarcity` stage.

## Risks / Trade-offs

- **[Risk] Runtime on 2-core CPU** → *Mitigation*: default `--epochs 30`, `--seeds 42,43,44`, arms default to two; `limit_threads(2)` like other runners; learning curve reuses the same backbone (~1.4 s/arm at 45 epochs measured in RQ2).
- **[Risk] t-SNE nondeterminism** → *Mitigation*: fixed seed, `init="pca"`, coords stored in JSON so the figure is reproducible.
- **[Risk] Few-shot labels are a weak proxy** → *Mitigation*: report field explicitly as `weak_proxy`; no stress claim; validation gate untouched.
- **[Risk] Alignment needs positive pairs** → *Mitigation*: positives = same-field different-cycle embeddings (fields are the natural semantic groups); fallback to 1-NN pairs when groups unavailable.
