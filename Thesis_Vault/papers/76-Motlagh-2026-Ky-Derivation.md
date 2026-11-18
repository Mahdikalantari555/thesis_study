# 76 — Satellite Ky Derivation for Sugarcane (Motlagh et al., 2026b)

**Full Citation:** Motlagh, A.H., Veysi, S., Mohammadi, A.S., & Naseri, A.A. (2026). Derivation of crop yield response factor (Ky) based on satellite data and machine learning methods. *Agricultural Water Management*, 330, 110260.
**DOI:** [10.1016/j.agwat.2026.110260](https://doi.org/10.1016/j.agwat.2026.110260) | **Citations: 0 (2026 — too new; locally load-bearing regardless)**
**Status:** ✅ Full read (2026-10-04) | Companion paper to #09 (same group; #09 = yield diagnosis, this = Ky derivation)
**Themes:** #Study-area #Ky #CWSI #Label-design #Water-accounting

---

## What It Does

Derives spatially explicit **yield response factor (Ky)** for sugarcane from satellite-derived daily CWSI (2023 season, southern Iran), using the Doorenbos & Kassam (1979) framework: (1 − Ya/Ym) = Ky·(1 − ETa/ETc) (Eq. 13). Pipeline: fused Landsat 7/8/9 + MODIS in Google Earth Engine → **RF bias-corrected LST** → daily CWSI → Ky at **dekadal / monthly / seasonal** scales. Field data: **12 field points** (canopy temperature via calibrated thermometer, 8–14 µm, ice-bath calibration; yield from the sugarcane development studies office).

## Verified Key Results (all abstract-level numbers confirmed in body)

| Metric | Value | Notes |
|--------|-------|-------|
| Average seasonal Ky | **1.05** | "lower than the FAO-66 default of 1.2" → standard coefficient "may prompt over-irrigation without yield benefits" (abstract) |
| Ky range | **0.2–1.63** (spatiotemporal) | dekadal-monthly-seasonal scales |
| Peak-sensitivity window | **early July, Ky > 1.82** | "highest Ky values occur in July" (§3.4.3, Fig. 14) |
| RF LST bias correction | RMSE < 1.0 °C, nRMSE < 3%, rMBE ≈ 0% | before CWSI |
| Satellite CWSI vs field | RMSE = 0.05, nRMSE = 11% | CWSI range 0.18–0.71 at dekadal scale |
| Climate context | ET₀ ≈ 2,150 mm/yr, peaks > 12 mm/day in summer; rainfall ~98 mm (Nov–Mar) | study-area section |
| Irrigation | furrow, 7–12 day intervals | study-area section |
| Landsat cadence | 16-day nominal → **8-day effective** via overlapping rows 165–39 / 166–38 | with Veysi et al. 2023 |

## Load-Bearing Findings for the Thesis

1. **FAO-66 Ky values date from the 1980s and overestimate sugarcane water-stress sensitivity here** (1.2 vs 1.05); the paper joins Dingre & Gorantiwar 2022 and Souza et al. 2015 reporting lower-than-FAO Ky — and explicitly calls for "regional updating to account for contemporary climatic conditions". Our water-accounting / label-severity weighting should use **local Ky**, not FAO defaults.
2. **Early July = peak stress sensitivity** → our temporal XAI should expect maximum water-stress selectivity in early-season timesteps (aligns with Wen 2023's trait-sequencing hypothesis: structural response first).
3. **⚠️ The paper's own confounding warning (§3.4 opening)**: "the CWSI represents crop water stress indirectly through temperature, and factors such as disease, nutrient deficiency, or **salinity stress that also affect canopy temperature could potentially confound interpretation**." — This is a *satellite-study author in our own study region* acknowledging that thermal water-stress signals are salinity-contaminated: a citable justification for our disentanglement design (a CWSI-only pipeline inherits the confound; ours models it explicitly).
4. **Label-severity design input:** Ky varies 0.2–1.63 across the season and space — a fixed field-level stress severity threshold would ignore this; supports dekadal stress curves rather than binary labels.
5. Same-group companion (#09) provides the salinity ground protocol (ECe weekly, 128 wells) this paper lacks — together they cover both axes of our label design.

## Quotable Verbatim

1. "This value is lower than the FAO-66 default of 1.2, indicating that the standard coefficient may prompt over-irrigation without yield benefits." — Abstract, p.1
2. "The analysis further identified early July as the period of peak water stress sensitivity, with Ky values exceeding 1.82." — Abstract, p.1
3. "…factors such as disease, nutrient deficiency, or salinity stress that also affect canopy temperature could potentially confound interpretation." — §3.4, p.(results)
4. "The FAO-66 data, originating from the 1980s, may require revision and regional updating to account for contemporary climatic conditions." — Discussion

## Cautions

- 2023 single season; Ky from 12 field points (calibration/validation), not an independent multi-year test — treat as region-calibrated, not globally validated.
- No salinity measurement in this paper itself (the confound is acknowledged, not modeled).
- Cites #09's group data; don't double-count the two papers' field campaigns as independent evidence.

## Links

- Matrix row: #76 (verified 2026-10-04)
- Feeds 04-Thesis-Design (label strategy: water-accounting severity weighting), lit-review §3.7, G4 (thermal confound motivation)
