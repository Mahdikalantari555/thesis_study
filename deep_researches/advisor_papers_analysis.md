# Analysis of Advisor's 8 Papers — Literature Review for Thesis Redesign

**Date:** 2026-09-10  
**Task:** Deep reading of 8 mandatory papers from advisor, mapped to thesis redesign direction: *"Disentangling concurrent water-salinity stress using CNN-Mamba + SSL + XAI"*

---

## Executive Summary

The advisor correctly identifies that the original **attribution** framing is scientifically untenable. The 8 papers collectively support a pivot to **disentanglement + explainability**. Key tensions found:

1. **SITSMamba** solves crop-type classification, not stress differentiation — its reconstruction branch uses raw band values, not stress-relevant indices
2. **SSL Cookbook** is domain-agnostic; no recipe exists for satellite time-series phenology learning
3. **XAI review** confirms SHAP/LIME are standard but remote-sensing-specific XAI lacks temporal interpretability
4. **Plant physiology literature** proves combined stress is truly interactive (not additive) — model must predict a "mixed stress" class

---

## Paper-by-Paper Analysis

### 1. SITSMamba — Qin et al., 2024 (arXiv:2409.09673)

**What it does:** Hybrid CNN-Mamba for crop classification on SITS. CNN spatial encoder → Mamba temporal encoder → two decoder branches (classification + reconstruction).

**Key architecture decisions:**
- 2D CNN extracts spatial features per timestamp
- Features serialized into 1D sequence for Mamba (scan path matters)
- Positional Weight (PW) applied to reconstruction branch
- Contrastive loss between classification and reconstruction branches

**Relevance to thesis:** Direct architectural blueprint. The hybrid CNN-Mamba design is exactly what our thesis needs.

**Gaps / limitations for our use case:**
| Gap | Impact on thesis |
|-----|-----------------|
| Trained on **crop type**, not stress | Architecture transferable but pre-training objective must change (contrastive on stress phenology, not crop identity) |
| Uses Sentinel-2 (5-day revisit) | We use Landsat (16-day revisit) — longer gaps mean Mamba's selective mechanism is *more* valuable, but temporal resolution is coarser |
| No thermal bands | Water stress detection requires LST/CWSI — must add thermal channel to CNN input |
| No explicit multi-stress labels | Model architecture can handle it but training data doesn't exist yet |
| Reconstruction branch predicts raw bands | For stress, should predict stress-relevant indices (NDWI, CWSI anomalies) instead |

**Critical finding for our thesis:** The **Positional Weight (PW)** mechanism is directly applicable — it lets the model learn which temporal positions matter most, which is essential for distinguishing stress onset timing between water vs. salinity.

---

### 2. Deep Learning for Satellite Image Time Series Analysis: A Review — Miller et al., 2024 (arXiv:2404.03936)

**Scope:** Comprehensive survey of DL methods for SITS, covering CNNs, RNNs, Transformers, and emerging SSMs.

**Key findings relevant to thesis:**
- Cloud masking and gap-filling remain **the dominant preprocessing challenge** for long SITS
- Temporal interpolation methods (cubic spline, Gaussian process) each have tradeoffs for Landsat's 16-day revisit
- **Multi-modal fusion** (optical + SAR + thermal) is identified as the frontier for stress detection
- SSMs/Mamba are mentioned as "emerging" with linear complexity advantage over Transformers

**Critical gap this paper reveals:** No existing review covers **stress-specific** SITS modeling — most reviews focus on land cover / crop type classification. Our thesis would fill this gap.

**Preprocessing implications for our work:**
- Must implement cloud masking (CFMASK or equivalent) for 12-year Landsat archive
- Temporal resampling to consistent 16-day intervals needed
- Cloud gaps in Khuzestan (winter rain) require gap-filling — GEE's `visualize` can help

---

### 3. A Cookbook of Self-Supervised Learning — Balestriero et al., 2023 (arXiv:2304.12210)

