# RL-VI: Reinforcement learning based dynamic vegetation index formulation for rice crop stress detection using satellite and mobile imagery

## Full citation
Seralathan, P., Edward, A. S. (2025/2026). Reinforcement learning based dynamic vegetation index formulation for rice crop stress detection using satellite and mobile imagery. *Scientific Reports*, 16, 3447. DOI: 10.1038/s41598-025-33386-9. SRM Institute of Science and Technology, India.

## Problem & setting
- Task: supervised rice crop stress detection (5 severity levels: Healthy/Low/Moderate/High/Extreme) by LEARNING a dynamic vegetation index instead of using static VIs (NDVI, EVI, SAVI, NDMI).
- Setting: rice fields at Polur, Tamil Nadu, India (lat 12.4998, lon 79.1343), kharif 2025; 45 cloud-free Sentinel-2 L2A images (≈10-day intervals, July–Oct 2025) + 1,200 geotagged 64-MP smartphone canopy images from 10 plots; benchmarks: Indian Pines AVIRIS hyperspectral (10,249 px, 224 bands, relabeled vegetation/non-vegetation) and a Wheat Salt Stress hyperspectral set (300 cubes, 204 bands, control vs stressed).

## Method
- VI formulation as an MDP solved with Deep Q-Network: state = normalized reflectance vector + band-selection history; action = select a band triplet (i, j, k) and optional weights (a, b, c) to build VI = (a·Bi − b·Bj)/(c·Bk + ε) (also linear form w1·NIR + w2·SWIR − w3·Red); reward = downstream F1-score, or hybrid F1 − β·entropy of classifier output.
- Learned VI feeds a lightweight classifier (RBF-SVM or 3-layer 1D-CNN with BN, dropout 0.3); DQN: 2-layer MLP [128,64], ReLU, Adam lr 1e-3, γ=0.95, ε-greedy 1.0→0.1, 200 episodes.
- Cross-platform fusion: RGB-derived indices (NDVI_RGB=(G−R)/(G+R), ExG=2G−R−B, VARI) used for validation/reward shaping/state extension; mobile+satellite joint training reported +3.4% accuracy and ~10 days earlier detection.
- Ablations: 2/3/4-band indices (3-band best; 4-band overfits), F1 vs entropy-regularized reward (hybrid slightly better), mobile integration.
- SHAP used to interpret band contributions (red-edge and SWIR most important).

## Data & labels
- Stress labels from expert/ground-truth; stratified 70/15/15 split; class balancing via random undersampling. Fully label-supervised — the RL optimizes a feature, not a representation.

## Results
- Polur Sentinel-2: RL-VI accuracy 89.4%, F1 0.88 vs NDVI 76.5% accuracy / 0.72 F1 (up to +12 points; mean 93.2% acc / 0.91 F1 reported across rice dataset with classwise F1 0.84–0.94).
- Transfer fine-tuning: Indian Pines 91.2% accuracy, +5–7% over NDVI/MLVI; Wheat Salt Stress also improved.
- Early detection: 10–14 days before visible symptoms, notably at panicle initiation/booting/flowering (SWIR/red-edge sensitivity).
- Statistics: one-way ANOVA F=88.24, p<0.001; pairwise t-tests p<0.001; mobile-satellite index discrepancy ≤2.3 pp for RL-VI vs 4.5 pp for NDVI.
- Cross-platform: adding mobile imagery +3.4% accuracy, ~10 days earlier detection.

## What transfers to our thesis
- Core idea is highly relevant: **learned, crop- and region-adaptive band combinations outperform static VIs** for stress; for our label-free sugarcane work, the RL/search objective (F1 reward) can be replaced by SSL/self-supervised criteria (e.g., reconstruction error, temporal contrast, CWSI agreement) to discover stress-sensitive Landsat band/LST combinations without labels.
- Confirms red-edge/SWIR (water content) bands carry earliest stress signal — for Landsat 8/9 this maps to SWIR1/SWIR2 + LST; supports our CWSI/ETa feature choices.
- 3-band composite sweet spot (interpretability vs overfitting) is a useful design rule for lightweight in-field indices/products.
- Hybrid reward (accuracy − entropy) to reduce prediction uncertainty is transferable to any stress classifier under uncertainty-aware deployment.
- Mobile/satellite cross-validation strategy: cheap RGB phone data as weak validation layer for satellite stress maps — usable for our in-field verification protocol.

## Limitations / caveats
- Fully label-supervised reward — needs labeled stress data; not SSL. RL exploration is computationally costly; single season, single region; no cross-year test (authors acknowledge).
- Sentinel-2 10-day composites, small area (one district); 5-class severity labels of unclear provenance/validation; smartphone RGB indices are weak proxies.
- Scientific Reports format; ablation tables sparse; "MLVI/H_VSI" baselines not deeply specified.

## Key numbers to quote in lit review
- RL-learned 3-band VI beats NDVI by ~12 points accuracy (89.4% vs 76.5%, F1 0.88 vs 0.72) for rice stress on Sentinel-2.
- Learned VI detects stress 10–14 days before visible symptoms using SWIR/red-edge sensitivity.
- Adding smartphone RGB imagery to the RL state improves accuracy +3.4% and detection lead ~10 days.
- ANOVA F=88.24 (p<0.001) for RL-VI vs static/ML indices; SHAP ranks red-edge and SWIR bands top for stress discrimination.
