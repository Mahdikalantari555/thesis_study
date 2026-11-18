# OPTIMUS: Observing Persistent Transformations in Multi-temporal Unlabeled Satellite-data

## Full citation
Yu, R., Han, P., Myers-Dean, J., Wolters, P., & Bastani, F. (2025). *OPTIMUS: Observing Persistent Transformations in Multi-temporal Unlabeled Satellite-data*. WACV 2025. arXiv:2506.13902 [cs.CV]. https://arxiv.org/abs/2506.13902

## Problem & setting
- Task: binary classification of satellite image time series — does a location contain a *persistent* (lasting >1 year), non-seasonal change (deforestation, urban expansion, lake recession, wildfire impacts) vs no change / only cyclic seasonal change?
- Data: Sentinel-2 (RGB bands B2/B3/B4 only, cloud-filtered <20%) and NAIP; 512×512 px at 10 m/px (5×5 km); 1,000,000 unlabeled time series for training, each 30–48 images spanning Jan 2016–Dec 2023 (8 years), minimum 2-month interval between images.
- Evaluation set: 300 labeled time series (~1/3 positive); a 100-series subset split into 1,600 128×128 patches with binary labels for localization. Global random sampling, deliberately non-urban-biased.

## Method
- **SSL pretext (temporal-order recovery):** hide timestamps; train a Siamese binary classifier on triplets (A1, A2, Q) to predict whether query image Q is temporally closer to anchor A1 or A2. Intuition: if long-term ordering of images is recoverable from appearance alone, a persistent change occurred; for purely seasonal/unchanged locations, cross-year ordering is indecipherable.
- Key design choices: (1) query Q is sampled *outside* the anchor interval (before A1 or after A2, equal probability) so visual similarity always matches temporal closeness — avoids mislabeling when change happens near an anchor; (2) each anchor = c=3 consecutive images (context size ablation: c=3 optimal, AUROC 0.877 vs 0.809 at c=1 and 0.817 at c=5); (3) BCE loss, AdamW lr 3e-4, batch 5, 5 epochs, ResNet-50 backbone (Satlas pretrained weights best: AUROC 0.876 vs 0.851 random init).
- **Change scoring at inference:** for a new series compute score sequence S = {b(I1, In, Ij)}; a "pivot score" = max over split index i of |mean(S before i) − mean(S after i)| (change-point statistic); pivot beats Spearman rank correlation (AUROC 0.877 vs 0.860).
- **Spatial localization:** iterative self-training — train on 512×512, keep top-50% highest-scoring series, retrain on 128×128 patches to boost change density (AUROC 0.9415 localized vs 0.8714 without iteration).

## Data & labels
- Training fully unsupervised (labels only emerge from temporal structure). Human binary labels used only for the 300-series evaluation set (annotated with geographic cross-reference via Google Maps/OSM; ~1/3 positive).

## Results
- Change/no-change AUROC: OPTIMUS 0.876 vs CaCo (OSCD-finetuned) 0.563, CaCo 0.494, SeCo 0.491; F1 0.760 vs 0.585 best baseline.
- Localization AUROC 0.9415 (iterative 512→128 training).
- Backbone ablation: ResNet-50 0.876, SwinBase-v2 0.865, ResNet-152 0.850 — method matters more than backbone.

## What transfers to our thesis
- The core pretext idea — recover hidden temporal ordering to detect *persistent, non-cyclic* deviations — is directly mappable to sugarcane stress: a chronically stressed (water/salinity) field has an anomalous, non-seasonal trajectory across years, while healthy fields share the seasonal rhythm. A temporal-ordering or "which year is this" pretext on Landsat 16-day series could flag cross-year stress trajectories without labels.
- Pivot-score change-point statistic is a cheap, threshold-free anomaly score usable per-field on our time series (e.g., detect onset of salinity decline across seasons).
- Demonstrates that SSL trained only on temporal structure can beat dedicated contrastive change methods (CaCo, SeCo) by a wide margin (0.876 vs 0.563 AUROC) — strong citation support for pretext-driven label-free anomaly detection over generic contrastive embeddings.
- Iterative self-filtering (train → select top-k anomalous → retrain) is a lightweight recipe to increase anomaly density in training data, applicable to our small in-field datasets.

## Limitations / caveats
- RGB-only Sentinel-2/NAIP, 10 m; no multispectral indices (NDVI/NDRE), no thermal/LST — direct transfer to Landsat optical+LST needs re-derivation of the pretext on band time series rather than images.
- Targets abrupt, visually obvious persistent change (roads, deforestation); slow subtle stress gradients (salinity) are untested and may be below the pivot-score sensitivity.
- Small evaluation set (300 series, 100 annotated for localization), binary labels only, some annotation errors acknowledged (one mislabeled row).
- Struggles with deserts/shadows/dune movement (false positives); seasonal-agriculture mixture cases are the hardest.

## Key numbers to quote in lit review
- AUROC 56.3% → 87.6% over prior unsupervised change-detection baselines (CaCo/SeCo family).
- Localization AUROC 0.9415 via iterative 512→128 retraining.
- Context size c=3 anchors optimal (AUROC 0.877 vs 0.809 c=1); pivot score > Spearman (0.877 vs 0.860).
- Training data: 1M time series × 30–48 images over 8 years, entirely label-free.
