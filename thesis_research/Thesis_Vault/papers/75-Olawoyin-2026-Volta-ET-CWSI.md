# 75 — Evapotranspiration & CWSI in the Volta Basin, 2000–2023 (Olawoyin et al., 2026)

**Full Citation:** Olawoyin, R., Amoah, G. O., & Danquah, J. A. (2026). Remote sensing-based assessment of evapotranspiration and crop water stress in the Volta Basin, 2000–2023. *H2Open Journal*, *9*(3), 100024. https://doi.org/10.1016/j.htopen.2026.100024
**DOI:** [10.1016/j.htopen.2026.100024](https://doi.org/10.1016/j.htopen.2026.100024) | Open access (CC BY) | IWA Publishing
**Status:** ✅ Full read (2026-10-20)
**Themes:** #CWSI #Thermal #Drought #Irrigation

---

## What It Does

Basin-scale spatiotemporal assessment of **land surface temperature (LST), evapotranspiration (ET) and the Crop Water Stress Index (CWSI)** over the **Volta River Basin (West Africa), 2000–2023**, using only MODIS, CHIRPS and ESA products. CWSI is derived with a **land-surface-temperature–NDVI triangular method**; the study couples the stress signal to land-use/land-cover change and to rainfall variability, and argues for restoration and climate-smart agriculture in the northern semi-arid zones.

## Key Methodology

- **Study area** (p. 2): Volta Basin, **> 400 000 km²**, spanning Ghana, Burkina Faso, Togo, Mali, Côte d'Ivoire and Benin; 5°30′N–14°30′N, 5°30′W–2°30′E; semi-arid Sahelian north → humid tropical south; rain-fed agriculture supports > 24 million people; principal crops rice, maize, millet, sorghum, yam.
- **Sensor stack — all public, all in Google Earth Engine** (p. 3):
  - **MOD16A2** (Collection 6) ET — 500 m, 8-day composites, Penman–Monteith; 8-day totals ÷ 8 → mm day⁻¹.
  - **MOD11A2** LST — 8-day, 1 km.
  - **MOD13Q1** NDVI — 16-day, 250 m.
  - **CHIRPS** rainfall — 0.05° (≈ 5 km) merged gauge + IR; chosen because it is useful in regions with sparse ground observations (p. 3).
  - **MCD12Q1** land cover — 500 m annual, IGBP classes; **ESA WorldCover 10 m** (Sentinel-1/2, 2020–2021) used to validate and refine classes.
- **Harmonisation** (p. 3): all datasets resampled to a common **500 m** grid — bilinear for ET/NDVI/LST/rainfall, nearest-neighbour for categorical land cover; cloud masking and QA in GEE; monthly/annual temporal aggregation; basin shapefile clip; statistics in the GEE JavaScript API, mapping in ArcGIS Pro v3.3, descriptive statistics in Excel.
- **CWSI construction** (p. 4): **LST–NDVI triangular method** (Carlson & Ripley 1997; Sandholt et al. 2002) — CWSI normalises the difference between observed LST and the minimum-temperature boundary relative to the full LST–NDVI temperature range; 0 = no stress, 1 = maximum stress. Pixels with **NDVI < 0.2 are excluded** to suppress bare-soil over-estimation of stress.
- **The in-situ-free anchor**: the method "relies solely on satellite observations and does not require extensive ground-based meteorological measurements" (p. 4). There is **no in-situ soil moisture, no ground CWSI, no station meteorology, no ML model and no uncertainty quantification** anywhere in the study.

## Key Findings

- **ET** 2000–2010: 0.03–15.7 mm day⁻¹ (north 0.03–4.64; south 9.25–15.29); 2011–2023: 0.04–15.72 mm day⁻¹ (north 0.04–5.08; mid/south 10.57–15.72); clear north–south regime split (north ≤ 5, south ≥ 10 mm day⁻¹) (p. 6).
- **NDVI**: −0.117 to 0.766 (2000–2010); −0.143 to 0.769 (2011–2023), with decline concentrated in the northern and central zones (pp. 4–5).
- **Rainfall trend** (p. 5): regression y = 4.0195x − 7093.8 with **R² = 0.1196** — the trend explains only ~12 % of interannual rainfall variance.
- **CWSI** (Table 3, p. 9): mean **0.975**, SD 0.018, min **0.955**, max **0.996**. Mapped classes 0.944–1.009 (p. 9): southwest/south 0.944–0.966 (lowest stress), mid-belt 0.966–0.975, northeast/central 0.975–0.983.
- **Correlations** (Table 2, p. 8): ET vs CWSI **r = −0.96**; ET vs NDVI **r = +0.96**; ET vs rainfall anomaly **r = +0.99**. Pearson with p-values (Table 4, p. 9): CWSI–NDVI **r = −0.94 (p = 0.004)**; rainfall anomaly–ET **r = +0.99 (p = 0.007)**; CWSI–ET **r = −0.96 (p = 0.040)**.
- ⚠️ **Internal inconsistency**: the Fig. 9 scatter panels instead report **CWSI–NDVI r = −0.99, CWSI–ET r = −0.98, CWSI–rainfall anomaly r = −0.97** (p. 10) — different from Table 4's −0.94 / −0.96 / +0.99, with the *sign* of the rainfall–CWSI relation flipping between table and figure. Cite one set only.
- ⚠️ **The authors' own caveat (p. 7)**: the correlation inputs are **four aggregated representative rows** (Table 1) derived from basin-aggregated annual values, and "should not be interpreted as the basis for rigorous statistical inference"; aggregation "produces a stronger statistical relationship than typically observed at local or short temporal scales" (p. 7). The headline r ≈ 0.99 ET–rainfall relation is therefore an averaging artefact, **not** a field-scale predictive relation.
- **Land cover 2000→2023** (Table 5, p. 12): wetlands **−74.76 %** (−795.00 km²), cropland **−51.50 %** (−4499.35 km²), built-up **+58.05 %** (+29 980.87 km²), woody savannah +263.14 %, grasslands +12.81 %, water bodies +6.00 %, forest vegetation −2.27 %, natural vegetation −5.72 %.
- **LST** (p. 12): north/northeast hottest in 2000 (22.38–46.70 °C, hotspots 40.79–46.70 °C); by 2023 the range is 23.66–42.9 °C with the mid-band 31.06–35.13 °C widening — southward spread of warmth.
- **Limitations (p. 13)**: 500 m MODIS cannot resolve smallholder heterogeneity; CHIRPS uncertainty in complex terrain; mixed-pixel and bare-soil effects bias CWSI in sparse-vegetation semi-arid areas; the authors recommend Sentinel-2/3 and crop-specific models at finer scale.
- ⚠️ *Minor correction to the intake note*: the NDVI range −0.143 to 0.769 is the **2011–2023** window; over 2000–2010 it was −0.117 to 0.766. Likewise, mean CWSI 0.975 with range 0.955–0.996 is the **basin-wide** descriptive statistic (Table 3, p. 9); the northern zone is the *high-CWSI region* of the map rather than a separately reported mean. The paper's own abstract conflates the two.

## Relevance to Thesis

**Medium** — a working template for an auxiliary water-stress covariate where ground data is sparse, but not a quantitative benchmark:
- ✅ **The ground-data-free covariate template**: a 24-year, entirely in-situ-free **LST–NDVI triangular CWSI** built from MODIS + CHIRPS + GEE, with NDVI < 0.2 masking and 500 m harmonisation. Directly reusable as an independent water-stress covariate or sanity validator for Khuzestan, where field CWSI labels are thin.
- ✅ Shows the **physiological coupling the thesis must break**: ET tracks rainfall (r ≈ 0.99) and NDVI (r ≈ 0.96) and is anti-correlated with CWSI (r ≈ −0.96) — water stress is not separable from rainfall and greenness by correlation alone, which is precisely the disentanglement problem the thesis tackles.
- ✅ Supplies **land-cover and warming covariates** (cropland −51.5 %, built-up +58.05 %, wetlands −74.76 %) and an arid-margin framing parallel to Khuzestan's water-scarcity context.
- ⚠️ MODIS 500 m — no field or intra-field scale; CWSI is nearly saturated basin-wide (mean 0.975, SD 0.018), so it discriminates poorly *within* the basin; the correlations rest on four aggregated rows, the authors say so, and Table 4 and Fig. 9 disagree — use them as qualitative context only.
- ❌ No salinity dimension despite irrigated basin agriculture; no predictive model, no validation against any field measurement, no uncertainty quantification — it cannot supply a quantitative benchmark for the thesis.

## Key Takeaway

Borrow the **LST–NDVI triangular CWSI as a ground-data-free auxiliary stress covariate template** (24-year MODIS + CHIRPS in GEE, NDVI < 0.2 masking, 500 m harmonisation, 0–1 normalisation) — but treat its headline correlations as descriptive context only: they come from four aggregated basin rows, the paper says so itself, and its own Table 4 and Fig. 9 disagree on the coefficients.

## Links

- Matrix row: #75
- Related: #73 (UAV CWSI/CEWT ML benchmarks), #78 (pre-2020 RS+ML critical review), #13 / #24 / #68 (CWSI physics cluster)

---

*Linked from: [[Literature-Matrix]]*
