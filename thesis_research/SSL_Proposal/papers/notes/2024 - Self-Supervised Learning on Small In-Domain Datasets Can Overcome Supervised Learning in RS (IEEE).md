# Self-Supervised Learning on Small In-Domain Datasets Can Overcome Supervised Learning in Remote Sensing

## Full citation
Sanchez-Fernandez, A. J., Moreno-Álvarez, S., Rico-Gallego, J. A., Tabik, S. (2024). Self-Supervised Learning on Small In-Domain Datasets Can Overcome Supervised Learning in Remote Sensing. *IEEE JSTARS*, 17, 12797–12812. DOI: 10.1109/JSTARS.2024.3421622. Code: github.com/sfandres/ssl-overcome-supervised-rs.

## Problem & setting
- Question: can SSL pretrained on a SMALL in-domain (in-distribution) RS dataset beat fully-supervised (FS) models initialized from ImageNet-1k or random weights, under label scarcity?
- Tasks: (i) LULC fraction estimation (per-patch percentages of 9 LULC classes) and (ii) LULC scene classification, both on RGB satellite patches (224×224, 10 m, Sentinel-2-derived composites).
- Downstream data: Land-1.0 mixed-pixel dataset — 15,038 train / 2,153 val / 4,298 test; train ratios of 5%, 10%, 25%, 50%, 100% to simulate label scarcity.

## Method
- Pretrain 4 contrastive/non-contrastive SSL models with ResNet-18 backbone on Sentinel2GlobalLULC v2.1 (194,877 single-class "pure-pixel" RGB patches, 29 LULC classes, cloud-free S2 composites 2015–2020): Barlow Twins, MoCov2, SimCLR, SimSiam.
- SSL specifics: two augmented views per image (random resized crop, H/V flip, color jitter with HUE KEPT CONSTANT — strategic for satellite color features, Gaussian blur); Barlow Twins = redundancy-reduction loss (cross-correlation matrix of embeddings pushed to identity, no negatives/large batches); MoCov2 = momentum encoder + negative queue; SimSiam = stop-gradient + prediction head.
- Pretraining: 500 epochs, batch 512, SGD with 10-epoch warm-up; training subset reduced to 40% (stratified) for hardware; Ray Tune hyperparameter search.
- Transfer: best SSL model (Barlow Twins by macro-F1 on frozen linear probe) evaluated via frozen linear probing (LP, 50 epochs) and full fine-tuning (FT, 100 epochs) against FS-ImageNet and FS-Random.

## Data & labels
- Pretraining: 194,877 unlabeled (label-agnostic) in-domain RGB patches vs ImageNet-1k's 1,281,167 natural images used for supervised init — 6.6× fewer samples.
- Downstream labels used only for LP/FT evaluation across 5 train ratios.

## Results
- LULC fraction estimation RMSE (lower better): SSL-BarlowTwins-LP 0.099 vs FS-Random-LP 0.122 (+18.85%); FT: 0.083 vs FS-Random-FT 0.099 (+16.16%). SSL-BarlowTwins-LP beats FS-ImageNet-LP by 2.94% (0.099 vs 0.102); FS-ImageNet-FT slightly better than SSL-BarlowTwins-FT (0.078 vs 0.083, 6.41%).
- SSL-BarlowTwins-LP beats even FS-Random-FT at small train ratios; SSL-FT beats FS-Random-FT in 58/60 per-class×ratio scenarios (fraction task: 60/60 for SSL vs random).
- Scene classification macro-F1: SSL-BarlowTwins-LP 0.561 vs FS-Random-LP 0.404 (+38.86%) and FS-ImageNet-LP 0.547 (+2.56%); FT: 0.643 vs FS-ImageNet 0.653 (−1.53%).
- Barlow Twins clearly best of the 4 SSL models in embedding cluster quality (t-SNE) and macro-F1; SimSiam next.

## What transfers to our thesis
- Core evidential claim for the proposal: **a small, in-domain, label-free pretraining set (195k patches) matches or beats 1.28M ImageNet supervised weights in RS** — argues our sugarcane/Landsat in-domain SSL pretraining over a single irrigated scheme can beat generic pretrained backbones without any labels.
- Barlow Twins (no negatives, no momentum encoder, batch-size robust, simple loss) was the best SSL family — a practical lightweight choice for our compute-constrained multi-product setting.
- Hue-constant augmentation lesson: preserve spectral/color information critical in RS; for multispectral Landsat, design augmentations that preserve band-ratio/thermal signals (e.g., no channel jitter that breaks VI physics).
- LP-vs-FT gap analysis: frozen SSL features are strong under label scarcity but FT adds a few %; supports evaluating our models in both frozen-feature (cheap multi-product deployment) and FT regimes.
- RMSE on continuous fractions ≈ our regression-style stress indices; the 5–100% train-ratio curve method is a reusable experiment design for our cross-year label-scarcity story.

## Limitations / caveats
- RGB only (3 bands) — no multispectral, no LST, no time series; Sentinel-2 10 m not Landsat 16-day.
- Pretraining "small" still = 78k images used (40% of 195k); single backbone (ResNet-18); no temporal dimension.
- SSL slightly loses to ImageNet-FT in the strongest-label regime — SSL advantage is concentrated in low-label regimes.
- 2D scene tasks only; no stress/anomaly detection, no crop phenology.

## Key numbers to quote in lit review
- SSL (Barlow Twins) pretrained on 194,877 in-domain RS patches beats ImageNet-1k (1,281,167 samples) supervised init in linear probing by 2.94% RMSE (fraction estimation) and 2.56% macro-F1 (scene classification).
- SSL beats random init by 16–19% RMSE and 21–39% F1 across LP/FT.
- Frozen SSL features beat random-init FINE-TUNED features at small training ratios.
- Barlow Twins outperformed MoCov2, SimCLR, SimSiam on all transfer protocols (ResNet-18, 500 epochs, batch 512).
