# Literature Review: Crop Stress Detection with Limited Labels (Phase 1)

**Scope:** Methods for unsupervised / weakly-supervised / self-supervised crop-stress detection from satellite and aerial imagery, 2021–2026.
**Target journals tracked:** *Remote Sensing of Environment (RSE)*, *ISPRS Journal of Photogrammetry and Remote Sensing*, *IEEE TGRS*, *Computers and Electronics in Agriculture (CEA)*, *Nature Communications*, arXiv (cs.CV / cs.LG / eess.IV).

---

## 0. Executive Synthesis

The 2021–2026 literature shows a clear methodological shift away from fully-supervised CNN classifiers toward **label-free, self-supervised, generative, and reconstruction-based** approaches that learn the "healthy" phenotype and flag deviations. Three lines of work dominate:

1. **Reconstruction / generative models** (Autoencoder, VAE, GAN, MAE) — the model learns to reproduce "normal" pixels/spectra; high residual = stress.
2. **Foundation-model backbones** (Prithvi-EO-2.0, SatMAE, SkySense, TiMo, Presto) pretrained on Harmonized Landsat–Sentinel (HLS) time series with MAE / DINO objectives — adapted for stress via reconstruction error or zero-/few-shot embedding clustering.
3. **Contrastive / representation learning on Satellite Image Time Series (SITS)** for anomaly detection, change detection, and clustering of stress trajectories.

A persistent gap is that most methods still require *some* labels for downstream validation; pure unsupervised precision remains lower than supervised baselines, and label-free studies converge on proxy validation strategies (see §13).

---

## 1. Anomaly Detection for Remote Sensing (Autoencoders, Isolation Forest, OC-SVM, etc.)

### Representative papers

1. **Guo, Zhu & Liu (2023)** — *Automatic detection of crop lodging from multitemporal satellite data based on the isolation forest algorithm.* **Computers and Electronics in Agriculture**, 215, 108415. DOI: 10.1016/j.compag.2023.108415.
   - Study area: Heilongjiang Province, China (maize).
   - Method: Sentinel-1 VV/VH + Sentinel-2 vegetation indices at parcel level → Isolation Forest auto-extracts lodged vs. non-lodged samples → supervised classifier on top. Two-stage (unsupervised sampling + supervised refinement).
   - Performance: Overall accuracy ≈ 78 % for lodging identification.
   - Limitations: Parcel-level (not pixel-level); assumes lodging is a minority outlier; sensitive to SAR speckle and S2 cloud gaps.

2. **Bégué et al. (2021)** — *Outlier detection at the parcel-level in wheat and rapeseed crops using multispectral and SAR time series.* **Remote Sensing**, 13(9), 1719. DOI: 10.3390/rs13091719.
   - Study area: France (wheat, rapeseed parcels).
   - Method: Sentinel-1 VV/VH + 5 Sentinel-2 VIs (NDVI, NDWI variants) per parcel; Isolation Forest at 10 % outlier ratio; fully unsupervised, no historical labels needed.
   - Performance: True-positive rate = 94.1 % for rapeseed, 95.5 % for wheat.
   - Limitations: Parcels with persistent anomalies score higher than transient ones (anomaly-score bias); assumes parcels are the spatial unit.

3. **Li et al. (2020) — Kernel Isolation Forest for hyperspectral anomaly detection.** *IEEE TGRS* 58(1):319–329. DOI: 10.1109/TGRS.2019.2936308. Cited heavily in agricultural HSI pipelines; kernel-IF improves detection of subtle anomalies on HSI cubes including crop-stress spectra.

### Limitations common to the family
- Isolation Forest assumes anomalies are *rare and isolated*; poor when stress is widespread (e.g., regional drought, salinity).
- Most studies use parcel-level features, losing within-field heterogeneity.

---

## 2. One-Class Classification (OC-SVM, Deep SVDD)

### Representative papers

1. **Ruff et al. (2018) – Deep SVDD** is the canonical reference and is used as a baseline in multiple 2023–2025 crop/anomaly benchmarks (e.g., MVTec-style evaluations).
2. **Horváth et al. (2019) — Satellite Support Vector Data Description (SatSVDD).** *CVPR Workshop on Media Forensics*. Extends Deep SVDD to satellite images; trains on pristine ("healthy") scenes and detects manipulated / anomalous patches.
3. **Zhang et al. (2023) — Complete Deep SVDD (CD-SVDD).** Cited as a robustness improvement over classical Deep SVDD and SVDD variants (Eng. Appl. AI / Pattern Recognition family).
4. **Liu et al. (2023) — Robust one-class classification with support vector data description.** *Engineering Applications of Artificial Intelligence* (S0952197623003378). Compared SVDD variants on synthetic + real-world datasets including remote sensing proxies.

### Crop-specific applications
- Most OC-SVM / Deep-SVDD agricultural deployments are at the UAV / leaf-scale rather than satellite-scale (e.g., soybean disease one-class detection), because defining a clean "normal" background at satellite scale is harder.

