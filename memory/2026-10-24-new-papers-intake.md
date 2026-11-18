# 2026-10-24 — New paper intake (single paper)

## Added

- **#79 Elbeltagi et al. (2026)** — "Estimation of agricultural vegetation water stress using feature-optimized remote sensing and ensemble machine learning", *Smart Agricultural Technology* 15:102536, DOI 10.1016/j.atech.2026.102536. MODIS 2018–2025, Dakahliyah (Nile Delta); BSR selects NDVI(+LAI) over {LAI,Fpar,ESI,NDVI,LST}; RF post-BSR best CC=0.9943, MAE=0.0063, RMSE=0.0161 on 2024–2025 test.
  - PDF copied to `papers/79-Elbeltagi-2026-Vegetation-Water-Stress-EVI-FeatureOptimized-ML.pdf`.
  - Vault note: `Thesis_Vault/papers/79-Elbeltagi-2026-Vegetation-Water-Stress-EVI-FeatureOptimized-ML.md`.
  - Matrix row 79 added; header last-updated bumped to 2026-10-24.

## Notes

- Source PDF supplied by user in `D:/RS/Thesis/New_papers/1-s2.0-S2772375526007616-main.pdf`.
- Relevance: Medium — same-crop-family (irrigated agriculture) baseline benchmark, feature-selection precedent (BSR+VIF), validation protocol template (year-based independent test + 5-fold CV), and a negative result for MLP that supports the thesis' preference for sequence models. Greenness-only (EVI) proxy reinforces the gap claim that thermal/CWSI + temporal structure is needed.