# GloSSR: Global-Scale Self-Supervised Spatiotemporal Learning for NDVI Time-Series Reconstruction

## Full citation
Li, A., Jiang, M., Guan, X., Chu, D., & Shen, H. (2026). *Global-Scale Self-Supervised Spatiotemporal Learning for NDVI Time-Series Reconstruction*. arXiv (preprint, Wuhan University; corresponding author Huanfeng Shen). No arXiv ID printed in text.

## Problem & setting
- Task: reconstruction of cloud-contaminated/noise-corrupted NDVI time series (gap filling + denoising) — a prerequisite step for any downstream vegetation/stress monitoring on optical satellite series.
- Data: MODIS MOD13A2 NDVI, 1 km, 23 images/year, 2001–2024, globally sampled tiles (training from low–mid-latitude vegetation-rich tiles; bare/desert/ice excluded). Artificial tests in East Asia, West Africa (persistent cloud), South America (Amazon, severe cloud), 10% random noise injection. Transfer test: AVHRR GIMMS-3G (~8 km, semi-monthly), no fine-tuning.
- Core bottleneck addressed: no paired clean/degraded NDVI exists at the same location — fixed-ratio random masking used by prior SSL does not mimic real cloud structure (spatially coherent, temporally persistent).

## Method
- **SSL sample construction (key idea):** pair relatively clean patches with genuinely cloud-affected patches (identified by pixel-level quality flags, 30% cloud threshold); replace clean pixels with the cloud-contaminated counterpart's values and inject mild noise into remaining pixels → realistic degraded inputs, with the original clean patch as self-supervised target. Trained on globally distributed samples across biomes/climate zones.
- **Network:** quality flags as extra input modulating NDVI features pixel-wise; **global-local spatiotemporal module** = bidirectional Transformer along time (long-range temporal dependencies) + bidirectional ConvLSTM (fine-grained spatiotemporal dynamics, past+future context), fused by conv; **temporal-channel dual attention** reconstruction module (AvgPool+MaxPool MLP sigmoid gates on both time steps and channels).
- **Loss:** L = L_cons + L_prior. Data consistency with three masked terms: fidelity (M1: clean pixels shared input/output), reconstruction (M2: artificially clouded pixels), uncertainty (M3: noised pixels), weights λ1=0.6, λ2=2, λ3=0.1. Prior loss = 0.1·spatial gradient loss + 0.4·temporal smoothness (second-order difference penalty for phenological plausibility).
- Patches 32×32×23 (T=23 images/year). Baselines: Savitzky–Golay, HANTS, ST-Tensor (variational tensor completion). Metrics: CC, RMSE, MAE.

## Data & labels
- Entirely self-supervised from real MODIS observations; clean observations used only for evaluation. Public data (MOD13A2, GIMMS-3G).

## Results
- Artificial degraded reconstruction: GloSSR best in all three regions, e.g., overall MAE 0.0124 (East Asia), 0.0098 (West Africa), 0.0150 (South America) vs ST-Tensor 0.0208/0.0192/0.0228 and SG ~0.028. Cloud removal in West Africa: CC 0.874 vs ST-Tensor 0.489 — huge gain under persistent cloud.
- Ablations (West Africa): removing Transformer/temporal attention/bidirectional structure all degrade; reconstruction loss term is the most critical for cloud removal (CC 0.874→0.761); removing temporal smoothness *improves* quantitative metrics (denoising MAE 0.0176→0.0127) but produces jagged curves — kept at ε=0.4 as phenological realism trade-off.
- Runtime: 24-year 800×800×529 reconstruction in 374 s (32 CPU cores) or **126 s on GPU** vs ST-Tensor ~9,863–11,470 s — ~80× faster.
- Long-term trend analysis (Theil–Sen + Mann–Kendall, 2001–2024): reconstructed series change trend classifications to better match known surface processes (cloudy mountains → significant increase; urbanizing Red River delta → weaker trend).
- Cross-sensor transfer to AVHRR GIMMS-3G without fine-tuning: CC 0.759 (cloud removal) vs ST-Tensor 0.672, RMSE/MAE reduced ~25%.

## What transfers to our thesis
- **Directly applicable preprocessing layer for Landsat 16-day sugarcane series:** cloud gaps are the central data-quality problem in tropical/subtropical Landsat monitoring; GloSSR shows a self-supervised gap-filler trained on realistic (quality-flag-derived) cloud patterns outperforms SG/HANTS, especially for long persistent cloudy segments that interannual methods can't fix. Adapting the pairing scheme (clean patch ↔ cloudy patch from same/neighbor region) to Landsat NDVI+LST series is straightforward and label-free.
- The **three-term data-consistency loss (fidelity / reconstruction / uncertainty)** is a template for any masked-reconstruction pretext on our series: keep fidelity on unmasked pixels, reconstruct masked ones, and add a noise-robustness term — more realistic than naive random masking (their critique of fixed-ratio masking aligns with the MIMRS caveats in this batch).
- The **temporal smoothness prior trade-off** is a warning directly relevant to stress detection: over-smoothing removes the very anomalies (stress dips) we want to detect — they found removing smoothness *improves* RMSE but creates unrealistic jaggedness; for stress work we would reduce ε or drop it, and validate that phenological troughs (harvest, dormancy) are preserved (their multi-peak preservation results).
- Cross-sensor zero-shot transfer (MODIS→AVHRR, CC +0.09) supports the claim that SSL trained on vegetation-dynamics priors generalizes across sensors — encouraging for cross-year/cross-region transfer of our models.
- GPU 126 s for 24-year reconstruction shows operational feasibility for wall-to-wall sugarcane estate monitoring.

## Limitations / caveats
- MODIS 1 km / 23 images per year — coarser and denser than Landsat 30 m / ~23 scenes per year but with far more cloud; spatial texture at 30 m (field level) untested; sugarcane fields smaller than 1 km.
- Reconstruction reproduces "expected" vegetation dynamics — by design it will smooth genuine stress signals; using it upstream of stress detection requires care (their smoothness prior fights anomaly preservation).
- NDVI only, no LST/thermal; loss weights (λ, δ, ε) empirically set and acknowledged as dataset-specific.
- Quantitative evaluation relies on artificial degradation; real-scene evaluation is qualitative/visual plus trend plausibility.
- Preprint (no journal DOI in text).

## Key numbers to quote in lit review
- GloSSR overall MAE 0.0098–0.0150 across three continents vs 0.019–0.028 for ST-Tensor/SG/HANTS; West Africa persistent-cloud CC 0.874 vs 0.489 (ST-Tensor).
- ~80× faster than ST-Tensor (126 s GPU vs ~11,470 s for 24-year reconstruction).
- Zero-shot MODIS→AVHRR transfer: CC 0.759 vs 0.672 (second-best), RMSE/MAE −25%.
- Realistic cloud-structured degradation beats random fixed-ratio masking for SSL reconstruction — a design lesson for all masked time-series pretraining.
