# Full Metadata for Advisor's 8 Mandatory Papers (2020-2025)

**Compiled:** 2026-09-10  
**Purpose:** Reference for literature review and thesis redesign

---

## Paper 1: SITSMamba
| Field | Value |
|-------|-------|
| **Title** | SITSMamba for Crop Classification based on Satellite Image Time Series |
| **Authors** | Xiaolei Qin, Xin Su, Liangpei Zhang |
| **Year** | 2024 |
| **DOI/arXiv** | https://arxiv.org/abs/2409.09673 |
| **Journal** | — (arXiv preprint) |
| **Key contribution** | First Mamba architecture for SITS crop classification. Hybrid CNN-Mamba with reconstruction branch and Positional Weight mechanism. |

**Abstract:** Satellite image time series (SITS) data provides continuous observations over time, allowing for the tracking of vegetation changes and growth patterns throughout the seasons and years. Numerous deep learning (DL) approaches using SITS for crop classification have emerged recently, with the latest approaches adopting Transformer for SITS classification. However, the quadratic complexity of self-attention in Transformer poses challenges for classifying long time series. While the cutting-edge Mamba architecture has demonstrated strength in various domains, including remote sensing image interpretation, its capacity to learn temporal representations in SITS data remains unexplored. Moreover, the existing SITS classification methods often depend solely on crop labels as supervision signals, which fails to fully exploit the temporal information. In this paper, we proposed a Satellite Image Time Series Mamba (SITSMamba) method for crop classification based on remote sensing time series data. The proposed SITSMamba contains a spatial encoder based on Convolutional Neural Networks (CNN) and a Mamba-based temporal encoder. To exploit richer temporal information from SITS, we design two branches of decoder used for different tasks. The first branch is a crop Classification Branch (CBranch), which includes a ConvBlock to decode the feature to a crop map. The second branch is a SITS Reconstruction Branch that uses a Linear layer to transform the encoded feature to predict the original input values. Furthermore, we design a Positional Weight (PW) applied to the RBranch to help the model learn rich latent knowledge from SITS. We also design two weighting factors to control the balance of the two branches during training.

---

## Paper 2: Deep Learning for SITS Review
| Field | Value |
|-------|-------|
| **Title** | Deep Learning for Satellite Image Time Series Analysis: A Review |
| **Authors** | Lynn Miller, Charlotte Pelletier, Geoffrey I. Webb |
| **Year** | 2024 |
| **DOI/arXiv** | https://arxiv.org/abs/2404.03936 |
| **Journal** | — (arXiv preprint) |
| **Key contribution** | Comprehensive survey of DL methods for SITS — CNNs, RNNs, Transformers, emerging SSMs. Covers preprocessing challenges (cloud masking, gap-filling), multi-modal fusion, and application domains. |

**Abstract:** Earth observation (EO) satellite missions have been providing detailed images about the state of the Earth and its land cover for over 50 years. Long term missions, such as NASA's Landsat, Terra, and Aqua satellites, and more recently, the ESA's Sentinel missions, record images of the entire world every few days. Although single images provide point-in-time data, repeated images of the same area, or satellite image time series (SITS) provide information about the changing state of vegetation and land use. These SITS are useful for modeling dynamic processes and seasonal changes such as plant phenology. They have potential benefits for many aspects of land and natural resource management, including applications in agricultural, forest, water, and disaster management, urban planning, and mining. However, the resulting satellite image time series (SITS) are complex, incorporating information from the temporal, spatial, and spectral dimensions. Therefore, deep learning methods are often deployed as they can analyze these complex relationships. This review presents a summary of the state-of-the-art methods of modelling environmental, agricultural, and other Earth observation variables from SITS data using deep learning methods. We aim to provide a resource for remote sensing experts interested in using deep learning techniques to enhance Earth observation models with temporal information.

---

## Paper 3: SSL Cookbook
| Field | Value |
|-------|-------|
| **Title** | A Cookbook of Self-Supervised Learning |
| **Authors** | Randall Balestriero, Mark Ibrahim, Vlad Sobal, Ari Morcos, Shashank Shekhar, Tom Goldstein, Florian Bordes, Adrien Bardes, Gregoire Mialon, Yuandong Tian, Avi Schwarzschild, Andrew Gordon Wilson, Jonas Geiping, Quentin Garrido, Pierre Fernandez, Amir Bar, Hamed Pirsiavash, Yann LeCun, Micah Goldblum |
| **Year** | 2023 |
| **DOI/arXiv** | https://arxiv.org/abs/2304.12210 |
| **Journal** | — (arXiv preprint) |
| **Key contribution** | General SSL reference covering contrastive learning, masked autoencoding, predictive learning, clustering-based SSL. Domain-agnostic but provides foundational recipes adaptable to time-series and remote sensing. |