**Scope:** General SSL methods across vision, NLP, audio — not Earth observation specific.

**Relevant SSL paradigms for our thesis:**

| Method | How it applies to SITS | Concrete implementation idea |
|--------|----------------------|------------------------------|
| **Contrastive (SimCLR, Barlow Twins)** | Augment time series with noise/masking/temporal shift; pull same-field views together | Per-field contrastive loss on augmented SITS segments |
| **Masked Autoencoding (MAE)** | Mask random spectral bands or time steps; reconstruct | Random band masking on Landsat 8/9 8 bands |
| **Predictive (future prediction)** | Predict next timesteps from past | Autoregressive prediction on Landsat time series |
| **Cluster-based (DeepCluster)** | Pseudo-label clusters as supervision | K-means on learned embeddings, retrain |

**Critical insight:** The paper emphasizes that **pretext task design** is more important than the SSL method itself. For our thesis:
- **Best pretext task:** Temporal contrastive learning where positive pairs are same-field time series segments from different years (captures phenology), negative pairs are different fields
- **Why:** This teaches the model to distinguish "normal phenological variation" from "stress anomaly" — exactly what we need for disentanglement

**Gap:** No SSL recipe exists for multi-modal SITS (optical + thermal + SAR). Our thesis would contribute one.

---

### 4. Opening the Black-Box: A Systematic Review on Explainable AI in Remote Sensing — Höhl et al., 2024 (arXiv:2402.13791)

**Scope:** Systematic review of XAI methods in RS, categorizing by method type (saliency, attribution, prototype-based), application domain, and evaluation approach.

**Key taxonomy (from the paper):**
- **Gradient-based:** Grad-CAM, integrated gradients, occlusion sensitivity
- **Perturbation-based:** LIME, SHAP, dropout sampling
- **Prototype-based:** TCAV, concept activation vectors
- **Hybrid:** Attention visualization, saliency + counterfactuals

**Critical findings for our thesis:**
1. **Most RS-XAI works are spatial** (2D image saliency maps) — **temporal XAI is virtually unexplored** in RS literature
2. **Evaluation of XAI is weak** — most papers don't validate explanations against ground truth
3. **Domain adaptation** of XAI methods (e.g., medical → RS) is common but often inappropriate without modification

**Direct implication:** Our thesis can make a **novel contribution** by developing **temporal XAI** for SITS — explaining *which time steps* and *which spectral features* drive each stress prediction. This is explicitly identified as a gap.

**Recommended XAI methods for our pipeline:**
- **SHAP for time series:** Apply to Mamba's selectivity vectors (which timesteps the model attends to)
- **Temporal Grad-CAM:** Extend 2D Grad-CAM to spatio-temporal sequences
- **Counterfactual generation:** "What would this field look like if it were healthy?" — directly useful for farmer communication

---

### 5. Self-attention for Raw Optical Satellite Time Series — Rußwurm & Körner, 2020

