# Literature Search Results — Crop Stress & Remote Sensing

**Date:** 2026-09-10  
**Search Terms:** crop stress detection, salinity/water stress, SITS, SSL, XAI, sugarcane, vegetation indices

---

## 🔥 MUST READ — Directly Relevant to Your Thesis

### 1. STS-NET: Self-Supervised Crop Stress Detection using Satellite Image Time Series
```
Authors: Pradeep Dalal, Rajiv Ranjan, Sushil Ghildiyal, Shashank Tamaskar
Year: 2026 | arXiv: 2607.18791
PDF: https://arxiv.org/pdf/2607.18791v1
Abs: https://arxiv.org/abs/2607.18791
```
**Why relevant:** Uses self-supervised 3D-convolutional autoencoder on SITS data with 4 vegetation indices (NDVI, EVI, NDRE, red-edge). Addresses label scarcity — exactly your problem with 490 farms.

### 2. EigenCL: Unsupervised Crop Stress Detection via Contrastive Learning on NDRE
```
Authors: Shafqaat Ahmad
Year: 2025 | arXiv: 2506.03394
PDF: https://arxiv.org/pdf/2506.03394v1
Abs: https://arxiv.org/abs/2506.03394
```
**Why relevant:** Eigenvector-guided contrastive learning on temporal NDRE dynamics. Tests on 10,000+ Sentinel-2 patches. Shows VI time series alone can drive unsupervised stress detection.

### 3. Sugarcane Health Monitoring with Satellite Spectroscopy & ML: Review
```
Authors: Ethan Kane Waters, Carla Chia-Ming Chen, Mostafa Rahimi Azghadi
Year: 2024 | arXiv: 2404.16844
PDF: https://arxiv.org/pdf/2404.16844v1
Abs: https://arxiv.org/abs/2404.16844
```
**Why relevant:** **Directly about sugarcane!** Reviews satellites, VIs, and ML methods for sugarcane health monitoring. Essential for your band selection and index choices.

### 4. Sugar-Beet Stress Detection using Satellite Image Time Series (3D-AE)
```
Authors: Bhumika Laxman Sadbhave, Philipp Vaeth, Denise Dejon, Gunther Schorcht
Year: 2025 | arXiv: 2507.13514
PDF: https://arxiv.org/pdf/2507.13514v1
Abs: https://arxiv.org/abs/2507.13514
```
**Why relevant:** Same sugar-crop family. 3D CNN autoencoder on Sentinel-2 sequences with temporal encodings. Methodological blueprint for your architecture.

---

## 🎯 HIGH RELEVANCE — Methodology & Physics

### 5. DeepSalt: Domain Adaptation for Soil Salinity Estimation from Satellite
```
Authors: Rupasree Dey, Abdul Matin, Everett Lewark, Tanjim Bin Faruk
Year: 2025 | arXiv: 2510.23124
PDF: https://arxiv.org/pdf/2510.23124v1
Abs: https://arxiv.org/abs/2510.23124
```
**Why relevant:** Bridges lab spectroscopy ↔ satellite hyperspectral data using domain adaptation. Key for generating salinity stress labels without ground ECe measurements.

### 6. XAI-Guided Enhancement of Vegetation Indices for Crop Mapping
```
Authors: Hiba Najjar, Francisco Mena, Marlon Nuske, Andreas Dengel
Year: 2024 | arXiv: 2407.08298
PDF: https://arxiv.org/pdf/2407.08298v1
Abs: https://arxiv.org/abs/2407.08298
```
**Why relevant:** Uses SHAP-based explainability to optimize vegetation indices. Bridges your XAI goal with practical index selection.

### 7. Optical Spectroscopic Imaging for Early Detection of Salinity Stress: Review
```
Authors: Ramji Gupta, Snehprabha Gujrathi, Swati Sharma, Saurav Bharadwaj
Year: 2025 | arXiv: 2509.02265
PDF: https://arxiv.org/pdf/2509.02265v1
Abs: https://arxiv.org/abs/2509.02265
```
**Why relevant:** Covers fluorescence, hyperspectral, and thermal imaging for salinity stress. Links spectral signatures to physiological mechanisms — informs your band selection.

### 8. Informed Learning for Drought Stress Estimation + Yield Prediction
```
Authors: Miro Miranda, Marcela Charfuelan, Matias Valdenegro Toro, Andreas Dengel
Year: 2025 | arXiv: 2510.18648
PDF: https://arxiv.org/pdf/2510.18648v1
Abs: https://arxiv.org/abs/2510.18648
```
**Why relevant:** Combines crop simulation models (physical) with ML using PINN-style losses. Your advisor's philosophy: use physics as constraints, not black-box attribution.

