# Label-free Anomaly Detection in Aerial Agricultural Images with Masked Image Modeling

## Full citation
Shikhar, S. & Sobti, A. (2024). "Label-free Anomaly Detection in Aerial Agricultural Images with Masked Image Modeling." arXiv:2404.08931v1 [cs.CV] (Plaksha University).

## Problem & setting
- Agricultural anomaly segmentation (nutrient deficiency, water stress, weed clusters, drydown, planter skip, double plant, endrow, waterway, storm damage) in UAV imagery without labels; goal is a single label-free model across all anomaly types that does NOT require curating "normal-only" training data.
- Data: Agriculture-Vision Challenge — 94,986 aerial images from 3,432 US farmlands, RGB+NIR (4 bands), 10 cm/px, 512x512 crops; 56,944/18,334/19,708 train/val/test; 9 anomaly classes (previous work reported 6).

## Method
- **SwinMAE (Swin-Transformer masked autoencoder)**: 4 Swin blocks encoder + lightweight Swin-Unet-like decoder; window masking strategy — divides the image into larger non-overlapping windows and masks whole windows (instead of individual 4x4 patches), preventing shortcut interpolation from neighboring unmasked patches; masked tokens replaced by learnable vectors so token count stays constant through the encoder (unlike MAE which drops masked tokens). Trains on 25% visible patches.
- **Anomaly detection by reconstruction error**: at inference, K=32 different random window masks; per-pixel error averaged over K reconstructions; binarized by Knee-point (Kneedle) thresholding.
- **Anomaly Suppression Loss (ASL)** (adapted from Wang et al. Auto-AD for hyperspectral): adaptive weight map w_ij = max(E) - e_ij over the reconstruction-error map, updated periodically after an initial 20 epochs; down-weights pixels with large reconstruction error (i.e., the anomalies) in the MSE loss L = sum w_ij*e_ij, so the network stops learning to reconstruct anomalies while training on uncurated (anomaly-contaminated) data — removes the normal-only training assumption.
- Training: 224x224 input, AdamW lr 1e-3, 200 epochs, batch 64, single 24 GB A5000.

## Data & labels
- No anomaly labels used in training (fully self-supervised reconstruction); ground-truth anomaly masks only for IoU evaluation. Leave-one-out protocol for Table 1 (train with anomaly class excluded); Table 2 trains with all anomalies included thanks to ASL.

## Results
- 6-class mIoU (comparable protocol): DSVDD 18.2, ARNet 20.5, GANomaly 25.3, InTra 29.3, ASD 29.4, RIAD 31.7, **MAE 36.2, SwinMAE 37.5, SwinMAE+ASL 38.0** — +6.3 mIoU over prior SSL/unsupervised SOTA (RIAD).
- 9-class: best IoU per class e.g. planter skip 52.7, waterway 46.9, double plant 46.6, water 37.8.
- Label-free robustness (Table 2): with anomalies included in training, mIoU 36.44 (median class IoU 42.3 vs 45.8 normal-only); only Drydown and Water degrade strongly (45.83->28.1 and 45.97->37.8) because these classes overlap least with other anomalies' distribution.
- Supervised upper bounds for context: AAFormer 41.2 mIoU; FusePN dice 82.71.
- Failure modes: dispersed anomalies (weeds, water) reconstructed well (learned as part of normal distribution); non-agricultural objects (trees, roads, cars) flagged as anomalies.

## What transfers to our thesis
- **The core template for our label-free sugarcane stress detection**: masked reconstruction of field time-series (or per-date image stacks), anomaly score = reconstruction error, threshold = knee point. On Landsat 16-day series, replace window masking with timestep/band masking (as in Presto) and score field-pixels by reconstruction error of masked composites.
- **ASL (adaptive suppression loss) is the key transferable trick**: our training archive will inevitably contain stressed fields; ASL lets the model learn normal crop phenology without manually filtering "healthy" fields — directly addressing a major practical objection to anomaly-detection-on-normal-data designs.
- Knee-point automatic thresholding avoids a hand-tuned anomaly threshold — useful for operational per-field stress flagging across years.
- Demonstrated limits that we should anticipate: anomalies that are spatially diffuse and distribution-overlapping (like gradual water stress across a field) are the hardest for reconstruction-based AD; single-date RGB/NIR misses them — our multi-temporal (seasonal) formulation should mitigate this.

## Limitations / caveats
- UAV 10 cm RGB+NIR single-date images — no temporal dimension, no thermal; agricultural anomalies defined by pattern shape, unlike satellite-resolution stress signatures.
- With anomalies in training, two of nine classes degrade sharply (drydown, water); dispersed anomalies poorly caught; non-field objects trigger false positives.
- Supervised SOTA (41.2 mIoU) still 3+ pp higher than the label-free method; knee-point threshold is image-global, not field-adaptive.

## Key numbers to quote in lit review
- Masked image modeling beats prior unsupervised AD on Agriculture-Vision by +6.3 mIoU (SwinMAE+ASL 38.0 vs RIAD 31.7 on 6 classes).
- Anomaly suppression loss allows training on anomaly-contaminated data with only ~3.5 median-IoU loss (42.3 vs 45.8 normal-only) — no normal-data curation needed.
- Reconstruction-based AD fails on spatially diffuse anomaly classes (weed/water) even with 75% masking — a documented caveat for reconstruction-error stress detection.
- Label-free SwinMAE approaches supervised AAFormer (38.0 vs 41.2 mIoU) within ~3 pp.
