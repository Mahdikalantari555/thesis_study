# 03 — SSL for Satellite Image Time Series (SITS) — Primary Focus

**Scope:** how temporal information is exploited during self-supervised pretraining on satellite image time series (Sentinel-2, Landsat, multisensor); which methods genuinely model temporal dynamics vs. aggregate independent images; irregular sampling, missing acquisitions, clouds; representation levels; benchmarks and evaluation evidence.
**Search date:** 2026-10-24. Evidence levels: [FT] full text; [ABS] abstract verified; [MO] metadata verified.

---

## 1. A taxonomy of temporal supervision (with verified exemplars)

| # | Temporal objective family | Mechanism | Verified exemplars |
|---|---|---|---|
| T1 | Temporal contrastive (seasonal/location positives) | positives = same location, different dates | SeCo [FT]; GASSL [MO]; CACo [via T-JEPA]; Resampling-augmentation SITS-CL (arXiv:2506.18587) [ABS]; EigenCL trajectory contrastive [FT] |
| T2 | Temporally-aware masked reconstruction | mask patches/timesteps across a sequence | SatMAE [FT]; SITS-Former [ABS+DOI]; Presto [FT-adjacent, local PDF]; Sadbhave 3D-CAE [FT]; TiMo [ABS]; Galileo [FT] |
| T3 | Forecasting / future prediction | predict future frames or latents | Time2Agri Future-Frame Prediction [FT]; T-JEPA time-gap-conditioned latent prediction [FT]; Sat-JEPA-Diff [via T-JEPA related work] |
| T4 | Temporal order / metadata prediction | predict time differences, frequency, order | Time2Agri TD + FP pretexts [FT] |
| T5 | Latent-transition (JEPA) prediction | predict target *representations* conditioned on elapsed time | T-JEPA [FT]; AnySat (JEPA-style) [MO] |
| T6 | Reconstruction of *gaps* (inpainting/denoising) | reconstruct masked/missing timesteps | Temporal inpainting AD [FT]; Global NDVI reconstruction SSL [FT-title/authors]; S2 SAR→optical densification [ABS] |

The T-JEPA paper [FT] independently groups published temporal supervision into exactly two prior paradigms — *relation-based* (SeCo, CACo: pairwise constraints) and *context-based* (SatMAE, Prithvi-EO-2.0: joint reconstruction context) — and positions itself as a third: *time-gap-conditioned latent transitions*. Our T1–T6 refine this with the agriculture-specific and gap-reconstruction strands.

## 2. Method-by-method evidence (temporal models only)

### 2.1 SatMAE — temporal MAE with time-encoding (NeurIPS 2022) [FT]
Temporal positional encoding divided equally across **year/month/hour**; masking applied independently per timestep (beats VideoMAE-style consistent masking — ablation: temporal enc. + indep. masking together lift fMoW-temporal top-1 from 78.07 → 81.49) [FT, Table 4]. Handles irregular times *only through* the temporal encoding; sequences are short (length 3 in fMoW-temporal). Not designed for long, sparse archives.

### 2.2 SITS-Former — missing-data imputation pretext (JAG 2022; DOI 10.1016/j.jag.2021.102651) [ABS+metadata]
Pretrains a patch-sequence transformer by masking random patches and regressing **central pixels of masked patches** from the residual series; claims to be "the first study that exploits self-supervised learning for patch-based representation learning and classification of SITS"; +2.64–3.30% OA over purely supervised on two crop classification tasks [ABS, OpenAlex, 85 citations].

### 2.3 Presto — lightweight pixel-time-series transformer (Tseng et al., 2024; arXiv:2304.14065) [FT-adjacent]
Title verified: "Lightweight, Pre-trained Transformers for Remote Sensing Timeseries." Pretrains on irregular **pixel time series** (S1/S2/meteorology) with masked modeling + temporal/positional embeddings; 400K parameters per STS-NET's report [FT, corpus #14]; remains a standard SITS-SSL baseline (STS-NET uses it as feature extractor: 82/81/72% on water/N/combined [FT, corpus #14]; Galileo benchmarks it: CropHarvest Togo 75.5 vs Galileo-Base 74.8 — Presto still wins Togo) [FT, Galileo Table 6].

### 2.4 SeCo — seasonal contrastive (ICCV 2021) [FT]
Temporal positives (same location, different dates) + three embedding sub-spaces (all-invariant / seasonal-invariant / artificial-invariant). The explicit design goal is to *preserve time-varying and invariant factors simultaneously*; change-detection F1 on OSCD 46.94 vs MoCo-v2+TP 40.12 shows temporal-variant features matter [FT, Table 4]. Single-date-per-view design: no sequence modeling.