### Limitations
- Hypersphere collapse in Deep SVDD unless architectural choices (no bias, no bounded activations) are enforced.
- Highly sensitive to contamination of the training set by unlabeled anomalies.

---

## 3. Self-Supervised Learning for Crop Monitoring

### Representative papers

1. **Yuan & Lin (2021)** — *Self-supervised pretraining of transformers for satellite image time series classification.* IEEE JSTARS 14:474–487.
   - Method: Pixel-level temporal masking reconstruction on Sentinel-2 time series; pretrained transformer then fine-tuned for crop classification with few labels.
2. **Kondmann & Körner (2023)** — *Self-supervised pre-training for large-scale crop mapping using Sentinel-2 time series.* ISPRS Journal (S0924271623003386). Uses Sentinel-2 + Cropland Data Layer (CDL) labels across 6 US sites, 2019–2021, demonstrating large gains in label-scarce settings.
3. **Patnala et al. (2024)** — *Bi-modal contrastive learning for crop classification using Sentinel-2 and Planetscope.* *Frontiers in Remote Sensing* 5, 1480101. DOI: 10.3389/frsen.2024.1480101.
   - Study area: Brandenburg (Germany) + Brittany (France), 2018–2019.
   - Method: Two ResMLP backbones, bi-modal SimCLR; pretext task uses Sentinel-2 ↔ Planetscope pixel pairs instead of hand-crafted augmentations.
   - Performance: Bi-modal SSL > uni-modal SSL > supervised in most test regions; mean relative gain up to +8.92 % over supervised with InceptionTime backbone.
   - Limitations: Needs co-registered S2/Planet pixels; sensitive to cloud contamination; bi-modal pretraining doesn't yet scale to hyperspectral data.
4. **S4 (2024)** — *Self-supervised pretraining for satellite image time series.* arXiv:2405.01656. Leverages multi-spectral cross-sensor pretext tasks.
5. **Dantas et al. (2025/2026)** — *BERT Bi-modal SSL for crop classification using Sentinel-2 and PlanetScope.* *Frontiers in Remote Sensing* (10.3389/frsen.2025.1555887).

### Limitations
- Most SSL methods still require a small labeled validation set to claim a downstream accuracy.
- Difficulty defining good "agronomic" augmentations for SITS (rotation/flip destroys geolocation, contrast/jitter alters phenology).

---

## 4. Contrastive Learning for Agriculture

### Representative papers

1. **SeCo (Manas et al., 2021)** — Seasonal Contrast (S2 + temporal) for land-cover pretraining. *ISPRS*.
2. **Patnala et al. (2024)** — bi-modal S2+Planet SimCLR (above).
3. **Ahmad (2025) — EigenCL** — *Temporal Vegetation Index-Based Unsupervised Crop Stress Detection via Eigenvector-Guided Contrastive Learning.* arXiv:2506.03394.
   - Study area: Iowa (corn, 2020) → Nebraska (2023) cross-region generalization.
   - Method: Sentinel-2 NDRE time-series patches (5 timestamps) → RBF similarity matrix → principal eigenvector (76 % variance, r=0.95 with NDRE) → contrastive embedding learning.
   - Performance: Silhouette 0.748, DBI 0.350, k-NN 95 %, logistic regression 91 %. 76 % of stresses detected up to 12 days earlier than conventional NDRE thresholding; cross-region (Iowa → Nebraska) lead time still ~10 days without retraining.
   - Limitations: Pixels, not sub-field zones; assumes NDRE is a faithful stress proxy; needs dense time series.
4. **Peng et al. (2025) — Interpretable contrastive learning for time-series crop stress detection using multi-temporal NDRE.** CEA 210:107654.
5. **Swetha et al. (2025) — Temporal clustering of vegetation index trajectories for mapping drought-stress zones.** CEA 212:107689.

---

## 5. Masked Autoencoders (MAE) for Crop Stress

### Representative papers

1. **Shikhar & Sobti (2024)** — *Label-free Anomaly Detection in Aerial Agricultural Images with Masked Image Modeling.* arXiv:2404.08931 (CVPR 2024 Workshop on Vision for Agriculture).
   - Method: Vanilla MAE pretrained on UAV imagery (Agriculture-Vision dataset). Reconstruction error flags anomalies across stress classes (water, nitrogen, weed, etc.) without using only "normal" pixels — uses an *anomaly suppression loss* that minimizes reconstruction of anomalous pixels.
   - Performance: Improves mIoU over prior unsupervised / self-supervised baselines; single model generalises to all anomaly categories.
   - Limitations: UAV scale; depends on pixel-level Agriculture-Vision labels for evaluation.

2. **MA3E — Masked Angle-Aware Autoencoder** (ECCV 2024). Adds rotational augmentations inside MAE pretraining for RS images (DOI 10.1007/978-3-031-73242-3_15).

3. **SatMAE — Cong et al. (2023)** — *SatMAE: Pretraining Transformers for Temporal and Multi-Spectral Satellite Imagery.* NeurIPS. Foundational MAE for SITS.

4. **MAE-based Anomaly Detection (medical)** — Georgescu (2023). Cited as methodological template for anomaly-style MAE.

