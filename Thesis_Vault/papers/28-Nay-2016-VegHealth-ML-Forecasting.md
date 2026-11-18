# 12 — ML for Forecasting Remotely Sensed Vegetation Health (Nay et al., 2016)

**Full Citation:** Nay, J.J., Burchfield, E., & Gilligan, J. (2016). A Machine Learning Approach to Forecasting Remotely Sensed Vegetation Health. *arXiv:1602.06335*.  
**PDF:** https://arxiv.org/pdf/1602.06335v4  
**Status:** Read  

## Key Contributions

- Open-source tool for **short-term vegetation health forecasting** at 250m resolution
- Uses MODIS data (global coverage) with Gradient Boosted Machine (GBM) models
- Compares four predictor sets: Spectral data, Level-3 products, Land Use+Time, Lagged EVI
- Tests on Sri Lanka (tropical, cloudy) and California (Mediterranean, clear)

## Methodology

```
Input: MODIS bands (B1-B7), LST, NDVI, EVI, LAI, GPP, NPP (lagged)
Model: Gradient Boosted Machine (h2o library)
Output: 16-day ahead EVI forecast
```

## Results

- GBM with spectral data outperforms all baselines
- In California: ~30-40% MSE reduction vs. lagged EVI baseline
- In Sri Lanka: ~15-25% MSE reduction (clouds reduce predictability)
- Raw spectral bands more predictive than derived Level-3 products

## Relevance to Thesis

**Low** — Classical ML baseline reference:
- ✅ Demonstrates value of raw spectral data over derived indices
- ✅ Time-series forecasting approach (lagged predictors)
- ❌ 250m resolution (too coarse for farm-level)
- ❌ MODIS (16-day revisit, not Landsat)
- ❌ Single-crop vegetation health, not stress type discrimination
- ❌ 2016 paper — outdated architecture compared to modern DL

## Key Insight

The finding that **raw spectral bands outperform derived indices** supports your approach of using Landsat raw bands (not just VIs) as model input. However, your CNN-Mamba architecture will automatically learn optimal band combinations, making explicit VI computation less critical.
