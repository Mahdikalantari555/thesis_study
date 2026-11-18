# EigenCL: Temporal Vegetation Index-Based Unsupervised Crop Stress Detection via Eigenvector-Guided Contrastive Learning

## Full citation
Ahmad, S. (2025). "Temporal Vegetation Index-Based Unsupervised Crop Stress Detection via Eigenvector-Guided Contrastive Learning (EigenCL)." arXiv preprint (independent/industry author, Brandt Group Canada). Note: preprint, not peer-reviewed venue; some cited works appear unverifiable — treat as gray literature.

## Problem & setting
- Label-free early drought-stress detection in corn from Sentinel-2 NDRE time series; goal: embeddings that cluster by physiological stress trajectory (not visual appearance), detecting stress before conventional NDRE thresholds trigger.
- Data: ~10,000 Sentinel-2 NDRE patches (100x100 px, 10 m) from drought-affected Iowa cornfields 2020, five cloud-free dates July 1-30 Aug (~15-day spacing); validation on 2,000 patches from Nebraska 2023 (milder drought), no fine-tuning, no retraining.

## Method
- **Per-patch NDRE time series**: mean NDRE over 5 dates -> 5-D vector; no normalization (preserve absolute chlorophyll differences).
- **Biological supervision signal**: RBF similarity matrix S_ij = exp(-gamma ||x_i - x_j||^2) over all patch time series; **principal eigenvector** (explains 76% of variance, r = 0.95 with raw NDRE) gives each patch a scalar stress-severity weight w_i — this replaces visual augmentations and cosine similarity as the positive/negative criterion.
- **Encoder**: ResNet-50 on NDRE rasters -> 2048-D embedding -> FC+BN+LeakyReLU projection head, L2-normalized.
- **EigenCL loss**: biological similarity S_ij = exp(-|w_i - w_j|/sigma), sigma=0.1 (final config sigma=0.5). Pull loss L_pull = sum S_ij * log(1 + (1-sim(z_i,z_j))/tau), tau=0.075; push loss L_push = sum lambda*(1-S_ij)*max(0, sim(z_i,z_j) - m), lambda=4.0, margin m=0.2; total normalized by N(N-1), batch 256. Hyperparameters grid-searched on Silhouette/DBI/CHI + NDRE-gradient stability.
- Key property: patches with similar stress trajectories cluster together regardless of visual appearance; visually similar patches with divergent NDRE dynamics separate.

## Data & labels
- Fully unsupervised training; NDRE-threshold stress stages (healthy >= 0.559, mild 0.479-0.559, moderate 0.322-0.479, severe < 0.322; detection threshold 0.40 from literature) used only for evaluating cluster agreement and early-detection lead time.

## Results
- Clustering (Iowa): EigenCL Silhouette 0.748, DBI 0.350, CHI 49,624 vs ablation w/o eigenvector (0.533/0.618/33,446), K-Means on NDRE (0.465/0.958/19,305), SimCLR (0.416/0.724/2,252), ProtoCLR (0.348/0.892/9,995). ARI between EigenCL clusters and NDRE stress stages 0.719 (95% CI 0.704-0.733).
- Clustering (Nebraska 2023, zero-shot): Silhouette 0.795, DBI 0.164, CHI 41,260 — generalizes across region/year with frozen model and Iowa thresholds; ~10-day lead time retained.
- Downstream (frozen embeddings, 70/30): k-NN 89.1% acc / F1 0.87; logistic regression 85.2% / F1 0.82 (abstract reports 95% k-NN — inconsistent with table; table is 89.1%).
- Early detection: stress flagged before the 0.40 NDRE threshold in **76% of cases, average lead 11.8 days (up to 12 days)**.
- Statistics: ANOVA across clusters F=37,950, p<0.0001; all Tukey pairwise NDRE differences significant.
- Ablation: replacing principal eigenvector with lower-variance components drops clustering and classification performance — the dominant stress-trajectory component is the necessary supervision.

## What transfers to our thesis
- **Closest methodological sibling in this batch** for our label-free sugarcane stress objective: guide contrastive learning with a physiologically meaningful scalar (here, an NDRE-trajectory eigenvector weight) instead of visual augmentation. For our case: derive the guide from ETa/CWSI or LST-derived stress proxies (physics-informed signal) and contrast Landsat field-patch embeddings by stress-trajectory similarity — directly addressing salinity/water stress where visual similarity is misleading.
- Demonstrates the failure mode we should cite: SimCLR with generic augmentations collapses on spectral-temporal agricultural data (Silhouette 0.416) — supports domain-aware SSL design in the thesis.
- Five-date 15-day-spaced VI series on Sentinel-2 transfers structurally to Landsat 16-day composites; the eigen-decomposition-of-trajectory-similarity trick is cheap and sensor-agnostic (works with NDVI/NDWI/LST trajectories).
- Zero-shot transfer Iowa 2020 -> Nebraska 2023 (different year, region, drought intensity) is exactly the cross-year evidence our thesis needs to replicate for sugarcane.
- Early-warning framing: lead time over index thresholds (11.8 days) is a strong headline metric we can adopt for ETa/CWSI-based early stress detection.

## Limitations / caveats
- Preprint quality concerns: single author, industry affiliation; citation list contains questionable entries; abstract's "95% k-NN" contradicts the results table (89.1%); hyperparameter sigma reported as 0.1 and 0.5 in different sections.
- "Stress labels" are NDRE-threshold proxies, not ground-truth physiological measurements — evaluation is circular (guide signal = evaluation signal, r=0.95 by construction).
- Only NDRE (no thermal/ETa), only corn, only 5 dates; needs red-edge band (Landsat lacks it — would need NDVI/SWIR substitutes).
- ResNet-50 on raster patches, not time-series-native architecture; no comparison to state-of-the-art SSL (MAE/DINO); no field-level aggregation or yield validation.

## Key numbers to quote in lit review
- Eigenvector-guided contrastive learning on 5-date NDRE trajectories: Silhouette 0.748 vs SimCLR 0.416 and K-Means 0.465; ARI 0.719 vs literature NDRE stress stages.
- Early stress detection 11.8 days (up to 12) ahead of conventional NDRE thresholds in 76% of cases.
- Zero-shot transfer to a different region/year (Nebraska 2023) retains clustering quality (Silhouette 0.795, DBI 0.164) without retraining.
- Principal NDRE-trajectory eigenvector explains 76% of variance and correlates r=0.95 with raw NDRE — a cheap biological supervision signal.