### 2.5 Galileo — multimodal dual-objective masked modeling (ICML 2025) [FT]
Global task (deep targets, structured space-time masking) + local task (shallow targets, unstructured masking), token contrastive (PatchDisc^B); month embeddings + temporal sinusoidal PEs; 24 monthly timesteps per instance; 9 modalities (S1, S2 incl. NDVI, SRTM, ERA5, TerraClimate, VIIRS, Dynamic World, WorldCereal, LandScan, location). Results: beats SatMAE/CROMA on image benchmarks and Presto on 3 of 4 pixel-series benchmarks (CropHarvest Brazil 99.3 vs 98.8, Kenya 84.2 vs 84.0, Breizhcrops 73.0 vs 63.0; Togo 74.8 vs 75.5) [FT, Table 6]. Ablation removing **TerraClimate** (climate water deficit, soil moisture, AET) or VIIRS from pretraining hurts downstream most [FT, Table 11] — direct evidence that *climate/water-related auxiliary channels* improve representations. Author-acknowledged: more research needed on local/global self-supervision beyond RS [FT].

### 2.6 T-JEPA — time-gap-conditioned latent transitions (arXiv:2610.05731, Oct 2026) [FT]
Elapsed time Δt as supervisory signal; all-pair transition supervision (short + long range, no error propagation); asymmetric metadata injection (online: metadata dropout 0.5; EMA target: none) to block shortcuts; masked-reconstruction branch in a separate decoder subspace; λ=0.5 optimal. Matched-corpus results (HiViT-S/16, CACo corpus): BE-1% mAP 66.0 (Prithvi-EO-2.0-TL 62.4, SatMAE 61.1), PASTIS T=8 mAP 50.7, DFC20 mIoU 39.4 (beats all despite *no downstream metadata*), OSCD F1 60.3 [FT, Table 1]. Time-conditioned probe Target R@1 87.5%, collapsing to 30.0% when Δt is shuffled [FT, Table 3] — representations encode *when-dependent* state. Emergent dynamics: decoded annual trajectories show greening/senescence and plausible unobserved states (winter snow), and cloud-contaminated dates decode to cloud-free surface states [FT, Fig. 4]. Overhead: +220.9% FLOPs vs MAE (wall-clock +20%) [FT, supp.].

### 2.7 Time2Agri — agriculture-specific temporal pretexts (arXiv:2507.04366, Plaksha) [FT]
Argues RSFM pretexts (SatMAE/DoFA-style MAE + contrastive) "overlook the unique temporal characteristics of agricultural landscape, namely nature's cycle." Three pretexts: **Time-Difference Prediction (TD)**, **Temporal Frequency Prediction (FP)**, **Future-Frame Prediction (FF)**. SICKLE dataset: FF 69.6% IoU crop mapping; FP reduces yield prediction error to 30.7% MAPE; TD competitive on most tasks. National-scale India (FTW dataset): FF 54.2% IoU field-boundary delineation, beating all baselines [FT, abstract+§1]. Evidence that *phenology-aware pretexts* outperform generic ones for agricultural mapping.

### 2.8 TiMo — SITS foundation model (arXiv:2505.08723, Wuhan/NUDT) [ABS]
Spatiotemporal FM for SITS; abstract: "existing [SITS] methods fail to ... " (title: "Spatiotemporal Foundation Model for Satellite Image Time Series"); included as the 2025 SITS-FM representative. [Metadata + abstract only — not deep-read.]

