# 36 — UAV CWSI in Almond: Proximal Radiometry vs UAV Thermal vs STSEB (Sánchez-Virosta et al., 2025)

**Full Citation:** Sánchez-Virosta, Á., Sánchez, J.M., Montoya, F., Gómez-Candón, D., González-Piqueras, J., Molina-Medina, A.J., López-Urrea, R. (2025). Assessment of different remote sensing techniques to estimate the CWSI of almond trees using canopy temperature. *International Journal of Applied Earth Observation and Geoinformation* 142, 104737.  
**Status:** 🆕

---

## What It Does

Compares three CWSI estimation routes in commercial almond orchards (Albacete, SE Spain) against stem water potential (SWP): (i) proximal high-precision thermal radiometry (CWSI_CIMEL), (ii) UAV thermal flights for canopy temperature (CWSI_UAV), and (iii) a simplified two-source surface energy balance run from combined UAV multispectral + thermal data (CWSI_STSEB), to quantify how platform and method choice affect CWSI accuracy.

## Key Methodology

- **Three CWSI variants**: CWSI_CIMEL (CIMEL CE 312-2 radiometer, 3 channels 10.2–11.0 µm, 4 measurements at two orientations); CWSI_UAV (DJI M600 with FLIR Tau2 640×512 thermal, ~90 m altitude, 6 cm GSD); CWSI_STSEB (CWSI = 1 − T/Tp with Kcb–NDVI relation Kcb = 2.069·NDVI − 0.32, R² = 0.78)
- **CWSI physics**: Idso–Jackson formulation (Eq. 1) with non-water-stressed baseline from in-situ IRTs (45°-tilted and downward-looking, 1.5 m above canopy) under optimal watered conditions; upper limit from high-VPD sunny midday conditions
- **Design**: two orchards (Hellín — young, well-watered; Las Tiesas — 0.13 ha, three irrigation treatments ND/MD/SD, randomized block), three seasons 2019–2021; 6 UAV flights; 9–12 SWP pressure-chamber dates per season (284 trees in Hellín, 1635 in Las Tiesas)
- **Radiometric rigor**: blackbody calibration of all sensors, self-derived soil/canopy emissivity, atmospheric correction of radiometer/IRT readings — explicitly identified as critical to CWSI quality
- **Results (abstract)**: pooled same-date R² with SWP = 0.86 (CIMEL), 0.68 (UAV), 0.70 (STSEB); all three showed similar CWSI trends across dates and treatments

## Relevance to Thesis

**Medium-High** — UAV thermal validation methodology (background, not core):
- ✅ Template for a validation design: one ground truth (SWP), three estimation routes, pooled same-date correlation analysis — directly transferable to your satellite-CWSI vs ground-truth comparison in Khuzestan
- ✅ Quantifies the accuracy cost of moving up the platform chain (radiometry R²=0.86 → UAV thermal 0.68 → energy-balance 0.70); complements row #25's Landsat-vs-Sentinel-2 sensor comparison
- ✅ STSEB route shows NDVI-based Kcb feeding an ET-based CWSI — precedent for combining S2 vegetation indices with thermal data in your multi-source pipeline
- ✅ Stresses sensor calibration and emissivity/radiometric correction as the dominant error sources — practical guidance for your CWSI preprocessing
- ⚠️ Orchard crop (almond) at single-tree level; sugarcane is a dense row grass crop
- ⚠️ Proximal/UAV platforms, not satellite time series
- ❌ No salinity dimension; no ML/DL, no SSL, no XAI

## Key Takeaway

All three CWSI routes tracked SWP with similar trends, but accuracy degrades from precision radiometry (R²=0.86) to UAV thermal (0.68) and STSEB (0.70), with calibration and radiometric processing dominating the error budget. Good validation-design and accuracy-expectation background for the thesis's CWSI work — not a core method itself.

---

*Linked from: [[Literature-Matrix]]*
