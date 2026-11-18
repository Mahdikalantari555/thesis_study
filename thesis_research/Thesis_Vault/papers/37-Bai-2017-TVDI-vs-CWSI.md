# 37 — TVDI vs CWSI for Drought Monitoring (Bai et al., 2017)

**Full Citation:** Bai, J., Yu, Y., Di, L. (2017). Comparison between TVDI and CWSI for drought monitoring in the Guanzhong Plain, China. *Journal of Integrative Agriculture* 16(2), 389–397.  
**Status:** 🆕

---

## What It Does

Head-to-head comparison of two remote-sensing drought indices — the Temperature Vegetation Dryness Index (TVDI, NDVI–LST triangle) and the Crop Water Stress Index (CWSI, from MOD16 ET/PET) — for agricultural drought monitoring in the Guanzhong Plain, China, during the 2003 drought year, validated against the standardized precipitation index (SPI) and surface soil moisture.

## Key Methodology

- **TVDI**: parameterized from monthly MODIS NDVI (MOD13A3) and LST (MOD11C3) at 1000 m using the Sandholt dry/wet-edge NDVI–LST triangle
- **CWSI**: CWSI = 1 − ET/PET (Eq. 2), with monthly ET/PET from the MOD16 product (MOD16A2, Penman–Monteith based) — i.e., CWSI derived from standard RS products, not in-situ canopy temperature
- **Validation data**: monthly SPI at 21 meteorological sites (precipitation 1963–2012) and soil moisture at 14 sites (10 and 20 cm depths); TVDI/CWSI rescaled as 3 km × 3 km averages around each site; linear regression analysis
- **Results visible in first pages**: CWSI and TVDI showed similar spatial drought patterns with differences in drought-intensity detail; CWSI–TVDI R² = 0.4422 (n=420, P<0.001); CWSI–SPI correlation coefficient −0.548 (P<0.001) — abstract states both SPI and soil moisture correlate better with CWSI than with TVDI, supporting CWSI as the more reliable indicator (TVDI–SPI/SM correlation values not in first pages — per matrix row #37, verify in full read)

## Relevance to Thesis

**Medium** — CWSI-methodology support paper (background, not core):
- ✅ Empirical argument for choosing CWSI over NDVI–LST triangle indices (TVDI) — justifies the thesis's CWSI-centric water-stress metric
- ✅ Shows CWSI computed purely from standard products (MODIS ET/PET) — precedent for satellite-only CWSI without ground canopy temperature, relevant to your S2/Landsat pipeline
- ✅ Validation design against SPI + in-situ soil moisture at meteorological stations — an alternative/complementary ground-truthing strategy for Khuzestan
- ⚠️ 2003-era MODIS at ~1 km, regional plain scale — far from Sentinel-2 field-scale sugarcane
- ⚠️ Drought (precipitation-deficit) framing; no irrigation management or salinity context
- ❌ No salinity dimension, no stress-interaction analysis
- ❌ No ML/DL, no SSL, no XAI

## Key Takeaway

Where TVDI and CWSI agree on spatial drought patterns, CWSI correlates significantly better with SPI and surface soil moisture, making it the more reliable index for agricultural drought. This is background justification for the thesis's choice of CWSI as its primary water-stress metric, not a methodological component.

---

*Linked from: [[Literature-Matrix]]*
