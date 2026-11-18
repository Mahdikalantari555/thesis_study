# Knowledge Base — Extended Literature Review

**Date:** 2026-09-10  
**Scope:** 32 papers total (8 advisor-mandated + 24 newly discovered)  
**Purpose:** Synthesize findings for thesis proposal on CNN-Mamba + SSL + XAI for water-salinity stress disentanglement in Khuzestan sugarcane

---

## I. Core Methodology Papers (Architecture Blueprint)

### 1. SITSMamba — Qin et al., 2024 (Advisor Paper #1)
- **Architecture:** Hybrid CNN-Mamba for SITS crop classification
- **Key Innovation:** Positional Weight (PW) mechanism for temporal attention
- **Relevance:** Direct architectural blueprint; 2D CNN spatial → Mamba temporal → dual decoder (classification + reconstruction)
- **Gap for Thesis:** Trained on crop type, not stress; no thermal bands; no multi-stress labels

### 2. STS-NET — Dalal et al., 2026
- **Architecture:** Self-supervised 3D-CAE for SITS stress detection
- **Key Innovation:** Pretraining on 22M unlabeled PlanetScope pixels; fine-tuning on 62 sugarcane fields
- **Performance:** 97.98% precision for water stress, 85.08% for nitrogen stress, 83.47% combined
- **Relevance:** Most similar to proposed methodology; proves SSL+SITS+stress detection paradigm
- **Gap:** Uses VIs as input (not raw bands); no Mamba; no salinity component; no XAI

### 3. EigenCL — Ahmad, 2025
- **Method:** Unsupervised contrastive learning on temporal NDRE
- **Key Innovation:** Eigenvector-guided similarity (76% variance captured) drives contrastive loss
- **Performance:** Silhouette 0.748; 76% early detection (12 days before threshold)
- **Relevance:** Proves VI time series alone can drive unsupervised stress detection
- **Gap:** Drought-only; corn crop; no deep architecture; no XAI

### 4. DeepSalt — Dey et al., 2025
- **Method:** Knowledge distillation + Spectral Adaptation Unit (SAU) for salinity estimation
- **Key Innovation:** Bridges lab FTIR (MIR) ↔ satellite hyperspectral (VNIR-SWIR) domains
- **Performance:** R²=0.87, MAE=0.25 dS/m for salinity estimation
- **Relevance:** Domain adaptation methodology directly applicable to salinity label generation
- **Gap:** No temporal dimension; single-date estimation; no stress disentanglement

---

## II. Sugarcane-Specific Papers

### 5. Sugarcane Health Monitoring Review — Waters et al., 2024
- **Scope:** Comprehensive review of satellite spectroscopy + ML for sugarcane
- **Key Finding:** Orange rust detection reaches 96.9% accuracy; no study differentiates water vs. salinity stress
- **Critical Gap Identified:** "Currently, only one study has attempted to classify multiple conditions simultaneously"
- **VI Table:** 20+ indices with formulas (NDVI, NDWI, NDMI, PRI, DSWI-1 to 5, SIPI, PSRI, etc.)
- **Relevance:** Most relevant review for your study crop; provides band selection guidance

### 6. Khuzestan Sugarcane Papers (Motlagh et al., Zoratipour et al., Hajeb et al., Malee et al.)
- **CWSI Threshold:** 0.4-0.5 (Zoratipour et al., 2026)
- **Critical Window:** July-September (water stress sensitivity)
- **Local Ky Factor:** 1.05 (vs. FAO default 1.2)
- **LAI Retrieval:** RMSE=0.48 (Hajeb et al., 2023)
- **Yield Prediction Baseline:** R²≥0.93 (Motlagh et al., 2026)
- **Relevance:** Provides local calibration parameters and validation benchmarks

---

## III. Stress Physiology & Physics Papers

### 7. Combined Drought-Salinity Stress — Angon et al., 2022 (Advisor Paper #7)
- **Key Finding:** Interactive (not additive) effects of concurrent stress
- **Mechanism:** Hormonal crosstalk (ABA-SOS pathway intersection)
- **Relevance:** Proves necessity of "mixed stress" class in your model

