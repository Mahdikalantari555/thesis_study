# 68 — A Review of Crop Water Stress Assessment Using Remote Sensing (Ahmad, Alvino & Marino, 2021)

**Full Citation:** Ahmad, U., Alvino, A., & Marino, S. (2021). A review of crop water stress assessment using remote sensing. *Remote Sensing*, *13*(20), 4155. https://doi.org/10.3390/rs13204155
**DOI:** [10.3390/rs13204155](https://doi.org/10.3390/rs13204155) | Open Access (CC BY) | Published 17 October 2021 | Academic editors: Abdelghani Chehbouni, Salah Er-Raki & Wenquan Zhu | Crossref-verified 2026-10-20
**Status:** ✅ Full read (2026-10-20) — pp. 1–16 read (proxy chain, ET, SIF, all sensor sections) plus §11 Future Directions and §12 Conclusions
**Themes:** #CWSI #Thermal #Review #Review-methods

---

## What It Does

**Critical (narrative) review** of crop water stress (CWS) assessment with remote sensing, in two layers: the **measurable stress-proxy chain** — relative water content (RWC) → equivalent water thickness (EWT) → soil moisture; then **process-level indicators** — evapotranspiration and sun-induced chlorophyll fluorescence (SIF); and finally a **sensor-technology taxonomy** — optical, thermometric, land-surface temperature, multispectral (spaceborne and airborne), hyperspectral, LiDAR — each with its own failure mode. Closes with future directions (ML forecasting from ground sensor networks) and a summary trade-off table. For the thesis it is the **water-branch sensor-taxonomy backbone**.

## Key Methodology

- **Review type (p. 1–3):** narrative critical review — **no PRISMA protocol, no search string, no inclusion/exclusion criteria, no corpus count, no year window**. Stated aims (p. 3): (i) summarise the current scope of CWS detection using RS, (ii) present real-world examples and relevant methods, (iii) classify common features of CWS used in detection.
- **Proxy chain (§2, p. 3–4):** RWC = (FW − DW)/(TW − DW); EWT = (FW − DW)/LAI. The review stresses the **RWC↔soil-moisture interdependency** — RWC is *over-estimated* at high soil moisture and *under-estimated* at low soil moisture, and "little research has been conducted on their effects on crop water stress" (p. 4). De Jong et al. report correlation **0.70** between leaf water content and spectral indices at 970 nm (p. 4).
- **Sensor taxonomy (§§5–10, p. 9–16)** with concrete instruments: thermometric cooled/uncooled IR and the **HSI3000** FPA sensor (8–14 µm, 160 × 120 px, IFOV 1.3 mrad, FOV 20° × 15°, thermal-conductance sensitivity 0.15 °C, p. 10); **AIRPHEN** six-camera multispectral (450/530/560/675/730/850 nm, 10 nm spectral resolution, 1280 × 960 px, 1 Hz, 8 mm lens, p. 12); spaceborne multispectral (Landsat, SPOT-5/TAKE-5, GeoEye, WorldView/QuickBird, Sentinel-1, ALOS-2 PALSAR, p. 13); airborne multispectral (**Optech Titan** 532–1550 nm; **Riegl VQ-1560i-DW** 532–1064 nm, p. 13–14); hyperspectral (p. 14–15); LiDAR (3-D canopy, LAI/LAD/AGB, p. 15–16); soil moisture via SMAP/SMOS (p. 4–6).
- **SIF treatment (§4, p. 8–9):** passive vs. active retrieval; **FLD** (Fraunhofer line depth); spaceborne sensors TROPOMI, OCO, GOME-2, SCIAMACHY, GOSAT; ESA **FLEX** (2023 mission); SIF magnitude 1.0–3.5% of shortwave energy; retrieval lines 650–800 nm at sub-nanometer resolution 760.5–687.5 nm.
- **LST treatment (§7, p. 11–12):** hot/cold-pixel energy-balance framing; emissivity is the dominant LST error source.

## Key Findings

- **The seven-family sensor taxonomy and its documented failure modes** (the backbone the thesis needs):
  1. **Optical** (§5, p. 9–10): greenness/senescence-based; stress diagnosis is confounded because "various stress factors impose similar effects on crops" (p. 10).
  2. **Thermometric** (§6, p. 10–11): canopy temperature; warns that pixel sampling "might be comprised" of dead leaves, trunk or soil, producing "non-realistic data or major errors"; recommends fusing thermal with NIR/visible "to exclude the non-leaf products from all samples" (p. 11).
  3. **Land surface temperature** (§7, p. 11–12): hot/cold-pixel energy balance; "The inclusion of a soil emissivity analysis results in a considerable **overestimation of LST**" (p. 12); the full retrieval chain (atmospheric correction, radiometric analysis, emissivity management, cloud removal) is "complex methods" (p. 12).
  4. **Multispectral — spaceborne & airborne** (§8, p. 12–14); airborne is called "currently … the most reliable multispectral remote-sensing equipment" (p. 13).
  5. **Hyperspectral** (§9, p. 14–15): "rarely studied"; three named barriers — high cost, "low and minor spectral emissivity … which provides non-significant data", and low chance of detecting minor crop changes (p. 15); missing dedicated satellite missions named (Landsat LSTM, HyspIRI, HiTeSEM, p. 15).
  6. **LiDAR** (§10, p. 15–16): "less developed"; "inherent faults in the procedure, vulnerability, and inefficiency in acquiring physiological traits"; "will need to be linked with another system" (p. 16).
  7. **Soil moisture / microwave** (§2, p. 4–6): SMAP/SMOS L-band, near-surface 0–5 cm, 25–40 km / 2–3 d, root-zone (top 1 m) via data assimilation; Sentinel-1 and ALOS-2 PALSAR at 10 m; older systems' 14-day revisit called "not efficient" (p. 5).
- **Index families actually reviewed:** the taxonomy is organised by **sensor, not by index**. Named indices: **CWSI** (Idso et al. — "normalizing the stress-degree-day parameter", p. 2; Khorsand et al. report leaf- vs. canopy-scale CWS values of **0.37 and 0.15** with a regression-baseline model, p. 2), the **water deficit index (WDI)** with the **NGRDI** companion (spatial resolution 0.25 m, p. 11), plus RWC, EWT, NDVI, SMAP/SMOS soil-moisture products, ET/energy-balance families (SEBAL, METRIC, GLEAM, ECOSTRESS) and SIF (p. 7–9). ⚠️ **TVDI, VDI and NDI are *not* reviewed here** — a full-text search returns no substantive treatment; the TVDI-vs-CWSI comparison lives in #37.
- **Secondary quantitative anchors (all attributed to the cited primary studies):** thermal CWSI ranges 0–0.68 (Romero-Trigueros et al.) and 0.02–0.71 (Akkuzu et al.), p. 7; halving irrigation gave ETc at 70–35% of original with "the particular crop water stress index at **0.4–0.6**" (Sun et al.; Shellie et al.), p. 7; fully irrigated wheat had CWS **0.2** at maturity (Gerhards et al.), p. 7; VPD 1.21–1.31 with r² = 0.68 for low-stress crops (López-López et al.), p. 7; seasonal reference ET 252.4 mm vs. crop ET 194.3 mm (Marino et al.), p. 7; LST method accuracy **1 °C** (Nugraha et al., p. 11); emissivity 0.157 (SD 0.227) bare soil vs. 0.905 (SD 0.111) full vegetation, max dLST 1.0 K (Heinemann et al., p. 12); UAV LST RMSE 0.68 °C on crop and 0.45 °C on grass (Malbéteau et al., p. 12); C-band backscatter RMSE 0.89 / 0.24 / 0.31 mm day⁻¹ for Sentinel-1 / Landsat-8 / combined (p. 12–13); CWS classification precision **83–99%** across three stress stages (p. 16).
- **Summary trade-off table (Table 2, p. 17):** thermal sensor — 1–16 days, 30 m–1 km, "limited commercial production"; optical — 12 days, 10–30 m, "limited data transmission"; soil-moisture sensor — 2–3 days, 20–40 km, "expensive".
- **The review's own identified gaps:**
  - *Sensing* — hyperspectral cost / low emissivity / low sensitivity to minor changes; LiDAR immaturity; missing dedicated satellite missions; "the hardware and software still need to be significantly improved" for thermal analysis against soil-based measurements (p. 11, p. 15–16).
  - *Scale* — "the methods for leaf water content estimation are overly time-consuming and are not considered efficient for large-scale spatial analysis" (p. 4).
  - *Exploitation* — "spectral bands (infrared, thermal, and multispectral) have **not been fully exploited**" (p. 16).
  - *Modelling* — ML is framed narrowly as **ANN-based forecasting from ground sensor networks** (ANN + infrared thermometers, the ARS-pivot system), not satellite time-series modelling (p. 16–17).
  - *Single-stress scope* — "salinity" occurs only in "Soil Moisture and Ocean Salinity (SMOS)" and one reference title; salt co-stress is never treated.
  - *Currency* — October 2021: no foundation models, no self-supervised learning, no Mamba/SSM sequence models. Deep learning appears only as an aid to SIF interpretation (p. 8–9) and in the reference list.

### ⚠️ Verification of the authorship correction and the issue number

- **Authorship confirmed from the PDF (p. 1): "Uzair Ahmad, Arturo Alvino and Stefano Marino"**, all at the Department of Agricultural, Environmental and Food Sciences (DAEFS), University of Molise, Campobasso, Italy. The repo's earlier "Grill et al." attribution was wrong; the correction to **Ahmad, Alvino & Marino** is confirmed.
- **Issue number:** the PDF's own citation line reads "Remote Sens. 2021, 13, 4155" (no issue), and **Crossref reports issue 20** for this DOI (published 2021-10-17). The matrix row (#68 → "13(16)") and the A9 intake note ("13(21)") are **both** wrong → correct citation is *Remote Sensing*, *13*(20), 4155.

### Reading caution on the extracted text

The extracted PDF text contains **duplicated pre-publication ("FOR PEER REVIEW") blocks** — §5 and §8 are each printed twice. All `p. n` references here use the **final published pagination** markers embedded in the extract (p. 1–17), not the peer-review draft numbering.

## Relevance to Thesis

**High** — the water-branch sensor-taxonomy backbone and a citable statement of the *limits* of thermal-only water-stress inference:

- ✅ Provides the canonical, peer-reviewed **sensor taxonomy** that lets the thesis justify a **multi-sensor** feature set — thermal (thermometric + LST), optical/multispectral, and the SWIR/moisture group — each with a named failure mode. Exactly the "per trait group" protocol needed for feature design and the XAI checklist (complementing #39, #42).
- ✅ Directly supports the **emissivity and ancillary-data argument**: LST accuracy is dominated by emissivity handling (p. 12) and thermal pixels are easily contaminated by soil/background (p. 11) — both justify an ML bias-correction of ground Tc (cf. #24) and per-field masking/QC.
- ✅ Supplies the **empirical CWSI value bands** the thesis can cite as context for its own Khuzestan triggers — 0.4–0.6 under half irrigation, 0.2 for fully irrigated wheat, thermal ranges 0–0.68 and 0.02–0.71 (p. 7) — which bracket the local triggers in #09/#10 (0.30–0.45) and give a defensible cross-check.
- ✅ "Spectral bands … have not been fully exploited" (p. 16) and the thermal+fusion recommendation (p. 11) are citable support for a multi-sensor thermal/optical design and for the claim that fusion improves cause discrimination.
- ⚠️ Methodological caveat: a **narrative critical review with no systematic protocol** — no search strategy, no corpus, no year window, no inclusion criteria, no risk-of-bias appraisal. Cite it for taxonomy and for individual reviewed studies' numbers (attributed to the original source); do **not** use it for any "the literature shows…" frequency or prevalence claim. Every quantitative value in it is secondary.
- ⚠️ Currency: October 2021 — predates SSL, foundation models and SSM/Mamba sequence models entirely, which is itself citable evidence that label-efficient temporal architectures were absent from the water-stress canon.
- ❌ No salinity co-stress treatment, no salinity-aware indices, no label protocol, no accuracy benchmark, no datasets, no label-free or active-learning component.

## Key Takeaway

Cite it for the **sensor taxonomy and its failure modes** — the seven families (optical / thermometric / LST / multispectral / hyperspectral / LiDAR / soil-moisture) plus the specific caveats (emissivity-dominated LST error, soil-pixel contamination of thermal indices, hyperspectral cost and low emissivity, LiDAR immaturity) — while treating it strictly as a narrative review: every number in it belongs to a cited primary study, and its salinity blind spot and 2021 vintage are exactly the openings the thesis exploits.

## Links

- Matrix row: #68 (authorship corrected 2026-10-04 from "Grill et al."; **issue number corrected here to 20**)
- Related: #39 (Maes & Steppe 2012 — ground-thermal CWSI canon), #42 (Gerhards 2019 — TIR physics; single-index CWSI fails under co-stress), #24 (ML bias correction of satellite CWSI — emissivity/ground-Tc pipeline), #25 (Sentinel-2 MSI vs Landsat thermal CWSI), #09 / #10 / #76 (Khuzestan local CWSI values and Ky derivation), #37 (Bai 2017 — TVDI vs CWSI, the index comparison this review omits), #15 (Ahmad 2025 EigenCL — SSL stress detection, absent from this canon)

---

*Linked from: [[Literature-Matrix]]*
