# 14 — STS-NET: Self-Supervised Crop Stress Detection (Dalal et al., 2026)

**Full Citation:** Dalal, P., Ranjan, R., Ghildiyal, S., Tamaskar, S., & Goel, N. (2026). STS-NET: Spatio-Temporal Stress Network for Self-Supervised Crop Stress Detection using Satellite Image Time Series. *arXiv:2607.18791v1* (21 Jul 2026).  
**PDF:** https://arxiv.org/pdf/2607.18791v1  
**Status:** ✅ Full read (2026-10-04)

## Key Contributions

- **Self-supervised 3D-CAE** for feature extraction from SITS data (pixel-level reconstruction pretext)
- Uses **4 vegetation indices**: NDVI, GNDVI, RECI (Red Edge Chlorophyll Index), NDRE — but actual model input is RGB + NIR + the *mean* of these 4 VIs (5 channels, Eq. 1)
- Pretrained on unlabeled BSPT (Barnala Spatial-Temporal) dataset (~22M pixels, PlanetScope, Barnala district, Punjab, India)
- Evaluated on labeled Lakhimpur Kheri (LK) sugarcane dataset (62 fields, ~3 acres per Sec III.A/Fig 1 — abstract says "2.5-acre test plot"; 9 stress classes: 3 water × 3 nitrogen)
- Frozen encoder + lightweight classifiers (Random Forest, SVM, XGBoost) — no end-to-end fine-tuning of the encoder

## Architecture

```
Input: T=32 timesteps × C=5 channels (R, G, B, NIR, V̄I)   [Eq. 1, p.3]
  V̄I = (NDVI + GNDVI + RECI + NDRE) / 4 at each timestep
→ 3D-CAE: stacked Conv3D encoder + MaxPooling3D + Upsampling3D decoder (Fig 2, p.3)
→ 64-dim latent vector per pixel time series
→ Decoder discarded, encoder frozen; RF / SVM / XGBoost on features (Algorithm 1, p.3)
```
19.2K parameters total (p.4), vs Presto's 400K [22]. Trained in TensorFlow on NVIDIA DGX A100 (40GB); batch 256, lr 0.001, Adam, ≤40 epochs with early stopping; 80:20 stratified split (Sec V.A, p.4).

## Results

Headline numbers **97.98% / 85.08% / 83.47%** are **Accuracy** values from ablation Table II (input = RGB+NIR+AvgVIs, T=32). The Abstract labels them "precision" but the Conclusion (p.5) explicitly calls them "high accuracy". Table I per-classifier metrics (Accuracy/Precision/Recall/F1, p.4):

| Task | Best model | Accuracy | Precision | Recall | F1 |
|------|------------|----------|-----------|--------|-----|
| Water stress (3-class) | 3D-CAE + RF | 0.98 | 0.98 | 0.98 | 0.98 |
| Nitrogen stress (3-class) | 3D-CAE + XGBoost | 0.87 | 0.87 | 0.87 | 0.87 |
| Combined W+N (9-class) | 3D-CAE + XGBoost | 0.84 | 0.85 | 0.85 | 0.84 |

Baselines (Table I, p.4): supervised RF, SVM, XGBoost; supervised 2-layer CNN (limited labels → poor generalization); Presto [22] SSL model fine-tuned (best config Presto+RF: water 0.82, nitrogen 0.81, W+N 0.72 accuracy). STS-NET beats all of them.

Ablation Table II (p.5): temporal depth T ∈ {8, 16, 24, 32}; T=32 best (97.98/85.08/83.47); T=8 (~2 months) → 90.32% water accuracy. Input ablation: RGB+NIR+AvgVIs (5ch) >> RGB+NIR (4ch); RGB+NIR+NDVI alone gives 94.48/78.76/75.17.

## Verified Full-Text Findings (2026-10-04)

Source: full-text read of arXiv:2607.18791v1 (5 pages), local PDF `D:\RS\Thesis\thesis_research\papers\14-Dalal-2026-STSPORT-SelfSupervised-Stress.pdf`. Section/page refs below are from the PDF.

### 1. Architecture, SSL pretext, temporal depth
- **Architecture:** 3D-convolutional autoencoder (3D-CAE), encoder of stacked 3D convolutional layers compressing a single pixel's time series into a lower-dimensional latent space; symmetric decoder with MaxPooling3D/Upsampling3D reconstructs the sequence (Sec IV.B + Fig 2, p.3). 64-dim latent vector (Sec IV.C, p.3); 19.2K parameters (Sec V.B.3, p.4).
- **SSL pretext task:** self-supervised **pixel-level time-series reconstruction** on unlabeled BSPT data, MSE loss over the reconstructed spectral sequence ("reconstruct the original sequence of a pixel's spectral values using information from the surrounding space and time", Sec IV.B, p.3; Algorithm 1, p.3). No masking, contrastive, or prediction-head pretext.
- **Temporal depth:** T = 32 timesteps (Eq. 1, p.3); BSPT = 32 PlanetScope scenes at 9–11 day intervals spanning Feb 2023–Feb 2024 (Sec III.B, p.2). Ablated over T ∈ {8, 16, 24, 32}; T=32 optimal, T=8 (~2 months) still 90.32% water accuracy (Table II, p.5).
- **Training recipe:** pretrain 3D-CAE on BSPT (MSE) → discard decoder, **freeze encoder** as fixed feature extractor → train external classifiers (RF/XGBoost/SVM) on 64-dim features (Algorithm 1 + Sec IV.C, p.3).

