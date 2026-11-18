# Extract: 1-s2.0-S235293852600412X-main.pdf

*First ~4 pages, extracted with pdftotext on 2026-10-04. Source: D:\RS\Thesis\New_papers$f*

---

                                  Remote Sensing Applications: Society and Environment 44 (2026) 102279

                                                    Contents lists available at ScienceDirect

                              Remote Sensing Applications: Society and
                                                 Environment

                                           journal homepage: www.elsevier.com/locate/rsase

Remote sensing-based machine learning and deep learning for
agriculture and forestry: Yield estimation, land-cover mapping,
and plant stress - A systematic review (2020-2025)

David Alejandro Gracia Rojas a,* , H´ector Javier Go´mez Díaz a, Richard de Jesús Gil
Herrera b

a Universidad Nacional Abierta y a Distancia, Bogota´ D.C., Colombia
b Universidad Internacional de La Rioja, Logron~o, Spain

ARTICLE INFO                  ABSTRACT

Keywords:                     Context: The integration of remote sensing with Machine Learning (ML) and Deep Learning (DL)
Remote sensing                has rapidly expanded in agricultural and forest monitoring, generating a heterogeneous body of
Machine learning              literature that requires systematic synthesis.
Deep learning                 Aims: This study aims to identify recent methodological patterns within the sampled 2020-2025
Optical-SAR fusion            evidence base, evaluate reporting practices, and highlight research gaps in remote sen­
Hybrid crop-AI models         sing-artificial intelligence (AI) applications for agricultural and forestry monitoring.
Systematic literature review  Methods: A systematic literature review covering 2020-2025 analyzed 105 research articles.
                              Proportional stratified sampling was applied across four repositories (IEEE Xplore, Scopus, Web of
                              Science, and ScienceDirect), supported by pilot testing and semantic expansion of search terms.
                              Information on algorithms, sensors, applications, and evaluation metrics was extracted using a
                              structured three-phase protocol.
                              Key results: Convolutional Neural Networks dominate land-cover mapping and segmentation
                              tasks, while Long Short-Term Memory networks and Transformers are widely used for time-series
                              analysis in applications such as yield estimation and plant stress monitoring. Classical ML ap­
                              proaches such as Random Forest, Gradient Boosted Decision Trees, and Support Vector Machines
                              remain competitive baselines when feature engineering is robust. Multimodal fusion, including
                              optical-synthetic aperture radar (SAR) integration, is used to preserve complementary structural
                              information when optical observations are cloud-constrained, although climate-stratified com­
                              parisons remain scarce. In forestry, hyperspectral imaging (HSI)-light detection and ranging
                              (LiDAR) combinations with three-dimensional convolutional neural network (3D-CNN) archi­
                              tectures improve species discrimination. Hybrid crop-AI models integrating biomass or Leaf Area
                              Index (LAI) with crop simulators enhance physiological consistency and early yield prediction,
                              although limitations persist in spatiotemporal validation, uncertainty quantification, and stan­
                              dardized evaluation metrics.
                              Conclusion: Operational deployment requires rigorous spatiotemporal validation schemes, explicit
                              uncertainty estimation, and standardized evaluation protocols.
                              Implications and impacts: These findings provide methodological guidance for developing scalable
                              remote sensing-AI monitoring systems and highlight priority research directions including

  * Corresponding author.
     E-mail address: david.gracia@unad.edu.co (D.A. Gracia Rojas).

