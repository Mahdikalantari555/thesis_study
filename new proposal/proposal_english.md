# Thesis Proposal — English

**Title:** Crop Stress Detection in Sugarcane Fields Using Satellite Image Time Series  
**Persian Title:** تشخیص تنش گیاهی در مزارع نیشکر با استفاده از سری زمانی تصاویر ماهواره‌ای  
**Level:** MSc Thesis  
**Department:** Remote Sensing and Geoinformatics  
**University:** Shahid Beheshti University  
**Study Area:** Amirkabir Agro-Industrial Unit, Khuzestan Province, Iran  
**Sensor:** Landsat 7/8/9 (L2), 2013–2025  
**Temporal Coverage:** 430 recorded dates; valid dates and temporal distribution to be verified  
**Unit of Analysis:** Farm per date or time window  
**Classes:** Healthy | Water-Only Stress | Salinity-Only Stress | Mixed Stress  

---

## 1. Problem Statement

Plant stress can affect vegetation status and crop growth trends. Remote sensing enables monitoring of spatial and temporal vegetation changes at large scale; however, converting satellite observations into reliable stress-status detection still requires an appropriate method and credible result evaluation.

This research investigates the possibility of detecting plant stress status in sugarcane farms using satellite image time series. The main focus is on evaluating and comparing different methods for detecting stressed vs. non-stressed conditions at farm scale. At this stage, determining the specific type or cause of stress is not the definitive goal of the research.

---

## 2. Main Objective

To evaluate the possibility of detecting plant stress status in sugarcane farms using satellite image time series and to compare the performance of different methods.

---

## 3. Sub-Objectives

1. Prepare and quality-control remote sensing time-series data at farm scale.
2. Investigate the capability of spectral and temporal features for detecting plant stress status.
3. Compare the performance of several selected methods using a fair evaluation design.
4. Examine the stability of method performance over time and identify detection limitations.

---

## 4. Main Research Question

Can plant stress status be detected in sugarcane farms using satellite image time series, and can the performance of different methods be compared credibly?

---

## 5. Initial Scope of Research

- **Study area:** Amirkabir Agro-Industrial Unit, Khuzestan Province, Iran.
- **Temporal data:** 430 recorded dates; the number of valid dates and their temporal distribution must be verified.
- **Unit of analysis:** Farm at each date or time window.
- **Farm area:** [To be completed after data review.]
- **Sensors, input variables, and final methods:** [To be determined after data review and validation feasibility.]

---

## 6. Important Limitation of the Research

Stress detection must be evaluated based on a clear operational definition and credible evidence. If sufficient independent data to determine stress status are not available, the scope of claims or problem framing must be revised. Research results alone will not constitute a basis for definitive attribution of stress cause.

---

## 7. Future Development Path

If the first phase succeeds and sufficient independent evidence is available, the research may be extended to differentiate probable stress types, including water stress and salinity stress. This extension is not a requirement of the initial version of the research.

---

## 8. Literature Review (20 Key Resources)

The literature review is organized as a matrix in `literature_matrix.md` and draws on 20 resources most relevant to this topic. Each entry specifies:

- The exact research problem addressed.
- Whether stress was detected directly or only vegetation status was monitored.
- Whether single-date or time-series data were used.
- The unit of analysis (pixel, field parcel, or farm).
- The source of labels and validation data.
- How evaluation was performed and its limitations.

The purpose is not to pre-claim that no similar research exists. Rather, we identify which parts of the problem remain insufficiently solved and which parts our data can answer.

Key findings from the literature:

- The Wen et al. trilogy (2021–2023) is the closest precedent for satellite-based concurrent drought–salinity monitoring, but it is statistical/descriptive (ANOVA only), contains no machine learning, no per-field stress-type disentanglement, no arid irrigated sugarcane, and no explainability.
- Berger et al. (2022) document that no concept exists for integrated multi-spectral differentiation of crop stress types, and salinity represents only 5% of reviewed studies.
- Paul et al. (2025) confirm that SSL for stress is limited to proximal/leaf studies; Mamba/SSM is absent from 163 reviewed studies.
- Motlagh et al. (2026) provide the local baseline at the target site: independent test R² = 0.821 for sugarcane yield prediction using CWSI and salinity at Amirkabir, Khuzestan.
- STS-NET (Dalal et al., 2026) is the closest competitor: self-supervised 3D-CAE for sugarcane water/nitrogen stress, but without salinity, Mamba, XAI, multi-year data, or moderate-resolution satellite input.

---

## 9. Methodology (Outline)

1. **Data preparation:** Landsat 7/8/9 Level-2 collection 2013–2025; cloud masking; 16-day compositing; gap-filling; raw bands + LST + vegetation indices.
2. **Labeling:** Expert labels (50–100 fields) plus proxy labels from CWSI thresholds and ECe salinity maps where available; soft/mixture labels preferred over hard classes.
3. **Modeling:** CNN-Mamba temporal encoder with self-supervised pre-training (Barlow Twins) on the full unlabeled archive; fine-tuning into four stress classes.
4. **Explainability:** Timestep-level SHAP and temporal Grad-CAM, validated against plant physiology (Angon et al., 2022; Maes & Steppe, 2012; Tardieu et al., 2018).
5. **Evaluation:** Leave-one-year-out cross-year validation; uncertainty reporting; comparison against RF/XGBoost index baselines and STS-NET-style 3D-CAE; baseline to beat: Motlagh test R² = 0.821.

---

## 10. Expected Contributions

1. A predictive, per-field model for detecting stressed vs. non-stressed sugarcane conditions from a 12-year Landsat archive.
2. Comparison of multiple methods under a fair evaluation design at the target site.
3. Timestep-level, physiologically validated explanations of stress predictions.
4. Documentation of detection limitations and performance stability over time.