### 2. Input features
- NOT VI-only. Input per Eq. 1 (p.3) is **5 channels: R, G, B, NIR, and V̄I = mean of (NDVI, GNDVI, RECI, NDRE)**, computed from PlanetScope spectral bands. The Abstract's "exploits four vegetation indices" refers to the VI set used; the ablation confirms RGB+NIR+AvgVIs (5 ch) is the best config (Table II, p.5). Raw bands ARE part of the input alongside the averaged VI.
- PlanetScope only (high-resolution ~3 m constellation, Planet Labs). Preprocessing: mosaicking (Rasterio), mean-based imputation of missing pixels (Sec IV.A, p.2), min-max normalization (Sec V.A, p.4).

### 3. Results and metrics
- 97.98 / 85.08 / 83.47 = **Accuracy** in Table II (RGB+NIR+AvgVIs, T=32), p.5. Abstract (p.1) calls them "precision"; Conclusion (p.5) calls them "accuracy" — internal inconsistency in the paper. Table I precision values per classifier: water 0.98 (3D-CAE+RF), nitrogen 0.87 (3D-CAE+XGB), combined 0.85 (3D-CAE+XGB), p.4.
- All four metrics (Accuracy/Precision/Recall/F1) reported per task in Table I (p.4).
- Baselines: Random Forest, SVM, XGBoost (supervised), 2-layer CNN (supervised), Presto [22] (self-supervised, pretrained on global landscapes, fine-tuned; best variant Presto+RF) — Table I, p.4.
- Tasks: water stress = 3-class (irrigation 150%/100%/50%); nitrogen = 3-class (High R / Medium Y / Low P); combined = **9-class** permutation task; separate classifiers per task on the same frozen features (Sec V, p.4).

