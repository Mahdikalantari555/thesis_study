# A Review of Remote Sensing Challenges for Food Security with Respect to Salinity and Drought Threats

**Authors:** Wen, W., Timmermans, J., Chen, Q., van Bodegom, P.M.
**Year:** 2021
**Venue:** *Remote Sensing*, 13(1), 6
**DOI / ID:** 10.3390/rs13010006
**Local PDF:** `D:\RS\Thesis\thesis_research\papers\69-Wen-2021-Salinity-Drought-RS-Challenges.pdf`
**Type:** meta-analytic review
**Thesis relevance:** **Highest** — closest review to the thesis core problem (concurrent drought × salinity)

## Summary
Reviews the ability of remote sensing to detect drought and salinity impacts on vegetation indices (VIs) and crop traits. Meta-analysis finds VIs insufficiently accurate (R² 0.02–0.80) to characterize crop health under either stress. Plant functional traits track vegetation processes better and are recommended as monitoring targets. Two critical findings: (a) spectral signals for drought and salinity are inconsistent across studies — both between studies on similar crops and between different crops; (b) the response signals of **joint drought + salinity stress overlap spectrally**, which significantly limits separating the two stresses remotely. Recommends radiative transfer models (RTMs) and multi-sensor frameworks to monitor multiple traits simultaneously.

## Methods / Approach
- Meta-analysis of VI–stress and trait–stress relationships across crops
- Comparison of drought-only vs salinity-only vs combined-stress spectral responses
- Gap analysis → RTM + multi-sensor multi-trait retrieval as the way forward

## Key quantitative results
- VI-based stress characterization: R² 0.02–0.80 (insufficient)
- Combined-stress signals spectrally overlap individual-stress signals
- Inconsistent trait–spectrum relationships across crops and studies

## Relevance to thesis
This is the **gap-analysis paper for the thesis niche**: it explicitly documents that remote sensing had not (as of 2021) monitored drought and salinity simultaneously, and that joint-stress spectral overlap blocks single-index separation. Directly motivates the thesis claim that concurrent water–salinity disentanglement needs multi-trait, temporal, learning-based approaches. Note the thesis frame: this paper stops at RTM+multi-sensor; it does not attempt deep temporal sequence models — the thesis (Mamba + SSL + temporal XAI) occupies exactly the next step.

## Gaps / opportunities
- Explicitly calls for simultaneous multi-trait evaluation — supports the thesis feature/multi-label design
- Spectral overlap of combined stress = the disentanglement problem the thesis addresses
- No ML/DL synthesis — trait retrieval proposals are physics/statistics-based

## Citation (APA 7th)
- Wen, W., Timmermans, J., Chen, Q., & van Bodegom, P. M. (2021). A review of remote sensing challenges for food security with respect to salinity and drought threats. *Remote Sensing*, *13*(1), 6. https://doi.org/10.3390/rs13010006

---
*Note written 2026-10-04 from first-page extract. Verify numbers in full PDF before formal proposal use.*
