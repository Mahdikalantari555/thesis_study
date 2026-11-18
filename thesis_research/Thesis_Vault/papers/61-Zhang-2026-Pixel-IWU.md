# 61 — Pixel-wise Irrigation Water Use from Satellite Soil Moisture + ET (Zhang et al., 2026)

**Full Citation:** Zhang, L., Che, T., Zhang, K., Zheng, D., & Li, X. (2026). A novel framework for pixel-wise estimation of irrigation water use by integrating remote sensing and reanalysis data. *Agricultural Water Management*, *323*, 110077. https://doi.org/10.1016/j.agwat.2025.110077
**DOI:** [10.1016/j.agwat.2025.110077](https://doi.org/10.1016/j.agwat.2025.110077) | Open Access (CC BY-NC-ND) | AWM 323 (2026) 110077 | online 13 Dec 2025
**Status:** ✅ Full read (2026-10-20, extracted text)
**Themes:** #Irrigation #Data-quality #Dataset

---

## What It Does

A physically based, spatially explicit framework for estimating irrigation water use (IWU) by differencing soil-water-balance quantities between natural and irrigated conditions, combining satellite soil moisture and ET against ERA5-Land reanalysis. It produces **1 km** monthly IWU for all of China, 2001–2020, as a weighted ensemble over product combinations. This is **not** a stress-detection method — it is a water-demand / irrigation-intensity **covariate** product (p. 1).

## Key Methodology

- **Study area** — mainland China: ~160 Mha cropland in 2020, ~60% irrigated / 40% rainfed; irrigated area expanded ~18 Mha (~25%) over two decades, ~60% of that expansion in water-scarce regions (p. 3). ⚠️ **Discrepancy:** the matrix label "Arizona analog" is not supported by the PDF — the study area is China; Arizona is paper #62.
- **Two model variants** — a **root-zone soil moisture (RSM)** model (Eq. 3) and a **surface soil moisture (SSM)** model (Eq. 11), both grounded in soil water balance. The irrigated balance is differenced against the natural balance (Eq. 13) to give `Irr = SSM_part + ET_part + D_part` (Eqs. 14–17); drainage follows a power law of relative soil moisture (Brocca et al., 2013) with porosity from a China soil-hydraulic-parameter dataset (pp. 5–6).
- **ET and SM sources** — ET: **MOD16A2GF** (8-day, 500 m) and **PML-V2** (daily, 500 m); SSM: **AMSR-D** (daily, 1 km) and **ERA-CCI-D** (2000–2020, daily, 1 km); reanalysis: **ERA5-Land** (0.01°, monthly; SSM = layer 1 at 0–7 cm, RSM = weighted sum of layers 1–3 at 0.40/0.35/0.25) — all resampled to **1 km** by nearest-neighbour; precipitation from ChinaMet (1 km), PET by Hargreaves (pp. 3–5). RSM under irrigation is itself predicted by a **Random Forest** trained on rainfed conditions (Eqs. 1–2); the satellite–model ET bias term is ≈ −9 and −11 mm/month for MODIS and PML-V2 (p. 6).
- **Calibration / validation** — minimise SSE between estimated and reported annual irrigation depth using prefecture-level IWU reports (**357 prefectures, 2000–2020**, from 31 provincial Water Resources Bureaux); calibrated separately at prefecture / province / subregion scale, MATLAB GlobalSearch repeated 10×; validation on held-out 2010–2020 (p. 7).
- **Ensemble** — 4 members (2 SSM × 2 ET) weighted by summed-squared-error (SSE) or Bayesian Three-Cornered Hat (BTCH) (p. 7). **Benchmark vs RF** — 6 Random Forest models using socioeconomic, climatic, auxiliary and EO predictors, trained on the same reports at matched scales and periods (p. 7).

## Key Findings

- **Model accuracy (p. 8):** RSM-based R² = **0.84**, SSM-based R² = **0.90** (prefecture-level calibration, validated 2010–2020), with systematic **overestimation** (bias +0.10 and +0.24 km³/yr) attributed to improved conveyance efficiency after the early calibration years; coarser calibration (province / subregion) gives R² 0.72–0.80, RMSE 0.55–0.65 km³/yr.
- **vs Random Forest (p. 8):** R² improved by **3–11%** and RMSE reduced by **3–15%** at prefecture-level reports; the margin widens at coarser reference scales, where RF degrades more sharply.
- **Product choice > model choice (p. 8):** swapping the SSM/ET combination moves R² by up to **0.15** and RMSE by up to **0.4 km³/yr**; ESA-CCI-D SSM + MODIS ET performs best.
- **Ensembling (pp. 9–10):** SSE and BTCH both help — R² up by up to 3% (RSM) and 13% (SSM), RMSE down by up to 18% and 28% respectively.
- **Final 1 km China product, 2001–2020 (SSM + SSE ensemble, p. 10):** R² = **0.95**, RMSE = **0.27 km³/yr**, bias 0.07 km³/yr against the calibration reports; against **independent** reports R² = **0.99** (10 basins), **0.93** (21 sub-basins), **0.89** (125 counties), RMSE 0.07–4.91 km³/yr, bias 0.02–3.22 km³/yr. Correlation with existing products IWU-Huang and IWU-Zhang > 0.60; those products are ≤ 0.25° and systematically underestimate (IWU-Cheng in southern China, IWU-Zhang in the northwest, all of them in NE China paddy) (p. 10).
- **Headline water-use numbers (p. 10):** China's IWU rose **339 → 395 km³/yr** over 2001–2020 (mean 360 km³/yr), driven mainly by irrigated-area expansion while interannual variability is controlled by water-use intensity; national average intensity ≈ **425 mm/yr**, declining.
- **Water partitioning (p. 13):** the model attributes **77%** of irrigation water to drainage, **20%** to ET and **3%** to surface soil-moisture storage — a symptom of underestimated ET and of conveyance losses never made explicit.
- **Field vs literature (p. 11):** of 31 recent RS-IWU studies, 47% ET-based, 44% SM-based, only **9%** combined; 47% field/plot scale, 32% basin/district, 20% national/global; published R² spans 0.3–1.0 with most below 0.70.
- **Caveats (p. 13):** not calibration-free (depends on annual regional census IWU); **groundwater contribution to ET is not modelled** — the authors flag this as material "particularly in arid regions"; paddy two-layer physics simplified; satellite ET tends to underestimate over irrigated cropland.

## Relevance to Thesis

**Medium** — background / environmental-covariate material, not a stress-detection method.

- ✅ Supplies a **1 km irrigation-intensity covariate template** in the same water-demand domain as the thesis's Khuzestan sugarcane, and reinforces the physical framing that irrigation *mitigates* drought and heat stress (their own opening argument, p. 1) — i.e. the covariate that separates water stress from non-water stress.
- ✅ Its **product-selection and ensemble findings** (ΔR² up to 0.15 from ET/SSM product swaps; SSE/BTCH ensembles worth +3–13% R² and −18–28% RMSE) are a usable precedent for assembling ET/soil-moisture covariates in the thesis's data-quality section.
- ✅ The protocol — calibrate against administrative IWU reports, then validate on a strictly **independent** report subset at three spatial scales — is a transferable validation-design template for a regional covariate layer.
- ⚠️ 1 km resolution is far coarser than the field-level SITS the thesis classifies; it cannot resolve within-field water-stress gradients and must **not** be used as a label source.
- ⚠️ Arid-transfer caveat: the framework does not model groundwater contribution to ET (p. 13), and Khuzestan is precisely a shallow-aquifer irrigated plain — so the IWU magnitudes will not transfer directly.
- ❌ No stress detection, no salinity, no XAI, no foundation model, no active learning, and no field-scale validation.
- ⚠️ **Matrix correction:** the "Arizona analog" label is wrong for this row — study area is mainland China (Arizona is #62).

## Key Takeaway

The most transferable contribution is **product-selection and ensemble discipline**: which ET and soil-moisture product you pick shifts R² by up to 0.15, and which weighting scheme you use buys another 3–13% R² and up to 28% RMSE reduction. The caveat is that the 1 km IWU field is a coarse regional water-demand covariate, and the framework omits groundwater-fed ET — material in arid irrigated plains.

## Links

- Matrix row: #61
- Related: #62 (companion IWU uncertainty study — same quantity, uncertainty-focused), #76 (Motlagh — Khuzestan Ky / ET accounting, the local water-balance neighbour), #75 (Volta Basin ET–CWSI covariate template)

---

*Linked from: [[Literature-Matrix]]*
