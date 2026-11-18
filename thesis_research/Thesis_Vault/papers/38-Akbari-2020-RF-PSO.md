# 38 — RF + PSO Feature Selection for Sentinel-2 Crop Mapping (Akbari et al., 2020)

**Full Citation:** Akbari, E., Darvishi Boloorani, A., Neysani Samany, N., Hamzeh, S., Soufizadeh, S., Pignatti, S. (2020). Crop Mapping Using Random Forest and Particle Swarm Optimization based on Multi-Temporal Sentinel-2. *Remote Sensing* 12(9), 1449.  
**Status:** 🆕

---

## What It Does

Tests particle swarm optimization (PSO) against RF variable-importance for feature selection in crop mapping with multi-temporal Sentinel-2 data (Ghale-Nou county, Tehran, Iran), and builds a classification–feature-selection ensemble whose best outputs are combined by majority voting. Aimed at identifying the most relevant/distinctive features while mitigating the Hughes (curse-of-dimensionality) effect.

## Key Methodology

- **Data**: 8 Sentinel-2A/B images (22 Jul–25 Sep 2017), Sen2Cor BOA correction, 10/20 m bands resampled to 10 m; study area 21,400 ha; classes: silage maize, rice, alfalfa, vegetables (+ bare soil, canalbrae, water); 155 surveyed fields, 70/30 train/validation split
- **Feature sets (Table 2)**: spectral bands (80), spectral indices — NDVI, EVI, ARVI, RVI, NDWI, IRECI (48), GLCM texture (640), variation of spectral index/VSI (48), and combinations up to 768 features
- **Pipeline**: RF classifier per feature set → PSO and RF-variable-importance feature selection per set → best method per set selected → majority-voting ensemble of outputs
- **Results (abstract)**: RF-PSO ensemble outperformed RF-only in each feature set — about 2.7–7.4% increases in overall accuracy (OA); F-score gains of 0.48–3.68% (silage maize), 0–1.61% (rice), 2.82–15.43% (alfalfa), 10.96–41.13% (vegetables); PSO beat RF-variable-importance in almost all feature sets and crop types
- **Band importance**: identifying the most informative Sentinel-2 features is the stated aim of the PSO/RF-VI analysis, but the specific band-importance results are beyond the first pages — per matrix row #38, verify in full read

## Relevance to Thesis

**Low-Medium** — feature-selection reference, low priority:
- ✅ Iranian Sentinel-2 agricultural case study with a concrete, systematic feature-set taxonomy (bands vs indices vs texture vs VSI) — useful as a band/feature-importance reference when pruning inputs
- ✅ Shows PSO feature selection beats RF variable importance and recovers a few percent of accuracy lost to the Hughes effect — a candidate classical-ML baseline for feature pruning before deep models
- ⚠️ Crop mapping (land-cover classification), not stress detection; 2017-era classical ML with no temporal architecture
- ⚠️ Gains are modest and crop-dependent (0–7.4% OA); biggest wins on heterogeneous classes (vegetables), less on homogeneous ones
- ❌ No stress or salinity labels, no SITS/Mamba modeling, no SSL, no XAI

## Key Takeaway

PSO-based feature selection gives small but consistent overall-accuracy gains (2.7–7.4%) over full feature sets and over RF variable importance in multi-temporal Sentinel-2 crop mapping. Keep as a low-priority reference for band/feature-importance ideas; not part of the thesis methodology.

---

*Linked from: [[Literature-Matrix]]*
