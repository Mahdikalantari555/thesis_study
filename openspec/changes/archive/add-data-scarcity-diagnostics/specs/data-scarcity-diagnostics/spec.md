# Spec Delta — Data-Scarcity & Representation-Quality Diagnostics

## Purpose

Provide honest, quantitative diagnostics that answer whether the SSL models suffer from data scarcity on the available archive (539 Landsat dates / 32 farms) and that every future model must run before any data-sufficiency claim: learning curves over training-set fractions, train-vs-validation gap, seed/LOYO-fold variance, SSL representation-quality metrics (collapse, alignment, uniformity, t-SNE), and few-shot downstream probing.

## ADDED Requirements

### Requirement: DS1 learning curve over training-set fractions
The system SHALL train the model on increasing fractions of the training cycles (default `0.2, 0.4, 0.6, 0.8, 1.0`) across multiple seeds and report downstream `AUC-PR` (fixed held-out perturbed-vs-clean pool) with mean and 95% bootstrap CI per fraction, plus the raw per-seed values.

#### Scenario: Learning curve computed for a pretext arm
- **WHEN** `scripts/run_data_scarcity.py` runs with `--fractions 0.2,0.4,0.6,0.8,1.0 --seeds 42,43,44`
- **THEN** `reports/data_scarcity.json` contains, per arm, a `learning_curve` entry with one point per fraction, each having `fraction`, `auc_pr_mean`, `auc_pr_ci_95`, `per_seed` values, and a derived `slope_last_segment` (metric gain from 80%→100%) used to judge whether the curve has flattened

### Requirement: DS2 train-vs-validation gap tracking
The system SHALL provide `train_pretext_arm_tracked(...)` in `models/pretexts.py` returning `(model, history)` with per-epoch `train_loss` and `val_loss` on an inner held-out split, without changing the existing `train_pretext_arm` signature or behavior.

#### Scenario: Gap reported per arm and seed
- **WHEN** the runner trains with an 85/15 inner train/val split and `--epochs 30`
- **THEN** the report contains `train_val_gap` per arm/seed with `final_train_loss`, `final_val_loss`, `gap = final_val_loss − final_train_loss`, `best_val_epoch`, `gap_trend`, and `val_loss_rising`, and the JSON flags `overfitting_suspected = true` when validation loss is rising over the last quarter of epochs while train loss is still decreasing (the classic overfitting signature)

### Requirement: DS3 SSL representation-quality metrics (collapse, alignment, uniformity, t-SNE)
The system SHALL compute, on frozen normalized cycle embeddings: mean pairwise **cosine similarity** (collapse; →1 = collapse), **alignment** (mean squared L2 distance over same-field positive pairs), **uniformity** (Wang & Isola, `log E exp(−2‖u−v‖²)`), effective rank (participation ratio of singular values), and a 2-D **t-SNE** projection (PCA fallback), stored in the report and rendered to `reports/figures/`.

#### Scenario: Embedding quality reported per arm
- **WHEN** the runner extracts frozen embeddings for all cycles from the full-data model of each arm
- **THEN** `embedding_quality` per arm contains `mean_cosine_sim`, `alignment`, `uniformity`, `effective_rank`, `tsne_coords` (N×2), and `collapse_suspected = true` when `mean_cosine_sim > 0.95`

### Requirement: DS4 few-shot downstream probing (1% / 5% / 10% labels)
The system SHALL evaluate frozen embeddings with stratified label fractions (default `0.01, 0.05, 0.10`, repeated `n_repeats=20` with fixed seed) using `LogisticRegression` on the labeled subset and out-of-sample `AUC-ROC`/`AUC-PR` on the remainder, against weak-proxy cycle labels (top 20% mean-CWSI = positive) explicitly tagged `weak_proxy_not_validated_stress`.

#### Scenario: Few-shot curve reported per arm
- **WHEN** the runner runs `few_shot_probe` on the full-data embeddings
- **THEN** the report contains per arm a `few_shot` entry keyed by fraction with `auc_roc_mean`, `auc_roc_ci_95`, `auc_pr_mean`, `n_labeled` (actual count), and the `label_source` field set to `weak_proxy_top20pct_mean_cwsi_not_validated_stress`

### Requirement: DS5 variance across seeds and LOYO folds
The system SHALL report std across seeds for every DS1–DS4 headline metric and std across Leave-One-Year-Out folds (via `eval/cv.generate_splits_dict`) for the full-data downstream `AUC-PR`, reusing `eval/stats.bootstrap_ci` / `paired_wilcoxon`.

#### Scenario: Seed and LOYO variance in report
- **WHEN** the runner completes with ≥3 seeds and the cycles parquet is available
- **THEN** the report contains `variance` with `per_metric_seed_std` and `loyo_full_data_auc_pr_per_fold` + `loyo_auc_pr_std`

### Requirement: Future-model evaluation protocol doc
The system SHALL ship `docs/eval_protocol_future_models.md` defining the mandatory command-level protocol (learning curve, train/val gap, DS3 metrics, few-shot, LOYO + baselines, validation gate) and the quantitative thresholds that classify a run as "data-scarce" (e.g. learning curve still rising at 100%, widening train/val gap, cosine collapse > 0.95, few-shot AUC dropping sharply below 10% labels).

#### Scenario: Protocol doc exists and is referenced
- **WHEN** a contributor opens `docs/eval_protocol_future_models.md`
- **THEN** it lists exact commands (`scripts/run_data_scarcity.py ...`, `run_rq1_benchmark.py`, probing), the output files to inspect, and the scarcity thresholds, and is linked from `docs/findings/00_index.md`