### 9. Crop Response to Climatic Stress: Plant Physiology Review
```
Authors: Jing Li, Giulia Forghieri, Danny Geelen, Patrick du Jardin
Year: 2025 | arXiv: 2506.01714
PDF: https://arxiv.org/pdf/2506.01714v2
Abs: https://arxiv.org/abs/2506.01714
```
**Why relevant:** Explains why mixed stress is interactive (not additive). Hormonal/biochemical basis for your "mixed stress" class design.

### 10. Reducing Soil Salinity via Irrigation Management in Arid Regions
```
Authors: Haiyang Shi
Year: 2022 | arXiv: 2204.02029
PDF: https://arxiv.org/pdf/2204.02029v1
Abs: https://arxiv.org/abs/2204.02029
```
**Why relevant:** 34-year satellite salinity monitoring (1984-2018). Bayesian network for salinity dynamics. Long-term perspective directly applicable to your 12-year Landsat timeline.

---

## 📊 BASELINE COMPARISONS — Classical Methods

### 11. Remote Sensing Based Crop Health Classification Using NDVI and FCNN
```
Authors: J. Judith, R. Tamilselvi, M. Parisa Beham
Year: 2025 | arXiv: 2504.10522
PDF: https://arxiv.org/pdf/2504.10522v1
Abs: https://arxiv.org/abs/2504.10522
```
**Why relevant:** Simple NDVI + fully connected NN baseline. Shows what classical approaches achieve vs. your deep learning method.

### 12. ML for Forecasting Remotely Sensed Vegetation Health
```
Authors: John J. Nay, Emily Burchfield, Jonathan Gilligan
Year: 2016 | arXiv: 1602.06335
PDF: https://arxiv.org/pdf/1602.06335v4
Abs: https://arxiv.org/abs/1602.06335
```
**Why relevant:** Open-source NDVI forecasting tool. Classical ML baseline for drought monitoring.

### 13. Perspectives and Insight toward Solving Flaws of Vegetation Indices
```
Authors: A. Khaliduzzaman, S. Yamamoto, Y. Nishimura
Year: 2022 | arXiv: 2212.00569
PDF: https://arxiv.org/pdf/2212.00569v1
Abs: https://arxiv.org/abs/2212.00569
```
**Why relevant:** Critiques VI limitations (saturation, soil background effects). Important for justifying your raw-band approach.

### 14. Latent Dirichlet Allocation Uncovers Spectral Characteristics of Drought Stressed Plants
```
Authors: Mirwaes Wahabzada, Kristian Kersting, Christian Bauckhage
Year: 2012 | arXiv: 1210.4919
PDF: https://arxiv.org/pdf/1210.4919v1
Abs: https://arxiv.org/abs/1210.4919
```
**Why relevant:** Early work using LDA (classical ML) to discover spectral drought signatures. Historical context for your DL approach.

---

## 🔧 METHODOLOGY REFERENCE — SSL & Mamba

### 15. Self-Supervised Contrastive Learning for Irrigation Detection
```
Authors: Chitra Agastya, Sirak Ghebremusse, Ian Anderson, Colorado Reed
Year: 2021 | arXiv: 2108.05484
PDF: https://arxiv.org/pdf/2108.05484v1
Abs: https://arxiv.org/abs/2108.05484
```
**Why relevant:** SSL methodology for water-related agricultural RS task. Foundation for your contrastive pre-training design.

### 16. ScopeMamba-YOLO: Mamba for Small Object Detection in RS
```
Authors: Junjie Fan, Yijun Mai, Linduo Wei, Jiayu Rao
Year: 2026 | arXiv: 2609.10156
PDF: https://arxiv.org/pdf/2609.10156v1
Abs: https://arxiv.org/abs/2609.10156
```
**Why relevant:** Alternative Mamba implementation for RS. May inspire architectural choices for your CNN-Mamba hybrid.

---

## 📚 ADDITIONAL CONTEXT PAPERS

### 17. Sentinel-2 for Crop Yield Estimation: Systematic Review
```
Authors: Mohammadreza Narimani, Alireza Pourreza, Ali Moghimi, Parastoo Farajpoor
Year: 2026 | arXiv: 2603.23779
PDF: https://arxiv.org/pdf/2603.23779v1
Abs: https://arxiv.org/abs/2603.23779
```

### 18. Branched Broomrape Detection in Tomato Farms Using SITS
```
Authors: Mohammadreza Narimani, Alireza Pourreza, Ali Moghimi
Year: 2025 | arXiv: 2509.10804
PDF: https://arxiv.org/pdf/2509.10804v1
Abs: https://arxiv.org/abs/2509.10804
```

