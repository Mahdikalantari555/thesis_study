# 78 — Remote Sensing + ML for Crop Water Stress: A Critical Review (Virnodkar et al., 2020)

**Full Citation:** Virnodkar, S. S., Pachghare, V. K., Patil, V. C., & Jha, S. K. (2020). Remote sensing and machine learning for crop water stress determination in various crops: A critical review. *Precision Agriculture*, *21*(5), 1121–1155. https://doi.org/10.1007/s11119-020-09711-9
**DOI:** [10.1007/s11119-020-09711-9](https://doi.org/10.1007/s11119-020-09711-9) | Published 17 Feb 2020 | No intake note exists for this slot — note built from the PDF alone
**Status:** ✅ Full read (2026-10-20)
**Themes:** #CWSI #Review #Thermal #Irrigation

---

## What It Does

A **critical review** of crop water stress (CWS) determination using **remote sensing (RS) + machine learning (ML)**, organised as a three-layer taxonomy: (1) field measurement-based methods (soil water measurement, plant responses), (2) RS-based methods (spectral indices, infrared thermometry & CWSI, evapotranspiration models), and (3) the ML algorithms applied on top (SVM, RF, XGBoost, rotation forest, oblique RF, ANN). It closes with a per-crop summary figure (Fig. 7) and future directions.

## Corpus & Scope

- **Narrative critical review, not systematic**: "based on a detailed study of the literature published in the main remote sensing journals" (p. 5). No PRISMA, no search string, no database list, **no reported corpus size (n)** — cite as a narrative synthesis with qualitative gap claims only. Coverage: wheat, cotton, maize, sugarcane, grapevine, olive orchards, eggplant, "other crops"; EO indices, canopy temperature, LST, ET.
- ⚠️ **Explicitly pre-deep-learning.** Full-text search of the extracted PDF returns **zero hits** for CNN, Transformer, LSTM, convolution, deep learning, self-supervision, foundation model or Mamba; the single "Sentinel" hit is inside a reference title (p. 34). The surveyed toolbox is classical ML on engineered indices and canopy temperature — a clean **pre-2020 evolution anchor** for the water-stress related-work section, to be described as such rather than as current state of the art.

## Key Methodology

- **Field measurement layer** (pp. 5–6, Table 1): soil-water methods (TDR, FDR, neutron probe, tensiometer, gamma attenuation, gypsum sensor, gravimetric, soil-water balance) and plant-response methods (stomatal/canopy conductance, leaf & pre-dawn leaf water potential, **stem water potential Ψstem**, sap flow).
- **RS layer** (pp. 11–14): *direct* water indices — WI, NDWI, WABI-1/2/3, MDWI, MSI; *indirect* — NDVI, MSAVI, GNDVI, PRI, TCARI, TCARI/OSAVI, NDRE, REIP and ~20 more (Tables 2–3). CWSI physics: empirical CWSI of Idso et al. (1981) / Jackson et al. (1977) with wet and dry baselines from VPD/VPG (Eq. 1); **normalised CWSI** of Jones (2013) with T_wet / T_dry (Eq. 2); **LST-based CWSI = (Ts − T_cold)/(T_hot − T_cold)** from hot/cold pixels, satellite data only (Eq. 3, Veysi et al. 2017). ET layer: SEBAL, METRIC, Penman–Monteith, Priestley–Taylor.
- **ML layer** (pp. 14–18): SVM (margin/OSH, kernel trick, small-sample strength), RF (bagging, out-of-bag error, MDA/MDG variable importance), XGBoost, rotation forest, oblique RF, ANN.
- **Synthesis artefacts**: Figs. 4–5 frequency histograms of direct vs indirect water-sensitive indices used across studies; Fig. 6 ANN usage; Fig. 7 per-crop × method matrix (sugarcane, grapevine, wheat, cotton, maize, olive, eggplant, other × CWSI, spectral indices, regression, ensemble learning, ANN, SVM, evolutionary algorithms) (pp. 23, 27–28).

## Key Findings

- **CWSI is the benchmark EO indicator.** "EO-based CWSI was suggested to be the best indicator of water stress in agricultural crops, in contrast with other VIs and WIs at local and regional scales" (p. 29); "the CWSI produces better results than other conventional and RF-based VI methods" (p. 24), and it quantifies stress **24–48 h before visual detection** (p. 23, citing Kacira et al. 2002). Three computable forms with different data demands (pp. 11–13): empirical (needs VPD/VPG baselines), normalised (Jones 2013, UAV TIR), and **satellite-only hot/cold-pixel CWSI** with no ground ancillary data.
- **Two canonical drawbacks of canopy-temperature CWSI** (p. 12, Cohen et al. 2005): hard to separate canopy temperature from soil background at handheld/airborne spatial resolution; varying atmospheric conditions complicate normalisation. The non-stress baseline varies crop-to-crop and climate-zone-to-climate-zone (p. 12); the upper/lower baselines are crop- and region-specific (p. 28).
- **Sugarcane precedents** (the thesis crop): Veysi et al. (2017) computed satellite-only hot/cold-pixel CWSI for **sugarcane** (May–September) without ground ancillary data and found **VWC negatively related to CWSI with R² = 0.42–0.78** (8 Landsat 8 images) (p. 24); Brunini & Turco (2016) found the sugarcane infrared water-stress index varies with **slope and exposure**, with ideal irrigation timing shifting by growth phase (tillering, growth, maturation) across a 2.0–5.0 °C band (p. 19); Abdel-Rahman & Ahmed (2008) used Landsat TM NIR, SWIR and a DMSV sensor to detect sugarcane water content (p. 19).
- **VI performance is crop- and study-specific, not transferable** (Tables 2–3, pp. 19–22): TCARI/OSAVI corn **R² = 0.98**, GNDVI cotton 0.9484, weighted NDVI cotton 0.883, WI vineyard 0.95 — against NDRE grapevines 0.05, MCARI2 0.00, MSAVI 0.00–0.25.
- **ML benchmarks in water stress (2020 state of the art)**: Berni et al. (2009a), olive — UAV thermal + airborne hyperspectral → CWSI vs LWP **R² = 0.82**, vs canopy conductance **R² = 0.91** (p. 24). Poblete et al. (2017), drip-irrigated Carmenère vineyard — ANN on UAV multispectral bands → Ψstem **R² = 0.56–0.87**, MAE 0.1 MPa, RMSE 0.12 MPa, RE −9.1 % (p. 26). Loggenberg et al. (2018), Shiraz vineyard hyperspectral — RF test accuracy **83.3 % (KHAT = 0.67)** over all 176 bands and over an 18-band subset; XGBoost **78.3 %** / **80.0 %** (p. 26). Hassan-Esfahani et al. (2015) — GA + ML over Landsat + weather + field measurements, with a water-allocation optimisation module feeding a soil-water-balance forecaster, used **20 % less water** on alfalfa and oats (p. 25). Xu et al. (2018) — 1-km monthly mean air temperature over the Tibetan Plateau from 11 MODIS/topographic/SRTM variables with 10 ML algorithms (cubist best) → an **auxiliary Ta dataset to improve CWSI computation** (p. 27).
- **Identified gaps** (pp. 26–30): **ML applied to CWSI itself is barely explored** — "only a few research studies have been carried out to date that have investigated the role of state-of-the-art machine learning techniques to estimate the upper and lower stress and well-watered threshold of temperature required by CWSI calculations. Therefore, there is much scope for ML algorithms in estimating these parameters" (p. 28). SVM and RF are "rarely applied for determining water status, unlike ANN" (p. 26); rotation forest and oblique RF had **never been evaluated for water stress determination** (pp. 29–30). Adoption barriers: cost of "cognitive solutions", need for open-source platforms, high computational-power requirements (p. 29). **Midday stem water potential is the most used validation target** for remotely detecting systems, and IRT canopy temperature "has moved towards becoming a benchmark technique for ground truth information" (p. 29). **Absent entirely**: sequence/temporal SITS modelling, deep learning, self-supervision, foundation models, uncertainty quantification, salinity.

## Relevance to Thesis

**Medium** — the pre-2020 evolution anchor for the water-stress related-work section; it frames the gap rather than supplying the method:
- ✅ Establishes the **"before" picture**: as of 2020 the entire surveyed ML toolbox for crop water stress was classical (SVM, RF, XGBoost, ANN) on engineered VIs and canopy temperature, with **no sequence model, no self-supervision, no foundation model** — a clean baseline to contrast with the thesis' temporal encoder and SSL design.
- ✅ Names the **exact seam the thesis occupies**: ML has barely been used to estimate CWSI upper/lower baselines (p. 28), and rotation/oblique RF were never evaluated for water stress (pp. 29–30) — the review itself calls this "much scope".
- ✅ Supplies the **physics and validation anchors**: CWSI as the best EO indicator (p. 29); the satellite-only hot/cold-pixel formulation needing no ground ancillary data (p. 13); the sugarcane precedents (Veysi et al. 2017 VWC–CWSI R² = 0.42–0.78; Brunini & Turco 2016 slope/exposure and growth-phase dependence).
- ⚠️ **Non-systematic and unquantified**: no PRISMA, no search strategy, no corpus size, no explicit inclusion criteria — its gap statements are qualitative expert judgement, and the tabulated R² values are single-study, single-crop numbers that must not be pooled across crops/years.
- ❌ Provides no multi-temporal/SITS modelling, no deep learning, no salinity dimension, no uncertainty quantification and no cross-year validation design — it cannot support any modern method claim, only the historical baseline.

## Key Takeaway

Use it explicitly as the **pre-2020 anchor**: the review's own conclusion is that ML for crop water stress was still classical, index-based and single-date, and it names estimating CWSI baselines with ML as an open problem — the precise seam the thesis' multi-temporal encoder, learned representations and timestep-level XAI occupy. Cite it for the physics, the validation targets (Ψstem, IRT canopy temperature) and the sugarcane precedents; do not cite its numbers as benchmarks, and do not let it stand for the current state of the art (contrast #74 and #73).

## Links

- Matrix row: #78
- Related: #73 (modern UAV CWSI/CEWT ML benchmarks — the "after" of this anchor), #74 (2020–2025 taxonomy: LSTM/Transformer now the accepted time-series family), #75 (satellite LST–NDVI CWSI over 24 years), #09 / #10 / #13 / #24 (CWSI physics cluster)

---

*Linked from: [[Literature-Matrix]]*