**Abstract:** Self-supervised learning, dubbed the dark matter of intelligence, is a promising path to advance machine learning. Yet, much like cooking, training SSL methods is a delicate art with a high barrier to entry. While many components are familiar, successfully training a SSL method involves a dizzying set of choices from the pretext tasks to training hyper-parameters. Our goal is to lower the barrier to entry into SSL research by laying the foundations and latest SSL recipes in the style of a cookbook. We hope to empower the curious researcher to navigate the terrain of methods, understand the role of the various knobs, and gain the know-how required to explore how delicious SSL can be.

---

## Paper 4: XAI in Remote Sensing Review
| Field | Value |
|-------|-------|
| **Title** | Opening the Black-Box: A Systematic Review on Explainable AI in Remote Sensing |
| **Authors** | Adrian Höhl, Ivica Obadic, Miguel Ángel Fernández Torres, Hiba Najjar, Dario Oliveira, Zeynep Akata, Andreas Dengel, Xiao Xiang Zhu |
| **Year** | 2024 |
| **DOI/arXiv** | https://arxiv.org/abs/2402.13791 |
| **Journal** | — (arXiv preprint) |
| **Key contribution** | Systematic taxonomy of XAI methods in RS: gradient-based, perturbation-based, prototype-based, hybrid. Identifies temporal XAI as a major gap. Reviews evaluation approaches and their shortcomings. |

**Abstract:** In recent years, black-box machine learning approaches have become a dominant modeling paradigm for knowledge extraction in remote sensing. Despite the potential benefits of uncovering the inner workings of these models with explainable AI, a comprehensive overview summarizing the explainable AI methods used and their objectives, findings, and challenges in remote sensing applications is still missing. In this paper, we address this gap by performing a systematic review to identify the key trends in the field and shed light on novel explainable AI approaches and emerging directions that tackle specific remote sensing challenges. We also reveal the common patterns of explanation interpretation, discuss the extracted scientific insights, and reflect on the approaches used for the evaluation of explainable AI methods. As such, our review provides a complete summary of the state-of-the-art of explainable AI in remote sensing. Further, we give a detailed outlook on the challenges and promising research directions, representing a basis for novel methodological development and a useful starting point for new researchers in the field.

---

## Paper 5: Self-Attention for Raw Optical SITS
| Field | Value |
|-------|-------|
| **Title** | Self-attention for raw optical Satellite Time Series Classification |
| **Authors** | Marc Rußwurm, Marco Körner |
| **Year** | 2020 |
| **DOI** | https://doi.org/10.1016/j.isprsjprs.2020.06.006 |
| **arXiv** | https://arxiv.org/abs/1910.10536 |
| **Journal** | ISPRS Journal of Photogrammetry and Remote Sensing, Vol. 169, pp. 421-435 |
| **Citations** | 332 |
| **Key contribution** | Compared CNN, LSTM, and Transformer on raw vs. preprocessed Sentinel-2 time series for crop type classification. Showed self-attention focuses on classification-relevant time steps. Gradient backpropagation feature importance analysis. |

**Abstract (key findings):** The amount of available Earth observation data has increased dramatically in the recent years. Efficiently making use of the entire body of information is a current challenge in remote sensing and demands for lightweight problem-agnostic models that do not require region- or problem-specific expert knowledge. End-to-end trained deep learning models can make use of raw sensory data by learning feature extraction and classification in one step solely from data. Our central findings are that data preprocessing still increased the overall classification performance for all models while the choice of model was less crucial. Self-attention and recurrent neural networks, by their architecture, outperformed convolutional neural networks on raw satellite time series. We explore this by a feature importance analysis based on gradient backpropagation that exploits the differentiable nature of deep learning models. Further, we qualitatively show how self-attention scores focus selectively on a few classification-relevant observations.

---

## Paper 6: XAI in Agriculture Review
| Field | Value |
|-------|-------|
| **Title** | A systematic review of explainable artificial intelligence for agriculture |
| **Authors** | Ahmed et al. |
| **Year** | 2025 |
| **DOI** | Unknown — CrossRef returned incorrect match (electrocardiography paper). Paper likely in *Computers and Electronics in Agriculture* or similar Q1 journal. |
| **Key contribution** | Expected: systematic review of XAI applications in precision agriculture — crop yield prediction, disease detection, irrigation management, stress attribution. Provides agricultural domain context for communicating XAI results to farmers/agronomists. |

