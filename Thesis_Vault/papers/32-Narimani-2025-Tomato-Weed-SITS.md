# 17 — Branched Broomrape Detection in Tomato Using SITS (Narimani et al., 2025)

**Full Citation:** Narimani, M., Pourreza, A., Moghimi, A., Farajpoor, P., Jafarbiglu, H., & Mesgaran, M. (2025). Branched Broomrape Detection in Tomato Farms Using Satellite Imagery and Time-Series Analysis. *SPIE Defense + Commercial Sensing 2025*, arXiv:2509.10804.  
**PDF:** https://arxiv.org/pdf/2509.10804v1  
**Status:** Read  

## Key Contributions

- End-to-end pipeline for detecting parasitic weed infestation using Sentinel-2 SITS
- **Phenological alignment** using Growing Degree Days (GDD) and Canopy Chlorophyll Content (CCC)
- **LSTM classifier** on 18,874 pixels × 48 GDD time steps
- Permutation feature importance for interpretability

## Methodology

```
Input: 12 Sentinel-2 bands + 20 VIs + 5 plant traits (LAI, Cab, CCC, FAPAR, FCOVER)
→ Phenological alignment via CCC trends + GDD
→ Vegetation segmentation via PCA + K-means
→ LSTM (2 layers: 64→32 units) on 48 GDD time steps
→ Binary classification (infected vs. healthy)
```

## Results

| Metric | Value |
|--------|-------|
| Training Accuracy | 88% |
| Test Accuracy | 87% |
| Precision | 0.86 |
| Recall | 0.92 |
| F1 Score | 0.89 |

**Most Important Features** (permutation importance):
1. NDMI (Normalized Difference Moisture Index)
2. CCC (Canopy Chlorophyll Content)
3. FAPAR (Fraction of Absorbed PAR)
4. CHL-RED-EDGE

## Relevance to Thesis

**Low-Medium** — Temporal stress detection methodology reference:
- ✅ Uses LSTM for temporal stress detection (alternative to Mamba)
- ✅ Phenological alignment approach (GDD + CCC) directly applicable to sugarcane
- ✅ Permutation feature importance for XAI (simple but effective)
- ✅ Multi-feature time series (bands + VIs + traits)
- ❌ Binary classification (infected/healthy), not multi-class stress
- ❌ Parasitic weed stress, not abiotic water-salinity stress
- ❌ Sentinel-2 (5-day revisit), not Landsat (16-day)

## Key Insight for Thesis

The **phenological alignment** methodology (using CCC to identify transplanting/peak/harvest stages, then aligning via GDD) is directly transferable to your sugarcane study. Sugarcane's long growth cycle (12-18 months) makes temporal alignment even more critical than for annual crops.
