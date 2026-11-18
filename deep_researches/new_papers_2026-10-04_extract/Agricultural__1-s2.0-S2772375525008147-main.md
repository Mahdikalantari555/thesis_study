# Extract: 1-s2.0-S2772375525008147-main.pdf

*First ~4 pages, extracted with pdftotext on 2026-10-04. Source: D:\RS\Thesis\New_papers$f*

---

                                                                 Smart Agricultural Technology 12 (2025) 101583
                                                                  Contents lists available at ScienceDirect

                                                Smart Agricultural Technology

                                      journal homepage: www.journals.elsevier.com/smart-agricultural-technology

Multi-dimensional optical remote sensing in agriculture: Spectral, angular,
and spatial scaling for crop stress monitoring

Syed Ijaz Ul Haq a,b , Guobin Wang a,b, Shahid Nawaz Khan d, Cancan Song a,b,*, Cong Ma c,
Xuejian Zhang c, Yubin Lan a,b,*

a College of Agricultural Engineering and Food Science, Shandong University of Technology, Zibo 255049, China
b Shandong University of Technology Sub-Center of National Center for International Collaboration Research on Precision Agricultural Aviation Pesticide Spraying
Technology, Zibo 255049, China
c Institute of Agricultural Economy and Information Technology, Ningxia Academy of Agriculture and Forestry Sciences, China
d Institute of Geographical Information Systems, National University of Sciences and Technology (NUST), Islamabad, Pakistan

ARTICLE INFO                          ABSTRACT

Keywords:                             Early and accurate detection of crop stress is essential for sustainable agriculture and food security, particularly
Crop stress detection                 as climate change and environmental degradation intensify agricultural challenges. This comprehensive review
Multi-dimensional remote sensing      examines advanced crop stress monitoring strategies that leverage multi-dimensional optical remote sensing
Spectral-angular-spatial integration  approaches, specifically integrating spectral, angular, and spatial perspectives across diverse observation scales.
Precision agriculture                 We systematically analyze how biotic stresses (diseases, pests) and abiotic stresses (drought, nutrient deficiency,
UAV monitoring                        temperature extremes) manifest through detectable changes in plant spectral signatures, from chlorophyll
                                      degradation in the visible spectrum to water content variations in shortwave infrared regions. Our review en­
                                      compasses sensing technologies spanning RGB, multispectral, hyperspectral, thermal infrared, and chlorophyll
                                      fluorescence sensors deployed across three complementary scales: proximal ground-based systems for detailed
                                      physiological assessment, unmanned aerial vehicles (UAVs) for field-scale monitoring, and satellites for regional
                                      surveillance. A key innovation of this work is the emphasis on multi-angle remote sensing, which captures
                                      bidirectional reflectance distribution function (BRDF) effects that reveal stress-induced changes in canopy
                                      structure and leaf orientation invisible to conventional nadir-only observations. We demonstrate how viewing
                                      geometry significantly affects vegetation indices (NDVI, PRI) and sun-induced fluorescence (SIF) measurements,
                                      requiring sophisticated angular correction methods for accurate stress assessment. Through synthesis of 138
                                      recent studies spanning 12 major crop types, we identify critical research gaps including: (1) inconsistent angular
                                      reflectance modeling across stress types, (2) inadequate sensor calibration protocols for variable field conditions,
                                      and (3) lack of standardized frameworks for integrating multi-source, multi-scale data streams. Our analysis
                                      reveals that advanced machine learning approaches particularly deep learning and transformer networks show
                                      exceptional promise for extracting meaningful stress signatures from complex, high-dimensional datasets while
                                      maintaining interpretability for agricultural decision-making. We propose a hierarchical monitoring architecture
                                      supported by physics-aware artificial intelligence models that address three fundamental challenges: temporal
                                      optimization for capturing stress progression dynamics, spatial integration across observation scales, and angular
                                      standardization for consistent stress quantification. This framework aims to transform crop stress monitoring
                                      from reactive management to predictive intervention, enabling real-time diagnostics suitable for diverse agri­
                                      cultural systems ranging from high-value specialty crops to extensive grain production. The review concludes
                                      with a strategic roadmap for operational implementation, addressing economic constraints, technological limi­
                                      tations, and knowledge transfer requirements necessary for widespread adoption. Our findings indicate that
                                      successful deployment requires service-based delivery models, simplified decision support interfaces, and staged
                                      implementation approaches that demonstrate incremental value while building organizational capacity. The
                                      literature selection was conducted using Scopus, Web of Science, and IEEE Xplore databases, covering publi­
                                      cations from 2018 to 2024. Search terms included "crop stress monitoring," "spectral remote sensing," "multi-
                                      angle sensing," and "UAV agriculture." A total of 138 peer-reviewed studies meeting relevance and

  * Coresponding authors at: College of Agricultural Engineering and Food Science, Shandong University of Technology, Zibo 255049, China.
     E-mail addresses: songcc@sdut.edu.cn (C. Song), ylan@sdut.edu.cn (Y. Lan).

