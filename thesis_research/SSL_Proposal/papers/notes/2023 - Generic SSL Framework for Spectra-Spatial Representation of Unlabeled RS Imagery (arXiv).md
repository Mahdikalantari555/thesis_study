# 2023 Zhang & Han — A Generic SSL Framework for Representation Learning from Spectra-Spatial Features of Unlabeled RS Imagery

## Full citation
Zhang, X.; Han, L. "A generic self-supervised learning (SSL) framework for representation learning from spectra-spatial feature of unlabeled remote sensing imagery." arXiv:2306.15836v1 [cs.CV], 27 Jun 2023 (Manchester Metropolitan University).

## Problem & setting
- Claim: existing RS pretext tasks are RGB/spatial extensions from CV and ignore spectral structure; no pretext task explicitly designed for joint spectral-spatial representation learning.
- Two downstream settings evaluated: (1) multi-label land-cover classification on Sentinel-2 multispectral (object-based, BigEarthNet), (2) soil parameter retrieval (N, P, K, Mg, pH) on hyperspectral data (pixel-based regression).

## Method
- **ObjSSL (object-based, contrastive/self-distillation)**: DINO-style teacher–student (momentum teacher, EMA update θt ← λθt + (1−λ)θs, λ cosine schedule 0.96→1; cross-entropy between teacher/student softmax output distributions, teacher temperature τt). Positive views from a **joint spatial-spectral multi-view pretext**: (a) regular augmentation (rotation, zoom, Gaussian blur, noise), (b) local (36×36 crops, <50% of global 120×120 view) + global views — locals to student, global to teacher, (c) **spectral-aware augmentation: randomly drop 30–50% of channels (set to zero) while preserving channel order** — explicitly avoids color-jitter-style channel shuffling that destroys spectral semantics. Encoder: Spectral–Spatial ViT.
- **PixSSL (pixel-based, generative)**: spectral-masked autoencoder — mask **50% of a pixel's spectral profile**, transformer encoder sees only visible bands, lightweight decoder reconstructs the full spectral profile (asymmetric MAE design, MSE loss in pixel space, mask tokens + positional embeddings). High masking ratio prevents trivial interpolation between adjacent bands.
- Same framework serves object-based (high/very-high resolution) and pixel-based (low/medium resolution) analysis.

## Data & labels
- BigEarthNet: 125 Sentinel-2 tiles (June 2017–May 2018), 10 European countries, Level-2A sen2cor-corrected, ~393,000 training patches; labels only for downstream fine-tuning/eval.
- Hyperspectral soil dataset for N/P/K/Mg/pH regression; labels only for downstream regression.

## Results (key quantitative results)
- Spectral-aware augmentation ablation: macro P/R/F1 = 78.66/66.52/71.10% vs. 73.02/62.12/66.05% without it → **+5.6 P, +4.4 R, +5.1 F1**; spectrum-sensitive classes (forests, grassland, wetlands, arable land) improve most.
- Label-efficiency: supervised-only collapses with 5% training data (F1 22.4%, LRAP 32.4%); **with SSL fine-tuning, best accuracy is reached using only 5% of training data**.
- SSL comparison (fine-tune on 50% labels): proposed 92.76% acc / 66.05% F1 / 89.13% LRAP vs. DINO 92.05/60.65/87.17, BYOL 91.86/57.03/86.33, MoCo-v2 91.71/60.96/86.25.
- Backbone comparison: proposed network + SSL 93.84% acc / 72.50% F1 vs. ResNet50 92.32/62.52, VGG16 90.96/45.85, ViT 89.94/39.00.
- PixSSL regression: soil N prediction R² ≈0.85 (traditional ML) → SSL linear probe R² 0.93→0.95 (P, K, Mg); fine-tuned encoder R² >0.95; masking ratio 50% (and 70%) optimal.
- Masking-ratio ablation: high ratios (50–70%) work best — consistent with MAE findings.

## What transfers to our thesis
- **Spectral-aware channel dropping (30–50%, order-preserving) is directly applicable** as an augmentation for Landsat time series: mask/drop bands (or entire 16-day acquisitions) while keeping band/time order intact — a physically valid pretext augmentation for optical+LST stacks.
- **PixSSL's band-masking pretext generalizes naturally to time-band masking on Landsat**: mask 50% of the (band × date) cube and reconstruct — supports our masked-autoencoder design for multi-year sugarcane stacks (NDVI, LST bands across 16-day steps).
- Their 5%-labels result supports the thesis argument that SSL pretraining on unlabeled multi-year imagery then light fine-tuning (or none) beats supervised training in label-scarce agricultural settings.
- The two-track design (object-level contrastive + pixel-level masked reconstruction) parallels our multi-product design: parcel-level embeddings for field stress scoring vs. pixel-level reconstruction for anomaly maps.

## Limitations / caveats
- No temporal dimension — purely single-date spectral-spatial; our setting adds the time axis.
- Downstream tasks are land-cover classification and soil chemistry regression, not stress/anomaly detection.
- BigEarthNet evaluation partly uses weighted metrics; F1 gains partly architecture-driven (their channel-information ViT module), so SSL-vs-architecture attribution is mixed.
- arXiv preprint (LaTeX template date fields stale); not peer-reviewed venue.

## Key numbers to quote in lit review
- +5.05 F1 points macro from spectral-aware augmentation alone (71.10% vs. 66.05%).
- Best downstream accuracy achievable with only **5% of training labels** when SSL-pretrained (vs. F1 22.4% supervised-only).
- Beats MoCo-v2/BYOL/DINO by 5.1–9.0 F1 points under 50%-label fine-tuning.
- Soil nutrient regression R² raised from ~0.85 to >0.95 by SSL representations.
- Optimal spectral masking ratio: 50%.
