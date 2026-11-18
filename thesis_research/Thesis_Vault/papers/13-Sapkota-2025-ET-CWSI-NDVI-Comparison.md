# 13 — ET/CWSI/NDVI Comparison for Irrigation Scheduling (Sapkota et al., 2025)

**Full Citation:** Sapkota, et al. (2025). Comparison of evapotranspiration, CWSI, and NDVI for irrigation scheduling. *Agronomy*.  
**Status:** 🆕

---

## What It Does

Multi-method comparison for irrigation scheduling: compares ET-based, CWSI-based, and NDVI-based approaches to determine optimal irrigation timing and amounts.

## Key Methodology

- **ET approach**: Penalman-Monteith based reference evapotranspiration (ET₀) with crop coefficients
- **CWSI approach**: Crop Water Stress Index using canopy temperature differential
- **NDVI approach**: Vegetation index thresholds for stress detection

## Relevance to Thesis

**Medium-High** — Validates multi-method CWSI approach:
- ✅ Directly compares CWSI against ET and NDVI methods
- ✅ Supports CWSI as primary metric with ground-truth validation
- ✅ Addresses uncertainty in single-metric approaches
- ⚠️ Crop-specific (needs verification for sugarcane)
- ❌ No temporal XAI component
- ❌ No salinity dimension
- ❌ No deep learning architecture

## Key Takeaway

Using multiple complementary metrics (ET + CWSI + NDVI) improves irrigation scheduling reliability compared to any single method. This supports your thesis goal of multi-modal stress detection.

---

*Linked from: [[Literature-Matrix]]*