### 8. Plant Stress Physiology Review — Li et al., 2025
- **Key Finding:** Non-additive stress responses due to hormone pathway intersections
- **Mechanism:** ABA for drought interacts with SOS pathway for salinity
- **Relevance:** Molecular basis for disentanglement objective

### 9. Spectroscopic Salinity Stress Review — Gupta et al., 2025
- **Modalities:** Fluorescence (92-98% accuracy), Hyperspectral (R²~0.79), Thermal (+0.88 to +1.19°C under salinity)
- **Key Bands:** Red-edge (700-750nm) most sensitive to chlorophyll degradation
- **Thermal Response:** Canopy warming correlates with salinity severity
- **Relevance:** Informs band selection (Landsat Band 5/6 for red-edge, Band 10 for LST)

---

## IV. XAI & Interpretability Papers

### 10. XAI in Remote Sensing Review — Höhl et al., 2024 (Advisor Paper #5)
- **Key Finding:** Temporal XAI in RS is virtually unexplored
- **Methods Covered:** SHAP, Grad-CAM, LIME in RS context
- **Relevance:** Confirms your novelty claim; provides XAI methodology survey

### 11. XAI-Guided VI Enhancement — Najjar et al., 2024
- **Method:** Shapley Value Sampling (SVS) for spectral attribution
- **Finding:** SWIR1 and RE1 bands most important (~20% each)
- **Result:** Two-VI combination (NDRE+NDMI2) outperforms full-band baseline
- **Relevance:** XAI → VI design loop; methodology for post-hoc interpretation

### 12. XAI for Spectroscopic Agriculture — Ahmed et al., 2025 (Advisor Paper #6)
- **Scope:** SHAP/Grad-CAM/LIME applied to 17 spectroscopic papers
- **Relevance:** Methodological analogy for band/importance interpretation

---

## V. SSL & Self-Supervision Papers

### 13. SSL Cookbook — Balestriero et al., 2023 (Advisor Paper #3)
- **Scope:** Comprehensive SSL taxonomy (contrastive, generative, predictive)
- **Relevance:** Foundation for SSL pre-training strategy

### 14. SSL for Irrigation Detection — Agastya et al., 2021
- **Method:** SimCLR-S2 for binary irrigation detection
- **Key Result:** 99% precision with 1% labeled data vs. 11% for supervised
- **Relevance:** Proves SSL essential for label-scarce agricultural RS

---

## VI. Baseline & Classical Papers

### 15. DL for SITS Review — Miller et al., 2024 (Advisor Paper #2)
- **Scope:** Comprehensive survey of CNNs, RNNs, Transformers, SSMs for SITS
- **Relevance:** Documents SITS challenges (cloud gaps, irregular sampling)

### 16. Self-Attention for Raw Optical SITS — Rußwurm & Körner, 2020 (Advisor Paper #4)
- **Method:** Transformer on raw optical SITS without manual VI computation
- **Relevance:** Historical baseline; shows raw-band approach validity

### 17. ML for Vegetation Health Forecasting — Nay et al., 2016
- **Method:** GBM for 16-day EVI forecasting using MODIS
- **Finding:** Raw spectral bands outperform derived indices
- **Relevance:** Classical ML baseline; supports raw-band approach

### 18. DroughtSet — Tan et al., 2024
- **Method:** Spatial-temporal Transformer for multi-task drought prediction
- **Features:** 11 dynamic climate predictors + 9 static geographic features
- **Interpretability:** Integrated Gradient (IG) for feature importance
- **Relevance:** Multi-task learning analogy for stress disentanglement

### 19. Tomato Broomrape Detection — Narimani et al., 2025
- **Method:** LSTM on 48 GDD time steps with phenological alignment
- **Performance:** 87% test accuracy, 89% F1
- **Key Features:** NDMI, CCC, FAPAR, CHL-RED-EDGE
- **Relevance:** Phenological alignment methodology applicable to sugarcane

---

## VII. Salinity & Water Management Papers

