# 43 — Soil Salinity Mapping with Sentinel-2 MSI + ML in Arid Xinjiang (Wang et al., 2021)

**Full Citation:** Wang, J., Peng, J., Li, H., Yin, C., Liu, W., Wang, T., & Zhang, H. (2021). Soil salinity mapping using machine learning algorithms with the Sentinel-2 MSI in arid areas, China. *Remote Sensing*, *13*(2), 305. https://doi.org/10.3390/rs13020305
**DOI:** [10.3390/rs13020305](https://doi.org/10.3390/rs13020305) | Open Access (CC BY) | Article no. 305, published 17 January 2021 | Crossref-verified 2026-10-20
**Status:** ✅ Full read (2026-10-20) — all 14 pages of extracted text
**Themes:** #Salinity #Salinity-mapping #Irrigation #Data-quality

---

## What It Does

Maps soil **electrical conductivity (EC)** across the Kongterik Pasture Nature Reserve (KPNR), Aksu Prefecture, Xinjiang, using **Sentinel-2B MSI** bands + derived covariates and three classical ML regressors (SVM, RF, ANN). Ground truth: 160 mixed soil samples (0–20 cm) collected on 14 June 2019, the day of the overpass; features are VIF-screened, the best model produces a salinity class map, and the paper closes with an explicit uncertainty analysis. Closest **salinity-branch analog in an arid irrigated system** in the corpus — though the site is a pasture/halophyte reserve, not a crop plantation.

## Key Methodology

- **Study area (p. 3):** KPNR, northern margin of the Tarim Basin; 6063.84 km²; 922–1207 m a.s.l.; mean annual temp 10.10 °C, precipitation 65.4 mm, evaporation 2300 mm; flat terrain, shallow groundwater, salt accumulation plus irrigation-driven secondary salinization.
- **Sampling (p. 4):** 160 quadrats of 10 m × 10 m, placed along the area's single highway; **five-point method** — soil from 4 corners + centre, **0–20 cm**, mixed into one sample per quadrat; Trimble JUNO GPS (≤ 5 m).
- **Laboratory (p. 4):** moisture from 20.00 g oven-dried at 105 °C ± 2 °C to constant weight; EC from a **1:5 soil-to-water extract** of air-dried soil, measured after filtration. → **Extract EC, not saturated-paste ECe** (values are an order of magnitude above typical ECe).
- **Imagery (p. 4):** Sentinel-2B, 14 June 2019, L1C TOA → Sen2Cor → L1A surface reflectance; 4 bands at 10 m (B2, B3, B4, B8) + 6 at 20 m (B5, B6, B7, B8a, B11, B12); 10 m resampled to 20 m and stacked in SNAP.
- **Predictors (Table 1, p. 5) — 35 covariates:** 10 band reflectances + PC1–PC3 (PCA of the 10 bands) + **tasseled-cap wetness (TCW)** + **DEM** + 15 indices — salinity **NDSI, S1, S2, S3, S5, S6, SI, SI1–SI4**; intensity **Int1, Int2**; vegetation **NDVI, EVI, CRSI, RVI, SAVI, GDVI**.
- **Screening (p. 7–8):** Pearson correlation vs. EC, then **VIF screening (1 < VIF < 10)** for multicollinearity → **18 variables** retained.
- **Split (p. 5):** **Kennard–Stone** 70/30 → 112 modelling / 48 verification (every fourth sample in sampling order held out).
- **Models (p. 5, MATLAB R2016a):** SVM (polynomial kernel, C = 6, ε = 0.1, γ = 2.0); ANN (MLP, 1 hidden layer, 30 nodes); RF (N = 100 trees, K = 34 features/split, depth 10, min child node 5).
- **Metrics (p. 6):** R², RMSE, **RPIQ**, **SEL/SEP**.

## Key Findings

- **EC statistics (Table 2, p. 6):** total n = 160, mean 24.03, min 1.07, max **79.6 dS m⁻¹**, SD 10.70, CV 44.53%; modelling n = 112 (mean 23.86, 1.07–79.6, SD 10.65); verification n = 48 (mean 24.72, 6.32–64.65, SD 10.64, CV 43.04%).
- **Spectral response to salinity is non-monotonic (p. 6–7):** per-band mean reflectance 0.21–0.28 (SD 0.041–0.054) over 6510 random soil pixels; salinized-soil reflectance 0.09–0.35; the *highest*-EC (79.60) and *lowest*-EC (1.07) samples both reflected **more** than intermediate samples — attributed to soil moisture and salt composition.
- **Index-level EC signal is weak (p. 7):** **NDVI, RVI, GDVI, SAVI, EVI, NDSI and B12 all failed the p < 0.05 significance test**; PCA2 and PCA3 gave the highest correlations; TCW correlated significantly but not most strongly; the soil-moisture index correlated poorly.
- **Model accuracy (Table 3, p. 8):** **SVM — verification R² = 0.88, RMSE = 4.89 dS m⁻¹, RPIQ = 1.96, SEL/SEP = 1.11** (modelling R² = 0.71) — the only model meeting the authors' criteria (RPIQ 1.7–2.2; SEL/SEP closest to 1). RF — modelling R² = 0.81 but **verification R² = 0.27**, RMSE 10.61, RPIQ 0.65, SEL/SEP 1.79. ANN — modelling R² = 0.80, **verification R² = 0.57**, RMSE 8.15, RPIQ 1.26, SEL/SEP 1.34.
- **Mapping (p. 9–10):** Schoeneberger et al. (2002) classes — non-saline (0–2), very slightly (2–4), slightly (4–8), moderately (8–16), strongly (>16 dS m⁻¹); strongly saline dominated, salt discharged from irrigated upper alluvial fan salinized the surrounding low areas, abandoned southern farmland showed secondary salinization.
- **Vegetation deliberately not masked (p. 11):** samples were collected *in* vegetated areas and VIs used to model EC under canopy; the authors state that "environmental information reflecting changes in soil properties such as vegetation cover, phenology, and plant growth should be carefully considered."
- **Authors' own uncertainty statement (p. 12):** the 0–20 cm sampled depth may not match what surface spectral variables represent (0–5 or 0–10 cm may be closer); indices are also driven by organic matter, moisture, surface roughness and metal-mineral content; terrain and shadow effects persist; "the inversion capability of a single satellite image is always limited."

### ⚠️ Discrepancies vs. the matrix row (#43) and the task brief — PDF wins

1. **The matrix says "RF on S2 indices … R²≈0.78." The PDF does not support that.** Table 3 (p. 8) gives RF verification R² = **0.27** (its 0.81 is the *modelling* fit); the best model is **SVM** (verification R² = 0.88, RMSE 4.89). The figure **0.783** appears once, in the Discussion (p. 11), as a comparison to Wang et al. (2020)'s MSI model (R² = 0.912, n = 64) and is **not attributed to a specific model**. → Cite "SVM, verification R² = 0.88 (Table 3, p. 8)"; **do not** attribute R² ≈ 0.78 to RF.
2. **There is no salt-vegetation index (SVI) in this paper.** Salinity indices are NDSI, S1, S2, S3, S5, S6, SI, SI1–SI4; vegetation indices NDVI, EVI, CRSI, RVI, SAVI, GDVI (Table 1, p. 5). No combined salt–vegetation index is formulated anywhere.
3. **Internal inconsistency in the paper:** the abstract (p. 1) says the survey "coincided with the transit time of the Sentinel-2**A** satellite", but §2.3 (p. 4) states the data are Sentinel-2**B** for 14 June 2019. Cite as Sentinel-2B.

## Relevance to Thesis

**Medium-High** — the closest arid-irrigated salinity-branch analog, and a methodological counterpoint rather than a method source:

- ✅ Confirms that S2 band + index features carry an EC signal in an **arid, irrigated, salt-affected** oasis — the same environmental setting class as Khuzestan.
- ✅ Supplies a **classical-ML salinity baseline and feature recipe** (10 bands + PCA + TCW + DEM + salinity/VI indices, VIF-screened) to benchmark a RF/LGBM salinity branch against — plus a **cautionary RF result** (modelling R² 0.81 → verification R² 0.27) arguing for spatially aware, multi-year validation rather than random splits.
- ✅ Documents the **surface-vs-root-zone mismatch** explicitly (p. 12), supporting the thesis's use of in-situ ECe at depth rather than surface proxies.
- ⚠️ Transfer conditions: single date, single scene, **no thermal band, no temporal dimension**; the site is a nature reserve with halophyte vegetation, so the signal is partly soil/halophyte, not crop stress.
- ⚠️ Its "EC" is 1:5 soil-water extract (1.07–79.6 dS m⁻¹), **not saturated-paste ECe**; absolute R²/RMSE are not comparable with the ECe-based Khuzestan results in #09 (1.7–8.0 dS/m).
- ❌ No water-stress / CWSI / thermal channel, no concurrent-stress disentanglement, no crop-level stress labels, nothing usable as validation for the mixed-stress classes.

## Key Takeaway

The most valuable artefact is Table 3 (p. 8): **RF looked best on the training split (R² 0.81) and collapsed on the held-out set (R² 0.27) while SVM generalized (verification R² 0.88)** — a direct empirical argument for the thesis's spatially aware, multi-year validation of the salinity branch, and a reminder that the matrix's "RF, R²≈0.78" summary is not what the paper reports.

## Links

- Matrix row: #43
- Related: #46 (Smanov 2026 — cites this paper as its ref. [25] in criticising surface/ECe-calibrated salinity models), #69 (Wen 2021 — zero VI–salinity correlations in the 2005–2020 corpus), #19 (DeepSalt — domain adaptation for salinity), #09 (Khuzestan ECe protocol — saturated paste, 0–90 cm, weekly), #70 / #71 (Wen trilogy — stage-dependent concurrent salinity/drought responses)

---

*Linked from: [[Literature-Matrix]]*
