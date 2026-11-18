# 23 — Harnessing AI and Remote Sensing for Precision Sugarcane Farming: Review (Vinayaka et al., 2025)

**Full Citation:** Vinayaka, P.P.R.C., Avinash, G., Amaresh, et al. (2025). Harnessing AI and Remote sensing for precision sugarcane farming: tackling water stress, salinity, and nitrogen challenges. *Frontiers in Agronomy*, 7, 1681294.  
**DOI:** [10.3389/fagro.2025.1681294](https://doi.org/10.3389/fagro.2025.1681294)  
**Status:** ✅ Read

---

## What It Covers

Comprehensive review of AI + RS applications for three critical stressors in sugarcane:
- **Water stress** — CWSI, NDVI, thermal imaging, SEBAL, UAV-based monitoring
- **Salinity stress** — Hyperspectral indices (SWSI, NDWI), SVM classifiers, Hyperion/Landsat comparisons
- **Nitrogen stress** — Red-edge indices (NDRE, S2REP), RF/SVR for LNC estimation

## Key Vegetation Indices Identified

| Index | Purpose | Relevant Bands |
|-------|---------|---------------|
| NDVI | General vegetation health | NIR, Red |
| NDWI | Water content | NIR, SWIR |
| NDMI | Moisture stress | NIR, SWIR |
| NDRE | Chlorophyll/stress sensitivity | NIR, Red-edge |
| PRI | Photosynthetic efficiency | 531nm, 570nm |
| S2REP | Sentinel-2 red-edge position | B5, B6, B7 |
| SWSI-1, SWSI-3 | Salinity + water stress | Various combinations |
| MSAVI, OSAVI | Soil-adjusted NDVI variants | NIR, Red |

## Critical Findings

1. **CWSI threshold**: Water stress detected at CWSI > 0.4–0.5 range (consistent with Khuzestan studies)
2. **Salinity mapping**: SVM + Hyperion achieved 78.7% accuracy; Landsat ETM+ better for categorical mapping (84.84%)
3. **Nitrogen estimation**: RF outperformed SVR; top indices: BNi, GNDVI, NDRE, RI-1db (R² > 0.65)
4. **Deep learning advances**: DenseResUNet (mIoU 61.91%), Inception-ResNet-v2 outperformed human assessments

## Relevance to Thesis

**Critical** — Most relevant sugarcane review for band/index selection:
- ✅ Covers water + salinity + nitrogen simultaneously (matches thesis triple-stress focus)
- ✅ Provides comprehensive VI table for spectral band selection
- ✅ Discusses thermal (LST/CWSI) + optical (NDVI/NDRE) fusion approaches
- ✅ Identifies gap: no study differentiates water stress vs. salinity stress using satellite data
- ❌ No temporal XAI component
- ❌ No deep temporal architecture (CNN-Mamba) discussion
- ❌ Focuses on conventional ML, not SSL or self-supervised approaches

## Key Quote

> "Currently, only one study has attempted to classify multiple conditions simultaneously" — highlighting the gap your thesis addresses.

---

*Linked from: [[Literature-Matrix]]*