### 2.9 Crop-stress SSL on SITS (the thesis's target family — see 04 for full analysis)
- **STS-NET** (Dalal, Ranjan, Ghildiyal, Tamaskar, Goel; arXiv:2607.18791) [FT, local]: 3D-conv autoencoder over VI channels (NDVI, GNDVI, RECI, NDRE + RGB/NIR avg), T=32 timesteps, PlanetScope 9–11-day cadence, BSPT pretraining (~22M pixels); frozen features → RF/XGBoost; sugarcane water-stress precision 97.98%, N 85.08%, combined 83.47% on 62 controlled plots; 19.2K params [FT].
- **Sadbhave et al. sugar-beet 3D-CAE** (arXiv:2507.13514, THWS/Greenspin) [FT, local]: *fully unsupervised* — 3D CAE + **acquisition-date-specific temporal encodings**; representations → downstream clustering to separate stressed vs healthy fields; "can be directly applied to data from different years."
- **EigenCL** (Ahmad, Brandt; arXiv:2506.03394 + extended arXiv:2608.25888 — same work, two versions; deduplicated) [FT, local]: contrastive embedding of NDRE *trajectories*; similarity defined by the principal eigenvector of an RBF kernel matrix (76% variance explained, r=0.95 with raw NDRE) — **biologically grounded positives instead of visual augmentations**; 10,000 maize NDRE patches (Iowa drought 2020), tested on Nebraska 2023 without retraining; Silhouette 0.748, DBI 0.35, CHI 49,624; 76% early stress detection up to 12 days before NDRE thresholds; downstream kNN 95% / logistic 91%; clusters peak severe stress at VT–R1 (tasseling–silking); validated against soil moisture (ρ at 0–14-day lags), US Drought Monitor, county yield.

## 3. Irregular sampling, missing acquisitions, clouds — what is actually solved

| Challenge | Verified evidence |
|---|---|
| Irregular intervals as *signal* | T-JEPA conditions latent transitions on actual Δt [FT]; SatMAE year/month/hour encodings [FT]; Sadbhave acquisition-date encodings [FT]; Presto timestamp handling [MO]; Galileo month embeddings [FT] |
| Clouds/missing data in pretraining | SeCo/SSL4EO-S12 simply filter <10% cloud scenes [FT] — pretraining avoids the problem rather than solving it; T-JEPA argues pixel-space targets are ill-suited *because of* clouds and predicts latents instead [FT]; S2 densification via SAR→optical generative models (arXiv:2605.04239) [ABS]; global NDVI reconstruction SSL (arXiv:2608.02322, Wuhan U — Li, Jiang, Guan, Chu, Shen) [FT-title] |
| Landsat 16-day cadence | **No verified temporal-SSL paper operates on Landsat 16-day composites**; SSL4EO-L (arXiv:2306.09424) [MO] provides Landsat SSL datasets/models but scene-level, and Chang et al. note time series were excluded because "not all models support satellite image time series" [FT]. This is a genuine corpus gap. |

**Interpretation (ours):** the field's cloud strategy splits into *avoid* (filter, pretrain on clear composites), *tolerate* (latent-space objectives), and *fix* (generative reconstruction/densification). For a sugarcane archive with mandatory 16-day compositing over a monsoon-influenced arid site, the *tolerate* route (latent objectives, date-conditioned encoders) has the strongest verified support; the *fix* route has no field-level stress application yet.

## 4. Representation levels

- **Pixel-set / parcel-level:** PSE + TAE (Garnot & Landrieu; CVPR 2020 arXiv:1911.07757; "Lightweight Temporal Self-Attention" arXiv:2007.00586) [MO, verified via title search]; MM-TAE multi-modal crop mapping (arXiv:2112.07558) [MO]. Pixel-set format handles irregular per-pixel acquisition sets efficiently ("Revisiting the Encoding of SITS," arXiv:2305.02086, sets SOTA on PASTIS) [ABS].
- **Patch-level:** U-TAE (ICCV 2021, arXiv:2107.07933 — ID corrected) [MO]; TSViT ("ViTs for SITS," CVPR 2023; arXiv:2301.04944; DOI 10.1109/cvpr52729.2023.01004) [ABS+DOI]: *temporal-then-spatial* factorization + **acquisition-time-specific temporal positional encodings** + multiple class tokens; SOTA on 3 SITS segmentation/classification datasets (supervised — a backbone reference, not SSL) [ABS].
- **Sequence/field-level:** Presto (pixel sequences) [MO]; STS-NET/EigenCL (field or patch trajectories) [FT].
- **Interpretation:** the thesis's field-level design (490 polygons, one score per field per date) is best matched by the parcel/trajectory families (PSE/TAE lineage, EigenCL, STS-NET) rather than dense-patch temporal MMs (TiMo, Prithvi-EO-2.0) which target segmentation at scene scale.

## 5. Benchmarks & reproducible assets (verified)