https://doi.org/10.1016/j.atech.2025.101583
Received 29 August 2025; Received in revised form 23 October 2025; Accepted 27 October 2025
Available online 28 October 2025
2772-3755/© 2025 The Author(s). Published by Elsevier B.V. This is an open access article under the CC BY-NC-ND license (http://creativecommons.org/licenses/by-
nc-nd/4.0/).
S.I.U. Haq et al.                                                                                                           Smart Agricultural Technology 12 (2025) 101583

                   methodological rigor criteria were included. These studies span 12 major crop types: wheat, maize, rice, soybean,
                   cotton, sugarcane, potato, grapevine, tomato, barley, sorghum, and rapeseed, ensuring broad coverage across
                   cereal, legume, fiber, tuber, and horticultural crops.

1. Introduction                                                                 often detected using RGB or texture analysis from drone-based imaging
                                                                                [30]. Specifically, crop stress in this review is categorized into two
    Global agriculture is increasingly challenged by biotic and abiotic         primary types: (1) abiotic stresses, including drought, salinity, extreme
stress factors, including pests, diseases, drought, nutrient deficiency,        temperature (heat and frost), nutrient imbalance, and soil compaction,
and heatwaves, all of which contribute to reduced crop productivity and         and (2) biotic stresses such as fungal, bacterial, and viral pathogen in­
food insecurity [1,2]. Timely identification and monitoring of such             fections, insect pest infestations, and competitive pressure from weeds.
stress conditions have therefore become central to precision agriculture        Each of these stressors induces unique physiological and structural
and sustainable crop management [3,4]. Optical remote sensing has               changes for example, water stress alters canopy temperature and leaf
emerged as a powerful, non-invasive solution for detecting plant stress         inclination detectable through thermal and angular sensing, while
through spectral signatures that reflect physiological and structural           nutrient deficiencies shift red-edge reflectance patterns observable
changes at the canopy, leaf, or landscape scale [5,6]. In recent years, the     through hyperspectral indices. Although many optical remote sensing
development of high-resolution RGB, multispectral, hyperspectral, and           techniques have applications beyond stress detection (e.g., yield esti­
thermal sensors has enabled early detection of subtle stress symptoms           mation or crop classification), this review focuses specifically on their
such as chlorophyll degradation, stomatal closure, and reduced leaf             adaptation and relevance to stress diagnosis and progression moni­
water content before visual indicators are observable [7-9].                    toring. The fusion of multispectral and thermal sensors has proven
                                                                                effective in distinguishing drought from disease-induced stress, espe­
    Despite progress in sensor technologies, a major bottleneck remains         cially under fluctuating environmental conditions [31,32]. Recent ad­
