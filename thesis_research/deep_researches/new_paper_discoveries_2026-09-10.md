# New Paper Discoveries — 2026-09-10

**Source:** arXiv API + web search  
**Purpose:** Supplementary papers for thesis on disentanglement of concurrent water-salinity stress in sugarcane (Khuzestan)

---

## Category A: Directly Relevant to Thesis

### A1. STS-NET — Self-Supervised Crop Stress Detection via SITS
**arxiv:** https://arxiv.org/abs/2607.18791 | **PDF:** https://arxiv.org/pdf/2607.18791v1  
**Year:** 2026 | **Authors:** Pradeep Dalal, Rajiv Ranjan, Sushil Ghildiyal, Shashank Tamaskar  
**Category:** cs.CV  
**Key Points:**
- Spatio-temporal stress network built on self-supervised 3D-convolutional autoencoder
- Uses Satellite Image Time Series (SITS) data for crop stress detection
- Exploits 4 vegetation indices: NDVI, EVI, NDRE, red-edge
- Addresses the label-scarcity problem directly — unsupervised pre-training
- **Relevance:** Very close to your methodology — SSL + SITS + vegetation indices for stress detection
- **Gap:** Uses VIs as input (not raw bands); no Mamba; no temporal XAI; single-crop

### A2. EigenCL — Unsupervised Crop Stress Detection via Contrastive Learning on NDRE
**arxiv:** https://arxiv.org/abs/2506.03394 | **PDF:** https://arxiv.org/pdf/2506.03394v1  
**Year:** 2025 | **Authors:** Shafqaat Ahmad  
**Category:** cs.CV  
**Key Points:**
- Fully unsupervised contrastive learning framework
- Guided by temporal NDRE dynamics + eigen decomposition
- Tested on 10,000+ Sentinel-2 NDRE patches from drought-affected Io
- Eigenvector-based guidance — learns phenological patterns without labels
- **Relevance:** Shows that vegetation index time series alone can drive unsupervised stress detection
- **Gap:** Only drought (not salinity); only NDRE (not multi-index); no XAI component

### A3. Sugar-Beet Stress Detection using SITS (3D Autoencoder)
**arxiv:** https://arxiv.org/abs/2507.13514 | **PDF:** https://arxiv.org/pdf/2507.13514v1  
**Year:** 2025 | **Authors:** Bhumika Laxman Sadbhave, Philipp Vaeth, Denise Dejon, Gunther Schorcht  
**Category:** cs.CV, cs.LG  
**Key Points:**
- Fully unsupervised approach for sugar-beet stress detection
- 3D convolutional autoencoder extracting features from Sentinel-2 image sequences
- Acquisition-date-specific temporal encodings to capture growth dynamics
- Learnable representations used for stress classification
- **Relevance:** Same crop family (sugar crops), same SITS + SSL paradigm, 3D-CNN approach
- **Gap:** Single stress type (drought/water); no salinity; no XAI

### A4. XAI-Guided Enhancement of Vegetation Indices for Crop Mapping
**arxiv:** https://arxiv.org/abs/2407.08298 | **PDF:** https://arxiv.org/pdf/2407.08298v1  
**Year:** 2024 | **Authors:** Hiba Najjar, Francisco Mena, Marlon Nuske, Andreas Dengel  
**Category:** cs.CV, cs.LG  
**Key Points:**
- Explainable AI method to select/optimize vegetation indices
- Uses XAI (SHAP-like) to understand which spectral bands contribute most
- Goes beyond expert-designed VIs — discovers better combinations
- **Relevance:** XAI applied to vegetation index selection — methodology bridge between your SSL and interpretability goals
- **Gap:** Static mapping (no temporal dimension); no stress discrimination

### A5. Informed Learning — Drought Stress Estimation + Yield Prediction
**arxiv:** https://arxiv.org/abs/2510.18648 | **PDF:** https://arxiv.org/pdf/2510.18648v1  
**Year:** 2025 | **Authors:** Miro Miranda, Marcela Charfuelan, Matias Valdenegro Toro, Andreas Dengel  
**Category:** cs.LG  
**Key Points:**
- Combines crop simulation models (physical) with ML for yield prediction
- PINN-inspired: physics-informed loss functions
- Drought stress estimation at fine spatial resolution
- Bridging physical processes and black-box ML for explainability
- **Relevance:** "Informed learning" is exactly the philosophy — use known crop physiology as constraints
- **Gap:** Only drought; not SITS; not satellite-based spatial prediction

