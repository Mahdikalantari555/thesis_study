# Multi-Dimensional Optical Remote Sensing in Agriculture: Spectral, Angular, and Spatial Scaling for Crop Stress Monitoring

**Authors:** Haq, S.I.U., Wang, G., Khan, S.N., Song, C., Ma, C., Zhang, X., Lan, Y.
**Year:** 2025
**Venue:** *Smart Agricultural Technology*, 12, 101583
**DOI / ID:** 10.1016/j.atech.2025.101583
**Local PDF:** `D:\RS\Thesis\thesis_research\papers\72-Haq-2025-MultiDim-Optical-Stress.pdf`
**Type:** systematic review (n = 138)
**Thesis relevance:** High — multi-angle/BRDF dimension missing from Berger 2022

> Note: previously known in `phase1_stress_detection_methods.md` only by Elsevier PII (S2772375525008147); now downloaded and identified.

## Summary
Review of 138 recent studies (2018–2024, 12 major crop types) on crop stress monitoring that integrates **spectral, angular, and spatial** dimensions of optical remote sensing across proximal, UAV, and satellite scales. Covers biotic (disease, pests) and abiotic (drought, nutrient, temperature) stress signatures from chlorophyll degradation (VIS) to water content (SWIR), plus thermal and chlorophyll-fluorescence sensing. Key innovation: emphasis on **multi-angle remote sensing** — BRDF effects reveal stress-induced canopy-structure and leaf-orientation changes invisible to nadir-only observation, and viewing geometry significantly biases NDVI, PRI, and SIF, requiring angular correction. Identifies three gaps: inconsistent angular reflectance modeling across stress types, inadequate sensor calibration protocols, and lack of standardized multi-source/multi-scale integration frameworks. Proposes a hierarchical monitoring architecture with **physics-aware AI** (deep learning + transformers) addressing temporal optimization, spatial integration, and angular standardization — moving crop stress monitoring from reactive management to predictive intervention.

## Methods / Approach
- Systematic review of 138 studies (Scopus, WoS, IEEE Xplore; 2018–2024)
- Stress × spectral-domain mapping across three observation scales
- BRDF/multi-angle analysis of VI and SIF stress signals
- Hierarchical architecture proposal: physics-aware AI, temporal + spatial + angular integration

## Key quantitative results
- 138 studies, 12 crop types, 2018–2024
- Viewing geometry significantly affects NDVI, PRI, SIF stress measurements
- Three named community-wide gaps (angular modeling, calibration, multi-source integration)

## Relevance to thesis
Complements Berger 2022 by adding the **angular/BRDF dimension** — relevant for Khuzestan multi-temporal compositing (viewing-geometry variability is an unmodeled confounder in single-angle time series). The physics-aware-AI proposal aligns with the thesis plan to couple data-driven sequence models with physical stress priors (gs↓, Ts↑, Na⁺↑, chlorophyll↓). Also useful as evidence that operational multi-source integration frameworks remain a recognized community gap (supports thesis framing).

## Gaps / opportunities
- Review-level only; no operational disentanglement of concurrent stresses
- Angular correction in practice requires multi-angle acquisitions — rarely available in HLS-style archives
- Deep learning praised but transformer/Mamba temporal architectures not concretely benchmarked for stress

## Citation (APA 7th)
- Haq, S. I. U., Wang, G., Khan, S. N., Song, C., Ma, C., Zhang, X., & Lan, Y. (2025). Multi-dimensional optical remote sensing in agriculture: Spectral, angular, and spatial scaling for crop stress monitoring. *Smart Agricultural Technology*, *12*, 101583. https://doi.org/10.1016/j.atech.2025.101583

---
*Note written 2026-10-04 from first-page extract. Verify numbers in full PDF before formal proposal use.*
