# 04 — XAI-Guided Enhancement of Vegetation Indices (Najjar et al., 2024)

**Full Citation:** Najjar, H., Mena, F., Nuske, M., & Dengel, A. (2024). XAI-Guided Enhancement of Vegetation Indices for Crop Mapping. *IGARSS 2024*, arXiv:2407.08298.  
**PDF:** https://arxiv.org/pdf/2407.08298v1  
**Status:** Read  

## Key Contributions

- Uses **Shapley Value Sampling (SVS)** for spectral attribution (feature importance per band)
- Trains GRU on Sentinel-2 time series (10 bands, 228 timesteps) for crop classification
- Identifies most important bands → designs/enhances vegetation indices accordingly
- Tests single-VI and two-VI combinations as model inputs

## Methodology

1. Train baseline GRU on all 10 S2 bands → achieve 67% OA
2. Apply SVS to get band attributions → SWIR1 and RE1 most important (~20% each)
3. Design VIs using important bands: NDRE (NIR-RE1), NDMI (NIR-SWIR1), n-NDVI (nNIR-RED)
4. Retrain GRU on VI inputs → compare performance

## Key Results

| Model | OA (%) | F1 | Best Crop |
|-------|--------|-----|-----------|
| Baseline (all 10 bands) | 67 | 67 | Rice: 84%, Sorghum: 86% |
| NDMI (single VI) | 67 | 67 | Yam: best |
| NDRE + NDMI2 (two VIs) | **70** | **69** | Outperforms baseline |

## Relevance to Thesis

**Medium-High** — Bridges XAI and practical VI selection:
- ✅ SHAP-based interpretability applied to RS time series
- ✅ Shows how XAI can guide feature engineering (VI selection)
- ✅ Two-VI combination outperforms full-band baseline
- ❌ Crop classification, not stress detection
- ❌ Static (per-pixel) interpretation, not temporal
- ❌ No Mamba or deep temporal architecture

## Key Insight for Thesis

The **XAI → VI design → retrain** loop is a powerful methodology: after training your CNN-Mamba model, you can use SHAP/attribution to identify which temporal positions and spectral bands drive stress predictions, then design custom stress indices for your specific task.
