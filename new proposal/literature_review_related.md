# Comprehensive Literature Review — Related Papers

**Topic:** Crop Stress Detection in Sugarcane Fields Using Satellite Image Time Series  
**Related papers reviewed:** 12 (Wen 2021, Wen 2022, Wen 2023, Angon 2022, Berger 2022, Motlagh 2026, Zoratipour 2025a, Zoratipour 2025b, Hajeb 2023, Maes 2012, STS-NET 2026, Höhl 2024)

---

## 1. Concurrent Drought–Salinity Stress: The Foundational Problem

### Wen et al. (2021) — Remote sensing challenges for food security with respect to salinity and drought threats
*Remote Sensing, 13*(1), 6.

The authors conducted a systematic review of satellite remote sensing for concurrent drought and salinity monitoring (2005–2020). Across 1,184 records, 115 publications, and 348 correlations, vegetation indices were found "insufficiently accurate (0.02 ≤ R² ≤ 0.80)". The joint remote sensing signal of drought and salinity "overlapped spectrally, thereby significantly limiting" the monitoring of them separately. Critically, the corpus contained **zero vegetation-index–salinity correlations**; all 171 VI–wavelength correlations were drought-only. Plant responses to both stresses were "identical at the early stage."

**Relevance:** This establishes the thesis problem statement: distinguishing concurrent water and salinity stress from satellite time series is not yet solved.

### Wen et al. (2022) — Monitoring the combined effects of drought and salinity stress on crops using remote sensing in the Netherlands
*Hydrology and Earth System Sciences, 26*, 4537–4559.

Five Sentinel-2-derived canopy traits (LAI, FAPAR, FVC, Cab, Cw) were monitored at 10 m via PROSAIL. Two-way ANOVA of stress-class × date yielded R² = 0.326–0.796; date effects dominated, drought dominated salinity ("salinity impacts may have been overstated"). Stresses were ground-defined via SPEI-3 and groundwater chloride proxies — no in-situ measurements.

**Relevance:** Closest empirical design to the proposed work; its statistical pipeline (ANOVA, proxy labels) is what the thesis's DL framework supersedes.

### Wen et al. (2023) — Evaluating crop-specific responses to salinity and drought stress from remote sensing
*International Journal of Applied Earth Observation and Geoinformation, 122*, 103438.

Upscaled to 8 crops over the US with a pairwise matched-control design (1-km cells, 30-km buffer, matched on crop/soil/climate/state). The combined stress exceeded individual impacts (exceptions: almond, sorghum). A testable hypothesis emerged: trait-response sequencing (LAI first → FVC/FAPAR → Cw/Cab last).

**Relevance:** The matched-control design is the statistical ancestor of contrastive self-supervised learning proposed in the thesis.

---

## 2. Physiological Basis of the Mixed Stress Class

### Angon et al. (2022) — How do plants respond to combined drought and salinity stress?
*Plants, 11*(21), 2884.

A systematic review of wheat, potato, and cotton-family evidence. Combined drought + salinity produced shoot dry weight reductions (−14% to −16% below both singles) and increased oxidative stress (H₂O₂ +52%). Critically, the review established that combined effects "cannot be predicted based on plant responses to individual stresses."

**Relevance:** Provides the physiological foundation for the four-class taxonomy (`Healthy | Water_Only | Salinity_Only | Mixed_Stress`) and the rationale for mixture/soft labels over hard global classes.

---

## 3. Multi-Sensor Stress Differentiation Gap

### Berger et al. (2022) — Multi-sensor spectral synergies for crop stress detection and monitoring in the optical domain
*Remote Sensing of Environment, 280*, 113198.

A 38-author review of 96 multi-domain studies. The flagship finding: "**no concept exists that uses multiple spectral domains in an integrated way … to differentiate between crop stress types**" (p. 3). Stress-type differentiation "will remain a challenge with purely RS-based approaches because distinct stressors often lead to similar stress reactions" (p. 14). Salinity comprised only 5% of studies; deep learning "is still missing" (p. 11).

**Relevance:** Validates the thesis design choice of integrating optical + thermal domains (Landsat) and frames the multi-sensor dimension as the key differentiator.

---

## 4. Site-Specific Validation at the Target Location

### Motlagh et al. (2026) — Leveraging remote sensing data and ML for assessing sugarcane yield variability
*Smart Agricultural Technology, 14*, 102391.

At the Amirkabir Agro-Industrial Unit (336 fields, ~25 ha each), an RF model predicted sugarcane yield using CWSI and soil salinity. Independent test R² = 0.821 (RMSE 7.56 t/ha); full-sample R² = 0.93. Feature importance: CWSI 40.6% > salinity 27.1%. Salinity × CWSI synergy appeared via partial dependence (salinity ≈ 3.4 dS/m + CWSI > 0.44 → yield collapse).

