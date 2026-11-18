# Embedding NDRE Trajectories into Contrastive Learning for Label-Free, Physiology-Aware Crop-Stress Staging and DSS Outputs (EigenCL)

## Full citation
Ahmad, S. (2026). *Embedding NDRE Trajectories into Contrastive Learning for Label-Free, Physiology-Aware Crop-Stress Staging and DSS Outputs*. arXiv (preprint). (Companion/extension of the author's 2025 EigenCL paper.) Note: no arXiv ID printed in the extracted text; author-affiliated preprint, single author (Brandt Group of Companies, Canada).

## Problem & setting
- Task: **label-free crop drought-stress staging** into 4 physiological clusters (Healthy, Mild, Moderate, Severe) from Sentinel-2 NDRE (red-edge chlorophyll index) temporal trajectories — moving beyond single-date index thresholds and visual-similarity clustering.
- Data: 10,000 maize 100×100-px Sentinel-2 NDRE patches, Iowa 2020 (drought year), 5-day cadence July–September (5 dates → 5-D mean-NDRE vectors per patch). Test without retraining: 3,500 patches Nebraska 2023. Soil-moisture validation: 1,500 patches each for Iowa 2020/2022/2023 at 3 Iowa Mesonet stations (12–24-inch depth, daily). U.S. Drought Monitor polygons define objectively stressed zones; USDA county yields (2019–2024) confirm stress years (Buena Vista 2020, Monona 2022, Buchanan 2023 = lowest yields).

## Method
- **EigenCL = eigenvector-guided contrastive learning.** Build RBF (Gaussian) similarity matrix over raw NDRE 5-date trajectories; extract the **principal eigenvector** of this matrix (captures ~76.3% of variance; correlates r=0.95 with mean NDRE) as a continuous stress-severity proxy per patch.
- ResNet-50 encoder on NDRE patches → 2048-D embeddings → FC+BN+LeakyReLU projection head → L2 normalize. Cosine similarity matrix computed between embeddings.
- **Loss replaces visual augmentation/cosine targets with physiological similarity:** physiological score s = exp(−Δ/σ), Δ = |normalized eigen-weight difference|, σ=0.5 (text also gives smoothing σ=0.1 in Eq. 5 context). Pull loss (temperature-scaled log, τ=0.075) attracts pairs with high s; push loss (margin hinge, margin m=0.2, weight λ=4.0) repels low-s pairs. Total normalized over pairs; batch 256. Hyperparameters tuned by grid search maximizing Pearson correlation between embedding distance and NDRE stress trajectories + clustering metrics.
- Downstream: k-NN and logistic regression on frozen embeddings; cluster quality via Silhouette/DBI/CHI; validation via lagged Spearman correlations with soil moisture (0–14-day lags) and ARI against soil-quartile stress classes.

## Data & labels
- Fully label-free training; validation only via independent physical data (soil moisture, drought maps, yields). Datasets on Kaggle.

## Results
- Clustering (Iowa): EigenCL Silhouette 0.748, DBI 0.350, CHI 49,624 vs ablation (no eigenvector guidance) 0.533/0.618/33,446, K-Means 0.465/0.958/19,305, SimCLR 0.416/0.724/2,252, ProtoCLR 0.348/0.892/9,995.
- Clusters form a monotonic NDRE gradient; severe-stress cluster shows sharp NDRE decline starting mid-July = tasseling–silking (VT–R1), the known most drought-sensitive maize stage (up to 50% yield loss). Clusters with nearly equal mean NDRE (0.51 vs 0.52) separate by trajectory shape — temporal dynamics, not magnitude, drive separation.
- Cross-region transfer (Iowa 2020 → Nebraska 2023, no fine-tuning): modest metric decline, clustering structure retained.
- Soil-moisture validation: NDRE lags soil moisture 0–14 days; best-lag Spearman ρ = 0.525 (2020, 6-day lag), 0.721 (2022, 14-day), 0.608 (2023, 0-day); ARI vs soil-quartile stress labels 0.12–0.371 (best lag) vs ~0 same-day.
- Downstream classification on frozen embeddings: k-NN 89.1% acc / F1 0.87; logreg 85.2% / 0.82. ANOVA F=37,950, all Tukey pairwise cluster NDRE differences p<0.0001.

## What transfers to our thesis
- **Closest methodological template in this batch for our label-free stress staging:** contrastive learning whose positive/negative pairs are defined by an unsupervised physiological signal (index trajectory structure) rather than augmentation — directly adaptable to sugarcane with Landsat NDVI/NDRE + LST/CWSI trajectories as the guiding signal.
- Demonstrates the key argument that generic SSL (SimCLR, cosine) fails on spectral-temporal agricultural data (Silhouette 0.416 vs 0.748) — a citable justification for domain-aware SSL design in our proposal.
- Trajectory-shape > magnitude: clusters with equal mean NDRE but different dynamics separate — supports modeling the full 16-day Landsat time series (shape) rather than single-date thresholds for water/salinity stress.
- Cross-year, cross-region zero-shot transfer validated (Iowa 2020 → Nebraska 2023) — direct precedent for our cross-year in-field model evaluation.
- The 0–14-day soil-moisture-to-canopy lag finding is directly relevant to our ETa/CWSI water-stress pathway: canopy optical signals respond with a delay to root-zone water — informs lag-aware feature construction and validation design for sugarcane water stress.
- 4-tier staged output (Healthy→Severe) + DSS rule thresholds shows how label-free clusters become decision products — template for our "multi-product" in-field outputs.

## Limitations / caveats
- Preprint, single author, no peer review; some internal inconsistencies (σ reported as both 0.1 and 0.5; some tables lack numeric detail, e.g., yield table empty in extraction).
- Only 5 dates per trajectory (5-D vector) and one index (NDRE); no thermal/LST, no soil salinity; maize only, US Midwest only.
- Spectral clustering context: RBF + principal eigenvector is essentially spectral-embedding-guided contrast; sensitive to bandwidth γ and eigenvector choice (lower eigenvectors degraded performance — acknowledged).
- Validation against station soil moisture is point-scale (~50 km² windows) vs 10-m patches; ARI values (0.12–0.37) show only moderate label agreement.
- Severe cluster timing linked to VT–R1 qualitatively; per-cluster yield penalties "not yet quantified."

## Key numbers to quote in lit review
- EigenCL clustering: Silhouette 0.748 / DBI 0.35 / CHI 49,624 vs SimCLR 0.416 / 0.724 / 2,252 — generic SSL fails on physiological time series.
- NDRE tracks 12–24-inch soil moisture at 0–14-day lag with Spearman ρ up to 0.72.
- Zero-shot cross-state transfer (Iowa 2020 → Nebraska 2023) preserves stress-cluster structure without fine-tuning.
- k-NN on frozen embeddings: 89.1% accuracy / F1 0.87 for 4-stage stress classification.
- Principal eigenvector of NDRE-trajectory RBF matrix explains ~76% of variance and correlates r=0.95 with mean NDRE.
