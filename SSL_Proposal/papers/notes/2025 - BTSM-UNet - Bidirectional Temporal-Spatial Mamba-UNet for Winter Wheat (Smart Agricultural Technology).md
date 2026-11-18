# BTSM-UNet: Bidirectional Temporal-Spatial Vision Mamba-UNet for winter wheat classification based on Sentinel-2 imagery

## Full citation
Fan, L., Chen, S., Xia, L., Zha, Y., Zhou, Q., Yan, Q. (2025). BTSM-UNet: Bidirectional Temporal-Spatial vision Mamba-UNet for winter wheat classification based on Sentinel-2 imagery. *Smart Agricultural Technology*, 12, 101547. DOI: 10.1016/j.atech.2025.101547. Chinese Academy of Agricultural Sciences.

## Problem & setting
- Task: supervised binary semantic segmentation (winter wheat vs non-wheat) from Sentinel-2 time series; goal is efficient large-area crop mapping (long time series, low compute).
- Study area: 10 sites of 4000×4000 px (40 km × 40 km) across China's main winter-wheat regions (North China Plain dominant); 8 train (A–H), 2 geographically separate test sites (T1, T2).
- Data: S2 Level-2A SR from GEE, growing season 1 Oct 2022 – 30 Jun 2023, cloud <20%, resulting in 152 clear images with Day-of-Year kept per observation; 9 bands (B2,B3,B4,B5,B6,B7,B8,B11,B12 — red-edge included, 60 m bands and B8A dropped).

## Method
- BTSM-UNet: UNet-style encoder–decoder where the three middle encoder layers insert a **Bidirectional Temporal-Spatial vision Mamba (Bi-TSM)** module.
- Key design: spatio-temporal DECOUPLING — 2D CNNs first extract multi-scale spatial detail per date; then bidirectional Vision Mamba models the temporal dimension as a sequence (forward + backward selective scan, O(T) instead of attention's O(T²)); complexity becomes additive O_space + O(T·D) rather than multiplicative like 3D CNNs. Motivation: avoid "spatio-temporal entanglement" of joint 3D processing (field texture vs phenology).
- Decoder fuses CNN local spatial features with Bi-TSM global spatiotemporal features at 3 scales (downsample 64/32/16) via deconvolution; single deconv output head. Fully supervised segmentation loss (cross-entropy family); no SSL, no masking.
- Baselines: UNet3D, UNet2D-LSTM, CNN-BiLSTM, TSViT, UTS-Former, VM-UNet.

## Data & labels
- Labels: Yang et al. 10 m China winter wheat product (2020–2022, knowledge-based + ML, OA >0.90, provincial R² ≥0.95 vs census) — an existing map, not field surveys.
- 8 train sites vs 2 held-out test sites = spatial cross-site generalization design.

## Results
- Test sites: T1 MCC 0.902 / F1 0.948; T2 MCC 0.908 / F1 0.957; overall best MCC 0.905, F1 0.952, precision 0.954, recall 0.951.
- Beats UNet3D (MCC 0.882), UTS-Former (0.881), VM-UNet (0.843), UNet2D-LSTM (0.827), TSViT (0.819), CNN-BiLSTM (0.659); relative MCC gain +2.5% over best CNN baseline.
- Efficiency: 4.86 M params, 60.19 GFLOPs, fastest inference 24 FPS — vs UNet3D 6.16 M / 2159 G FLOPs / 9 FPS; VM-UNet lacks the temporal module.
- Band-combination robustness: restricting to RGB, BTSM-UNet MCC drops only 2.43% (relative, MCC/All) vs 28.4% for CNN-BiLSTM — temporal modeling compensates for spectral poverty.

## What transfers to our thesis
- Direct architectural template for our **lightweight multi-product in-field model on Landsat 16-day series**: decoupled 2D-spatial + 1D-temporal Mamba keeps complexity additive in T — matches our long, cloudy, irregularly-sampled Landsat stacks (their DoY-encoding of irregular acquisitions is reusable).
- The 4.86 M-param / 60 G class of model is exactly the "lightweight in-field" budget; cross-site train/test (8 vs 2 disjoint regions) is our cross-year/cross-field protocol analog.
- Strong empirical evidence that **good temporal modeling partially substitutes for spectral bands** (RGB-only −2.43% MCC): supports our premise that with 16-day optical+LST and a strong temporal encoder, labels — not bands — are the bottleneck; also relevant if we drop noisy bands.
- Mamba vs Transformer efficiency claim (vision transformer ≈35× vision-mamba compute at same sequence input) — quotable for justifying SSM choice over ViT for Landsat time series.

## Limitations / caveats
- Fully supervised with map-derived labels (inherits label noise from Yang et al. product); binary crop-only task; no stress/anomaly component.
- S2 5-day revisit and 152 clear scenes — far denser than Landsat 16-day; no SSL pretraining, so temporal representation is learned only from ~8 sites of labels.
- No cross-YEAR test (single season 2022–23); spatial encoders only 2D per date; no comparison to masked-pretraining baselines.
- MCC/F1 from one season, one crop; cloud handling not deeply addressed despite claims about Landsat cloud issues.

## Key numbers to quote in lit review
- Bi-TSM-UNet: MCC 0.905, F1 0.952 winter-wheat mapping with only 4.86 M params, 60.19 GFLOPs, 24 FPS (best of 7 deep models tested).
- RGB-band-only MCC drops 2.43% for BTSM-UNet vs 28.4% for CNN-BiLSTM — temporal modeling buffers spectral loss.
- Decoupled spatial(2D-CNN)+temporal(bidirectional Mamba) design: O(HW·C²k²) + O(T) vs joint 3D convolution's multiplicative T·H·W·C²·t·k².
- Vision Transformer ≈35× the computational load of vision Mamba for equal sequence input (cited from prior work).