**Relevance:** The local baseline to beat; provides the ECe salinity protocol and the honest independent performance estimate.

### Zoratipour et al. (2025a) — Bias correction of satellite-based crop water stress index using ML methods
*Agricultural Water Management, 320*, 109862.

At Amir Kabir, ML bias correction of satellite CWSI (RF on LST/NDVI/LAI/emissivity/DEM) raised CWSI R² from 0.73 to 0.92 (+20.65%); rMBE −16% → −8%.

**Relevance:** Validates the ML bias-correction pipeline for the water-stress branch in the target region.

### Zoratipour et al. (2025b) — Sentinel-2 MSI vs Landsat thermal CWSI: sensor comparison
*Iranian Journal of Soil and Water Research, 56*(5), 1219–1238.

Landsat thermal CWSI (R² 0.78–0.92) slightly outperformed Sentinel-2 (R² 0.74–0.89); S2 recommended as fallback. Peaks at 24 July.

**Relevance:** Justifies Landsat 8/9 (TIRS) as the primary sensor in the thesis design, with Sentinel-2 as fallback.

### Hajeb et al. (2023) — Simultaneous retrieval of sugarcane biophysical traits from Sentinel-2 via BRANN
*International Journal of Applied Earth Observation and Geoinformation, 116*, 103168.

Retrieval of LAI, plant-water, chlorophyll, and nitrogen from Sentinel-2 at the same region (Amir Kabir zone). Plant-water proxy retrieved to 2.91% RRMSE; LAI RMSE 0.48 m²/m².

**Relevance:** Provides the ground-campaign template (ESU, destructive LAI, SPAD) and demonstrates that plant-water stress signals are recoverable in the target landscape.

---

## 5. Thermal Physics and Stress Differentiation

### Maes & Steppe (2012) — Estimating evapotranspiration and drought stress with ground-based thermal remote sensing in agriculture: A review
*Journal of Experimental Botany, 63*(12), 4671–4685.

Canonical CWSI physics: the thermal signal is a one-dimensional functional of stomatal conductance (eq. 41). Because T_pot and T_dry are defined by energy balance of maximally transpiring vs. non-transpiring canopies, all drivers that lower stomatal conductance (hydraulic, osmotic, cuticular) move the canopy temperature along the same axis — the thermal signal is **equifinal with respect to the driver**.

**Relevance:** The physics backbone: no CWSI threshold can separate water from salinity stress; a predictive temporal model with a second evidence channel is required.

---

## 6. Closest Competitor and Methodological Context

### STS-NET (Dalal et al., 2026) — Self-supervised 3D convolutional autoencoder for sugarcane water/nitrogen stress
arXiv:2607.18791.

Self-supervised 3D-CAE on sugarcane water and nitrogen stress using PlanetScope (~3 m satellite) time series (T = 32). Accuracy: 97.98% (water), 85.08% (N), 83.47% (combined). Combined task = 9-class water×nitrogen permutation.

**Relevance:** Closest competitor for sugarcane stress detection via self-supervision; lacks salinity, Mamba, XAI, multi-year data, and moderate-resolution satellite input — motivating the thesis design.

### Höhl et al. (2024) — Opening the black-box: A systematic review on explainable AI in remote sensing
arXiv:2402.13791.

207 studies (2017–2023); SHAP most-used (94 papers); >90% evaluate explanations only anecdotally; 15/207 use functional metrics. Temporal dependencies not explicitly considered by most methods; real-world RS lacks controlled XAI ground truth.

**Relevance:** Establishes the XAI gap that motivates the thesis's temporal XAI contribution.

---

## 7. Synthesis

The 12 related papers form a coherent evidence chain:

1. **Problem:** Wen et al. trilogy establishes concurrent stress monitoring as unsolved; Berger et al. establishes stress-type differentiation as lacking.
2. **Physiology:** Angon et al. establishes the Mixed stress class; Maes & Steppe establishes thermal equifinality.
3. **Site:** Motlagh et al. + Zoratipour et al. establish validated local baselines and sensor decisions at Amir Kabir.
4. **Methods:** STS-NET demonstrates self-supervised SITS stress detection; Höhl et al. frames the XAI gap.
5. **Proposal:** The proposed CNN-Mamba + SSL + temporal-XAI framework directly addresses the gaps identified.

The literature converges on the need for: (a) predictive, per-field models over proxy/statistical approaches; (b) multi-sensor integration; (c) multi-year time series; (d) temporal explainability.