the lack of integration across scales and angles. Single-source data often      vances also highlight the utility of vegetation indices (e.g., NDVI, PRI)
suffer from spatial, angular, or temporal limitations, restricting their        and chlorophyll fluorescence (SIF 670-780 nm) in detecting subtle stress
capacity to generalize across environments or crop types [10,11]. To            changes before visual symptoms appear [33,34]. These optical signals,
overcome this, researchers have explored synergistic sensor configura­          however, are influenced by factors like phenological stage and envi­
tions that combine proximal, airborne (UAV), and satellite-based remote         ronmental variability, which must be accounted for during interpreta­
sensing for continuous multi-scale observation [12-14]. Likewise,               tion [35].
viewing geometry significantly affects reflectance properties and vege­
tation indices, necessitating multi-angle acquisition strategies to reduce          Fig. 1 illustrates the conceptual framework of our approach, where
errors caused by bidirectional reflectance distribution function (BRDF)         crop stress detection is guided by spectral feature analysis and inte­
effects [15,16]. However, integrating multi-scale, multi-sensor, and            grated with remote sensing across varying observation conditions. The
multi-angle data presents computational and methodological chal­                diagram highlights how stress symptoms observable in the crop canopy
lenges, particularly in heterogeneous field environments [17].                  such as wilting, discoloration, or leaf senescence are identified using
                                                                                data from multiple sources including UAVs, proximal field sensors, and
    Emerging deep learning and transformer-based models show prom­              satellite platforms. These platforms enable the application of multi-
ise in extracting meaningful features from complex, high-dimensional            angle (e.g., UAVs for oblique imaging), multi-scale (e.g., combining
datasets by learning temporal, spatial, and spectral patterns simulta­          leaf-level and landscape-level observations), and multi-sensor (e.g.,
neously [18,19]. These approaches have improved classification accu­            thermal, multispectral, hyperspectral) strategies. This synergy enhances
racy for stress types and severity levels, though many remain confined to       the temporal and spatial granularity of monitoring systems, ultimately
experimental settings with limited operational deployment [20,21].              contributing to early and robust stress detection in real-world agricul­
Therefore, there is a pressing need for a unified framework that not only       tural environments,
bridges spatial and angular resolution gaps but also incorporates
physics-aware AI for scalable crop monitoring. This review addresses            1.2. Plant stress stages
these challenges by systematically analyzing the literature on crop stress
detection using spectral synergies across multiple angles, scales, and              Understanding the temporal progression of plant stress is crucial for
sensor types. We highlight key developments in sensor fusion, vegeta­           effective intervention. Generally, crop stress evolves through four pri­
tion index optimization, and data integration workflows, while identi­          mary stages: pre-symptomatic, early, advanced, and chronic, Fig. 2
fying open issues in field validation and model generalizability [22,23].       present the stress stages [36]. In the pre-symptomatic phase,
Ultimately, our study provides a roadmap for operationalizing smart             sun-induced chlorophyll fluorescence (SIF) and hyperspectral vegeta­
agricultural monitoring systems that can deliver real-time, reliable, and       tion indices (e.g., PRI) serve as sensitive indicators of emerging stress
robust crop stress diagnostics under varying field conditions.                  [37]. During the early stress stage, pigment variation and thermal
                                                                                anomalies (e.g., T > 2C between canopy and air) become more
1.1. Stress definition and symptoms                                             apparent, detectable via multispectral cameras and thermal IR imaging
                                                                                [17,38]. Advanced stress manifests in significant drops in NDVI and RVI
    Plant stress is broadly defined as a physiological condition where          and noticeable structural deformation captured by UAV-based RGB