### A6. DeepSalt — Domain Adaptation for Soil Salinity Estimation from Satellite
**arxiv:** https://arxiv.org/abs/2510.23124 | **PDF:** https://arxiv.org/pdf/2510.23124v1  
**Year:** 2025 | **Authors:** Rupasree Dey, Abdul Matin, Everett Lewark, Tanjim Bin Faruk  
**Category:** cs.CV, cs.LG  
**Key Points:**
- Bridges laboratory spectroscopy and satellite hyperspectral data
- Domain adaptation + knowledge distillation for large-scale salinity mapping
- Addresses the domain gap between ground-truth lab measurements and satellite observations
- **Relevance:** Direct methodology for salinity estimation from satellite — you can adapt this for your salt stress label generation
- **Gap:** No stress interaction (salinity-only); no temporal analysis

---

## Category B: Methodology & Plant Stress Physics

### B1. Optical Spectroscopic Imaging for Early Detection of Salinity Stress — Review
**arxiv:** https://arxiv.org/abs/2509.02265 | **PDF:** https://arxiv.org/pdf/2509.02265v1  
**Year:** 2025 | **Authors:** Ramji Gupta, Snehprabha Gujrathi, Swati Sharma, Saurav Bharadwaj  
**Category:** q-bio.QM  
**Key Points:**
- Comprehensive review of fluorescence imaging, hyperspectral imaging, thermal imaging for salinity stress detection
- Covers physiological and biochemical responses of plants to saline conditions
- Links spectral signatures to specific stress mechanisms
- **Relevance:** Essential for understanding what spectral features distinguish salinity from water stress — informs your band selection and SSL pretext tasks
- **Gap:** Ground-based/handheld sensors, not satellite; no DL component

### B2. Crop Response to Climatic Stress — Plant Physiology & Biostimulants Review
**arxiv:** https://arxiv.org/abs/2506.01714 | **PDF:** https://arxiv.org/pdf/2506.01714v2  
**Year:** 2025 | **Authors:** Jing Li, Giulia Forghieri, Danny Geelen, Patrick du Jardin  
**Category:** q-bio.BM, q-bio.GN, q-bio.MN  
**Key Points:**
- Mechanisms of how plants sense and respond to combined abiotic stresses
- Role of plant hormones, biostimulants, and genetic plasticity in stress response
- Discusses synergistic vs antagonistic effects of concurrent stresses
- **Relevance:** Your advisor's key point — mixed stress is interactive, not additive. This paper provides the physiological basis for why you need a "mixed stress" class
- **Gap:** Laboratory/agronomy focus, not remote sensing

### B3. DroughtSet — Spatial-Temporal Learning for Drought
**arxiv:** https://arxiv.org/abs/2412.15075 | **PDF:** https://arxiv.org/pdf/2412.15075v1  
**Year:** 2024 | **Authors:** Xuwei Tan, Qian Zhao, Yanlan Liu, Xueru Zhang  
**Category:** cs.LG  
**Key Points:**
- Dedicated dataset and benchmark for drought understanding
- Spatio-temporal learning approaches for drought monitoring
- Subseasonal-to-seasonal (S2S) prediction horizon
- **Relevance:** Temporal modeling of stress evolution — similar to your 12-year Landsat time series
- **Gap:** Drought-only; climate-scale, not field-scale; no salinity

### B4. Sugarcane Health Monitoring with Satellite Spectroscopy & ML — Review
**arxiv:** https://arxiv.org/abs/2404.16844 | **PDF:** https://arxiv.org/pdf/2404.16844v1  
**Year:** 2024 | **Authors:** Ethan Kane Waters, Carla Chia-Ming Chen, Mostafa Rahimi Azghadi  
**Category:** cs.CV, cs.LG, eess.SP  
**Key Points:**
- **Directly about sugarcane!** Reviews satellite-based health monitoring
- Covers relevant satellites, vegetation indices, ML methods for sugarcane
- Discusses factors influencing sugarcane spectral response
- Disease/pest detection in sugarcane
- **Relevance:** Most relevant review paper for your study crop. Must read carefully for band selection, index choices, and ML method comparisons specific to sugarcane
- **Gap:** General health monitoring, not specifically water-salinity stress disentanglement

