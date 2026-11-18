# 24 — ML Bias Correction of Satellite CWSI for Sugarcane (Zoratipour et al., 2025)

**Full Citation:** Zoratipour, E., Veysi, S., Mohammadi, A.S., Boroomand Nasab, S., & Naseri, A.A. (2025). Bias correction of satellite based crop water stress index using machine learning methods. *Agricultural Water Management*, 320, 109862.
**DOI:** [10.1016/j.agwat.2025.109862](https://doi.org/10.1016/j.agwat.2025.109862)
**Status:** ✅ Full read (2026-10-04)
**Themes:** #CWSI #ML #BiasCorrection #LST #Satellite #Sugarcane

---

## What It Does

Uses three ML models (RF, SVM, XGBoost) to bias-correct Landsat 8/9 Land Surface Temperature (LST), then re-computes CWSI from corrected LST. Validates against Idso-method ground-truth CWSI from proximal sensors.

## Study Area

- **Amirkabir Agro-Industrial Unit**, Khuzestan, Iran (same site as papers #10 and #12)
- 14,000 ha, 18 measurement points across sugarcane fields (abstract, §2.1 and QA/QC §2.7 all state 18 points / 18 proximal sensing stations; but §2.2.1 says 3 PS devices in each of 4 fields = 12 — paper-internal inconsistency)
- 24 cloudless Landsat 8/9 images (June–September 2023), 8-day effective revisit

## Methodology

### LST Retrieval
- Single-channel algorithm (SC) from Landsat 8/9 TIR band 10
- Emissivity from NDVI threshold method (Sobrino et al., 2008)
- Atmospheric functions from Jimenez-Munoz & Sobrino coefficients

### CWSI (raw, uncorrected)
```
CWSI = (LST - LST_cold_pixel) / (LST_hot_pixel - LST_cold_pixel)
```
Hot/cold pixels identified via SEBAL methodology.

### ML Bias Correction Framework
**Input features → LST correction:** NDVI, LAI, raw LST, emissivity (ε), DEM
**Target:** Canopy temperature (Tc) from ground sensors
**Split:** 70% train / 30% test

**Three models compared:**
| Model | Key Strength | Performance Ranking |
|-------|-------------|---------------------|
| Random Forest (RF) | Best overall, handles nonlinear dynamics | **#1** |
| XGBoost | Most temporally stable | #2 |
| SVM | Prone to overfitting on unseen data | #3 |

### Best Model (RF) Results — Testing Set
- Mean R² = **0.86**, RMSE = **2.66 °C**
- nRMSE = **1%**, rMBE = **2%** (very low bias)
- RF >> XGBoost > SVM ranking confirmed

### Feature Importance (RF)
1. **Satellite LST** — dominant predictor
2. **NDVI / LAI** — secondary, captures canopy characteristics
3. **DEM / emissivity** — weak importance (flat terrain, uniform sugarcane)

### CWSI After Bias Correction (vs. Raw)
- R² improvement: **+20.65%** (actual values: 0.73 → 0.92, Fig. 10, p.12 — the earlier "from ~0.65 to ~0.85" example was wrong)
- rMBE reduction: **~50%**
- nRMSE improvement: **~43.5%**
- Greatest gains on dates when raw R² was lowest (< 0.4)
- Cold pixel correction more effective than hot pixel (stable vegetation vs. heterogeneous bare soil)

## Key Findings

| Finding | Value | Implication |
|---------|-------|-------------|
| Best ML model | Random Forest | Superior for nonlinear LST-CWSI relationships |
| R² enhancement after correction | +20.65% avg | Substantial accuracy gain |
| Landsat 8 vs 9 | No significant difference | Framework portable across sensors |
| Seasonal pattern | Corrections largest in Aug–Sep | Crop water demand peaks; raw CWSI most biased then |
| Cold vs hot pixel correction | Cold pixels correct better | Vegetated surfaces more uniform; hot pixels heterogeneous |

## Relevance to Thesis

**High.** Directly relevant to the ML-based bias correction component of the proposed CNN-Mamba + SSL framework:

1. **Validates ML bias correction approach** for satellite-derived CWSI — supports the idea that ML can correct systematic LST/CWSI errors
2. **RF as gold standard** — provides a baseline model to beat with CNN-Mamba
3. **Aug–Sep peak bias** — confirms that raw satellite CWSI is most unreliable during high-demand period, justifying need for correction
4. **Limitation noted by authors**: only Landsat temporal coverage (~8 days); no daily monitoring — supports integration with higher-frequency data
5. **Limitation**: no salinity stress separation — CWSI conflates water and osmotic stress; directly motivates the disentanglement goal of this thesis
6. **Feature importance results** confirm LST as primary driver, vegetation indices as secondary — supports multimodal input design

## Limitations Cited by Authors

1. Hourly data unavailable; Landsat overpass at 10:30 misses peak stress (12–14:00)
2. ML models used separately, not ensembled/hybrid
3. Limited sensor network (18 points across 14,000 ha)
4. Single crop, flat topography — generalizability uncertain
5. No explicit separation of water vs. salinity stress effects on CWSI

## Verified Full-Text Findings (2026-10-04)

Full read of `papers/24-Zoratipour-2025-ML-BiasCorrection-CWSI.pdf` (16 pp; AWM 320:109862; printed pages = PDF pages). Every number below was checked against the PDF text.

### Study site & data (verified)
- **Site:** "Amir Kabir Agro Industry Unit," Khuzestan; 14,000 ha; farms 25 ha (Q4 channel 1000 m, furrow 250 m); arid; annual mean T 27 °C, rainfall 198 mm (§2.1, p.2). Four fields (Field1 = plant; Field1r2/r3/r4 = ratoons 1–3), clay loam/silty clay (Table 1, p.3).
- **Points:** abstract, §2.1 and QA/QC §2.7 state **18 points / 18 proximal sensing stations** (54 soil samples at 3 depths); §2.2.1 says 3 PS devices per field (= 12). Internal inconsistency; "18" is the recurring figure.
- **Imagery:** 24 cloudless Landsat 8/9 images, 22 Jun–19 Sep 2023 (12 L8 + 12 L9, Table 2, p.3); effective 8-day revisit from path/row overlap 165/39 + 166/38 (§2.2.2, p.3). LST: single-channel (SC) algorithm, TIR band 10, in Google Earth Engine; emissivity via NDVI threshold method (Sobrino et al., 2008) (§2.3.1, pp.3–4).
- **Raw satellite CWSI:** Eq 14 = (LST − LST_cold)/(LST_hot − LST_cold), hot/cold pixels via SEBAL (Bastiaanssen et al., 1998), cold/hot pixel extent ≥ 30 × 30 m (§2.3.1, p.4). Ground truth: Idso CWSI (Eq 1) with (Tc−Ta) baselines (Eq 2–3) from proximal sensors at the 10:30 am overpass (§2.2.1 p.2; §4 p.13).

### ML pipeline (verified)
- Models: **Random Forest (RF), SVM, XGBoost** (§2.4, p.4).
- **Input features** (Table 3, p.5; Fig. 2, p.6): satellite LST, NDVI, LAI, emissivity (ε), DEM. **Target:** field-measured canopy temperature (Tc) — ML learns the LST bias vs ground Tc; corrected LST recomputes CWSI via Eq 15 (§2.5, p.5). Split 70:30 train/test; ML coded in R 4.4.2 (§2.5, p.5).
- Hyperparameters tuned per overpass (Table 4, p.7): RF ntree = 100, mtry 2–4 (OOB 0.99→19.57%); XGBoost nrounds 50/100/150, max_depth 4/6/8, eta 0.05/0.1/0.3; SVM C 1/10/100, sigma 0.01/0.05.

### Results (verified)
- **RF best** for LST bias correction: mean test R² = 0.86, RMSE = 2.66 °C, nRMSE 1%, rMBE 2% (§3.3, p.7). Ranking **RF > XGBoost > SVM** on all evaluation metrics; SVM most overfitting (esp. 2023/06/23, 2023/09/19); XGBoost most stable (§3.2–3.3, p.7). **No significant L8 vs L9 difference** (§3.3, p.7; Conclusion p.14).
- **Feature importance** (§3.3.1, p.7; Fig. 6, p.9): Satellite LST dominant (r = 0.88 with measured LST, Fig. 6b) > LAI > NDVI > emissivity > DEM (weak — flat terrain, uniform crop).
- **Hot/cold pixels after RF correction** (Fig. 7, p.10; §3.4, p.8): cold R² 0.62→0.83 (RMSE 1.71→0.48 °C); hot R² 0.62→0.74 (RMSE 1.71→0.82 °C) → **cold-pixel correction more effective** (vegetated cold pixels more stable than heterogeneous hot pixels).
- **CWSI improvement** (§3.6, p.10; Fig. 10, p.12): before R² = 0.73, RMSE = 0.09, nRMSE = 23%, rMBE = −16% → after R² = 0.92, RMSE = 0.05, nRMSE = 13%, rMBE = −8%. Exact text: "R² increasing by **20.65%**"; "rMBE was reduced by approximately **50%**"; nRMSE "improved by approximately **43.47%**." (The abstract's "R² = 35 %, nRMSE = 47 % and rMBE = 50 %" is a garbled paraphrase — cite §3.6 instead.)
- **Per-overpass gains** (Table 5, p.13): R² enhancement ranges 15.18% (22 Jun) → 66.93% (25 Jul; raw R² 13.01→93.14). §3.6 text: lowest R² gains (<20%) on 22 Jun–8 Jul, 9 Aug, 10 Sep; highest on 25 Jul, 2 Aug, 26 Aug, 3 Sep. nRMSE/rMBE improvements average 30–65%.
- **Seasonal pattern:** corrections minor in June–July, "much larger and more spatially variable" in Aug–Sep when demand peaks (§3.5, pp.8–9; Fig. 9 difference maps, p.12).
- **Limitations (§4, p.13):** (1) no hourly data — Landsat overpass 10:30 am vs peak stress 12:00–14:00; (2) ML used separately, not ensembled/hybrid; (3) too few sensors (≥30 recommended). Conclusion (p.14): "the limited temporal coverage of Landsat remains a constraint, underlining the need to explore complementary platforms such as Sentinel or fused datasets to enable daily stress monitoring."

### Salinity (verified — mention only, never measured)
- Intro (p.2): "sugarcane faces multiple stresses, including heat, waterlogging, and **soil salinity**. Under such complex conditions, soil- or climate-based methods may not fully capture crop water status, making plant-based indices like the Crop Water Stress Index (CWSI) a more appropriate tool." Salinity never appears again — not in results, discussion, limitations, and no EC data.

### Repo-claim verification

| # | Repo claim | Verdict | Evidence |
|---|------------|---------|----------|
| 2 | ML = RF + XGBoost + SVM | VERIFIED | §2.4 p.4; Fig. 2 p.6 |
| 2 | Features: NDVI, LAI, raw LST, emissivity, DEM; target = ground Tc (LST bias correction) | VERIFIED | Table 3 p.5; §2.5 p.5; Fig. 2 p.6 |
| 2 | R² improved +20.65% | VERIFIED | §3.6 p.10 (0.73→0.92; Fig. 10 p.12) |
| 2 | rMBE reduced ~50% (direction: |−16%| → |−8%|) | VERIFIED | §3.6 p.10; Fig. 10 p.12 |
| 2 | nRMSE improved ~43.5% | VERIFIED (43.47%; 23%→13%) | §3.6 p.10 |
| 2 | RF #1, XGBoost #2 (most stable), SVM #3 (overfits) | VERIFIED | §3.2 p.7; §3.3 p.7 |
| 2 | Cold pixel corrects better than hot | VERIFIED | §3.4 p.8; Fig. 7 p.10 |
| 2 | Greatest gains when raw R² lowest (<0.4) | PARTIAL — Table 5: max +66.93% at 25 Jul (raw R² 0.13→0.93); but text also reports lowest gains (<20%) on other dates; paper wording self-contradictory | §3.6 p.10; Table 5 p.13 |
| 2 | Corrections largest Aug–Sep | VERIFIED | §3.5 pp.8–9; Fig. 9 p.12 |
| 2 | L8 vs L9 no significant difference | VERIFIED | §3.3 p.7; Conclusion p.14 |
| 5 | Site Amirkabir; 24 images Jun–Sep 2023; 8-day effective revisit | VERIFIED | §2.1 p.2; §2.2.2 p.3; Table 2 p.3 |
| 5 | 18 measurement points | PARTIAL — "18" stated 3×; §2.2.1 implies 12 (3 devices × 4 fields) | pp.1, 2, 5 vs §2.2.1 |
| 5 | Soil salinity measurements | NOT FOUND — salinity only as intro motivation (p.2), never measured | p.2 |

---

*Linked from: [[Literature-Matrix]], [[00-Thesis-Overview]]*