### 4. Study area and scale
- **BSPT (pretraining):** Barnala district, Punjab, India (30°35'56.94"N, 75°27'34.35"E), ~196 km² (~45,433 acres, Fig 1), PlanetScope, 32 images Feb 2023–Feb 2024, 9–11 day intervals, <15% cloud, ~22M pixels (Sec III.B, p.2).
- **LK (evaluation):** Lakhimpur Kheri, Uttar Pradesh, India (28°27'14.2"N, 80°55'42.0"E), controlled field experiment, 62 individual sugarcane fields, "approximately 3 acres" (Sec III.A, p.2; Fig 1: "Area: 3 acres") — **abstract says "2.5-acre test plot"** (p.1). Crop = sugarcane (plant cane, first year, planted Feb 2023; treatments April–September during tillering + grand-growth; no ratoon cropping). Stressors systematically induced: water at 150%/100%/50% of irrigation; nitrogen 0.25/0.5/1 kg (Block 1) and 0.21/0.42/0.84 kg (Blocks 2–3) → nine classes (Sec III.A, p.2).

### 5. Verified absences
- **SALINITY: NOT PRESENT.** Only water and nitrogen stress are considered anywhere (Sec I, III.A, V); no mention of salinity, salt, or EC.
- **MAMBA / SSM: NOT PRESENT.** No state-space models; future work mentions only "temporal attention mechanisms or transformer-based backbones" (Sec VI, p.5).
- **XAI: NOT PRESENT.** No interpretability/explainability method used; "improve stress interpretability" appears only as future work (Sec VI, p.5).
- **MULTI-YEAR ARCHIVE: NOT PRESENT.** Single year throughout: BSPT Feb 2023–Feb 2024 (Sec III.B); LK labels from one 2023 growing season, first-year plant cane only (Sec III.A).
- **MODERATE-RESOLUTION SATELLITE IMAGERY (Landsat/Sentinel-class, 10–30 m): NOT PRESENT.** Only PlanetScope (~3 m) is used; Sentinel-2 appears only as related work (Sec I, p.1–2).
- **MIXED-STRESS CLASSES AS DISTINCT LABELS: NOT AN ABSENCE — PRESENT.** "The combined stress task includes all nine permutations of water-nitrogen regimes, resulting in a 9-class label" (Sec V, p.4). Distinction for the thesis: their combined pair is water×nitrogen (not water×salinity), and it is a fine-grained 9-class task rather than a single "mixed" class.

### 6. Stated limitations / future work (Sec VI, p.5)
1. Generalize the framework across diverse crop types and geographic regions with heterogeneous stress patterns.
2. Integrate multimodal sensing (UAVs, SAR, thermal imagery) to enrich features and "improve stress interpretability".
3. Explore temporal attention mechanisms or transformer-based backbones for better stress-pattern recognition across longer crop cycles.
4. Deploy in a real-time decision-support pipeline for farmers and agronomists.
- Implicit limitation (Sec V.B.1, p.4): supervised CNN struggled due to limited labeled samples — the motivation for their SSL approach.

### Repo-claim verification

| Repo/abstract claim | Verdict | Evidence |
|---|---|---|
| Self-supervised 3D-CAE on SITS | VERIFIED | Abstract, p.1; Sec IV.B + Fig 2, p.3 |
| SSL pretext | Pixel-level reconstruction (MSE), not masking/contrastive | Sec IV.B, p.3; Algorithm 1, p.3 |
| Input = 4 VIs (NDVI, GNDVI, RECI, NDRE) from PlanetScope | PARTIAL — VIs used, but model input is RGB+NIR+mean-of-4-VIs (5 channels) | Eq. 1, p.3; Table II, p.5 |
| Temporal depth | T=32 timesteps (9–11 day interval, 1 year) | Eq. 1, p.3; Sec III.B, p.2 |
| Trained on BSPT (Barnala Spatial-Temporal) dataset | VERIFIED (Barnala district, Punjab, ~22M pixels, 32 scenes) | Abstract, p.1; Sec III.B, p.2 |
| Evaluated on 2.5-acre Lakhimpur-Kheri sugarcane plot, one year | VERIFIED with discrepancy — abstract "2.5-acre" vs Sec III.A/Fig 1 "approximately 3 acres"; 62 fields; one season (2023) | p.1 vs p.2 |
| Precision 97.98% / 85.08% / 83.47% | PARTIAL — numbers verified but they are **Accuracy** (Table II, RGB+NIR+AvgVIs, T=32); Conclusion calls them "accuracy"; Table I precisions are 0.98/0.87/0.85 | Table II, p.5; Table I, p.4 |
| Combined stress reported | VERIFIED — as a 9-class water×nitrogen permutation task | Sec V, p.4 |
| Frozen encoder + RF/XGB classifiers | VERIFIED (SVM also reported) | Algorithm 1 + Sec IV.C, p.3; Table I, p.4 |
| No Mamba/SSM | VERIFIED absent | whole paper; Sec VI, p.5 |
| No XAI | VERIFIED absent (interpretability = future work) | Sec VI, p.5 |
| No salinity | VERIFIED absent | whole paper |
| No multi-year archive | VERIFIED absent (single year, single season labels) | Sec III.A–B, p.2 |
| No moderate-resolution satellite (Landsat/Sentinel) imagery | VERIFIED absent (PlanetScope only) | Sec III.B, p.2 |

### Differentiation paragraph (draft)

> Dalal et al. (2026) (STS-NET) is the closest methodological predecessor of this thesis, and the two works differ on every major design axis. STS-NET pretrains a 3D-convolutional autoencoder (19.2K parameters) with a pixel-reconstruction objective on 32 PlanetScope scenes (~3 m) and classifies frozen 64-dimensional embeddings with Random Forest or XGBoost, whereas the thesis develops a Mamba (state-space) sequence model trained end-to-end on raw spectral bands augmented with land surface temperature (LST) rather than derived vegetation indices. Their stress taxonomy is water and nitrogen stress — three induced levels each, evaluated as separate 3-class tasks and a 9-class combined task — while the thesis targets water and salinity stress, the governing constraints in the arid, irrigated systems of Amirkabir/Khuzestan, Iran. Their evidence comes from a single controlled ~2.5–3-acre plot in humid-subtropical Lakhimpur Kheri (Uttar Pradesh, India) over one growing season with artificially imposed treatments, whereas the thesis uses multi-year, field-scale satellite archives in which stress occurs naturally. Finally, STS-NET contains no explainability component — interpretability is deferred to future work — whereas the thesis contributes timestep-level XAI attribution over the input sequence.

## Relevance to Thesis

**Very High** — Closest direct predecessor to proposed methodology:
- ✅ SSL pre-training on unlabeled SITS (but reconstruction-only pretext; no masked/contrastive variant)
- ✅ Sugarcane crop
- ✅ Combined stress evaluated (water + nitrogen, 9-class permutation task — our pair is water + salinity)
- ✅ Vegetation index inputs (as mean-VI channel alongside raw RGB+NIR bands)
- ❌ No Mamba architecture (transformers/attention only as future work)
- ❌ No salinity stress component
- ❌ No XAI / temporal attribution
- ❌ Single plot, single year; PlanetScope (~3 m), not Landsat-scale (30 m) multi-year archive

## Key Quote

> "We propose our STS-NET, a novel spatial-temporal stress network, built on a self-supervised 3D-convolutional autoencoder (3D-CAE), designed to utilize Satellite Image Time Series (SITS) data for crop stress detection." (Abstract, p.1)