### B5. Self-Supervised Contrastive Learning for Irrigation Detection
**arxiv:** https://arxiv.org/abs/2108.05484 | **PDF:** https://arxiv.org/pdf/2108.05484v1  
**Year:** 2021 | **Authors:** Chitra Agastya, Sirak Ghebremusse, Ian Anderson, Colorado Reed  
**Category:** cs.CV, cs.LG  
**Key Points:**
- SSL contrastive learning applied to irrigation water usage detection from satellite imagery
- Addresses unsustainability of crop water demand
- Foundation for understanding how SSL works in agricultural water context
- **Relevance:** SSL methodology for water-related agricultural monitoring — directly applicable to your SSL design
- **Gap:** Irrigation detection, not stress detection; no time series

### B6. Reducing Soil Salinity via Irrigation Management in Arid Regions
**arxiv:** https://arxiv.org/abs/2204.02029 | **PDF:** https://arxiv.org/pdf/2204.02029v1  
**Year:** 2022 | **Authors:** Haiyang Shi  
**Category:** physics.geo-ph  
**Key Points:**
- Remote sensing estimation of soil salinity from 1984-2018
- Bayesian network modeling of salinity dynamics
- Irrigation and water management strategies for salinity reduction
- **Relevance:** Long-term salinity monitoring from space — directly relevant to your 12-year timeline and salinity stress mapping
- **Gap:** No DL; salinity-only; no stress interaction

### B7. ML for Forecasting Remotely Sensed Vegetation Health
**arxiv:** https://arxiv.org/abs/1602.06335 | **PDF:** https://arxiv.org/pdf/1602.06335v4  
**Year:** 2016 | **Authors:** John J. Nay, Emily Burchfield, Jonathan Gilligan  
**Category:** q-bio.OT, stat.AP  
**Key Points:**
- Short-term vegetation health forecasting using ML
- Global coverage, high spatial resolution
- Open-source tool for drought early warning
- **Relevance:** Classical ML approach to vegetation health — good baseline for comparison with your deep learning approach
- **Gap:** No spectral/temporal modeling; no stress type discrimination

---

## Category C: Related Applied Papers

### C1. Low-Cost Sensing for Early Stress & Disease Detection in Avocado
**arxiv:** https://arxiv.org/abs/2508.13379 | **PDF:** https://arxiv.org/pdf/2508.13379v1  
**Year:** 2025 | **Authors:** Abdulrahman Bukhari, Bullo Mamo, Mst Shamima Hossain, Ziliang Zhang  
**Category:** eess.SY  
**Key Points:** Field-deployed sensors for early stress/disease detection; salinity management evaluation  
**Relevance:** Sensor-based stress detection approach — useful for discussing multi-modal fusion possibilities

### C2. Potato Crop Stress Identification in Aerial Images using DL Object Detection
**arxiv:** https://arxiv.org/abs/2106.07770 | **PDF:** https://arxiv.org/pdf/2106.07770v3  
**Year:** 2021 | **Authors:** Sujata Butte, Aleksandar Vakanski, Kasia Duellman, Haotian Wang  
**Category:** cs.CV, cs.LG  
**Key Points:** Deep learning-based object detection for crop stress in aerial imagery; practical field deployment considerations  
**Relevance:** Shows limitations of pixel-wise/object-detection approaches vs. time-series approach

### C3. ScopeMamba-YOLO — Small Object Detection in RS using Mamba
**arxiv:** https://arxiv.org/abs/2609.10156 | **PDF:** https://arxiv.org/pdf/2609.10156v1  
**Year:** 2026 | **Authors:** Junjie Fan, Yijun Mai, Linduo Wei, Jiayu Rao  
**Category:** cs.CV  
**Key Points:** Mamba architecture adapted for remote sensing object detection; selective scanning for small targets  
**Relevance:** Alternative Mamba implementation — could inspire architectural choices for your CNN-Mamba hybrid

### C4. Sentinel-2 for Crop Yield Estimation — Systematic Review
**arxiv:** https://arxiv.org/abs/2603.23779 | **PDF:** https://arxiv.org/pdf/2603.23779v1  
**Year:** 2026 | **Authors:** Mohammadreza Narimani, Alireza Pourreza, Ali Moghimi, Parastoo Farajpoor  
**Category:** eess.IV, physics.geo-ph  
**Key Points:** Comprehensive review of Sentinel-2 yield estimation; shift from regional to field-level assessments  
**Relevance:** Shows current state-of-the-art in satellite-based yield/stress monitoring