adverse biotic or abiotic factors disrupt normal plant functions, ulti­         imaging [39] Chronic stress, often irreversible, is tracked over longer
mately leading to reduced growth, yield, and quality [24]. Biotic stresses      periods using satellite-derived time-series data [40,41]. Modern AI
include pathogen infections, pest attacks, and weed interference [25],          models, particularly deep learning and transformer architectures, now
while abiotic stresses stem from drought, salinity, extreme temperature,        facilitate automated stage classification by learning from
and nutrient imbalances [26]. These stressors result in distinct                temporal-spectral features across multiple sensor types [42,43]. How­
biochemical, physiological, and structural changes within the plant that        ever, variations in sun-canopy-sensor geometry especially at oblique
can be captured through optical remote sensing techniques. Early stress         angles can distort spectral signatures and complicate accurate stage
indicators such as chlorophyll degradation (450-700 nm), flavonoid              identification [44,45].
accumulation (300-400 nm), and reduced leaf water content (SWIR
1450-1900 nm) are traceable using hyperspectral and thermal imaging                 Our review builds upon these foundations by critically evaluating the
[27-29]. Structural symptoms like leaf curling and canopy thinning are          interplay of multi-angle, multi-scale, and multi-sensor synergies in crop

                                                                             2
S.I.U. Haq et al.                                                                                                                   Smart Agricultural Technology 12 (2025) 101583

stress detection. Specifically, we focus on three underexplored areas: (1)   stress monitoring: sensor types, spectral feature extraction, and quan­
angular variations in reflectance and their influence on stress feature      titative model applications.
visibility, (2) hierarchical fusion of proximal, UAV, and satellite sensors
for spatial-scale continuity, and (3) integrating temporal, spatial, and         Fig. 3 presents the conceptual framework for remote sensing-based
spectral data via physics-aware machine learning [46-48]. Notably, we        crop stress monitoring. The process initiates with diverse sensor sys­
identify the role of canopy bidirectional reflectance distribution func­     tems including RGB, multispectral, hyperspectral, thermal infrared, and
tions (BRDF) in improving stress mapping precision across different crop     fluorescence sensors that capture key physiological and structural plant
types [49]. Our synthesis covers 47 unique sensor setups spanning 12         responses. Through spectral analysis, vegetation indices and advanced
major crops, addressing real-world challenges in spectral noise, platform    spectral features are extracted, while correcting for angular effects and
limitations, and ecological variability [9,50,51]. Section 2 elaborates on   selecting the most informative features using machine learning-driven
sensor-based spectral diagnostics and introduces the latest hardware         dimensionality reduction. These spectral indicators feed into quantita­
innovations, including portable snapshot systems and MIMO-SAR im­            tive modeling pipelines, ranging from classical statistical models to
aging [52,53]. Section 3 describes the multi-scale remote sensing            modern deep learning architectures and physics-aware AI systems.
framework, incorporating proximal tools [54], UAV technologies [55],         Stress indicators such as pigment degradation, water content reduction,
and satellite-based platforms [56]. Section 4 examines angular de­           and canopy structure alteration serve as biological anchors linking
pendency effects on vegetation indices [57], and Section 5 offers rec­       spectral signals to plant health status. Finally, these integrated models
ommendations for optimizing temporal and spatial integration pipelines       support practical agricultural applications including early stress detec­
through AI-powered systems [58,59]. This work aims to bridge knowl­          tion, precision management, yield forecasting, and decision-support
edge gaps and guide future research toward robust, scalable, and             systems. The framework highlights the essential synergy among sensor
real-time crop stress detection strategies.                                  technology, data analytics, and application-driven design necessary for
                                                                             robust crop stress monitoring in dynamic field environments.
    Table 1 summarizes the key physiological symptoms, spectral sig­
natures, optimal sensors, and detection indices associated with different    2.1. Sensor monitoring
crop stress stages. This characterization enables precise mapping of
stress progression and guides sensor selection for operational agricul­          Sensor-based crop monitoring leverages diverse instruments capable
tural monitoring systems.                                                    of capturing different spectral, thermal, and structural signals from plant
                                                                             canopies. RGB sensors offer low-cost and high-frequency observations
