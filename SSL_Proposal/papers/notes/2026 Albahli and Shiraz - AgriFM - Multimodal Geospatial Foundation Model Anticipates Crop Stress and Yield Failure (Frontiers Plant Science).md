# AgriFM: A multimodal geospatial foundation model anticipates crop stress and yield failure across climates and species

## Full citation
Albahli, S., & Shiraz, M. (2026). *A multimodal geospatial foundation model anticipates crop stress and yield failure across climates and species*. Frontiers in Plant Science 17:1883297. DOI 10.3389/fpls.2026.1883297

## Problem & setting
- Task: retrospective early crop-stress detection (no stress / drought / heat / compound drought-heat) and yield-failure prediction (seasonal yield below crop-region 20th percentile), across 5 crops (maize, wheat, soybean, rice, sorghum) and 5 agroclimatic regions (North America, Europe, South Asia, East Africa, Latin America).
- Emphasis on transfer: random, geography-split, time-split, and crop-transfer evaluation regimes; deployment metrics include alert lead time, false alerts at matched recall, calibration.
- Data modalities: Sentinel-2 L2A optical, Sentinel-1 GRD radar, MODIS LST + ECOSTRESS thermal, ERA5-Land weather trajectories, SoilGrids soil, topography, sparse management proxies. Unit = field-season (or non-overlapping patch-season), with explicit modality/time masks for missingness.

## Method
- **AgriFM:** modality-specific encoders (spatial-temporal satellite encoder; weather-trajectory encoder with event tokens such as hot-day runs, rainfall-deficit windows, recovery periods; soil/static-context encoder) + **phenology-alignment module** that conditions cross-modal attention on estimated crop developmental stage (not calendar time) + multitask heads (stress class, yield failure, yield anomaly, auxiliary phenology).
- **SSL pretraining on 2.4M field-season sequences:** combination of (i) masked temporal reconstruction, (ii) masked spatial-patch prediction, (iii) cross-modal contrastive alignment, (iv) next-window forecasting. Exact hyperparameters/layer sizes were removed from the revised manuscript (not verifiable in archive).
- Fine-tuning: task-balanced batches, focal loss for rare stress classes, 5 seeds. Uncertainty: heteroscedastic prediction + 5-member deep ensemble + split-conformal calibration.
- Labels: retrospective rule-derived proxies — drought from precipitation/root-zone soil-moisture anomalies, heat from Tmax/Tmin/VPD, compound from overlap in the same phenology window, yield failure from historical 20th percentile; rule-outcome disagreements excluded from fine-tuning. No expert adjudication dataset.
- Explainability: integrated gradients, temporal diagnostics, counterfactual event-token suppression (presented as model-behavior diagnostics, not validated causal explanations).

## Data & labels
- Benchmark "AgriStress-Global": 186,214 labeled field-season records; 2.4M unlabeled sequences for SSL pretraining. Labels are proxy/rule-based, explicitly flagged as a limitation; no prospective field validation.

## Results
- Geography-split stress: AUROC 0.879 vs 0.821 best baseline (late-fusion multimodal transformer, +0.058); AUPRC 0.523 vs 0.418 (+0.105). Time-split yield failure: AUROC 0.891 vs 0.846; AUPRC 0.556 vs 0.428 (+0.128); ECE 0.038 vs 0.061.
- Baseline ladder: logistic regression (AUROC 0.742) < RF 0.761 < XGBoost 0.778 < crop-model hybrid 0.791 < satellite-only transformer 0.812 < late-fusion transformer 0.821 < AgriFM 0.879.
- **Ablations:** removing SSL pretraining = largest drop (stress AUROC −0.041, yield AUPRC −0.074, lead time −8 days); removing weather = −0.037 AUROC / −0.065 AUPRC; phenology conditioning −0.028 AUROC and lead time 24→18 days; radar −0.023; thermal −0.014; soil/terrain small discrimination effect but false-alert benefit 17.3%→13.8%.
- **Alert lead time:** AgriFM median 24 days vs 13 (late-fusion) and 8 (satellite-only); AUPRC advantage +0.11 at 3–4-week horizon; 17.3% false-alert reduction at matched recall via calibration; risk-coverage abstention preserves precision.
- Largest gains on compound drought+heat records: AgriFM alerts 18–24 days earlier than satellite-only baseline.

## What transfers to our thesis
- Confirms the thesis premise quantitatively: **multimodality (optical + thermal + weather) and SSL pretraining are the two largest performance factors** for stress detection under geographic/temporal shift — exactly our Landsat optical+LST cross-year setting. The SSL-removal ablation (−0.041 AUROC, −8 days lead time) is a directly quotable justification for SSL.
- Phenology-conditioned fusion (condition attention on developmental stage rather than calendar date) is a concrete design idea for sugarcane (tillering→grand growth→ripening stages shift with planting/ratoon dates; conditioning on stage rather than DOY should improve cross-year transfer).
- Alert lead time as an evaluation metric (median days before stress confirmation) is a strong addition to our evaluation protocol for early water/salinity stress detection — more decision-relevant than end-of-season accuracy.
- Uncertainty calibration (ensemble + conformal) reducing false alerts 17.3% at matched recall is a practical blueprint for in-field alerting where false positives cost scouting/irrigation effort.
- Rule-derived proxy labels (drought/heat/compound windows from weather+soil moisture) show how "pseudo ground truth" for stress can be constructed without field labels — a possible weak-validation strategy for our sugarcane case when in-field measurements are sparse.
- Counterfactual event-token suppression + integrated gradients = XAI methodology applicable to our XAI requirement (attributing stress alerts to specific drought/heat windows in the Landsat series).

## Limitations / caveats
- Severely weakened paper: the revised version removed all unverifiable details (architecture dims, optimizer, split manifests, per-crop tables, CIs, significance claims) — treat numbers as descriptive effect sizes, not validated results.
- Labels are rule-derived proxies, not physiological measurements; no expert adjudication; no prospective field trial — the authors themselves disclaim operational readiness.
- Sentinel/MODIS/ECOSTRESS mix, not Landsat-only; heavy FM scale (2.4M sequences) is the opposite of our lightweight in-field constraint.
- Management variables (irrigation class, planting window) were coarse proxies with attenuated contribution.
- AUPRC values (~0.42–0.56) show the task itself remains hard under class imbalance.

## Key numbers to quote in lit review
- Multimodal SSL pretraining beats late-fusion under geography shift: stress AUROC 0.879 vs 0.821, AUPRC 0.523 vs 0.418; time-split yield-failure AUPRC +0.128.
- Median alert lead time 24 days vs 13 (late-fusion) and 8 (satellite-only); alerts 18–24 days earlier on compound drought-heat events.
- Removing SSL pretraining is the largest single ablation hit (−0.041 AUROC, −0.074 AUPRC, −8 days lead time).
- Phenology-conditioned fusion beats calendar-time fusion (AUROC 0.879 vs 0.851; lead 24 vs 18 days).
- Conformal-calibrated uncertainty cuts false alerts 17.3% at matched recall; ECE 0.038 vs 0.061.
