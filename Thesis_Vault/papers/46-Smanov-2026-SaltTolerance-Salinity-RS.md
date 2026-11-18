# 46 — Crop Salt Tolerance × Remote-Sensing Salinity Mapping: A Review (Smanov et al., 2026)

**Full Citation:** Smanov, Z., Abuduwaili, J., Samat, A., Samarkhanov, K., Laiskhanov, S., Kulymbet, K., Yershibul, A., Duisekov, S., Massakbayeva, A., & Sharapkhanova, Z. (2026). Role of crop salt tolerance in enhancing remote sensing-based soil salinity mapping across irrigated agroecosystems: A review. *Remote Sensing*, *18*(9), 1420. https://doi.org/10.3390/rs18091420
**DOI:** [10.3390/rs18091420](https://doi.org/10.3390/rs18091420) | Open Access (CC BY) | Published 3 May 2026 | Academic editor: Mohammadmehdi Saberioon | 11 authors (Al-Farabi Kazakh National University; CAS Xinjiang Institute of Ecology and Geography; ENU) | Crossref-verified 2026-10-20
**Status:** ✅ Full read (2026-10-20) — pp. 1–10 in full, plus §3.4 (crop physiology / salt tolerance), §3.5 (knowledge gaps), §4 (conclusions)
**Themes:** #Salinity #Salinity-mapping #Review #Stress-physiology

---

## What It Does

PRISMA-2020 systematic review + bibliometric + thematic synthesis of how **crop salt tolerance** is (or is not) embedded in remote-sensing soil-salinity mapping for irrigated agroecosystems (58 Scopus studies, 1994–2024). Central claim: RS salinity models are calibrated against **bulk ECe** and treat vegetation as a proxy or as noise, whereas crop salt tolerance is a genuine **mediating variable** in the soil–plant–spectral continuum; ignoring it produces *systematic, directional* bias that breaks transferability across heterogeneous irrigated mosaics. This is the paper that turns "our salinity branch has confounders" into a citable, mechanistic argument.

## Corpus & Scope

- **Protocol (p. 4):** PRISMA 2020 — pre-defined questions, inclusion/exclusion criteria, **independent double filtering**, data-extraction methodology, defined review period.
- **Database (p. 4):** **Scopus only**; no additional registers or secondary databases. Window **1 Jan 1994 – 31 Dec 2024**, run in **TITLE-ABS-KEY**.
- **Boolean strategy (Table 1, p. 4):** four dimensions ANDed — (i) soil salinity/degradation, (ii) irrigated agriculture & water management, (iii) RS & geospatial tech (Sentinel-2, Landsat, SMOS, NDVI, "salinity index", hyperspectral), (iv) **crop salt tolerance** (wheat, rice, barley, cotton, tomato, halophytes, "crop-specific salinity response"). English and Chinese articles only.
- **PRISMA flow (p. 5, Fig. 1):** 71 records → 1 excluded (no abstract) → **12 full texts unretrievable** → **58 studies** in the final synthesis.
- **Bibliometrics (p. 5, p. 8):** VOSviewer v1.6.20, association-strength normalization; keyword co-occurrence network of **157 terms in 17 clusters**; temporal overlay map.
- **Thematic coding (Table 2, p. 10):** soil-based RS salinity mapping **25 (43.10%)**, crop physiological response **12 (20.69%)**, integrated crop–salinity–RS models **10 (17.24%)**, irrigation/hydro-management **11 (18.97%)**; each domain split into 1994–2007 / 2008–2015 / 2016–2019 / 2020–2024.
- **Publication dynamics (p. 7–8):** ≤ 1 article/yr 1994–2005; 1–3/yr 2006–2015; **peak 9 publications in 2022**; 2020–2024 = largest share; citation peaks ~218 (2007) and ~436 (2021).
- **Global framing (p. 2):** salinity affects ~**1 billion hectares ≈ 20% of all irrigated land**.

## Key Findings

- **The mediation mechanism (§3.4, p. 19–20; §3.4.1, p. 20):** "In intensively cultivated landscapes, **RS rarely observes salinity directly; rather, it detects the surface or canopy manifestation of salinity** under specific physiological and phenological conditions." Identical root-zone salinity gives divergent VI trajectories depending on crop type, developmental stage and adaptive capacity → "the mapping function linking reflectance features to soil salinity is **not universal but crop-dependent**", and crop tolerance is "a **structural determinant** of spectral salinity expression" (p. 19–20).
- **Threshold-vs-proportional failure mode (§3.4.2, p. 21):** agronomic tolerance is a **two-parameter structure** — threshold ECe below which yield reduction is negligible, plus a yield-decline slope beyond it (Maas & Hoffman 1977; Grieve et al. 2012). RS models instead assume canopy reflectance "varies **continuously and proportionally** with salinity intensity across crops", and ECe "functions solely as a **calibration target** rather than as a physiological constraint". Consequence: "models may misinterpret crop resilience as low salinity or, conversely, amplify early stress in sensitive crops as severe salinity."
- **Directional bias (§3.4, p. 20; §3.5.1, p. 24):** in mixed mosaics salinity is **under-estimated** under tolerant crops that keep green canopies and **over-estimated** under sensitive crops showing early stress — amplified when vegetation indices are the primary predictors.
- **The three variables RS salinity models ignore — the core threats-to-validity for Khuzestan:**
  1. **Ion composition / salt chemistry (§3.4.3, p. 22; §3.5.4, p. 27):** bulk ECe does not differentiate chloride-, sulfate-, carbonate- or sodic-dominated salinity; chloride toxicity, carbonate/bicarbonate-driven pH and nutrient availability, and sodium-induced dispersion act through different pathways. "A species classified as moderately tolerant under sulfate-dominated salinity may exhibit **greater sensitivity under chloride or sodic conditions**" (p. 22). Most models "predominantly rely on bulk salinity proxies … while rarely accounting for ion-specific toxicity and salt chemistry" (p. 3).
  2. **Root-zone vs. surface salinity (§3.4.3, p. 22; §3.5.2, p. 25):** plant response is governed by the **active rooting depth**, not the surface; "surface layers appear weakly saline while subsurface horizons contain elevated salt concentrations", and temporary post-evaporation salt crusts "may exaggerate salinity severity without reflecting persistent subsurface conditions" (p. 22, p. 25).
  3. **Phenology / stage-dependent tolerance (§3.4.1, p. 20; §3.5.1, p. 25; §3.5.3, p. 26):** "Sensitivity thresholds vary across germination, vegetative growth, flowering, and grain-filling stages" (p. 26); single-date or seasonally averaged imagery "may obscure transient stress signals or confound salinity effects with normal phenological transitions — for example, declines in NDVI during senescence may be misinterpreted as salinity-induced stress" (p. 26). Varietal differences within a species also shift leaf optics (p. 26).
- **Structural evidence from the keyword network (p. 9):** crop/physiology descriptors (salt stress, stomatal behaviour, canopy resistance, halophyte cover) form "smaller and less centrally positioned subnetworks" — "**physiological salt tolerance has not yet become a fully integrated component of mainstream salinity mapping frameworks**", and "**crops are predominantly treated as spectral proxies rather than as mechanistic biophysiological mediators of salinity response**".
- **Crop-response studies rarely invert salinity (§3.2, p. 11):** they "interpret salinity as an external driver and **rarely reconstruct soil salinity gradients directly from vegetation response**".
- **Proposed remedies matching the thesis design (§3.4.4, p. 22–23):** stratified calibration by **crop identity and phenological stage**; **hierarchical / multi-level models** sharing spectral–salinity structure while accommodating crop-specific parameters; tolerance thresholds embedded as **priors or constrained calibration**; coupling spectral time series with **irrigation data, groundwater depth, soil-moisture proxies and terrain attributes**; multi-temporal analysis "aligned with phenological windows that maximize sensitivity to stress manifestation **rather than relying on arbitrary acquisition dates**" (p. 23); hydrochemical proxies (sodicity indicators, soil texture classes, hydrogeological context) for indirect ion differentiation; and **uncertainty quantification** — prediction intervals, spatial uncertainty surfaces, sensitivity analyses.
- **Explicit XAI recommendation (p. 29):** "**Explainable artificial intelligence (XAI)** approaches may further enhance transparency by clarifying how physiological and environmental variables influence model outputs"; **hybrid modelling** combining process models (salinity transport, crop growth) with ML is named a critical frontier (p. 29).
- **Conclusions (§4, p. 29–30):** crop salt tolerance "functions as a **spectral mediator** of salinity signals rather than as a peripheral agronomic parameter"; failing to incorporate it "introduces structural bias, reduces model transferability, and limits agronomic interpretability"; three overarching needs — physiological-tolerance integration, subsurface/hydrological salinity representation, mechanistically informed soil–plant–spectral frameworks.

### ⚠️ Discrepancies and scope limits vs. the intake note (A8)

- **A8's "Kazakh and Xinjiang irrigated analogs transfer conceptually to Khuzestan" is the note author's inference, not the paper's claim.** The review names **no** study region Xinjiang, **no** Iran/Khuzestan and **no sugarcane**; Xinjiang and Kazakhstan appear only in author affiliations and one reference. The search-string crop set is wheat, rice, barley, cotton, tomato and halophytes (Table 1, p. 4).
- A8's other metadata all check out: 58 Scopus studies, 1994–2024, surface-oriented bulk-ECe dominance, ~1 billion ha / 20% of irrigated land, soil–plant–water–spectral proposal.
- **Bibliographic limit to state if cited as "systematic":** one database (Scopus only — authors state at p. 29: "We did not include other indexing bases such as Web of Science due to time constraints and the risk of increasing the article's length"), 12 of 71 full texts unretrievable, and the four-domain classification is **qualitative thematic coding by the authors** (Table 2 note, p. 10) rather than an independent coding protocol.
- **Typesetting artifact:** the published PDF carries a stray editorial leftover "**Bulleted lists look like this:**" at the head of §3.5.1 (p. 24) — not content.

## Relevance to Thesis

**High** — the strongest available framing reference for the salinity branch and for the thesis's threats-to-validity section:

- ✅ Supplies a **mechanistic, citable account of why** concurrent water and salt stress are hard to separate from spectral data: crop salt tolerance mediates the spectral–ECe relationship, so a canopy signal is a *soil × crop × stage* composite rather than a soil reading (p. 19–20) — the physiology-side counterpart to the sensor-side argument in #44 and #68.
- ✅ Names exactly the variables most RS salinity models ignore — **ion composition, root-zone vs. surface salinity, and phenological stage** — with the *directional* bias each introduces. For Khuzestan this argues for modelling a **stress class** rather than regressing a single index to EC, and for sampling ECe at depth.
- ✅ Endorses the thesis's own design choices as best practice: phenology-windowed multi-temporal analysis, crop/phenology-stratified calibration, explicit uncertainty reporting (p. 23) — plus a direct call for **XAI** to make physiological/environmental drivers legible (p. 29).
- ✅ Provides the physiological justification for a **crop-specific, multi-phase, soil–plant–water** framing of the salinity branch, and for probabilistic/soft labels under co-occurrence.
- ⚠️ Transfer condition: **no sugarcane, no Iran** — the specific tolerance thresholds are not transplantable to Khuzestan sugarcane; the *argument structure* transfers, the constants do not. Phrase as "the review's general argument", never as "Smanov et al. report for sugarcane".
- ⚠️ Citing caveat: single-database review, 12 unretrievable full texts, author-coded thematic classification — do not present it as a meta-analysis with effect sizes.
- ❌ No accuracy benchmark, no label protocol, no dataset, no operational salinity model of its own — a framing/gap paper, not a method source.

## Key Takeaway

Use it as the physiological justification for the thesis's central claim, with one honest caveat: it establishes that "spectral signal = soil salinity" is false because crop salt tolerance, root-zone distribution, ion composition and phenology all mediate it (p. 19–22) — but it never mentions sugarcane or Iran, so it supports the **argument**, not any transferable threshold.

## Links

- Matrix row: #46
- Related: #43 (Wang 2021 — cited here as ref. [25], the surface/ECe-calibrated paradigm this review critiques), #69 (Wen 2021 — VI–salinity accuracy ceiling 0.02 ≤ R² ≤ 0.80), #70 / #71 (Wen trilogy — stage-dependent, trait-level concurrent salinity/drought responses), #08 (Paciolla 2025 — salinity from satellite LAI), #19 (DeepSalt), #27 (Shi 2022 — long-term salinity dynamics), #44 (Berger 2022 — sensor-side counterpart)

---

*Linked from: [[Literature-Matrix]]*
