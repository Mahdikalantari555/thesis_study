# 77 — Sugarcane Health Monitoring With Satellite Spectroscopy and ML: A Review (Waters et al., 2025)

**Full Citation:** Waters, E.K., Chen, C.C.-M., & Rahimi Azghadi, M. (2025). Sugarcane health monitoring with satellite spectroscopy and machine learning: A review. *Computers and Electronics in Agriculture*, 229, 109686.
**DOI:** [10.1016/j.compag.2024.109686](https://doi.org/10.1016/j.compag.2024.109686) | Preprint read here (arXiv:2404.16844; published version verified via arXiv API 2026-10-04 — cite the CEA 2025 version)
**Status:** ✅ Full read (2026-10-04)
**Themes:** #Sugarcane #Band-selection #Review #Gap-anchor

---

## What It Does

The only recent review dedicated to **satellite spectroscopy + ML for sugarcane health monitoring**: collates the literature (Table 1: health condition × spectroscopy category × satellite × time-series use × ML algorithm × accuracy, plus two comparator crops) and catalogs sugarcane-relevant vegetation indices (Table 2: moisture, leaf-pigment, leaf-structure indices).

## Verified Findings That Carry Thesis Weight

1. **Salinity: ZERO mentions in the entire review.** The study-crop's own review literature does not cover salinity at all (verified by full-text search) — alongside Berger (salinity = 5% of 96 stress studies), Paul (~2/163), and Wen 2021 (zero VI–salinity correlations), this completes a four-way documentation that salinity is the neglected axis of sugarcane/stress EO.
2. **Time series: essentially unused.** In Table 1, only ~one study is marked as using time series; the temporal section (§6.3) covers phenology/morphology (Landsat-7 phenological separability, Gers 2004; flowering/lodging effects) but no SITS classification methodology. → per-field multi-temporal modeling is absent from the sugarcane literature the review represents.
3. **DL named as future work (verbatim bullet):** "Neural networks and deep learning have shown unparalleled performance in various applications. Future research can develop new neural networks for sugarcane health monitoring and compare them with…" — i.e., the reviewed corpus has not yet done it (CNN appear in a handful of rows; no transformer/Mamba/SSL; "self-supervised" and "Mamba": zero hits).
4. **Moisture indices flagged (verbatim):** "the best result… for sugarcane was found based on vegetation indices that accentuate variation in the moisture content of vegetation, thereby indicating that **other moisture-based vegetation indices should be heavily considered in future studies**" (§5, before Table 2). → Direct support for including SWIR-based water indices (NDWI/SIWSI-type) in our Landsat feature set.
5. **BRDF/viewing-geometry caveat, sugarcane-specific:** only one reviewed health study applied BRDF correction; "Future research should ensure spectral images are centred at a consistent location and viewing angle. Additionally, the BRDF correction model should be considered to handle the anisotropy factor." (§6). → protocol requirement for our 2013–2025 Landsat compositing.
6. **Landsat presence in sugarcane studies:** Landsat 7/8 appear for phenology (Gers 2004), field characterization (Som-ard et al. 2021, 25 fields, Thailand), and herbicide/disease detection (Vargas et al. 2016, Landsat 8 + handheld spectrometer, 79.8/85.5%) — but no stress-type disentanglement, no thermal stress studies.

## Implications for the Thesis

- **Band selection input:** adopt their Table 2 moisture/pigment/structure index list, filtered to Landsat 8/9 capability (no red-edge): NDVI/SAVI/EVI (structure+chlorophyll), **NDWI/SIWSI-family (moisture — their explicit "heavily consider" recommendation)**, pigment proxies limited to VIS/NIR. Their finding justifies SWIR water features even without red-edge.
- **Positioning:** "the sugarcane-specific review (Waters et al. 2025) catalogs no salinity study, ~one time-series study, and names deep learning as *future* work — the four pillars of this thesis (multi-temporal per-field modeling, concurrent stress incl. salinity, deep SSL architectures, XAI) are each absent from the reviewed state of the art."
- **Protocol:** consistent viewing geometry + BRDF consideration for our compositing (their §6 recommendation).

## Quotable Verbatim (with locations)

1. "This review intends to critically assess the current literature regarding health condition monitoring in sugarcane with the use of satellite spectroscopy." — §1
2. "…the best performing method for sugarcane was found based on vegetation indices that accentuate variation in the moisture content of vegetation, thereby indicating that other moisture-based vegetation indices should be heavily considered in future studies." — §5
3. "Future research should ensure spectral images are centred at a consistent location and viewing angle. Additionally, the BRDF correction model should be considered to handle the anisotropy factor." — §6
4. "Neural networks and deep learning have shown unparalleled performance in various applications. Future research can develop new neural networks for sugarcane health monitoring and compare them with…" — Future-directions bullet list

## Cautions

- Read from the arXiv preprint; the published CEA version may differ slightly in pagination — quote by section, not page, until the published PDF is fetched.
- Review's study table includes 2 non-sugarcane comparator crops; don't over-count.
- The review covers "health" broadly (disease-heavy); water stress is a minority topic and salinity absent — phrase our coverage claims accordingly.

## Links

- Matrix row: #77 (metadata fixed to published version 2026-10-04)
- Feeds lit-review §3.7 (band-selection input) and G4 salinity-neglect evidence chain
