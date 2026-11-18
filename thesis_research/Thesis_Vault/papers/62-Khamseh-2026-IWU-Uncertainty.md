# 62 — Uncertainty in Remote-Sensing IWU: ET-Product Resolution Bias (Khamseh & Danesh-Yazdi, 2026)

**Full Citation:** Khamseh, F., & Danesh-Yazdi, M. (2026). Uncertainty and performance of remote sensing-based irrigation water use estimates. *Agricultural Water Management*, *331*, 110444. https://doi.org/10.1016/j.agwat.2026.110444
**DOI:** [10.1016/j.agwat.2026.110444](https://doi.org/10.1016/j.agwat.2026.110444) | Open Access (CC BY-NC-ND) | AWM 331 (2026) 110444 | online 20 May 2026
**Status:** ✅ Full read (2026-10-20, extracted text)
**Themes:** #Irrigation #Data-quality #Thermal

---

## What It Does

Quantifies regional irrigation water use (IWU) in Arizona for 2017 by differencing an **irrigation-free** soil-water-balance simulation of root-zone soil moisture and actual ET against satellite observations, and then measures how far the answer moves with the **spatial resolution of the ET product**. It is explicitly a data-quality / uncertainty study: "how wrong can a water budget be because of a coarse ET product?" (p. 1).

## Key Methodology

- **Residual formulation** — `IWU(t) = IWU_RZSM(t) + IWU_ET(t)` (Eqs. 15–16), where IWU_ET is the ET residual (ET_sat − ET_mod) gated on effective rainfall (Eq. 17) and IWU_RZSM the soil-moisture residual at SMAP resolution (Eq. 18). Runoff and deep-percolation residuals are neglected during the dry irrigation season (≈13% of precipitation converts to R + DP in wet periods) (p. 3).
- **ET products compared** — **OpenET 30 m** (surface-energy-balance ensemble of METRIC, SEBAL, DisALEXI, PT-JPL, SIMS, SSEBop; monthly), **MOD16 500 m** (8-day) and **PML 500 m** (8-day) (p. 1, p. 5, Table 1 p. 6).
- **Other inputs** — SMAP L3 V5 (9 km, 2–3 day; exponential filter converts surface SM to RZSM), Landsat 8 L2 NDVI (30 m, 16-day), NOAA weather stations, MirAD-US irrigated-land map (250 m), USDA Farm and Ranch Irrigation Survey gross IWU, USDA-NASS Cropland Data Layer for root depth, NLDAS soil parameters (pp. 4, 6).
- **Model** — FAO-56 style ET_mod = ET0 × kc × ks, with kc from NDVI and ks from calibrated wilting point / field capacity; ET0 from Penman–Monteith forced by IDW-interpolated NOAA meteorology; wp, fc and curve number calibrated by **MCMC over the non-irrigated season (Oct 2016–Mar 2017)** to avoid irrigation-induced bias; VARS (IVARS-50) sensitivity analysis (p. 3).
- **Uncertainty** — forward **Monte Carlo** with normal per-input errors and a **Nataf transformation** for correlated variables (rainfall ↔ ET) (p. 4).
- **Study area** — Arizona, 2017 water year, March–September peak season; 383 k-ha irrigated land; agriculture takes 74% of state freshwater; >90% of croplands irrigated, **88% flood irrigation**; alfalfa 46% of cropland area, cotton 18%; mean rooting depth 1.27 m; irrigation efficiency 0.60–0.66 over ~88% of croplands; sandy clay loam; the Colorado River supplies ~36% of state water and its flow has fallen 20% in two decades (p. 4, p. 6).

## Key Findings

- **The headline resolution-bias result (p. 11, §3.5):** with OpenET (30 m) the IWU bias is **−16% to −23%**; with **PML (500 m) −55% to −60%** in the abstract and −56% to −60% in the results; with **MOD16 (500 m) −93% to −94%**. Merely **resampling OpenET to 500 m** widens the bias to **−20% to −27%** — the penalty is the *resolution*, not the algorithm.
- **ET magnitude ordering (p. 11):** OpenET estimates ET **36% higher per month** than PML and **69% higher** than MOD16; PML ↔ OpenET r = 0.85, but **MOD16 ↔ OpenET r = −0.09** (no meaningful relationship).
- **Residual decomposition (pp. 9, 12):** **97% of total IWU comes from the ET residual** and only ~3% from soil moisture, because SMAP's 9 km averaging smooths irrigation pulses and dense canopy weakens the L-band signal. Variance decomposition (2017–2023) attributes **87%** of IWU_ET variance to ET_sat and 38% to ET_mod; CV(IWU) = 25% against CV(OpenET ET) = 21%.
- **Water budget (p. 9):** annual gross IWU_ET **4.41 BCM** + IWU_RZSM **0.15 BCM** against a USDA reference of **5.42 BCM**; net IWU_ET mean 634 mm/yr, SD 282 mm/yr, CV 44%.
- **Model fidelity (p. 6):** RZSM_mod vs RZSM_sat over the non-irrigated season — median RMSE **0.011 m³/m³**, R² **0.68**, r **0.95**; calibrated wp 0.078, fc 0.38, CN 75, cross-checked against NLDAS (fc ≈ 0.36, wp = 0.066). Sensitivity: wp 0.6 > fc 0.28 overall (dry-season wp 0.66; in wet months wp falls to 0.46 and CN rises to 0.25).
- **Error-propagation audit (pp. 10–11):** on a non-irrigated control pixel, annual false irrigation is < 5% of mean agricultural IWU; OpenET overestimates ET by 17% in dry months and by 9% (50% spike in August) in urban pixels; desert false-irrigation in August equals 39% of simulated ET; annual false IWU in urban/desert pixels stays < 1% of cropland IWU. ETmod ↔ OpenET correlation in non-irrigated areas is r = 0.80 year-round.
- **Uncertainty budget (pp. 12–14):** IDW rainfall CV 30–40%; FAO-56 ET0 CV 10–15%; NDVI-source differences CV 20–50%; IWU bias −14% to −20% as the rainfall power parameter falls 3 → 0.5; root depth 0.5 → 3 m changes IWU by only CV 0.017 (sensitivity index 0.03; gross IWU 4.53 → 4.27 BCM). In the SEB energy balance, LST is the dominant input (1% ΔLST → up to 1.62 mm/day ΔET), ahead of albedo (0.056) and air temperature (0.02) (p. 12).
- **Recommendation (pp. 14–15):** move beyond coarse-resolution ET for IWU; exploit OpenET's 30 m Landsat-based SEB, and — because OpenET is monthly and US-only — adopt **daily ET products such as Sen-ET (Sentinel-2 + Sentinel-3)** for IWU_ET timing. The paper also proposes classifying a field as *excessively irrigated* when actual IWU exceeds the irrigation water requirement (PET − Peff) (p. 14).
- **Transfer limits (pp. 9, 14):** results hold for **flood irrigation** only (~88% of Arizona cropland); sprinkler and drip produce different ET signatures and were not tested.

## Relevance to Thesis

**Medium** — data-quality and design-rationale material for an arid irrigation remote-sensing study.

- ✅ **Direct design lesson for covariate assembly:** if the thesis builds any ET- or water-balance-derived covariate, the ET product's spatial resolution dominates the error budget — a 500 m ET product biases a residual water budget by −55% to −94%, while a 30 m thermal-SEB product stays within −16% to −23% (p. 11).
- ✅ **Quantitative support for a thermal/SEB (LST-based) covariate design:** OpenET's advantage is traced to LST being the most influential SEB input (1% ΔLST → up to 1.62 mm/day ΔET, p. 12), so a thermal-first covariate is defensible against a cheaper optical or 500 m alternative.
- ✅ **A transferable uncertainty-propagation recipe:** forward Monte Carlo + Nataf for correlated meteorological errors, per-input CVs (rainfall 30–40%, ET0 10–15%, NDVI 20–50%), and an explicit CV(IWU) ≈ 25% envelope to quote when reporting a stress-index confidence band.
- ✅ **Irrigation-system caveat to carry into the thesis:** results are established for flood irrigation, with sprinkler/drip explicitly untested (p. 9, p. 14) — directly relevant to Khuzestan's mixed irrigation systems.
- ⚠️ Single state, single year (Arizona 2017) and no field-level IWU ground truth, so absolute bias figures are not portable; the *relative* ET-resolution effect is the transferable claim. The paper also never tests whether an IWU error propagates into a stress classifier, so propagating ET uncertainty into stress-detection confidence remains unvalidated.
- ❌ No stress detection, no salinity, no XAI, no foundation model, no active learning.
- ⚠️ Minor inconsistency: the abstract gives the PML bias as −55% to −60% while §3.5 gives −56% to −60% (p. 1 vs p. 11).

## Key Takeaway

The single most useful number for the thesis's data-quality section is that **ET-product resolution, not ET-product algorithm, is what breaks residual irrigation budgets** — 30 m OpenET: −16% to −23%; OpenET resampled to 500 m: −20% to −27%; native 500 m PML: −55% to −60%; MOD16: −93% to −94% (p. 11). The honest caveat is that these are Arizona-2017, flood-irrigation-specific figures, so they justify *prioritising* high-resolution thermal ET, not calibrating a bias correction for the thesis's own site.

## Links

- Matrix row: #62
- Related: #61 (companion China-scale IWU framework), #76 (Motlagh — local Khuzestan ET / Ky accounting, same product-choice question), #72 (BRDF / geometry-aware compositing protocol, data-quality companion)

---

*Linked from: [[Literature-Matrix]]*
