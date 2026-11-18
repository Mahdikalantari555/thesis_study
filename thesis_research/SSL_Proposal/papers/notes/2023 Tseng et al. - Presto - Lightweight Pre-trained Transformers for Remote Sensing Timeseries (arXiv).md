# Presto: Lightweight, Pre-trained Transformers for Remote Sensing Timeseries

## Full citation
Tseng, G., Cartuyvels, R., Zvonkov, I., Purohit, M., Rolnick, D., & Kerner, H. (2023). "Lightweight, Pre-trained Transformers for Remote Sensing Timeseries." arXiv:2304.14065v4 [cs.CV] (Mila/McGill/ASU; NASA Harvest).

## Problem & setting
- Label scarcity for satellite ML globally; existing SSL backbones treat RS as single-timestep images (no temporal dimension), single-sensor, and are too large to deploy for contiguous map making. Goal: a small, multi-sensor, pixel-time-series pre-trained transformer usable by feature extraction or fine-tuning.
- Pre-training data: 21.5M pixel-timeseries sampled globally (Dynamic World sampling strategy, stratified by ecoregion/land cover), 10 m/px, 12 contiguous monthly timesteps within 2020-2021.

## Method
- **Architecture**: encoder-decoder transformer, 2 attention layers, 8 heads, embedding dim 128, MLP ratio 4, ~402K params total (0.40-0.81 M depending on count); MAE-style (He et al. 2022): mask input, decoder reconstructs, decoder discarded at downstream time.
- **Tokenization**: per timestep, channels split into sensor/product groups (S1 VV/VH; S2 RGB, Red-Edge, NIR-10m, NIR-20m, SWIR; NDVI; ERA5 precip+2m-temp; Dynamic World class; static SRTM elevation+slope; static lat/lon 3D Cartesian). Each group gets learned linear projection + learned channel-group encoding + sinusoidal positional + month (sin/cos of month/12) encodings. Coordinates never masked.
- **SSL objective**: masked autoencoding with **structured masking** at ratio 0.75 — randomly select one of 4 strategies per sample: (1) random (t x d), (2) channel-groups (whole sensor masked), (3) contiguous timesteps, (4) random timesteps. Loss: L_total = L_MSE + lambda*(Ncat/Ncont)*L_CE balancing continuous (MSE) and categorical (cross-entropy, Dynamic World) reconstructions, lambda=2. Trained 20 epochs, batch 4096, AdamW, lr 1e-3 cosine, wd 0.05; 43 h on one V100.
- Downstream modes: Presto_R (linear/logistic on frozen embeddings), Presto_RF (random forest on embeddings), Presto_FT (full fine-tune); image tasks use mean+std aggregation of per-pixel tokens.

## Data & labels
- Pre-training fully label-free (reconstruction only). Downstream: CropHarvest crop-type segmentation (Kenya maize 1,345, Brazil coffee 203, Togo cropland 1,319 samples), S2-Agri100 crop classification (1,500), TreeSatAI (45,337), EuroSat (21,600), fuel moisture (1,578), algae blooms (777) regressions. Labels used only at fine-tuning/probing.

## Results
- CropHarvest mean F1: Presto_R 0.835 (adapting only 129 params) vs TIML 0.802 (91K params) and MOSAIKS-1D 0.738; AUC 0.917 vs TIML 0.890. Random forest baseline 0.441.
- Robust to missing inputs: with only 3 of 12 months, Presto still matches full-input TIML/MOSAIKS-1D; negligible drop without Dynamic World (0.835->0.836 without).
- S2-Agri100: pre-trained Presto OA 68.89%, kappa 0.58 vs SITS-Former 67.03%/0.56, with 6x fewer params (0.4 M vs 2.5 M); random-init Presto only 45.98% — pre-training adds ~+23% OA.
- EuroSat fine-tune: MS 0.953 accuracy (SatMAE ViT-L MS 0.990 with 306 M params); pre-training adds +14-22% acc over random init. kNN: Presto MS ~0.92 comparable to ScaleMAE/SatMAE with 4 orders of magnitude fewer FLOPs (2.37 MFLOPs/pixel vs 535 GFLOPs/image for SatMAE MS).
- Regression: best mean RMSE delta vs linear baseline (-7.24% Presto_FT; fuel moisture RMSE 25.28).
- Ablations: combining all structured masking strategies (0.665 F1) beats random-only (0.646); performance scales with size (2x width 128->256: F1 0.665->0.687).

## What transfers to our thesis
- **The canonical lightweight RS time-series backbone**: 0.4 M params, feature-extraction mode trains only 129 params — directly supports our "lightweight multi-product in-field" requirement; inference cheap enough for whole-field Landsat mapping.
- Structured masking over (timesteps x sensor-groups) is the exact recipe to adapt to Landsat: mask whole months (cloud gaps), whole band groups (optical vs LST/derived indices) so the model natively handles missing 16-day composites and missing thermal data.
- Demonstrates month encodings + static location/topography tokens transfer across geographies/years — supports our cross-year model reuse; mixing derived products (NDVI; analogously ETa/CWSI, NDWI, salinity proxies) as extra channel groups improves performance.
- Shows pixel-time-series models can rival image models on many tasks; but for scene-level tasks aggregation (mean+std) is the weak point — relevant when deciding pixel-level vs field-level pooling for stress maps.
- Presto is explicitly pre-trained on Sentinel data at 10 m; our thesis extends the pixel-time-series MAE recipe to Landsat 30 m / 16-day with thermal.

## Limitations / caveats
- No thermal band in pre-training; 10 m assumption; monthly (not 16-day) timesteps during pre-training.
- Pixel-independent: no spatial context; image-level aggregation loses information (EuroSat Highway/River classes plateau).
- Crop/stress labels downstream still needed; pre-training validation was on CropHarvest (crop-type, not stress).
- Training data 2020-2021 only; no explicit cross-year evaluation.

## Key numbers to quote in lit review
- 0.4 M-parameter transformer beats 2.5 M SITS-Former on crop classification (OA 68.89% vs 67.03%) and matches 300 M ViT MAEs on EuroSat MS (0.953 vs 0.990) with up to 1000x fewer parameters and 4 orders of magnitude fewer FLOPs.
- CropHarvest mean F1 0.835 with only 129 adapted parameters vs meta-learning SOTA 0.802.
- Structured masking (channel-group + contiguous/random timestep) outperforms MAE random masking (F1 0.665 vs 0.646).
- Pre-training yields +23% OA over random init on the small crop dataset (S2-Agri100), and robust performance with only 25% of input timesteps.
