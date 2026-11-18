# Deep learning for plant stress detection: A comprehensive review of technologies, challenges, and future directions

**Authors:** Paul, N., Sun, G. C., Horvath, D., & Sun, X.  
**Year:** 2025  
**Venue:** Computers and Electronics in Agriculture, 229, 109734  
**DOI / arXiv:** 10.1016/j.compag.2024.109734  
**Local PDF:** 1-s2.0-S0168169924011256-main.pdf  
**Type:** review  
**Thesis relevance:** HIGH  

## Summary
This review surveys deep-learning pipelines for plant stress detection, covering the full workflow from data acquisition and preprocessing through classification, detection, and segmentation. It notes that most training to date relies on RGB imagery; self-supervised learning (SSL) and few-shot learning (FSL) may outperform transfer learning (TL) under severe label scarcity; and multimodal fusion (e.g., imagery plus temperature/humidity) improves stress assessment. Abiotic stressors addressed include drought, salinity, flooding, extreme temperature, and heavy metals/nutrient deficiencies.

## Methods / Architecture
- Review of DL pipelines for plant stress: acquisition → preprocessing → classification / detection / segmentation.
- Data modalities discussed: predominantly RGB; multimodal (image + temperature/humidity) highlighted as beneficial.
- Learning paradigms: transfer learning, self-supervised learning, few-shot learning.
- Stress taxonomy focus: abiotic (drought, salinity, flooding, extreme temperature, metals/nutrients).

## Key quantitative results
- This is a review paper; no single headline experimental result is provided in the first-page extract.
- Key qualitative synthesis: SSL/FSL may beat TL under label scarcity; multimodal inputs help.

## Relevance to thesis
Foundational Phase-1 framing for an EO foundation-model + active-learning crop-stress thesis: establishes the DL stress-detection pipeline, the label-scarcity problem that motivates AL, and the abiotic stress types relevant to arid environments.

## Gaps / opportunities
- Few works integrate EO foundation models with active learning for arid-region stress.
- Multimodal fusion beyond RGB (SAR, hyperspectral, reanalysis covariates) remains underexplored for stress.
- Opportunity: position the thesis as closing the label-scarcity gap via SSL/FSL + AL on EO-FM embeddings.

## Citation (APA 7th)
Paul, N., Sun, G. C., Horvath, D., & Sun, X. (2025). Deep learning for plant stress detection: A comprehensive review of technologies, challenges, and future directions. *Computers and Electronics in Agriculture*, *229*, 109734. https://doi.org/10.1016/j.compag.2024.109734

---
*Note written 2026-09-10 from first-page extract. Verify numbers in full PDF before formal proposal use.*