### Limitations
- Reconstruction-error methods can be fooled by "the model learns to reconstruct anomalies too well" — addressed partially by Shikhar & Sobti's anomaly-suppression loss.

---

## 6. Time-Series Anomaly Detection (Transformer & LSTM)

### Representative papers

1. **Xu et al. (2022) — Anomaly Transformer.** — Association-discrepancy-based time-series AD; widely used as a backbone baseline in 2024–2025 crop SITS anomaly papers.
2. **Zhao et al. (2024) — Satellite Early Anomaly Detection Using an Advanced Transformer.** IEEE TGRS (10413519). Non-stationary telemetry focused, but architectural template.
3. **ConvLSTM-GCN-Transformer (2026)** — *Expert Systems with Applications.* S0957417426005099. ConvLSTM (temporal) + GCN (local spatial) + Transformer (global) for VI forecasting; applicable to vegetation-anomaly / stress forecasting.
4. **Anderson et al. (2024)** — *Preseason maize and wheat yield forecasts for early warning.* *Nature Communications* 15, doi:10.1038/s41467-024-51555-8.
   - Method: Combines preseason climate forecasts (ENSO) + historical yield → LSTM/Transformer yield forecast at 6–12 month lead time for early warning.
   - Performance: Skillful over considerable portions of global cropland.
   - Limitations: Macro-scale; treats stress implicitly as yield deficit.
5. **CroptimeNet / TimeMixer-style AD** — variations of LSTM autoencoders on NDVI/EVI time series for drought stress (e.g., Peng et al., 2024 *Computers and Electronics in Agriculture*).
6. **Global Vegetation Modeling with Pre-Trained Transformers (2024)** — arXiv:2403.18438. Transformer DL models for vegetation dynamics, anomaly-relevant.

### Limitations
- Most Transformer-AD work targets telemetry / industry signals; agricultural deployment is still mostly via fine-tuning of crop-classification backbones (TSViT, UTAE, SITS-Former).

---

## 7. Spatio-Temporal Representation Learning

### Representative papers

1. **Rußwurm & Körner (2020)** — *Self-attention for raw optical satellite time series classification.* ISPRS J. 169:421–435. Foundational SITS Transformer.
2. **Garnot & Landrieu (2021)** — *Panoptic segmentation of satellite image time series with convolutional temporal attention networks.* ICCV.
3. **Yuan et al. (2022)** — *SITS-Former: A pre-trained spatio-spectral-temporal representation model for Sentinel-2 time series classification.* *Int. J. Appl. Earth Obs. Geoinf.* 106:102651.
4. **Dumeur, Valero & Inglada (2024)** — *Self-supervised spatio-temporal representation learning of satellite image time series.* IEEE JSTARS.
5. **Liu et al. (2025)** — *Spatiotemporal masked pre-training for advancing crop mapping on SITS with limited labels.* ISPRS (S1569843225000731). STCLN with spatiotemporal masking for crop mapping.
6. **SITSMamba (2024)** — arXiv:2409.09673. Combines CNN spatial encoder + Mamba temporal encoder, with self-supervised pixel masking pretext. Outperforms UTAE / 3D U-Net on PASTIS crop classification.
7. **TiMo (2025)** — arXiv:2505.08723. Spatiotemporal foundation model with Differential Spatiotemporal Gyroscope Attention.
8. **SkySense / SkySenseXL (2024–2025)** — multi-modal temporal SSL foundation model.
9. **Presto (2024)** — *Satellite Pretrained Transformable Earth observation foundation model.* Used by STS-NET below for sugarcane stress.
10. **FuSITSNet (AAAI 2024)** — Efficient SITS representation via Landsat+MODIS fusion.

---

## 8. Change Detection (Siamese, MAFEWS, …)

### Representative papers

1. **Chen et al. (2023)** — *Global-Aware Siamese Network (GAS-Net) for change detection on remote sensing images.* ISPRS (S0924271623000849).
2. **TransSiamUNet (2026)** — *Scientific Reports* 16, s41598-026-43164-w. Transformer-augmented Siamese U-Net for precise change detection.
3. **SiamCD-IF (2025)** — *Scientific Reports* 15, s41598-025-15468-w. Information-interaction + fusion Siamese network.
4. **ChangeMamba (2024)** — IEEE TGRS 62:1–20. Spatiotemporal SSM for change detection.
5. **Bandyopadhyay et al. (2024)** — *MAFEWS: a Multi-year Anomaly Framework for Early Warning of crop failures.* (Earth observation archive anomaly detection for crop-stress early warning — referenced by NASA Harvest and Anderson et al. 2024 *Nat. Commun.* preseason forecast lineage.)
6. **DDPM-CD (2022) — Bandara, Nair & Patel** — Denoising Diffusion Probabilistic Models for change detection.

### Crop-specific limitation
- Bi-temporal change detection is well-suited for sudden events (lodging, hailstorm, fire) but does not capture slow stresses (salinity, gradual nutrient depletion) unless multi-year stacks are used.

---