### C5. Branched Broomrape Detection in Tomato Farms Using Satellite Imagery & Time-Series
**arxiv:** https://arxiv.org/abs/2509.10804 | **PDF:** https://arxiv.org/pdf/2509.10804v1  
**Year:** 2025 | **Authors:** Mohammadreza Narimani, Alireza Pourreza, Ali Moghimi  
**Category:** eess.IV, cs.AI, cs.CV, cs.LG  
**Key Points:** SITS-based detection of plant parasitic weed infestation  
**Relevance:** Time-series approach for plant stress/health degradation — methodological parallel

### C6. JEDI: JEPA-to-Edge Distillation for Cropland Segmentation
**arxiv:** https://arxiv.org/abs/2609.07915 | **PDF:** https://arxiv.org/pdf/2609.07915v1  
**Year:** 2026 | **Authors:** Kishor Kumar Bhaumik, Nicolas Roque dos Santos, Jia Chen, Evangelos E. Papalexakis  
**Category:** cs.CV, cs.LG  
**Key Points:** Vision foundation model distillation for satellite segmentation; efficient edge deployment  
**Relevance:** Shows direction of foundation model adoption in RS — could inform future work

---

## Persian/Iranian Papers

Due to API limitations, direct search from Iranian academic databases (SID.ir, Magiran, Noormags, Civilica) was blocked. Search these manually:

**Recommended search terms for Persian papers:**
- «تشخیص تنش آبی شوری遥感» (water-salinity stress detection remote sensing)
- «بررسی اثرات شوری خاک بر عملکرد گندم و جو» (soil salinity effects on wheat/barley yield)
- «پایش遥感 منابع آب کشاورزی» (agricultural water resources remote sensing monitoring)
- «شاخصهای گیاهی تشخیص خشکی» (vegetation indices for drought detection)
- «تنش همزمان خشکی و شوری» (concurrent drought and salinity stress)
- «مدلسازی تنش آبی گیاهان با استفاده از دادههای ماهوارهای» (plant water stress modeling using satellite data)

**Key Iranian journals to check:**
- Journal of Agricultural Science and Sustainable Production (علوم کشاورزی و تولید پایدار)
- Irrigation Sciences (علوم آبیاری)
- Iranian Journal of Crop Science (مجله علوم کشاورزی ایران)
- Agricultural Economics Research (اقتصاد کشاورزی)
- Water and Soil (آب و خاک)

---

## How These Papers Connect to Your Thesis

```
Your Proposed Framework: CNN-Mamba + SSL + Temporal XAI
        │
        ├─→ SSL Foundation: STS-NET (A1), EigenCL (A2), Agastya (B5)
        │         Used: 3D-CAE for feature extraction, contrastive learning on VI time series
        │
        ├─→ Mamba Architecture: SITSMamba (advisor), ScopeMamba (C3)
        │         Used: Selective state-space for long-sequence processing
        │
        ├─→ Sugarcane Specifics: Waters Review (B4), Motlagh et al. (Khuzestan)
        │         Used: Band selection, index choices, Ky factor calibration
        │
        ├─→ Salinity Component: DeepSalt (A6), Shi (B6), Paciolla (advisor)
        │         Used: Salinity spectral signatures, LAI-as-proxy approach
        │
        ├─→ Stress Physics: Angon (advisor), Li (B2), Gupta (B1)
        │         Used: Physiological basis for mixed-stress class design
        │
        └─→ XAI/Explainability: Höhl (advisor), Ahmed (advisor), Najjar (A4)
                  Used: SHAP/attention-based interpretation of model decisions
```

---

## Download Commands (if needed)

```bash
# Batch download all PDFs
for id in 2607.18791 2506.03394 2507.13514 2407.08298 2510.18648 2510.23124 \
          2509.02265 2506.01714 2412.15075 2404.16844 2108.05484 2204.02029 \
          1602.06335 2508.13379 2106.07770 2609.10156 2603.23779 2509.10804 2609.07915; do
    curl -L -o "papers_new/${id}.pdf" "https://arxiv.org/pdf/${id}"
done
```