### 19. DroughtSet: Spatial-Temporal Learning for Drought Understanding
```
Authors: Xuwei Tan, Qian Zhao, Yanlan Liu, Xueru Zhang
Year: 2024 | arXiv: 2412.15075
PDF: https://arxiv.org/pdf/2412.15075v1
Abs: https://arxiv.org/abs/2412.15075
```

### 20. Potato Crop Stress Identification in Aerial Images using DL
```
Authors: Sujata Butte, Aleksandar Vakanski, Kasia Duellman, Haotian Wang
Year: 2021 | arXiv: 2106.07770
PDF: https://arxiv.org/pdf/2106.07770v3
Abs: https://arxiv.org/abs/2106.07770
```

---

## 🇮🇷 PERSIAN PAPERS — Manual Search Required

Due to API blocks on SID.ir and IranDoc, search manually with these terms:

**برای پایش遥感 منابع آب کشاورزی:**
- «تنش آبی شوری遥感» (water-salinity stress remote sensing)
- «پایش遥感 تنش خشکی شوری» (remote sensing drought-salinity stress monitoring)
- «شاخصهای گیاهی تشخیص تنش» (vegetation indices for stress detection)
- «مدلسازی تنش آبی با دادههای ماهوارهای» (plant water stress modeling with satellite data)

**نشریات کلیدی:**
- Journal of Agricultural Science and Sustainable Production (علوم کشاورزی و تولید پایدار)
- Irrigation Sciences (علوم آبیاری)
- Iranian Journal of Crop Science (مجله علوم کشاورزی ایران)
- Water and Soil (آب و خاک)

---

## 📥 BATCH DOWNLOAD COMMAND

```bash
# Create folder and download all PDFs
mkdir -p papers_new && cd papers_new

# Core papers (1-10)
curl -L -o "01_STS-NET.pdf" "https://arxiv.org/pdf/2607.18791v1"
curl -L -o "02_EigenCL.pdf" "https://arxiv.org/pdf/2506.03394v1"
curl -L -o "03_Sugarcane_Review.pdf" "https://arxiv.org/pdf/2404.16844v1"
curl -L -o "04_SugarBeet_SITS.pdf" "https://arxiv.org/pdf/2507.13514v1"
curl -L -o "05_DeepSalt.pdf" "https://arxiv.org/pdf/2510.23124v1"
curl -L -o "06_XAI_VI.pdf" "https://arxiv.org/pdf/2407.08298v1"
curl -L -o "07_Salinity_Spectroscopy_Review.pdf" "https://arxiv.org/pdf/2509.02265v1"
curl -L -o "08_Informed_Learning.pdf" "https://arxiv.org/pdf/2510.18648v1"
curl -L -o "09_Plant_Stress_Physiology.pdf" "https://arxiv.org/pdf/2506.01714v2"
curl -L -o "10_Salinity_Irrigation.pdf" "https://arxiv.org/pdf/2204.02029v1"

# Baseline papers (11-14)
curl -L -o "11_NDVI_FCNN.pdf" "https://arxiv.org/pdf/2504.10522v1"
curl -L -o "12_VegHealth_ML.pdf" "https://arxiv.org/pdf/1602.06335v4"
curl -L -o "13_VI_Flaws.pdf" "https://arxiv.org/pdf/2212.00569v1"
curl -L -o "14_LDA_Drought.pdf" "https://arxiv.org/pdf/1210.4919v1"

# Methodology (15-16)
curl -L -o "15_SSL_Irrigation.pdf" "https://arxiv.org/pdf/2108.05484v1"
curl -L -o "16_ScopeMamba.pdf" "https://arxiv.org/pdf/2609.10156v1"

# Additional context (17-20)
curl -L -o "17_S2_Yield_Review.pdf" "https://arxiv.org/pdf/2603.23779v1"
curl -L -o "18_Tomato_Weed_SITS.pdf" "https://arxiv.org/pdf/2509.10804v1"
curl -L -o "19_DroughtSet.pdf" "https://arxiv.org/pdf/2412.15075v1"
curl -L -o "20_Potato_Stress_Aerial.pdf" "https://arxiv.org/pdf/2106.07770v3"
```

---

## 📊 SUMMARY: What This Adds to Your Thesis

| Category | Papers Found | Key Contribution |
|----------|-------------|------------------|
| **Direct relevance** | 4 | SSL+SITS+stress pipeline, sugarcane-specific |
| **Methodology** | 6 | Domain adaptation, XAI for VI, physics-informed learning |
| **Physiology** | 2 | Mechanistic basis for mixed-stress class |
| **Baselines** | 4 | Classical ML/Vegetation Index approaches |
| **Additional context** | 4 | Yield estimation reviews, weed stress detection |

**Total: 20 new papers** discovered, all with PDF download links.
