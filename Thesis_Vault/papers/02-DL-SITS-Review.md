# 02 — Deep Learning for SITS Review (Miller et al., 2024)

**Full Citation:** Miller, L., Pelletier, C., & Webb, G.I. (2024). Deep Learning for Satellite Image Time Series Analysis: A Review. *arXiv:2404.03936*.  
**Status:** ✅ Read  
**Themes:** #Review/SITS #Preprocessing #Multi-modal

---

## What It Does

Comprehensive survey of DL methods for SITS analysis across CNNs, RNNs, Transformers, and emerging SSMs.

## Key Coverage

| Topic | What They Found |
|-------|-----------------|
| **Cloud masking** | Dominant preprocessing challenge for long SITS |
| **Gap-filling** | Cubic spline vs. Gaussian process tradeoffs |
| **Temporal resolution** | Landsat 16-day vs. S2 5-day implications |
| **Multi-modal fusion** | Optical + SAR + thermal is the frontier |
| **SSMs/Mamba** | Mentioned as "emerging" with linear complexity advantage |

## Critical Gap Identified

> No existing review covers **stress-specific** SITS modeling — most focus on land cover / crop type classification.

This confirms our thesis fills a genuine gap.

## Preprocessing Implications

| Challenge | Our Solution |
|-----------|--------------|
| Cloud masking | CFMASK via GEE (following Motlagh et al.) |
| Temporal resampling | Cubic spline to 16-day composites |
| Gap-filling | STRFM fusion (Landsat + MODIS) |
| Multi-modal | Raw bands + LST + derived indices |

---

*Linked from: [[Literature-Matrix]]*
