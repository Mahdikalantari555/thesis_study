# Monitoring the Combined Effects of Drought and Salinity Stress on Crops Using Remote Sensing in the Netherlands

**Authors:** Wen, W., Timmermans, J., Chen, Q., van Bodegom, P.M.
**Year:** 2022
**Venue:** *Hydrology and Earth System Sciences*, 26, 4537–4552
**DOI / ID:** 10.5194/hess-26-4537-2022
**Local PDF:** `D:\RS\Thesis\thesis_research\papers\70-Wen-2022-Drought-Salinity-Combined-NL.pdf`
**Type:** empirical (large-scale validation)
**Thesis relevance:** **Highest** — closest empirical template for concurrent water–salinity stress mapping

## Summary
Provides a new monitoring approach using remote sensing to evaluate joint drought + salinity impacts on crop functional traits at large spatial scale (138.74 km², Netherlands). From Sentinel-2 observations, five functional traits are derived for maize and potato: LAI, FAPAR, FVC, leaf chlorophyll content (Cab), and leaf water content (Cw). One-way and two-way ANOVAs quantify individual and combined stress effects on seasonal trait dynamics. Both stresses significantly affect traits (R² 0.326–0.796), with stronger sensitivity to drought than salinity. Co-occurring stresses show exacerbating effects, but impact level depends strongly on the moment in the growing season; LAI, FAPAR, and FVC drop most under severe drought.

## Methods / Approach
- Sentinel-2 multi-temporal trait retrieval (RTM-based, five traits)
- One-way + two-way ANOVA across stress classes (drought, salinity, combined)
- Seasonal-dynamics analysis (stress × phenology interaction)

## Key quantitative results
- R² 0.326–0.796 for stress → trait relationships
- Drought sensitivity > salinity sensitivity for both crops
- Combined-stress effects exacerbated but strongly stage-dependent
- Traits most affected under severe drought: LAI, FAPAR, FVC

## Relevance to thesis
The closest published empirical design to the thesis core: multi-trait retrieval from a free satellite archive, explicit combined-stress classes, and interaction statistics. Direct design lessons for Khuzestan sugarcane: (1) trait-level labels (incl. Cw, Cab) beat single-index classes; (2) stress effects are phenology-dependent → temporal models need growth-stage context; (3) two-way interaction framing maps to the thesis mixed/multi-label stress targets. Crucially, the analysis is **statistical (ANOVA), not deep learning** — no sequence model, no SSL, no disentanglement network — leaving the thesis methodological niche intact.

## Gaps / opportunities
- Statistical attribution only; no predictive model, no XAI
- Sentinel-2 only (no thermal/SAR fusion)
- Temperate climate (NL) — arid irrigated analog (Khuzestan) untested
- No sugarcane; maize/potato physiology differs in salt tolerance

## Citation (APA 7th)
- Wen, W., Timmermans, J., Chen, Q., & van Bodegom, P. M. (2022). Monitoring the combined effects of drought and salinity stress on crops using remote sensing in the Netherlands. *Hydrology and Earth System Sciences*, *26*, 4537–4552. https://doi.org/10.5194/hess-26-4537-2022

---
*Note written 2026-10-04 from first-page extract. Verify numbers in full PDF before formal proposal use.*
