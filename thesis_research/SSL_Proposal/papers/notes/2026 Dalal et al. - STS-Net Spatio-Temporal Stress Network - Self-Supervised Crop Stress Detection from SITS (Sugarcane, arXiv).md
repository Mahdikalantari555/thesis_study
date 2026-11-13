# STS-NET: Spatio-Temporal Stress Network for Self-Supervised Crop Stress Detection using Satellite Image Time Series

## Full citation
Dalal, P., Ranjan, R., Ghildiyal, S., Tamaskar, S., & Goel, N. (2026). *STS-NET: Spatio-Temporal Stress Network for Self-Supervised Crop Stress Detection using Satellite Image Time Series*. arXiv:2607.18791 [cs.CV] (preprint, IEEE member format). https://arxiv.org/abs/2607.18791

## Problem & setting
- Task: **sugarcane water stress, nitrogen stress, and combined water–nitrogen stress detection** from satellite image time series with minimal labels — the single most thesis-relevant paper in this batch (same crop, same stress types).
- Pretraining data (BSPT): PlanetScope imagery over Barnala district, Punjab, India (~196 km²), 32 time steps Feb 2023–Feb 2024 at 9–11-day intervals, <15% cloud, ~22M pixels, fully unlabeled.
- Evaluation data (LK dataset, from Ranjan et al./Plaksha): controlled 3-acre sugarcane experiment in Lakhimpur Kheri, Uttar Pradesh (28°27'N, 80°55'E); 62 plots, plant cane planted Feb 2023; 3 water blocks (50%/100%/150% of standard irrigation) × 3 nitrogen levels (0.2–1 kg fertilizer) imposed during tillering + grand-growth (April–September) → 9 combined stress classes; no ratoon.

## Method
- **Input:** per-pixel time series tensor (T=32 × C=5): RGB + NIR + Avg(NDVI, GNDVI, RECI, NDRE); mean-imputed missing values; min–max normalized.
- **SSL pretraining:** 3D convolutional autoencoder (3D-CAE) — stacked 3D conv encoder compresses the pixel-time-series into latent space, decoder reconstructs the original spectral sequence from surrounding space–time context; **MSE reconstruction loss** on unlabeled BSPT pixels. Adam lr 0.001, batch 256, ≤40 epochs, early stopping.
- **Fine-tuning:** decoder discarded, encoder frozen as feature extractor → 64-D latent vector per pixel → lightweight classifiers (RF / XGBoost / SVM) trained on labeled LK pixels for three separate multiclass tasks (water 3-class, nitrogen 3-class, combined 9-class). 80:20 stratified split.
- Model size: **19.2K parameters** (vs Presto ~400K).

## Data & labels
- Pretraining fully label-free (BSPT, 22M pixels). Fine-tuning labels come from the controlled LK field experiment (systematically induced stress = ground truth), pixel-level.

## Results
- Water stress: 3D-CAE+RF accuracy 0.97, precision 0.98 (claimed 97.98% precision), F1 0.98. Nitrogen: 3D-CAE+XGBoost acc 0.87, precision 0.87 (85.08% claimed). Combined 9-class: 3D-CAE+XGBoost acc 0.84, precision 0.85 (83.47% claimed).
- Baselines: supervised RF/SVM/XGBoost on raw series 0.44–0.60 (water), 0.28–0.31 (combined); supervised 2-layer CNN 0.54/0.52/0.28; **Presto (SSL foundation model) 0.82/0.81/0.72** — the domain-specific 3D-CAE beats the general-purpose Presto by 0.08–0.12 accuracy.
- Ablations: RGB+NIR+Avg(VIs) is the best channel config (97.98/85.08/83.47 vs RGB+NIR 86.32/72.14/68.21); temporal depth T: 8 steps (≈2 months) still gives 90.32% water accuracy, monotonic improvement to T=32 — stress signals visible within ~2 months.

## What transfers to our thesis
- **Direct recipe template:** self-supervised reconstruction autoencoder on pixel-level vegetation-index time series, pretrained on unlabeled regional data, frozen encoder + tiny classifier head — exactly the "lightweight SSL + in-field model" architecture class of our thesis, here demonstrated on sugarcane with water AND nitrogen stress simultaneously.
- Key competitive result to cite: a 19.2K-parameter domain-specific 3D-CAE outperforms Presto (400K params, globally pretrained) on sugarcane stress — supports the thesis argument that small agri-specific SSL models can beat large generic FMs for in-field deployment.
- Ablation evidence for channel selection: red-edge VIs (NDRE/RECI) + NIR + averaged VIs substantially outperform RGB/NIR alone (+11.7 pp water accuracy) — informs which Landsat-8/9 bands/indices (no red edge on Landsat, but NDVI/GNDVI analogs + thermal) to include.
- Temporal-depth ablation (T=8 → 32: 90.3→98.0 water accuracy) quantifies the value of dense temporal sampling; for Landsat 16-day series this sets expectations (fewer steps, lower ceiling) and justifies multi-year stacking.
- The LK controlled-experiment design (induced water×nitrogen factorial, 9 classes, tillering+grand-growth windows) is a validation-design blueprint for our sugarcane stress ground truth.
- Pixel-level (not field-level) formulation allows within-field stress heterogeneity mapping.

## Limitations / caveats
- Preprint, not peer-reviewed; arXiv ID 2607.18791 (July 2026).
- PlanetScope 3-m 9–11-day imagery, NOT Landsat 30-m 16-day; spatial resolution is a major driver of their accuracy — results will not transfer 1:1 to Landsat.
- No thermal band / LST / CWSI or ETa — water stress inferred only through optical VIs; the thesis's thermal pathway is complementary and untested here.
- Only one season, one site, plant cane only (no ratoon); pretraining region (Punjab) ≠ evaluation region (UP) but same broad agro-zone — cross-year and true cross-region transfer untested.
- Reconstruction-only pretext (no masking strategy, no contrastive term); MSE imputation of missing pixels may leak temporal smoothness.
- Ground truth = imposed treatment levels, not measured plant physiological stress (soil moisture, canopy temperature) — treatment≠stress severity assumption.

## Key numbers to quote in lit review
- First self-supervised 3D-CAE for crop stress detection from SITS: 97.98% precision (water), 85.08% (nitrogen), 83.47% (combined 9-class) on a controlled sugarcane experiment.
- 19.2K-parameter 3D-CAE beats Presto (400K params): accuracy 0.97 vs 0.82 (water), 0.87 vs 0.81 (nitrogen), 0.84 vs 0.72 (combined).
- Supervised baselines on raw series collapse on combined stress (0.23–0.31 accuracy) vs 0.84 with SSL features.
- Water stress detectable with only 8 time steps (~2 months, 90.3% accuracy); full 32 steps reach 98.0%.
- Red-edge VIs (NDRE/RECI averaged with NDVI/GNDVI) add +11.7 pp water-stress accuracy over RGB+NIR.