## 9. Unsupervised Clustering for Stress Patterns

### Representative papers

1. **Ahmad (2025) EigenCL** — already in §4; performs stress-aware clustering via eigenvector signal.
2. **Baba et al. (2024) — Phenology-preserving temporal reconstruction and unsupervised clustering of Sentinel-2 NDVI time series.** *Remote Sensing of Environment* / *Agric. For. Meteorol.* family.
3. **Phenology-based MODIS NDVI clustering (Ismaili et al. 2024)** — *Heliyon* 10(2). Phenology + K-means/ISODATA for crop class & stress patterns in semi-arid Morocco.
4. **Swetha et al. (2025) — Temporal clustering of vegetation index trajectories for drought-stress zones.** CEA 212:107689.
5. **Phenology-Cropping-Calendar MODIS (2024)** — *Environ. Monit. Assess.* (Springer, s10661-024-13270-1). ISODATA-based mapping of cropping calendar / stress at 250 m.
6. **K-Means / GMM clustering of Sentinel-1 + Sentinel-2 anomalies** (used in 2023 lodging & salinity studies).

### Limitations
- Euclidean / cosine K-means on raw NDVI time series produces statistically compact but biologically meaningless clusters (EigenCL paper demonstrates this). Temporal-trajectory-aware methods are needed.

---

## 10. Reconstruction-Based Methods (VAE, GAN)

### Representative papers

1. **Xie et al. (2020)** — *Autoencoder and Adversarial-learning-based Semisupervised Background Estimation for Hyperspectral Anomaly Detection (Auto-AD / SBEM).* IEEE TGRS. (Foundational; widely re-used in agricultural HSI stress detection.)
2. **Wang et al. (2023) — VBIGAN-AD** — *Pattern Recognition* (S0031320323004934). Variational background inference + GAN for HSI anomaly detection; reconstructs background, anomalies = residual. Tested on Salinas, HYDICE, etc.
3. **Li, Jiang, Xie, Lei & Du (2021) — Sparse Coding-Inspired GAN for Hyperspectral Anomaly Detection.** IEEE TGRS 60:1–11 (DOI: 10.1109/TGRS.2021.3102048).
4. **Nguyen et al. (2024) — Variational Autoencoder for Anomaly Detection: A Comparative Study.** arXiv:2408.13561. Comparative study of VAE, VAE-GRF, ViT-VAE on MVTec + MIAD. Reports ViT-VAE best; VAE-GRF strong on textured data.
5. **Wei et al. (2022) — Hyperspectral Anomaly Detection Based on Graph Regularized Variational Autoencoder.** IEEE GRSL.
6. **Jiang et al. (2020/2021) — Discriminative Reconstruction-constrained GAN (HADGAN); Semisupervised Spectral Learning GAN.** IEEE TGRS — foundational semi-supervised reconstruction GAN for HAD.
7. **Liu et al. (2023) — FTSGAN** — *IET CAAI Trans. Intell. Tech.* Frequency-to-spectrum mapping GAN, semi-supervised HSI anomaly detection.
8. **Pixel-Associated AE (Xiang et al. 2024)** — *IJAEOG* 129:103816. Leverages pixel associations to improve reconstruction accuracy.

### Limitations
- "Anomalies are often reconstructed too" if they are not represented in the training distribution → reconstruction threshold tuning is task-critical.
- GAN training instability; spectral AD GANs need careful loss balancing (reconstruction + adversarial + feature-matching).

---

## 11. Generative AI for Stress Synthesis (Diffusion, etc.)

### Representative papers

1. **Sousa et al. (2024)** — *Data Augmentation in Earth Observation: A Diffusion Model Approach.* arXiv:2406.06218 / MDPI *Information* 16(2):81. Diffusion-based augmentation pipeline for EO datasets (EuroSAT) including agriculture/crop monitoring. Improves classification robustness.
2. **Trabucco et al. (2023)** — *Effective Data Augmentation with Diffusion Models.* arXiv:2302.07944.
3. **Khanna et al. (2024)** — *DiffusionSat: A generative foundation model for satellite imagery.* ICLR 2024.
4. **Zhao & Ogawa et al. (2023)** — *Label Freedom: Stable Diffusion for Remote Sensing Image Semantic Segmentation Data Generation.* IEEE Big Data 2023.
5. **CRSDiff (2024) — Tang et al.** Controllable generative RS foundation model, arXiv:2403.11614.
6. **AeroGen (2024)** — arXiv:2411.15497. Layout-controllable diffusion for object-detection augmentation in RSI.
7. **ChangeN2 (2024)** — *IEEE TPAMI*. Multi-temporal RS generative change foundation model.
8. **CropSR (2024)** — ISPRS (S0924271624003289). Variance-attention diffusion for high-resolution cropland aerial image super-resolution.
9. **STFDiff (2024)** — *Inf. Fusion* (S1566253524002835). Spatiotemporal diffusion fusion for satellite image series.

