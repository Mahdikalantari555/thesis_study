# 09 — ML Yield Diagnosis in Khuzestan Sugarcane (Motlagh et al., 2026)

**Full Citation:** Motlagh, A.H., Veysi, S., Mohammadi, A.S., & Naseri, A.A. (2026). Leveraging remote sensing data and machine learning method for assessing sugarcane yield variability to support smart agriculture. *Smart Agricultural Technology*, 14, 102391.  
**DOI:** [10.1016/j.atech.2026.102391](https://doi.org/10.1016/j.atech.2026.102391)  
**Status:** ✅ Full read (2026-10-04)  
**Themes:** #Study-area #CWSI #Salinity #Yield

---

## What It Does

Diagnoses drivers of sugarcane yield variability across 336 fields in Amirkabir Agro-Industrial, Khuzestan using RF on fused satellite + soil + water table data.

## Study Area

| Parameter | Value |
|-----------|-------|
| Location | Amirkabir Agro-Industrial, Khuzestan (31°15'–31°40'N, 48°12'–48°30'E) |
| Fields | 336 study fields (unit has ~400 fields, each ~25 ha) |
| Climate | Semi-arid, 198 mm annual rain, no summer rain |
| Soil | Heavy to semi-heavy; texture 0–100 cm: clay 13–28%, silt 42–53%, sand 29–38% (§3.1, p.6) |
| Period | July–September 2023 |
| Drainage | Subsurface drainage at 1.8 m depth (all fields) |

## Methodology

```
Inputs:
  ├─ Daily CWSI (Landsat-MODIS fused via STRFM)
  ├─ Soil salinity (ECe, weekly, 0–90 cm, kriging-interpolated from 128 wells)
  ├─ Water table depth (weekly, 128 observation wells)
  ├─ Soil texture (Sand/Silt/Clay from SoilGrids, 0–30 cm)
  ├─ Crop age + variety
  └─ Ambient temperature

Model: Random Forest (70:30 split)
Output: Yield prediction + feature importance + interaction analysis
```

## Key Results

### Feature Importance
| Driver | Importance (%) | Interpretation |
|--------|---------------|----------------|
| **Water stress (CWSI)** | **40.6%** | Dominant driver |
| **Soil salinity** | **27.1%** | Second driver |
| Crop age | 9.0% | Tertiary |
| Water table depth | 7.0% | Fourth (Fig. 8, p.7) |
| Water × Salinity interaction | **Synergistic (PDP-based; no % given)** | Disproportionate loss — see §3.3 quantification below |

### Performance
- **R² = 0.93, RMSE = 5.38 t/ha** — full-dataset fit, n = 336 (Fig. 13, §3.4, p.10); NOT a held-out score
- Training (n = 236): R² = 0.965, RMSE = 4.12, nRMSE = 5.19%, rMBE = −0.06% (Fig. 12a, p.10)
- Independent test (n = 100): R² = 0.821, RMSE = 7.56, nRMSE = 9.56%, rMBE = 1.35% (Fig. 12b, p.10)
- Yield range: <40 to >130 t/ha under **uniform management** (§1, p.2); observed 40–134 t/ha (Fig. 14a)

### Critical Finding: Synergistic Interaction
Abstract (p.1): "Strong synergistic interactions were observed between water and salinity stresses, leading to disproportionate yield losses that accelerated markedly when high salinity coincided with elevated CWSI, particularly in ratoon fields."

Exact quantification (§3.3, p.7): "The interaction between CWSI and salinity (Figs. 10 and 11) was strongly synergistic: yield declined only gradually with either stressor alone, but their combination produced disproportionately severe losses. For example, moderate salinity (3.4 dS m⁻¹) alone caused only a modest yield reduction, but when combined with high water stress (CWSI > 0.44), yield collapsed."

The interaction is real and measurable at field scale — but **no interaction percentage is reported anywhere**; it is expressed via 2-D/3-D PDP surfaces (Figs. 10–11) plus this worked example.

## Verified Full-Text Findings (2026-10-04)

Every number below was read directly from the PDF (14 pp., Motlagh et al. 2026, Smart Agric. Technol. 14:102391); source = section/page/figure.

### Model & performance (§2.3–2.4, §3.4)
- Random Forest in R v4.5.2 (§2.3, p.4); 70:30 train-test split → n = 236 train / n = 100 test (§2.4, p.5).
- Inputs (§2.3, p.4): CWSI, soil salinity, water table depth, soil texture (sand/silt/clay), varieties, age. Ambient temperature also appears in the workflow feature list (§2.5/Fig. 4, p.5).
- Target: actual harvested yield per field (t ha⁻¹), 2023 season; observed range 40–134 t/ha (Fig. 14a, p.11). Records come from the unit database ("Actual Yield, historical records", Fig. 4, p.5).
- **Full-sample fit (n = 336): R² = 0.93, RMSE = 5.38 t/ha, nRMSE = 6.8%, rMBE = 0%** (Fig. 13 + §3.4, p.10).
- Training: R² = 0.965, RMSE = 4.12, nRMSE = 5.19%, rMBE = −0.06% (Fig. 12a, p.10).
- Independent test: R² = 0.821, RMSE = 7.56, nRMSE = 9.56%, rMBE = 1.35% (Fig. 12b + §3.4, p.10). Train→test R² decline = 0.144.
- Interpretation bands used: R² > 0.75 strong; nRMSE < 10% excellent; rMBE ±10% acceptable (§2.4, p.5).

### Feature importance (Fig. 8, p.7; §3.2, p.6)
CWSI 40.6% > Salinity 27.1% > Age 9.0% > Water_Table_Depth 7.0% > Clay 4.8% > Sand 4.4% > Silt 3.3% > Variety_1 2.0% > Variety_2 0.6% > Variety_3 0.5% > Variety_4 0.5% > Variety_8 0.2% > Variety_5 0.2%. Importance type (permutation vs impurity) is NOT specified in the text.

### Water × salinity synergy — the exact quantification (§3.3, pp.6–7)
- Key sentence (§3.3, p.7): "The interaction between CWSI and salinity (Figs. 10 and 11) was strongly synergistic: yield declined only gradually with either stressor alone, but their combination produced disproportionately severe losses. For example, moderate salinity (3.4 dS m⁻¹) alone caused only a modest yield reduction, but when combined with high water stress (CWSI > 0.44), yield collapsed."
- **No interaction percentages exist in the paper** — the synergy is shown as 2-D PDPs (Fig. 10, p.8: CWSI×salinity dS/m; CWSI×age; salinity×age) and 3-D PDPs (Fig. 11, p.9: CWSI×salinity×age quantiles Q1–Q5, yield color scale 50–120 t/ha).
- Age dependence (§3.3, p.7): older cane (Age 4–5) far more vulnerable to water deficit than Age 1–2; salinity×age negative effect intensifies with age ("supporting the practice of shorter crop cycles in salinity-affected areas"); Fig. 11 Q5 (oldest) = lowest yields under all conditions, flatter stress response. Conclusion (p.12): vulnerability "intensifies sharply in older ratoon fields".

### Salinity: measurement & ranges (§2.2.3, p.4; §3.1, p.5–6)
- Protocol: weekly sampling from root zone **0–90 cm**; EC of saturated-paste extract per standard US Salinity Laboratory methods; kriging interpolation across fields; 128 observation wells serve combined salinity/water-table monitoring (Fig. 3, p.4).
- Measured EC across all fields and sampling dates: **1.7–8.0 dS/m** (§2.2.3, p.4).
- Seasonal (Jul–Sep 2023) interpolated root-zone map: **2.93–4.35 dS/m**, hotspots in western/central/southern regions (§3.1 + Fig. 5b, p.5–6).
- 1.7 dS/m doubles as the cited tolerance threshold: salinity "significantly above the well-established sugarcane tolerance threshold of 1.7 dS·m⁻¹" (§3.1, p.5, ref [50]).

### CWSI & water table (§2.2.1–2.2.2, p.2; §3.1, p.5–6)
- CWSI = (Ts − Tcold)/(Thot − Tcold), simplified empirical, per-pixel (Eq. 1); hot/cold = max/min LST of vegetated reference pixels, ET assumed zero there; seasonal mean CWSI per field feeds the ML.
- Fusion: Landsat 7/8/9 LST (single-channel algorithm) + MOD11A1/MYD11A1 1-km daily, blended with STRFM; 31 cloud-free images pre-processed in GEE; effective 8-day revisit via overlapping paths 39–165 / 38–166 (§2.2.1, p.2; Fig. 2, p.3). Window deliberately restricted to July–September 2023 (§2.2.2, p.2).
- Seasonal field-mean CWSI: **0.31–0.58** per text (§3.1, p.5); Fig. 5a legend reads 0.31–0.56. Values > 0.5 labelled "severe water deficit" (§3.1, p.5).
- Water table depth: **82–116 cm**, shallowest in east/northeast near irrigation canals (§3.1, p.5–6; Fig. 5c).

### Study area & data inheritance (§2.1, p.2; Figs. 1, 7; §3.7, p.12)
- Amirkabir Agro-Industrial Unit, Khuzestan, 31°15′–31°40′N, 48°12′–48°30′E, ~7 m a.s.l. (§2.1, p.2; Fig. 1, p.3; confirmed in Acknowledgements, p.12).
- Unit = ~400 fields of ~25 ha; study uses 336 (Abstract p.1; Fig. 5/7 captions; n = 336 in Fig. 13).
- **Single growing season 2023** (Limitations §3.7, p.12: "based on a single growing season (2023)"); RS window Jul–Sep 2023, harvest begins Oct–Nov (§3.5, p.11).
- Varieties: CP48, CP57, CP69, CP73, IRC, SP70; age classes Plant → Ratoon 4 (Fig. 7, p.7).
- Soil texture from SoilGrids, weighted 0–30 cm from 0–5/5–15/15–30 layers (Eqs. 2–4, §2.2.3, p.3–4) — but §3.1 (p.6) reports composition for "root zone (0–100 cm)": clay 13–28%, silt 42–53%, sand 29–38%. Internal inconsistency in the paper.
- Data availability: "Data will be made available on request" (p.12) — no public dataset.

### Repo-claim verification

1. **R² = 0.93** — VERIFIED (with a critical nuance). RF; target = per-field harvested yield, 2023 season; inputs = CWSI + salinity + water table + soil texture + variety + age. R² = 0.93 / RMSE = 5.38 is the **full-sample (n = 336) fit** (Fig. 13, §3.4, p.10), NOT the held-out score — independent test R² = 0.821 (n = 100, Fig. 12b). The old note wording "train + test" was wrong and is corrected above.
2. **Water×salinity synergy** — PARTIAL (real, but no numeric interaction %). Quantified via PDPs (Fig. 10a, p.8; Fig. 11, p.9) and the worked example: 3.4 dS/m alone → modest loss; 3.4 dS/m + CWSI > 0.44 → "yield collapsed" (§3.3, p.7). Ratoon amplification is qualitative (Abstract p.1; §3.3 p.7; Conclusion p.12). The 40.6%/27.1% figures are main-effect importances (Fig. 8), not interaction shares.
3. **Salinity 1.7–8.0 dS/m** — VERIFIED (§2.2.3, p.4): weekly ECe (saturated paste), 0–90 cm root zone, 128 wells, kriged; all fields/dates span 1.7–8.0 dS/m. "EC_LOW = 1.7 dS/m" is also the cited tolerance threshold (§3.1, p.5). Caveat: the seasonal field map spans only 2.93–4.35 dS/m (Fig. 5b).
4. **CWSI threshold 0.4–0.5** — PARTIAL. THIS paper proposes its own age-tiered triggers: young (Plant–Ratoon 2) fields CWSI 0.40–0.45; older (Ratoon 3–5) 0.30–0.35 (§3.5, p.11); >0.5 = severe deficit (§3.1, p.5). So 0.4–0.5 matches the young-field band, but the paper does not cite Zoratipour for it, and the old-field band is lower (0.30–0.35).
5. **Inheritable data** — VERIFIED. 336 fields at Amirkabir Agro-Industrial Unit (confirmed); one year only (2023); yield = per-field harvested tonnage t/ha (40–134, Fig. 14a); salinity = weekly ECe 0–90 cm saturated paste from 128 wells, kriged; water table weekly from the same 128 wells (82–116 cm); texture from SoilGrids. Varieties CP48/CP57/CP69/CP73/IRC/SP70; Plant–Ratoon4. Data not public — "available on request".



## Direct Implications for Thesis

1. **Baseline R² = 0.93** (full-sample fit; honest baseline = test R² 0.821) — our CNN-Mamba must match or exceed this
2. **CWSI is #1 driver** — confirms thermal-based water stress focus
3. **Salinity is #2** — must be modeled separately, not as confounder
4. **Interaction effect demonstrated via PDPs** (no numeric %) — validates "Mixed Stress" class requirement
5. **Same study area, same crop** — our results should be directly comparable
6. **Ratoon vulnerability** — must include ratoon age as feature

## Methods to Reproduce

| Component | Their Approach | Our Adaptation |
|-----------|---------------|----------------|
| CWSI computation | STRFM fusion (Landsat 8-day + MODIS daily) | Same; use GEE + STRFM |
| Cloud masking | Cloud masking in GEE (31 cloud-free images; algorithm not named in Methods) | Same |
| Soil salinity | Weekly ECe (saturated paste), 0–90 cm, 128 wells → kriging | Need to establish well network |
| Feature importance | RF variable importance (type not specified; Fig. 8) | Use SHAP for our neural model |
| Interaction analysis | 1-D / 2-D / 3-D Partial Dependence Plots (Figs. 9–11) | Use SHAP interaction values |

## Gaps This Paper Doesn't Cover (Our Contribution)

- ❌ No temporal modeling (single-season snapshot)
- ❌ No deep learning (RF baseline)
- ❌ No SSL pre-training
- ❌ No explainability beyond RF importance + PDPs (no SHAP)
- ❌ No mixed-stress class (treats water + salinity as separate features)

---

*Linked from: [[Literature-Matrix]], [[00-Thesis-Overview]]*
