# Harvesting AlphaEarth: Benchmarking the Geospatial Foundation Model for Agricultural Downstream Tasks

## Full citation
Ma, Y., Shen, Y., Swatantran, A., & Lobell, D. B. (2026). *Harvesting AlphaEarth: Benchmarking the Geospatial Foundation Model for Agricultural Downstream Tasks*. arXiv (under review; Stanford University + Corteva Agriscience). Code: github.com/yuchima8/Harvest_AlphaEarth

## Problem & setting
- Task: first systematic evaluation of **Google DeepMind's AlphaEarth Foundations (AEF)** embeddings for agricultural downstream tasks — county- and field-level crop yield prediction (corn, soybean, winter wheat), spring tillage mapping (high vs low intensity), and cover crop mapping — across the U.S. Corn Belt (12 states), 2017–2024.
- AEF: ~480M-param GFM, pretrained on ~3B images from ~5M locations (Landsat 8/9, Sentinel-1/2, GEDI LiDAR, ERA5-Land climate, GRACE gravity, GLO-30 elevation, Wikipedia text) via a Space-Time Precision encoder + teacher–student framework; produces **annual 64-dim embeddings at 10 m**, public on Google Earth Engine 2017–2024, gap-free and cloud-immune.
- Ground truth: USDA-NASS county yields/statistics (2017/2022 Census), plus private Corteva field-level data (89,938 corn + 73,492 soybean fields 2017–2018, 20,401 winter wheat 2017–2022; 24,514 tillage records; 47,709 cover-crop field-years).

## Method
- Comparison: RF and XGBoost (200 trees) trained either on **AEF 64-dim embeddings** or on **handcrafted RS features**: 80 harmonic-regression features (2nd-order Fourier fit of 6 Landsat bands + NDVI + GCVI, with peak/b30/a30 partial-integral phenology metrics) for yield; 66 monthly features incl. tillage indices (NDTI, STI, CRC) + elevation for tillage; 144 monthly harmonic min/max features Oct–May for cover crops; plus ERA5-Land GDD/precipitation.
- **Evaluation schemes designed to prevent spatial autocorrelation inflation:** State/County-Year CV, Yearly CV (train all years, test held-out year), Scale-Transfer (county→field), Space-Transfer (EPA ecoregions: Eastern Temperate Forests ↔ Great Plains; plus U.S.→Argentina soybean).

## Data & labels
- Labels are supervised (government statistics + grower-submitted records); AEF embeddings themselves are the SSL-pretrained "label-free" representation being evaluated. RS features derived from Landsat C2 Tier 1 SR, quality-masked, crop-masked via CDL, aggregated to county/field means.

## Results
- Yield, county-level: AEF XGB R² 0.78/0.78/0.78 (corn/soy/wheat, State-Year CV) vs RS XGB 0.80/0.79/0.71 — competitive; under Yearly CV AEF consistently better (e.g., wheat 0.78 vs 0.69) → stronger temporal generalization.
- Yield, field-level: AEF ≈ RS under County-Year CV (corn 0.44 vs 0.46); **Scale-Transfer (county→field) AEF collapses: corn R² 0.25 vs RS 0.38; wheat −0.04 vs 0.22** — county-averaged embeddings dilute field-level signal.
- Tillage: county R² ~0.47–0.52 both; field-level accuracy/F1 ~0.70–0.80, RS slightly better; both struggle with high-intensity tillage (F1-0 < F1-1 — brief residue windows).
- Cover crop: RS-RF best (accuracy ~0.80–0.85); AEF good at detecting cover crops (F1-1) but misclassifies negatives; largest yearly variability.
- **Space-Transfer failure:** corn East→West AEF R² 0.02 (RS 0.66); soybean East→West −0.28 (RS 0.53); U.S.→Argentina soybean: AEF R² −2.13 (all years fail) vs RS 0.27. t-SNE shows marked ecoregion separation of AEF embeddings — geographic shift is intrinsic (static DEM/gravity reconstruction + region-specific Wikipedia text inputs suspected).
- Interpretability: AEF bands A00–A63 lack physical meaning (top feature "A05" unexplainable); RS features are interpretable (GCVI > NDVI > raw bands).
- Other limits: temporal variability under yearly CV similar to RS; annual embeddings cannot support in-season/time-critical prediction; but AEF provides better spatial coverage (AEF retrievable for 90,210 corn records vs 89,938 for RS features — cloud/gap losses).

## What transfers to our thesis
- **The key negative result for the FM-versus-lightweight-model debate:** a 480M-param, 3B-image FM's embeddings are *not* consistently better than 80 handcrafted harmonic features + RF for agricultural regression/classification, and are dramatically worse for spatial transfer and scale transfer. This directly supports our thesis choice of small domain-specific SSL models with interpretable spectral/temporal features for in-field sugarcane deployment, over FM embeddings.
- Their critique set — **spatial transferability, interpretability, temporal sensitivity** — is exactly the evaluation axes our cross-year sugarcane models must address; we can cite AEF's failures as motivation for explicit cross-year validation and XAI.
- Harmonic-regression feature engineering (2nd-order Fourier coefficients + peak-window integrals from Landsat series) is a proven, cheap, physically interpretable featurization of 16-day Landsat time series that beat a 480M-param FM — a strong candidate baseline/predictor set for our stress-detection models, and a feature family our SSL encoder should at least match.
- Two-year concatenated embeddings for cover crops (cross-season tasks spanning calendar-year boundaries) is a design pattern applicable to sugarcane ratoon cycles and off-season salinity/water stress.
- The GCVI > NDVI feature-importance finding (saturation of NDVI in high biomass — sugarcane is a high-biomass crop) supports choosing saturation-resistant indices for sugarcane monitoring.
- Yearly-CV protocol (train all years, test one held-out year, 5 seeds, report variability) is a clean evaluation template for our cross-year experiments.

## Limitations / caveats
- Under review (preprint); U.S.-centric (Corn Belt + Argentina test), temperate row crops, no stress/anomaly task, no sugarcane.
- Only RF/XGBoost on tabular features — no fine-tuning of AEF's encoder itself or DL heads on embeddings; conclusions apply to embedding-as-features use, not all FM usage.
- Annual embeddings discard intra-seasonal dynamics; the authors note in-season prediction is impossible with AEF v1 — precisely the granularity stress detection needs.
- Private Corteva labels not fully public; country-transfer test limited to soybean county yields.

## Key numbers to quote in lit review
- AEF (480M params, 3B pretraining images) vs 80 harmonic RS features: county yield R² 0.78 vs 0.80; but scale-transfer corn R² 0.25 vs 0.38 and East→West corn R² 0.02 vs 0.66.
- U.S.→Argentina soybean transfer: AEF R² −2.13 vs RS features 0.27 — FM embeddings failed completely across continents.
- GCVI outperformed NDVI in RF feature importance (NDVI saturation in high-biomass crops).
- AEF advantages: gap-free cloud-immune 10-m annual 64-dim embeddings 2017–2024 on GEE; retrieved features for 90,210 vs 89,938 corn records (272 records lost to Landsat gaps with RS features).