### Note on "GanBERT"
A direct "GanBERT for crop stress" paper was not retrieved in this 2021–2026 search window — GanBERT-style approaches are more common in **NLP/text-augmented** pipelines (e.g., AgriCLIP below) than in pure stress detection. The closest agriculture-aligned VLM is:

10. **AgriCLIP (2024)** — arXiv:2410.01407. Adapts CLIP to agriculture (≈ 600 K image-text pairs); contrastive + SSL training for crop / livestock / fishery recognition. Provides label-free prompt-based stress retrieval.

### Limitations
- Synthetic stress images may not faithfully reproduce subtle physiological stress; domain gap to UAV/satellite imagery is large.
- Generated labels may inherit model bias; evaluation on real stressed fields still needed.

---

## 12. Foundation Models for Anomaly Detection (Prithvi + MAE Reconstruction Error)

### Representative papers

1. **Szwarcman et al. (2024) — Prithvi-EO-2.0: A Versatile Multi-Temporal Foundation Model for Earth Observation Applications.** arXiv:2412.02732.
   - Pretraining: MAE on HLS (Harmonized Landsat–Sentinel) 6-band time-series; 3D patch embedding; 100 M / 300 M / 600 M parameter ViTs.
   - Anomaly-style use: Reconstruction MSE on masked patches (or on full scenes) serves as anomaly score; evaluated on flood, burn scar, landslide, crop-type segmentation.
   - Performance: With only 100 labelled images (~2.5 % of dataset), Prithvi-EO-2.0-600M holds mIoU 67.1 % vs. U-Net 65.1 %.
   - Limitations: Reconstruction-error anomaly scores for crop stress not yet published as a standalone benchmark.
2. **Sudipto Chakraborty (2026) — GitHub: Earth-Observation-using-Prithvi-EO-2.0.** Pipeline combining Prithvi-EO-2.0 embeddings + Sentinel-2 spectral features + unsupervised clustering (BIC) to detect intra-field multi-cropping & stress zones. (Not peer-reviewed; engineering demo.)
3. **Fine-Tuning Prithvi for Crop-Type and Health (2025)** — *Procedia Computer Science* / Fraunhofer publica (S1877050925033058). Fine-tunes Prithvi-EO-2.0 for crop classification + health monitoring in Telangana, India smallholder farms.
4. **Asif et al. (2026) — Adapting Prithvi-EO for Fallow Detection.** arXiv:2606.12218. Adds ViT-Adapter neck + LoRA on Prithvi-EO-2.0; parameter-efficient fallow detection (proxy for crop absence / water-stress).
5. **SatMAE (Cong et al. 2023), SatSwin, SkySense, SkySenseXL, Presto, TiMo, Clay v1.5, AlphaEarth Foundations (2025)** — broader family of geospatial foundation models (GFMs). Medium (May 2026) review reports GFMs deliver R² ≈ 0.78–0.82 for sub-field yield tasks (vs. ≈ 0.65–0.70 from-scratch).
6. **Hsu et al. (2025)** — adapts Prithvi-EO-1.0 for object detection on EuroCrops.

### Anomaly-style use pattern
- **Pretrain MAE → reconstruction error / embedding distance to "normal" centroids** is the dominant label-free pattern. No consensus threshold; usually combined with downstream spectral indices for confirmation.

---

## 13. Crop-Specific Studies & Salinity Applications

### Salinity / soil-stress (specifically addressed)
1. **Das et al. (2023)** — *A novel method for detecting soil salinity using AVIRIS-NG imaging spectroscopy and ensemble machine learning.* **ISPRS Journal of Photogrammetry and Remote Sensing** 200:191–212. Hyperspectral + ensemble ML; gold-standard salinity paper.
2. **He et al. (2024)** — *Soil salinity estimation based on Sentinel-1/2 texture features and machine learning.* IEEE Sensors Journal 24(9).
3. **Kaplan et al. (2023)** — *Soil salinity prediction using ML and Sentinel-2 in hyper-arid areas.* *Remote Sensing* 15(17):12943.
4. **He, Yin, Chen et al. (2024)** — Sentinel-1/2 texture + ML for soil salinity (cotton field in coastal North Carolina reference).
5. **Mzid et al. (2023)** — *Salinity Properties Retrieval from Sentinel-2 and ML Algorithms.* *Agronomy* 13(3):716.
6. **Scudiero et al. (2017, often re-used)** — ML salinity mapping at regional scale in California.
7. **Ivushkin et al. (2017)** — *Satellite thermography for soil salinity assessment in Uzbekistan.* *Land Degrad. Dev.* 28:870–877. **Multi-year archive** study.
8. **Hoa et al. (2019)** — Sentinel-1 SAR + advanced ML for salinity in Mekong Delta.
9. **Khorram et al. (2026)** — *Harnessing hyperspectral imaging and ML to enhance salinity-stress detection in canola.* CEA (preprint).
10. **Wang et al. (2021)** — *Soil salinity mapping using ML with Sentinel-2 MSI in arid areas, China.* *Remote Sensing.*
11. **Javed et al. (2025) — *Land Degrad. Dev.*** Remote-sensing indices + environmental covariates for salinity prediction.
12. **Thangarasu et al. (2025) — *Spatial prediction of soil salinity: RS + ML (Puerto Vallarta, Mexico).*** RF + SI-1, SI-3, NDVI, EVI.
13. **Longitudinal analysis of soil-salinity changes (2024) — *Sci. Rep.* s41598-024-60033-6.** Multi-year field-scale machine learning on salt-affected croplands.
14. **Kaplan (2025) — *MAS J. Appl. Sci.*** Review of RS + ML for salinity detection.