2. Remote sensing for stress monitoring                                      but are often limited to detecting visible stress symptoms such as leaf
                                                                             yellowing or canopy thinning [60]. Multispectral sensors, typically
    Remote sensing has revolutionized the field of crop stress monitoring    covering 5-10 bands across visible and near-infrared regions, enable the
by offering scalable, non-invasive, and temporally consistent methods to     calculation of vegetation indices like NDVI, PRI, and REIP, providing
detect physiological and structural alterations in plants. Unlike tradi­     earlier indicators of stress conditions [61,62]. Hyperspectral sensors,
tional ground-based sampling, optical and thermal sensors mounted on         with hundreds of narrow contiguous bands (400-2500 nm), facilitate
proximal platforms, UAVs, and satellites capture dynamic vegetation          fine-grained biochemical trait retrieval such as chlorophyll, carotenoid,
responses over large areas with fine spatial and temporal resolution         and water content estimation [63]. Thermal infrared sensors detect
[59]. This section elaborates the key elements of remote sensing-based       canopy temperature anomalies, critical for identifying water stress via

Fig. 1. Conceptual overview of crop stress monitoring and detection using spectral synergies through remote sensing, combining multi-angle, multi-scale, and multi-
sensor approaches.

                                                                                                                          3
S.I.U. Haq et al.                                                                                                                   Smart Agricultural Technology 12 (2025) 101583

transpiration deficits [64]. Fluorescence sensors, particularly for              Angular effects must be carefully accounted for during spectral
sun-induced chlorophyll fluorescence (SIF), offer pre-visual stress          analysis. Changes in sun-sensor viewing geometry induce bidirectional
detection linked to photosynthetic efficiency [65].                          reflectance variations, impacting VI values and potentially leading to
                                                                             erroneous stress interpretation [70]. Therefore, BRDF correction models
    Platform integration further enhances sensor utility: proximal           or multi-angle acquisition strategies are recommended to normalize
handheld sensors allow leaf-level biophysical characterization, UAV-         spectral measurements and improve stress signal stability across con­
mounted payloads bridge field- and canopy-scale monitoring with              ditions [71]. Recently, feature extraction through machine learning
flexible revisit times, and satellite sensors offer continuous, large-scale  techniques like principal component analysis (PCA), partial least
observations [66]. Multi-sensor synergy thus ensures comprehensive           squares (PLS), and manifold learning has enabled the selection of the
stress detection across multiple spatial and temporal scales.                most informative spectral features, reducing dimensionality while pre­
                                                                             serving diagnostic power [72].
2.2. Spectral analysis
                                                                             2.3. Quantitative model application
    Spectral analysis involves extracting meaningful features from raw
sensor data to diagnose plant stress. Vegetation indices (VIs) remain the        Quantitative models translate spectral observations into actionable
most common approach, combining reflectance at specific bands to             stress diagnostics by establishing predictive relationships between
amplify physiological signals while suppressing background noise [67].       spectral features and plant physiological states. Statistical approaches
Traditional indices like NDVI are sensitive to chlorophyll content, while    such as multiple linear regression (MLR) and generalized additive
enhanced indices such as EVI and PRI capture canopy structure and            models (GAM) provide interpretable, physics-based stress estimation
photosynthetic light-use efficiency, respectively [68]. Advances in          [73]. However, with the increasing complexity of spectral datasets,
hyperspectral analytics have introduced narrowband indices and de­           machine learning methods have become predominant.
rivative spectroscopy to detect pigment degradation, cell structure
breakdown, and water status with greater precision [69].                         Supervised learning algorithms, including random forests, support

Fig. 2. Stages of plant stress progression. The diagram illustrates the sequential stress phases in plants: beginning with a healthy physiological state, followed by
hormonal signaling, then progressing to internal physiological alterations, and finally culminating in visible tissue damage. Early-stage detection particularly during
the hormonal and physiological phases is crucial for precision agriculture applications, as remote sensing technologies can identify subtle spectral and thermal
changes before symptoms become visually apparent.

                                                                                                                          4
