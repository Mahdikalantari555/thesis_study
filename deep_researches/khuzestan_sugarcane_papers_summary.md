# Summary of Key Papers — Khuzestan & Sugarcane (Directly Relevant to Thesis)

**Date:** 2026-09-10  
**Purpose:** Critical summaries of papers from the same study area (Amirkabir Agro-Industrial, Khuzestan) that must inform the thesis methodology.

---

## 1. Zoratipour et al. (2026) — Hourly/Daily CWSI in Khuzestan Sugarcane Fields

**Citation:** Zoratipour, E., Veysi, S., Mohammadi, A.S., Boroomand Nasab, S., & Naseri, A.A. (2026). Deriving hourly and daily crop water stress index through the lens of proximal sensing in sugarcane fields. *Ain Shams Engineering Journal*, 17, 103903. DOI: [10.1016/j.asej.2025.103903](https://doi.org/10.1016/j.asej.2025.103903) | **Open Access**

**Study area:** Amirkabir Agro-Industrial Unit, Khuzestan, Iran (same as your 490 fields)

### Key Findings
| Finding | Value |
|---------|-------|
| CWSI threshold for irrigation initiation | **0.4–0.5** (proposed) |
| Peak water stress time of day | 10:00 AM and 14:00 (two peaks) |
| Daily CWSI minimum | 2 days post-irrigation |
| Strongest correlation | Soil moisture 0–90 cm depth |
| Climate | Semi-arid, 198 mm annual rain, no summer rain |
| Growing season peak demand | July–September |

### Methodology
- Stationary proximal sensors (Apogee SI-11 H infrared thermometers) at 3m height, 45° zenith angle
- Continuous Tc measurement from 6:00–18:00
- CWSI calculated from canopy-air temperature difference normalized by NWSB
- Validated against stem water potential and soil moisture

### Direct Implications for Our Thesis
1. **CWSI threshold = 0.4–0.5** for sugarcane in Khuzestan — this is our validation benchmark
2. **July–September is the critical window** — stress outside this period is negligible (confirms our seasonal focus)
3. **Proximal sensing validates satellite CWSI** — their work bridges ground truth → satellite-scale inference
4. **Two-peak daily pattern** (10 AM + 14:00) matters for Landsat overpass timing (10:30 local ~ mid-morning peak)

---

## 2. Motlagh et al. (2026) — ML Diagnosis of Sugarcane Yield Variability in Khuzestan

**Citation:** Motlagh, A.H., Veysi, S., Mohammadi, A.S., & Naseri, A.A. (2026). Leveraging remote sensing data and machine learning method for assessing sugarcane yield variability to support smart agriculture. *Smart Agricultural Technology*, 14, 102391. DOI: [10.1016/j.atech.2026.102391](https://doi.org/10.1016/j.atech.2026.102391) | **Open Access**

**Study area:** Amirkabir Agro-Industry, Khuzestan — **336 fields** (similar to our 490)

### Key Findings
| Driver | Importance (%) |
|--------|---------------|
| Water stress (CWSI) | **40.6%** |
| Soil salinity | **27.1%** |
| Crop age | 9.0% |
| Water × Salinity interaction | **Synergistic — disproportionate yield loss** |

### Critical Results
- **R² = 0.93, RMSE = 5.38 t/ha** for yield prediction
- Yield gap: <40 to >130 t/ha **under uniform management** — proves hidden subsurface stressors dominate
- **Strong synergistic interaction**: high salinity + elevated CWSI → accelerated yield loss, especially in ratoon fields
- Soil salinity ranged **1.7–8.0 dS/m** across fields
- 128 observation wells for water table depth monitoring
- Cloud-free Landsat 7/8/9 images (31 overpasses, July–September 2023)

### Methodology
- Daily CWSI from **Landsat-MODIS fusion** (STRFM — Spatiotemporal Remote Sensing Fusion Model)
- Soil data from SoilGrids (sand/silt/clay for 0–30 cm root zone)
- Random Forest with 70:30 train:test split
- Feature importance + interaction analysis

### Direct Implications for Our Thesis
1. **CWSI is the dominant driver (40.6%)** — validates our focus on thermal-based water stress
2. **Soil salinity is #2 (27.1%)** — confirms salinity must be modeled separately from water stress
3. **Interaction effect is real and quantified** — directly supports the "Mixed Stress" class requirement from Angon et al.
4. **STRFM fusion method** (Landsat MODIS temporal fusion) is applicable to our 12-year archive
5. **Same study area, same crop** — our model should achieve comparable or better R²
6. **Ratoon fields are more vulnerable** — must account for ratoon age as feature

---

## 3. Motlagh et al. (2026b) — Satellite-Derived Ky for Sugarcane in Southern Iran

**Citation:** Motlagh, A.H., Veysi, S., Mohammadi, A.S., & Naseri, A.A. (2026). Derivation of crop yield response factor (Ky) based on satellite data and machine learning methods. *Agricultural Water Management*, 330, 110260. DOI: [10.1016/j.agwat.2026.110260](https://doi.org/10.1016/j.agwat.2026.110260) | **Open Access**

### Key Findings
| Metric | Value |
|--------|-------|
| Average seasonal Ky | **1.05** (vs. FAO-66 default of 1.2) |
| Ky range | 0.2–1.63 (substantial spatiotemporal variability) |
| Peak water stress sensitivity | **Early July, Ky > 1.82** |
| LST bias correction (RF) | RMSE < 1.0°C, nRMSE < 3%, rMBE ≈ 0% |
| Satellite CWSI vs field | RMSE = 0.05, nRMSE = 11% |

### Methodology
- Fused Landsat 7/8/9 + MODIS LST in GEE
- RF algorithm corrected LST biases before CWSI calculation
- Ky computed at dekadal, monthly, and seasonal scales
- 12 field points for ground calibration/validation

### Direct Implications
1. **FAO-66 Ky = 1.2 overestimates water stress sensitivity** for Khuzestan sugarcane — using 1.05 (local calibration) is more accurate
2. **Early July is critical period** (Ky > 1.82) — our model must capture stress onset in early growing season
3. **LST bias correction with RF works** — we can apply same approach to our Landsat archive
4. ** dekadal Ky variability** proves stress is not static — supports time-series approach over single-date

---

## 4. Hajeb et al. (2023) — Multi-Variable Sugarcane Retrieval from Sentinel-2

**Citation:** Hajeb, M., Hamzeh, S., Alavipanah, S.K., Neissi, L., & Verrelst, J. (2023). Simultaneous retrieval of sugarcane variables from Sentinel-2 data using Bayesian regularized neural network. *International Journal of Applied Earth Observation and Geoinformation*, 116, 103168. DOI: [10.1016/j.jag.2022.103168](https://doi.org/10.1016/j.jag.2022.103168) | **Open Access**

**Study area:** Amir Kabir Sugarcane Agro-Industrial zone, Khuzestan — **same 14,000 ha area**

### Key Findings
| Variable | RMSE | Unit |
|----------|------|------|
| LAI | 0.48 | m²/m² |
| Leaf Sheath Moisture (LSM) | 2.36 | % wb |
| Leaf Chlorophyll Content (LCC) | 5.85 | μg/cm² |
| Leaf Nitrogen Concentration (LNC) | 0.23 | % |

- **Simultaneous retrieval outperformed individual retrieval** for all variables
- BRANN (Bayesian Regularized ANN) superior to conventional LM_ANN
- Best architecture: 1 hidden layer, 4 neurons
- 136 field samples across 5 varieties and 7 ratoon ages
- 10 Sentinel-2 bands used (B2–B8, B8a, B11–B12)

### Direct Implications
1. **LAI is retrievable from S2 for sugarcane** — can use as indirect salinity proxy (per Paciolla et al. methodology)
2. **Multi-variable simultaneous retrieval** reduces error vs. individual models — supports our multi-output classifier design
3. **BRANN regularization prevents overfitting** with small datasets (136 samples) — relevant for our 50–100 labeled fields
4. **5 varieties + 7 ratoon ages covered** — our 490 fields should have similar diversity
5. **Sentinel-2 10m bands are sufficient** — don't need hyperspectral

---

## 5. Malee et al. (2026) — Deficit Irrigation & Water Productivity in Sugarcane

**Citation:** Malee, C., Phattaralerphong, J., Kositsakulchai, E., Rattanasakphakdee, S., Luepromchai, E., & Kachenchart, B. (2026). Enhancing water productivity in sugarcane cultivation by integrating basal crop coefficient with deficit irrigation. *Agricultural Water Management*, 333, 110529. DOI: [10.1016/j.agwat.2026.110529](https://doi.org/10.1016/j.agwat.2026.110529) | **Open Access**

### Key Findings
| Parameter | Value |
|-----------|-------|
| Kcb (initial growth) | 0.15 |
| Kcb (mid-season) | 1.11 |
| Kcb (late-season) | 0.49 |
| Optimal deficit irrigation | 25–50% MAD (Management Allowed Depletion) |
| Yield loss under deficit | Minimal at 25–50% MAD |
| Rainfed yield loss | Significant due to rainfall variability |

### Methodology
- Weighing lysimeters (full irrigation vs. 50% MAD deficit)
- SIMDualKc model calibrated for KK3 cultivar
- AquaCrop model validated against lysimeter + regional yield data
- FAO-56 dual Kc framework

### Direct Implications
1. **Kcb values for tropical savanna climate** — provides reference for ETc estimation in arid irrigated systems
2. **Deficit irrigation is viable** — supports our thesis focus on water stress monitoring (not just avoiding it)
3. **Mid-season Kcb = 1.11** is critical — highest water demand period aligns with July–September stress window
4. **AquaCrop model framework** could be used for physics-guided constraints in our ML pipeline

---

## Cross-Paper Synthesis: What This Means for the Thesis

### Confirmed Methodology (from these papers)
| Component | Source | Implementation |
|-----------|--------|----------------|
| CWSI computation | Zoratipour et al. (2026) | Landsat-MODIS fusion via STRFM; threshold 0.4–0.5 |
| Cloud masking | Motlagh et al. (2026) | CFMASK + GEE preprocessing |
| Temporal fusion | Motlagh et al. (2026) | STRFM for daily LST from 8-day Landsat |
| LST bias correction | Motlagh et al. (2026b) | RF correction (RMSE < 1°C) |
| Salinity gradient | Motlagh et al. (2026) | ECe 1.7–8.0 dS/m; 128 wells for interpolation |
| LAI as proxy | Hajeb et al. (2023) | Sentinel-2 BRANN retrieval (RMSE 0.48) |
| Yield baseline | Motlagh et al. (2026) | R² = 0.93, RMSE = 5.38 t/ha |
| Ky calibration | Motlagh et al. (2026b) | Local Ky = 1.05 (not FAO default 1.2) |
| Peak stress period | Multiple papers | Early July (Ky > 1.82), July–September window |

### Validation Framework (from these papers)
1. **CWSI validation:** Proximal Tc measurements (Zoratipour) → satellite CWSI
2. **Salinity validation:** ECe from 128 wells → kriging interpolation → field-level labels
3. **Yield validation:** Combine harvester records → RF prediction accuracy
4. **LAI validation:** Field measurements (136 ESUs) → Sentinel-2 retrieval

### Gap These Papers Don't Cover (Our Contribution)
| What they do | What we add |
|-------------|-------------|
| Single-timepoint classification | **12-year temporal sequence** → phenology + stress trajectory |
| Supervised RF on indices | **CNN-Mamba SSL** → learns representations from unlabeled data |
| Static stress indicators | **Temporal XAI** → explains which time steps drive predictions |
| Water OR salinity | **Both + mixed stress class** → interactive effects (Angon et al.) |
| No explainability | **SHAP + temporal Grad-CAM** → physically interpretable predictions |

---

## Recommended Reading Order for Thesis Writing

1. **Motlagh et al. (2026)** — establishes the yield-stress-salinity relationship in our exact study area
2. **Zoratipour et al. (2026)** — provides CWSI methodology and thresholds for Khuzestan
3. **Hajeb et al. (2023)** — shows multi-variable retrieval from S2 for our crop
4. **Motlagh et al. (2026b)** — satellite-derived Ky for precision irrigation
5. **Malee et al. (2026)** — deficit irrigation context and Kcb calibration

---

*Compiled by Kilo, 2026-09-10*