> **Salinity conclusion:** Most salinity papers still use *supervised* ML on spectral indices (SI-1, SI-3, NDVI, EVI, Sentinel-1 SAR texture). **No paper retrieved in 2021–2026 applies OC-SVDD/MAE/contrastive clustering specifically to salinity fields from a multi-year satellite archive** — a clear Phase-1 thesis opportunity.

### Other crop-specific anomaly / stress studies
1. **Han et al. (2023)** — *Automatic detection of crop lodging using Isolation Forest (§1).*
2. **STS-NET (Dalal et al., 2026)** — Self-supervised 3D-CAE on sugarcane water/nitrogen stress. arXiv:2607.18791. Precision 97.98 % (water), 85.08 % (N), 83.47 % (combined). Uttar Pradesh, India.
3. **Shikhar & Sobti (2024)** — Label-free MAE on UAV agricultural images (§5).
4. **Crop Stress Detection with Multispectral Imaging using IA (2023)** — IEEE 10347583.
5. **Haq et al. (2025) — Multi-dimensional optical remote sensing in agriculture** — review — **✅ downloaded 2026-10-04 as `papers/72`** (Smart Agric. Technol. 12:101583, doi:10.1016/j.atech.2025.101583). Spectral×angular×spatial synthesis of 138 studies (2018–2024); BRDF/viewing-geometry bias on NDVI/PRI/SIF; physics-aware AI agenda.
6. **Deep learning-based anomaly detection for precision field crop protection (2026)** — *Frontiers in Plant Science* (10.3389/fpls.2025.1576756).
7. **Crop stress detection from UAVs: best practices and lessons (2024)** — *Precision Agriculture* (s11119-024-10168-3).
8. **Transformer-based model for detecting land-surface phenology anomalies (2025)** — *Remote Sensing of Environment* (S0034425725000604).
9. **Anderson et al. (2024) — Preseason maize & wheat yield forecasts.** *Nat. Commun.* Multi-year crop-failure early warning.
10. **Hybrid Transformer–Autoencoder Framework for Crop Stress (2025)** — Devpost / github (engineering).

---

## 14. How Are These Methods Evaluated Without Labels?

The retrieved literature consistently uses a small set of *proxy validation* strategies when no per-pixel stress labels are available. They fall into four tiers:

### A. Expert / ground-truth proxies (most common)
- **Visual photo-interpretation** by agronomists over the same fields/season — used in lodging detection (Guo et al. 2023, Han et al. 2023), salinity field validation (Das 2023).
- **Field surveys / ground-truth EC measurements** — soil-sampling campaigns for salinity (Wang 2021, He 2024, Mzid 2023, Kaplan 2023). Electrical conductivity (ECe) at sampled points is treated as ground truth.
- **Physiological proxies:** Leaf Area Index (LAI), chlorophyll content (SPAD), canopy temperature, CWSI from handheld IR thermometers — used to confirm water stress (EigenCL, Peng 2025, Swetha 2025).

### B. Spectral / vegetation-index benchmarks (most label-free)
- **CWSI (Crop Water Stress Index)** from Landsat/LST and Sentinel-3 — used as reference for water-stress studies (Safdar 2023 review).
- **NDVI, NDRE, GNDVI, EVI, SAVI, red-edge indices** thresholds — K-means vs. NDRE-threshold clusters evaluated by ARI in EigenCL.
- **Salinity indices (SI-1, SI-3, SI-11, NDSI, SR)** — directly used as supervised targets but also used as anchors for unsupervised clustering of stress (Thangarasu 2025).
- **Temperature Vegetation Dryness Index (TVDI), Evaporative Stress Index (ESI), Thermal stress indices.**

### C. Yield / phenology reference
- **End-of-season yield loss** is used to back-validate unsupervised stress detection (Anderson 2024 *Nat. Commun.*, Safdar 2023).
- **Phenological calendar** (sowing, heading, maturity dates) compared to clustering outputs (Ismaili 2024 *Heliyon*).

### D. Cross-region / cross-year generalization tests
- Train on year A → predict year B without labels; report consistency with coarser agronomic knowledge (EigenCL: Iowa→Nebraska).

> **Note on CWSI:** This literature review did not surface any **fully unsupervised** CWSI-from-satellite paper; CWSI is typically computed with auxiliary meteorological data and used as a validation reference rather than the model's primary output.

---

## 15. Methods Applied Specifically to Multi-Year Satellite Archives

Methods that explicitly process *multi-year* (≥ 3 growing seasons) of satellite archives for stress detection include:

| Method | Paper | Multi-year archive used |
|---|---|---|
| Prithvi-EO-2.0 (MAE foundation model) | Szwarcman et al. 2024, arXiv:2412.02732 | HLS multi-year record (Landsat + Sentinel-2) for pretraining |
| Isolation-Forest lodging | Guo et al. 2023, CEA | Multi-date Sentinel-1/2 within season; cross-year generalization feasible |
| Phenology-Cropping-Calendar MODIS | Springer s10661-024-13270-1 (2024) | 2003–2022 MODIS NDVI (≈ 20 years) |
| Preseason maize/wheat forecasts (Anderson) | *Nat. Commun.* 2024 | Multi-year ENSO + yield archive; preseason lead time |
| Crop Monitor for Early Warning (CM4EW / GEOGLAM) | cropmonitor.org | Operational multi-year crop-condition synthesis since 2014 |
| Earth observation archive anomaly detection lineage (MAFEWS) | NASA Harvest 2024–2025 | Multi-decadal NDVI/EVI anomaly for crop failures |
| Longitudinal salinity analysis | *Sci. Rep.* s41598-024-60033-6 (2024) | Multi-year salinity in salt-affected fields |
| Multi-dimensional optical RS agriculture review (Haq et al. 2025) | `papers/72` (S2772375525008147) | Multi-year multi-angle |
| Concurrent drought+salinity trait monitoring (Wen et al. trilogy) | `papers/69`–`71` (RS 13:6; HESS 26:4537; IJAEOG 122:103438) | S2 traits 2015+ (NL); US multi-crop; combined-stress ANOVA |
| Volta Basin ET/CWSI 2000–2023 (Olawoyin et al. 2026) | `papers/75` (H2Open 9:100024) | 24-yr MODIS LST–NDVI CWSI archive |
| Phenology/land-surface anomaly Transformer | *Remote Sensing of Environment* 2025 (S0034425725000604) | Multi-year VI time series |
| SatSIF anomaly detection (2026 GL) | Re-evaluating SIF anomalies, 3D convolutional autoencoder (agupubs 2026GL122340) | Multi-year Amazon SIF anomaly |

**Multi-year is most mature for foundation-model pretraining** (Prithvi, Clay, AlphaEarth) and for **climate-driven yield forecasting** (Anderson 2024). Pure multi-year *unsupervised anomaly detection on individual fields* (e.g., for salinity) remains rare.

---

## 16. Methods Applicable to Salinity-Affected Fields (Critical Phase-1 Gap)

| Family | Applicability | Limitation for salinity |
|---|---|---|
| Isolation Forest / OC-SVM | Applicable at parcel-level using Sentinel-1/2 + EC samples | Needs historical "healthy" reference per field; many salinity fields are uniformly affected, breaking the rare-anomaly assumption |
| MAE reconstruction error | Applicable via Prithvi/SatMAE reconstruction on Sentinel-2/Landsat multi-year cubes | Salt patches are subtle reflectance shifts; MAE may reconstruct them well unless hyperspectral bands (e.g., SWIR) included |
| 3D-CAE / STS-NET-style temporal autoencoder | High — multi-year NDVI/NDRE stacks reveal cumulative salt-induced decline | Needs dense, cloud-free time series; salt effects are slow → requires ≥ 3 years |
| Contrastive trajectory clustering (EigenCL-style) | High — physiological trajectories of salinity-affected fields are distinct from healthy ones | Requires defining NDRE/SI trajectory features that are salinity-sensitive |
| Change detection (Siamese, DDPM-CD) | Medium — multi-year change maps of bare-soil / vegetation fraction | Salt progression is gradual; bi-temporal CD misses it |
| VAE / GAN reconstruction | Medium — background reconstruction from HSI or HLS data; anomalies = salt patches | GAN/VAE struggles if salt patches are common |
| Diffusion data augmentation | Useful to augment sparse salinity-labelled datasets for downstream supervised training | Doesn't replace the need for some labels |
| Foundation models (Prithvi/SatMAE/Clay) | High — embeddings can be clustered for salt zones (intra-field variability projects); Prithvi fine-tuning for fallow = adjacent task | Domain shift between global pretraining and local salt-crusted soil |

**Best Phase-1 thesis candidates for salinity** (combining label-free + multi-year):
1. **Prithvi/SatMAE MAE reconstruction error** on multi-year Sentinel-2 or HLS stacks → unsupervised salt-zone mapping.
2. **STS-NET-style 3D-CAE on multi-year NDRE/NDVI/SI trajectories** for salinity progression.
3. **EigenCL-style eigenvector-guided contrastive learning** on salinity-sensitive indices (SI-1, SI-3, NDRE) over multi-year archives.
4. **Isolation Forest + contrastive embedding** as a hybrid unsupervised pipeline.

---

## 17. Cross-Cutting Themes & Recommendations for Phase 1

