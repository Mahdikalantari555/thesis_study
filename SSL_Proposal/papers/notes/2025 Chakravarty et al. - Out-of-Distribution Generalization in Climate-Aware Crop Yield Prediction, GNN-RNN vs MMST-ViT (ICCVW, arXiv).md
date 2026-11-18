# Out-of-Distribution Generalization in Climate-Aware Crop Yield Prediction with Earth Observation Data

## Full citation
Chakravarty, A. (2025). "Out-of-Distribution Generalization in Climate-Aware Crop Yield Prediction with Earth Observation Data." ICCV 2025 Workshop on Sustainability with Earth Observation and AI, arXiv:2510.07350v1 (independent researcher).

## Problem & setting
- First large-scale OOD evaluation of deep crop-yield models: county-level corn and soybean yield prediction across the contiguous US under (i) leave-one-cluster-out (LCO/LORO) cross-region CV and (ii) year-ahead transfer (test on 2022, 3-to-1 train-test).
- Data: CropNet (Lin et al., KDD 2024) — Sentinel-2 at 40 m resampled, 14-day revisit, <=20% cloud, only 4 of 12 bands (AG + NDVI), 2017-2022, 2,291 counties (1,200 analyzed), aggregated to 9x9 km grids; county weather data; USDA Farm Resource Regions (7 clusters) as spatial OOD domains.

## Method
- Benchmarks two SOTA models:
  - **GNN-RNN** (Fan et al. 2022): CNN + LSTM over multi-year county weather sequences with graph message passing among counties; tuned n_layers=4, dropout=0, agg=mean/pool.
  - **MMST-ViT** (Lin et al. 2023): multi-modal spatial-temporal vision transformer with attention over fused weather + satellite inputs; tuned e=128, drop=0.
- OOD difficulty levels defined from cluster similarity (Table 1): Case 1 Easy, Case 2 Medium, Case 3 Hard; metrics RMSE (bu/acre), R2, correlation; same-region year-ahead as reference.

## Data & labels
- Fully supervised (USDA county yields); no SSL. CropNet public (HuggingFace CropNet/CropNet).

## Results
- **GNN-RNN consistently beats MMST-ViT cross-region** for both crops. Soybean cross-region RMSEs: HL->MSP 8.88, NGP->HL 8.04 (best); Prairie Gateway (PG) worst in all directions (e.g., PG->EU 21.42). Corn: PG->EU 48.36.
- Year-ahead (diagonal): soybean GNN-RNN best RMSE 5.46 (EU) / 6.15 (HL) / 7.11 (NGP); corn 21.65-26.69 in stable regions.
- OOD gaps (diff-region vs same-region year-ahead): MMST-ViT gaps 1.2-18.7% (stable but less accurate); GNN-RNN gaps up to 58.5% (more accurate but more sensitive to shift). Case 3 (hard): soybean GNN-RNN 11.11 vs 7.11 same-region (56.2% gap); corn 32.07 vs 21.65 (48.1%).
- Stable regions under shift: Eastern Uplands, Heartland, Northern Great Plains; corn NGP R2~0.45 with MMST-ViT (e=128, drop 0.5); several LORO settings give negative R2/correlation for MMST-ViT.
- **Efficiency: GNN-RNN 14 min total training vs MMST-ViT 31.5 h (23 h pretrain + 8.5 h finetune) — ~135x speedup on one RTX 4090.**
- PG hardest to predict: semi-arid, unmodeled irrigation, internal heterogeneity, sparse labels, and omitted red-edge/SWIR bands that carry stress signal.

## What transfers to our thesis
- **Protocol to adopt**: leave-one-region-out and year-ahead (train past, test next season) splits are exactly the cross-year/cross-region evaluation our sugarcane model needs; the paper's "performance gap %" between same-region and shifted test is a clean metric to report.
- Warning for our model choice: large multimodal ViTs (MMST-ViT) "rely on regional memorization" and collapse OOD, while the simpler recurrent+graph model generalizes better and is 135x cheaper — supports the thesis claim that lightweight models are more transferable across years/regions for in-field products.
- Omitted red-edge and SWIR bands degrade stress-sensitive prediction (PG failure partly attributed to this) — for Landsat, advocate including SWIR1/SWIR2 + thermal since red-edge is unavailable.
- Identifies that temperature anomalies (not precipitation) drive yield variability (citing Iizumi & Sakai 2020) — supports LST/thermal-driven stress indices (CWSI) in our feature set.
- Equity framing: models underperform in irrigated semi-arid zones — directly relevant to our salinity/irrigated sugarcane context; region-aware normalization and domain-adversarial methods suggested as remedies we can cite.

## Limitations / caveats
- Single author, short workshop paper; only two models, no SSL or process-based baselines (DSSAT/APSIM acknowledged as missing); no domain adaptation techniques actually tested.
- CropNet restrictions: 4 bands, L1C uncorrected reflectance, 9 km aggregation erases field-level variability, uneven county grid coverage (5-130+ grids) biases learning.
- Yield is annual — no within-season stress dynamics; supervised labels required.

## Key numbers to quote in lit review
- First large-scale OOD benchmark of crop-yield DL: GNN-RNN beats MMST-ViT cross-region and is ~135x faster (14 min vs 31.5 h on RTX 4090).
- MMST-ViT performs well in-domain but fails under regional shift (negative R2 in several leave-one-region-out settings) — model complexity does not buy generalization.
- OOD performance gaps reach 48-58% in structurally distinct regions (Prairie Gateway) for both models.
- PG failure partly due to missing red-edge/SWIR stress bands — argument for SWIR+thermal inputs in Landsat stress detection.
