# Mapping seasonal dynamics of forage and cereal crops in a hyper-arid environment using Sentinel-1 and Sentinel-2 time series

## Full citation
Alwahas, A., Johansen, K., Rodriguez, J., & McCabe, M. F. (2026). *Mapping seasonal dynamics of forage and cereal crops in a hyper-arid environment using Sentinel-1 and Sentinel-2 time series*. Frontiers in Artificial Intelligence 9:1803320. DOI 10.3389/frai.2026.1803320

## Problem & setting
- Task: seasonal, field-scale crop-type mapping (4 functional groups: fallow, cereal, vegetables, forage) in a label-scarce, irrigation-driven hyper-arid region — Wadi Al-Dawasir, Saudi Arabia (4,560 km², <50 mm rain/yr, center-pivot irrigation on non-renewable groundwater), 2020–2024.
- Challenges: irrigation (not rain) drives phenology so crop calendars shift between fields/years; field labels scarce (300 center pivots surveyed in 4 campaigns, 2023–2024); arid irrigated systems underrepresented in global products (WorldCereal, GFSAD).
- Data: biweekly (15-day median) stacks of Sentinel-2 NDVI + Sentinel-1 VH/VV ratio (dB), temporally aligned ±6 days, seasons Nov 2022–Oct 2024, tiles 128×128 with T=12 timesteps; NDVI-only vs NDVI+SAR ablation.

## Method
- **SSL pretraining (MAE-style, temporal masking):** per modality, 3-layer spatial encoder (conv + group norm + GELU) per frame → adaptive average pooling to a coarse spatial grid → spatiotemporal tokens + positional encodings → random **50% temporal masking** → transformer temporal encoder → modality-specific decoder reconstructs masked timesteps with a spatial prior (mean of encoder features over unmasked frames), upsampled to 128×128. Huber loss (δ=0.5) computed only on masked frames, summed over NDVI and VH/VV channels (L = L_NDVI + L_VH/VV). ~500 epochs, Adam lr 1e-4, batch 4, 11,721 train / 2,931 val tiles. Pre-training scope ablation: single season (S1) vs all seasons (S4).
- **Pseudo-labels:** K-means (K=8, chosen by scanning K=4–16 with label agreement + cluster purity/Shannon entropy) on full-season NDVI+VH/VV pixel series, restricted to agricultural mask (seasonal median NDVI > 0.5); clusters assigned to crop groups by majority of verified field labels; connected regions ≥100 px (0.1 ha) kept, rest ambiguous/unlabeled. Used only as auxiliary supervision in fine-tuning — never for pretraining, validation, or model selection.
- **Fine-tuning:** DeepLabV3+ segmentation (class-weighted CE, early stopping, grad clipping 1.0) and RF (600 trees, class-balanced) on frozen MAE encoder embeddings.
- **Uncertainty:** normalized predictive entropy maps (low-confidence flag ≤0.50 confidence), Bernoulli-variance-based uncertainty on area totals.

## Data & labels
- Ground truth: 300 center-pivot fields, 4 GPS field campaigns (winter/summer 2023, 2024); label QC — every "fallow" label cross-checked against the S2 NDVI trajectory and removed if the visit-day observation contradicted the seasonal signal (e.g., field idle only on visit day).

## Results
- Best config (S4-P, DeepLabV3, NDVI+VH/VV): mIoU 0.80, F1 0.88, OA 0.97. Pseudo-labels are the dominant factor: mIoU 43–45 → 77–80 (+~35 points), F1 55–56 → 86–88; pretraining scope (1→4 seasons) adds only ~2 points.
- **Optical-only ablation collapses: mIoU 0.35, F1 0.32, OA 0.64 vs 0.80/0.88/0.97 with SAR** — NDVI alone cannot separate crops in irrigated arid systems.
- Per class: fallow mIoU 0.95/0.97, forage 0.815/0.85, cereal 0.71 (F1 0.85), vegetables worst 0.506–0.52 (main confusion vegetables→cereal due to overlapping single-peak NDVI).
- External FM baselines under same protocol underperform: ScaleMAE decoder-only + field labels mIoU 46.8, Prithvi-EO-1.0 42.5 — far below the local MAE (80.1); pseudo-labels actually *hurt* the external FMs (mIoU ~29–31), showing pseudo-label benefit is representation/task-aligned, not universal.
- DeepLabV3 slightly beats RF (80.1 vs 77.2 mIoU). Uncertainty concentrated on vegetables, post-cut forage, field edges. Mapped area trends: forage peaked 17,441 ha (summer 2022) → 8,775 ha (2024); cereal rose to 15,076 ha (winter 2024).

## What transfers to our thesis
- Same climate/drought-relevant setting as our sugarcane work: irrigation-driven, water-stressed agriculture where rainfall-based calendars fail — validates our full-time-series (rather than fixed-calendar-date) approach to stress detection.
- The **temporal-masking MAE on biweekly NDVI+SAR time-series tiles** is architecturally the closest SSL recipe in this batch to a Landsat 16-day optical+LST version: swap S2 NDVI→Landsat NDVI/NDRE, VH/VV→LST, 15-day→16-day compositing. Their finding that masking-based temporal pretraining works with only ~12 timesteps/season is directly encouraging for Landsat's sparser series.
- Pseudo-label augmentation via unsupervised K-means clustering of seasonal time series (+35 mIoU) is a cheap semi-supervision strategy for our label-scarce sugarcane setting — cluster field temporal profiles first, expand supervision.
- Strong evidence for multimodality: NDVI-only ablation halves performance; supports our optical+LST (and potentially SAR) fusion claim for stress detection — single optical index streams are insufficient in irrigated arid fields.
- Entropy-based confidence maps + low-confidence flagging is a practical XAI/QC layer we can adopt for flagging uncertain stress predictions in-field.
- Negative result worth citing: external geospatial FMs (Prithvi, ScaleMAE) transfer poorly to a local hyper-arid task — supports training small local SSL models rather than fine-tuning giant FMs for in-field deployment.

## Limitations / caveats
- Crop-type classification (4 functional groups), not stress/anomaly detection; requires field labels for fine-tuning and pseudo-label cluster assignment.
- NDVI-only input choice justified pragmatically, not optimized (authors admit no full-multispectral comparison).
- Vegetables mIoU ~0.5 — phenologically overlapping classes remain unreliable; the same problem will affect separating mild vs severe stress stages.
- Only 300 labeled pivots from 2 years used for fine-tuning/validation; area uncertainty ignores spatial error correlation.
- Sentinel 5–12 day data, not 16-day Landsat; SAR VH/VV is unavailable in a Landsat-only scenario (Landsat has no SAR), so their multimodality gain needs re-derivation with LST/thermal as the second modality.

## Key numbers to quote in lit review
- SSL MAE + pseudo-labels + optical–radar: mIoU 0.80 / F1 0.88 / OA 0.97 vs NDVI-only mIoU 0.35 — a 2.3× mIoU drop without the second modality.
- Pseudo-label augmentation adds ~35 mIoU points; pretraining scope (1→4 seasons) adds only ~2.
- Local MAE (80.1 mIoU) crushes Prithvi-EO-1.0 (42.5) and ScaleMAE (46.8) under identical fine-tuning protocol.
- Label QC by NDVI-trajectory cross-checking removed visit-day-only "fallow" mislabels — a reusable label-cleaning practice.
