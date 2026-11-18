# 79 — Estimation of Agricultural Vegetation Water Stress via Feature-Optimized RS + Ensemble ML (Elbeltagi et al., 2026)

**Full Citation:** Elbeltagi, A., Srivastava, A., & Alsumaiei, A. A. (2026). Estimation of agricultural vegetation water stress using feature-optimized remote sensing and ensemble machine learning. *Smart Agricultural Technology*, *15*, 102536. https://doi.org/10.1016/j.atech.2026.102536
**DOI:** [10.1016/j.atech.2026.102536](https://doi.org/10.1016/j.atech.2026.102536) | Received 4 Apr 2026; revised 19 Aug 2026; accepted 2 Sep 2026; published online 2 Sep 2026 | Elsevier BV, CC BY-NC-ND 4.0
**Status:** ✅ Full read (2026-10-24)
**Themes:** #EVI #MODIS #FeatureSelection #RandomForest #Irrigation #NileDelta

---

## What It Does

A **controlled, single-site benchmark** for estimating agricultural vegetation water stress (represented by **MODIS EVI**) in an intensively irrigated semi-arid delta (Dakahliyah Governorate, Egypt's Nile Delta), built around a **feature-optimized pipeline**: **Best Subset Regression (BSR)** over five MODIS indicators (LAI, Fpar, ESI, NDVI, LST) selects a parsimonious predictor set, which is then fed to four ML architectures (MLP, Random Subspace, Regression by Discretization, Random Forest) plus XGBoost/CatBoost/linear baselines, under identical training (2018–2023), independent testing (2024–2025) and 5-fold CV. **Random Forest after BSR wins**: CC = 0.9943, MAE = 0.0063, RMSE = 0.0161 on the 2024–2025 test period. The headline scientific claim is that NDVI alone carries most of the linear EVI information (r = 0.934; standardized coefficient 0.935) and LAI adds a small but significant residual (0.017), while Fpar, ESI and LST are linearly redundant once NDVI+LAI are in.

## Study Area & Data

- **Site:** Dakahliyah (Ad Daqahliyah) Governorate, northern Nile Delta — one of Egypt's principal crop-producing governorates; Mediterranean semi-arid climate; ~24 °C mean air temp, ~16 °C min, wind 3.8–5.2 m/s; ~75 % of rain in Oct–Jan, peak Dec–Jan.
- **Sensor stack — all MODIS, 2018–2025, governorate-level monthly aggregates** (pixels not modeled individually):
  - **MOD13Q1** NDVI & EVI — 250 m, 16-day composites.
  - **MOD15A2H** LAI & Fpar — 500 m, 8-day.
  - **MOD11A2** LST — 1 km, 8-day.
  - **MOD16A2** ET & PET — 500 m, 8-day → ESI = ET/PET (lower = more stress).
- **Scale factors applied:** NDVI/EVI ×0.0001; LAI ×0.1 (m² m⁻²); Fpar ×0.01 (%); LST ×0.02 → K → °C; ET/PET ×0.1 (mm per 8-day). QA layers used to mask cloud/cloud-shadow/aerosol/snow/low-confidence pixels; bilinear resampling to common grid; monthly governorate means.
- **Split:** train 2018–2023, independent test 2024–2025, 5-fold CV.

## Key Methodology

- **BSR** evaluates all 2⁵ combinations of {LAI, Fpar, ESI, NDVI, LST} using adjusted R², AIC, BIC, Mallows' Cp, plus VIF multicollinearity screening; variables normalized first.
- **ML models (WEKA):** MLP (lr 0.3, momentum 0.2, 500 epochs, 3 hidden layers 7/8/9 neurons, batch 100); Random Subspace (REPTree base, 10 iters, subspace 0.5, seed 1); RF (100 trees, seed 1, bag size 100 %); Regression by Discretization (RandomTree, equal-frequency 10 bins). Plus linear baselines (univariate NDVI; multivariate NDVI+LAI) and XGBoost (300 iters, depth 4, lr 0.05, subsample 0.8) / CatBoost (300 iters, depth 6, lr 0.05) in Python.
- **Metrics:** CC, MAE, RMSE, RAE, RRSE.

## Key Findings

- **Correlations with EVI:** NDVI r = 0.934; LAI/Fpar/ESI/LST weak; inter-predictor |r| ≤ 0.109 (low multicollinearity).
- **Standardized multiple-regression coefficients (Table 3):** NDVI 0.935 (t = 198.9, p < 0.0001, 95 % CI 0.925–0.944); LAI 0.017 (p ≈ 0.000, CI 0.008–0.027); Fpar, ESI, LST ≈ 0 with CIs spanning both signs and non-significant p-values (> 0.5 for ESI/LST; ~0.96 for Fpar). Hence BSR retains NDVI (+ LAI) and discards Fpar/ESI/LST.
- **Pre-BSR (test period):** RD strongest accuracy; RF degraded more than expected; RS low slope (0.4768).
- **Post-BSR (test period):** RF largest gain R² 0.9161 → 0.9886, slope 0.8957 → 0.9894; RS R² 0.9414 → 0.9738, slope 0.4768 → 0.9666; RD R² 0.9549 → 0.9603; MLP R² 0.8831 → 0.8818 (no benefit, slope 0.8807 → 0.8477). Training: RS R² 0.9588 → 0.9757; RF R² 0.9886 → 0.9871 (slight drop) but slope → 1; MLP/RD slight drops.
- **Best model (RF post-BSR, test 2024–2025):** CC = 0.9943, MAE = 0.0063, RMSE = 0.0161.
- **Time series (Fig. 7):** RF tracks seasonal greening/senescence; post-BSR amplitude biases at peaks/troughs reduced; pre-BSR over-smooths high-frequency variability.

## Relevance to Thesis

**Medium** — a clean, same-crop-family (irrigated agriculture) **baseline benchmark** for the related-work and methods sections:
- ✅ **Direct comparator for the thesis' stress representation.** The paper treats EVI as the stress proxy and shows it is almost entirely linearly predictable from NDVI (r = 0.934) in a semi-arid irrigated delta — i.e., in such settings EVI is a redundant proxy and the real signal lives in the *residuals* (LAI, phenology, thermal). This motivates the thesis' choice of **CWSI/thermal + temporal structure** over static greenness indices, and supports the gap claim that greenness-only proxies are insufficient for water-stress disentanglement (cf. #76 Motlagh: salinity confounds canopy temperature).
- ✅ **Feature-selection precedent.** BSR + VIF as a parsimony/interpretability step is directly transferable; the finding that Fpar/ESI/LST drop out of the *linear* model but may still carry nonlinear/interaction signal (Fig. 6) is the exact argument for keeping them in a nonlinear temporal encoder rather than discarding them at the feature-selection stage.
- ✅ **Validation template.** Year-based independent test (2024–2025) + 5-fold CV + CC/MAE/RMSE/RAE/RRSE is a ready-made evaluation protocol the thesis can mirror for its own ablations.
- ✅ **Negative result for MLP** (no benefit from BSR; range compression) reinforces the thesis' preference for sequence models (Mamba/SSL) over plain MLPs on SITS.

## Gaps vs. Our Thesis

| Gap | Impact | Our Fix |
|-----|--------|---------|
| **Static, single-site, governorate-level aggregation** (no spatial/temporal structure; monthly means; no pixel-level modelling) | No SITS learning; cannot capture phenology or stress dynamics | Per-pixel temporal encoder (SITSMamba-style) over Landsat SITS |
| **Greenness proxy (EVI) as the target**, not CWSI/ET/salinity | Measures vigor, not water stress; salinity confound unaddressed | Stress-aware targets (CWSI, thermal anomalies, salinity indices) |
| **No thermal exploitation** (LST dropped as linearly redundant) | Discards the strongest water-stress signal (canopy temperature) | Keep LST/thermal as first-class channels in the encoder |
| **No sequence/temporal modelling, no SSL, no XAI** | Cannot attribute which timesteps/bands drive stress | CNN-Mamba + SSL pretext + XAI (SHAP/attention) |
| **MODIS only (250 m–1 km)** | Too coarse for field-scale sugarcane management | Landsat 30 m (fused with MODIS for temporal density) |
| **Single governorate, no cross-site/cross-year generalization test** | Unknown transferability | Cross-year + cross-site validation on Khuzestan sugarcane |
| **No uncertainty quantification** | Over-confident point estimates | Predictive intervals / MC-dropout in the ensemble |

## Notes

- The paper is a 2026 Elsevier article (Smart Agricultural Technology) with a 2026 acceptance date — very recent; treat as a fresh benchmark rather than an established result. Citation count unknown at time of noting.
- Authors: Elbeltagi (Mansoura University, Egypt), Srivastava (IIT Madras), Alsumaiei (Kuwait University) — hydrology/RS group; recurring co-authors on drought/ML papers (refs 41–42 are their own prior work on discretization regression).
- Useful for the thesis' **"related work → vegetation-index modeling"** subsection as a representative, well-controlled 2026 data point, and as a **methodology template** for the ablation/evaluation protocol.