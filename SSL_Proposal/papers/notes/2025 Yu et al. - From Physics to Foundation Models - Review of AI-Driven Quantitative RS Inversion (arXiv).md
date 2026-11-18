# From Physics to Foundation Models: A Review of AI-Driven Quantitative Remote Sensing Inversion

## Full citation
Yu, Z., Idna Idris, M. Y., Wang, H., Wang, P., Chen, J., & Wang, K. (2025). *From Physics to Foundation Models: A Review of AI-Driven Quantitative Remote Sensing Inversion*. arXiv:2507.09081 [cs.CV]. https://arxiv.org/abs/2507.09081

## Problem & setting
- Review paper (no new experiments): quantitative remote sensing (RS) inversion = estimating continuous surface variables (LAI, NDVI, FAPAR, FVC, AGB, canopy height, ET, soil moisture, LST, VPD, albedo, turbidity, AOD, etc.) from satellite observations.
- Framing: three-stage paradigm evolution — (1) physics-based models (PROSAIL, SCOPE, DART, Hydrolight, MODTRAN/6S, Penman–Monteith), (2) data-driven ML/DL (RF, SVR, XGBoost, CNN, LSTM/RNN, GNN, Transformer), (3) foundation models (SatMAE, GFM, mmEarth).
- Emphasizes inversion task attributes: continuous outputs with physical semantics, multi-scale (10–500 m), single- to multi-temporal sequences, multimodal heterogeneous sensors (MSI, HSI, SAR, TIR, LiDAR), cross-region domain shift.

## Method (survey structure / taxonomy)
- **Physics-based inverse strategies:** Look-Up Tables (no differentiability needed, poor OOD generalization, high cost in high dimensions); optimization-based estimation (least squares, MCMC, Kalman — sensitive to initialization/local minima); PINNs (physical equations as soft loss constraints; suited to weak supervision but training instability and loss-weighting sensitivity).
- **Foundation models for inversion (Table 5):**
  - SatMAE: MAE + ViT, multi-temporal Sentinel-2, masked autoencoding (mask + reconstruct); tasks NDVI/LAI/FAPAR.
  - GFM: multimodal Transformer, optical+SAR+DEM, self-supervised + multi-task; tasks AGB, canopy height, SIF, carbon stock.
  - mmEarth: cross-modal Transformer, HSI+SAR+DSM, masked + contrastive learning; tasks NDVI, biomass.
- Identified FM gaps for regression: regression heads are shallow MLPs under-explored; fine-tuning strategies not standardized; almost no physical constraints in pretraining objectives.

## Data & labels
- Benchmark dataset table: BigEarthNet (S1+S2, Europe, 10–20 m), SSL4EO-S12/L (global, 10–30 m, used for LAI/FAPAR/SIF), Satlas (S2+SMAP+meteo, soil moisture/AGB), Sen4AgriNet (S1/S2 + agronomic ground truth, Europe/Africa), Open-Canopy (France, RGB+LiDAR, 1–10 m, canopy height/AGB).
- Recurring theme: ground truth for inversion targets (AGB, SIF, SM) is sparse, expensive, temporally mismatched, and label-noisy; this motivates self-supervised pretraining and RTM-simulation-based weak supervision.
- Metrics: RMSE, MAE, R2, SSIM, PSNR.

## Results
- No quantitative benchmark of its own (review). Comparative qualitative claims: ML = interpretable, small-data friendly, but manual features and weak spatio-temporal context; DL = end-to-end, nonlinear, multimodal, but label-hungry and domain-shift sensitive; FMs = strong few-shot/multi-task transfer but high compute cost and unproven regression adaptation.

## What transfers to our thesis
- Directly relevant framing for the lit review: positions ET/LST/soil-moisture retrieval (our CWSI/ETa water-stress pathway) as "quantitative inversion," and argues self-supervised FM pretraining is the current answer to label scarcity — the exact gap our label-free sugarcane stress work targets.
- Supports the argument that SSL pretraining + lightweight regression/anomaly heads beats task-specific supervised models under label scarcity; also supports using physics constraints (energy balance, Penman–Monteith/CWSI relationships) as loss terms (PINN-style) — a concrete design option for our ETa-proxy-informed SSL.
- The claim that regression heads and fine-tuning protocol are under-studied in RS FMs justifies our choice of lightweight downstream heads (AE ensembles, small decoders) instead of heavy FM fine-tuning.
- Cross-region/cross-year domain shift is named as the core generalization bottleneck — aligns with our cross-year in-field model requirement.

## Limitations / caveats
- Pure review, mostly pre-2025 literature; no experiments, no quantitative comparison tables of methods' accuracy.
- Coverage of FMs for *time-series* inversion is thin (SatMAE/GFM/mmEarth are spatial/pixel-level; temporal SITS foundation models like Presto are not central).
- No treatment of anomaly-detection-style stress monitoring; all targets assume regression with some labels.
- Some citations are oddly off-topic (e.g., stealth/multimedia references), suggesting loose citation hygiene.

## Key numbers to quote in lit review
- Taxonomy of 5 inversion variable groups with variable→model mapping (e.g., ET: RF/LSTM → no FM yet; LST: XGBoost/CNN-LSTM → mmEarth) — useful as evidence that ET/SM inversion lacks mature FM solutions.
- 3-stage paradigm claim: physics → data-driven → foundation models, with label scarcity + domain shift cited as the two persistent blockers.
- Benchmark datasets span 1–30 m resolution; SSL4EO explicitly supports LAI/FAPAR/SIF self-supervised benchmarks.
