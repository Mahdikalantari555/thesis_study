# 08 — Salinity from Satellite LAI (Paciolla et al., 2025)

**Full Citation:** Paciolla, N., Corbari, C., et al. (2025). Salinity stress and water availability inferred from satellite leaf area index assimilated into a water-energy-crop model. *Precision Agriculture*.  
**DOI:** [10.1007/s11119-025-10279-5](https://doi.org/10.1007/s11119-025-10279-5)  
**Status:** ✅ Full read (2026-10-04)  
**Themes:** #Validation #Study-area #LAI

---

## What It Does

Assimilates **Landsat-8-derived LAI** (NDVI → FVC → LAI, Choudhury 1987; p.9–10) via an Ensemble Kalman Filter into the FEST-EWB-SAFY water-energy-crop model, so that salinity and water effects on growth/yield emerge without any salinity input in the DA run (p.4, p.16). LST (Landsat 8 + Sentinel-3) is used separately to calibrate/validate the water-energy balance (p.9, p.13). *(Correction 2026-10-04: earlier note said "Sentinel-2 LAI" — wrong; Sentinel-2 only provides NDVI for LST downscaling and albedo.)*

## Study Area

- Ca' Bianca farm, Chioggia, NE Italy — **one 21-ha field**, southern margin of Venice Lagoon, lower Po Valley (p.7)
- Rainfed maize, 4 seasons 2019–2022 (p.8); field at −1.0 to −3.3 m below sea level; water table −0.5 to −1.8 m = the ONLY irrigation source (sub-irrigation); seawater intrusion (p.7–8)
- Silty clay with acid peat; sandy paleoriver strip (>60% sand); root-zone EC 0.3–5.8 dS/m at control points (p.16); EC map (0–7 dS/m) from 123 points measured in 2012 (p.8, Fig. 2b)
- Landsat 8: 12–13 images/yr (Table 1, p.11); "~14 images ≈ new image every 11 days" stated for the investigated period (p.17); only 1 Landsat image between mid-April and early Aug in 2021 (p.19)

## Methodology

```
FEST-EWB-SAFY Model:
  ├─ FEST-EWB: Distributed energy-water balance
  └─ SAFY: Crop model for yield prediction
  
Data Assimilation — EnKF (Evensen 2003/2009; p.6–7):
  ├─ 100 ensemble members; state updates at each satellite overpass (p.6–7)
  ├─ Perturbed: model initial conditions + met forcing (radiation, air T), Gaussian, null mean, err = avg std dev
  ├─ LAI obs: lognormal perturbation (non-negative); obs error = std over the years; assimilated as log(LAI), Eq. 3
  └─ Satellite obs: Landsat-8 LAI (NDVI→FVC→LAI, k=0.5 calibrated); LST (L8+S3) → calibration/validation only
```

## Key Results

| Metric | Finding |
|--------|---------|
| LAI–salinity link | Marked peak-LAI decrease above EC_LOW = 1.7 dS/m in the EC-informed calibrated model (Fig. 9a, p.17); satellite LAI ~15% lower at high-salinity point (5.8 dS/m) vs low (0.3 dS/m) (p.16, Fig. 8) |
| Yield prediction | DA comparable to EC-informed model: MAE 1.3–2.9 vs 1.7–1.9 t/ha; RMSE 1.7–3.3 vs 2.2–2.5 t/ha (Table 4, p.15); observed ~5 t/ha (northern part, 2019) with marked drop in 2021 |
| Spatial heterogeneity | DA captured within-field patterns; yield R² 0.22 vs 0.03 in 2021 (Table 4, p.15–16) |
| Validation | Claas Lexion 780 yield monitor (northern part of field only; no yield data 2022) (p.9, p.15) |
| LAI fit (Table 3, p.14) | DA better in 2019/2022 (MAE 0.51/0.83 vs 0.79/0.86 m²/m²), worse in 2020/2021 (RMSE 1.66/1.93 vs calibration 1.09/1.39) |

## Implications for Thesis

| Their Finding | Our Application |
|---------------|-----------------|
| LAI captures salinity without direct EC | Use Landsat-derived LAI as indirect salinity proxy |
| ECLOW = 1.7 dS/m threshold | Validation benchmark for salinity class boundaries |
| DA results comparable to EC-informed calibration (p.20–21), not uniformly better | Supports DA/dynamic approach, but per-year validation needed |
| ~11-day cadence OK in clear-sky periods; cloud gaps degraded 2021 badly (p.19–20) | Our Landsat+S2 fusion helps; Khuzestan summer cloud cover is low (favorable) |

## Methodological Template

⚠ **Verified caveat (2026-10-04):** Paciolla et al. do NOT convert LAI into salinity and never validate inferred salinity against measured EC. They skip salinity as model **input** (not as output): salinity effects emerge implicitly when Landsat-8 LAI is assimilated (EnKF) into FEST-EWB-SAFY. A direct LAI→EC regression over 490 fields is the Hajeb et al. (2023) route — a different method. Paciolla's route requires running + LST-calibrating the crop model per field.
Transferable template (with their conditions, see Verified Findings below):
1. Retrieve LAI time series (they: Landsat-8, NDVI→FVC→LAI, extinction coeff. calibrated to 0.5 on ground LAI, p.9–10)
2. Calibrate water-energy balance on LST (pixel-wise, 2020 calibration year, p.6)
3. Run EnKF DA of LAI with crop-specific FAO salinity parameters (maize EC_LOW = 1.7 dS/m, Eq. 2, p.5)
4. Validate against yield monitor / subset of field ECe measurements

## Verified Full-Text Findings (2026-10-04)

All page numbers refer to *Precision Agriculture* (2025) 26:91 (26 pp., PDF).

### DA scheme (Claim 2 — VERIFIED)

- **Method:** Ensemble Kalman Filter (EnKF; Evensen 2003, 2009) with **100 ensemble members** (p.6). Errors injected via (a) model initial conditions and (b) meteorological forcing (radiation, air temperature) — Gaussian, null mean, error = average standard deviation; (c) LAI observations perturbed with a **lognormal** distribution (non-negative constraint; Kondrashov et al. 2011), observation error = standard deviation over the years (p.6–7).
- **Assimilated variable:** satellite LAI via log-transform Λ = log(LAI) (Eq. 3, p.7); state updates applied at local satellite overpass time (p.7). DA corrects LAI and effectively re-calibrates the phase of plant development (p.16).
- **Model:** FEST-EWB-SAFY — distributed energy-water balance FEST-EWB (computes LST internally, no external LST input needed) coupled to SAFY crop model (GAI + dry aboveground mass, daily; Monteith LUE); ΔDAM = APAR·PLUE·f(Td)·f_water_S·K_saltS (Eq. 1, p.5). Run at **1-h temporal / 5 m spatial** resolution, seasons 2019–2022 (p.5).
- **Salinity response inside model:** K_saltS = 1 − b/(K_y·100)·(EC − EC_LOW) (Eq. 2, p.5), parameters from FAO Irrigation & Drainage Papers 33 (Doorenbos et al. 1979) and 48 (Rhoades et al. 1992); for maize **EC_LOW = 1.7 dS/m** (p.17).
- **Satellite observations:** LAI retrieved from **Landsat 8** (NDVI→FVC, Gutman & Ignatov 1998 with NDVI_S=0.2, NDVI_V=0.9; LAI = −ln(1−FVC)/k(θ), Choudhury 1987; k calibrated to 0.5 against ground LAI) (p.9–10). LST from Landsat 8 (30 m, 16-day) and Sentinel-3 SLSTR (1 km, downscaled to 10 m by NNTS using Sentinel-2 NDVI) — used for pixel-wise calibration/validation of the water-energy balance, **not** in the DA (p.9, p.13; Table 1, p.11).
- **Region/period:** Ca' Bianca, Chioggia (NE Italy), Venice Lagoon margin; 21-ha rainfed maize field at −1.0 to −3.3 m below sea level; water table −0.5 to −1.8 m, the only irrigation source (sub-irrigation); seasons 2019–2022 (p.7–8). Rainfall ~670 mm/yr, ET0 850 mm (p.8).
- Ground truth that existed but was NOT used in the DA run: EC map from 123 points (2012) at 4 depths (p.8); TEROS-12 soil moisture/EC at 5 stations (10–70 cm); weekly water-table salinity; ground LAI at 5 stations 3/5/4/4 times per season (p.8–9).
- Claimed novelty: first assimilation of satellite LAI into a complete crop-water-energy balance model under salinity stress and changing water availability (p.3).

### LAI as salinity proxy — precise evidential basis (Claim 1 — PARTIAL)

- **What is demonstrated:** with NO salinity input, the DA run reproduces LAI dynamics and yield patterns comparable to a model calibrated WITH the direct (2012) EC map (p.16; Conclusions p.20–21).
- **Accuracy numbers:** Yield vs harvester (Table 4, p.15): DA MAE 1.3/1.3/2.9 t/ha, RMSE 1.7/1.7/3.3 t/ha, R² 0.10/0.09/0.22 vs calibration MAE 1.9/1.7/1.7, RMSE 2.5/2.2/2.2, R² 0.07/0.10/0.03 (2019/2020/2021; no yield data 2022). LAI vs satellite (Table 3, p.14): DA MAE 0.51/1.19/1.20/0.83 m²/m², RMSE 0.75/1.66/1.93/1.14 vs calibration MAE 0.79/0.83/1.19/0.86, RMSE 0.95/1.09/1.39/1.07 — DA better in 2019 & 2022, worse in 2020–2021.
- **LAI–salinity numbers:** satellite LAI at the very saline point B (5.8 dS/m) is **~15% lower** than at low-salinity point A (0.3 dS/m) — a 20× EC contrast (p.16, Fig. 8). In the EC-informed calibrated model, pixels with EC > **EC_LOW = 1.7 dS/m** show a marked decrease in peak LAI (Fig. 9a, p.17); peak LAI can exceed 8 m²/m² (p.14).
- **What is NOT shown:** 1.7 dS/m is the FAO maize parameter embedded in the model (p.5, p.17), NOT an empirically fitted LAI-reduction threshold from this dataset. The paper never regresses LAI against EC, never predicts EC values, and never validates an inferred salinity map against measured EC — no salinity-accuracy metric exists in the paper. In the DA run the EC_LOW signal is even blurred: DA resets LAI to the EO retrieval value, points cluster at few similar LAI values, and "the effect of EC_LOW is less marked than in the calibrated model and heavily reliant on the salinity impact on LAI and its visibility from satellite" (p.17, Fig. 9b).
- **Water vs salinity disentangling:** handled by the coupled model (f_water_S and K_saltS both act on DAM, water balance constrained by LST); paper flags salinity-induced soil cracking that raises permeability as an interpretive confounder (p.12, p.18–19).

### Transfer conditions / limitations (Claim 3 — PARTIAL; "490 fields" NOT FOUND in paper)

- The paper contains **no mention of 490 fields** — it is ONE 21-ha maize field. "Skipping ECe" there means skipping salinity as model input; the output is stress/yield, never an EC map.
- **Their own transferability claims:** bypasses "detailed local observations of salt concentration", reduces reliance on site-specific data, applicable "during the agricultural season itself and without the need for extensive salinity measurements", feasible "over large irrigation consortia"; exportable to regions with salinity stress and/or shallow groundwater tables (p.19, p.21).
- **Hard requirements / stated limitations:**
  - Crop-specific FAO parameters (EC_LOW, b, K_y) must be known (p.5); the linear EC_e–yield–K_saltS relation is a limitation at very high salinity, and a single seasonal K_saltS is used although salinity impact varies through the season (p.20).
  - Strong reliance on LAI imagery: 10×10 m may be too coarse for within-field singularities (Fig. 6, p.19); temporal frequency critical — clouds: in 2021 only 1 Landsat image between mid-April and early Aug dispersed the ensemble (p.19–20). "Satellite-based approaches are more viable for regions with limited cloud cover during the period of plant development" (p.19–20).
  - The water-energy balance still needs pixel-wise LST-based calibration (2020 calibration year; Corbari & Mancini 2014) plus met forcing, soil hydraulic parameters, groundwater level (p.5–6) — DA removes the salinity map and crop calibration, NOT the hydrological parameterization.
  - Independent validation still needs ground truth: here a yield monitor (northern part of field only; none in 2022) and 5 instrumented stations (p.8–9, p.15).
  - Salinity range covered: root-zone EC ~0.3–5.8 dS/m (p.16); EC map 0–7 dS/m (Fig. 2b) — moderate coastal salinity; the EC map dates from 2012, 7–10 years before the study seasons (p.8).
  - Context is rainfed maize with a shallow saline water table as sole irrigation — different from irrigated arid agriculture (Khuzestan), where irrigation-water salinity dominates and water-stress vs salinity-stress confounding in LAI must be handled explicitly (here the coupled model + LST does that job).
- **Error scales to expect:** LST MAE ~3.0–3.5 °C (Table 1, p.11); soil moisture RMSE 0.053–0.104 (10 cm) and 0.047–0.087 m³/m³ (70 cm) (Table 2, p.12); yield MAE 1.3–2.9 t/ha (Table 4, p.15).

### Repo-claim verification

| # | Repo claim | Verdict | Evidence |
|---|-----------|---------|----------|
| 1 | Satellite LAI can infer salinity effects without ECe measurement | **PARTIAL** | True only as DA into a crop model: salinity effects on LAI/yield reproduced with no salinity input (p.16; Tables 3–4 p.14–15; Conclusions p.20–21). No LAI→EC relationship fitted, no EC predicted, no salinity-accuracy metric. EC_LOW = 1.7 dS/m is the FAO maize parameter in the model (Eq. 2 p.5; p.17), not an observed LAI-reduction threshold. Observed signals: ~15% lower satellite LAI at 5.8 vs 0.3 dS/m (p.16); marked peak-LAI drop above 1.7 dS/m only in the EC-informed calibration (Fig. 9a, p.17); effect blurred in the DA run (Fig. 9b, p.17). |
| 2 | DA scheme details | **VERIFIED** | EnKF (Evensen 2003/2009), 100 members; Gaussian perturbations on initial conditions + met forcing (radiation, air T); lognormal on LAI obs; obs error = std over years; LAI assimilated as log(LAI) (Eq. 3); updates at overpass time (p.6–7). Model: FEST-EWB-SAFY, 1-h / 5 m (p.4–5). Observations: Landsat-8 LAI (p.9–10); LST (L8 + Sentinel-3) only for water-energy calibration (p.9, p.13). Region: Ca' Bianca, Chioggia (Venice Lagoon margin), 21-ha rainfed maize, 2019–2022 (p.7–8). |
| 3 | "Justifies skipping ground ECe for 490 fields" | **PARTIAL** (490 fields: NOT FOUND) | Paper is a single 21-ha field; "490" appears nowhere. Skipping ECe = skipping salinity as model input; no salinity map is produced or validated. Transfer requires: crop-specific FAO params (p.5, p.20), dense clear-sky LAI series (2021 cloud failure case, p.19–20), LST-based hydrological calibration + met/soil/groundwater data (p.5–6), independent validation (yield monitor, p.9), moderate salinity range (~0.3–5.8 dS/m) where the FAO linear response holds (p.20). Claimed transferable to large irrigation consortia and shallow-water-table salinity regions (p.19, p.21). |

### Corrections to the pre-existing note (2026-10-04)

- "Sentinel-2 LAI" → LAI is retrieved from **Landsat 8** (p.9–10); Sentinel-2 provides NDVI for LST downscaling (NNTS) and albedo only.
- "Maize fields" → a **single 21-ha field** (p.7), rainfed, sub-irrigated by the shallow water table.
- "DA outperforms static calibration" → results are "**comparable**" (Conclusions p.20–21); DA wins some years/metrics (yield 2020, R² 2021, LAI 2019/2022) and loses others (LAI RMSE 2020–2021, yield RMSE 2019/2021).
- "LAI reduction markedly decreased when EC > 1.7 dS/m" → that contrast is explicit in the EC-informed calibrated model (Fig. 9a); in the DA run the EC_LOW effect is less marked (p.17).

---

*Linked from: [[Literature-Matrix]]*