### 20. Salinity from Satellite LAI — Paciolla et al., 2025 (Advisor Paper #8)
- **Key Finding:** Satellite LAI can infer salinity effects without ECe measurement
- **Relevance:** Eliminates need for ground salinity labels; enables proxy label generation

### 21. Salinity-Irrigation Bayesian Network — Shi, 2022
- **Scope:** 34-year Landsat salinity estimation across 10 arid basins
- **Finding:** Drip irrigation negatively correlated with salinity
- **Relevance:** Long-term salinity dynamics perspective; causal framework reference

---

## VIII. Research Gap Summary

| Component | State of Art | Your Contribution |
|-----------|-------------|-------------------|
| **Architecture** | CNN-LSTM, 3D-CAE, Transformer | CNN-Mamba (first for stress SITS) |
| **SSL** | 3D-CAE reconstruction, SimCLR on VIs | SSL on raw Landsat bands + phenology-aware pretext |
| **Stress Types** | Water-only or salinity-only | **Water + Salinity + Mixed** disentanglement |
| **Crop** | Corn, sugar-beet, wheat, tomato | **Sugarcane** (first DL stress paper on this crop) |
| **Region** | India, USA, Europe, China | **Khuzestan, Iran** (first for this region) |
| **Temporal Scale** | Single season (3-6 months) | **12-year** Landsat time series |
| **XAI** | Static band importance | **Temporal XAI** (first in RS) |
| **Resolution** | PlanetScope (3m) or Sentinel-2 (10m) | **Landsat (30m)** — matches existing data pipeline |

---

## IX. Recommended Reading Priority

### Phase 1: Architecture & SSL Foundation (Week 1-2)
1. SITSMamba (Qin et al., 2024) — arXiv:2409.09673
2. STS-NET (Dalal et al., 2026) — arXiv:2607.18791
3. EigenCL (Ahmad, 2025) — arXiv:2506.03394
4. SSL Cookbook (Balestriero et al., 2023) — arXiv:2304.12210

### Phase 2: Sugarcane Context (Week 2-3)
5. Sugarcane Review (Waters et al., 2024) — arXiv:2404.16844
6. Motlagh et al. (2026) — CWSI yield diagnosis
7. Zoratipour et al. (2026) — Hourly/daily CWSI
8. Hajeb et al. (2023) — Multi-var sugarcane retrieval

### Phase 3: Stress Physiology & Salinity (Week 3-4)
9. Angon et al. (2022) — Combined stress physiology
10. Paciolla et al. (2025) — Salinity from LAI
11. Gupta et al. (2025) — Spectroscopic salinity review
12. DeepSalt (Dey et al., 2025) — Domain adaptation for salinity

### Phase 4: XAI & Interpretability (Week 4-5)
13. Höhl et al. (2024) — XAI in RS review
14. Najjar et al. (2024) — XAI-guided VI enhancement
15. DroughtSet (Tan et al., 2024) — IG for feature importance

### Phase 5: Baselines & Additional Context (Ongoing)
16. Miller et al. (2024) — DL for SITS review
17. Rußwurm & Körner (2020) — Self-attention SITS
18. Agastya et al. (2021) — SSL for irrigation
19. Narimani et al. (2025) — Tomato SITS detection

---

## X. Key Quotes for Proposal

> "The interactive (not additive) effects of concurrent drought and salinity stress require a dedicated 'mixed stress' class in any predictive model." — Angon et al., 2022

> "Temporal explainability in remote sensing remains virtually unexplored, representing a critical gap for trustworthy AI in agriculture." — Höhl et al., 2024

> "Currently, only one study has attempted to classify multiple sugarcane conditions simultaneously, and none differentiate abiotic water vs. salinity stress." — Waters et al., 2024

> "With only 1% of labeled data, self-supervised learning achieves 99% precision vs. 11% for supervised baselines — making SSL essential for label-scarce agricultural applications." — Agastya et al., 2021

> "Satellite-derived LAI can serve as a proxy for salinity effects, eliminating the need for direct ECe measurements in stress classification." — Paciolla et al., 2025