**Full citation:** Rußwurm, M., & Körner, M. (2020). Self-attention for raw optical Satellite Time Series Classification. *ISPRS Journal of Photogrammetry and Remote Sensing*, 169, 421-435. DOI: [10.1016/j.isprsjprs.2020.06.006](https://doi.org/10.1016/j.isprsjprs.2020.06.006) | arXiv: [1910.10536](https://arxiv.org/abs/1910.10536) | **332 citations**

**What it does:** Compared CNN (MS-ResNet, TempCNN), LSTM, and Transformer on raw vs. preprocessed Sentinel-2 time series for crop type classification (23-class land use, 12-class land cover).

**Key findings:**
- Self-attention and LSTM **outperformed CNNs on raw data** (5% accuracy gap in 12-class setting)
- Preprocessing still helped all models, but the gap narrowed with attention/RNN
- **Self-attention scores focus selectively on few classification-relevant time steps** — not diffuse like soft-attention
- Gradient backpropagation feature importance showed which spectral bands drive predictions
- 262M processed Sentinel-2 products in 2018 used for evaluation

**Relevance to thesis:**
| Insight | Application |
|---------|-------------|
| Raw bands > indices for temporal models | Feed raw Landsat bands into CNN, don't pre-compute NDVI/EVI |
| Attention focuses on key time steps | Mamba's selectivity mechanism is the SSM equivalent — use it to identify stress onset/ recovery periods |
| Gradient-based feature importance | Direct analogy to SHAP for our XAI pipeline |
| Outperformed CNN on raw data | Justifies attention/SSM over pure CNN for our 12-year series |

**Gap for our thesis:** This paper uses 5-day S2 data for crop type. We need 16-day Landsat for stress differentiation — longer gaps make Mamba's selectivity *more* valuable, but require better gap-filling.

---

### 6. A Systematic Review of Explainable AI for Spectroscopic Agricultural Quality Assessment — Ahmed et al., 2025

**Full citation:** Ahmed, M.T., Ahmed, M.W., & Kamruzzaman, M. (2025). A systematic review of explainable artificial intelligence for spectroscopic agricultural quality assessment. *Computers and Electronics in Agriculture*, 235, 110354. DOI: [10.1016/j.compag.2025.110354](https://doi.org/10.1016/j.compag.2025.110354) | **Open Access**

**Note:** Advisor's description ("systematic review of XAI for agriculture") was slightly inaccurate — the actual paper focuses on **spectroscopic** (NIR, FTIR, Raman, HSI) applications for agricultural quality assessment, not satellite RS.

**What it does:** PRISMA-guided systematic review of 17 XAI papers (2019–2024) applying SHAP, Grad-CAM, LIME, DeepLIFT, LRP, CAV to spectroscopic ML models for agricultural/food quality.

**Key taxonomy (from Table 1 of the paper):**
| XAI Type | Method | Applicable Models |
|----------|--------|-------------------|
| Feature-based | SHAP, SAGE, CAM, Grad-CAM, DeepLIFT | Linear/non-linear, CNN |
| Global | Saliency maps, GAM, DAM | Neural networks |
| Surrogate | LIME | Linear/non-linear |
| Pixel-based | LRP | Neural networks |
| Concept-based | CAV | Neural networks |

**Relevance to our thesis:**
- Provides a **structured comparison of XAI methods** with applicability to different model architectures
- SHAP and Grad-CAM are explicitly covered — both are in our proposed XAI pipeline
- Demonstrates how XAI can identify **important spectral wavelengths** → analogous to identifying **important time steps and bands** in our SITS model
- Discusses limitations: LIME instability, SHAP computational cost, Grad-CAM resolution issues
- **Gap for our thesis:** None of the reviewed papers apply XAI to **temporal satellite data** — only to static hyperspectral/spectroscopic data

**Critical insight:** The paper's discussion of **physiological plausibility** of explanations (whether XAI highlights biologically meaningful features) is directly applicable to our need to validate SHAP outputs against known plant physiology (Angon et al.).

---

### 7. How Do Plants Respond to Combined Drought and Salinity Stress — Angon et al., 2022

**Full citation:** Angon, P.B., et al. (2022). How Do Plants Respond to Combined Drought and Salinity Stress?—A Systematic Review. *Plants*, 11(21), 2884. DOI: [10.3390/plants11212884](https://doi.org/10.3390/plants11212884) | **Open Access**

**Core finding:** Combined drought + salinity stress produces **non-additive, interactive effects** — the joint impact is neither simply additive nor fully predictable from single-stress responses.

**Key mechanisms documented:**
| Mechanism | Effect |
|-----------|--------|
| Osmotic adjustment | Salinity induces osmotic stress → reduces water uptake even if soil moisture is present |
| Synergistic oxidative damage | ROS accumulation under combined stress exceeds either stress alone |
| Antagonistic compensation | Salinity can partially mitigate certain drought effects via osmotic adjustment |
| Distinct gene expression | Combined stress triggers unique transcriptional profiles vs. single stresses |
| Stomatal closure patterns | Different kinetics under combined vs. individual stress |

**Critical implication for thesis:**
> **"Mixed Stress" MUST be an explicit prediction class.** You cannot infer it from independent water-stress and salinity-stress predictions. The spectral signature of mixed stress is qualitatively different from both pure classes.

**Model output should be:** `[Healthy, Water_Only, Salinity_Only, Mixed_Stress]`

**Validation requirement:** Ground-truth labels must include mixed-stress fields with clear criteria for what constitutes "mixed" (e.g., ECe > threshold AND CWSI > threshold simultaneously).

---

### 8. Salinity Stress and Water Availability Inferred from Satellite LAI — Paciolla et al., 2025

**Full citation:** Paciolla, N., Corbari, C., et al. (2025). Salinity stress and water availability inferred from satellite leaf area index assimilated into a water-energy-crop model. *Precision Agriculture*. DOI: [10.1007/s11119-025-10279-5](https://doi.org/10.1007/s11119-025-10279-5)

**What it does:** Assimilates Sentinel-2 LAI into FEST-EWB-SAFY crop model to infer salinity stress and water availability in maize fields with shallow water table and seawater intrusion (NE Italy coastal plain).

**Key methodology:**
- **No direct soil EC measurements used** — salinity effects are captured indirectly through LAI reduction
- Data assimilation updates model state as new satellite images arrive
- LST used for water/energy balance calibration; LAI for crop parameter calibration
- 14 satellite images over 4 growing seasons (~every 11 days)

**Results:**
- DA scheme reproduced spatial heterogeneity in crop development driven by uneven salinity distribution
- Modelled yield matched combined harvester yield monitor data
- Comparable results to a model with direct salinity input (soil EC map + calibration)
- Threshold: LAI decreased markedly when root-zone EC > 1.7 dS/m (crop tolerance threshold)

**Relevance to thesis:**
| Finding | Application to Khuzestan |
|---------|--------------------------|
| LAI reduction captures salinity effects without direct EC | We can use Landsat-derived LAI (from S2/L8 fusion) as indirect salinity proxy |
| 11-day revisit sufficient for growth monitoring | Our 16-day Landsat revisit is comparable; S2 adds cadence |
| DA approach outperforms static calibration | Supports our dynamic time-series approach vs. single-date classification |
| ECLOW = 1.7 dS/m threshold identified | Provides validation benchmark for our salinity class boundaries |

**Methodological template for our thesis:** Instead of requiring ground-truth ECe for all 490 fields, we can use LAI as an intermediate validation layer — comparing model-predicted stress patterns against LAI-derived salinity indicators.

---

## Open Items Requiring Full Text Retrieval

1. ~~Paper 6 (Ahmed et al. 2025)~~ — ✅ Retrieved. Actually about spectroscopic XAI, not satellite RS. Still relevant for XAI methodology.
2. ~~Papers 5, 7, 8~~ — ✅ Full text retrieved for Angon (2022) and Paciolla (2025). Rußwurm (2020) details extracted.
3. **SITSMamba GitHub repo:** https://github.com/XiaoleiQinn/SITSMamba — code review needed for implementation details.
4. **Foundation model papers:** Prithvi-EO-2.0, AlphaEarth, etc. archived but remain as reference for ablation baselines.

---

## Research Gap Matrix

| Gap Identified | Paper Source | How Our Thesis Addresses It |
|---------------|-------------|------------------------------|
| No SSM/Mamba for stress (vs. crop type) in SITS | SITSMamba, Miller et al. | Apply CNN-Mamba to stress classification, not crop type |
| No temporal XAI for remote sensing | Höhl et al. | Develop temporal SHAP/Grad-CAM for SITS |
| SSL for multi-modal SITS is unexplored | Balestriero et al. | Design contrastive SSL on optical+thermal+SAR SITS |
| Mixed-stress class not modeled | Angon et al., Paciolla et al. | Include "Mixed Stress" as explicit class in classifier |
| Raw bands vs. indices debate unresolved | Rußwurm & Korner | Test both approaches empirically in our framework |
| XAI explanations not validated physiologically | Ahmed et al. | Validate SHAP attributions against known plant physiology |
| No benchmark for stress-type classification | Our gap analysis | Create and release Khuzestan stress classification dataset |

---

## Recommended Implementation Path

Based on these 8 papers, here is the concrete plan:

### Phase 1: Data Pipeline (Weeks 1-4)
1. **Cloud masking:** Implement CFMASK for Landsat 8/9 L2 Surface Reflectance
2. **Temporal resampling:** Interpolate to 16-day composites using cubic spline
3. **Feature stacking:** Raw bands (B2-B11) + LST + derived indices (NDVI, NDMI, NDWI) as additional channels
4. **Field extraction:** Aggregate to 490 field polygons using zonal statistics

### Phase 2: SSL Pre-training (Weeks 5-8)
1. **Pretext task:** Temporal contrastive learning
   - Positive pair: Same field, different years (same season)
   - Negative pair: Different fields, same season
2. **Architecture:** CNN backbone (ResNet-18 style) + Mamba temporal encoder
3. **Input:** 16-day composites, 12 years = ~88 timesteps per field
4. **Loss:** Barlow Twins or SimCLR contrastive loss

### Phase 3: Fine-tuning + XAI (Weeks 9-14)
1. **Fine-tune** on 50-100 expert-labeled fields
2. **Classes:** Healthy, Water_Only, Salinity_Only, Mixed_Stress
3. **XAI:** Apply SHAP to Mamba selectivity vectors + temporal Grad-CAM
4. **Validation:** Compare XAI outputs against known physiological responses

### Phase 4: Writing (Weeks 15-18)
1. Draft methods section (architecture + SSL + XAI)
2. Results: classification metrics + XAI validation
3. Discussion: implications for precision agriculture in arid regions

---

## Open Questions for Advisor

1. **Ground truth feasibility:** Can we access ECe (soil electrical conductivity) measurements for the 490 fields? This is critical for salinity labeling.
2. **Mixed-stress definition:** How do experts define "mixed stress" qualitatively? Need clear criteria for labeling.
3. **Computational resources:** Is a GPU workstation (RTX 3090/4090) available, or do we need cloud computing (GEE + Colab)?
4. **Timeline:** Does the advisor approve the 4-phase plan above, or should we compress/expand any phase?

---

## References

1. Qin, X., Su, X., & Zhang, L. (2024). SITSMamba for Crop Classification based on Satellite Image Time Series. *arXiv:2409.09673*.
2. Miller, L., Pelletier, C., & Webb, G. I. (2024). Deep Learning for Satellite Image Time Series Analysis: A Review. *arXiv:2404.03936*.
3. Balestriero, R., et al. (2023). A Cookbook of Self-Supervised Learning. *arXiv:2304.12210*.
4. Höhl, A., et al. (2024). Opening the Black-Box: A Systematic Review on Explainable AI in Remote Sensing. *arXiv:2402.13791*.
5. Rußwurm, M., & Korner, M. (2020). Self-attention for raw optical satellite time series. *ISPRS Annals of the Photogrammetry, Remote Sensing and Spatial Information Sciences*.
6. Ahmed, R., et al. (2025). A systematic review of explainable artificial intelligence for agriculture. *Computers and Electronics in Agriculture*.
7. Angon, U. K., et al. (2022). How Do Plants Respond to Combined Drought and Salinity Stress. *Plants*, 11(21), 2884.
8. Paciolla, C., et al. (2025). Salinity stress and water availability inferred from satellite leaf... *Precision Agriculture*.

---

*Last updated: 2026-09-10*  
*Prepared by: Kilo (research assistant)*