https://doi.org/10.1016/j.rsase.2026.102279
Received 11 May 2026; Received in revised form 5 September 2026; Accepted 21 September 2026
Available online 27 September 2026
2352-9385/© 2026 The Authors. Published by Elsevier B.V. This is an open access article under the CC BY-NC-ND license
(http://creativecommons.org/licenses/by-nc-nd/4.0/).
D.A. Gracia Rojas et al.                                            Remote Sensing Applications: Society and Environment 44 (2026) 102279

                                         multimodal data fusion, hybrid process-AI models, and efficient learning strategies for data-
                                         scarce agricultural and forestry environments.

List of abbreviations Machine Learning - ML and Deep Learning - DL

                          3D-CNN         3-D Convolutional Neural Network
                          AdaBoost       Adaptive Boosting
                          AE             Autoencoder
                          APSIM          Agricultural Production Systems Simulator
                          BDL            Bayesian Deep Learning
                          BNN            Bayesian Neural Network
                          BPNN           Backpropagation Neural Network
                          CART           Classification and Regression Trees
                          CatBoost       Categorical Boosting
                          CenterNet      Center-point detection (Key point-based object detector)
                          CGRU           Convolutional Gated Recurrent Unit
                          ChOA           Chimp Optimization Algorithm
                          CNN            Convolutional Neural Network
                          Conv3D         3-D Convolution
                          ConvLSTM       Convolutional Long Short-Term Memory
                          DBN            Deep Belief Network
                          DNN            Deep Neural Network
                          DRQN           Deep Recurrent Q-Network
                          DTO            Dipper-Throated Optimization
                          ELM            Extreme Learning Machine
                          EVT            Extreme Value Theory
                          FPN            Feature Pyramid Network
                          FFNN           Feed-Forward Neural Network
                          Faster R-CNN   Region-based CNN object detector (faster variant)
                          GAT            Graph Attention Network
                          GBDT           Gradient-Boosted Decision Trees
                          GAN            Generative Adversarial Network
                          GOA            Grasshopper Optimization Algorithm
                          GPR            Gaussian Process Regression
                          GRU            Gated Recurrent Unit
                          HRSL           Hybrid Reinforcement and Supervised Learning
                          KELM           Kernel Extreme Learning Machine
                          KNN/k-NN       k-Nearest Neighbors
                          LASSO          Least Absolute Shrinkage and Selection Operator
                          LightGBM       Light Gradient Boosting Machine
                          LSTM           Long Short-Term Memory
                          MLP            Multilayer Perceptron
                          MPA            Marine Predators Algorithm
                          MSCA           Multi-Scale Channel Attention
                          PCA            Principal Component Analysis
                          PLS/PLSR       Partial Least Squares (Regression)
                          PSPNet-STL     Pyramid Scene Parsing Network with Statistical Texture Learning
                          Res/ResNet-50  Residual Network (50-layer variant)
                          RF             Random Forest
                          RRDN           Residual-in-Residual Dense Network
                          RNN            Recurrent Neural Network
                          SCM            Structural Causal Model
                          SimAM          Simple Attention Module
                          STCCL          Spatial-Temporal Contrastive Self-Supervised Learning
                          SVM            Support Vector Machine
                          SVR            Support Vector Regression
                          TL             Transfer Learning
                          ViT            Vision Transformer
                          VGG16/19       Visual Geometry Group networks (16/19 layers)
                          XGBoost        Extreme Gradient Boosting
                          YOLOv4         You Only Look Once v4 (object detector)

1. Introduction

1.1. Background and motivation

    The integration of Artificial Intelligence (AI) within the agricultural and agroforestry sectors is undergoing a consistent and gradual
augmentation, encompassing the implementation of blockchain, cloud computing, the Internet of Things (IoT), machine learning (ML),

                                                                                                             2
D.A. Gracia Rojas et al.                     Remote Sensing Applications: Society and Environment 44 (2026) 102279

and deep learning (DL) across the entire production cycle (Meshram et al., 2021). This technological convergence finds particular
application in multispectral and hyperspectral sensors employed in drones (unmanned aerial vehicles-UAVs) and satellite platforms
(Leo´n P´erez, 2021). At the conceptual level, international organizations promote the use of agroinformatics, defined as the application
of information technology to manage and analyze agricultural data. This approach enables the execution of more precise and specific
interventions (Food and Agriculture Organization of the United Nations).

    Concurrently, the digitization of agriculture is contingent upon substantial data from machinery, UAVs, and geoinformation
(Ahmad and Nabi, 2021; Nekouei et al., 2024). The incorporation of remote sensing with machine learning (ML) has been demon­
strated to result in cost and labor savings when compared to conventional field measurements of stress variables, such as water, as
evidenced by Virnodkar et al. (2020). In this vein, the capacity of machine learning and deep learning for the early detection and
enhancement of performance in the soil-plant nexus has been thoroughly documented (Liu et al., 2023; L. Zhang and Zhang, 2022).
Historically, the adoption of DL was described as incipient (Y. Chen et al., 2014). However, recent literature demonstrates widespread
use, although operational adoption requires resources and standardization.

    From an Earth observation perspective, agricultural remote sensing has progressed from early Landsat-based monitoring and the
widespread adoption of spectral vegetation indices such as normalized difference vegetation index-NDVI (Tucker, 1979) to indices
explicitly designed to mitigate soil background and atmospheric effects, including soil-adjusted vegetation index-SAVI (A. R. Huete,
1988) and enhanced vegetation index-EVI in the Moderate Resolution Imaging Spectroradiometer-MODIS era (A. Huete et al.,
2002). This sensor and index evolution, followed by the proliferation of high-revisit constellations and UAV-based multispectral
imaging, has enabled dense time-series analyses that align naturally with modern ML/DL pipelines.

1.2. Scope and contributions of this review

    In this context, the present paper conducts a systematic literature review (SLR) on machine learning (ML) and deep learning (DL)
applied to remote sensing for yield, stress, and classification/segmentation of agricultural and forest cover. The paper integrates
optical (multispectral/hyperspectral), synthetic aperture radar (SAR), light detection and ranging (LiDAR), thermal, and unmanned
aerial vehicle (UAV) data.

    The modernization of the sector through the implementation of machine learning (ML) and deep learning (DL) is evident in
operational solutions, including disease detection, species classification, fertility monitoring, and management, within the framework
of precision agriculture (Saravanan and Bhagavathiappan, 2024; A. Sharma et al., 2021). This overview contextualizes and justifies
SLR, as well as the contributions and methodological gaps that the article develops below.

    To contextualize the evidence synthesized in this review, a brief overview is presented of the evolution of remote sensing-based
decision support in agriculture and forestry and summarized in Fig. 1. Early satellite programs (e.g., Landsat) enabled regional crop
area estimation and productivity monitoring, but coarse spatial resolution, infrequent revisits, and delayed data delivery constrained
field-level decision-making.

    During the 2000s, vegetation indices -particularly the NDVI- emerged as a pragmatic benchmark for monitoring canopy condition
and seasonal dynamics. However, index-based approaches may saturate in dense vegetation and provide limited physiological
specificity, thus motivating the use of richer spectral and temporal information.

    The 2010s witnessed the emergence of advanced observation technologies, characterized by higher resolutions and frequencies (e.
g., Sentinel-2 and commercial constellations). Concurrently, the affordability of unmanned aerial vehicles (UAVs) led to a paradigm

Fig. 1. Timeline of remote sensing (RS) and geospatial artificial intelligence (GeoAI) for agro-environmental monitoring and decision-making.
Source: Own work.

                                                                                                             3
D.A. Gracia Rojas et al.     Remote Sensing Applications: Society and Environment 44 (2026) 102279

shift in applications, transitioning from regional statistics to scales that encompass plot- and management-zone levels. In parallel,
modeling moved from simple regression toward machine learning (e.g., Random Forests-RF, support vector machines-SVM, gradient
boosting), improving predictive accuracy while raising concerns about generalization and interpretability.

    More recently, multi-source integration (optical, SAR, LiDAR, thermal, and ancillary climate/soil variables) has improved
robustness under clouds and heterogeneous management. Since the late 2010s, the advent of deep learning has facilitated end-to-end
feature learning from imagery and time series (e.g., convolutional neural networks for mapping and segmentation; recurrent and
attention-based models for phenology and yield). However, the operational implementation of these models remains contingent upon
the availability of labels, the transferability of models across regions and seasons, the quantification of uncertainty, the computational
cost, and the necessity for transparent decision support. These constraints provide the foundation for the subsequent discussion of
future directions, which is presented in the following sections of this manuscript.

    A growing corpus of literature encompasses reviews on the topics of remote sensing, agriculture, and forestry. However, the
conventional organizational frameworks, which categorize these reviews by crop (e.g., corn, rice, soybeans), sensor (e.g., Sentinel-2,
UAV, SAR), or method family (Random Forest-RF/Support Vector Machine-SVM/Gradient Booted Decision Trees-GBDT; Convolu­
tional Neural Network-CNN/Long Short Term Memory-LSTM/Transformers), offer a fragmented view that impedes cross-domain
comparison and collaboration. A recent, cross-cutting synthesis is lacking in its coverage of all scales, sensors, and techniques
without restriction, in addition to a comparison of model families by task (yield/biomass; classification/segmentation; stress), and a
translation of the evidence into adoption criteria.

    Recent surveys have focused on specific segments of the Remote Sensing-Artificial Intelligence (RS-AI) landscape rather than
providing a comprehensive, cross-disciplinary perspective. For instance, Ariza-Sentís et al. (2024) provide a systematic review of
object detection and tracking in precision farming, centering on computer-vision pipelines rather than cross-sensor or cross-task
comparisons. In their 2022 review, Wang et al. (2022) examined the application of deep learning across various spatial scales,
ranging from leaf to field and beyond. However, their analysis remained predominantly image-model centered, lacking a formal
framework to establish comparability rules among different model families. Task-focused syntheses on yield prediction from remote
sensing--both general deep-learning reviews and UAV-based systematic reviews--also emphasize a single outcome family without
benchmarking model families across classification/segmentation vs. regression tasks or translating evidence into adoption criteria
(Muruganantham et al., 2022). Crop-specific reviews, such as those addressing the potato vegetation index and the timing of growth
monitoring and yield prediction, further illustrate the fragmentation by crop and index (Mukiibi et al., 2025). In light of these con­
siderations, our review is meticulously crosscutting, integrating all major sensors and scales while systematically comparing model
families based on their function (classification/segmentation; yield/biomass; stress). Additionally, it places significant emphasis on
spatiotemporal validation, uncertainty, and cost/latency as fundamental prerequisites for transfer and adoption. Rather than
providing an exhaustive inventory of methods, this review advances the field by enabling cross-task and cross-sensor comparability
and by translating methodological evidence into operational decision criteria.

    This suggests the presence of a knowledge gap: the absence of a comprehensive, comparative, and decision-oriented review that
integrates sensors and methods without distinction, establishes rules of comparability between model families, and explicitly discusses
spatiotemporal validation, uncertainty, and cost/latency as necessary conditions for transfer and adoption. To address this gap, the
present review adopts a two-dimensional analytical framework that is maintained throughout the article. On the application axis, we
distinguish three domains: (1) yield and biomass prediction, (2) land-cover classification and segmentation, and (3) plant health
monitoring and crop management. On the methodological axis, we consider four cross-cutting dimensions: (i) model families (classical
machine learning, deep learning, and hybrid crop-AI schemes), (ii) remote sensor configurations (single-vs. multi-sensor, including
satellite, UAV, proximal, hyperspectral, LiDAR, and optical-SAR fusion), (iii) validation and uncertainty practices (spatiotemporal
data splits, treatment of leakage, uncertainty quantification, and class-wise metrics), and (iv) operational constraints (cost, latency,
and transferability conditions for adoption). The 105 primary studies are mapped onto this 3 × 4 framework, which guides both the
descriptive synthesis in Section 3 and the comprehensive discussion of gaps and adoption criteria in Section 4.

    In the preceding five years, there has been an evolution in the way remote sensing and artificial intelligence intersect in agriculture
and forestry. This development represents a progression from earlier reviews, which were more limited in scope. The increasing
availability of high-resolution and multi-temporal data streams (e.g., Sentinel-2, PlanetScope, UAVs, and new SAR or hyperspectral
missions) is coinciding with a methodological leap--from traditional machine learning (ML) to deep architectures capable of
spatiotemporal reasoning and multimodal fusion. These advances have prompted a shift in the discourse from feasibility to scalability
and generalization, necessitating a synthesis that traces the evolution of performance and data requirements across tasks and envi­
ronments. Consequently, this review captures a period in which the field transitions from experimentation to operational maturity,
offering a timely, comprehensive evaluation of progress and the challenges that persist.

    This article makes four concrete contributions: (i) A cross-cutting taxonomy that organizes the evidence by task (yield/biomass;
land-cover mapping/segmentation; plant stress) × sensor (optical, SAR, thermal, LiDAR, hyperspectral, UAV) × learning family (ML/
DL). (ii) A comparative synthesis that normalizes evidence with explicit rules of comparability by task (priority metrics, class-wise vs.
overall reporting, and strong baselines). (iii) An adoption-oriented reading of the literature using consistent criteria (spatiotemporal
validation schemes, uncertainty calibration, and inference cost/latency). (iv) Aggregated tables and distribution summaries that
surface what performs well under which data and scale conditions.

    Beyond synthesizing methods and results, the objective of this review is to serve as a decision-support tool for individuals involved
in the design, commissioning, or operation of RS-AI systems in agriculture and forestry. The evidence is organized by task and
compared across model families under varying data and scale conditions, thereby providing a structured foundation for selecting
plausible modeling pipelines for monitoring, mapping, and forecasting. The analysis also elucidates the limitations of current

                          4