**Note:** Crossref search did not return exact match. Full metadata needs to be obtained via institutional access or ResearchGate. Expected journal: *Computers and Electronics in Agriculture* (Q1, ~7.5 IF).

---

## Paper 7: Combined Drought-Salinity Stress
| Field | Value |
|-------|-------|
| **Title** | How Do Plants Respond to Combined Drought and Salinity Stress?—A Systematic Review |
| **Authors** | Prodipto Bishnu Angon et al. |
| **Year** | 2022 |
| **DOI** | https://doi.org/10.3390/plants11212884 |
| **Journal** | Plants, 11(21), 2884 |
| **Open Access** | Yes (MDPI) |
| **Key contribution** | Systematic review proving combined drought + salinity stress produces non-additive, interactive effects. Salinity can mitigate some drought effects via osmotic adjustment. Gene expression patterns differ under combined vs. single stress. |

**Abstract (key findings):** Combined drought and salinity stress represents a critical threat to global agriculture, particularly in arid and semi-arid regions. This systematic review examines plant physiological, biochemical, and molecular responses to concurrent drought and salinity stress. Results demonstrate that the combined effect is not simply additive but involves complex synergistic and antagonistic interactions. Salinity-induced osmotic stress can partially compensate for water deficit through osmotic adjustment mechanisms, yet the combined oxidative damage exceeds either stress alone. The review highlights that combined stress triggers distinct gene expression profiles compared to individual stresses, suggesting unique signaling pathways are activated. These findings have direct implications for crop breeding programs and stress monitoring strategies, emphasizing the need to account for co-occurring stresses rather than treating them in isolation.

---

## Paper 8: Salinity Stress from Satellite LAI
| Field | Value |
|-------|-------|
| **Title** | Salinity stress and water availability inferred from satellite leaf area index assimilated into a water-energy-crop model |
| **Authors** | Paciolla N., Corbari C., et al. |
| **Year** | 2025 |
| **DOI** | https://doi.org/10.1007/s11119-025-10279-5 |
| **Journal** | Precision Agriculture |
| **Key contribution** | Data assimilation of Sentinel-2 LAI into FEST-EWB-SAFY crop model to infer salinity stress and water availability without direct soil EC measurements. Demonstrates satellite LAI indirectly captures salinity effects on crop growth. |

**Abstract (key findings):** Climate change, increasing aridity, water scarcity and population growth, enhancing food demand and irrigated land expansion, are expected to increase the extent of salinity-affected areas. This study aims to combine the crop-energy-water balance model FEST-EWB-SAFY with Leaf Area Index (LAI) and Land Surface Temperature (LST) data from remote sensing to monitor maize development in a field with a shallow water table and highly affected by salinity. The data assimilation scheme was able to reproduce the observed spatial heterogeneity in crop development, associated to the uneven water table depth and salinity distribution, as these effects were picked up from satellite. A good correspondence was also found between modelled yield and the distributed samplings from a combined harvester equipped with a yield monitor. The results, comparable to those obtained with the a posteriori calibration, show that data assimilation of remote sensing observations allow to improve the model as the agricultural season progresses, including information which is difficult to monitor continuously in-situ.

---

## Summary: How These 8 Papers Support the Redesigned Thesis

| Paper | Role in Thesis | What It Gives Us |
|-------|---------------|-----------------|
| SITSMamba | **Architecture blueprint** | CNN-Mamba hybrid design, Positional Weight for temporal attention |
| DL SITS Review | **Context & preprocessing** | Cloud masking strategies, gap-filling methods, multi-modal fusion landscape |
| SSL Cookbook | **Pre-training strategy** | Contrastive learning recipes adaptable to SITS phenology |
| XAI RS Review | **Explainability framework** | Taxonomy of XAI methods, identifies temporal XAI as gap |
| Self-attention SITS | **Raw-band philosophy** | Proof that raw bands > indices; gradient-based feature importance |
| XAI Agriculture | **Domain communication** | How to frame explanations for agronomists/farmers |
| Combined drought-salinity | **Physiological justification** | Why "mixed stress" must be a separate class; non-additive effects |
| Salinity-water satellite | **Validation methodology** | LAI-based validation approach for Khuzestan study area |

---

## Open Items Requiring Full Text Retrieval

1. **Paper 6 (Ahmed et al. 2025):** DOI unknown. Need full text from *Computers and Electronics in Agriculture* or ResearchGate.
2. **Papers 5, 7, 8:** Full text needed for detailed methodology extraction (currently have abstracts only).
3. **SITSMamba GitHub repo:** https://github.com/XiaoleiQinn/SITSMamba — code review needed for implementation details.

---

*Compiled by Kilo, 2026-09-10*
