# 35 — CWSI for Oak Water Stress from High-Resolution Thermal Imaging (Hornero et al., 2026)

**Full Citation:** Hornero, A., Quero, J.L., Zarco-Tejada, P.J., González-Dugo, V., Tomás Riera, F., Marcos, M.J., Hernandez-Clemente, R. (2026). Assessing CWSI as an indicator of water stress in oak trees based on high-resolution thermal images. *Remote Sensing of Environment* 344, 115549.  
**Status:** 🆕

---

## What It Does

Validates the Crop Water Stress Index (CWSI) as a water-stress indicator in holm oak (*Quercus ilex*) forests in Andalusia, Spain, asking whether an index built for irrigated crops still works in unmanaged, heterogeneous forest stands affected by decline. Combines multi-year ground measurements of stem water potential and stomatal conductance with continuous crown-temperature logging and aerial thermal campaigns.

## Key Methodology

- **CWSI formulation**: Idso–Jackson CWSI (Eq. 1) from canopy–air temperature difference (Tc−Ta), normalized between an empirical non-water-stressed baseline (NWSB, derived from filtered multi-day dT vs VPD data; sunny days 10–13 h, April–September, LOESS smoothing + outlier filtering) and an upper-limit (Tc−Ta)_UL; discusses why the simple empirical CWSI_ID is preferred for map analyses over the parameter-hungry energy-balance CWSI_SG
- **Continuous measurements**: infrared thermometers on 3 trees recording crown temperature every 10 min (2012–2014, Huelva site)
- **Aerial campaigns**: 16 flights between 11–14 h (9 in Huelva 2012–2017, 7 in Córdoba 2019–2024) with a FLIR SC655 thermal camera on a Cessna at ~350 m, sub-60 cm pixels; per-tree crown temperature via object-based classification/Mahalanobis distance
- **Ground truth**: stem water potential (pressure chamber; 2012, 2015, 2020, 2021, 2024) and stomatal conductance (LI-6400XT; Córdoba 2019–2024); crown-defoliation severity levels 1–4 (1228 trees inventoried in Huelva, 146 in Córdoba)
- **Two sites**: Pueblo de Guzmán (Huelva) and Sierra de Córdoba, contrasting dry/sub-humid Mediterranean climates

## Relevance to Thesis

**Medium** — CWSI-methodology support paper (background, not core):
- ✅ Confirms CWSI tracks physiological ground truth: correlated with stem water potential (R²=0.526, p<0.05) and stomatal conductance (R²=0.517, p<0.05) — the exact values behind matrix row #35's rounded 0.53/0.52
- ✅ Clearly explains CWSI baseline variants (empirical NWSB vs energy-balance formulations) and their sensitivity to VPD/humidity — useful physics background for your Landsat/Sentinel-2 thermal CWSI preprocessing (rows #24–25)
- ✅ Shows image-based CWSI discriminates decline-severity levels — a stress-grading analogue for sugarcane stress classes
- ⚠️ Forest (holm oak) context with unmanaged, heterogeneous canopies — far from irrigated sugarcane
- ⚠️ Correlations are moderate (R² ≈ 0.52–0.53), not the 0.7–0.9 typical of crops — tempers expectations for natural/complex canopies
- ❌ No salinity dimension, no stress-interaction analysis
- ❌ No ML/DL, no SSL, no XAI component

## Key Takeaway

CWSI, though formulated for irrigated crops, still correlates with stem water potential and stomatal conductance in unmanaged oak woodlands — but only moderately, and only with careful meteorological filtering and site-specific baselines. Useful background on the physics and limits of thermal CWSI; not a method transferable to sugarcane.

---

*Linked from: [[Literature-Matrix]]*
