# Label-Free Deep Learning with Feature Adaptation for Crop Anomaly Detection on Small Datasets

## Full citation
Yang, M.-D., Lee, T.-H., Tseng, H.-H., Su, T.-C., & Hsu, Y.-C. (2026). *Label-Free Deep Learning with Feature Adaptation for Crop Anomaly Detection on Small Datasets*. Agriculture 16(8), 854. DOI 10.3390/agriculture16080854

## Problem & setting
- Task: label-free (unsupervised) image-level anomaly detection + pixel-level localization of crop diseases/defects, adapted from industrial inspection, explicitly targeting **small datasets** (100–200 normal training images).
- Data: MVTec AD (industrial benchmark, 15 classes), PlantVillage subsets (Apple, Arjun, Cherry, Grape, Pongamia, Potato), Coffee Leaf Disease (79 train/51 test), and a custom real-world Sweet Potato dataset (157 train / 105 test; 5 defect types: black rot, southern blight, crack, mechanical damage, rat bite) collected in controlled factory conditions (RGB, vertical 450 mm).
- Motivation: agricultural intra-class variance from natural growth makes a pure "normal" baseline hard; supervised CNNs need thousands of labels.

## Method (EfficientAD — teacher-student + autoencoder, label-free)
- **Patch Description Network (PDN):** lightweight teacher distilled from ImageNet-pretrained WideResNet-101; deliberately narrow receptive field (33×33 px) for local texture anomalies; input 256×256.
- **Student–teacher (local anomalies):** student (same architecture, random init) trained to regress teacher features on normal-only images; anomaly signal = squared difference D(c,w,h); hard-example mining loss with p_hard=0.999 quantile + penalty term on out-of-distribution ImageNet samples to stop the student imitating the teacher off-target.
- **Autoencoder (logical/global anomalies):** AE reconstructs teacher feature maps (L_AE); student's extra channels predict AE output (L_STAE) to suppress AE false positives. Final anomaly map = quantile-normalized combination of local (T−S) and global (S′−A) maps; image score = max.
- Training: Adam lr 1e-4, 70,000 iterations, batch 1, no data augmentation. Metrics: AUROC (image level), AUPRO (pixel level, FPR limit 0.3).
- Background preprocessing strategies tested on Sweet Potato: Original, Background-Removed black (BGRM), Background-Replaced with out-of-distribution pure green (BGRP-G, RGB 0,255,0).

## Data & labels
- Only normal (defect-free) images used in training; disease/defect masks used solely for evaluation (AUPRO). Truly label-free training paradigm.

## Results
- MVTec AD mean AUROC 98.6%; PlantVillage up to 100% (Pongamia), Potato 99.0%, Coffee leaf 99.8%; Sweet Potato AUROC 88.9 (original) → 91.0 (BGRM) → **99.5 (BGRP-G)**.
- AUPRO localization much weaker: Sweet Potato 47.1 → 48.3 → 61.9; Coffee 75.3; per-defect: crack 82.3, southern blight 83.9 (BGRP-G), black rot only 37.7 (BGRM) → 47.6 (BGRP-G), mechanical damage 76.3, rat bite 72.2.
- Baseline comparison: EfficientAD dominates AnoGAN, Pix2Pix, InTra, Teacher–Student across datasets (e.g., MVTec Grid: 99.8 vs 50.9 best baseline).
- Deployment: S model 8.06M params / 75.94 GFLOPs / 104 MiB GPU; latency 1.153 ms (867 FPS RTX 6000 Ada), 476 FPS RTX 5000 Ada; M model 20.74M, 443 FPS.
- Failure analysis: dark black-rot boundaries suppressed by pure-black background mask (intensity collision); out-of-distribution green mask preserves dark lesion edges. Blurry/gradual lesion boundaries are the main weakness; t-SNE/DBSCAN shows "normal" crop features scatter into many sub-clusters — natural biological variance is treated as outliers, explaining the image-level vs pixel-level gap.

## What transfers to our thesis
- Core paradigm directly relevant: **train on normal-only fields, flag anomalies without any stress labels** — this is exactly our label-free sugarcane stress detection premise. EfficientAD's teacher-student + AE hybrid is a candidate lightweight architecture for field-level anomaly scoring on Landsat time-series features (embed field time series instead of image patches).
- The background-interference finding transfers to remote sensing: in satellite imagery, soil/road/water background consumes AE capacity. Their fix — replace background with out-of-distribution constant instead of black — is a concrete preprocessing trick for masking non-crop pixels (field mask with OOD fill) before anomaly modeling.
- Quantified caveat to carry into our thesis: image-level AUROC near-perfect (99.5) while pixel AUPRO only ~62 even after background correction — we should expect robust field-level "stressed vs normal" flags but weaker within-field localization, and should report AUPRO-style metrics, not just AUROC.
- Small-data claim (near-perfect AUROC from 100–200 normal samples, no augmentation) supports feasibility on limited sugarcane in-field datasets.
- 8–21M params and >400 FPS confirm edge deployment viability of student-teacher anomaly models — aligns with our lightweight multi-product model requirement.
- The dark-lesion/background-collision lesson generalizes: anomaly signals must not share feature space with masked regions (relevant when masking clouds/shadows in Landsat series).

## Limitations / caveats
- RGB close-range imagery of leaves/tubers, not satellite time series; no temporal dimension, no multispectral/LST — transfers only at the methodological level.
- Pixel localization weak on blurry/gradual symptoms (black rot 37.7 AUPRO) — water/salinity stress in sugarcane is exactly such a gradual signal; expect the same difficulty.
- Background strategies require a segmentation mask; for satellite data, field-boundary masks must come from somewhere (cadastral or SSL segmentation).
- Sweet Potato dataset captured under controlled factory lighting — not true field variability; specular reflections caused false activations even so.
- Needs a strictly "normal" training set — hard in agriculture where subclinical stress is widespread (authors note this inherent tension).

## Key numbers to quote in lit review
- Label-free EfficientAD reaches up to 100% AUROC on crop disease datasets with only 100–200 normal training images and no augmentation.
- Background-replaced (OOD green) preprocessing lifts Sweet Potato AUROC 88.9→99.5% and AUPRO 47.1→61.9%.
- Image-level vs pixel-level gap: ~99.5 AUROC but only ~62 AUPRO even after background correction — localization of gradual lesions remains the open problem.
- Efficiency: 8.06M params, 1.153 ms/image, 867 FPS (RTX 6000 Ada).
- EfficientAD mean AUROC 98.6% on MVTec AD vs ≤98.8 max for AnoGAN/Pix2Pix/InTra baselines (many below 60%).
