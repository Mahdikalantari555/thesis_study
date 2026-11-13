# Temporal Data Explainability in Remote Sensing for Agriculture: A Systematic Review

- **Full citation**: Zheng, B., Liang, B., Liang, S., & Chen, F. (2026). "Temporal Data Explainability in Remote Sensing for Agriculture: A Systematic Review." SSRN preprint (Data Science Institute, University of Technology Sydney). Systematic Literature Review (SLR); no DOI stated in the text file.

- **Problem & setting**: First systematic review at the triple intersection of temporal data, remote sensing, and explainable AI (XAI) in agriculture. Three research questions: (RQ1) how temporal RS data are utilized/represented in agriculture; (RQ2) which methods discover temporal patterns; (RQ3) what information is explained with XAI and how effectively. Covers 2020+ literature across UAV, MODIS, Landsat, Sentinel, and proximal/other sensors.

- **Method** (review methodology): Systematic Literature Review. Databases: Web of Science (query: temporal AND (remote sensing|sentinel|landsat|modis|UAV) AND agriculture AND (explainable|interpretable|XAI|feature importance)) and Google Scholar. Screening: 140 WoS + 3,080 GS hits -> year (>=2020) and English filters -> 114 + 2,030 -> citation thresholds (>=25 WoS, >=50 GS) -> 38 + 55 -> deduplication and relevance filtering -> 82 papers for detailed review. Analyses: data source distribution, input representations (multi-spectral bands, VIs, climate variables, soil properties, topography), preprocessing methods, model families, temporal-pattern-analysis strategies, and a post-hoc-XAI taxonomy (model-agnostic: perturbation/SHAP, LIME, visual t-SNE/UMAP; model-specific: ensemble feature importance, attention-based, gradient-based) with explanation targets and visualization types.

- **Data & labels**: N/A (survey). 82 reviewed publications form the evidence base.

- **Results** (quantitative findings across the 82 papers):
  - Sensor mix: "Others" (incl. proximal sensing, hyperspectral, PlanetScope) 33.3%, Sentinel 27.5%, Landsat 14.5%, MODIS 13.0%, UAV 11.6%. Landsat positioned as the long-term (30 m, 16-day revisit) compromise for multi-year monitoring; Sentinel-2 dominates field-level work.
  - Models: tree-structure models >1/3 of usage, SVM 18.2%, neural networks/other deep models 17%, regression 8% — i.e., the field is dominated by inherently more interpretable ensembles, and advanced sequential models (transformers, diffusion) remain under-adopted.
  - Preprocessing: >1/3 is data correction (geometric/atmospheric/radiometric), ~1/4 data aligning and filtering, temporal & spatial aggregation 15.4% each.
  - Temporal pattern analysis: stage analysis (growth-stage-segmented modeling) is the leading strategy, ahead of temporal attention mechanisms, feature-specific analysis, and scenario simulations.
  - XAI usage: only ~1/3 of the collected papers apply XAI at all; within those, model-specific explanations (especially ensemble/RF feature importance) dominate; SHAP is the most common perturbation method; no reviewed paper used simplified surrogate models for explanation; gradient-based methods are underutilized; temporal (time-aware) explanations are rare and mostly custom.
  - Identified gaps: temporal feature aggregation, adoption of advanced sequential architectures, and evaluation of explanation quality (especially human-centered/stakeholder evaluation) are the three persistent weaknesses.

- **What transfers to our thesis**:
  - Positions our XAI component: a Landsat-16day, stage-aware temporal explanation method for label-free stress detection addresses three gaps this review names explicitly — temporal explanation, advanced sequential architectures, and explanation-quality evaluation.
  - Quantifies that only ~1/3 of RS-agriculture papers do any XAI and almost none do time-aware explanations — a citable justification that our time-aware XAI on stress models is novel and needed.
  - Stage-based temporal analysis being the leading pattern-discovery strategy supports our plan to condition stress detection on sugarcane growth stage (phenology-aware baselines rather than fixed calendar windows).
  - Confirms Landsat's niche: 14.5% usage but explicitly the long-term, 16-day, 30 m option for multi-year agricultural monitoring — supports our choice of Landsat time series for cross-year sugarcane analysis.
  - Warning for method design: bar charts/custom 2D plots dominate visualizations; explanations must link features to crop stages and actionable agronomic decisions for farmer/policymaker stakeholders — shapes how we should present CWSI/ETa/VI attributions.
  - The review's call for adaptive temporal aggregation aligned to crop cycles matches our cross-year modeling where growth-stage alignment (not calendar months) should structure the time axis.

- **Limitations / caveats**: Citation thresholds (>=25 WoS, >=50 GS) bias the corpus toward established, highly cited work and exclude recent or niche contributions; SLR covers 2020+ only; no quantitative meta-analysis of reported accuracies; XAI subset is small (~1/3 of papers); SSRN preprint status (not yet peer-reviewed venue); no specific treatment of SSL, anomaly detection, or thermal/LST data as separate categories; "Others" category (33.3%) is heterogeneous.

- **Key numbers to quote in lit review**:
  - 82 papers reviewed from 140 (WoS) + 3,080 (Google Scholar) initial hits; first SLR jointly covering temporal data + RS + XAI in agriculture.
  - Only about one-third of agricultural RS papers incorporate any XAI; temporal/time-aware explanations are rarest.
  - Sensor usage: Sentinel 27.5%, "Others" 33.3%, Landsat 14.5%, MODIS 13.0%, UAV 11.6%.
  - Models: tree ensembles >33%, SVM 18.2%, NN/deep 17%, regression 8% — advanced sequential architectures under-adopted.
  - Stage analysis is the leading temporal pattern-discovery strategy; human-centered XAI evaluation is the biggest open gap.
