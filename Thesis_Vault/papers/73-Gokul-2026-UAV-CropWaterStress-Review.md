# 73 — UAV-Based Crop Water Stress Monitoring: Sensor × ML Review (Gokul et al., 2026)

**Full Citation:** Gokul, S., Manivannan, V., Thirukumaran, K., Boominathan, P., Jagadeeswaran, R., Raja, R., Prabukumar, G., Asritha, M., & Surya, K. (2026). Recent trends in crop water stress monitoring using remote sensing technologies: A review. *Plant Science Today*, *13*(sp2), 1–18. https://doi.org/10.14719/pst.13057
**DOI:** [10.14719/pst.13057](https://doi.org/10.14719/pst.13057) | Open access (ISSN 2348-1900) | Received 04 Dec 2025; accepted 10 Apr 2026; online 04 Jun 2026
**Status:** ✅ Full read (2026-10-20)
**Themes:** #CWSI #Review #Thermal #Benchmark

---

## What It Does

Narrative review of **crop water stress (CWS)** detection with remote sensing, centred on UAV platforms but spanning satellite RS and crop-model coupling. It organises the literature as **sensor class (RGB / MSP / HSP / thermal) × physiological indicator × ML/DL algorithm**, tabulates ML benchmarks for maize and cotton, and closes with a gap analysis on standardisation, cross-regional validation, and decision-support-system (DSS) integration (p. 1–2).

## Corpus & Scope

- **Narrative review, not systematic**: no PRISMA protocol, no reported corpus size (n), no search string — cite as a structured narrative synthesis, not a systematic count. 18 pp.; six tables (soil-based, plant-based, VI formulae, sensor types, DL models, cost/scalability).
- Coverage: UAV RGB / multispectral (MSP) / hyperspectral (HSP) / thermal; satellite thermal (CWSI, VWC); ET-based and canopy-temperature indicators; classical ML (SVM, RF, XGBoost, ANN) and DL (CNN, LSTM/BiLSTM, VGG16, GoogLeNet).

## Key Methodology

- **Sensors** (p. 7–8): thermal 3–14 µm (commonly 3–5 or 7–14 µm); MSP = RGB + NIR/VNIR; HSP 400–2500 nm; RGB is cheap but needs controlled lighting and fixed leaf orientation.
- **Physics**: CWSI from canopy temperature with wet/dry reference surfaces (Eq. 1), range 0–1 (0 = no stress, 1 = severe); the **hybrid CWSI** pairs an empirical upper limit with a theoretical lower limit to cut parameter demands (p. 4).
- **VI families** (p. 3, Table 3): structure (NDVI, RDVI, SAVI), chlorophyll (TCARI, TCARI/OSAVI), xanthophyll/PRI, moisture (WI, SRWI, NDWI).
- **Processing chain** (p. 10): radiometric → atmospheric → geometric correction → orthomosaic (Pix4Dmapper) → GCP georeferencing → segmentation → feature extraction (Tc, NDVI, NDRE in ArcGIS 10.4.1 / QGIS 3.12.3) → R²/RMSE statistics.
- **Crop-model coupling** (p. 10): AquaCrop, APSIM, DSSAT, CROPSYST, DAISY; UAV-derived LAI/canopy cover can drive the crop models, and remote-sensing-driven DSS then drive irrigation scheduling.

## Key Findings

- **Maize (RF benchmark)** — UAV **MSP + thermal indices + LAI** with **Random Forest: R² > 0.575, RMSE < 0.073**, stage-specific: crop water content resolved at the **9th-leaf** and **milking** stages, normalised **stomatal conductance at tasseling and silking** (p. 1, p. 9, p. 13).
- **Cotton (XGBoost benchmark)** — UAV **VIs + texture features (TFs)**: **XGBoost VIs + TFs → CEWT R² = 0.75**; **XGBoost VIs + TFs + TIs → CWSI R² = 0.90** (p. 9, p. 13).
- **CEWT = canopy equivalent water thickness** (p. 1, p. 9). ⚠️ *Discrepancy:* CEWT is sometimes glossed as a "crop evapotranspiration water stress" index — the PDF defines it as **canopy equivalent water thickness**; use the PDF wording.
- **MSP beats thermal as maize input** (p. 9): MSP R² = 0.97 vs thermal R² = 0.71 (nRMSE 10 % vs 25 %); RF best on MS (R² = 0.97), elastic net next (R² = 0.88); the SWC–thermal relation is **exponential**, so GLM failed (> 40 % nRMSE) while RF handled it (24.4 % nRMSE).
- **VI↔CWSI correlations are stage-dependent** (p. 3): TCARI/RDVI and TCARI/SAVI gave R² = 0.47 and 0.50 at reproductive and final stages, rising to 0.81 and 0.80 at late reproductive and final stages.
- **Satellite thermal already reaches sugarcane** (p. 8, Table 4): CWSI and VWC from satellite thermal, **strong correlation with VWC R² = 0.42–0.78**, but coarse resolution and low revisit frequency.
- **UAV thermal vs ground sensors** (p. 7): R² = 0.94 against in-field IRT sensors; maize Tc best at mid-vegetative stage (RMSE = 0.59 °C, R² = 0.81, RMSE = 2.9 %); simplified CWSI (CWSI_si) beat empirical CWSI for gs (R² = 0.660) and tr (R² = 0.592) in cotton.
- **DL status (p. 9–10, Table 5)** is classification-dominated, not regression: AlexNet 98.8 % (5-class maize drought categorisation), ResNet50/120 98 %, VGG16 98 % treatment / 85 % severity, GoogLeNet 98.3 % maize / 97.5 % okra / 94.1 % soybean (p. 10 quotes 98.30 / 97.50 / 94.16 %), BiLSTM 80 % on 3-class maize/jowar. **No representation learning on time series, no self-supervision.**
- **Gaps** (p. 1, p. 13): standardising data acquisition, suppressing environmental variability, **integrating UAV data into reliable irrigation DSS**, **cross-regional validation**, real-time monitoring, and compatible systems linking UAV imagery with ground sensors and crop models. UAV limits: short flight time, lightweight uncooled TIR → unstable Tc and low mosaic precision, tie-point/geolocation errors, heavy pre-processing (p. 12). Context: agriculture uses 80–90 % of global freshwater; a change in irrigation frequency alone can cut maize yield by 10–27 % (p. 1).

## Relevance to Thesis

**Medium** — UAV-scale proximal validation anchors plus a classical-ML baseline comparator, one transfer step away from the thesis' satellite design:
- ✅ Supplies the **benchmark scale** the thesis must meet or beat: RF R² > 0.575 (maize, stage-specific) and XGBoost CWSI R² = 0.90 (cotton) as proximal (UAV) ceilings.
- ✅ Independently confirms **stage-dependence** of water-stress signals (9th-leaf/milking vs tasseling/silking) — direct support for the temporal-encoder motivation.
- ✅ Its **DSS-integration gap** (UAV imagery → ground sensors → crop models → irrigation decision) is the thesis' own gap statement, independently sourced.
- ⚠️ UAV-only and single-stress (no salinity); all ML is classical on engineered indices, so it cannot support a foundation-model/SSL claim.
- ❌ No multi-year satellite archive, no concurrent water-vs-salinity disentanglement, no XAI or uncertainty layer.

## Key Takeaway

The most useful artifact is the **benchmark pair** (RF R² > 0.575 maize; XGBoost CWSI R² = 0.90 cotton) plus the review's own admission that UAV CWS is not yet wired into irrigation DSS — the thesis can position satellite-scale, multi-year, salinity-aware modelling as the missing step *above* this UAV layer. Caveat: the review is narrative (no n, no protocol), so its gap statements are qualitative, not systematic.

## Links

- Matrix row: #73
- Related: #75 (satellite LST–NDVI CWSI over 24 years), #78 (pre-2020 RS+ML critical review), #74 (2020–2025 taxonomy: LSTM/Transformer now the accepted time-series family), #24 / #39 (CWSI physics cluster)

---

*Linked from: [[Literature-Matrix]]*