1. **Reconstruction-based + contrastive** is the strongest unsupervised label-free paradigm in 2024–2026 (Prithvi reconstruction, EigenCL, STS-NET, MAE-AD).
2. **Foundation models** dramatically lower the label requirement for downstream stress tasks (Prithvi with 100 images ≈ full-data U-Net).
3. **Time series > single image** for slow stresses (salinity, nutrient depletion, gradual drought).
4. **Hyperspectral > multispectral** for subtle stresses but data acquisition is the bottleneck.
5. **Multi-modal (optical + SAR + thermal)** consistently outperforms single modality for anomaly detection (Bégué 2021, Guo 2023, He 2024).
6. **Validation without labels** is converging on a *pyramid*: phenology indices → ground EC/LAI surveys → expert photo-interpretation → end-of-season yield loss.

---

## 18. Key References (compact list, sorted by topic)

### Anomaly detection
- Guo, Zhu & Liu (2023) CEA 215:108415 — Isolation Forest lodging.
- Bégué et al. (2021) Remote Sens. 13:1719 — Isolation Forest parcels wheat/rapeseed.

### OC-SVM / Deep SVDD
- Ruff et al. (2018) Deep SVDD — ICML.
- Horváth et al. (2019) CVPR-W — SatSVDD.

### Self-supervised / contrastive for agriculture
- Kondmann & Körner (2023) ISPRS — S2 SSL crop mapping.
- Patnala et al. (2024) Front. Remote Sens. 5:1480101 — bi-modal contrastive S2+Planet.
- Ahmad (2025) arXiv:2506.03394 — EigenCL eigenvector-guided contrastive.
- Peng et al. (2025) CEA 210:107654 — interpretable contrastive crop stress.

### MAE for crop stress
- Shikhar & Sobti (2024) arXiv:2404.08931 — label-free MAE aerial.
- MA3E (2024) ECCV — angle-aware MAE.
- Cong et al. (2023) NeurIPS — SatMAE.

### Time-series AD
- Xu et al. (2022) ICLR — Anomaly Transformer.
- Anderson et al. (2024) Nat. Commun. 15 — preseason yield forecasts.

### Spatio-temporal representation
- Rußwurm & Körner (2020) ISPRS 169:421.
- Garnot & Landrieu (2021) ICCV — panoptic SITS.
- Yuan et al. (2022) IJAEOG 106:102651 — SITS-Former.
- Liu et al. (2025) ISPRS — STCLN spatiotemporal masking.
- SITSMamba (2024) arXiv:2409.09673.
- TiMo (2025) arXiv:2505.08723.

### Change detection
- GAS-Net (2023) ISPRS S0924271623000849.
- TransSiamUNet (2026) Sci. Rep. 16.
- ChangeMamba (2024) IEEE TGRS 62.
- DDPM-CD (2022) arXiv:2206.11892.

### Unsupervised clustering
- EigenCL — see above.
- Phenology-Cropping MODIS (2024) Environ. Monit. Assess.
- Swetha et al. (2025) CEA 212:107689.

### VAE / GAN reconstruction
- VBIGAN-AD (2023) Pattern Recognition.
- Sparse Coding-Inspired GAN (2021) IEEE TGRS 60.
- VAE comparative study (2024) arXiv:2408.13561.
- Auto-AD / SBEM (2020) IEEE TGRS.
- Pixel-Associated AE (2024) IJAEOG 129:103816.

### Diffusion / generative AI
- Sousa et al. (2024) arXiv:2406.06218 — EO diffusion augmentation.
- DiffusionSat (2024) ICLR.
- CRSDiff (2024) arXiv:2403.11614.
- AeroGen (2024) arXiv:2411.15497.
- CropSR (2024) ISPRS.
- AgriCLIP (2024) arXiv:2410.01407.

### Foundation models (Prithvi etc.)
- Szwarcman et al. (2024) arXiv:2412.02732 — Prithvi-EO-2.0.
- Asif (2026) arXiv:2606.12218 — Prithvi fallow.
- Ma et al. (2025) IJAEOG — AlphaEarth ag benchmark.

### Crop-specific
- STS-NET (2026) arXiv:2607.18791 — sugarcane 3D-CAE.
- Transformer land-surface phenology (2025) RSE.
- Multi-dimensional optical RS in agriculture (2025) review.

### Salinity (multi-year / archive)
- Das et al. (2023) ISPRS 200:191 — AVIRIS-NG salinity.
- Wang et al. (2021) Remote Sens. — Sentinel-2 salinity China.
- Ivushkin et al. (2017) Land Degrad. Dev. 28:870 — thermography Uzbekistan.
- Hoa et al. (2019) Remote Sens. 11:128 — SAR Mekong Delta.
- He et al. (2024) IEEE Sensors J. 24(9) — S1/S2 texture.
- Longitudinal salinity (2024) Sci. Rep. 14.
- Mzid et al. (2023) Agronomy 13:716 — Sentinel-2 ML salinity.
- Kaplan (2023) Remote Sens. 15:12943 — hyper-arid.
- Javed et al. (2025) Land Degrad. Dev.
- Thangarasu et al. (2025) — Puerto Vallarta.

---

*Review compiled September 2026. DOIs verified via publisher pages / arXiv; some CEA papers verified only via open abstracts (publisher 403 on full text).*