| Benchmark | Content | Used by |
|---|---|---|
| **PASTIS** (Garnot & Landrieu 2021) | S2 parcel segmentation, France | TSViT, U-TAE, T-JEPA, Galileo [FT] |
| **Breizhcrops** (Rußwurm et al. 2019) | S2 pixel time series, Brittany | Galileo/Presto lineage [FT] |
| **CropHarvest** (Tseng, Zvonkov, Nakalembe, Kerner; NeurIPS 2021 D&B; arXiv:2112.06540) [MO, web-verified] | 90K+ global multi-sensor crop samples | Presto, Galileo, TIML |
| **SICKLE** | multi-sensor agricultural benchmark | Time2Agri [FT] |
| **MTLCC** | S2 crop classification | SITSMamba (OA 0.9100, IGARSS 2025; arXiv:2409.09673; DOI 10.1109/igarss55030.2025.11243832) [ABS+DOI] |
| **EuroCropsML** (Reuss et al., Sci Data 2025; DOI 10.1038/s41597-025-04952-7) [ABS] | 706,683 parcels, 176 classes, S2, farmer-reported | few-shot SSL/MAML benchmark (companion 2026 study, DOI 10.1016/j.ophoto.2026.100117) |
| **DroughtSet** (Tan, Zhao, Liu, Zhang; arXiv:2412.15075; Ohio State) [FT, local] | CONUS drought indices + RS/reanalysis predictors for S2S drought *forecasting* (not SSL) | SPDrought |
| **BSPT / LK sugarcane** (STS-NET) | PlanetScope Barnala + controlled stress plots [FT, local] | STS-NET |

Code availability (verified statements): SeCo github.com/ElementAI/seasonal-contrast [FT]; SSL4EO-S12 github.com/zhu-xlab/SSL4EO-S12 [FT]; CROMA github.com/antofuller/CROMA [FT]; Galileo github.com/nasaharvest/galileo [FT]; AnomalyBERT github.com/Jhryu30/AnomalyBERT [FT]; TSViT github.com/michaeltrs/DeepSatModels [ABS]; SITS-Former github.com/linlei1214/SITS-Former [ABS]; SITSMamba github.com/XiaoleiQinn/SITSMamba [ABS].

## 6. Direct comparative evidence — does temporal SSL beat alternatives?

Verified head-to-head results (same protocol unless noted):

1. **Temporal SSL vs single-image SSL:** SeCo > MoCo-v2 on identical corpus/backbone (BigEarthNet linear mAP 78.56 vs 73.71; OSCD F1 46.94 vs 40.71) [FT]; SSL4EO-S12 seasonal-augmentation ablation (BE-10%: 77.6 vs 75.1 fixed-season) [FT].
2. **Temporal pretext vs generic pretext, agriculture:** Time2Agri FF/FP beat SatMAE/DoFA-style baselines on SICKLE crop mapping and yield [FT].
3. **Latent temporal prediction vs pixel reconstruction:** T-JEPA > MAE/SatMAE/Prithvi-EO-2.0-TL on matched corpus across static + temporal tasks [FT]; ablations show pixel-reconstruction + latent-prediction dual objectives beat either alone [FT, Table 4c].
4. **More modalities:** CROMA both-objectives > either alone [FT, Table 6]; Galileo: removing TerraClimate hurts most [FT, Table 11].
5. **SSL vs from-scratch, crop classification (real-world few-shot):** EuroCropsML benchmark — SSL beats from-scratch and standard transfer, but **meta-learning (MAML) leads**, at higher compute [ABS, 2026 study].
6. **SSL vs non-pretrained for time-series AD:** "SSL yields substantial gains in anomaly detection" under matched budgets (Major et al.) [FT] — the strongest published support for the thesis's AD-first design.
7. **Missing comparisons (explicitly absent from the verified literature):** (a) temporal SSL vs *simple time-series baselines* (RF on VI time series, Gaussian processes) for SITS AD; (b) reconstruction vs contrastive vs one-class for SITS crop-stress AD under one protocol; (c) any head-to-head on Landsat archives; (d) SSL vs handcrafted indices for *stress* (EigenCL's baseline comparison is clustering-based, not index-threshold-based at field level with independent ground truth).

---

*Verification note: [FT] full text read 2026-10-24 (alphaXiv page extraction: SeCo, SSL4EO-S12, SatMAE, CROMA, Galileo, T-JEPA; local pypdf extraction: STS-NET, EigenCL both versions, Time2Agri, temporal inpainting, Sadbhave, DroughtSet, transfer study, Zhang taxonomy). [ABS] abstracts verified via alphaXiv discovery/OpenAlex. [MO] metadata verified via arXiv export API (IDs corrected in QC: U-TAE 2107.07933, PSE 1911.07757, SwAV 2006.09882). Performance numbers are quoted from the specific tables cited and are not comparable across datasets/protocols.*
