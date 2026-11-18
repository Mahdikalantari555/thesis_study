# Research Gaps — New Proposal

**Topic:** Crop Stress Detection in Sugarcane Fields Using Satellite Image Time Series

---

## Identified Gaps (from literature review)

### G1 — No Mamba/SSM applied to crop stress classification from SITS
- **Evidence:** SITSMamba (2024) is the first Mamba architecture for SITS — but for crop classification, not stress. Miller et al. (2024) review notes SSMs as "emerging" with no stress applications.
- **Status:** Negative searches documented (no Mamba stress application found).
- **Thesis contribution:** Apply CNN-Mamba temporal encoder to stress detection.

### G2 — No timestep-level temporal XAI for deep SITS stress models
- **Evidence:** Höhl et al. (2024): most XAI methods "do not explicitly consider temporal dependencies." James et al. (2025) combines contrastive SITS with feature-level SHAP/Grad-CAM — but no timestep-level attribution, no water-vs-salinity typing, no physiological validation.
- **Thesis contribution:** Temporal SHAP on Mamba selectivity vectors + temporal Grad-CAM, validated against plant physiology.

### G3 — No multi-modal (optical + thermal) SSL recipe for satellite time series
- **Evidence:** Paul et al. (2025): across 163 studies, SSL occupies one subsection with 3 studies, all proximal/leaf — no satellite, no thermal, no multi-temporal SSL. Balestriero et al. (2023) is domain-agnostic.
- **Thesis contribution:** Barlow Twins pre-training on raw Landsat bands + LST across 490 fields × 12 years.

### G4 — Concurrent water–salinity has only been monitored descriptively
- **Evidence:** Wen et al. trilogy (2021–2023) is ANOVA-only, no ML, no per-field stress-type disentanglement, no arid irrigated sugarcane, no explainability. Berger et al. (2022): no integrated multi-sensor concept for stress-type differentiation.
- **Thesis contribution:** Predictive per-field disentanglement of water vs. salinity stress in arid irrigated sugarcane.

### G5 — No public benchmark for stress-type classification
- **Evidence:** CropHarvest and PASTIS are crop-type only; no stress-type benchmark exists.
- **Thesis contribution:** Release benchmark dataset + code (G5 promise to advisor).

### G6 — XAI explanations not validated physiologically
- **Evidence:** Höhl et al. (2024): >90% of studies evaluate explanations only anecdotally; real-world RS lacks controlled XAI ground truth. Angon et al. (2022) provides physiology but is unused by RS.
- **Thesis contribution:** Physiological validation (Angon response directions: gs↓, Na⁺↑, ROS↑, Chl a↓).

### G7 — Raw bands vs. indices unresolved for stress SITS
- **Evidence:** Rußwurm & Körner (2020): raw bands beat indices for temporal models. Waters et al. (2024): moisture-accentuating VIs recommended for sugarcane.
- **Thesis contribution:** Raw bands + LST as primary input; indices as ablation arm.

---

## How Our Data Can Address These Gaps

| Gap | Addressable with our data? | How |
|-----|---------------------------|-----|
| G1 | ✅ Yes | Landsat archive (2013–2025) + 490 fields provide sufficient data for CNN-Mamba stress classification |
| G2 | ✅ Yes | Timestep-level attributions possible; 12-year archive enables temporal analysis |
| G3 | ✅ Yes | Full unlabeled archive (490 fields × 12 years) enables SSL pre-training; LST provides thermal channel |
| G4 | ✅ Yes | Amirkabir site has both water (CWSI) and salinity (ECe) measurements; 430 dates enable temporal modeling |
| G5 | ✅ Yes | Can release benchmark with code; 490 fields with expert labels |
| G6 | ⚠️ Partial | Requires expert review; physiology from Angon et al. (2022) as validation reference |
| G7 | ✅ Yes | Ablation study: raw bands vs. indices on same data |
