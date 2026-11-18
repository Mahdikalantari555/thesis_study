# Remote Sensing-Based Machine Learning and Deep Learning for Agriculture and Forestry: Yield Estimation, Land-Cover Mapping, and Plant Stress — A Systematic Review (2020–2025)

**Authors:** Gracia Rojas, D.A., Gómez Díaz, H.J., Gil Herrera, R. de J.
**Year:** 2026
**Venue:** *Remote Sensing Applications: Society and Environment*, 44, 102279
**DOI / ID:** 10.1016/j.rsase.2026.102279
**Local PDF:** `D:\RS\Thesis\thesis_research\papers\74-GraciaRojas-2026-ML-DL-AgriForestry-SLR.pdf`
**Type:** systematic literature review (n = 105)
**Thesis relevance:** Medium-high — methods taxonomy + reporting-practice evidence

## Summary
Systematic review of 105 research articles (2020–2025, stratified sampling across IEEE Xplore, Scopus, WoS, ScienceDirect) on RS+ML/DL for agricultural and forestry monitoring. Findings: CNNs dominate land-cover mapping and segmentation; LSTMs and Transformers are widely used for time-series tasks such as yield estimation and plant-stress monitoring; classical ML (Random Forest, Gradient-Boosted Trees, SVM) remains competitive when feature engineering is robust. Multimodal fusion (optical–SAR) preserves structural information under cloud cover, but climate-stratified comparisons are scarce. In forestry, HSI–LiDAR with 3D-CNN improves species discrimination. Hybrid crop-AI models (biomass/LAI coupled to crop simulators) improve physiological consistency and early yield prediction. Persistent limitations: spatiotemporal validation, uncertainty quantification, and standardized evaluation metrics.

## Methods / Approach
- PRISMA-style SLR: 105 articles, proportional stratified sampling, 4 repositories
- Three-phase structured extraction protocol (algorithms, sensors, applications, metrics)
- Synthesis by task family (mapping, segmentation, time series, yield, stress)

## Key quantitative results
- 105 articles (2020–2025)
- CNN → segmentation/mapping; LSTM/Transformer → time series (yield, stress)
- Classical ML (RF/GBDT/SVM) still competitive with robust features
- Named deficits: spatiotemporal validation, uncertainty quantification, metric standardization

## Relevance to thesis
Independent evidence for two thesis design choices: (1) sequence architectures (LSTM/Transformer family) are the accepted tool for RS stress/yield time series — supports the Mamba-style temporal backbone choice as the natural next step; (2) the field lacks standardized validation and uncertainty reporting — the thesis can differentiate by explicit cross-year validation and uncertainty outputs. Also useful for related-work taxonomy (optical–SAR fusion, hybrid crop-AI models).

## Gaps / opportunities
- Stress monitoring covered as a task family, not disentangled by stress type
- Climate-stratified comparison scarcity = transferability gap the thesis can address
- No foundation-model / SSL-for-stress synthesis depth

## Citation (APA 7th)
- Gracia Rojas, D. A., Gómez Díaz, H. J., & Gil Herrera, R. de J. (2026). Remote sensing-based machine learning and deep learning for agriculture and forestry: Yield estimation, land-cover mapping, and plant stress — A systematic review (2020–2025). *Remote Sensing Applications: Society and Environment*, *44*, 102279. https://doi.org/10.1016/j.rsase.2026.102279

---
*Note written 2026-10-04 from first-page extract. Verify numbers in full PDF before formal proposal use.*
