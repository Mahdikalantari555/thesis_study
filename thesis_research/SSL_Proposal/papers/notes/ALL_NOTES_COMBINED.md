## FILE: 2021 Ruff et al. - A Unifying Review of Deep and Shallow Anomaly Detection (Proc IEEE).md
# 2021 Ruff et al. — A Unifying Review of Deep and Shallow Anomaly Detection

## Full citation
Ruff, L.; Kauffmann, J.R.; Vandermeulen, R.A.; Montavon, G.; Samek, W.; Kloft, M.; Dietterich, T.G.; Müller, K.-R. "A Unifying Review of Deep and Shallow Anomaly Detection." *Proceedings of the IEEE*, Vol. 109, No. 5, May 2021, pp. 756–795. DOI: 10.1109/JPROC.2021.3052449.

## Problem & setting
- Review/tutorial paper (not a single experiment): organizes the entire anomaly detection (AD) field — classic "shallow" methods (PCA, OC-SVM, SVDD, KDE, k-NN, LOF, isolation forest) and deep methods (AEs, deep one-class classification, deep generative models, self-supervised AD) — into one framework of components: **feature map φ, model/loss, regularization, inference mode**.
- Motivating setting: mostly **unsupervised AD** where labeled anomalies are absent/insufficient; anomalies diverse and rare; normality concept must be learned from (possibly contaminated) unlabeled data.

## Method (taxonomy and precise objectives)
- Formalizes AD as **density level-set estimation**: A = {x | p+(x) ≤ τ}; concentration (cluster) assumption: normal data concentrates in a bounded high-density region, anomalies do not.
- Anomaly taxonomy: point, contextual/conditional, group/collective, plus the deep-learning-relevant split of **low-level sensory vs. high-level semantic anomalies** — semantic anomalies can be closer to normal data in raw pixel space than normal-class variants are to each other, so detecting them requires semantic feature representations.
- **Deep SVDD objective** (one-class deep classification): min over ω, c of (1/n) Σᵢ ‖φω(xᵢ) − c‖² (+R); collapse prevention via reconstruction terms, architectural constraints (no unbounded/biased activations, no pooling), frozen embeddings, auxiliary negatives, or variance penalties.
- **Self-supervised AD** reviewed: train multiclass classifiers on pseudo-labels from geometric transformations (rotations/flips/translations; GOAD uses random affine transformations); anomaly score from softmax prediction uncertainty (near-uniform ⇒ anomaly). Also notes contrastive self-supervision as promising for AD.
- Deep generative models (VAE, flows, GANs) reviewed; flags the **Nalisnick et al. "typical set" failure**: DGM likelihoods biased toward low-level background statistics, can assign higher likelihood to OOD samples — a key caution for reconstruction/density-based AD.
- Empirical assessment (MNIST/CIFAR-style k-classes-out benchmarks, tables with AUROC) enriched with explainability (layer-wise relevance propagation-style relevance maps) so one can see *why* a point is anomalous.

## Data & labels
- Benchmark-style experiments on image AD benchmarks (MNIST, Fashion-MNIST, CIFAR-10, GTSRB); toy 2-D examples (moons); n unlabelled training samples, labels only used for evaluation and (in DSAD) a few labeled anomalies.

## Results (key empirical findings)
- Deep one-class (DOCC/Deep SVDD) beats shallow baselines on complex image benchmarks; on simple structured data shallow methods remain competitive.
- Self-supervised (geometric transformation) AD shows "significant performance improvements" on k-classes-out benchmarks over vanilla Deep SVDD.
- XAI-based relevance analysis shows deep detectors often latch onto background/low-level statistics — motivating explicit explainability checks before deployment.

## What transfers to our thesis
- Frame label-free sugarcane stress detection as **one-class / level-set estimation on SSL-learned embeddings of Landsat time series**, not as supervised classification — the concentration assumption maps to "healthy fields concentrate, stress is diverse."
- The **contextual/group anomaly taxonomy** fits our problem: stress is a *contextual* anomaly (a parcel anomalous for its date, soil, and phenological stage) and often a *collective* anomaly (a sub-series), so the detector should be conditioned on context (season, crop stage) rather than use global thresholds.
- **Low-level vs. semantic anomaly distinction** is a design warning: pixel/reconstruction-based detectors on Landsat tiles may only catch low-level anomalies (clouds, missing data) while water/salinity stress is semantic — argues for SSL representations (masked temporal modeling, contrastive) + one-class head, as in Deep SAD/DOCC lineage.
- Softmax-uncertainty / transformation-classification AD (rotation prediction) could be a cheap pretext on 16-day NDVI/LST stacks; but their caveat that self-supervision may learn mainly low-level statistics supports pairing it with temporal pretext tasks.
- Deep SVDD's collapse-avoidance tricks (no biased activations/pooling, whiten the embedding) are directly reusable for a lightweight per-field stress scorer.

## Limitations / caveats
- 2021 review: predates masked-image-modeling AD, modern foundation-model era, and satellite time-series SSL; benchmarks are natural images, not remote sensing.
- Authors' own bias acknowledged (Deep SVDD lineage).
- Does not address nonstationarity of "normal" across years/sensors beyond discussion — a core issue for cross-year Landsat models.

## Key numbers to quote in lit review
- Published in Proc. IEEE vol. 109, no. 5 (2021); DOI 10.1109/JPROC.2021.3052449 — the standard citation for unifying shallow+deep AD.
- Self-supervised geometric-transformation AD gives "significant performance improvements" over vanilla Deep SVDD on k-classes-out image benchmarks (e.g., MNIST-family AUROC gains reported in their Table 3).
- DGM likelihood failure: models trained on Fashion-MNIST systematically assign *higher* likelihood to MNIST digits (Nalisnick et al.) — caution against pure-likelihood AD.
- Anomaly score hierarchy: point vs. contextual vs. collective anomalies — the formal vocabulary for stress-as-contextual-anomaly framing.



---


## FILE: 2022 Wang et al. - Self-supervised Learning in Remote Sensing - A Review (arXiv).md
# 2022 Wang et al. — Self-supervised Learning in Remote Sensing: A Review

## Full citation
Wang, Y.; Albrecht, C.M.; Ait Ali Braham, N.; Mou, L.; Zhu, X.X. "Self-supervised Learning in Remote Sensing: A Review." IEEE Geoscience and Remote Sensing Magazine (accepted 2022); arXiv:2206.13188v2.

## Problem & setting
- Didactic review + empirical benchmark of SSL for earth observation (SSL4EO). Motivation: RS annotation is expensive, noisy, and datasets go stale (labels outdated by natural/man-made change); supervised pre-training suffers domain gap between source and target sensors/regions.
- Provides taxonomy of SSL (generative / predictive / contrastive) with side-by-side CV↔RS method mapping.

## Method (taxonomy)
- **Generative**: AEs (sparse, denoising, VAE, MAE), GANs; self-supervision signal = raw input reconstruction ||x − D(E(x))||.
- **Predictive**: self-produced labels from context — spatial (relative position, jigsaw, rotation, inpainting), spectral (colorization), temporal (frame order).
- **Contrastive**: negative sampling (CPC, MoCo, SimCLR), clustering (DeepCluster, SeLa, SwAV), knowledge distillation (BYOL, SimSiam, DINO, iBOT), redundancy reduction (Barlow Twins, VICReg).
- RS-specific insight: augmentations must respect physical semantics — color jitter is inappropriate for SAR and questionable for multispectral; seasonal/geographic co-locations and multi-sensor views (SAR↔optical) can serve as natural positive pairs.
- Evaluation protocols: linear probing, k-NN, fine-tuning; kernel/feature-map visualization.

## Data & labels (their benchmark)
- Pre-training ResNet-18 (100 epochs, batch 256, 4×A100) with MoCo-v2, SwAV, SimSiam, Barlow Twins on Sentinel-2: BigEarthNet (590,326 patches 128×128, 311,667 used for pre-training), SEN12MS (180,662 S1/S2/MODIS triplets, cropped to 128×128), So2Sat-LCZ42 culture-10 (352,366 training patches). Transfer eval on EuroSAT (27,000 patches). Augmentations: crop, grayscale, Gaussian blur, h-flip, channel drop (no color jitter except SimSiam).

## Results (key quantitative findings)
- All four contrastive methods beat random init on linear probing across all three datasets; **MoCo-v2 (negative sampling) generally best** and most stable.
- **SimSiam collapses after ~10 epochs** on Sentinel-2 without momentum encoder — practical warning.
- Augmentation ablation (BigEarthNet): removing RandomResizedCrop collapses SwAV/Barlow Twins and hurts MoCo-v2/SimSiam; **using cropping ONLY performs nearly as well as the full augmentation set** — opposite to natural images where color distortion matters. More aggressive crops (min size 0.2) help.
- Limited-label regime (BigEarthNet, MoCo-v2): SSL **linear probing beats supervised-from-scratch when labels drop to 1%**; SSL fine-tuning beats supervised at ALL label fractions, with huge gains at 0.1–1% labels.
- Transfer (BigEarthNet→EuroSAT): fine-tuning with 50% of labels beats full-label supervised; 10% of labels ≈ full-label supervised.

## What transfers to our thesis
- This is the canonical "SSL works in RS, and label efficiency is the payoff" citation: our thesis's core claim (label-free stress detection needs no annotations) is directly supported — their curve shows SSL dominates exactly in the regime where we operate (no/1% labels).
- **Cropping-only augmentation result** is operationally important: a lightweight Landsat model can use simple spatial crop augmentations without fancy spectral jittering; but note we must add *temporal* augmentations (seasonal subsetting, time jitter, band dropout) as our RS-specific analog.
- MoCo-v2 with negative sampling as a robust, stable contrastive baseline for field-embedding pre-training on unlabeled multi-year Landsat stacks (nearby parcels in space-time = natural negatives; same parcel across season = positive).
- Their warning against color jitter translates to: design augmentations that preserve the *physical* signal we care about (do not augment away LST/NDVI stress signatures).
- Evaluation protocol (linear probe + k-NN + fine-tune with 0.1/1/10/50% labels) is a template for our cross-year lightweight model evaluation.

## Limitations / caveats
- Benchmark is Sentinel-2 scene classification only (no time series, no LST, no agriculture-specific tasks); pre-training only 100 epochs ResNet-18.
- No masked-image-modeling methods benchmarked (2022); SimSiam instability partially implementation-dependent.
- No downstream stress/anomaly tasks — classification accuracy may not proxy detection of subtle sub-pixel stress.

## Key numbers to quote in lit review
- SSL linear probing surpasses supervised training when labels are reduced to **1%** on BigEarthNet (ResNet-18, MoCo-v2).
- SSL fine-tuning beats supervised at all label fractions; transfer BigEarthNet→EuroSAT with **50% labels beats 100%-label supervised**; **10% labels ≈ full supervised**.
- Cropping-only augmentation ≈ full augmentation suite on Sentinel-2 (unlike natural images).
- Benchmark scale: 590,326 BigEarthNet patches; 180,662 SEN12MS triplets; 400,673 So2Sat pairs.



---


## FILE: 2023 - Generic SSL Framework for Spectra-Spatial Representation of Unlabeled RS Imagery (arXiv).md
# 2023 Zhang & Han — A Generic SSL Framework for Representation Learning from Spectra-Spatial Features of Unlabeled RS Imagery

## Full citation
Zhang, X.; Han, L. "A generic self-supervised learning (SSL) framework for representation learning from spectra-spatial feature of unlabeled remote sensing imagery." arXiv:2306.15836v1 [cs.CV], 27 Jun 2023 (Manchester Metropolitan University).

## Problem & setting
- Claim: existing RS pretext tasks are RGB/spatial extensions from CV and ignore spectral structure; no pretext task explicitly designed for joint spectral-spatial representation learning.
- Two downstream settings evaluated: (1) multi-label land-cover classification on Sentinel-2 multispectral (object-based, BigEarthNet), (2) soil parameter retrieval (N, P, K, Mg, pH) on hyperspectral data (pixel-based regression).

## Method
- **ObjSSL (object-based, contrastive/self-distillation)**: DINO-style teacher–student (momentum teacher, EMA update θt ← λθt + (1−λ)θs, λ cosine schedule 0.96→1; cross-entropy between teacher/student softmax output distributions, teacher temperature τt). Positive views from a **joint spatial-spectral multi-view pretext**: (a) regular augmentation (rotation, zoom, Gaussian blur, noise), (b) local (36×36 crops, <50% of global 120×120 view) + global views — locals to student, global to teacher, (c) **spectral-aware augmentation: randomly drop 30–50% of channels (set to zero) while preserving channel order** — explicitly avoids color-jitter-style channel shuffling that destroys spectral semantics. Encoder: Spectral–Spatial ViT.
- **PixSSL (pixel-based, generative)**: spectral-masked autoencoder — mask **50% of a pixel's spectral profile**, transformer encoder sees only visible bands, lightweight decoder reconstructs the full spectral profile (asymmetric MAE design, MSE loss in pixel space, mask tokens + positional embeddings). High masking ratio prevents trivial interpolation between adjacent bands.
- Same framework serves object-based (high/very-high resolution) and pixel-based (low/medium resolution) analysis.

## Data & labels
- BigEarthNet: 125 Sentinel-2 tiles (June 2017–May 2018), 10 European countries, Level-2A sen2cor-corrected, ~393,000 training patches; labels only for downstream fine-tuning/eval.
- Hyperspectral soil dataset for N/P/K/Mg/pH regression; labels only for downstream regression.

## Results (key quantitative results)
- Spectral-aware augmentation ablation: macro P/R/F1 = 78.66/66.52/71.10% vs. 73.02/62.12/66.05% without it → **+5.6 P, +4.4 R, +5.1 F1**; spectrum-sensitive classes (forests, grassland, wetlands, arable land) improve most.
- Label-efficiency: supervised-only collapses with 5% training data (F1 22.4%, LRAP 32.4%); **with SSL fine-tuning, best accuracy is reached using only 5% of training data**.
- SSL comparison (fine-tune on 50% labels): proposed 92.76% acc / 66.05% F1 / 89.13% LRAP vs. DINO 92.05/60.65/87.17, BYOL 91.86/57.03/86.33, MoCo-v2 91.71/60.96/86.25.
- Backbone comparison: proposed network + SSL 93.84% acc / 72.50% F1 vs. ResNet50 92.32/62.52, VGG16 90.96/45.85, ViT 89.94/39.00.
- PixSSL regression: soil N prediction R² ≈0.85 (traditional ML) → SSL linear probe R² 0.93→0.95 (P, K, Mg); fine-tuned encoder R² >0.95; masking ratio 50% (and 70%) optimal.
- Masking-ratio ablation: high ratios (50–70%) work best — consistent with MAE findings.

## What transfers to our thesis
- **Spectral-aware channel dropping (30–50%, order-preserving) is directly applicable** as an augmentation for Landsat time series: mask/drop bands (or entire 16-day acquisitions) while keeping band/time order intact — a physically valid pretext augmentation for optical+LST stacks.
- **PixSSL's band-masking pretext generalizes naturally to time-band masking on Landsat**: mask 50% of the (band × date) cube and reconstruct — supports our masked-autoencoder design for multi-year sugarcane stacks (NDVI, LST bands across 16-day steps).
- Their 5%-labels result supports the thesis argument that SSL pretraining on unlabeled multi-year imagery then light fine-tuning (or none) beats supervised training in label-scarce agricultural settings.
- The two-track design (object-level contrastive + pixel-level masked reconstruction) parallels our multi-product design: parcel-level embeddings for field stress scoring vs. pixel-level reconstruction for anomaly maps.

## Limitations / caveats
- No temporal dimension — purely single-date spectral-spatial; our setting adds the time axis.
- Downstream tasks are land-cover classification and soil chemistry regression, not stress/anomaly detection.
- BigEarthNet evaluation partly uses weighted metrics; F1 gains partly architecture-driven (their channel-information ViT module), so SSL-vs-architecture attribution is mixed.
- arXiv preprint (LaTeX template date fields stale); not peer-reviewed venue.

## Key numbers to quote in lit review
- +5.05 F1 points macro from spectral-aware augmentation alone (71.10% vs. 66.05%).
- Best downstream accuracy achievable with only **5% of training labels** when SSL-pretrained (vs. F1 22.4% supervised-only).
- Beats MoCo-v2/BYOL/DINO by 5.1–9.0 F1 points under 50%-label fine-tuning.
- Soil nutrient regression R² raised from ~0.85 to >0.95 by SSL representations.
- Optimal spectral masking ratio: 50%.



---


## FILE: 2023 - Productive Crop Field Detection Dataset and SSL Benchmarks (arXiv).md
# Productive Crop Field Detection: A New Dataset and Deep Learning Benchmark Results

## Full citation
Nascimento, E., Just, J., Almeida, J., & Almeida, T. (2023). "Productive Crop Field Detection: A New Dataset and Deep Learning Benchmark Results." IEEE Geoscience and Remote Sensing Letters (SIBGRAPI 2023), arXiv:2305.11990v2.

## Problem & setting
- Binary detection of *productive* crop fields (fields consistently used for growth/harvest) from Sentinel-2 multi-temporal imagery; motivated by precision agriculture (17 productive corn fields on a single large US farm, John Deere machine-operation data).
- Temporal window 2018-10-29 to 2019-08-15; 15-38 Sentinel-2 acquisitions per hexagon (irregular, non-16-day).
- Space discretized as H3 level-12 hexagons (~10 m edges, 307 m2, ~3 S2 pixels); tabular time series per hexagon, not raster segmentation.

## Method
- Three complementary training paradigms benchmarked on a small 4-layer CNN (4 conv layers, kernel 3, stride 1) taking 15x12 arrays (15 randomly sampled dates x 12 Sentinel-2 bands, band-median per hexagon):
  1. **PU learning** (semi-supervised; SVM base): only positives are labeled (machine-evidence hexagons); negatives inferred as unlabeled — fits settings where positives are highly confident.
  2. **Triplet-Loss Siamese**: anchor-positive vs anchor-negative distance margin loss.
  3. **SimCLR contrastive learning**: augmentation = random band jitter of up to +/-10% on all bands; standard NT-Xent InfoNCE-style objective (per SimCLR), recommended for low-label regimes.
- Key design choice: positives labeled from machine operations (planting/harvest telemetry); negatives inferred from a 3-hexagon ring around fields (hard negatives at boundaries).

## Data & labels
- 17 fields; 106,735 hex-date rows total: 75,990 positive rows (5,066 unique positive hexagons), 30,745 negative rows (2,050 unique negatives). Grouped into 8,342 multitemporal samples of 15 dates x 12 bands.
- Labels avoided manual annotation: derived from harvester/planter GPS operations + spatial rules. Dataset + notebooks public (github.com/egnascimento/productivefieldsdetection).
- Split 80/10/10 train/test/val, class balance preserved.

## Results
- Supervised DL baseline: 96.62% acc, F1-w 96.61%, MCC 0.92.
- PU-SVM: 95.36% acc, MCC 0.89 (semi-supervised, no full negatives needed).
- SimCLR contrastive: 97.05% acc, F1-w 97.03%, MCC 0.93 — best when labeled data scarce.
- Triplet-Loss Siamese: 97.47% acc, F1-w 97.47%, F1-Pos 98.19%, MCC 0.94 — best overall (with accurate labels).
- Errors concentrate at field/non-field boundary hexagons (the inferred hard negatives).

## What transfers to our thesis
- Direct template for label-free sugarcane field/parcel screening: machine-operation or management-derived positives + PU learning is a way to avoid full annotation on Landsat time series.
- Hexagon (H3 L12) tabularization of 16-day Landsat bands is a lightweight alternative to raster patches — the model is a tiny 4-layer CNN on 15x12 arrays, matching our "lightweight in-field" requirement.
- Demonstrates SimCLR works on small agricultural time-series arrays with trivial augmentation (band jitter +/-10%) — analogous augmentation (band jitter, temporal subsampling) can be used on Landsat 16-day stacks.
- PU framing parallels our stress problem: stressed-field positives can be scarce/confident, negatives unlabeled.

## Limitations / caveats
- Only 17 fields, one crop (corn), one region, one season; negatives inferred (possible false negatives from unshared machine data).
- Sentinel-2 only (no thermal band); 15 dates randomly sampled, irregular cadence — not a fixed 16-day composite scheme.
- No cross-year or cross-region evaluation; augmentation for contrastive learning admittedly primitive.

## Key numbers to quote in lit review
- Triplet-Loss Siamese 97.47% accuracy / MCC 0.94 > SimCLR 97.05% > PU-SVM 95.36% on productive-field detection.
- SimCLR nearly matches supervised baseline despite scarce labels (97.05% vs 96.62% acc) — evidence SSL suffices in agriculture with minimal annotation.
- Dataset: 106,735 hex-date observations, 5,066 positive / 2,050 negative hexagons, labels from machine telemetry without manual annotation.



---


## FILE: 2023 Chen and Bruzzone - Unsupervised Change Detection in SITS by Contrastive Learning and Feature Tracking (arXiv).md
# Unsupervised Change Detection in Satellite Image Time Series by Contrastive Learning and Feature Tracking

## Full citation
Chen, Y. & Bruzzone, L. (2023). "Unsupervised Change Detection in Satellite Image Time Series by Contrastive Learning and Feature Tracking." arXiv:2304.11375v1 [cs.CV], University of Trento.

## Problem & setting
- Fully unsupervised (no manual labels) change detection in *long* satellite image time series (SITS), outputting per-date change maps relative to the first image; the core difficulty is separating real changes from seasonal noise in multi-year series.
- Two datasets: (1) MUDS Sentinel-2, 74 locations 2017-2020, 512x512 px, 4 bands at 10 m, irregular intervals, 30 scenes labeled for eval; (2) UTRnet Landsat-8 dataset, 9 Chinese city scenes 2013-2021, 30 m, 6 spectral bands (B,G,R,NIR,SWIR1,SWIR2), 10 cloud-free images per scene, 400x400 px.

## Method
- Two-stage self-training framework, teacher-student with EMA (teacher gets color jitter):
  1. **Pseudo-label generation**: pixel features pre-trained with the authors' earlier self-supervised bi-temporal contrastive approach [Chen & Bruzzone TGRS 2022]; threshold features into change maps; then **feature tracking** (dense label propagation, queue of NT=3 most-correlated change pairs, top-k=10 cosine-similar embeddings, temperature 0.005) propagates labels across the sequence — suppresses seasonal false alarms vs raw thresholding.
  2. **Self-training**: ResUnet (FC-Siam-conc-like, 32-64-128 ch, ResBlk encoders) + Bi-ConvLSTM (2-layer, forward+backward) + MLP head. Change pairs anchored at first image; outputs change map time series.
- Losses: feature-learning stage L = L_supcon + 0.1*L_crw (pixel-wise supervised contrastive on pseudo-labels + **contrastive random walk** cycle-consistency over a space-time graph, L_crw = -tr(log(A_t,t+k * A_t+k,t)), softmax affinities over cosine similarities of neighboring-frame features); fine-tuning stage L = L_ce + 0.0005*L_supcon (cross-entropy for the final change map head). Adam 3e-4, batch 2, 200 epochs feature stage; SGD 0.01, 50 epochs fine-tuning.

## Data & labels
- Training uses zero manual labels; ground truth (changed/unchanged/unlabeled from Google Earth) used only for evaluation of the most significant change pair. Landsat-8 change classes: city expansion, water change, soil change.

## Results
- Landsat-8 (all-scene fitting, the setting matching our cross-scene goal): proposed OA 91.30%, kappa 0.644 vs UTRnet all-scene OA 48.50% (kappa 0.09) and one-scene UTRnet 89.66% (kappa 0.557); weighted CVA pseudo-labels 91.02% OA. Proposed (All-Scene) beats per-scene UTRnet while using one shared model.
- Sentinel-2 (unseen-scene inference): proposed OA 93.90%, F1 0.801, kappa 0.765 vs UTRnet inference OA 84.67% (kappa 0.451); generalizes to unseen scenes.
- Ablations (30 S2 scenes): feature-tracking pseudo-labels + self-training OA 94.41%/kappa 0.599 vs threshold-based pseudo-labels 92.51%/0.552; both contrastive losses (SupCon + CRW) OA 94.41% vs only cross-entropy 87.86% (kappa 0.441) — contrastive losses add ~+6.5% OA and +0.16 kappa; only-SupCon 93.67%/0.553.

## What transfers to our thesis
- The most relevant Landsat recipe in the batch for label-free anomaly/stress detection: multi-year Landsat-8 6-band 30 m time series (2013-2021), seasonal noise handled by feature-tracking pseudo-labels + supervised contrastive loss — directly analogous to separating sugarcane stress onset from phenological seasonality on 16-day composites.
- Supervised-contrastive-on-pseudo-labels + cycle-consistency (contrastive random walk) is a concrete recipe for improving label quality without annotations; could be adapted to contrast field embeddings across years.
- Bi-ConvLSTM after a lightweight ResUnet is a mid-weight spatio-temporal encoder between ConvLSTM and Mamba; shows temporal bidirectionality matters for change/stress detection.
- Demonstrates that a single model trained on multiple scenes transfers to unseen scenes (kappa 0.765), supporting our cross-year/multi-product goal.

## Limitations / caveats
- Evaluation restricted to the "most significant change" pair per scene — gradual/subtle stress-type changes not quantified; small data (10 images/scene, 9 scenes).
- Two-stage pipeline with hand-tuned thresholds (temperature 0.005, top-k 10, NT 3) and pseudo-label noise persists (precision only 76% on inference).
- Landsat results are "fitting" (evaluated on training scenes), not held-out; pixel-level contrastive on 512x512 scenes is computationally heavy (batch size 2).

## Key numbers to quote in lit review
- Unsupervised SITS change detection on Landsat-8 (6 bands, 2013-2021): OA 91.30%, kappa 0.644 vs UTRnet one-scene 0.557 — with a single all-scene model.
- Generalizes to unseen Sentinel-2 scenes: OA 93.90%, F1 0.801, kappa 0.765.
- Contrastive losses (SupCon + contrastive random walk) add ~6.5% OA over cross-entropy self-training (94.41% vs 87.86%).
- Feature-tracking pseudo-labels reduce seasonal false alarms vs thresholding (+~2% OA, +0.05 kappa).



---


## FILE: 2023 Tseng et al. - Presto - Lightweight Pre-trained Transformers for Remote Sensing Timeseries (arXiv).md
# Presto: Lightweight, Pre-trained Transformers for Remote Sensing Timeseries

## Full citation
Tseng, G., Cartuyvels, R., Zvonkov, I., Purohit, M., Rolnick, D., & Kerner, H. (2023). "Lightweight, Pre-trained Transformers for Remote Sensing Timeseries." arXiv:2304.14065v4 [cs.CV] (Mila/McGill/ASU; NASA Harvest).

## Problem & setting
- Label scarcity for satellite ML globally; existing SSL backbones treat RS as single-timestep images (no temporal dimension), single-sensor, and are too large to deploy for contiguous map making. Goal: a small, multi-sensor, pixel-time-series pre-trained transformer usable by feature extraction or fine-tuning.
- Pre-training data: 21.5M pixel-timeseries sampled globally (Dynamic World sampling strategy, stratified by ecoregion/land cover), 10 m/px, 12 contiguous monthly timesteps within 2020-2021.

## Method
- **Architecture**: encoder-decoder transformer, 2 attention layers, 8 heads, embedding dim 128, MLP ratio 4, ~402K params total (0.40-0.81 M depending on count); MAE-style (He et al. 2022): mask input, decoder reconstructs, decoder discarded at downstream time.
- **Tokenization**: per timestep, channels split into sensor/product groups (S1 VV/VH; S2 RGB, Red-Edge, NIR-10m, NIR-20m, SWIR; NDVI; ERA5 precip+2m-temp; Dynamic World class; static SRTM elevation+slope; static lat/lon 3D Cartesian). Each group gets learned linear projection + learned channel-group encoding + sinusoidal positional + month (sin/cos of month/12) encodings. Coordinates never masked.
- **SSL objective**: masked autoencoding with **structured masking** at ratio 0.75 — randomly select one of 4 strategies per sample: (1) random (t x d), (2) channel-groups (whole sensor masked), (3) contiguous timesteps, (4) random timesteps. Loss: L_total = L_MSE + lambda*(Ncat/Ncont)*L_CE balancing continuous (MSE) and categorical (cross-entropy, Dynamic World) reconstructions, lambda=2. Trained 20 epochs, batch 4096, AdamW, lr 1e-3 cosine, wd 0.05; 43 h on one V100.
- Downstream modes: Presto_R (linear/logistic on frozen embeddings), Presto_RF (random forest on embeddings), Presto_FT (full fine-tune); image tasks use mean+std aggregation of per-pixel tokens.

## Data & labels
- Pre-training fully label-free (reconstruction only). Downstream: CropHarvest crop-type segmentation (Kenya maize 1,345, Brazil coffee 203, Togo cropland 1,319 samples), S2-Agri100 crop classification (1,500), TreeSatAI (45,337), EuroSat (21,600), fuel moisture (1,578), algae blooms (777) regressions. Labels used only at fine-tuning/probing.

## Results
- CropHarvest mean F1: Presto_R 0.835 (adapting only 129 params) vs TIML 0.802 (91K params) and MOSAIKS-1D 0.738; AUC 0.917 vs TIML 0.890. Random forest baseline 0.441.
- Robust to missing inputs: with only 3 of 12 months, Presto still matches full-input TIML/MOSAIKS-1D; negligible drop without Dynamic World (0.835->0.836 without).
- S2-Agri100: pre-trained Presto OA 68.89%, kappa 0.58 vs SITS-Former 67.03%/0.56, with 6x fewer params (0.4 M vs 2.5 M); random-init Presto only 45.98% — pre-training adds ~+23% OA.
- EuroSat fine-tune: MS 0.953 accuracy (SatMAE ViT-L MS 0.990 with 306 M params); pre-training adds +14-22% acc over random init. kNN: Presto MS ~0.92 comparable to ScaleMAE/SatMAE with 4 orders of magnitude fewer FLOPs (2.37 MFLOPs/pixel vs 535 GFLOPs/image for SatMAE MS).
- Regression: best mean RMSE delta vs linear baseline (-7.24% Presto_FT; fuel moisture RMSE 25.28).
- Ablations: combining all structured masking strategies (0.665 F1) beats random-only (0.646); performance scales with size (2x width 128->256: F1 0.665->0.687).

## What transfers to our thesis
- **The canonical lightweight RS time-series backbone**: 0.4 M params, feature-extraction mode trains only 129 params — directly supports our "lightweight multi-product in-field" requirement; inference cheap enough for whole-field Landsat mapping.
- Structured masking over (timesteps x sensor-groups) is the exact recipe to adapt to Landsat: mask whole months (cloud gaps), whole band groups (optical vs LST/derived indices) so the model natively handles missing 16-day composites and missing thermal data.
- Demonstrates month encodings + static location/topography tokens transfer across geographies/years — supports our cross-year model reuse; mixing derived products (NDVI; analogously ETa/CWSI, NDWI, salinity proxies) as extra channel groups improves performance.
- Shows pixel-time-series models can rival image models on many tasks; but for scene-level tasks aggregation (mean+std) is the weak point — relevant when deciding pixel-level vs field-level pooling for stress maps.
- Presto is explicitly pre-trained on Sentinel data at 10 m; our thesis extends the pixel-time-series MAE recipe to Landsat 30 m / 16-day with thermal.

## Limitations / caveats
- No thermal band in pre-training; 10 m assumption; monthly (not 16-day) timesteps during pre-training.
- Pixel-independent: no spatial context; image-level aggregation loses information (EuroSat Highway/River classes plateau).
- Crop/stress labels downstream still needed; pre-training validation was on CropHarvest (crop-type, not stress).
- Training data 2020-2021 only; no explicit cross-year evaluation.

## Key numbers to quote in lit review
- 0.4 M-parameter transformer beats 2.5 M SITS-Former on crop classification (OA 68.89% vs 67.03%) and matches 300 M ViT MAEs on EuroSat MS (0.953 vs 0.990) with up to 1000x fewer parameters and 4 orders of magnitude fewer FLOPs.
- CropHarvest mean F1 0.835 with only 129 adapted parameters vs meta-learning SOTA 0.802.
- Structured masking (channel-group + contiguous/random timestep) outperforms MAE random masking (F1 0.665 vs 0.646).
- Pre-training yields +23% OA over random init on the small crop dataset (S2-Agri100), and robust performance with only 25% of input timesteps.



---


## FILE: 2023 Zhang et al. - Self-Supervised Learning for Time Series Analysis - Taxonomy, Progress, Prospects (IEEE TPAMI, arXiv).md
# Self-Supervised Learning for Time Series Analysis: Taxonomy, Progress, and Prospects

## Full citation
Zhang, K., Wen, Q., Zhang, C., Cai, R., Jin, M., Liu, Y., Zhang, J.Y., Liang, Y., Pang, G., Song, D., & Pan, S. (2023/2024). "Self-Supervised Learning for Time Series Analysis: Taxonomy, Progress, and Prospects." IEEE TPAMI, arXiv:2306.10125v4. Companion repo: github.com/qingsongedu/Awesome-SSL4TS.

## Problem & setting
- First comprehensive survey of SSL specifically for (multivariate) time series; motivated by the fact that CV/NLP pretext tasks do not transfer trivially (time series have seasonality/trend/frequency structure; image-style augmentation such as rotation/crop breaks temporal dependency; information concentrated in few variables).
- Covers four downstream tasks: anomaly detection, forecasting, classification, clustering.

## Method (taxonomy — precisely)
**Three top-level families, ten subcategories:**
1. **Generative-based** (pretext = generate data):
   - *Autoregressive-based forecasting (ARF)*: predict x[t+1:t+K] from x[1:t], MSE loss (THOC multi-resolution dilated RNN TSS; GDN graph forecasting; STraTS triple-representation transformer for irregular series).
   - *Autoencoder-based reconstruction*: BAE, DAE (Gaussian noise / zeroing timesteps), **MAE (loss only on masked part)**, VAE (reconstruction + KL). Masking for time series classified into time-step-wise, segment-wise (STEP; captures slow features/trends, shortens encoder input), variable-wise (VSF; sensor-absence forecasting), and attention-guided (TARNet). VAE variants: InterFusion, OmniAnomaly (+Planar NF), GRELEN/VGCRN (graph), LaST (disentangled seasonal-trend with MI constraints).
   - *Diffusion-based generation*: CSDI (imputation), TimeGrad, D3VAE, ImDiffusion (anomaly detection), SSSD (structured state space + diffusion).
2. **Contrastive-based** (classified by how positives/negatives are built):
   - *Sampling contrast*: temporal-neighborhood assumption (USRL); TNC uses ADF stationarity test + PU-learning weighting of possible false negatives; NCL adds supervised signal.
   - *Prediction contrast*: CPC/InfoNCE — predict future latent to maximize mutual information between context and future ("slow features"); TS-CP2 and Skip-Step CPC use TCN; Skip-step distance choice changes anomaly detection results; TS-TCC/CA-TCC cross-view context prediction; CMLF multi-granularity.
   - *Augmentation contrast*: SimCLR-style NT-Xent (eq. 25) with time-series augmentations — jitter/scale/permutation (TS-TCC strong vs weak), masking (TS2Vec), frequency-domain (CoST FFT seasonal-trend disentanglement; BTSF time-freq bilinear fusion; TF-C frequency perturbations beating TS2Vec/TS-TCC); DTW-based TimeCLR; DCdetector dual-attention patch contrast for anomaly detection; multi-scale views (MTFCC, MRLF).
   - *Prototype contrast*: cluster-center/prototype-based contrast (PCL, SwAV; TS: ShapeNet shapelet triplet, TapNet, DVSL, MHCCL hierarchical with outlier masking) — avoids the uniformity bias of instance discrimination.
   - *Expert-knowledge contrast*: priors select positives/negatives (DTW-distance labels; ExpCLR continuous pair loss; SleepPriorCL).
3. **Adversarial-based**: GAN generation/imputation (TimeGAN, TTS-GAN, E2GAN, GRUI) and auxiliary representation enhancement L = L_base + L_adv (USAD two-AE adversarial reconstruction error amplification; AnomalyTrans prior-vs-series association KL; BeatGAN; L = L_mse + lambda1*L_cluster + lambda2*L_adv).

**Quantitative takeaways (Appendix I):**
- Anomaly detection (PSM/SMD/MSL/SMAP/SWaT, point-adjusted F1): best methods are contrastive + association-based — DCdetector (PSM F1 97.94, SMAP 97.02, SWaT 96.33), Skip-CPC (PSM 98.55), ImDiffusion (PSM 97.81, SMD 94.88), AnomalyTrans; key ingredients: global/local association modeling (anomalies associate weakly with the whole series) + adversarial regularization to amplify anomaly scores. USAD (SMD F1 93.82) remains a strong simple baseline.
- Forecasting: disentangled seasonal-trend SSL methods (LaST, CoST) dominate (e.g., LaST ETTh-24h MSE 0.324, CoST 0.386 vs CPC 0.728, TS2Vec 0.590).
- Classification/clustering: contrastive methods dominate; no single method wins across 30 UCR/UEA/HAR datasets — model choice must be data-dependent.
- Survey's stated correlation: generative SSL suits anomaly detection + forecasting; contrastive SSL suits classification + clustering.

## Data & labels
- Standard benchmarks tabulated: AD — PSM (26 dim, 27.8% anomaly), SMD (38 dim, 4.16%), MSL/SMAP (NASA), SWaT/WADI (water treatment); Forecasting — ETTh/ETTm, Electricity (321 dim), Weather, Traffic (862 dim); C&C — HAR, UCR-128, UEA-30. All SSL pretraining label-free; metrics: P/R/F1 (with point-adjustment for AD), MSE/MAE, accuracy.

## What transfers to our thesis
- Provides the taxonomy vocabulary for the thesis lit review: our Landsat field-time-series work can be framed as **generative (masked reconstruction/forecasting) + contrastive** hybrid; the survey's guidance that generative/forecasting objectives suit anomaly detection supports our "predict future 16-day NDVI/LST, flag unpredictability as stress" design.
- Key anomaly-detection design principle to cite: anomalies are hard to associate/predict from the rest of the series (association-discrepancy and unpredictability objectives outperform plain reconstruction on PSM/SMD/SWAT).
- Sampling-contrast pitfall directly relevant to crop phenology: neighboring timesteps of a sugarcane series are NOT always similar (seasonality); TNC's stationarity-tested neighborhoods and PU-weighted negatives show how to avoid false-negative contrastive pairs — analogous to not contrasting winter vs summer composites as "negatives".
- Seasonal-trend disentanglement (CoST/LaST) is attractive for stress detection: stress signal is a deviation from the normal seasonal component, so disentangled representations could separate phenology from stress.
- Future directions that justify thesis novelty: SSL for irregular/sparse series without interpolation (cloud gaps in Landsat), inductive bias/prior injection (physics of ETa), large pre-trained time-series models, benchmark evaluation.

## Limitations / caveats
- General-purpose time series (industrial/medical/traffic) — no remote sensing/agricultural case studies; all benchmarks are 1-D sensor series, not spatio-temporal image time series.
- Point-adjustment F1 protocol in many AD benchmarks is known to inflate scores; numbers not comparable to spatial (per-pixel) anomaly detection.
- Survey snapshot to early 2024; no coverage of Mamba/SSM backbones, foundation models for EO, or masked spectral-spatial modeling.

## Key numbers to quote in lit review
- Taxonomy: 3 families, 10 subcategories; contrastive split into sampling/prediction/augmentation/prototype/expert-knowledge; masking into time-step-, segment-, variable-wise.
- Best AD F1 on PSM: DCdetector 97.94%, Skip-CPC 98.55%, ImDiffusion 97.81% — all exploit "anomalies are poorly associated/predicted with the rest of the series".
- USAD's adversarial two-AE amplification reaches F1 93.82% on SMD with a simple reconstruction objective.
- Seasonal-trend disentanglement SSL (LaST) cuts ETTh-24h forecasting MSE from 0.590 (TS2Vec) to 0.324.
- No contrastive model wins across all 30 classification datasets — augmentation choice is task-dependent (jitter/scale/permutation/masking/frequency).



---


## FILE: 2024 - Physics-Constrained Deep Learning for Biophysical Parameter Retrieval - PROSAIL Inversion Sentinel-2 (Remote Sensing of Environment).md
# Physics-constrained deep learning for biophysical parameter retrieval from Sentinel-2 images: Inversion of the PROSAIL model

## Full citation
Zérah, Y., Valero, S., Inglada, J. (2024). Physics-constrained deep learning for biophysical parameter retrieval from Sentinel-2 images: Inversion of the PROSAIL model. *Remote Sensing of Environment*, 312, 114309. DOI: 10.1016/j.rse.2024.114309. CESBIO (CNES/CNRS/INRAE/IRD/UT3 Toulouse).

## Problem & setting
- Task: probabilistic inversion of the PROSAIL radiative transfer model (RTM) to retrieve ALL input biophysical variables simultaneously (LAI, Cab/chlorophyll, Cw, Cm, Cc, Cb, N, leaf angle, soil parameters) from single-date Sentinel-2 surface reflectance (10/20 m bands upsampled to 10 m) + 3 observation angles.
- Setting: 14 western-European S2 MGRS tiles (THEIA, MAJA-corrected), acquisitions 2016–2019, 512×512 px ROIs over croplands and forests split into 128×128 patches (14 train / 1 val / 1 test per ROI).
- Motivation: hybrid (simulation-trained) inverters such as SNAP's BVNET Biophysical Processor degrade when simulated distributions mismatch reality; simulation design (distributions, inter-variable correlations, RTM version) is fragile and case-dependent.

## Method
- PROSAIL-VAE: a VAE whose decoder is a **differentiable PROSAIL** implementation. The encoder maps S2 reflectance (+angles) to the parameters of truncated-Normal distributions over the 11 PROSAIL input variables (latents ARE the physical parameters, constrained to physical ranges by rescaling to [0,1] bounds).
- Training is fully self-supervised on real unlabeled S2 images: sampled latent parameters are pushed through differentiable PROSAIL, converted to S2 bands via sensor response functions, and reconstruction loss = spectral reflectance matching + β_KL × KL divergence against uniform priors over the physical ranges. Loss: L = L_rec + β_KL·L_KL (β_KL ∈ {0,1,2}).
- Gradient backpropagates through the physics decoder into the encoder only — no simulations, no labels needed; only variable value ranges (min/max bounds) are prior knowledge, not full distributions (β_KL=0 config needs even less).
- Encoders: residual backbone, 3 residual blocks (2 layers each), 32 units wide, ReLU; two variants — pixel-wise MLP and a CNN ("spatial") whose first layer is 3×3 conv (rest 1×1).
- Baselines: BVNET (SNAP, 66-weight 2-layer ANN trained on PROSAIL simulations, MSE) and MPSR (same encoder architecture trained supervised on 3×10^5 simulated samples with NLL of truncated Gaussians).

## Data & labels
- Unlabeled training data: S2 patches from 14 tiles, Jan 2016–Dec 2019, cloud coverage <3%.
- Labels used ONLY for evaluation: 211 LAI + 121 CCC in-situ measurements from FRM4Veg/BelSAR campaigns at 3 sites (Las Tiesas-Barrax crops Spain, 2018 & 2021; Wytham Woods deciduous forest UK; BelSAR).
- Uncertainty evaluated via MPIW (mean prediction interval width) and PICP (coverage) at 2σ.

## Results
- Overall in-situ RMSE: PROSAIL-VAE LAI = 1.16 vs SNAP = 1.24; CCC = 42.33 vs SNAP = 88.08 μg/cm² (halves CCC error). CCC better than SNAP on ALL sites (e.g. Barrax 2021: 20.51 vs 84.53).
- Simulation-trained BVNET accuracy depended strongly on (i) PROSPECT version, (ii) LAI distribution choice, (iii) co-distribution strategy; best simulation config was case-dependent — direct evidence that simulation design does not transfer.
- PROSAIL-VAE-NP (β_KL=0, no distributional prior, only ranges) already accurate; priors on ALL variables (PROSAIL-VAE-AV) HURT accuracy — mild, targeted priors (LAI only, β_KL=2) were best (Pix-B2-L).
- PICP ≈ 0.95 target met for LAI (0.95 overall) and CCC (0.94). Spatial CNN encoder gave no measurable benefit over pixel-wise MLP (3×3 first layer too small; no spatial loss term).
- PROSAIL-VAE predictions saturated at CCC 250 μg/cm² and CWC 0.17 cm where SNAP overestimated CCC; LAI time series over a maize parcel matched double-logistic phenology and in-situ values.

## What transfers to our thesis
- Template for **physics-in-the-decoder SSL**: replace PROSAIL with a crop-growth/energy-balance or RTM forward model for Landsat; the encoder can output stress-relevant latent variables (e.g. Cw, Cab, LAI → water status proxies) trained with ZERO labels on Landsat time series — directly relevant to sugarcane water stress where Cw/CWC relates to drought.
- Shows unlabeled real satellite imagery (not simulations) can train an inverter that beats an operational simulation-trained product — supports our label-free premise and our cross-year generalization argument (no simulated distribution to mismatch).
- "Mild priors only" lesson: constrain latents to physical ranges, apply KL on few well-known variables; overly strong priors degrade accuracy — relevant when we encode ETa/CWSI priors.
- Probabilistic outputs (TN latents, PICP/MPIP calibration) give uncertainty — useful for in-field decision support products.
- Landsat analog: their angle-aware input + band-response conversion is directly reusable for Landsat 8/9 SR + thermal channels if a differentiable forward model for LST is used.

## Limitations / caveats
- Single-date inversion (no temporal model); Sentinel-2 only (10–20 m VNIR/SWIR), no thermal band — water-stress retrieval via Cw is indirect.
- Spatial encoder showed no gain; architecture/scale small (32-wide residual nets) — scaling behavior unknown.
- PROSAIL cannot model non-agricultural/heterogeneous canopies well (their own motivation); epistemic RTM error remains.
- CCC/CWC validation limited (121 points); saturation at high CCC.
- Requires differentiable reimplementation of the physics model — engineering cost.

## Key numbers to quote in lit review
- PROSAIL-VAE trained purely on unlabeled S2 images reaches overall RMSE 1.16 (LAI) and 42.33 μg/cm² (CCC) vs SNAP's 1.24 and 88.08 — CCC error halved with zero in-situ labels.
- Only 211 LAI / 121 CCC in-situ samples used, exclusively for evaluation.
- Latents are truncated-Normal distributions over the 11 PROSAIL physical parameters; loss = spectral reconstruction + β_KL·KL to uniform priors (best: β_KL=2, LAI prior only).
- Training set: unlabeled S2 patches, 14 MGRS tiles, 2016–2019, THEIA/MAJA surface reflectance.



---


## FILE: 2024 - Self-Supervised Learning on Small In-Domain Datasets Can Overcome Supervised Learning in RS (IEEE).md
# Self-Supervised Learning on Small In-Domain Datasets Can Overcome Supervised Learning in Remote Sensing

## Full citation
Sanchez-Fernandez, A. J., Moreno-Álvarez, S., Rico-Gallego, J. A., Tabik, S. (2024). Self-Supervised Learning on Small In-Domain Datasets Can Overcome Supervised Learning in Remote Sensing. *IEEE JSTARS*, 17, 12797–12812. DOI: 10.1109/JSTARS.2024.3421622. Code: github.com/sfandres/ssl-overcome-supervised-rs.

## Problem & setting
- Question: can SSL pretrained on a SMALL in-domain (in-distribution) RS dataset beat fully-supervised (FS) models initialized from ImageNet-1k or random weights, under label scarcity?
- Tasks: (i) LULC fraction estimation (per-patch percentages of 9 LULC classes) and (ii) LULC scene classification, both on RGB satellite patches (224×224, 10 m, Sentinel-2-derived composites).
- Downstream data: Land-1.0 mixed-pixel dataset — 15,038 train / 2,153 val / 4,298 test; train ratios of 5%, 10%, 25%, 50%, 100% to simulate label scarcity.

## Method
- Pretrain 4 contrastive/non-contrastive SSL models with ResNet-18 backbone on Sentinel2GlobalLULC v2.1 (194,877 single-class "pure-pixel" RGB patches, 29 LULC classes, cloud-free S2 composites 2015–2020): Barlow Twins, MoCov2, SimCLR, SimSiam.
- SSL specifics: two augmented views per image (random resized crop, H/V flip, color jitter with HUE KEPT CONSTANT — strategic for satellite color features, Gaussian blur); Barlow Twins = redundancy-reduction loss (cross-correlation matrix of embeddings pushed to identity, no negatives/large batches); MoCov2 = momentum encoder + negative queue; SimSiam = stop-gradient + prediction head.
- Pretraining: 500 epochs, batch 512, SGD with 10-epoch warm-up; training subset reduced to 40% (stratified) for hardware; Ray Tune hyperparameter search.
- Transfer: best SSL model (Barlow Twins by macro-F1 on frozen linear probe) evaluated via frozen linear probing (LP, 50 epochs) and full fine-tuning (FT, 100 epochs) against FS-ImageNet and FS-Random.

## Data & labels
- Pretraining: 194,877 unlabeled (label-agnostic) in-domain RGB patches vs ImageNet-1k's 1,281,167 natural images used for supervised init — 6.6× fewer samples.
- Downstream labels used only for LP/FT evaluation across 5 train ratios.

## Results
- LULC fraction estimation RMSE (lower better): SSL-BarlowTwins-LP 0.099 vs FS-Random-LP 0.122 (+18.85%); FT: 0.083 vs FS-Random-FT 0.099 (+16.16%). SSL-BarlowTwins-LP beats FS-ImageNet-LP by 2.94% (0.099 vs 0.102); FS-ImageNet-FT slightly better than SSL-BarlowTwins-FT (0.078 vs 0.083, 6.41%).
- SSL-BarlowTwins-LP beats even FS-Random-FT at small train ratios; SSL-FT beats FS-Random-FT in 58/60 per-class×ratio scenarios (fraction task: 60/60 for SSL vs random).
- Scene classification macro-F1: SSL-BarlowTwins-LP 0.561 vs FS-Random-LP 0.404 (+38.86%) and FS-ImageNet-LP 0.547 (+2.56%); FT: 0.643 vs FS-ImageNet 0.653 (−1.53%).
- Barlow Twins clearly best of the 4 SSL models in embedding cluster quality (t-SNE) and macro-F1; SimSiam next.

## What transfers to our thesis
- Core evidential claim for the proposal: **a small, in-domain, label-free pretraining set (195k patches) matches or beats 1.28M ImageNet supervised weights in RS** — argues our sugarcane/Landsat in-domain SSL pretraining over a single irrigated scheme can beat generic pretrained backbones without any labels.
- Barlow Twins (no negatives, no momentum encoder, batch-size robust, simple loss) was the best SSL family — a practical lightweight choice for our compute-constrained multi-product setting.
- Hue-constant augmentation lesson: preserve spectral/color information critical in RS; for multispectral Landsat, design augmentations that preserve band-ratio/thermal signals (e.g., no channel jitter that breaks VI physics).
- LP-vs-FT gap analysis: frozen SSL features are strong under label scarcity but FT adds a few %; supports evaluating our models in both frozen-feature (cheap multi-product deployment) and FT regimes.
- RMSE on continuous fractions ≈ our regression-style stress indices; the 5–100% train-ratio curve method is a reusable experiment design for our cross-year label-scarcity story.

## Limitations / caveats
- RGB only (3 bands) — no multispectral, no LST, no time series; Sentinel-2 10 m not Landsat 16-day.
- Pretraining "small" still = 78k images used (40% of 195k); single backbone (ResNet-18); no temporal dimension.
- SSL slightly loses to ImageNet-FT in the strongest-label regime — SSL advantage is concentrated in low-label regimes.
- 2D scene tasks only; no stress/anomaly detection, no crop phenology.

## Key numbers to quote in lit review
- SSL (Barlow Twins) pretrained on 194,877 in-domain RS patches beats ImageNet-1k (1,281,167 samples) supervised init in linear probing by 2.94% RMSE (fraction estimation) and 2.56% macro-F1 (scene classification).
- SSL beats random init by 16–19% RMSE and 21–39% F1 across LP/FT.
- Frozen SSL features beat random-init FINE-TUNED features at small training ratios.
- Barlow Twins outperformed MoCov2, SimCLR, SimSiam on all transfer protocols (ResNet-18, 500 epochs, batch 512).



---


## FILE: 2024 Marsocci et al. - X-STARS - Cross-Sensor Self-Supervised Training and Alignment, Sentinel-2-Landsat-8 (arXiv).md
# X-STARS: Cross-sensor Self-supervised Training and Alignment for Remote Sensing

## Full citation
Marsocci, V. & Audebert, N. (2024). "Cross-sensor self-supervised training and alignment for remote sensing (X-STARS)." arXiv:2405.09922v2 [cs.CV] (ESA Phi-lab / IGN / CNAM).

## Problem & setting
- Sensor-agnostic SSL: models trained on one optical sensor (e.g., Sentinel-2 10 m) generalize poorly to another (Landsat-8 30 m, SPOT-6 1.5 m, BDORTHO 0.2 m) due to different GSD, bands, calibration, blur/aliasing. Also: VHR data is scarce; goal is to pretrain on abundant low-res data and adapt (continual pretraining) to scarce high-res sensors.
- Downstream: 4 classification (EuroSAT, Worldstrat, UC-Merced, CV-BrCT) + 3 segmentation (FLAIR 0.25 m, SpaceNet-8 0.8 m, Chesapeake Land Cover with Landsat-8 30 m) benchmarks; k-NN + linear probing (frozen) and UperNet/ResUNet fine-tuning.

## Method
- **X-STARS loss** = off-the-shelf SSL (DINO self-distillation, multi-scale local-to-global crops, EMA teacher) + lambda * **MSAD (Multi-Sensor Alignment Dense loss)**, lambda=0.1, L = L_DINO + lambda*L_MSAD.
- **MSAD**: cross-sensor InfoNCE between paired acquisitions (same geographic area, different sensors, images resized to common size); instead of only global CLS tokens, similarities are computed **patchwise** — per-token (patch t) softmax over cosine similarities v_i^A[t] vs v_j^B[t], summed over T tokens (eq. 6); **label smoothing** alpha=0.3 relaxes hard positive/negative pairs because same-area multi-sensor acquisitions are not simultaneous (seasonal/structural change) (eq. 7: y = (1-alpha)*y + alpha/(N-1)). Per-sensor linear projection heads psi_A, psi_B.
- Two regimes: (i) from-scratch (DINO teacher = EMA student), (ii) **continual pretraining** — frozen domain teacher F from pretrained sensor A extracts targets; DINO student adapts to new sensor B while MSAD aligns student's A-features to F's outputs.
- ViT-L/16, 800 epochs (400 for continual), batch 32/GPU, 8x V100; RGB only.

## Data & labels
- **MSC-France** (new, released): 4,496 triplets over 12 French cities, Sentinel-2 10 m + Landsat-8 30 m + SPOT-6 1.5 m, summer 2018, <0.1% cloud; plus Multi-View Ile-de-France: 45,200 pairs BDORTHO 0.2 m / SPOT-6 1.5 m. Pretraining label-free; downstream labels only for eval. Scale advantage: ~5k patches vs 200-363k for SeCo/CROMA/Scale-MAE (10-100x fewer data).

## Results
- From-scratch on S2+LS (ViT-L): EuroSAT kNN/linear 94.4/95.5 (vs Scale-MAE-on-fMoW 92.9/93.9, CROMA 87.3/85.2, SeCo 62.6/93.9); UC-Merced 89.9/91.7 (+7.7% over Scale-MAE); CV-BrCT 76.9/76.4; CLC (Landsat-8) segmentation mIoU 19.9.
- Continual pretraining: adapting Scale-MAE (S6→BDORTHO) gives FLAIR 53.3 mIoU (+1.4 over Scale-MAE), UC-Merced linear 97.6 (+11%); adapting X-STARS (LS→S6): EuroSAT 95.0/96.1. Always beats GFM continual pretraining.
- Ablations: patchwise alignment + smoothing best (EuroSAT 92.7 vs 91.6 baseline MSAD); smoothing alone hurts (85.6); lambda in [0, 0.3] improves over DINO-only, 0.1 optimal, large lambda collapses; MSAD speeds convergence (400 epochs w/ MSAD ≈ 800 w/o: EuroSAT 93.4 vs 93.3); 3-sensor joint training saturates (pairwise inconsistencies); gains biggest when adaptation GSD matches downstream GSD; few-shot: 5% labels EuroSAT 88.1% (X-STARS) vs 75.2% (Scale-MAE).

## What transfers to our thesis
- **Directly relevant to cross-sensor Landsat work**: X-STARS explicitly trains on Sentinel-2 + Landsat-8 pairs (MSC-France) and shows sensor-agnostic features transfer across 10 m/30 m GSD — the exact problem of mixing Landsat optical (30 m) with thermal LST and possibly Sentinel-2 calibration shifts.
- MSAD's core idea transfers to **cross-year alignment**: contrast the same field's features from year Y and year Y' (or paired Landsat/Sentinel-2 acquisitions) with smoothed, patchwise InfoNCE — a principled way to build cross-year-consistent field embeddings without labels, supporting our "cross-year model reuse" goal.
- Label smoothing rationale is insightful for agriculture: same-field acquisitions at different dates are never perfectly aligned (phenology) — hard positives would push seasonality signal into the embedding; softening is the stated remedy.
- Continual pretraining recipe: pretrain once on the long historical archive, then cheaply adapt (400 epochs, frozen teacher) to a new product/region/year — matches our lightweight multi-product reuse story.
- MIM underperforms contrastive approaches at low resolution / small data (SatMAE/Scale-MAE trained on S2-LS drop to 83.4/70.2 kNN EuroSAT) — caution for masked-modeling choices on 30 m Landsat; but note this is for images, and Presto showed the opposite for pixel time series.

## Limitations / caveats
- RGB-only experiments (drops multispectral and thermal; no time-series input — single-date images).
- Saturation with >2 sensors due to pairwise averaging of the alignment loss; no SAR/thermal yet (authors list it as future work).
- Requires co-located paired acquisitions from multiple sensors — for Landsat-only archives, cross-sensor pairs are unavailable (would need S2-LS pairs for adaptation).
- Downstream tasks are land cover / urban classification, not crop stress; mIoU values on CLC (Landsat-8) are low (~20).

## Key numbers to quote in lit review
- Cross-sensor SSL on S2+Landsat-8 with only ~5k patches matches/exceeds Scale-MAE trained on 363k fMoW patches (EuroSAT kNN 94.4% vs 92.9%).
- Patchwise dense alignment + label smoothing (alpha=0.3) yields +1.1% EuroSAT accuracy over global-token MSAD; alignment loss weight lambda=0.1 optimal, >0.3 collapses.
- Continual pretraining adapts Scale-MAE to aerial imagery, +11% linear-probing accuracy on UC-Merced and +1.4 mIoU FLAIR.
- Few-shot EuroSAT with 5% labels: X-STARS 88.1% vs Scale-MAE 75.2%.



---


## FILE: 2024 Najjar et al. - XAI-Guided Enhancement of Vegetation Indices for Crop Mapping (arXiv).md
# XAI-Guided Enhancement of Vegetation Indices for Crop Mapping

## Full citation
Najjar, H., Mena, F., Nuske, M., & Dengel, A. (2024). "XAI-Guided Enhancement of Vegetation Indices for Crop Mapping." IGARSS 2024, arXiv:2407.08298v1 (RPTU Kaiserslautern-Landau / DFKI).

## Problem & setting
- Crop-type classification from Sentinel-2 time series in Ghana + South Sudan (Rustowicz et al. 2019 African crop dataset), Jan-Dec 2016, 10 m, 10 S2 bands + cloud-coverage channel; classes with >10k pixels: maize (329,847 px), groundnut (101,314), rice (98,986), soybean (67,638), sorghum (65,185), yam (22,091).
- Goal: use XAI feature attribution (not SSL) to find which bands matter, then design/select vegetation indices (VIs) that compress the model input.

## Method
- **Supervised pipeline, XAI-guided feature engineering**: (1) train a GRU (pre-padded to length 228, weighted sampler for imbalance) on all 10 bands; (2) attribute band importance with **Shapley Value Sampling (SVS)** — up to 10,000 correctly classified pixels per class, attributions grouped over time per band, negatives suppressed, per-pixel normalized to sum 1, averaged globally and per class; (3) select/modify VIs to cover high-attribution bands; (4) retrain on individual VIs or pairs of two.
- Newly proposed indices: n-NDVI (n-NIR instead of NIR), NDRE2 (RE2), NDRE3 (RE3), NDMI2 (SWIR2). Constraint: each index contains at least one 10 m band.

## Data & labels
- Fully supervised; labels from the public African crop segmentation dataset; 5% validation split, patch-disjoint (pixels of the same image patch never split across train/val).

## Results
- Baseline GRU on 10 bands: OA 67%, weighted F1 0.67 (rice 0.84, sorghum 0.86, yam only 0.27).
- Attribution ranking (global): SWIR1 and RE1 each ~20% of total importance, then red, SWIR2, n-NIR, NIR; cloud mask channel marginal (no leakage).
- Single VI: NDMI (NIR-SWIR1) best, OA 0.65 (-2 pp vs baseline) but beats baseline on sorghum, groundnut, yam; NDMI2 (SWIR2) best for rice (0.76); NDVI best for maize/soybean.
- Two VIs: **NDRE + NDMI2 = OA 0.70 / F1 0.70, +3 pp over the all-band baseline**, best for sorghum (0.88), maize (0.70), rice (0.83), and beats baseline on groundnut and yam. NDMI + n-NDVI comparable (0.68). NDRE+n-NDVI worst.
- Proposed NDMI2 > NDMI for rice confirms the SWIR2 attribution; NDRE2/NDRE3 underperform NDRE except for soybean/sorghum, matching their RE2/RE3 attributions.

## What transfers to our thesis
- **Recipe for our XAI thread**: train model on raw bands -> Shapley Value Sampling per band (temporal aggregation) -> design minimal indices. Translates directly to Landsat: e.g., verify whether an ETa/CWSI-proxy index (thermal + SWIR-based, Landsat lacks red-edge) plus one SWIR/water index suffices for sugarcane water/salinity stress.
- Justifies **lightweight multi-product models**: two VIs (2 channels instead of 10 bands) gave +3 pp over the full-band baseline in medium-sized datasets — supports our claim that compact, index-based inputs (NDVI + LST/NDMI/NDWI-like) can outperform band-stacks on moderate data, easing in-field deployment.
- For stress (not just type): SWIR1/SWIR2 importance for water-related discrimination (rice/yam) supports using NDMI/NDWI-style and thermal indices in salinity/water-stress detection; note Landsat has SWIR1/SWIR2 and thermal, but no red-edge — XAI-guided index design must be sensor-aware.
- Caveat they explicitly state: explanation quality is bounded by model accuracy (OA 67% baseline) — in our thesis, XAI on SSL embeddings needs a validated downstream task first.

## Limitations / caveats
- Supervised only — no SSL, no label-free setting; single year (2016), two countries; medium-size data with heavy class imbalance (yam 22k px).
- SVS on 10k pixels/class is computationally heavy and attribution-to-VI mapping is partially inconsistent (soybean/yam RE behavior contradicts attributions).
- Baseline GRU accuracy modest (67%), so attribution reliability is limited by model quality (acknowledged by authors).

## Key numbers to quote in lit review
- Two XAI-selected indices (NDRE + NDMI2) beat the 10-band baseline: OA 70% vs 67% (+3 pp) on African crop mapping.
- Single NDMI index alone reaches OA 65% (-2 pp only) — vegetation-index compression retains most signal.
- SVS attribution: SWIR1 and red-edge-1 carry ~20% importance each for crop discrimination in S2 time series.
- Landsat-relevant: SWIR2 (NDMI2) was the single best index for rice (water-associated) — supports SWIR/thermal indices for water-stress detection on Landsat.



---


## FILE: 2024 Qin et al. - SITSMamba - Mamba for Crop Classification on Satellite Image Time Series, IGARSS (arXiv).md
# SITSMamba: Crop Classification based on Satellite Image Time Series with Mamba

## Full citation
Qin, X., Su, X., & Zhang, L. (2024). "SITSMamba for Crop Classification based on Satellite Image Time Series." IGARSS 2024, arXiv:2409.09673v2 (Wuhan University). Code: github.com/XiaoleiQinn/SITSMamba.

## Problem & setting
- SITS crop classification with long series (38-61 Sentinel-2 acquisitions in PASTIS); Transformer self-attention is quadratic in sequence length, limiting long time series; and standard supervised training uses only crop labels, under-exploiting temporal structure.
- First application of Mamba (selective SSM) as a SITS temporal encoder.

## Method
- **Architecture**: per-timestep CNN spatial encoder (UTAE's ConvBlock: 2x Conv2D 3x3, 128 filters, BN+ReLU) -> reshape to (H*W) x T x 128 -> **Mamba block** as temporal encoder (linear complexity, selective SSM with SiLU-gated branches).
- **Multi-task two-branch decoder** (key design):
  - *CBranch* (classification): temporal max-pool -> ConvBlock -> per-pixel crop map; cross-entropy L_cls.
  - *RBranch* (reconstruction): Linear layer maps encoded features back to the original SITS values; auxiliary self-supervised signal **integrated directly into supervised training** (not a two-stage pretrain-finetune). MSE loss with **Positional Weight (PW)** {1/L, 2/L, ..., L/L} — later timesteps weighted more (assumption: later positions are easier to predict, so early-season values dominate plain reconstruction otherwise).
  - Overall loss L = L_cls + w0 * w1 * L_tp, w0 = 0.03 (best in sweep 0.01-0.1), w1 = L_cls/L_tp (adaptive loss-ratio balancing).
- Inference uses only CBranch. Trained 100 epochs, Adam lr 1e-4, RTX 3090.

## Data & labels
- **PASTIS32**: PASTIS Sentinel-2 (4 tiles in France, Sep 2018-Nov 2019, 10 bands, 10 m, 38-61 acquisitions), clipped to 32x32 patches, 20 classes, folds 1/4/5 for train/val/test.
- **MTLCC**: Munich 102x42 km, Sentinel-2 2016, 13 bands, 30 timesteps, 6248 patches 48x48, 18 classes, split 4:1:1.
- Supervised labels for CBranch; SITS itself is the unlabeled supervision for RBranch.

## Results
- **PASTIS32**: SITSMamba OA 0.7416, mIoU 0.5005, mF1 0.6449 — beats UTAE (0.7349/0.4686/0.6107), TSVIT (0.7200/0.4561/0.5999), 3D U-Net, BCLSTM and ConvLSTM variants.
- **MTLCC**: OA 0.9104, mIoU 0.7639, mF1 0.8496 — beats UTAE (0.9063/0.7467/0.8391) and BUnetConvLSTM; best F1 in 9/17 classes.
- **Complexity**: only 0.25 M params and 56.5 GFLOPs vs UTAE 1.09 M / 28.8 GFLOPs, TSVIT 2.16 M / 84.4 GFLOPs, 3D U-Net 6.18 M / 274 GFLOPs — smallest model in the comparison.
- **Ablations (PASTIS32)**: full model mF1 0.6449; w/o PW 0.6401 (-0.5 pp); w/o w1 0.6250 (-2.0 pp); w/o RBranch entirely 0.6301 (-1.5 pp) — auxiliary reconstruction consistently helps; w1 (loss-ratio balancing) the most important component.
- Qualitative: better parcel boundary delineation in fragmented areas; better on hard classes (winter triticale F1 0.4632 vs UTAE 0.3407; sorghum 0.4139 vs 0.2697).

## What transfers to our thesis
- **Mamba as temporal encoder for long Landsat series**: linear-complexity sequence modeling fits 16-day composites spanning many years (hundreds of timesteps) where attention becomes expensive; 0.25 M params fits the "lightweight" requirement for in-field deployment.
- The **single-model multi-task design** (classification head + auxiliary reconstruction with positional weighting) is directly reusable: for stress detection, an auxiliary branch reconstructing the NDVI/LST/ETa series (or a forecasting branch) regularizes the encoder without extra labels; PW suggests up-weighting recent/recently-reconstructed timesteps.
- Benchmark context: Mamba ~+0.7-2.8 pp OA over UTAE/TSVIT on 20-class PASTIS with 38-61 timesteps — evidence for the SSM-vs-Transformer trade-off we can cite when justifying our backbone choice.
- Caveat they flag applies to us: reconstructing raw SITS reconstructs cloud/snow noise too — masking or cloud screening is needed; for our stress task, reconstructing *normal* phenology (e.g., on healthy years) is preferable to reconstructing raw inputs.

## Limitations / caveats
- Fully supervised crop classification (labels needed); no stress/anomaly task.
- Mamba only temporal; spatial context by a simple 2-layer CNN; no bidirectional scan (one-directional sequence).
- RBranch reconstructs noisy (cloudy) values — authors note this may harm optimization.
- Sentinel-2 only, 10 m; no Landsat, no thermal; accuracy numbers not directly comparable to full-resolution PASTIS benchmarks (32x32 clipping).

## Key numbers to quote in lit review
- SITSMamba: OA 74.16% (PASTIS32) and 91.04% (MTLCC), first Mamba-based SITS crop classifier.
- Smallest and fastest in comparison: 0.25 M params, 56.5 GFLOPs vs TSVIT 2.16 M / 84.4 GFLOPs.
- Auxiliary in-training reconstruction branch adds +1.5 pp mF1; position-weighted reconstruction loss adds another +0.5 pp.
- Linear-complexity SSMs beat quadratic Transformer temporal attention (UTAE, TSVIT) at 38-61 timesteps while using 4x fewer parameters.



---


## FILE: 2024 Shikhar and Sobti - Label-free Anomaly Detection in Aerial Agricultural Images with Masked Image Modeling (arXiv).md
# Label-free Anomaly Detection in Aerial Agricultural Images with Masked Image Modeling

## Full citation
Shikhar, S. & Sobti, A. (2024). "Label-free Anomaly Detection in Aerial Agricultural Images with Masked Image Modeling." arXiv:2404.08931v1 [cs.CV] (Plaksha University).

## Problem & setting
- Agricultural anomaly segmentation (nutrient deficiency, water stress, weed clusters, drydown, planter skip, double plant, endrow, waterway, storm damage) in UAV imagery without labels; goal is a single label-free model across all anomaly types that does NOT require curating "normal-only" training data.
- Data: Agriculture-Vision Challenge — 94,986 aerial images from 3,432 US farmlands, RGB+NIR (4 bands), 10 cm/px, 512x512 crops; 56,944/18,334/19,708 train/val/test; 9 anomaly classes (previous work reported 6).

## Method
- **SwinMAE (Swin-Transformer masked autoencoder)**: 4 Swin blocks encoder + lightweight Swin-Unet-like decoder; window masking strategy — divides the image into larger non-overlapping windows and masks whole windows (instead of individual 4x4 patches), preventing shortcut interpolation from neighboring unmasked patches; masked tokens replaced by learnable vectors so token count stays constant through the encoder (unlike MAE which drops masked tokens). Trains on 25% visible patches.
- **Anomaly detection by reconstruction error**: at inference, K=32 different random window masks; per-pixel error averaged over K reconstructions; binarized by Knee-point (Kneedle) thresholding.
- **Anomaly Suppression Loss (ASL)** (adapted from Wang et al. Auto-AD for hyperspectral): adaptive weight map w_ij = max(E) - e_ij over the reconstruction-error map, updated periodically after an initial 20 epochs; down-weights pixels with large reconstruction error (i.e., the anomalies) in the MSE loss L = sum w_ij*e_ij, so the network stops learning to reconstruct anomalies while training on uncurated (anomaly-contaminated) data — removes the normal-only training assumption.
- Training: 224x224 input, AdamW lr 1e-3, 200 epochs, batch 64, single 24 GB A5000.

## Data & labels
- No anomaly labels used in training (fully self-supervised reconstruction); ground-truth anomaly masks only for IoU evaluation. Leave-one-out protocol for Table 1 (train with anomaly class excluded); Table 2 trains with all anomalies included thanks to ASL.

## Results
- 6-class mIoU (comparable protocol): DSVDD 18.2, ARNet 20.5, GANomaly 25.3, InTra 29.3, ASD 29.4, RIAD 31.7, **MAE 36.2, SwinMAE 37.5, SwinMAE+ASL 38.0** — +6.3 mIoU over prior SSL/unsupervised SOTA (RIAD).
- 9-class: best IoU per class e.g. planter skip 52.7, waterway 46.9, double plant 46.6, water 37.8.
- Label-free robustness (Table 2): with anomalies included in training, mIoU 36.44 (median class IoU 42.3 vs 45.8 normal-only); only Drydown and Water degrade strongly (45.83->28.1 and 45.97->37.8) because these classes overlap least with other anomalies' distribution.
- Supervised upper bounds for context: AAFormer 41.2 mIoU; FusePN dice 82.71.
- Failure modes: dispersed anomalies (weeds, water) reconstructed well (learned as part of normal distribution); non-agricultural objects (trees, roads, cars) flagged as anomalies.

## What transfers to our thesis
- **The core template for our label-free sugarcane stress detection**: masked reconstruction of field time-series (or per-date image stacks), anomaly score = reconstruction error, threshold = knee point. On Landsat 16-day series, replace window masking with timestep/band masking (as in Presto) and score field-pixels by reconstruction error of masked composites.
- **ASL (adaptive suppression loss) is the key transferable trick**: our training archive will inevitably contain stressed fields; ASL lets the model learn normal crop phenology without manually filtering "healthy" fields — directly addressing a major practical objection to anomaly-detection-on-normal-data designs.
- Knee-point automatic thresholding avoids a hand-tuned anomaly threshold — useful for operational per-field stress flagging across years.
- Demonstrated limits that we should anticipate: anomalies that are spatially diffuse and distribution-overlapping (like gradual water stress across a field) are the hardest for reconstruction-based AD; single-date RGB/NIR misses them — our multi-temporal (seasonal) formulation should mitigate this.

## Limitations / caveats
- UAV 10 cm RGB+NIR single-date images — no temporal dimension, no thermal; agricultural anomalies defined by pattern shape, unlike satellite-resolution stress signatures.
- With anomalies in training, two of nine classes degrade sharply (drydown, water); dispersed anomalies poorly caught; non-field objects trigger false positives.
- Supervised SOTA (41.2 mIoU) still 3+ pp higher than the label-free method; knee-point threshold is image-global, not field-adaptive.

## Key numbers to quote in lit review
- Masked image modeling beats prior unsupervised AD on Agriculture-Vision by +6.3 mIoU (SwinMAE+ASL 38.0 vs RIAD 31.7 on 6 classes).
- Anomaly suppression loss allows training on anomaly-contaminated data with only ~3.5 median-IoU loss (42.3 vs 45.8 normal-only) — no normal-data curation needed.
- Reconstruction-based AD fails on spatially diffuse anomaly classes (weed/water) even with 75% masking — a documented caveat for reconstruction-error stress detection.
- Label-free SwinMAE approaches supervised AAFormer (38.0 vs 41.2 mIoU) within ~3 pp.



---


## FILE: 2025 - AgroGraphNet - Intelligent Crop Disease Prediction using Spatio-Temporal GNNs.md
# AgroGraphNet — Intelligent Crop Disease Prediction Using Spatio-Temporal Graph Neural Networks

## Full citation
Bose, S. R., Jeba, J. A., Evangeline, N. C., Regin, R., Sameer Ali, M. M., Aravintha, S. J. V. (2025). Intelligent Crop Disease Prediction Using Spatio-Temporal Graph Neural Networks. *FMDB Transactions on Sustainable Intelligent Networks*, 2(4), 176–189. DOI: 10.69888/FTSIN.2025.000549. (Low-tier venue; treat cautiously.)

## Problem & setting
- Task: supervised crop disease prediction per farm (Healthy / Blight / Rust / Mosaic / Bacterial) by modeling farms as graph nodes; edges from spatial proximity (<5 km configurable) + environmental similarity.
- Data: farm-level CSVs — Sentinel-2 10 m vegetation indices (NDVI, NDRE, GNDVI, EVI, SAVI, NDWI), daily weather (temp, rain, humidity, wind) aggregated to 7-day/30-day windows, lab soil properties (pH, nutrients, texture), management records, agronomist disease labels. Multi-season; 72.2% healthy, Rust 9.4%, Blight 8.2%, Mosaic 6.2%, Bacterial 3.8%.

## Method
- Fully supervised (NOT SSL). Three GNNs compared: GCN (Kipf-Welling spectral conv), GraphSAGE (inductive neighbor sampling/aggregation), GAT (attention-weighted neighbor aggregation); GNN branch F→128→64 conv layers, ReLU, dropout (0.5 in diagram / 0.2 in training config); 3 hidden layers of 64 dims, Adam lr=0.001, batch 32, early stopping patience 10, converges in 40–60 epochs.
- Ensemble: 3 GNNs + Random Forest + SVM + Logistic Regression → majority voting + confidence averaging; CLI package for preprocessing/training/visualization.
- Evaluation protocols: random 60/20/20 split; spatial CV via k-means clusters on coordinates assigned wholly to train/val/test; temporal validation holding out the most recent season.

## Data & labels
- ~5,000 fields for full-graph training (synthetic graphs >50,000 nodes for scaling tests); labels from expert visual inspection + lab testing. Satellite features 10 m S2; Landsat mentioned only as complementary source.

## Results
- Accuracy: GAT 91.6% > GraphSAGE 89.7% > GCN 88.3%; GNNs beat CNN/MLP baselines that treat fields as isolated samples. GraphSAGE most robust across spatial/temporal evaluation conditions.
- Full-graph training on ~5,000 fields: 2–3 h on an RTX 3050 (16 GB RAM); mini-batch on >50k-node synthetic graphs 4–6 h; inference <10 s.
- Feature correlation matrix: NDVI–EVI correlation only 0.12, weather correlations −0.09 to 0.04 — used to justify multi-source integration.
- No per-class F1 table or confidence intervals reported; example output shows uniform 0.800 ensemble confidence for all Healthy predictions — weak evidentiary depth.

## What transfers to our thesis
- Limited direct transfer (supervised, no SSL, no time-series encoder), but the **field-as-node graph with edges from distance + environmental similarity** is a relevant relational prior for our sugarcane scheme: spatially adjacent fields share water/salinity stress drivers, and a graph over field embeddings from our SSL encoder could propagate stress evidence to label-scarce fields.
- The spatial k-means cluster CV and hold-out-last-season validation are exactly the cross-year generalization protocols we should adopt and report.
- Supports the argument that ignoring spatial context underperforms — a baseline motivation for including inter-field context in a lightweight multi-product model.

## Limitations / caveats
- Weak venue (FMDB Transactions), no public data ("available on request"), no code link, no ablation of edge construction, no precision/recall/F1 numbers despite claiming them; sample output table is degenerate (all identical predictions/confidence 0.800).
- Supervised only; requires agronomist labels; disease classes generic (not sugarcane, not water/salinity stress).
- Small real dataset (~5k fields), scaling numbers from synthetic graphs.

## Key numbers to quote in lit review
- GAT 91.6% / GraphSAGE 89.7% / GCN 88.3% accuracy for farm-level disease classification vs isolated-sample CNN/MLP baselines.
- Edge threshold 5 km spatial proximity + environmental similarity; node degree typically 2–3.
- Full-graph training of ~5,000 fields feasible on consumer GPU (RTX 3050) in 2–3 h; inference <10 s.
- Class imbalance: 72.2% healthy vs 3.8–9.4% per disease class.



---


## FILE: 2025 - BTSM-UNet - Bidirectional Temporal-Spatial Mamba-UNet for Winter Wheat (Smart Agricultural Technology).md
# BTSM-UNet: Bidirectional Temporal-Spatial Vision Mamba-UNet for winter wheat classification based on Sentinel-2 imagery

## Full citation
Fan, L., Chen, S., Xia, L., Zha, Y., Zhou, Q., Yan, Q. (2025). BTSM-UNet: Bidirectional Temporal-Spatial vision Mamba-UNet for winter wheat classification based on Sentinel-2 imagery. *Smart Agricultural Technology*, 12, 101547. DOI: 10.1016/j.atech.2025.101547. Chinese Academy of Agricultural Sciences.

## Problem & setting
- Task: supervised binary semantic segmentation (winter wheat vs non-wheat) from Sentinel-2 time series; goal is efficient large-area crop mapping (long time series, low compute).
- Study area: 10 sites of 4000×4000 px (40 km × 40 km) across China's main winter-wheat regions (North China Plain dominant); 8 train (A–H), 2 geographically separate test sites (T1, T2).
- Data: S2 Level-2A SR from GEE, growing season 1 Oct 2022 – 30 Jun 2023, cloud <20%, resulting in 152 clear images with Day-of-Year kept per observation; 9 bands (B2,B3,B4,B5,B6,B7,B8,B11,B12 — red-edge included, 60 m bands and B8A dropped).

## Method
- BTSM-UNet: UNet-style encoder–decoder where the three middle encoder layers insert a **Bidirectional Temporal-Spatial vision Mamba (Bi-TSM)** module.
- Key design: spatio-temporal DECOUPLING — 2D CNNs first extract multi-scale spatial detail per date; then bidirectional Vision Mamba models the temporal dimension as a sequence (forward + backward selective scan, O(T) instead of attention's O(T²)); complexity becomes additive O_space + O(T·D) rather than multiplicative like 3D CNNs. Motivation: avoid "spatio-temporal entanglement" of joint 3D processing (field texture vs phenology).
- Decoder fuses CNN local spatial features with Bi-TSM global spatiotemporal features at 3 scales (downsample 64/32/16) via deconvolution; single deconv output head. Fully supervised segmentation loss (cross-entropy family); no SSL, no masking.
- Baselines: UNet3D, UNet2D-LSTM, CNN-BiLSTM, TSViT, UTS-Former, VM-UNet.

## Data & labels
- Labels: Yang et al. 10 m China winter wheat product (2020–2022, knowledge-based + ML, OA >0.90, provincial R² ≥0.95 vs census) — an existing map, not field surveys.
- 8 train sites vs 2 held-out test sites = spatial cross-site generalization design.

## Results
- Test sites: T1 MCC 0.902 / F1 0.948; T2 MCC 0.908 / F1 0.957; overall best MCC 0.905, F1 0.952, precision 0.954, recall 0.951.
- Beats UNet3D (MCC 0.882), UTS-Former (0.881), VM-UNet (0.843), UNet2D-LSTM (0.827), TSViT (0.819), CNN-BiLSTM (0.659); relative MCC gain +2.5% over best CNN baseline.
- Efficiency: 4.86 M params, 60.19 GFLOPs, fastest inference 24 FPS — vs UNet3D 6.16 M / 2159 G FLOPs / 9 FPS; VM-UNet lacks the temporal module.
- Band-combination robustness: restricting to RGB, BTSM-UNet MCC drops only 2.43% (relative, MCC/All) vs 28.4% for CNN-BiLSTM — temporal modeling compensates for spectral poverty.

## What transfers to our thesis
- Direct architectural template for our **lightweight multi-product in-field model on Landsat 16-day series**: decoupled 2D-spatial + 1D-temporal Mamba keeps complexity additive in T — matches our long, cloudy, irregularly-sampled Landsat stacks (their DoY-encoding of irregular acquisitions is reusable).
- The 4.86 M-param / 60 G class of model is exactly the "lightweight in-field" budget; cross-site train/test (8 vs 2 disjoint regions) is our cross-year/cross-field protocol analog.
- Strong empirical evidence that **good temporal modeling partially substitutes for spectral bands** (RGB-only −2.43% MCC): supports our premise that with 16-day optical+LST and a strong temporal encoder, labels — not bands — are the bottleneck; also relevant if we drop noisy bands.
- Mamba vs Transformer efficiency claim (vision transformer ≈35× vision-mamba compute at same sequence input) — quotable for justifying SSM choice over ViT for Landsat time series.

## Limitations / caveats
- Fully supervised with map-derived labels (inherits label noise from Yang et al. product); binary crop-only task; no stress/anomaly component.
- S2 5-day revisit and 152 clear scenes — far denser than Landsat 16-day; no SSL pretraining, so temporal representation is learned only from ~8 sites of labels.
- No cross-YEAR test (single season 2022–23); spatial encoders only 2D per date; no comparison to masked-pretraining baselines.
- MCC/F1 from one season, one crop; cloud handling not deeply addressed despite claims about Landsat cloud issues.

## Key numbers to quote in lit review
- Bi-TSM-UNet: MCC 0.905, F1 0.952 winter-wheat mapping with only 4.86 M params, 60.19 GFLOPs, 24 FPS (best of 7 deep models tested).
- RGB-band-only MCC drops 2.43% for BTSM-UNet vs 28.4% for CNN-BiLSTM — temporal modeling buffers spectral loss.
- Decoupled spatial(2D-CNN)+temporal(bidirectional Mamba) design: O(HW·C²k²) + O(T) vs joint 3D convolution's multiplicative T·H·W·C²·t·k².
- Vision Transformer ≈35× the computational load of vision Mamba for equal sequence input (cited from prior work).



---


## FILE: 2025 - GWSC-SegMamba - Gate Wavelet Spatial Convolution State Space Model for Multi-Temporal Agricultural Segmentation (IEEE Access).md
# GWSC-SegMamba: Gate Wavelet Spatial Convolution Enhanced State Space Model for Multi-Temporal Agricultural Land Segmentation

## Full citation
Hestrio, Y. F., Mantau, A. J., Jatmiko, W. (2025). GWSC-SegMamba: Gate Wavelet Spatial Convolution Enhanced State Space Model for Multi-Temporal Agricultural Land Segmentation. *IEEE Access*, 13, 133246–133274. DOI: 10.1109/ACCESS.2025.3593389. University of Indonesia + BRIN.

## Problem & setting
- Task: supervised multi-temporal agricultural land / crop segmentation with linear-complexity sequence modeling; targets spectrally analogous crops and minority classes.
- Datasets (all Sentinel-2 time series): Munich (8,610 patches; 17 crop classes; 2016–17), Lombardia (29,962 patches; 7 classes; 9 bands B2–B8,B11,B12 + MSA VI; 4 years 2016–2019, two test sets A and Y), PASTIS (2,433 patches of 128×128; 20 French crop classes; 10 S2 bands).

## Method
- GWSC-SegMamba: SegMamba (3D Mamba segmentation backbone) extended with two gating modules:
  - **GWC (Gate Wavelet Convolution)**: discrete wavelet transform multi-resolution decomposition — low-frequency = seasonal phenology, high-frequency = texture; intended to sharpen discrimination of spectrally similar crops.
  - **GSC (Gate Spatial Convolution)**: dual-path 3×3 conv (local) + 1×1 conv (global context) for field-boundary delineation.
- Complexity of additions is additive: O(HWD·(3C²+4CD+W+S)) vs base SegMamba O(HWD·(3C²+4CD)); SSM temporal scan keeps linear cost in sequence length, vs Swin-UNETR's window-quadratic term.
- Loss: Dice-Focal (α Dice overlap + β focal weighting γ for hard examples), compared against CE and Dice-CE; 200 epochs, cosine annealing, weight decay 1e-3; systematic search over optimizers (SGD/Adam/AdamW), batch sizes, LRs, depths, feature sizes; V100 GPUs; flip augmentation only.
- Extensive statistics: independent t-tests + bootstrap (n=1000), 95% CIs, Cohen's d.
- Fully supervised; no SSL component. The paper also contains a long theoretical section (information-theoretic theorems, PAC-Bayes bounds) — mostly decorative.

## Data & labels
- Standard public benchmarks with per-pixel crop labels; no labels avoided — purely supervised segmentation.

## Results
- Headline gains vs SegMamba: +7.65% mIoU (claimed), vs Swin-UNETR +4.43%; minority-class IoU +53.13% (winter triticale claimed).
- Per-dataset (measured): PASTIS — biggest benefit: OA ≈0.82 (+7.66% vs Swin-UNETR, p=0.002, Cohen's d=4.12), Kappa +9.08%, weighted precision +11.81%; mIoU gain +2.39% NOT significant (p=0.078). Munich — OA +1.79% (d=0.85), Kappa +2.24%, weighted F1 +1.79%; but mIoU significantly WORSE than Swin-UNETR (−5.02%, p=0.003). Lombardia — NO significant difference on any of 7 metrics; baseline SegMamba beat GWSC on per-class F1 (rice 0.34 vs FPN 0.62).
- Ablation: GWC positive on Munich (+2.42% OA) and PASTIS (+7.24% OA, +25.93% RAcc); GSC positive mainly on PASTIS; BOTH components negative or neutral on Lombardia. mIoU consistently lower than baseline SegMamba on Munich (0.790 baseline best) and PASTIS (0.423 baseline best) — the extra components trade per-class balance for overall accuracy.
- Failure modes: F1 = 0.00 for winter spelt (Munich), and for small grain cereals, spring barley, soy (PASTIS), where U-Net 3D still scored 0.47–0.79.
- Overhead: ~8–10% compute over base SegMamba; linear scaling retained.

## What transfers to our thesis
- The **wavelet (frequency) decomposition of temporal features** — low-frequency = phenology, high-frequency = intra-season events — is a transferable idea for sugarcane stress: water/salinity stress signatures may live in specific frequency bands of the NDVI/LST time series; a wavelet-gated module over Landsat time series could separate slow phenology from stress-induced anomalies.
- Linear-cost Mamba backbone for multi-year Landsat stacks (long T) is reinforced; ~8–10% overhead quantifies the cost of adding multi-resolution gating.
- The honest negative results are instructive: architecture add-ons are dataset-dependent, and boosting OA can silently degrade minority-class mIoU — for our rare stress events we should report per-class/IoU-style metrics, not just accuracy.
- Bootstrap + Cohen's d evaluation protocol is a good template for our cross-year comparisons.

## Limitations / caveats
- Supervised only; no SSL; no Landsat/thermal; Sentinel-2 5-day dense series.
- Gains inconsistent across datasets (none on Lombardia); several total class failures (F1=0); mIoU of the full model often WORSE than baselines — the abstract's headline numbers are cherry-picked relative to specific baselines.
- Heavy pseudo-theoretical section (PAC-Bayes, information theorems) adds no empirical value.
- No temporal-length ablation, no param count table for the models, no cross-year holdout within dataset.

## Key numbers to quote in lit review
- GWSC-SegMamba on PASTIS: OA +7.66% over Swin-UNETR (Cohen's d=4.12), Kappa +9.08%, weighted precision +11.81%; but mIoU gain insignificant (+2.39%, p=0.078).
- Component overhead only ~8–10% over base SegMamba with linear temporal complexity O(HWD·(3C²+4CD+W+S)).
- Claimed +53.13% IoU for hard minority class (winter triticale), yet the full model scores F1=0.00 on three other PASTIS classes — architecture gains are class-dependent.
- Wavelet gating premise: low-frequency components encode seasonal phenology, high-frequency encode texture/detail — separable for spectrally similar crops.



---


## FILE: 2025 - Integrating Phenology Knowledge Graph into Parcel-Scale Crop Classification (Int J Applied Earth Obs Geoinformation).md
# Integrating phenology knowledge graph into parcel-scale crop classification using multi-period deep time series modelling (TSKG)

## Full citation
Shen, Q., He, D., Liu, X., Shi, Q. (2025). Integrating phenology knowledge graph into parcel-scale crop classification using multi-period deep time series modelling. *International Journal of Applied Earth Observation and Geoinformation*, 143, 104809. DOI: 10.1016/j.jag.2025.104809. Sun Yat-sen University.

## Problem & setting
- Task: supervised parcel-scale crop classification (wheat / rice / other) from multi-modal monthly time series; novelty = automatically constructed crop remote-sensing knowledge graph (KG) as a global classifier guide + multi-period (FFT-based) temporal feature extraction.
- Study area: 4 Yangtze River cities (Wuhan, Nanjing, Jingzhou, Yichang); ~4,100–4,900 field-survey samples per city (e.g., Wuhan: 1403 wheat / 1520 rice / 1203 other), parcel vectors from Zhu et al. (2023) high-res parcel product.

## Method
- Features per parcel (zonal aggregation): S2 R,G,B,NIR + NDVI + LSWI; S1 VV, VH + Mul/Cross indices + RVI; median-composited to MONTHLY series; Savitzky-Golay (order 3, window 3) gap filling.
- **KG auto-construction**: train a decision tree per city on labeled samples; take top-3 Gini-ranked attributes per node; discretize decision values into 11 verbal levels ("Minimum"… "Maximum", 0.1 bins); emit triples (key recognition feature, month, crop type), e.g., ("Var Red Very High", January, Wheat); add manual phenology nodes. KG is regenerated per region from local samples — no manual ontology.
- **KG embedding**: 2-layer Relational GCN (R-GCN, Schlichtkrull) over the triples → graph feature vectors fed into the classifier head; jointly backpropagated.
- **Multi-period temporal model**: FFT over the multivariate time series → pick top-k dominant frequencies → reshape 1D series into 2D (intra-period × inter-period) tensor → Inception modules (1×1, 3×3, 5×5, MaxPool branches) extract multi-period patterns; concatenate with KG embedding → FC + softmax.
- Baselines: Random Forest (200 trees), Transformer, Informer, DLinear; also TSKG without KG (ablation). Training: 150 epochs, Adam lr 1e-3, batch 16, 6:2:2 split, single RTX 4060 8 GB.

## Data & labels
- Field survey points (quality-controlled); labels only for supervised training/eval and for KG generation. Monthly temporal resolution deliberately coarse (12 steps).

## Results
- OA across 4 cities: 94.43% (Wuhan), 91.26% (Nanjing), 89.45% (Jingzhou), 92.91% (Yichang); F1 essentially identical. TSKG w/ KG beats RF by up to +1.5 OA and Transformer by +0.4–0.7.
- Ablation: KG embedding adds +0.5 (Wuhan 93.94→94.43), +0.2 (Nanjing), +0.8 (Jingzhou), +0.5 (Yichang) OA — modest but consistent, mostly improving spatial consistency in contiguous parcels.
- County-level planting-area validation vs 2020 statistical yearbooks: R² = 0.8944 (wheat, slight overestimation) and 0.9783 (rice).
- Qualitative: KG guidance fixes visually-similar adjacent parcels (rice/wheat continuity cases).

## What transfers to our thesis
- **Automatic KG-from-data** idea transfers directly: our sugarcane phenology/stress knowledge (e.g., "LST high + NDVI drop in dry season → water stress") can be mined as decision triples from unlabeled or weakly labeled series and injected as guidance features — a knowledge-prior alternative to labels in the label-free pipeline.
- FFT-based multi-period reshaping (top-k dominant periods → 2D Inception) is a cheap, lightweight temporal encoder well matched to Landsat's annual cycle + intra-season stress oscillations; runs on an 8-GB RTX 4060 — fits our in-field/low-cost constraint.
- LSWI (water content) + SAR features for moisture status echo our optical+thermal water-stress features; monthly median + SG filtering is a pragmatic baseline preprocessing for 16-day Landsat with clouds.
- County-level R² validation against census statistics is a label-light validation trick usable for our sugarcane area/product sanity checks.

## Limitations / caveats
- Fully supervised (field samples); KG is derived FROM labels via decision trees, so it adds no information beyond the labels — only regularization/consistency; KG gain is +0.2–0.8 OA (small).
- Monthly median composites (12 steps) discard sub-monthly stress dynamics; only 3 crop classes; S1+S2 10 m not Landsat; single-year snapshots.
- KG depends on parcel vector quality (authors flag this); no stress/anomaly task; R-GCN on a small hand-tuned triple set may be overkill.
- Modest absolute gains; baselines (Transformer/Informer) close behind.

## Key numbers to quote in lit review
- TSKG OA 89.45–94.43% across 4 Yangtze cities; KG embedding adds +0.2 to +0.8 OA over the same model without KG.
- FFT-selected top-k periods reshape time series into 2D for Inception — multi-period phenology modeling without hand-defined season boundaries.
- Auto-generated KG triples of form (feature level, month, crop) from decision-tree Gini ranking; per-region KG regeneration.
- County-level planted-area agreement with census: R² = 0.89 (wheat), 0.98 (rice).



---


## FILE: 2025 - RL-VI - Reinforcement-Learning-Based Dynamic Vegetation Index for Rice Crop Stress Detection (Sci Rep).md
# RL-VI: Reinforcement learning based dynamic vegetation index formulation for rice crop stress detection using satellite and mobile imagery

## Full citation
Seralathan, P., Edward, A. S. (2025/2026). Reinforcement learning based dynamic vegetation index formulation for rice crop stress detection using satellite and mobile imagery. *Scientific Reports*, 16, 3447. DOI: 10.1038/s41598-025-33386-9. SRM Institute of Science and Technology, India.

## Problem & setting
- Task: supervised rice crop stress detection (5 severity levels: Healthy/Low/Moderate/High/Extreme) by LEARNING a dynamic vegetation index instead of using static VIs (NDVI, EVI, SAVI, NDMI).
- Setting: rice fields at Polur, Tamil Nadu, India (lat 12.4998, lon 79.1343), kharif 2025; 45 cloud-free Sentinel-2 L2A images (≈10-day intervals, July–Oct 2025) + 1,200 geotagged 64-MP smartphone canopy images from 10 plots; benchmarks: Indian Pines AVIRIS hyperspectral (10,249 px, 224 bands, relabeled vegetation/non-vegetation) and a Wheat Salt Stress hyperspectral set (300 cubes, 204 bands, control vs stressed).

## Method
- VI formulation as an MDP solved with Deep Q-Network: state = normalized reflectance vector + band-selection history; action = select a band triplet (i, j, k) and optional weights (a, b, c) to build VI = (a·Bi − b·Bj)/(c·Bk + ε) (also linear form w1·NIR + w2·SWIR − w3·Red); reward = downstream F1-score, or hybrid F1 − β·entropy of classifier output.
- Learned VI feeds a lightweight classifier (RBF-SVM or 3-layer 1D-CNN with BN, dropout 0.3); DQN: 2-layer MLP [128,64], ReLU, Adam lr 1e-3, γ=0.95, ε-greedy 1.0→0.1, 200 episodes.
- Cross-platform fusion: RGB-derived indices (NDVI_RGB=(G−R)/(G+R), ExG=2G−R−B, VARI) used for validation/reward shaping/state extension; mobile+satellite joint training reported +3.4% accuracy and ~10 days earlier detection.
- Ablations: 2/3/4-band indices (3-band best; 4-band overfits), F1 vs entropy-regularized reward (hybrid slightly better), mobile integration.
- SHAP used to interpret band contributions (red-edge and SWIR most important).

## Data & labels
- Stress labels from expert/ground-truth; stratified 70/15/15 split; class balancing via random undersampling. Fully label-supervised — the RL optimizes a feature, not a representation.

## Results
- Polur Sentinel-2: RL-VI accuracy 89.4%, F1 0.88 vs NDVI 76.5% accuracy / 0.72 F1 (up to +12 points; mean 93.2% acc / 0.91 F1 reported across rice dataset with classwise F1 0.84–0.94).
- Transfer fine-tuning: Indian Pines 91.2% accuracy, +5–7% over NDVI/MLVI; Wheat Salt Stress also improved.
- Early detection: 10–14 days before visible symptoms, notably at panicle initiation/booting/flowering (SWIR/red-edge sensitivity).
- Statistics: one-way ANOVA F=88.24, p<0.001; pairwise t-tests p<0.001; mobile-satellite index discrepancy ≤2.3 pp for RL-VI vs 4.5 pp for NDVI.
- Cross-platform: adding mobile imagery +3.4% accuracy, ~10 days earlier detection.

## What transfers to our thesis
- Core idea is highly relevant: **learned, crop- and region-adaptive band combinations outperform static VIs** for stress; for our label-free sugarcane work, the RL/search objective (F1 reward) can be replaced by SSL/self-supervised criteria (e.g., reconstruction error, temporal contrast, CWSI agreement) to discover stress-sensitive Landsat band/LST combinations without labels.
- Confirms red-edge/SWIR (water content) bands carry earliest stress signal — for Landsat 8/9 this maps to SWIR1/SWIR2 + LST; supports our CWSI/ETa feature choices.
- 3-band composite sweet spot (interpretability vs overfitting) is a useful design rule for lightweight in-field indices/products.
- Hybrid reward (accuracy − entropy) to reduce prediction uncertainty is transferable to any stress classifier under uncertainty-aware deployment.
- Mobile/satellite cross-validation strategy: cheap RGB phone data as weak validation layer for satellite stress maps — usable for our in-field verification protocol.

## Limitations / caveats
- Fully label-supervised reward — needs labeled stress data; not SSL. RL exploration is computationally costly; single season, single region; no cross-year test (authors acknowledge).
- Sentinel-2 10-day composites, small area (one district); 5-class severity labels of unclear provenance/validation; smartphone RGB indices are weak proxies.
- Scientific Reports format; ablation tables sparse; "MLVI/H_VSI" baselines not deeply specified.

## Key numbers to quote in lit review
- RL-learned 3-band VI beats NDVI by ~12 points accuracy (89.4% vs 76.5%, F1 0.88 vs 0.72) for rice stress on Sentinel-2.
- Learned VI detects stress 10–14 days before visible symptoms using SWIR/red-edge sensitivity.
- Adding smartphone RGB imagery to the RL state improves accuracy +3.4% and detection lead ~10 days.
- ANOVA F=88.24 (p<0.001) for RL-VI vs static/ML indices; SHAP ranks red-edge and SWIR bands top for stress discrimination.



---


## FILE: 2025 - Representation Learning of Multi-Spectral EO Time Series - 6.8k-Param AE Ensemble (MDPI Remote Sensing 17-3-378).md
# Representation Learning of Multi-Spectral EO Time Series and Evaluation for Crop Type Classification

## Full citation
González-Ramírez, A., Atzberger, C., Torres-Roman, D., & López, J. (2025). "Representation Learning of Multi-Spectral Earth Observation Time Series and Evaluation for Crop Type Classification." Remote Sensing 17(3), 378. DOI: 10.3390/rs17030378 (CINVESTAV / Mantle Labs).

## Problem & setting
- Crop-type classification from Sentinel-2 spectral time series under cloud corruption; targets the state-of-the-art pain points: (1) complex models, (2) poor scalability to large areas, (3) dependence on interpolation/gap-filling/compositing, (4) dependence on reliable cloud masks, (5) fixed-length inputs.
- Data: BreizhCrops benchmark — Brittany, France, Sentinel-2 L2A, Jan-Dec 2017, 9 crop classes, 608,489 field parcels (FRH01+02 train, FRH03 val, FRH04 test; 319,414/166,367/122,708). Extreme imbalance: temporary meadows >300x sunflower (19 samples) and nuts (49 samples).

## Method
- **Ensemble of C=9 class-specific single-layer autoencoders** (semi-supervised variant): one tiny AE per crop class, each trained (MSE, Adam 1e-4, hidden 5 units, early stopping) only on the time-tagged cloud-free spectral signatures of that class.
- Inputs per observation: 10 S2 bands + 2 cyclic day-of-year encodings (sin/cos of 2*pi*DOY/365 — "spring-fall" and "summer-winter" axes) + 5 spectral indices (NDVI, NDWI, NDTI, NDSVI, EVI); F=17 features. Cloudy observations removed via Sen2Cor scene classification — no gap filling, variable-length per pixel.
- **Representation** (not the AE code, but the residual): for pixel with t valid observations, compute per-AE absolute reconstruction difference vectors |X - X_hat^(c)|, average over t (eq. 7), concatenate over the 9 AEs -> z in R^135.
- Downstream classifier: simple 3-layer FCN (128-64-32) on z; compared with RF, SVM, XGBoost on both raw S2 and z.

## Data & labels
- Labels only for the class-specific AE training (semi-supervised; authors state an unsupervised variant with random/clustered AEs is straightforward future work). Sentinel-2-only, field-level averaged signatures.

## Results
- Separability of representations vs raw data: silhouette -0.76 -> 0.20; Calinski-Harabasz 1.4 -> 73,074; Davies-Bouldin 72.44 -> 18.96.
- Classification (same test samples as [12]): representations improve every conventional classifier by ~2-7% OA; FCN on representations: OA 0.7706, kappa 0.6995, MCC 0.7014 (vs FCN on raw S2 0.7438; XGBoost 0.7139; SVM 0.7466; RF 0.7345).
- vs deep benchmarks (same test set, reported from Rußwurm et al.): Transformer/LSTM OA 0.80 (kappa 0.75), TempCNN/StarRNN 0.79, OmnisCNN 0.73; **AE-FCN 0.77 with only 6,825 parameters and 23.8 it/s** vs Transformer 188,429 params (0.44 it/s) and TempCNN 3.2 M params (0.70 it/s) — ~28-470x fewer parameters, 30-54x faster, only -3% OA.
- Low-label regime: FCN+SVM on representations stay stable at ~30k samples while raw-S2 models degrade; accuracy saturates with more labels (classes not separable from the data itself).
- Failure: sunflower/nuts unclassifiable by every model (19/49 samples); permanent vs temporary meadows confounded; field-polygon mode post-processing removes edge-pixel noise.

## What transfers to our thesis
- **Directly supports the lightweight multi-product in-field model claim**: 6.8k-parameter model, CPU-only, 54x faster than Transformer, within 3% of deep baselines — a concrete existence proof for our "in-field deployable" requirement.
- The **per-class AE ensemble residual as representation** is conceptually adaptable to stress: train AEs on the normal (unstressed) phenology manifold per class/field cluster; the reconstruction-difference vector per field/date becomes both a classification feature and a stress anomaly score. Note the authors themselves connect AE reconstruction difference to change/anomaly detection.
- **Variable-length, gap-free handling of cloud-corrupted series without interpolation** — averaging residuals over whatever clear observations exist is exactly the robustness needed for Landsat 16-day series with clouds/shadows; works as an in-season (anytime) estimate.
- DOY sin/cos time encoding is a cheap trick to embed phenology that transfers directly (though for multi-year Landsat we need year-aware or phase-normalized encodings).
- Reported spectral indices (NDVI, NDWI, NDTI, NDSVI, EVI) as extra input features give gains — supports our multi-product input design (indices + LST-derived proxies).

## Limitations / caveats
- Semi-supervised, not label-free: class-specific AEs need labels (fully unsupervised version left as future work); labels also drive the 9-class split.
- Sentinel-2 field-level signatures only (center pixel averages), no spatial context, no thermal; 2017 single year, single region (Brittany) — no cross-year/cross-region validation.
- Very small classes hopeless (19/49 samples); meadows confusion shows feature ceiling without other sensors (authors suggest radar/thermal).
- Robustness under extreme cloud cover not quantified.

## Key numbers to quote in lit review
- 6.8k-parameter AE-ensemble+FCN reaches 77.06% OA on BreizhCrops — ~4 pp above OmnisCNN (2.7 M params), only ~3 pp below Transformer/LSTM, at 23.8 it/s (54x faster than Transformer).
- Representations lift every conventional classifier by 2-7% OA (FCN 0.7438 -> 0.7706).
- Class separability jumps: Calinski-Harabasz 1.4 -> 73,074, Davies-Bouldin 72.4 -> 19.0.
- Works with any number of cloud-free observations (no gap filling); stable accuracy at ~30k labeled samples (~10% of the training set).



---


## FILE: 2025 - SAKG - Self-Supervised Crop Mapping via Adaptive Clustering + Graph Convolution (Int J Applied Earth Obs Geoinformation).md
# SAKG: Mitigating data constraints in crop mapping — self-supervised framework integrating adaptive clustering, graph convolution and global spatiotemporal attention

## Full citation
Xie, L., You, S., Liu, A., He, Y., Huang, C., Deng, J. (2025). Mitigating data constraints in crop mapping: A self-supervised framework integrating adaptive clustering, graph convolution and global spatiotemporal attention. *International Journal of Applied Earth Observation and Geoinformation*, 144, 104951. DOI: 10.1016/j.jag.2025.104951. Zhejiang University + Land Satellite RS Application Center (MNR, China). Code: github.com/LijianXie/SAKG-net.

## Problem & setting
- Task: SSL-pretrained crop mapping (corn / soybean / other) from Sentinel-2 time series, explicitly evaluated for cross-spatial, cross-temporal, and cross-spatiotemporal transfer.
- Study areas: USA Corn Belt (Grant+Stevens MN, Kossuth IA, Iroquois IL, Jay+Randolph IN) and China (Kedong, Heilongjiang; Si County, Anhui); S2 April–Oct 2019–2021; 10 S2 bands + NDVI + NDMI; 15-day median composites → 14 steps/year; cloud-masked, missing marked 0 (no interpolation); labels from CDL (30 m, resampled 10 m, >95% confidence pixels) and Li et al. China corn/soybean product.

## Method
- Two-branch SSL pretraining (Barlow-Twins-style):
  - Encoder branch: 4 conv layers (3×3, pool, ReLU) each followed by spatiotemporal self-attention (1×1 conv Q/K/V, scaled dot-product, dk=C/8).
  - **Adaptive clustering + graph convolution branch**: 3×3 conv embedding → adaptive K-means (cluster count Kb adapted per sample from feature variance: Kb∈[2, √n], penalty α(Kb−K̂b)², α=0.1; soft one-hot membership weighted features instead of hard labels) → 4 GCN layers (Kipf-Welling propagation) at multiple scales.
  - **Adaptive feature fusion**: Ffused = W1⊙Fc + W2⊙Fg, W1+W2=1, weights from softmax(1×1 conv on concatenated features).
- Pretraining loss (Loss1) = Barlow Twins cross-correlation: Σ(1−Cii)² + λΣΣ_{i≠j}Cij² — diagonal = invariance to augmentation; off-diagonal = band-feature redundancy reduction (explicitly framed as per-band decorrelation for spectral sensitivity).
- Augmentations simulate illumination/cloud/seasonal change (optical domain perturbations).
- Fine-tuning: same trunk + attention-decoder (4 upsampling layers with skip connections), cross-entropy Loss2. lr 0.001, batch 4, Adam, 100 epochs; 7:2:1 split.
- Baselines: SVM, RF, ViT, Swin-UNet, STCLN (SSL), AKG = same architecture WITHOUT pretraining.

## Data & labels
- Pretraining: unlabeled S2 time series patches (all pixels). Labels (CDL / Chinese product) used only for fine-tuning and evaluation.

## Results
- Same-year 2021 US test: SAKG best everywhere — OA 0.9203 (MN), 0.9381 (IA), 0.9184 (IL), 0.9012 (IN); Kappa up to 0.9010; beats STCLN by ~+1.4 OA (MN 0.9067→0.9203) and AKG by ~+0.9–1.8; ViT collapses (OA 0.74–0.81).
- Cross-temporal (2019→2020 same region): SAKG OA 0.8570 (MN) to 0.9015 (IA); best in all 4 states; >80% stable accuracy for every crop.
- Cross-spatial: IN→MN OA 0.8753/Kappa 0.8108; cross-country 2019MN→2019HLJ OA 0.7804 (Kappa 0.6657); HLJ→IL OA 0.7406.
- Cross spatiotemporal (2019→2020, different region): MN→IA OA 0.8338 (Kappa 0.7386); HLJ→MN OA 0.8592; hardest AH→IN OA 0.6860 (Kappa 0.5375) — still best of 7 models.
- Ablation (Iowa 2021): clustering-GCN branch adds +1.89% mF1; + adaptive fusion + self-attention gives +3.09% mIoU; full stack + SSL pretraining +3.79% mIoU over base.
- Label-efficiency: at 10% labels, SSL pretraining gives +1–3% OA and +2% mIoU vs no pretraining.
- t-SNE: post-model features align source and target domain distributions.

## What transfers to our thesis
- Closest architectural analogue to our plan (SSL pretraining + temporal-spatial encoder + cross-year/cross-region transfer on optical time series), with a rigorous three-way transfer protocol we should mirror (spatial / temporal / spatiotemporal) for sugarcane cross-year models.
- **Adaptive K-means → GCN** over clustered pixels: a cheap way to inject spatial structure at field/parcel scale with controlled compute; directly reusable over our field-level Landsat embeddings (cluster fields, propagate features via GCN).
- Bandwise decorrelation (off-diagonal Barlow loss) framed for spectral sensitivity — applicable to our 6–7 Landsat bands + LST with multispectral channels as embedding dims.
- 15-day compositing with 0-fill missing (no interpolation) — same cadence class as Landsat 16-day; shows SSL works with incomplete series.
- Label-efficiency evidence: pretraining helps most at ~10% labels — supports our claim that SSL relieves the label bottleneck for multi-product in-field models.

## Limitations / caveats
- SSL pretraining still followed by supervised fine-tuning (not end-label-free); only 3 classes (corn/soy/other); S2 10 m, no thermal/LST.
- Cross-country transfer degrades notably (AH→IN OA 0.686) — phenology/latitude mismatch; authors recommend similar-latitude transfer.
- GCN cost bounded only via clustering; "other" class heterogeneous; CDL-derived labels carry product noise.
- No stress/anomaly task; small batch (4); no comparison with masked-modeling SSL baselines (only STCLN contrastive).

## Key numbers to quote in lit review
- SSL pretraining (Barlow-style + clustering-GCN) lifts corn/soybean mapping OA to 0.90–0.94 across 4 US Corn Belt counties and wins all cross-spatial, cross-temporal and cross-spatiotemporal transfers.
- Cross spatiotemporal 2019→2020 different-region: OA 0.8338–0.8592 domestically, 0.686–0.786 cross-country (China↔USA).
- At 10% training labels, SSL pretraining adds +1–3% OA and +2% mIoU over training from scratch.
- Ablation: adaptive clustering-GCN +1.89% mF1; full framework +3.79% mIoU vs base encoder.



---


## FILE: 2025 - SSL and Multi-Sensor Fusion PlanetScope-Jilin-1 (MDPI Plants 14-20-3153).md
# Self-Supervised Learning and Multi-Sensor Fusion for Alpine Wetland Vegetation Mapping: Bayinbuluke, China

## Full citation
Zaka, M.M., Samat, A., Abuduwaili, J., Zhu, E., Akhtar, A., & Li, W. (2025). "Self-Supervised Learning and Multi-Sensor Fusion for Alpine Wetland Vegetation Mapping: Bayinbuluke, China." Plants 14(20), 3153. DOI: 10.3390/plants14203153 (Xinjiang Institute of Ecology and Geography, CAS / Univ. Pavia).

## Problem & setting
- Wetland vegetation / land-cover classification and invasive plant species (IPS) early detection in the Bayinbuluke Alpine Wetland (~2,400 m elevation, Xinjiang, China); challenges: spectral similarity of species, patchy invasive distributions, scarce ground truth, spatial heterogeneity.
- Data: PlanetScope-3 (3 m, 8 bands incl. red-edge, coastal blue, yellow, 2 NIR) and Jilin-1 (4 m, 4 bands: B,G,R,NIR), acquired June 2024 (single date, peak season); HS-fusion into one 11-band image + EN2N self-supervised denoising. 13 land-cover/vegetation classes digitized from field GPS + OSM, verified on high-res imagery. 64x64 patches; 80/20 train/val.

## Method
- **SSL pretraining**: ResNet-50 online encoder (first conv adapted to spectral depth C), projection head, momentum/target encoder with EMA m=0.99; two stochastic views of each patch; method-specific objectives — BYOL (cosine/predictive, no negatives), MoCo v3 (InfoNCE with negatives/queue), DINO (centering/sharpening self-distillation).
- **Downstream**: SSL-initialized ResNet-50 transferred to DeepLabV3+ semantic segmentation, fine-tuned with cross-entropy on labeled patches; sliding-window inference on full mosaics. Purely supervised DeepLabV3 baseline for comparison.

## Data & labels
- Labels: 13-class polygons from field GPS points + OSM; SSL pretraining label-free. Classes include open water, meadows, Elymus dahuricus and Pedicularis spp. (invasive/sparse and dense), developed surfaces, roads, asphalt, bare land.

## Results
- SSL representation quality (kNN/top-1 OA): MoCo v3 best on single sensors (PlanetScope-3 97%, Jilin-1 86%), **BYOL best on fused data (95% vs MoCo v3 96% on PS / DINO 87%)** — contradictory reporting across figures, but the stated pattern is: negative-sample contrastive (MoCo v3) wins on low-spectral-dimension/high-temporal-variability single sensors; non-contrastive predictive (BYOL) wins on redundant high-dimensional fused data.
- DeepLabV3+ segmentation OA / mIoU: Jilin-1 — BYOL 93%/64%, DINO 76%/56%, MoCo v3 72%/58%; PlanetScope-3 — BYOL 92%/63%, DINO 84%/65% (best mIoU), MoCo v3 86%/61%; fused — BYOL 88%/64%, MoCo v3 87%/63%, DINO 87%/57%.
- Fusion improves rare/fragmented class detection (invasive patches, wet meadows) and boundary sharpness; SSL-initialized backbones give sharper boundaries than supervised-only under limited ground truth.
- Method conclusions: MoCo v3 for single-sensor, BYOL for fusion (no collapse with channel redundancy); DINO unstable but preserves boundary quality.

## What transfers to our thesis
- Confirms the pattern that **SSL choice is data-dependent**: contrastive-with-negatives (MoCo v3) for spectrally limited inputs, non-contrastive predictive (BYOL) for redundant multi-sensor stacks — directly relevant to deciding between BYOL/DINO/MoCo-style objectives for our multi-product Landsat (optical + LST) stacks where channels are redundant/complementary.
- Multi-sensor fusion (11-band) "significantly improves detection of rare and fragmented vegetation patches and enables early identification of invasive species" — the ecological analogue of early stress detection; supports our optical+LST fusion premise (analogous bands: red-edge ~ NIR/SWIR + thermal).
- EN2N self-supervised denoising of fused imagery is a small extra SSL stage we can cite for label-free preprocessing of noisy multi-product composites.
- Caveat relevant to us: single-date (June 2024) imagery misses phenological dynamics — the authors themselves call for multi-temporal data; our thesis is precisely the multi-temporal extension.

## Limitations / caveats
- Single acquisition date (June 2024) — no phenology, no time series; weak for stress/anomaly which unfold temporally.
- Small ground-truth set; OA vs mIoU reporting is internally inconsistent across sections/figures (e.g., fused BYOL 88% OA in Table 1 vs "95%" in text) — treat numbers cautiously.
- No Landsat/moderate-resolution testing; DeepLabV3+ with ResNet-50 is heavy (~25 M params) — not lightweight; 13 classes generic land cover, stress not addressed.
- Fusion = simple band stacking + denoising, not learned fusion; no SAR/thermal.

## Key numbers to quote in lit review
- SSL pretraining + fine-tuning beats supervised-only DeepLabV3 under scarce labels (e.g., 93% OA / 64% mIoU on Jilin-1).
- SSL objective choice is dataset-dependent: MoCo v3 (InfoNCE) best on single-sensor imagery, BYOL (negative-free) best on 11-band fused imagery.
- Multi-sensor fusion (PlanetScope-3 8-band + Jilin-1 4-band) improves detection of rare, fragmented, spectrally similar vegetation classes including invasive species.
- Authors explicitly note single-date imagery limits phenology-based detection — motivating multi-temporal (time-series) approaches.



---


## FILE: 2025 - STCLN - Spatiotemporal Masked Pre-training for Crop Mapping (Int J Applied Earth Obs Geoinformation).md
# STCLN: Spatiotemporal Masked Pre-training for Crop Mapping

- **Full citation**: Qin, X., Guo, H., Su, X., Zhao, Z., Wang, D., Zhang, L. (2025). Spatiotemporal masked pre-training for advancing crop mapping on satellite image time series with limited labels. *International Journal of Applied Earth Observation and Geoinformation*, 137, 104426. https://doi.org/10.1016/j.jag.2025.104426
- **Problem & setting**: Crop type mapping from SITS with very few labels. Sentinel-2 imagery (10 bands, 10 m, ~38–61 observations over Sept 2018–Nov 2019) on PASTIS (France, 4 tiles, ~4000 km², 18 classes) and MTLCC (Munich, Germany, 2016, 13 bands, T=30, 17 classes). Evaluation under label-scarce regimes (1–5% of training samples).
- **Method**: SpatioTemporal Collaborative Learning Network (STCLN): a CNN spatial encoder (two DoubleConv 3x3 layers, 32→256 filters, applied per timestep) followed by a 3-layer, 8-head Transformer temporal encoder (d_model=256, GN + positional encoding), plus a SpatioTemporal Attention (STA) module that computes a pixel-to-pixel attention map from projected spatial/temporal features and reintegrates temporally pooled features via residual connection. SSL pretext: random pixel-level **spatiotemporal masking** — 40% of pixels replaced with a learnable mask token (excluding cloud regions), whole SITS reconstructed by a linear decoder; MSE loss computed only on masked pixels. Fine-tuning with cross-entropy.
- **Data & labels**: Pre-training: 7936 unlabeled PASTIS patches (32x32) / 3872 MTLCC patches (48x48). Fine-tuning with only 152 PASTIS / 78 MTLCC labeled patches (~2% of one fold); pixel-level crop labels from French LPIS and Bavarian StMELF.
- **Results**: PASTIS: STCLN_wp OA 0.8170, mIoU 0.4843, mF1 0.6059 — beats SITS-Former (mIoU 0.4548) by +6.49% mIoU; pre-training alone gives +2.34% OA over scratch. MTLCC: OA 0.9086, mIoU 0.6953, beats SITS-Former by +4.04% mIoU. Ablations: spatiotemporal masking (+9.0% mIoU) clearly beats temporal-only masking (+3.7%); STA + pretraining combined = +10.2% mIoU. Mask-ratio sweep (0.15–0.8) found 0.4 optimal. With only 1% labels, pre-training gives +7.5–17.1% mIoU over scratch; gain shrinks to ~5% mIoU at 5% labels.
- **What transfers to our thesis**: (1) Direct evidence that masking strategy matters — masking random *pixels* across both space and time trains the spatial encoder too, unlike temporal-only masking (SITS-Former/UTAE-style); relevant to our Landsat 16-day field-cube masking design. (2) Mask ratio ~0.4 optimal for SITS reconstruction, between SITS-Former's 0.15 and U-BARN's 0.6 — a starting point for our masked pretraining on sugarcane time series. (3) Pre-training gains are largest exactly in the label-scarce regime we target (+7.5–17.1% mIoU at 1% labels), supporting label-free pre-training + minimal fine-tuning for cross-year transfer. (4) Excluding cloud-contaminated pixels from mask positions improved temporal feature quality — applicable to Landsat cloud/shadow handling. (5) Their STA attention couples spatial and temporal encoders; a design option if we use patch (not pixel-set) inputs.
- **Limitations / caveats**: Sentinel-2 only (10 m, denser revisits than Landsat 16-day); pre-training is regional — authors themselves flag weak cross-area generalization; some phenologically similar classes still fail (winter triticale, mixed cereal IoU <0.11); supervised fine-tuning still required (not label-free); STA adds parameters and complicates optimization; classification (crop type), not stress/anomaly detection.
- **Key numbers to quote in lit review**:
  - Spatiotemporal masking beats temporal-only masking by +5.3% mIoU (9.0% vs 3.7% gain) in SITS pre-training ablations.
  - STCLN_wp: +6.49% mIoU over prior SOTA on PASTIS and +4.04% on MTLCC with only ~2% of labels.
  - Optimal SITS mask ratio 0.4 (masked reconstruction, learnable mask token).
  - At 1% labeled samples, SSL pre-training yields +7.5–17.1% mIoU over training from scratch.



---


## FILE: 2025 Abdelrahim et al. - SAED-ViT - Self-Supervised Seasonal Anomaly Embedding ViT for Label-Free Drought (Earth and Space Science).md
# SAED-ViT: Self-Supervised Seasonal Anomaly Embedding ViT for Label-Free Drought Mapping

- **Full citation**: Abdelrahim, N. A. M., Jin, S., & Li, S. (2025). A self-supervised seasonal anomaly embedding ViT for label-free drought mapping in the Horn of Africa. *Earth and Space Science*, 12, e2025EA004716. https://doi.org/10.1029/2025EA004716
- **Problem & setting**: Fully label-free drought severity classification/mapping in the Horn of Africa (Eritrea, Ethiopia, Somalia, Djibouti; ~1.88M km², 2.1°S–17.55°N), where ground truth and station data are nearly absent. Monthly satellite stacks Jan 2000–Dec 2024 (300 months) at 0.05° (~5.5 km): MODIS NDVI (MOD13Q1, 250 m 16-day → monthly), MODIS LST (MOD11A2, 1 km 8-day → monthly), CHIRPS precipitation (0.05° monthly).
- **Method**: Pipeline: (1) per-pixel Z-score anomalies computed per calendar month against 25-year climatology; (2) grouped into 3 agricultural seasons (MAM, JJA, OND) → 75 seasonal composites (25 yr x 3 seasons), each a 3-band stack (NDVI, LST, precip anomalies); (3) MAE-ViT self-supervised pre-training: split into non-overlapping 4x4-pixel patches (3x4x4 tensors), linear embedding, 75% patch masking, ViT encoder on the 25% visible tokens, lightweight decoder reconstructs masked patches; MSE reconstruction loss on masked patches only; (4) freeze encoder, extract 128-d embeddings for every patch; (5) K-Means (k=6) clustering in latent space; clusters empirically mapped to Extreme/Severe/Moderate/Mild/Normal/Wet by their mean anomaly signatures — no thresholds, no labels. Cluster quality: silhouette ≈ 0.59, Calinski–Harabasz ≈ 0.59.
- **Data & labels**: Zero drought labels used anywhere in training or class assignment. Only external reference: SPEI-3 computed from CHIRPS + ERA5-Land PET (FAO Penman-Monteith) for independent validation; secondary comparison to NDVI, VCI/TCI, VHI.
- **Results**: Model drought severity correlates strongly with SPEI (Pearson r = −0.909, p < 0.01); known drought years 2011, 2017, 2022 (and 2009–2011, 2015–2016, 2020–2022 build-ups) emerge as spikes in Extreme/Severe cluster frequency. Outperforms NDVI, TCI, VHI on temporal tracking of onset/recovery and on ROC/AUC for drought-event identification; better spatial discrimination (e.g., adjacent Wet vs Extreme zones along ecotones) than coarse indices. Cluster signatures are physically coherent: Extreme cluster has mean anomalies NDVI −0.61, LST +0.63, precip −0.60. Best classification consistency in JJA/SON; MAM weaker (smaller anomaly amplitude).
- **What transfers to our thesis**: (1) Closest methodological template for our label-free sugarcane water/salinity stress detection: seasonal Z-score anomalies of optical (NDVI) + LST + rainfall → SSL (MAE) → unsupervised clustering → interpretable stress classes without any labels or fixed thresholds. (2) Confirms the optical+LST combination we plan: LST anomaly carries evapotranspiration/thermal stress signal that vegetation indices alone miss (VHI/TCI lag behind the learned model). (3) The "cluster-then-label-by-mean-anomaly-signature" recipe is directly reusable for defining sugarcane stress regimes from Landsat 16-day series, with CWSI/ETa statistics used to name clusters instead of SPEI. (4) Anomaly (departure-from-climatological-norm) input representation, not absolute values — supports our cross-year design, since anomalies generalize across years better than absolute reflectance. (5) Uncertainty maps from intra-cluster variability offer a simple confidence product for in-field advisory.
- **Limitations / caveats**: Coarse 0.05° (~5.5 km) resolution — far above field scale; 4x4-pixel fixed patches miss hyper-local signals; validation is proxy-based (SPEI correlation), not against measured crop stress/yield; monthly temporal aggregation discards within-season dynamics (16-day Landsat rhythm would be richer); class ordering into severity levels done manually after clustering; cluster mapping not calibrated per crop type (mixed land cover).
- **Key numbers to quote in lit review**:
  - Label-free MAE-ViT + K-Means drought classification reaches r = −0.909 (p<0.01) against SPEI with no drought labels or thresholds.
  - 75% patch-masking MAE pre-training on 25 years of NDVI+LST+precipitation anomalies (2000–2024).
  - Outperforms NDVI, TCI, VHI in drought onset/recovery timing and ROC-AUC.
  - Extreme-drought cluster identified by mean anomalies NDVI −0.61, LST +0.63, precipitation −0.60 (physically interpretable unsupervised classes).



---


## FILE: 2025 Abu Zaid et al. - Uniformly Scaling Flows - Density-Aligned Deep One-Class Classification (arXiv).md
# On Uniformly Scaling Flows: A Density-Aligned Approach to Deep One-Class Classification

## Full citation
Abu Zaid, F., Katzke, T., Müller, E., & Neider, D. (2025). "On Uniformly Scaling Flows: A Density-Aligned Approach to Deep One-Class Classification." arXiv:2510.09452v1 [cs.LG] (TU Dortmund, RC Trustworthy Data Science). Code basis: github.com/aai-institute/USFlows.

## Problem & setting
- Theory + practice for unsupervised anomaly detection: bridges Deep SVDD (one-class, compact hypersphere of normality, collapse-prone) and normalizing flows (exact likelihoods, but scores confounded by input-dependent log-Jacobian terms). Industrial AD benchmarks: MVTec AD and VisA (15 and 12 object classes), image-level and pixel-level AUC-ROC.

## Method
- **Uniformly Scaling Flow (USF)**: normalizing flow with constant Jacobian determinant, det J_phi(x) = kappa for all x. Built from masked **additive coupling layers** (volume preserving) + bijective affine transforms parameterized by LU-decomposed matrices (determinants cancel between adjoint blocks), via USFlows library; non-US counterpart differs only by affine coupling.
- **Core theorem**: training a USF by MLE with base N(c, 1/2 I) reduces exactly to a Deep SVDD one-class objective min E||phi(x)-c||^2 with a unique weight regularizer -ln psi_det(w) that penalizes volume collapse — inheriting both flow density faithfulness and one-class distance reasoning. Consequence: latent norm ||phi(x)-c|| is a provably faithful anomaly score (density monotonicity, p_X(x)<p_X(y) iff ||phi(x)||>||phi(y)||), which non-US flows and Deep SVDD violate (Proposition 1 shows Deep SVDD admits density-inverting minimizers).
- **Determinant regularization**: Bayesian log-normal prior on |det J| (per LU diagonal) prevents exploding determinants; MAP estimation.
- **VAE-USFlow hybrid**: USF as learnable VAE prior (latent z ~ phi^-1(N(0,I))) for explicit dimensionality reduction, combined with reconstruction score; Wide-ResNet50 encoder, transposed-conv decoder.
- **Drop-in experiments**: replace affine coupling with additive coupling inside FastFlow (ResNet-18 features), CFlow (Wide ResNet-50-2 + positional conditioning), U-Flow (MS-CaiT multi-scale); Anomalib v2.0, ImageNet-frozen backbones, 100 epochs, 3 seeds, no per-class tuning.

## Data & labels
- Unsupervised: trained only on normal samples (MVTec/VisA train splits); labels used only for AUC-ROC evaluation.

## Results
- Drop-in USF substitution: never hurts means, greatly reduces variance (often to ~±0.0-1.1). MVTec AD image AUC: CFlow 72.5±12.8 -> 90.8±1.1 (+18.3, near-eliminates training failures); U-Flow 92.7±4.6 -> 94.5±0.6; FastFlow 91.3 -> 91.0 (unchanged, more stable). MVTec pixel: 95.4-95.9 -> 96.6-97.0. VisA image: CFlow 82.5±8.3 -> 88.4±0.9; pixel FastFlow 96.3±0.7 -> 98.8±0.0.
- Toy experiments (Gaussian mixtures, d=2..128): only USFs keep monotonic likelihood-vs-latent-norm alignment up to 128 dims (Spearman rho/Kendall tau); non-US flows collapse at 128 dims with numerical instability; Deep SVDD latents inhomogeneous.
- VAE-USFlow proof of concept on MVTec: mean image AUC 81.54 (median 82.52, 0 failed runs) vs VAE-NonUSFlow 58.11 (53.68, 11 failed runs of 45).

## What transfers to our thesis
- Provides a principled **density-based anomaly detection option for label-free crop stress detection**: a flow (or USF) fitted on normal field embeddings (e.g., from an SSL encoder over Landsat 16-day series) yields exact likelihood-based stress scores with the theoretical guarantee that the latent norm alone ranks anomalies — simpler scoring than reconstruction error and immune to hypersphere collapse.
- The collapse analysis justifies design choices in our one-class baselines: Deep SVDD needs fixed non-zero center, no biases, unbounded activations, and benefits from USF-style regularization; latent-norm scoring is valid only for uniform-Jacobian transforms — a concrete recommendation if we try flow heads on top of Presto/SSL embeddings.
- Strong empirical message: **variance/stability gains** from USF substitution (std 12.8 -> 1.1) matter for cross-year deployment where retraining per year is required — a stable detector is more important than +1 AUC when models must transfer across seasons/regions without re-tuning thresholds.
- CFlow's positional conditioning idea (condition density on spatial index) is adaptable: condition on day-of-year/phenology stage so "normal density" is season-aware — relevant for 16-day seasonal stress baselines.

## Limitations / caveats
- Industrial images (MVTec/VisA) only — no remote sensing, no time series, no multispectral data; normal-only training assumed (agricultural archives contain anomalies).
- Flows are more expensive than plain encoders; hybrid VAE-USFlow still far from specialized detectors (81.5 vs ~99 AUC for FastFlow/CFlow+USF).
- USF requires equal input/latent dimensionality (diffeomorphism), so dimensionality reduction needs the VAE hybrid, which is the weakest variant.

## Key numbers to quote in lit review
- MLE training of a uniformly scaling flow is mathematically equivalent to Deep SVDD with a determinant regularizer — unifying one-class classification and density estimation.
- Drop-in USF substitution: CFlow MVTec image AUC 72.5±12.8 -> 90.8±1.1; VisA pixel FastFlow 96.3±0.7 -> 98.8±0.0; means never regress and variance collapses across 12 configurations.
- Only USFs preserve monotonic likelihood-latent-norm alignment up to 128 dimensions; non-US flows numerically fail there.
- VAE-USFlow 81.5 mean AUC with 0/45 failed runs vs 58.1 with 11 failed runs for the non-USF prior.



---


## FILE: 2025 Ahmad - EigenCL - Temporal VI Unsupervised Crop Stress Detection via Eigenvector-Guided Contrastive Learning (arXiv).md
# EigenCL: Temporal Vegetation Index-Based Unsupervised Crop Stress Detection via Eigenvector-Guided Contrastive Learning

## Full citation
Ahmad, S. (2025). "Temporal Vegetation Index-Based Unsupervised Crop Stress Detection via Eigenvector-Guided Contrastive Learning (EigenCL)." arXiv preprint (independent/industry author, Brandt Group Canada). Note: preprint, not peer-reviewed venue; some cited works appear unverifiable — treat as gray literature.

## Problem & setting
- Label-free early drought-stress detection in corn from Sentinel-2 NDRE time series; goal: embeddings that cluster by physiological stress trajectory (not visual appearance), detecting stress before conventional NDRE thresholds trigger.
- Data: ~10,000 Sentinel-2 NDRE patches (100x100 px, 10 m) from drought-affected Iowa cornfields 2020, five cloud-free dates July 1-30 Aug (~15-day spacing); validation on 2,000 patches from Nebraska 2023 (milder drought), no fine-tuning, no retraining.

## Method
- **Per-patch NDRE time series**: mean NDRE over 5 dates -> 5-D vector; no normalization (preserve absolute chlorophyll differences).
- **Biological supervision signal**: RBF similarity matrix S_ij = exp(-gamma ||x_i - x_j||^2) over all patch time series; **principal eigenvector** (explains 76% of variance, r = 0.95 with raw NDRE) gives each patch a scalar stress-severity weight w_i — this replaces visual augmentations and cosine similarity as the positive/negative criterion.
- **Encoder**: ResNet-50 on NDRE rasters -> 2048-D embedding -> FC+BN+LeakyReLU projection head, L2-normalized.
- **EigenCL loss**: biological similarity S_ij = exp(-|w_i - w_j|/sigma), sigma=0.1 (final config sigma=0.5). Pull loss L_pull = sum S_ij * log(1 + (1-sim(z_i,z_j))/tau), tau=0.075; push loss L_push = sum lambda*(1-S_ij)*max(0, sim(z_i,z_j) - m), lambda=4.0, margin m=0.2; total normalized by N(N-1), batch 256. Hyperparameters grid-searched on Silhouette/DBI/CHI + NDRE-gradient stability.
- Key property: patches with similar stress trajectories cluster together regardless of visual appearance; visually similar patches with divergent NDRE dynamics separate.

## Data & labels
- Fully unsupervised training; NDRE-threshold stress stages (healthy >= 0.559, mild 0.479-0.559, moderate 0.322-0.479, severe < 0.322; detection threshold 0.40 from literature) used only for evaluating cluster agreement and early-detection lead time.

## Results
- Clustering (Iowa): EigenCL Silhouette 0.748, DBI 0.350, CHI 49,624 vs ablation w/o eigenvector (0.533/0.618/33,446), K-Means on NDRE (0.465/0.958/19,305), SimCLR (0.416/0.724/2,252), ProtoCLR (0.348/0.892/9,995). ARI between EigenCL clusters and NDRE stress stages 0.719 (95% CI 0.704-0.733).
- Clustering (Nebraska 2023, zero-shot): Silhouette 0.795, DBI 0.164, CHI 41,260 — generalizes across region/year with frozen model and Iowa thresholds; ~10-day lead time retained.
- Downstream (frozen embeddings, 70/30): k-NN 89.1% acc / F1 0.87; logistic regression 85.2% / F1 0.82 (abstract reports 95% k-NN — inconsistent with table; table is 89.1%).
- Early detection: stress flagged before the 0.40 NDRE threshold in **76% of cases, average lead 11.8 days (up to 12 days)**.
- Statistics: ANOVA across clusters F=37,950, p<0.0001; all Tukey pairwise NDRE differences significant.
- Ablation: replacing principal eigenvector with lower-variance components drops clustering and classification performance — the dominant stress-trajectory component is the necessary supervision.

## What transfers to our thesis
- **Closest methodological sibling in this batch** for our label-free sugarcane stress objective: guide contrastive learning with a physiologically meaningful scalar (here, an NDRE-trajectory eigenvector weight) instead of visual augmentation. For our case: derive the guide from ETa/CWSI or LST-derived stress proxies (physics-informed signal) and contrast Landsat field-patch embeddings by stress-trajectory similarity — directly addressing salinity/water stress where visual similarity is misleading.
- Demonstrates the failure mode we should cite: SimCLR with generic augmentations collapses on spectral-temporal agricultural data (Silhouette 0.416) — supports domain-aware SSL design in the thesis.
- Five-date 15-day-spaced VI series on Sentinel-2 transfers structurally to Landsat 16-day composites; the eigen-decomposition-of-trajectory-similarity trick is cheap and sensor-agnostic (works with NDVI/NDWI/LST trajectories).
- Zero-shot transfer Iowa 2020 -> Nebraska 2023 (different year, region, drought intensity) is exactly the cross-year evidence our thesis needs to replicate for sugarcane.
- Early-warning framing: lead time over index thresholds (11.8 days) is a strong headline metric we can adopt for ETa/CWSI-based early stress detection.

## Limitations / caveats
- Preprint quality concerns: single author, industry affiliation; citation list contains questionable entries; abstract's "95% k-NN" contradicts the results table (89.1%); hyperparameter sigma reported as 0.1 and 0.5 in different sections.
- "Stress labels" are NDRE-threshold proxies, not ground-truth physiological measurements — evaluation is circular (guide signal = evaluation signal, r=0.95 by construction).
- Only NDRE (no thermal/ETa), only corn, only 5 dates; needs red-edge band (Landsat lacks it — would need NDVI/SWIR substitutes).
- ResNet-50 on raster patches, not time-series-native architecture; no comparison to state-of-the-art SSL (MAE/DINO); no field-level aggregation or yield validation.

## Key numbers to quote in lit review
- Eigenvector-guided contrastive learning on 5-date NDRE trajectories: Silhouette 0.748 vs SimCLR 0.416 and K-Means 0.465; ARI 0.719 vs literature NDRE stress stages.
- Early stress detection 11.8 days (up to 12) ahead of conventional NDRE thresholds in 76% of cases.
- Zero-shot transfer to a different region/year (Nebraska 2023) retains clustering quality (Silhouette 0.795, DBI 0.164) without retraining.
- Principal NDRE-trajectory eigenvector explains 76% of variance and correlates r=0.95 with raw NDRE — a cheap biological supervision signal.



---


## FILE: 2025 Chakravarty et al. - Out-of-Distribution Generalization in Climate-Aware Crop Yield Prediction, GNN-RNN vs MMST-ViT (ICCVW, arXiv).md
# Out-of-Distribution Generalization in Climate-Aware Crop Yield Prediction with Earth Observation Data

## Full citation
Chakravarty, A. (2025). "Out-of-Distribution Generalization in Climate-Aware Crop Yield Prediction with Earth Observation Data." ICCV 2025 Workshop on Sustainability with Earth Observation and AI, arXiv:2510.07350v1 (independent researcher).

## Problem & setting
- First large-scale OOD evaluation of deep crop-yield models: county-level corn and soybean yield prediction across the contiguous US under (i) leave-one-cluster-out (LCO/LORO) cross-region CV and (ii) year-ahead transfer (test on 2022, 3-to-1 train-test).
- Data: CropNet (Lin et al., KDD 2024) — Sentinel-2 at 40 m resampled, 14-day revisit, <=20% cloud, only 4 of 12 bands (AG + NDVI), 2017-2022, 2,291 counties (1,200 analyzed), aggregated to 9x9 km grids; county weather data; USDA Farm Resource Regions (7 clusters) as spatial OOD domains.

## Method
- Benchmarks two SOTA models:
  - **GNN-RNN** (Fan et al. 2022): CNN + LSTM over multi-year county weather sequences with graph message passing among counties; tuned n_layers=4, dropout=0, agg=mean/pool.
  - **MMST-ViT** (Lin et al. 2023): multi-modal spatial-temporal vision transformer with attention over fused weather + satellite inputs; tuned e=128, drop=0.
- OOD difficulty levels defined from cluster similarity (Table 1): Case 1 Easy, Case 2 Medium, Case 3 Hard; metrics RMSE (bu/acre), R2, correlation; same-region year-ahead as reference.

## Data & labels
- Fully supervised (USDA county yields); no SSL. CropNet public (HuggingFace CropNet/CropNet).

## Results
- **GNN-RNN consistently beats MMST-ViT cross-region** for both crops. Soybean cross-region RMSEs: HL->MSP 8.88, NGP->HL 8.04 (best); Prairie Gateway (PG) worst in all directions (e.g., PG->EU 21.42). Corn: PG->EU 48.36.
- Year-ahead (diagonal): soybean GNN-RNN best RMSE 5.46 (EU) / 6.15 (HL) / 7.11 (NGP); corn 21.65-26.69 in stable regions.
- OOD gaps (diff-region vs same-region year-ahead): MMST-ViT gaps 1.2-18.7% (stable but less accurate); GNN-RNN gaps up to 58.5% (more accurate but more sensitive to shift). Case 3 (hard): soybean GNN-RNN 11.11 vs 7.11 same-region (56.2% gap); corn 32.07 vs 21.65 (48.1%).
- Stable regions under shift: Eastern Uplands, Heartland, Northern Great Plains; corn NGP R2~0.45 with MMST-ViT (e=128, drop 0.5); several LORO settings give negative R2/correlation for MMST-ViT.
- **Efficiency: GNN-RNN 14 min total training vs MMST-ViT 31.5 h (23 h pretrain + 8.5 h finetune) — ~135x speedup on one RTX 4090.**
- PG hardest to predict: semi-arid, unmodeled irrigation, internal heterogeneity, sparse labels, and omitted red-edge/SWIR bands that carry stress signal.

## What transfers to our thesis
- **Protocol to adopt**: leave-one-region-out and year-ahead (train past, test next season) splits are exactly the cross-year/cross-region evaluation our sugarcane model needs; the paper's "performance gap %" between same-region and shifted test is a clean metric to report.
- Warning for our model choice: large multimodal ViTs (MMST-ViT) "rely on regional memorization" and collapse OOD, while the simpler recurrent+graph model generalizes better and is 135x cheaper — supports the thesis claim that lightweight models are more transferable across years/regions for in-field products.
- Omitted red-edge and SWIR bands degrade stress-sensitive prediction (PG failure partly attributed to this) — for Landsat, advocate including SWIR1/SWIR2 + thermal since red-edge is unavailable.
- Identifies that temperature anomalies (not precipitation) drive yield variability (citing Iizumi & Sakai 2020) — supports LST/thermal-driven stress indices (CWSI) in our feature set.
- Equity framing: models underperform in irrigated semi-arid zones — directly relevant to our salinity/irrigated sugarcane context; region-aware normalization and domain-adversarial methods suggested as remedies we can cite.

## Limitations / caveats
- Single author, short workshop paper; only two models, no SSL or process-based baselines (DSSAT/APSIM acknowledged as missing); no domain adaptation techniques actually tested.
- CropNet restrictions: 4 bands, L1C uncorrected reflectance, 9 km aggregation erases field-level variability, uneven county grid coverage (5-130+ grids) biases learning.
- Yield is annual — no within-season stress dynamics; supervised labels required.

## Key numbers to quote in lit review
- First large-scale OOD benchmark of crop-yield DL: GNN-RNN beats MMST-ViT cross-region and is ~135x faster (14 min vs 31.5 h on RTX 4090).
- MMST-ViT performs well in-domain but fails under regional shift (negative R2 in several leave-one-region-out settings) — model complexity does not buy generalization.
- OOD performance gaps reach 48-58% in structurally distinct regions (Prairie Gateway) for both models.
- PG failure partly due to missing red-edge/SWIR stress bands — argument for SWIR+thermal inputs in Landsat stress detection.



---


## FILE: 2025 Choi et al. - Multimodal Data Fusion + XAI for Water Stress Classification in Sweet Potato, CWSI Grad-CAM (Frontiers Plant Science).md
# Application of Multimodal Data Fusion and Explainable AI for Classifying Water Stress in Sweet Potatoes

## Full citation
Choi, J.W., Cho, S.B., Hidayat, M.S., Hwang, W.-H., Cho, Y.-S., Lee, H., Cho, B.-K., & Kim, G. (2025). "Application of multimodal data fusion and explainable AI for classifying water stress in sweet potatoes." Frontiers in Plant Science 16:1681915. DOI: 10.3389/fpls.2025.1681915 (Gyeongsang National University et al., Korea).

## Problem & setting
- Water-stress level classification of field-grown sweet potato (cv. Jinyulmi) using low-altitude RGB + thermal (TRI) imagery and growth indicators; two 320 m2 plots, May-Sep 2024; five VWC-based stress classes (Severe Dry <=10%, Dry 20±2%, Optimal 30±3%, Wet 40±3%, Severe Wet 50% volumetric water content), subsurface drip irrigation, TDR soil moisture at 20 cm.
- Aim: practical, low-cost, interpretable water monitoring without specialized hyperspectral/UAV equipment.

## Method
- **ML branch**: features per growth stage (June early, July tuber bulking, August late): leaf temperature (FLIR A65 640x512, emissivity 0.9, ~1.05 m height, 6-7 a.m., mean of 3 manually-selected leaf regions), modified CWSI, stem length, NDVI, SPAD, chlorophyll fluorescence. RF-based feature importance selects top-4 per stage (e.g., July: CWSI 0.271, leaf temp 0.161, SPAD 0.172, NDVI 0.152); classifiers LR/RF/KNN/MLP/SVM on 300 samples (50/stage, O doubled 1:1:2:1:1), 80/20 split + 5-fold stratified CV.
- **Modified CWSI** (key contribution): replaces unmeasurable T_wet/T_dry with field-observable variables — correction coefficient d = 2 + 0.1*|soil moisture - 30| + 2*(1 - RH/100), capped at 6; T_wet = T_a - d; T_dry fixed at 34 degC (max observed); CWSI = (T_c - T_wet)/(T_dry - T_wet), clipped to [0.05, 1].
- **DL branch**: CNN+ViT (~220k trainable params; fused system ~30.5 M incl. GUI) — separate CNNs for RGB (128x128, color-calibrated) and thermal (grayscale), thermal channels filtered by mean activation >0.1, GAP + channel-concat fusion, Transformer block, 3-class output. 904 images (452 thermal + 452 RGB), Adam 1e-3, batch 64, up to 100 epochs, early stopping patience 10, 5-fold CV.
- **Deployment**: Tkinter GUI ("sweet potato water monitor system") — averages KNN + CNN-ViT predictions, shows Grad-CAM attention maps for RGB and thermal separately, ~30.5 M params, near real-time on CPU.

## Data & labels
- Labels: irrigation-treatment VWC classes (SD/D/O/W/SW); 2,374 leaf-temperature observations (after +/-3-sigma outlier removal from 2,399); ANOVA leaf temp across classes F=2.376 (text) / 12.57 (table), p<0.05.

## Results
- ML: KNN best at all stages — June test acc 1.0 (CV 0.94), July 1.0 (CV 0.96), August 1.0 (CV 0.94); RF/LR/SVM ~0.84 in June/Aug; misclassifications concentrated at adjacent/mid classes (O confused with W or SD).
- DL: 5-class CNN+ViT accuracy only 0.75 (loss 0.7); merging to 3 classes (Severe Dry, Optimal, Severe Wet) raises accuracy to 0.92 (0.97 in confusion matrix: SD 100%, SW 100%, O 97%), 5-fold CV 0.91.
- Grad-CAM visualizations localize stress-relevant canopy regions per modality; GUI merges both models for decision support (irrigate/maintain/reduce).

## What transfers to our thesis
- **CWSI is the thermal anchor of our thesis** — this paper shows the CWSI's main practical bottleneck (needing T_wet/T_dry) can be circumvented by redefining it with field-observable/measurable variables. For Landsat: LST + air temperature reanalysis + soil moisture/precipitation products can define an analogous CWSI proxy without in-situ wet/dry reference — a concrete design for our ETa/CWSI multi-product input.
- Confirms **thermal signal alone separates extreme water stress classes perfectly (100% SD and SW)** but struggles with intermediate stress — supports our thesis framing of stress detection as early/anomaly detection (deviation from normal) rather than fine-grained multi-class staging.
- Supports **coarse class schemes** (3 levels: deficit/optimal/excess) as both more accurate and more actionable — matches operational irrigation decisions for sugarcane.
- Grad-CAM per-modality maps: template for the XAI component of our thesis (which bands/dates drive stress predictions); shows the GUI/deployment pattern for farmer-facing lightweight tools.
- Cites the sugarcane-relevant prior: de Melo et al. 2022 (Inception-ResNet-v2 on thermal images for sugarcane water deficit, +23/17/14% accuracy at AWC 25/50/100%) — useful related-work anchor.

## Limitations / caveats
- Small scale: one cultivar, one field, one season, ~300 tabular samples / 452 image pairs; near-perfect accuracies on tiny test sets (20% of 300) with doubled optimal class — overfitting risk; no external validation.
- Static single-date imagery; authors explicitly note no temporal stress accumulation modeling — the gap our 16-day time-series thesis fills.
- Ground-level 1.05 m thermal imaging, not satellite; leaf temp extraction is manual (3 hand-drawn ROIs); CWSI modification is ad hoc (fixed T_dry 34 degC, heuristic d formula) — not validated against standard Idso/Jackson CWSI or ETa.
- Supervised only; no SSL; label noise from VWC classes defined by irrigation treatment.

## Key numbers to quote in lit review
- Modified CWSI using field-observable variables (air temp, RH, soil moisture) enables CWSI computation without wet/dry reference surfaces.
- Thermal+RGB CNN-ViT: 5-class accuracy 0.75 vs 3-class 0.92 (CV 0.91); extreme classes classified with 100% accuracy, optimal 97%.
- KNN on growth indicators + CWSI + leaf temperature: CV accuracy 0.94-0.96 across growth stages; CWSI the most important feature at tuber bulking (importance 0.271) and late growth (0.265).
- 30.5M-parameter fused system runs near real-time on CPU with on-the-fly Grad-CAM — feasibility evidence for lightweight in-field deployment.



---


## FILE: 2025 Choudhury et al. - MIMRS - Survey on Masked Image Modeling in Remote Sensing (arXiv).md
# MIMRS: A Survey on Masked Image Modeling in Remote Sensing

## Full citation
Choudhury, S., Vasim, A., Schmitt, M., & Banerjee, B. (2025). "MIMRS: A Survey on Masked Image Modeling in Remote Sensing." arXiv:2504.03181v2 [cs.CV] (IIT Bombay / UniBw Munich). Short survey (IGARSS-style, 4 pages).

## Problem & setting
- ImageNet pretraining transfers poorly to RS (spatial resolution, spectral bands, densely packed small objects, aerial viewpoint); labels scarce and domain-specific. MIM positioned as the alternative to contrastive SSL that avoids the false "different images = different classes" assumption (multiple RS images contain the same class) and uses inherent image structure/redundancy.
- Motivating RS-specific pain points MIM addresses: cloud cover/occlusion/sensor limitations -> cloud removal, multimodal fusion, super-resolution.

## Method (taxonomy)
- **Generic MIM framework**: mask pixels/patches/latent features, reconstruct missing parts from visible context. Variants: BEiT (60% masking, dVAE token prediction), SimMIM (direct pixel prediction with visible+masked tokens in encoder), MAE (~75% random masking, encoder sees only visible patches, lightweight decoder, MSE loss on masked patches, decoder discarded after pretraining), CrossMAE (cross-attention between masked/visible tokens for efficiency).
- **RS-specific MIM (MIM-RS)** customizations catalogued: RVSA (rotational + variable-size window attention instead of global attention, MillionAID pretraining); RingMo (patch-based imperfect masking, 2M+ images); CMID (contrastive + MIM self-distillation for global semantics + local awareness); GFM (continual pretraining on GeoPile); SatMAE (temporal + multispectral position embeddings, fMoW); ScaleMAE (GSD-based positional encoding, high/low-frequency reconstruction); spectral-domain masking for MSI (SpectralGPT) and HSI (HyperSigma); multimodal MIM — msGFM (shared encoder + per-modality patch embed/decoder for RGB/MSI/SAR/DSM), MMEarth (12 modalities, multi-modal pretext tasks), SenPa-MAE (sensor-parameter-aware).
- Objectives formalized: InfoNCE (contrastive, eq. 1) vs MIM masked-reconstruction NLL (eq. 2) vs MAE MSE on masked patches (eq. 3).

## Data & labels
- Survey of pretraining corpora: MillionAID, fMoW, RingMo 2M+ images, GeoPile, SSL4EO-S12, Sen1/2 archives — all label-free pretraining; downstream labels for classification/detection/segmentation.

## Results (key comparative table, from SelectiveMAE paper)
- Scene classification AID (TR=50%/20%) & RESISC-45, detection DIOR/DIOR-R mAP50, segmentation LoveDA mIoU / SpaceNet mF1:
  - Contrastive: SeCo 95.99/92.91, GASSL 95.92/93.06, CaCo 95.05/91.94; segmentation LoveDA ~43.6-48.9 mIoU.
  - MAE-based: SatMAE (ViT-L 307M) 96.94/94.10; ScaleMAE 97.58/95.04, DIOR 73.81; RingMo (Swin-B 88M) DIOR 75.90; RVSA 98.50/95.69, DIOR-R 70.51, LoveDA 54.00; **SelectiveMAE (ViT-L 307M) best overall: AID 98.48/95.77, DIOR 77.80, DIOR-R 77.80, LoveDA 54.31, SpaceNet 79.46**.
- Pattern: MAE-based foundation models outperform contrastive baselines on detection/segmentation; RVSA/SelectiveMAE lead.

## What transfers to our thesis
- **The one-stop citation for the thesis's MIM background**: canonical MAE formulation, and the catalog of RS-specific modifications we can borrow — most relevant for Landsat 16-day time series: SatMAE-style temporal position embeddings, ScaleMAE's GSD-aware encodings (30 m vs 10 m products), SenPa-MAE's sensor-parameter awareness (Landsat-8 vs -9, LST resolution), and multimodal MIM (msGFM/MMEarth) as the blueprint for optical+LST masked reconstruction (mask thermal, reconstruct from optical — the cross-modal pretext directly serves our cloud-gap and multi-product story).
- The contrastive-vs-MIM distinction (contrastive's false inter-image class assumption breaks on RS) justifies our choice of masked reconstruction over SimCLR-style pretraining on field time series.
- Quantitative anchor: MAE-based models beat contrastive ones on dense prediction tasks (LoveDA mIoU 54.3 vs 43.6-48.9), while differences on scene classification are ~1-3 pp — informs expectations for our downstream stress segmentation.
- Future-direction quote: joint embedding-predictive architectures unifying generative reconstruction with discriminative alignment — frames our hybrid (reconstruction + contrastive/stress-guided) design.

## Limitations / caveats
- Very short survey (4 pages): no detailed method-by-method analysis, no agricultural/time-series focus, no Landsat-specific discussion, no numbers of its own (Table 1 imported from SelectiveMAE).
- MIM models are heavy (ViT-L ~307M params) — the survey does not address the lightweight deployment constraint central to our thesis; parameter efficiency absent.
- No treatment of reconstruction-error anomaly detection or cross-year temporal masking strategies.

## Key numbers to quote in lit review
- MIM (MAE) masks ~75% of patches and trains only on visible ones, with MSE loss restricted to masked patches — the foundation our masked Landsat time-series pretraining builds on.
- MAE-based RS models outperform contrastive baselines on dense tasks: SelectiveMAE LoveDA mIoU 54.31 vs SeCo 43.63 / GASSL 48.76.
- RS-specific MIM customizations: temporal/multispectral embeddings (SatMAE), GSD-based positional encoding (ScaleMAE), variable-size window attention (RVSA), sensor-parameter awareness (SenPa-MAE), multimodal cross-reconstruction (MMEarth, 12 modalities).
- Contrastive SSL's class-assumption flaw in RS (same-class images pushed apart) is a documented motivation for MIM in agricultural/EO settings.



---


## FILE: 2025 Dewis et al. - STSMamba - Spatial-Temporal-Spectral Mamba with Sparse Deformable Tokens for MODIS (arXiv).md
# STSMamba: Spatial-Temporal-Spectral Mamba with Sparse Deformable Token Sequence for Enhanced MODIS Time Series Classification

## Full citation
Dewis, Z.*, Xu, Z.*, Zhu, Y., Alkayid, M., Heffring, M., & Xu, L.L. (2025). "Spatial-Temporal-Spectral Mamba with Sparse Deformable Token Sequence for Enhanced MODIS Time Series Classification." arXiv:2508.02839v1 [eess.IV] (University of Calgary; NSERC-funded).

## Problem & setting
- Land-cover classification from MODIS MOD13Q1 time series (250 m, 16-day revisit, 23 timesteps/year, 6 bands: blue, red, NIR, MIR, NDVI, EVI) — same 16-day cadence as Landsat; challenges: high temporal dimensionality, mixed pixels, spatial-temporal-spectral coupling.
- Data: Saskatchewan 2010 (11 classes, 100 train/100 val/1000 test per class, 13x13 patches, homogeneous-pixel filtering with 5x5 filter); Alberta 2010 as unseen-province generalization test (10.6M pixels mapped); ground truth NRCan 30 m LCLU resampled to 250 m.

## Method
- **Temporal Grouped Stem (TGS)**: per-timestep 3x3 conv + BN + GELU (6 bands -> 18 features/timestep) to disentangle temporal-spectral coupling before sequencing.
- **Sparse Deformable Mamba Sequencing (SDMS)**: instead of feeding full rigid token sequences to a Mamba block, compute an attention matrix (learnable), take mean over rows, sort descending, keep top floor(lambda*T) tokens, run Mamba on the re-ordered sparse sequence, then scatter outputs back (residual connection) — sequence order is learnable ("deformable") and length sparse.
- **Three dedicated modules**: SDTM (temporal: 23 -> 6 tokens), SDSpeM (spectral: 18 -> 6 tokens), SDSpaM (spatial: HW -> 4 tokens, using arccos similarity to central pixel, sparsity ratio lambda=0.3). Reduces redundancy, correlation decay in long sequences, and compute.
- Training: batch 1024, 100 epochs, RTX A6000 Ada; supervised classification head.

## Data & labels
- Supervised; labels from NRCan map (only for training/eval). No SSL — but architecture directly applicable to SSL pretraining over 16-day multi-band cubes.

## Results
- Saskatchewan: STSMamba OA 97.59%, AA 96.01%, Kappa 96.76% — beats SSRN 96.28/96.51/93.91, ConvNeXt 95.64, ViT 95.26, SwinT 93.72, LSTM 92.51, MambaHSI 93.04. +3-8 pp over MambaHSI; +3.8/6.2/4.0 pp over SwinT.
- Alberta (spatial transfer, unseen province): STSMamba best again — outperforms MambaHSI by ~7.2 (OA), 12.4 (AA), 4.4 (Kappa) pp and SwinT by 7.0/8.4/21.1 pp; all methods drop vs in-domain as expected.
- Sparsity ablation: temporal sparsity ratio 0.3 best (preserves phenology while cutting redundancy); spectral sparsity better at 0.8 (spectral richness critical).
- Per-class: biggest gains on subtle classes — polar shrubland 93.73 (vs 84-92 baselines), cropland 97.96, wetland 98.12.

## What transfers to our thesis
- **Same temporal sampling as our target**: MOD13Q1 16-day/23-steps is structurally identical to Landsat 16-day composites (~23 scenes/year); the TGS per-timestep stem + separated temporal/spectral Mamba streams transfer directly to Landsat optical+LST stacks (treat LST as extra bands in the spectral stream).
- The **decoupling of spatial-temporal-spectral streams** is the paper's core insight: bands with opposite seasonality (NDVI summer peak vs red/NIR winter snow peak) get entangled in mixed sequences — for sugarcane, NDVI/NDWI (phenology) vs LST/CWSI (stress) seasonality similarly differ, so decoupled streams are preferable to a single mixed token stream.
- Sparse deformable sequencing (top-k attention-guided token selection) is a concrete mechanism for lightweight models: keep only the most informative timesteps (e.g., peak-season composites) — reduces compute for in-field deployment and mitigates correlation decay on multi-year series.
- Cross-province generalization protocol (train Saskatchewan -> test Alberta) mirrors our cross-year/cross-field evaluation design; sparse+deformable model showed the strongest transfer.
- Note: supervised only — our thesis would wrap this encoder in a masked-reconstruction or contrastive pretext.

## Limitations / caveats
- Supervised classification only (NRCan labels); no SSL pretext, no anomaly/stress task; no thermal band.
- 250 m MODIS (no Landsat 30 m test); ground truth resampled 30 m -> 250 m introduces label impurity despite filtering.
- Sparsity ratios hand-tuned; spatial module keeps only 4 tokens per patch — questionable for fine-grained within-field stress gradients; no code link stated; AA vs Kappa table consistency unclear.

## Key numbers to quote in lit review
- STSMamba: OA 97.59% / Kappa 96.76 on 23-step 16-day MODIS series, +3-8 pp over prior Mamba (MambaHSI) and +3.8 pp over Swin Transformer.
- Spatial generalization to an unseen province: best of 9 models (e.g., +7.0 pp OA over SwinT, +21.1 pp Kappa), showing disentangled SSM encoders transfer across regions.
- Optimal sparsity: temporal 0.3 (phenology preserved) vs spectral 0.8 (spectral richness matters) — guidance for timestep-subsampling in lightweight time-series models.
- Decoupled temporal/spectral/spatial Mamba streams outperform mixed long sequences when bands have opposing seasonal patterns.



---


## FILE: 2025 Dufourg et al. - On the Use of Graphs for Satellite Image Time Series (arXiv).md
# On the Use of Graphs for Satellite Image Time Series

## Full citation
Dufourg, C., Pelletier, C., May, S., & Lefevre, S. (2025). "On the use of Graphs for Satellite Image Time Series." IEEE Geoscience and Remote Sensing Magazine, DOI: 10.1109/MGRS.2025.3622200; arXiv:2505.16685v2 (Universite Bretagne Sud/IRISA, CNES, UiT). Code: github.com/corentin-dfg/graph4sits.

## Problem & setting
- Survey + methodology + two case studies on representing satellite image time series (SITS) as **spatio-temporal graphs** (extension of Object-Based Image Analysis): nodes = spatio-temporal objects (fields/regions), spatial edges (adjacency) + spatio-temporal edges (object states linked across dates). Positions graphs vs pixel-grid methods (CNN/ViT) and against DTDG/CTDG dynamic-graph formalisms.
- Case study 1: land-cover mapping on DynamicEarthNet (75 areas worldwide, Planet Fusion 3 m daily Jan 2018-Dec 2019, 24 monthly labeled dates, 7 classes). Case study 2: NDWI forecasting on SEN2DWATER (3,682 filtered Sentinel-2 64x64 sequences, 17 basins in Italy/Spain, ~2-month revisit, 6 input acquisitions -> predict next).

## Method
- **Graph construction pipeline**: (i) collect SITS considering resolution trade-offs; (ii) entity definition — objects from segmentation (SLIC, Felzenszwalb), land registers, or clustering of similar disconnected pixels; endurantist (object persists, properties evolve) vs perdurantist (3D spatio-temporal objects) paradigms; features = per-region spectral statistics (mean/std/min/max per band); (iii) edges: region adjacency (spatial) + footprint overlap between consecutive dates (spatio-temporal); optionally attributed/weighted edges.
- **Case 1**: Felzenszwalb segmentation per date; GNN encoders (4 layers, hidden 64; 2 spatial + 2 temporal aggregation layers) with GCN/GraphSAGE/GIN/GATv2/ResGatedGCN vs MLP (edge-free OBIA) vs pixel-based U-Net; CE loss, Adam 1e-4, 100 epochs.
- **Case 2**: GraphCast-style encoder-processor-decoder on a coarse SLIC superpixel mesh (256 superpixels); pixel time series + spatio-temporal positional embedding (sin lat, sin/cos lon, sin DOY) via MLPs into node features; residual prediction (predicts change from last state); Huber loss, Adam 1e-4; baselines LSTM, ConvLSTM, TDCNN-ConvLSTM, persistence, input-average.

## Data & labels
- Supervised (monthly pixel labels in case 1; next-image NDWI in case 2); authors note semi-supervised extension with the unlabeled daily acquisitions is possible. Basin-disjoint train/test split enforced in case 2 (85:15).

## Results
- **Case 1 (DynamicEarthNet)**: U-Net best (val mIoU 33.69, test OA 69.85); GraphSAGE best graph model (val mIoU 31.48, test OA 68.21) with 35x fewer params (27,782 vs 983,654) and 5x faster training (2.32 h vs 10.63 h); MLP 29.42 mIoU — spatio-temporal context adds ~2 pp mIoU over context-free OBIA; anisotropic aggregators (GATv2, ResGatedGCN) and sum-aggregation (GIN) underperform mean-aggregation (GraphSAGE). U-Net/SITS control (same batch regime) collapses to 9.25 mIoU, showing spatio-temporal modeling helps when data variety per batch is limited. Segmentation ceiling ~91-92% OA; object-based error is not the bottleneck. Preprocessing (graph building) = 98% of test time (34 s/SITS, CPU segmentation).
- **Case 2 (NDWI forecasting)**: graph-based model best RMSE 0.1097 and PSNR 26.42 vs TDCNN-ConvLSTM 0.1111/25.68, LSTM 0.1162, persistence 0.1332; graph model generalizes better to under-represented NDWI values and water/impervious targets; TDCNN-ConvLSTM better on vegetation; both fail on abrupt changes (harvest, drought) due to low temporal frequency. Superpixel count (1-4096) barely affects RMSE — regional analysis suffices. Input length ablation: 1-2 acquisitions worse than persistence; 6 (full year) best (RMSE 0.1097 vs 0.1200 at 5).

## What transfers to our thesis
- **Field-as-node graph representation for sugarcane**: parcel/field objects with per-date spectral statistics and adjacency + cross-date edges is a natural, lightweight alternative to pixel grids for 16-day Landsat series — reduces working units (memory/compute), supports farmer-facing field-level outputs, and lets an SSL encoder operate at field granularity.
- Case-study design lessons for our cross-year models: basin/field-disjoint splits (avoid leakage), full-year input windows (1-2 dates worse than persistence — a caution for short-window stress detection), and the residual-prediction trick (predict change from last state, as GraphCast) which maps to forecasting NDVI/ETa anomalies rather than absolute values.
- Honest negative results to cite: GNNs on SITS still trail pixel CNNs (U-Net) on segmentation; aggregator choice matters (mean > attention/gated); preprocessing (object extraction) dominates inference cost — supports the argument that pixel/time-series models remain the pragmatic choice for our Landsat pipeline unless field objects are pre-existing (as in our sugarcane case).
- Multi-year annual cycle argument: models need >=6 acquisitions (~1 year) to learn seasonality — justifies our multi-year Landsat input windows for normal-behavior learning.

## Limitations / caveats
- Graph case study 1 clearly loses to U-Net (mIoU 31.5 vs 33.7 val); graph construction is slow and hand-crafted; no SSL or label-free pipeline anywhere in the paper.
- Case 2 forecasting limited by ~2-month revisit and cloud filtering (3,682/5,264 sequences kept); abrupt changes unpredicted — analogous to our stress-onset problem.
- No thermal/ETa products; optical only; NDWI-specific conclusions may not transfer to vegetation indices.
- Survey sections are comprehensive but the empirical evidence rests on two small case studies.

## Key numbers to quote in lit review
- Spatio-temporal GNN (GraphSAGE) matches U-Net on land-cover mapping from daily Planet SITS with 35x fewer parameters and 5x faster training (OA 68.2% vs 69.9%), but U-Net still leads mIoU (33.7 vs 31.5).
- Spatio-temporal context improves over context-free object features by ~2 pp mIoU (GraphSAGE 31.48 vs MLP 29.42).
- GraphCast-style superpixel-mesh model achieves best NDWI forecasting (RMSE 0.1097, PSNR 26.42) beating ConvLSTM variants; needs >=6 acquisitions (~1 year) to beat even persistence.
- 98% of graph-model inference time is graph construction (object segmentation) — a practical scalability caveat for field-level graph pipelines.



---


## FILE: 2025 Faran et al. - Self-Supervised Transformers for Long-Term Prediction of Landsat NDVI Time Series (SCITEPRESS).md
# SST-LTP: Self-Supervised Transformers for Long-Term Prediction of Landsat NDVI Time Series

## Full citation
Faran, I., Netanyahu, N.S., Roitberg, E., & Shoshany, M. (2025). "Self-Supervised Transformers for Long-Term Prediction of Landsat NDVI Time Series." ICPRAM 2025 (SCITEPRESS), pages 542-552. DOI: 10.5220/0013381700003905 (Bar-Ilan University / Technion). Code: github.com/FaranIdo/SST-LTP.

## Problem & setting
- Multi-decade NDVI forecasting on Landsat (1984-2024, missions 5/7/8/9) in a heterogeneous Mediterranean-to-arid desert-fringe landscape in Israel (rainfall 450 -> 250 mm/yr); challenges: strong seasonality, long-term trends, droughts, fires, abrupt changes, cloud gaps.
- Study area: 53.94 x 37.35 km, 30 m/px, 1,798x1,245 pixels, 2,238,510 pixel time series; two annual seasonal composites (Winter Oct-Apr, Summer May-Sep) averaged from scenes with <20% cloud -> 2 values/pixel/year.

## Method
- **Self-supervised pretext = direct future-value prediction**: input sequence O = {(NDVI_i, year_i, season_i)} for one pixel; model predicts NDVI at a *specified* future time N+delta in a single forward pass (not autoregressive — avoids error accumulation and repeated inference of AR models). Trained on MSE loss against observed NDVI; no labels needed.
- **Architecture**: BERT-style Transformer — 3 encoder blocks, 8 heads, embedding dim 256, dropout 0.2; observation embedding = NDVI linear embedding + sinusoidal continuous temporal encoding of normalized time t' = (2(t-t_start)+s) / (2(t_end-t_start+1)) (year+season as continuous cyclic signal, sin/cos harmonics) + positional encoding; decoder = MaxPool over temporal dimension + dense -> scalar NDVI. 200 epochs, Adam 1e-4 with 10-epoch warmup + exponential decay.
- Evaluation across input lengths (2.5-20 years) and horizons (1-5 years); baselines SVM (RBF), 3-layer FCN, CNN-1D, 3-layer LSTM trained on the same 10-sample (5-year) sequences.

## Data & labels
- Fully label-free (self-supervised on the NDVI series itself); 80/10/10 pixel split; windowing extracts (N past + 1 target) sequences.

## Results
- Best configuration: 10-year input sequences give the largest gains; 15-20 years marginally lower L1; performance declines with horizon (best next-year).
- **Next-year prediction with 10-year inputs: SST-LTP MAE 0.0338, MSE 0.0027, R2 0.8337** vs LSTM 0.0363/0.0031/0.8088, FCN 0.0383/0.7953, CNN-1D 0.0391/0.7810, SVM 0.0456/0.7459.
- Key architectural advantage: target year/season given as input -> direct multi-year prediction in one inference call (baselines need iterative calls).
- Failure mode: struggles with unexpected outliers/abrupt events (sudden disturbances) — model captures trends and seasonality, not anomalies.
- Qualitatively tracks high-variability samples better than LSTM (which oversmooths) and CNN/FCN.

## What transfers to our thesis
- **The Landsat time-series SSL pretext that most closely matches our stress-detection pipeline**: a transformer trained to predict future NDVI on unlabeled multi-decadal Landsat data; deviations of observed from predicted NDVI (the model's own residuals, which the authors flag as "outliers it cannot predict") are exactly the anomaly/stress signal our thesis exploits — the paper's stated weakness is our design's mechanism.
- **Temporal embedding design transfers directly**: normalized continuous year+season encoding (t' with sin/cos harmonics) handles multi-year Landsat composites; for 16-day sugarcane series, replace season in {0,1} with DOY phase — the formula is given and reusable.
- Two-composites-per-year (winter/summer) cloud-filtering strategy (<20% cloud scenes averaged) is a simple Landsat compositing baseline we can improve on with 16-day composites.
- Supports the thesis's "normal-behavior model + anomaly score" framing with quantitative evidence that prediction-based SSL outperforms LSTM/CNN/SVM on long Landsat series.
- Non-autoregressive direct multi-horizon prediction avoids error accumulation — relevant for forecasting ETa/CWSI trajectories to anticipate stress.

## Limitations / caveats
- Single variable (NDVI only), single scene/region, pixel-wise (no spatial context — authors list spatial correlation as future work); seasonal (2/year) not 16-day resolution.
- Not evaluated on cross-region transfer; no downstream stress/anomaly task quantified (anomaly detection is future work); pixel split may leak spatial autocorrelation between train/test pixels.
- Transformer is small but no parameter/FLOP reporting; no comparison to modern forecasting SSL (Presto, PatchTST, iTransformer empirically — only cited).
- Mediterranean natural vegetation; sugarcane is managed perennial with different phenology and irrigation dynamics.

## Key numbers to quote in lit review
- Self-supervised Transformer on 40 years of Landsat NDVI (1984-2024): next-year prediction MAE 0.0338, R2 0.834 — beating LSTM (0.0363/0.809), CNN-1D, FCN and SVM.
- 10 years of history is the practical optimum for multi-decadal prediction; gains saturate beyond 10-15 years.
- Direct (non-autoregressive) prediction with year/season conditioning outperforms iterative multi-step inference and avoids error accumulation.
- The model cannot predict abrupt outliers — the documented failure mode that anomaly-based stress detection can invert into a detection signal.



---


## FILE: 2025 Feng et al. - TESSERA - Temporal Embeddings of Surface Spectra for Earth Representation and Analysis (arXiv).md
# TESSERA: Temporal Embeddings of Surface Spectra for Earth Representation and Analysis

- **Full citation**: Feng, Z., Atzberger, C., Jaffer, S., Knezevic, J., Sormunen, S., Young, R., Lisaius, M. C., Immitzer, M., Jackson, T., Ball, J., Coomes, D. A., Madhavapeddy, A., Blake, A., Keshav, S. (2025). TESSERA: Temporal Embeddings of Surface Spectra for Earth Representation and Analysis. arXiv:2506.20380v7 (University of Cambridge et al.).
- **Problem & setting**: Pixel-wise foundation model ("embeddings-as-data") for multi-modal (Sentinel-1 SAR + Sentinel-2 optical) EO time series that are irregular due to cloud/orbital sampling. Avoids compositing, which flattens phenology; avoids patch-based RSFMs that assume cloud-filtered inputs. Global coverage, 10 m, annual embeddings (2017–2024, 3012 MGRS tiles, ~800M d-pixels).
- **Method**: Per-pixel "d-pixel" representation (all channel values over time at one 10 m location, with validity mask). Dual-branch encoders (one per modality): linear band projection + learnable Day-of-Year positional encodings, sequence padded to L=40 valid observations (sampled with replacement if fewer), 4-layer Transformer encoder, GRU pooling to 128-d; S1 and S2 embeddings concatenated and fused by a 2-layer MLP into a 128-d embedding; int8 quantization-aware training (~4x storage saving, negligible loss). SSL objective: **Barlow Twins** — two augmented views per d-pixel created by independently random-sampling 40 valid time steps; loss = cross-correlation diagonal (invariance to temporal sampling) + off-diagonal redundancy reduction (lambda=5e-3), plus a mix-up regularization term (lambda_mix=1.0, Bandara et al.) enforcing linear embedding interpolation, plus global shuffling of d-pixels across tiles to break spatial autocorrelation. Encoder 30.2M params; frozen at inference, projector (16384-d) discarded.
- **Data & labels**: Pre-training fully label-free on ~800M d-pixels. Downstream: TreeSatAI-TS (tree species, Germany), PASTIS-R (parcel segmentation, France), Austrian Crop (classification + segmentation, INVEKOS parcel labels), Biomassters (AGB regression, Finland), Borneo Canopy Height (LiDAR-calibrated, Malaysia). Adaptation via only a 2-layer MLP (pixel classification) or lightweight UNet head on frozen embeddings; evaluated at 1%/30%/100% labels.
- **Results**: TreeSatAI-TS F1 77.96 (full labels) vs AlphaEarth 76.90; at 1% labels 60.58 vs AlphaEarth 52.79. Austrian Crop classification: F1 66.15 at 1% labels vs AlphaEarth 37.22 and Presto 32.74 (+33.4 over Presto); ~0.5 F1 with only 4 samples/class. Austrian Crop segmentation mIoU 53.12 (AlphaEarth 25.70, Presto 34.04). PASTIS-R mIoU 50.68 (AlphaEarth 51.08 best). Biomassters AGB RMSE 27.43 t/ha (best FM; task-specific Biomassters competition winner 25.90). Borneo canopy height RMSE 12.2 m (AlphaEarth 16.1, Presto 17.9). Ablations: removing global shuffling −9.2 F1, removing mixup −11.1 F1, both −14.7 F1; no-pretraining −33.5 F1; removing S1 branch −3.1 F1; encoder fine-tuning after pretraining gives no benefit; regional retraining gives negligible gains over the single global model; robust to clouds until <~20 valid S2 observations/year; L=40 sampled time steps is the accuracy–efficiency sweet spot.
- **What transfers to our thesis**: (1) Strongest argument in this batch for the "embeddings + lightweight head" paradigm: a 30M-param frozen encoder + small MLP/UNet matches or beats 100–700M-param fine-tuned RSFMs — directly supports our lightweight multi-product in-field models on modest hardware. (2) Temporal sampling invariance via Barlow Twins on irregular sparse time series is exactly the right pretext for Landsat 16-day + cloud gaps (only 5% loss from dropping S1 suggests optical temporal signal dominates; S1 optional). (3) DoY positional encoding + sampling-with-replacement padding handles irregular/gappy acquisitions better than fixed-length composites — directly applicable to our Landsat series. (4) Embeddings remain valid under shifted calendars, missing seasons, short seasonal windows (spring–autumn inference) — supports cross-year sugarcane models where season start varies. (5) Pixel-wise (not patch) pretraining keeps field-level flexibility; a spatial UNet head adds context downstream without complicating pretraining. (6) int8 embeddings viable for edge/in-field deployment (~25% of fp32 storage).
- **Limitations / caveats**: Sentinel-1/2 only — no thermal band (no LST/CWSI signal), so water-stress information must come from elsewhere or be fused; 10 m resolution; annual window default (multi-year context not modeled); pixel-wise pretraining discards spatial structure (needs a downstream spatial head for segmentation); trained on 16 AMD MI300X GPUs — pretraining itself is not reproducible at lab scale (but inference/embedding use is); global model may under-specialize for a single crop like sugarcane (their ablation: regional retraining gave negligible gains, but that was across diverse crops, not one stress-specific task).
- **Key numbers to quote in lit review**:
  - Barlow Twins temporal-sampling-invariant pixel SSL on 800M d-pixels; frozen 30.2M-param encoder beats fine-tuned 100M+ RSFMs on 6 benchmarks.
  - At 1% labels, TESSERA F1 66.15 vs Presto 32.74 and AlphaEarth 37.22 (Austrian Crop classification) — label efficiency is the headline.
  - Ablations: global shuffling + mixup regularization worth +14.7 F1; pretraining worth +33.5 F1.
  - Robust to cloudiness until <~20 valid observations/year; int8 quantization costs only ~0.6 F1 for 4x compression.
  - L=40 randomly sampled valid time steps per view (temporal sampling invariance objective).



---


## FILE: 2025 Garske et al. - SHAZAM - Self-Supervised Change Monitoring for Hazard Detection and Mapping, 473K params (arXiv).md
# SHAZAM: Self-Supervised Change Monitoring for Hazard Detection and Mapping

- **Full citation**: Garske, S., Heidler, K., Evans, B., Wong, K. C., Zhu, X. X. (2025). SHAZAM: Self-Supervised Change Monitoring for Hazard Detection and Mapping. arXiv:2503.00348v1 (submitted to IEEE; Univ. of Sydney / TUM).
- **Problem & setting**: Label-free continuous monitoring of a region of interest (ROI) for multiple hazard types — bushfires/burned areas, extreme out-of-season snowfall, deforestation, algal blooms, drought, floods — distinguishing genuine hazards from normal seasonal change with a single observation (no multi-observation confirmation lag). Sentinel-2 L2A, 10 spectral bands (10/20 m); ROIs at 30 m (SNP, Gran Chaco, Lake Copeton) and 10 m (Lismore); training periods of 2–3.5 years (56–186 images per ROI).
- **Method**: Seasonally Integrated UNet (SIU-Net), 473K parameters: a conditional UNet that translates a fixed "baseline" patch (median of training period, 32x32 px) to the expected image for any day of year, conditioned on cyclical day-of-year encodings (sin/cos of 2*pi*t/365) and patch row/col position encodings, concatenated as extra input channels and re-injected after each up-block; L1 (MAE) reconstruction loss; trained self-supervised on hazard-free training images only. Anomaly scoring: per-pixel SSIM (11x11 window) between generated expected image and actual observation, averaged per channel, inverted+clamped+squared into SDIM map (background suppression); image-wise SDIM score for detection. Seasonally adaptive threshold: two circular linear regressions fit on training-period anomaly scores (mean curve + 1.64 x monthly-SD curve = 95th percentile), no dataset-specific tuning.
- **Data & labels**: Four self-built Sentinel-2 datasets (Sequoia NP; Gran Chaco, South America; Lake Copeton, NSW Australia; Lismore, NSW Australia; 1024x1024/512x512 ROIs). Labels used only for test evaluation (ground stations' snow depth, NBR/NDVI outlier + visual inspection, WaterNSW water-quality alerts, dam capacity <50%, council flood records). Training uses no labels.
- **Results**: F1 improvements of +0.066 (Gran Chaco) to +0.234 (Lake Copeton) over best baselines (cVAE 2.6M, RaVAEn-Local/Global 617K, COLD 41.9M): SNP F1 0.771 (vs cVAE 0.245, RaVAEn 0.182), Gran Chaco 0.728, Lake Copeton 0.881 (RaVAEn-Local 0.486), Lismore 0.466 with perfect recall 1.0. Gains driven mainly by much higher recall (e.g., SNP recall 0.775 vs 0.10 for RaVAEn). Ablations: seasonal threshold removal is the biggest hit (SNP F1 −0.393, Gran Chaco −0.260); cyclical (vs linear) day-of-year encoding crucial in strongly seasonal regions (SNP −0.281 F1); MAE scoring sometimes rivals SSIM (Gran Chaco +0.148 F1) but SSIM gives better background suppression for mapping; positional encodings marginal for metrics but sharpen maps.
- **What transfers to our thesis**: (1) The closest architectural template for our lightweight in-field anomaly models: 473K-param conditional UNet, trainable on a desktop RTX 3080, delivering seasonal-aware anomaly maps from SITS — well within TinyML/edge budgets for multi-product sugarcane deployment. (2) The "expected image for any day of year" formulation (baseline patch + cyclical DoY conditioning + reconstruction error vs actual observation) is directly adaptable to label-free sugarcane water/salinity stress detection on Landsat 16-day series: a stressed field shows large structural difference from its seasonally expected state. (3) The seasonally adaptive threshold (mean + 1.64 SD from training-period scores) is a principled, tuning-free alarm rule we can adopt for CWSI/ETa-derived anomaly flags — their ablation shows flat thresholds cost up to −0.39 F1. (4) SSIM-based difference maps give spatially interpretable, XAI-friendly outputs (where in the field is the anomaly), complementing C-SHAP-style temporal explanations. (5) Percentile-based (1st/99th) normalization robust to cloud/outlier heavy tails — practical for Landsat. (6) Demonstrates detection of gradual hazards (drought, deforestation) that event-based methods (RaVAEn) miss — analogous to slow-onset salinity/water stress.
- **Limitations / caveats**: Trained per-ROI (no cross-region model); assumes training data essentially hazard-free; baseline as multi-year median means gradual persistent changes become invisible if absorbed into the baseline (they observed missed recently-cleared fields); evaluated only on <10% cloud-cover data (cloud handling unsolved — they suggest SAR augmentation); intra-annual seasonality only (no inter-annual trends like El Nino); 10-band Sentinel-2, no thermal band; hazard labels partly from visual inspection; region-level detection focus, pixel maps secondary.
- **Key numbers to quote in lit review**:
  - 473K-parameter self-supervised seasonal translation UNet beats cVAE/RaVAEn/COLD on 4 hazard datasets, F1 gains +0.066 to +0.234.
  - Seasonally adaptive threshold (mean + 1.64 SD cyclical regression) worth up to +0.39 F1 vs a flat threshold.
  - Cyclical day-of-year encodings outperform linear time encoding by +0.281 F1 in strongly seasonal regions.
  - Perfect recall (1.0) for flood detection at Lismore with a single observation, no confirmation lag.



---


## FILE: 2025 Gupta and Sobti - Time2Agri - Temporal Pretext Tasks for Agricultural Monitoring (arXiv).md
# Time2Agri: Temporal Pretext Tasks for Agricultural Monitoring

- **Full citation**: Gupta, M. R., & Sobti, A. (2025). Time2Agri: Temporal Pretext Tasks for Agricultural Monitoring. arXiv:2507.04366v1 (Plaksha University, India).
- **Problem & setting**: SSL pretext-task design specifically for agricultural monitoring, exploiting the cyclical sowing-growth-harvest dynamics ("nature's cycle") that generic RSFM pretexts (MAE, temporal-invariance contrastive) ignore. Two settings: regional (SICKLE benchmark, Cauvery Delta, Tamil Nadu; Sentinel-2 10 m, monthly Jan 2018–Mar 2021, RGB+NIR) and national India scale (FTW India field delineation; monthly bitemporal harmonized S2 RGB+NIR, Jan 2016–Jan 2019).
- **Method**: Three agriculture-specific pretext tasks on bitemporal image pairs with a ViT-S encoder: (1) **TD — Time-Difference Prediction**: classify the absolute monthly time gap |Δt| between two images from stacked CLS tokens (3-layer MLP, cross-entropy, symmetric loss for order robustness); (2) **FP — Temporal Frequency Prediction**: from two frames + positional/temporal encodings (month+year sinusoidal), an MAE-style 6-layer transformer decoder regresses a per-pixel map of the top-3 dominant FFT frequencies of that pixel's full NDVI time series (Savitzky-Golay-smoothed, monthly-interpolated); normalized pixel-wise MSE; (3) **FF — Future-Frame Prediction**: predict the future image from a single past frame, via a 2-layer "time translator" transformer that maps Z_t1 + [pos; te1; te2] to the future latent, then a 4-layer decoder reconstructs the future frame; normalized pixel-wise MSE. Time encoding = month+year (explicitly avoiding DoY/month-of-year encodings that erase inter-year differences). Baselines: single-frame MAE on same data, frozen DoFA, supervised ViT-S, supervised UNet3D.
- **Data & labels**: Pre-training fully unlabeled: regional chips (224x224, 10 m, ≥80% agricultural, ocean-masked, ≥1 valid image/month via adaptive cloud thresholding) and national 3x3-neighborhood grids around FTW India chips. Labels only for downstream: SICKLE (paddy crop-type IoU, parcel yield MAPE, sowing/transplanting/harvest date MAPE) and FTW India (3-class field interior/boundary/exterior, presence-only labels).
- **Results**: SICKLE: FF best on crop-type mapping with 69.6% IoU, beating MAE 67.1%, supervised ViT-S 65.5%, UNet3D 65.4%, DoFA 58.4% (+11.2 over DoFA). FP best on yield: 30.7% MAPE in-season (FF 32.5, DoFA 34.6) and 34.3% full-season. Date prediction: supervised UNet3D still best. Temporal-gap ablation (FF): 0–3 month gaps best for crop mapping (69.6 IoU), 3+6 months best for yield (33.4 MAPE), 3+6+9 months best for date prediction — task-specific temporal horizons. FTW India: FF 54.2% IoU vs MAE 52.8, ViT-S 49.3, DoFA 38.1. SSL pretraining on India-only data recovers 99.7% (FF) to 100.8% (MAE) of cross-region-supervised performance. **Regional (Tamil Nadu) pretraining beats national (India) pretraining by +9.1% IoU for crop mapping and +3.0% yield MAPE** — geographic specialization over scale.
- **What transfers to our thesis**: (1) Strongest direct support for our thesis's premise that domain-informed pretext design beats generic SSL: predicting phenology-aware targets (time gaps, dominant NDVI frequencies, future states) yields more agriculturally relevant representations than MAE or global FMs. (2) FP's per-pixel dominant-frequency prediction is a ready pretext for sugarcane: multi-year sugarcane cycles and stress-induced frequency shifts encode growth rate and disturbance; predicting them forces phenology learning without labels. (3) The explicit finding that *regional pretraining outperforms national-scale* models (+9.1% IoU) directly justifies our in-region, sugarcane-specific SSL pretraining on local Landsat archives instead of relying on global foundation models. (4) Month+year time encoding preserving inter-year differences suits cross-year sugarcane models (ratoon vs plant cycles differ across years). (5) Future-frame prediction (FF) doubles as a stress-sensitive probe: stressed fields violate the "predictable" crop cycle, so prediction error itself is an anomaly signal (links to SHAZAM's expected-vs-observed paradigm). (6) Practical scale: ViT-S + single RTX A6000 pretraining; monthly cadence comparable to Landsat 16-day.
- **Limitations / caveats**: Only 4 bands (RGB+NIR), Sentinel-2 dominated, no thermal/LST — no water-stress signal; bitemporal pairs (max 3-month gap default) discard most of the dense series at downstream; FP requires precomputing frequency maps over the whole archive; downstream tasks are crop mapping/yield/dates — no stress or anomaly evaluation; FP's stated link to stress detection ("captures stress events over a longer horizon") is argued, not measured; supervised baselines still win on precise date prediction; SICKLE binary paddy segmentation limits generality.
- **Key numbers to quote in lit review**:
  - Future-frame prediction pretext: 69.6% IoU crop mapping vs 58.4% for DoFA and 67.1% for MAE (SICKLE).
  - Temporal-frequency prediction pretext: 30.7% MAPE in-season yield, best of all models.
  - Regional pretraining beats national-scale pretraining by +9.1% IoU (crop mapping) — geographic specialization > scale.
  - India-only SSL pretraining recovers 99.7–100.8% of cross-region supervised FTW performance, removing the need for foreign labels.
  - Temporal-gap ablation: 0–3 months best for mapping, 3–6 for yield, 3–9 for phenological dates.



---


## FILE: 2025 Jutte et al. - C-SHAP for Time Series - High-Level Temporal Explanations (arXiv).md
# C-SHAP: Concept-Based (High-Level Temporal) Explanations for Time Series

- **Full citation**: Jutte, A. M. P., Ahmed, F., Linssen, J., van Keulen, M. (2025). C-SHAP for time series: An approach to high-level temporal explanations. arXiv:2504.11159v2 (Saxion University of Applied Sciences / University of Twente, Netherlands).
- **Problem & setting**: XAI for time-series models. Point- and subsequence-based attributions (KernelSHAP, TimeSHAP, WindowSHAP) miss global patterns (e.g., overall trend, variance change) whose importance is spread across the whole signal, and are poorly interpretable to humans. Goal: attribute model predictions to human-meaningful high-level concepts. Demonstrated on two use cases: Human Activity Recognition (OPPORTUNITY dataset, univariate knee accelerometer, 90-point windows, 11,517 train / 1,967 test, 4 locomotion classes) and predictive maintenance (Turbofan C-MAPSS, P30 pressure, 100-cycle windows, 2,086 train / 70 test, RUL regression), using GRU black-box models.
- **Method**: C-SHAP treats SHAP "features" as high-level **concepts** extracted from the series rather than points. Concepts are built via invertible time-series decomposition (required for the post-hoc path: recombination of all masked/unmasked concepts must reconstruct the original input — Condition 2). Two variants: (a) **fully post-hoc, concept-agnostic** — model trained on raw series; concepts masked by replacing components with components sampled from training data and recombined into a univariate signal (N=100 background samples); (b) **partially ante-hoc, concept-informed** — model trained with one channel per concept; masking replaces whole concept channels. Two decompositions: (1) Discrete Wavelet Transform (Daubechies-6, detail level 3 → Approximation + Detail-1..3); (2) a custom human-centred hybrid decomposition: y = Trend + Bias + Scale x (LowFreq + Variance x HighFreq) — Trend (least-squares slope), Bias (mean level), Scale (max amplitude, multiplicative), Variance (sliding-window SD, multiplicative), Low/High frequency (DWT soft-thresholding + residual). Because only ~4–6 concepts exist, SHAP values are computed exactly (no exponential-cost coalition sampling). Decomposition is deterministic; explainability not dependent on annotated concept datasets (unlike TCAV/CBMs).
- **Data & labels**: Supervised tasks only (HAR class labels; RUL values). XAI method itself is post-hoc and model-agnostic; concept construction is unsupervised (pure signal decomposition). No remote-sensing data.
- **Results**: Concept-informed vs concept-agnostic model performance is comparable (OPPORTUNITY weighted acc 75.78% agnostic vs 76.87% custom / 73.59% DWT informed; Turbofan RMSE 20.87 vs 21.83/22.45 cycles) — so the explanation layer does not sacrifice accuracy. Local explanations: C-SHAP clearly identifies 'Trend' as driving a Turbofan RUL prediction where point-based KernelSHAP spreads attribution uselessly across points. Global explanations: HAR models rely mainly on 'Bias' (mean knee angle) and 'Scale' (amplitude of largest fluctuation) — matches human intuition (standing vs lying angle; walking amplitude); Turbofan models rely on 'Trend' (linear pressure decay indicates remaining life). DWT's additive structure smears amplitude across components (its 'Detail-3' scored low), while the custom 'Scale' concept captures it explicitly.
- **What transfers to our thesis**: (1) Direct XAI toolkit for our label-free sugarcane stress models: per-field Landsat 16-day VI/LST series can be decomposed (STL/wavelet or their custom Trend/Bias/Scale/Variance/LF/HF scheme) and C-SHAP run to answer "did the model flag stress because of a trend break, amplitude change, or slow decline?" — far more actionable for agronomists than pixel/point saliency. (2) Concepts map naturally to stress physics: water stress → increasing trend in LST anomaly + variance change; salinity → long-term trend decline in NDVI (chronic) vs seasonal variance change; the custom decomposition's Trend and Variance concepts align with detecting chronic vs acute stress. (3) The concept-informed variant offers a way to build interpretable-by-design stress classifiers with concept channels (interpretability without post-hoc cost). (4) Exact SHAP is tractable because concept count is small — cheap enough for in-field/edge use alongside lightweight models. (5) Their masking-by-resampling-from-training-data protocol is directly reusable on our satellite time series.
- **Limitations / caveats**: Not remote sensing — demonstrated only on accelerometer and engine simulation signals; univariate series only in experiments (multi-channel satellite stacks untested); custom decomposition is heuristic, hyperparameters (wavelet, thresholds, window sizes) hand-picked by visual inspection with no sensitivity analysis; no user study yet validating interpretability claims; concept-informed models showed no accuracy gain here (may differ for more complex tasks); ordering choice of the hybrid decomposition is pragmatic, not proven unique.
- **Key numbers to quote in lit review**:
  - C-SHAP computes exact Shapley values over 4–6 human-interpretable concepts (trend, bias, scale, variance, LF/HF) instead of thousands of points.
  - Concept-informed GRU models match concept-agnostic accuracy (75.8% vs 76.9% HAR; 20.87 vs 21.83 RMSE Turbofan) — explanations at no accuracy cost.
  - Turbofan RUL: 'Trend' is the dominant concept — a global pattern invisible to point-based KernelSHAP.
  - Provides both post-hoc (model-agnostic, requires invertible decomposition) and concept-informed (ante-hoc) variants.



---


## FILE: 2025 Kamangir et al. - California Crop Yield Benchmark - Landsat + Climate + ET + Soil, 70 Crops, CVPRW (arXiv).md
# California Crop Yield Benchmark: Landsat + Climate + ET + Soil for County-Level Yield Forecasting of 70+ Crops

- **Full citation**: Kamangir, H., Hajiesmaeeli, M., Earles, J. M. (2025). California Crop Yield Benchmark: Combining Satellite Image, Climate, Evapotranspiration, and Soil Data Layers for County-Level Yield Forecasting of Over 70 Crops. arXiv:2506.10228v1 (CVPR Workshop paper; UC Davis / Texas A&M-Corpus Christi). Public dataset + code on GitHub.
- **Problem & setting**: County-level, crop-specific yield forecasting across ALL California counties, 70+ crops, 2008–2022 (2012 excluded — only one Landsat sensor that year, no cloud-free monthly series). Ground truth: USDA NASS County-Based Yield Reports. Crop identity/field masks from USDA Cropland Data Layer (CDL, 30 m), fields ≥10 ha.
- **Method**: Contribution is primarily a benchmark dataset plus a supervised multi-modal Vision Transformer (not an SSL method). Modalities and encoders: (1) Landsat monthly time series, 12 steps x 6 bands (RGB, NIR, SWIR-1, SWIR-2), 30 m → 12x6x256 embeddings; (2) Daymet daily climate, 365 steps x 8 variables (tmin, tmax, precip, day length, shortwave radiation, vapor pressure, snow water equivalent, PET), 1 km → 365x8x256; (3) OpenET monthly evapotranspiration, 12x1xN at 30 m (energy-balance + ML ensemble over Landsat); (4) static SSURGO soil properties rasterized to 30 m, 5 channels (available water storage top-100 cm, slope, available water supply in root zone, drainage class, hydrologic soil group); (5) crop identity as a learned categorical embedding. Each modality passes a stratified feature-extraction module (handles differing pixel counts per crop) to a common 256-d space; fused in a multi-modal Transformer encoder (8 layers, 6 heads, d=256) with a time-series regression head (MSE loss, AdamW, lr 1e-4, wd 0.01). Temporal split: train 2008–2018 (5-fold CV), validation 2019–2020, test 2021–2022 (fully unseen years).
- **Data & labels**: ~14 years x 70 crops x all CA counties of county-level yield labels (ton/ha); all covariates standardized and pixel-stratified per crop via CDL. Labels are annual county aggregates — no field-level yield.
- **Results**: Overall R² = 0.767 on the unseen test years (0.864 train, 0.667 validation). Per-crop test RMSE/MAE (ton/ac): Grapes 3.24/3.10, Tomatoes 6.13/5.75, Greens 3.47/2.66, Alfalfa 6.74/6.56, Strawberries 5.47/5.45; weakest for Corn (10.10/9.98), Almond (8.41/8.36), Walnuts (8.36/7.21) — higher variability / fewer samples crops degrade. No baseline model comparison is reported in the paper itself.
- **What transfers to our thesis**: (1) Modal blueprint for multi-product input fusion on exactly our sensor stack: monthly Landsat 6-band reflectance + OpenET (30 m) + Daymet PET/precip/temperature + static soil properties; our sugarcane ETa/CWSI water-stress product can reuse this ET source and the idea of static soil/context embeddings — directly relevant to salinity + water stress which both modulate ET and SWIR. (2) Temporal (leave-years-out) validation protocol — train 2008–2018, test 2021–2022 — is the correct cross-year evaluation design our thesis needs (prevents same-year spatial leakage); adopt it for the cross-year sugarcane splits. (3) Crop-identity embedding enables one multi-product model across crops — analogous to including variety/ratoon-cycle or field metadata embeddings for sugarcane. (4) Demonstrates ET as a first-class modality (monthly, 30 m, from Landsat) rather than a derived index — supports our thesis's ETa/CWSI product integration. (5) The ≥10 ha field filtering via a crop-type layer is a practical way to get clean field-level pixel stacks without field boundaries. (6) Public benchmark provides a reproducible external dataset for sanity-checking multi-modal fusion choices.
- **Limitations / caveats**: Fully supervised — needs yield labels; SSL appears only as cited related work (MAE, MMST-ViT contrastive), no self-supervised pretraining is performed; county-level labels prevent field-scale precision-agriculture use (authors acknowledge); test-period "improvement" over validation (0.667→0.767) suggests high inter-annual variance in labels rather than clear generalization; no ablations or baselines, weak paper experimentally (CVPRW); 30 m Landsat monthly compositing loses the 16-day cadence and cloud gaps are not discussed; yield units inconsistent in tables (ton/ac) vs abstract (ton/ha).
- **Key numbers to quote in lit review**:
  - Multi-modal Transformer over Landsat (monthly, 6 bands) + OpenET (30 m) + Daymet climate (8 vars, daily) + SSURGO soil (5 props) reaches R² = 0.767 on unseen years (2021–2022) across 70+ crops.
  - Benchmark spans 2008–2022 (minus 2012) for all California counties, with temporal train/test split (2008–2018 train; 2021–2022 test).
  - OpenET provides 30 m monthly evapotranspiration from Landsat — the same water-stress signal family as our ETa/CWSI products.
  - Per-crop test RMSE ranges 3.2 t/ac (grapes) to 10.1 t/ac (corn) — multi-crop generalization is harder for high-variability crops.



---


## FILE: 2025 Miranda et al. - Informed Learning for Estimating Drought Stress at Fine-Scale, ET Proxy Physics-Informed (arXiv).md
# Informed Learning for Estimating Drought Stress at Fine-Scale Resolution Enables Accurate Yield Prediction

- **Full citation**: Miranda, M., Charfuelan, M., Valdenegro Toro, M., & Dengel, A. (2025). "Informed Learning for Estimating Drought Stress at Fine-Scale Resolution Enables Accurate Yield Prediction." arXiv:2510.18648v1 [cs.LG], 21 Oct 2025. DFKI / Univ. Kaiserslautern-Landau / Univ. Groningen. Code: https://github.com/mmiranda-l/Yield-Loss.

- **Problem & setting**: Predict crop drought stress (actual evapotranspiration, ETa) and sensitivity to water scarcity (yield response factor Ky) at 10x10 m pixel resolution, and use them to sequentially solve the FAO yield-response-to-water function for pixel-level yield prediction. Study area: Switzerland, cereal crops, 54 harvester yield-map fields, seasons 2017-2021. Sensors: Sentinel-2 multispectral time series (16-55 time steps per season, ~5-day revisit, 10 m) + daily ERA5 reanalysis weather (precipitation, Tmin, Tmax) aggregated between S2 acquisitions (input-level fusion; 14 features).

- **Method** (supervised, physics-informed — not SSL): Formulate yield as a function of temporal water scarcity using the FAO-33/Doorenbos-Kassam relation yl = Ky*(1 - ETa/ETx); cumulative yield loss is a discrete integral of Ky_t*(1 - ETa_t/ETx_t) over the season; Yx = max yield over dataset. Two-component loss: L_total = λ1*||ŷa - ya||² + λ2*L_phys, where L_phys = indicator-weighted sum of (i) lower-bound penalty (ETa<0), (ii) upper-bound penalty (ETa>ETx), and (iii) within-bounds MSE pulling ETa toward ETx. ETx (maximum ET) is simulated with FAO-56/pyfao56 from ERA5 + SoilGrids + Hihydrosoil soil data + crop coefficients and used only as a physics regularizer, not a spatial product. Architecture: 2-layer LSTM backbone (128 hidden units, per-time-step linear+BN+dropout-0.2 heads), two linear output heads predicting ETa_t and Ky_t per time step (PG-LSTM); optional scaled dot-product temporal attention (PG-LSTM_attn). Uncertainty via deep ensemble of 10 members (±2σ bands). Pixel-wise training, K=10-fold CV + Leaf-One-Year-Out (LOYO).

- **Data & labels**: SwissYield dataset (Perich et al. 2023): 54,098 georeferenced combine-harvester yield samples from 54 yield maps, rasterized to 10 m; yield in t/ha as the only label. Labels are required (supervised); ETa/Ky are never directly labeled — they are latent quantities learned indirectly through the physics-constrained yield objective. Weather + simulated ETx are unlabeled covariates/regularizers.

- **Results**: PG-LSTM_attn R2 = 0.82 (MAE 0.59 t/ha, RMSE 0.86, MAPE 11%), beating Transformer (0.73), plain LSTM (0.80), Linear Regression (0.70). Physics loss is what drives gains. Ablation (fixed literature Ky = 1.05, only ETa learned): R2 drops to 0.74 (PG-LSTM) — estimating Ky matters, though a constant Ky still yields competitive performance. LOYO temporal transfer collapses for all models (best R2 0.41 in 2019; several negative years) — cross-year generalization is the open problem. Predicted yield loss anti-correlates with ET deficit (Pearson -0.45); learned Ky rises toward flowering (matching FAO-662 agronomy), ETa tracks NDVI, ETa stays bounded below ETx as physically required.

- **What transfers to our thesis**:
  - Directly validates ETa as an estimable drought/water-stress proxy at pixel level from multispectral SITS + coarse weather — supports using ETa/ETx deficit (CWSI-like) as the stress target signal in sugarcane water-stress work, and shows LST/energy-balance-free ET modeling is feasible when paired with a physics constraint.
  - The physics-informed loss bounding ETa in [0, ETx] and pulling toward ETx is a ready template for embedding FAO-56/CWSI prior knowledge into our supervised or SSL fine-tuning heads without ETa ground truth.
  - Estimating Ky (stage-varying water sensitivity) as a free latent parameter mirrors sugarcane's growth-stage-dependent stress susceptibility; Ky uncertainty > ETa uncertainty in their ensemble — an XAI/uncertainty angle.
  - Deep ensembles (10 members) as lightweight uncertainty quantification for in-field stress maps.
  - Their LOYO failure quantifies exactly the cross-year generalization gap our SSL approach (label-free, year-agnostic pretraining) targets; no SSL is used here — a clear positioning opportunity.

- **Limitations / caveats**: Single country, single crop group (cereals), only 54 fields / 5 years; supervised pixel-level yield labels required; no true ETa ground truth (validated only qualitatively by experts and via yield correlation); LOYO R2 often negative — temporal transfer unsolved; ETx from FAO-56 simulation assumed accurate and coarse (field-level, not pixel-level); ETa/Ky jointly estimated is ill-posed (hence the ensemble); Sentinel-2, not Landsat; salinity stress not considered.

- **Key numbers to quote in lit review**:
  - R2 = 0.82 pixel-level cereal yield prediction (PG-LSTM_attn) vs 0.73 Transformer, 0.80 plain LSTM — physics-informed loss adds +9 p.p. over Transformer.
  - ETa estimated at 10 m resolution where simulation models are field-level/coarse.
  - Ablation: fixing Ky = 1.05 (literature value) drops R2 from 0.81/0.82 to 0.74 — stage-varying water sensitivity is worth ~8 p.p.
  - LOYO: best unseen-year R2 only 0.41 (2019), several negative — cross-year temporal transfer is the bottleneck.
  - Predicted yield loss vs ET deficit Pearson correlation = -0.45; deep ensemble of 10 for uncertainty.



---


## FILE: 2025 Perantoni, Weikmann and Bruzzone - Bayesian Modelling of Multi-Year Crop Type Classification - Transformer + HMM (arXiv).md
# 2025 Perantoni, Weikmann and Bruzzone — Bayesian Modelling of Multi-Year Crop Type Classification (Transformer + HMM)

- **Full citation**: Perantoni, G., Weikmann, G., Bruzzone, L. (2025). "Bayesian Modelling of Multi-Year Crop Type Classification Using Deep Neural Networks and Hidden Markov Models." arXiv:2510.07008; Proc. IEEE IGARSS 2024, pp. 941–945, DOI 10.1109/IGARSS53475.2024.10642432. University of Trento.
- **Problem & setting**: Multi-year (Y=6 years) crop-type classification of yearly satellite image time series — predicting a *consistent sequence* of 47 crop labels per parcel across years, not independent per-year maps. Emphasis on temporal consistency of labels across years (crop rotations).
- **Method**: Cascade/Bayesian classification. A Transformer Encoder (TE, per Rußwurm & Körner 2020 self-attention on raw optical TS) is the HMM **emission model** p(x|ω), trained per-year on parcel-mean time series (13 S2 bands, T observations, no cloud screening). A custom **HMM layer** stores joint log-probabilities P(ω(y), ω(y+1)) for each adjacent year pair (per-pair transition matrices, not shared) and performs forward AND backward cascade classification (forward–backward fusion, Eq. 7) so each year's prediction depends on all years. Also a 2nd-order HMM variant P(ω(y+2)|ω(y+1),ω(y)). Key design: "generative" TE head — bias-free, weight-normalised (cosine) softmax that implicitly enforces uniform class prior, aligning posteriors with the HMM emission requirement and reducing dominant-class bias. Training: TE trained on all years' labels; HMM initialised from label co-occurrence matrices; then joint supervised fine-tuning with cross-entropy through the cascade.
- **Data & labels**: Austrian LPIS/INVEKOS farmer-declaration crop maps, MGRS tile 33UVP, 805 Sentinel-2 L1C acquisitions, Sept 2016–Sept 2022, all 13 bands resampled to 10 m; 47 crop classes, ~300,000 fields ≥400 m², per-class occurrence >0.05%, fields present all 6 years. Stratified split by agglomerative clustering of label sequences under Hamming distance with circular (rotation-invariant) shifts; 60/20/20 train/val/test.
- **Results**: Mean F1 on test: TE generative 68.71 → fine-tuned 70.88; TE discriminative 64.85 → 70.05; +HMM 1st-order cascade 70.16 → **73.59**; 2nd-order 70.08 → 73.49. HMM cascade +4.7 F1 over fine-tuned TE alone. Per-class: biggest gains on hard classes (e.g., pasture two uses 48.3→56.4/57.2, misc. field fodder 22.2→32.4/32.7); 2nd-order HMM helps hardest classes, 1st-order better overall.
- **What transfers to our thesis**: (i) The HMM-prior idea is directly reusable for **cross-year sugarcane stress staging**: stress states persist across growing seasons/years, so an HMM transition model on top of an SSL encoder's posterior could enforce temporal consistency of stress labels without new per-year annotations. (ii) The "generative" cosine-normalised head that removes class-prior bias is a cheap trick for imbalanced stress datasets. (iii) Backward+forward fusion means past AND future observations inform the stress state at year y — relevant since our Landsat archive (1984–present) lets us see "after the fact" whether stress preceded yield loss. (iv) The rotation-aware Hamming clustering for train/test splitting prevents leakage of similar crop sequences across splits — applicable to our cross-year protocol.
- **Limitations / caveats**: Fully supervised (needs per-year parcel labels); works on parcel-mean vectors, not per-pixel maps; small geographic footprint (one S2 tile); crop types ≠ continuous stress states (HMM states are discrete classes, CWA/ETa stress is continuous — would need discretisation); transition matrices estimated from labels, so label-free use would require unsupervised or self-supervised estimation of the prior.
- **Key numbers to quote**:
  - HMM cascade lifts mean F1 from 70.88% (TE only, fine-tuned) to 73.59% across 47 crop classes over 6 years of S2.
  - 47 classes, ~300,000 fields, 805 S2 acquisitions, single MGRS tile.
  - Generative (normalised-weight) head beats discriminative softmax head by ~3.9 F1 before fine-tuning (68.71 vs 64.85).



---


## FILE: 2025 Rouet-Leduc and Hulbert - Anomaly Detection in Satellite Imagery through Temporal Inpainting (arXiv).md
# 2025 Rouet-Leduc and Hulbert — Anomaly Detection in Satellite Imagery through Temporal Inpainting

- **Full citation**: Rouet-Leduc, B., Hulbert, C. (2025). "Anomaly detection in satellite imagery through temporal inpainting." arXiv:2512.23986. Kyoto University DPRI / Geolabe.
- **Problem & setting**: Label-free anomaly/change detection in Sentinel-2 time series (10 m, ~5-day revisit, 9 spectral bands + SCL). Detect sudden surface changes (here: 2023 Kahramanmaraş earthquake surface rupture at Tepehan, Turkey) despite atmospheric noise, seasonality, and illumination variation. Frames change detection as *temporal prediction*: predict the last frame from the preceding ones; prediction–observation residual = anomaly score.
- **Method**: Self-supervised temporal inpainting. Input = 4 consecutive cloud-free S2 frames (~1 month span); the target frame is 5–40% randomly masked (rectangular + freeform masks); model reconstructs masked RGB+NIR of the target. Architecture: SATLAS Swin-v2 Transformer backbone (27 M pre-trained params, SatlasPretrain on 290 M S2 images) + FPN decoder with pixel-shuffle upsampling (62 M decoder params, 89 M total); a 1×1 conv input adapter maps 37 channels (4×9 bands + mask) into the backbone's 9 channels. Loss: L = masked L1 + λ_SSIM·MS-SSIM (ramped to 0.15) + λ_HF·L1 on Laplacian-filtered outputs (ramped to 0.5). Two-stage training: 5 warmup epochs with frozen backbone (LR 1e-3), then 495 epochs full fine-tune with differential LRs (backbone 5e-5, head 1e-4), AdamW, EMA, FP16. Anomaly score at inference: 95th percentile of per-pixel L1 error within a 500 m-radius circular inpainting mask, evaluated under a mask excluding cloud/shadow/water/snow via SCL, hillshade<0.5 topographic shadow (Copernicus DEM), and projected cloud shadows.
- **Data & labels**: ~50,000 valid 256×256 time cubes from >10,000 globally distributed 5 km-grid locations spanning arid/temperate/tropical climate zones (S2 L2A via Planetary Computer/CUBO), 1 year, cloud<10%, reflectance/8160 clipped to [0,1]. **No labels** — training purely self-supervised; evaluation on synthetic anomalies (5 types: brightness, darkening, texture, spectral shift, vegetation/NDVI perturbation; intensity 0.3–25% of local dynamic range; circular 20% region; 150 test samples) plus the real earthquake case.
- **Results**: Synthetic anomalies — ROC-AUC 0.949±0.104 vs Reed–Xiaoli (RX) 0.904±0.120 and temporal median 0.803; PR-AUC 0.854 vs 0.711 (RX) and 0.626 (median); best F1 0.849 vs 0.735 / 0.664. At anomaly intensities <5% of dynamic range (visually imperceptible) ROC-AUC stays >0.85 while baselines approach chance (~0.5) — i.e., ~3× lower detection threshold. Tepehan rift: normalized anomaly score peaks at 0.89 on 12 Feb 2023 vs pre-event background <0.15; temporal median peak 0.71 (pre-event up to 0.42); RX peak 0.58 (pre-event up to 0.51). Inference ~50 ms/image on consumer GPU.
- **What transfers to our thesis**: This is the closest architectural template for our label-free sugarcane water/salinity stress detection: treat gradual stress onset as anomaly against what the pixel "should" look like. Concretely: (i) replace S2 frames with **Landsat 8/9 surface reflectance + LST composites at 16-day steps** (the 4-frame input could become 8–12 composites = a full growing season); (ii) mask-and-reconstruct the current frame from history, flagging fields whose reflectance/LST/CWSI deviates from seasonal expectation — no stress labels needed; (iii) their confound-removal list (SCL, topographic shadow, projected cloud shadow) maps to Landsat QA_PIXEL + DEM hillshade; (iv) the 95th-percentile-of-residual scoring gives a per-field anomaly statistic we can track across seasons; (v) their honest caveat that *slow persistent change is invisible* motivates combining forecast-style pretraining (cf. Faran et al.) with inpainting; (vi) using a frozen pre-trained backbone + trained decoder is a cheap fine-tuning recipe consistent with our lightweight in-field goal.
- **Limitations / caveats**: Fixed 4-frame input (short baseline) — misses gradual change; empirical anomaly threshold (no calibrated FPR); validated mostly on synthetic perturbations + one real event; 89 M params is heavy for in-field deployment; S2 revisit allows 4 frames in 1 month, whereas Landsat 16-day composites need a longer window for the same prediction context; RGB+NIR output only (no LST/thermal, no SWIR) in the prediction target.
- **Key numbers to quote**:
  - ROC-AUC 0.949 (inpainting) vs 0.904 (RX) vs 0.803 (temporal median) on synthetic S2 anomalies.
  - Detection threshold ~3× lower than baselines; ROC-AUC >0.85 for anomalies <5% of dynamic range where baselines ≈ chance.
  - Earthquake rupture: anomaly score 0.89 post-event vs <0.15 background (baselines 0.71 / 0.58 with far noisier background).
  - Training: ~50,000 self-labelled time cubes, zero external labels; 500 epochs; ~50 ms inference per 2.56 km tile.



---


## FILE: 2025 Sadbhave et al. - Sugar-Beet Stress Detection using Satellite Image Time Series - Fully Unsupervised Cross-Year (arXiv).md
# 2025 Sadbhave et al. — Sugar-Beet Stress Detection using Satellite Image Time Series (Fully Unsupervised)

- **Full citation**: Sadbhave, B.L., Vaeth, P., Dejon, D., Schorcht, G., Gregorová, M. (2025). "Sugar-Beet Stress Detection using Satellite Image Time Series." arXiv:2507.13514. THWS Center for AI and Robotics (with GreenSpin GmbH). Code: github.com/bhumikasadbhave/Sugar-beet-Stress-Detection-System.
- **Problem & setting**: Binary stressed-vs-healthy field detection for sugar beet (Beta vulgaris) in Bavaria, Germany, from Sentinel-2 L2A. Labels exist for only ~5% of fields and are used **only for evaluation**; the pipeline is fully unsupervised and designed to transfer directly to data from different years (cross-year deployment is an explicit design goal, tested on 2019, planned for 2024).
- **Method**: 3D convolutional autoencoder (3D_AE). Input: per-field 4D tensors (4×4 spatial sub-patches × C channels × 7 cloud-free acquisition dates, June–early Sept). Key design: **sinusoidal acquisition-date encodings** (sin/cos of 2πd/365 for day-of-year d) added element-wise to all input pixels, handling irregularly spaced acquisition dates across fields. Encoder: 3D convs preserving spatiotemporal dims → flatten → FC layers → 1-D latent z; decoder: transposed 3D convs; MSE reconstruction loss. Downstream: k-means (k=2) on latent features of all 1,857 unlabeled fields; sub-patch cluster labels aggregated to field label by threshold α (field = stressed if >α fraction of sub-patches stressed; default α=0.5, ablated 0.1–1.0). Preprocessing: field-ID mask, SCL cloud mask, border-pixel removal, sub-patch gap-filling with channel-wise means.
- **Data & labels**: Sentinel-2 L2A, 1000×1000 tiles, 10 bands (excluding S2 bands 1, 9, 10), 10 m; 7 cloud-free dates across the season. 1,857 unlabeled cloud-free fields (1,228 patches → 33,128 sub-patches, 80/20 train/test for the AE). Evaluation: 61 fields (35 stressed, 26 healthy) with farmer-collected ground truth. Tensor variants ablated: B10 (10 raw bands), MVI (NDVI, EVI, MSI), B4 (bands 2, 4, 8, 11).
- **Results**: Best model 3D_AE_B10 **with** temporal encodings: Accuracy 69.4%, F1 75.21%. Without encodings: 59.56% / 67.25% (temporal encoding is the single biggest gain, +8 F1). Baselines: raw data + k-means 63.93% / 74.42; histogram features 63.93% / 69.7; 2D AE 60.11% / 67.78. MVI (VI-only) worst: 52.46% / 64.32; B4 60.65% / 68.84 — raw bands beat pre-computed vegetation indices for unsupervised learning. At α≥0.5 the learned features outperform raw-data k-means in precision; at low α raw data has higher recall.
- **What transfers to our thesis**: This is a direct structural precedent for our thesis: fully unsupervised AE → clustering for crop stress detection on optical SITS with the same sparse-label reality (labels only for evaluation, cross-year reuse). Transferable pieces: (i) day-of-year sinusoidal encodings added at input — cheap and directly applicable to **irregular Landsat 16-day composites** (which drift around the 16-day grid and have gaps); (ii) sub-patch → field aggregation with tunable threshold α gives a field-level stress score with a precision/recall operating knob — analogous to our per-field CWSI/ETa anomaly thresholds; (iii) their finding that raw bands beat derived vegetation indices supports feeding Landsat raw reflectance + thermal/LST rather than VI-only channels; (iv) MSI (moisture stress index, SWIR-based) as a relevant moisture channel — Landsat 5/7/8 all have SWIR for an MSI analogue; (v) the 80/20 AE train/test on unlabeled data plus k-means evaluation protocol is a reproducible baseline we can beat with masked time-series SSL.
- **Limitations / caveats**: Only 61 evaluation fields, single season validated; accuracy barely above raw-data baseline (69.4 vs 63.93 acc) — AE adds precision, not overall accuracy; k=2 k-means assumes a clean two-cluster structure (real stress is a continuum); no temporal-consistency or spatial-context modeling beyond 4×4 sub-patches; class-imbalance acknowledged (farmer-reported labels over-represent stress); MSE reconstruction can spend capacity on clouds/illumination rather than stress; no statistical significance tests (averaged over 3 runs).
- **Key numbers to quote**:
  - Fully unsupervised F1 75.21% (acc 69.4%) on 61 farmer-labeled sugar-beet fields, with labels used only for evaluation.
  - Adding acquisition-date sinusoidal encodings: F1 67.25% → 75.21% (+8.0 points).
  - Raw 10-band input (F1 75.21) beats NDVI/EVI/MSI-only input (F1 64.32) by ~11 F1 in unsupervised clustering.
  - 1,857 unlabeled fields for training / 61 labeled for validation (~5% label availability), 33,128 sub-patches.



---


## FILE: 2025 Velazquez et al. - EarthView - Large-Scale RS Dataset for Self-Supervision, 15 Tpx (arXiv).md
# 2025 Velazquez et al. — EarthView: A Large-Scale Remote Sensing Dataset for Self-Supervision (15 Tpx)

- **Full citation**: Velazquez, D., Rodriguez López, P., Alonso, S., Gonfaus, J.M., Gonzalez, J., Richarte, G., Marin, J., Bengio, Y., Lacoste, A. (2025). "EarthView: A Large Scale Remote Sensing Dataset for Self-Supervision." arXiv:2501.08111. CVC / Satellogic / Mila / ServiceNow Research. Data: huggingface.co/datasets/satellogic/EarthView.
- **Problem & setting**: Curated multi-sensor unlabeled dataset for pretraining Earth-observation SSL models: 15 tera-pixels, global, 2017–2022, three sources — (1) **Satellogic**: RGB+NIR, 1 m GSD, 3,758 captures (clouds<30%), 2,967,663 patches of 384×384, 437,682 km², 1–68 revisits (986,521 regions with ≥2), 6.17 M images; (2) **Sentinel-2** (13 bands, 10/20/60 m) + **Sentinel-1** GRD (VV/VH, 2 bands, resampled 10 m): >2,000 S2 tiles within 50 km of largest world cities + tiles covering Satellogic scenes, ~1 M unique 384×384 regions of 3,840 m, 10 S2 revisits per location (6 dense + 4 at 3-month intervals covering seasons), 3–9 S1 revisits; (3) **NEON**: 369-band hyperspectral 1 m, RGB 0.1 m, lidar canopy height 1 m over 12 US forest sites, 35,501 patches, ≤3 revisits.
- **Method (EarthMAE)**: MAE (He et al.) adapted per SpectralMAE/SatMAE with: per-source linear tokenizers (handles heterogeneous band counts; all resized to 224×224); token encodings = concatenation of positional + **source embeddings** (64-d, per-source) + **temporal embeddings** (year/month/day/hour → 4×16-d, concatenated 64-d; 10% probability timestamps zeroed to simulate missing time); ViT encoder + lightweight ViT decoder; MSE loss on masked patches (normalized pixels). Task-based training system distributes source-subset tasks across GPUs. Masking ablation: random (95%), tube (75%, same patches masked across all time steps/sources, prevents cross-time copying, per VideoMAE), and combined (tube 75% + random 25% of remainder). Pretraining 100 epochs, batch 2048 (32×64 GPUs), blr 1.32e-4, wd 0.0457.
- **Data & labels**: Entirely unlabeled; evaluated on GeoBench classification (m-BigEarthNet, m-Brick-Kiln, m-EuroSAT, m-ForestNet, m-PV4GER, m-SO2SAT), fine-tuned with random-search hyperparameters, 5 seeds, normalized scores against ResNet18=0/SwinV2=1 anchors.
- **Results**: Tube masking 75% consistently best masking scheme; removing time information hurts all tasks. Satellogic pretraining beats Sentinel-only pretraining on all tasks; Sentinel+Satellogic combined is best (high resolution is a useful pretraining signal). Performance still mostly stable after ~15–25 epochs; on some tasks (m-forestnet, m-pv4ger) monotonic improvement. **Candid negative result**: aggregated performance is *significantly lower* than other GeoBench pretrained models (ViT-S, SwinV2, SeCo-S2, MoCo-S2) — authors hypothesize MAE may not be the right loss for heterogeneous multi-source data. Scaling: for harder tasks performance increases ~linearly with dataset size. Reconstruction loss is much higher on Satellogic (tube 0.561) than Sentinel (0.285) — higher resolution is harder to reconstruct.
- **What transfers to our thesis**: (i) Direct evidence that **timestamp embeddings beat no-time** in masked reconstruction on satellite time series — supports embedding acquisition dates (16-day composite day-of-year) in our Landsat SSL encoder; (ii) **tube masking** (mask the same patch across all dates/sources) is the right anti-shortcut strategy when our optical+LST Landsat cubes are reconstructed — otherwise the model copies across time steps; (iii) their honest negative MAE result is a caution: pure MSE masked reconstruction may underperform contrastive/multi-objective SSL for semantic downstream tasks — a justification for our mixed-objective (reconstruction + invariance) design; (iv) multi-source co-location idea (same region from two sensors) supports pairing Landsat optical with LST/ETa products as separate tokenized sources with source embeddings; (v) per-source tokenizers allow mixing bands of different native resolutions (Landsat 30 m SR vs LST, resampled).
- **Limitations / caveats**: Model underperforms published GeoBench baselines (not competitive as an encoder); unexplained m-BigEarthNet performance drop at later epochs; no thermal/temperature modality; no time-series-specific downstream (crop/stress) tasks evaluated; 15 TB and 64-GPU scale is far beyond a lightweight in-field thesis budget; seasonal sampling of 10 dates is thin vs our 16-day multi-year series.
- **Key numbers to quote**:
  - 15 tera-pixels, 2017–2022, three sensor families (Satellogic RGBN 1 m; Sentinel-1/2; NEON 369-band hyperspectral + lidar).
  - Tube masking 75% beats random (95%) and combined masking across 6 GeoBench tasks; dropping timestamp embeddings degrades all tasks.
  - Satellogic+Sentinel pretraining > Satellogic > Sentinel on every downstream task (high-res co-located data helps).
  - Despite scale, the MAE model scores significantly below SeCo/MoCo pretrained ResNets on GeoBench (negative result on MAE for heterogeneous RS data).



---


## FILE: 2025 Wei, Shan and Zhen - Deep Learning-Based Anomaly Detection for Precision Field Crop Protection (Frontiers Plant Science).md
# 2025 Wei, Shan and Zhen — Deep Learning-Based Anomaly Detection for Precision Field Crop Protection

- **Full citation**: Wei, C., Shan, Y., Zhen, M. (2025). "Deep learning-based anomaly detection for precision field crop protection." Front. Plant Sci. 16:1576756, DOI 10.3389/fpls.2025.1576756.
- **Problem & setting**: Claims a framework (IMSFNet + AROS) for crop anomaly detection via multi-modal fusion of satellite, UAV, ground sensors, and weather data, plus reinforcement-learning-based adaptive resource allocation (water/fertilizer/pesticide) under budget constraints. Proposal is domain-generic (wheat/rice/corn stresses: nutrient deficiency, fungal infection, drought, pests).
- **Method (as stated)**: IMSFNet — per-modality encoders projected into a shared latent space, softmax attention-based modality weighting, spatial attention maps, cross-modal scaled dot-product attention between all modality pairs, residual fusion + self-attention refinement, Transformer temporal modeling (vs LSTM) and GNN spatial modeling. AROS — multi-objective optimization O(U)=Y(U)−λ1C(U)−λ2E(U) with linear yield model (β coefficients + over-application penalty γ), budget constraints, prioritized resource allocation and real-time feedback; a "FFCA-YOLO / L-FFCA-YOLO" backbone with CSP/CBS blocks is also mentioned in figures/tables. Unsupervised anomaly formulation: anomaly if P(xi|q)<t, score si=D(xi,μ) (Mahalanobis/Euclidean), with variational autoencoders mentioned for subtle anomalies.
- **Data & labels**: Radiant MLHub, Kaggle agricultural sets, NAB, SWaT (industrial control benchmark), plus GFSAD/CropDeep in ablations. No new labels released despite claims. Evaluation supervised (accuracy/precision/recall/F1).
- **Results (claimed)**: Radiant MLHub: acc 91.56%, F1 89.78% vs best baselines (BLIP 88.34/85.73; ViT 87.12/85.21). Kaggle: acc 92.14%, F1 90.59%. Efficiency: 32.2% lower inference time and 12.7% less GPU memory than CNN-LSTM; 44.7%/40.3% lower time/memory than ViT-LSTM; 28.3 M params vs 65.3 M (ViT-LSTM). Ablations: removing multi-modal feature extraction costs ~2.4 acc; removing prioritized resource allocation costs ~3.2 F1 (86.56 F1); removing satellite data drops recall 8–9%; removing UAV ~3.6–3.9 acc; ground sensors 5.5–6.3 F1.
- **⚠ CREDIBILITY WARNING — treat as unreliable, do NOT cite for methods or numbers**: Multiple hallmarks of a low-quality/AI-generated paper: (i) the experimental section suddenly describes **point clouds (1,024 points/object, unit-sphere normalization, voxelization of LiDAR, RGB-D scans)** for agricultural satellite datasets — incoherent with the claimed task; (ii) internally contradictory results (identical acc 91.56 reported for two datasets with different data types; "3D anomaly detection" and "indoor/urban scenes" language in an agriculture paper); (iii) baseline citations are mismatched to real literature (e.g., "Grover et al. (2021)" for T5, "Friday et al.", "Wattasseril et al." for BLIP, "Chen and Rudnicky (2023)" for Wav2Vec 2.0 — these pairings are spurious); (iv) Figure 3 "DMO architecture" description is copied from a triplet-attention module unrelated to resource optimization; (v) suspiciously uniform ±0.02–0.03 std over all cells. The peer review appears shallow.
- **What transfers to our thesis**: Very little methodologically. Usable only in the lit review as an example of (a) the framing "anomaly = deviation from learned normal distribution" with per-zone Mahalanobis scoring — consistent with our label-free stress detection formulation; and (b) a cautionary tale on predatory/questionable publications in precision-agriculture DL — worth citing (if at all) only in a critical-discussion context, not as a source of evidence.
- **Limitations / caveats**: See warning above; no code/dataset actually released; no external validation; supervised labels required; AROS yield model is a synthetic linear function, never validated against real agronomic data.
- **Key numbers to quote** (only with the caveat above, if at all):
  - Claims F1 89.78% on Radiant MLHub vs 85.73% best baseline (+3.12 F1, +2.89 acc as stated in abstract).
  - Claims 28.3 M params / 1.45 s inference vs 65.3 M / 2.62 s for ViT-LSTM.



---


## FILE: 2025 Xu et al. - Knowledge-Aware Mamba for Joint Change Detection and Classification from MODIS Time Series (arXiv).md
# 2025 Xu et al. — Knowledge-Aware Mamba (KAMamba) for Joint Change Detection and Classification from MODIS Time Series

- **Full citation**: Xu, Z., Zhu, Y., Dewis, Z., Heffring, M., Alkayid, M., Taleghanidoozdoozan, S., Xu, L.L. (2025). "Knowledge-Aware Mamba for Joint Change Detection and Classification from MODIS Time Series." arXiv:2510.09679. University of Calgary (Geomatics Engineering). (Related STSMamba paper by same group.)
- **Problem & setting**: Land-cover change detection + per-year LULC classification from **MOD13Q1 MODIS 250 m, 16-day, 23 frames/year** time series (bi-temporal: 2010 vs 2015), Saskatchewan, Canada; 6 bands (NDVI, EVI, MODIS bands 1, 2, 3, 7 → C×T=138 channels per pixel, 13×13 patches). Challenges: mixed pixels, space-time-spectral coupling, class-heterogeneous background, implausible transitions (e.g., glacier→cropland).
- **Method**: KAMamba, supervised multi-task. (1) **Knowledge-aware transition loss (KAT-loss)**: an asymmetric, knowledge-driven class transition matrix P∈[0,1]^{K×K} couples pre-change classification posterior, post-change posterior, and change logits; bilinear MSE-based "Area of Union Transition Loss" penalizes ecologically implausible transitions — the "from" distribution gives stronger gradients. (2) **Multi-task losses**: PreC-loss + PostC-loss (per-year classification CE) + Chg-loss (change CE, weight 1.0 vs 0.5 for classification, KAT weight init 2.0). (3) **SSTMamba**: Temporal Grouped Stem (per-date depthwise 3×3 conv groups), then Sparse Deformable Mamba blocks for spatial (anchor-guided cosine-similarity token pruning, top-k=30% of HW tokens → Mamba → scatter-back + residual), spectral (attention row/column-sum sparsification, top 30%), and temporal dims. (4) **Feature Differential Module**: absolute differences of same-layer features from both epochs at three levels feed the CD head. Sequential (not parallel) coupling of the two classification flows. Contrastive learning is also part of the pipeline (w/o CL ablation).
- **Data & labels**: MOD13Q1 for 2010 and 2015; NRCan 30 m LULC maps (5-yearly) resampled to 250 m by mode aggregation as labels; class-wise sampling cap (10/50/100 samples by class frequency) for a filtered balanced set, full imbalanced set kept for realism. Adam, LR 1e-3, batch 128, 50 epochs.
- **Results**: Filtered dataset — change detection F1 93.26% (Change class) / 98.80% (No-Change), macro-F1 97.34%, OA 98.15, Kappa 94.76; beats BiSRNet/ChangeMask (89.31/89.36 Change F1, −3.9), SCanNet (91.33, −1.93), ChangeSparse (93.15, −0.11), ChangeMamba (92.56, −0.70). Full imbalanced dataset — Change-class F1 50.17% vs ChangeMamba 43.16, SCanNet 46.30, BiSRNet 27.94, ChangeMask 31.92; macro-F1 71.24% (BiSRNet 58.29, ChangeMask 63.84). Ablations: removing KAT → CD Kappa −2.82 (94.76→91.94); only-CD loss → Kappa 92.63; removing contrastive loss → AA up 0.10 but Kappa −0.42 (majority-class bias); sequential > parallel coupling (Kappa 94.76 vs 94.46). KAT benefits the "from" year head more (2010 OA +0.41).
- **What transfers to our thesis**: (i) **Same input format as ours**: 16-day MODIS time series with 23 annual composites is structurally identical to Landsat 16-day composites — their per-date grouped stem + separate spatial/spectral/temporal sparse-Mamba tokenization is a directly transferable lightweight backbone design (linear-time scanning, 30% token pruning → in-field friendly). (ii) The **transition/knowledge prior idea** is a strong fit for stress detection: impose a physiologically-informed transition matrix over stress states (e.g., CWSI classes cannot jump healthy→severe in one 16-day step; recovery after irrigation is allowed) as an unsupervised regularizer on cluster/state assignments — no labels needed. (iii) Their multi-task coupling (classification consistency ↔ change detection) suggests coupling our per-season stress staging with season-to-season change detection within one model. (iv) The imbalanced-set result (Change F1 drops to ~50% without class-balanced sampling) quantifies how badly minority-class (stress) detection suffers — motivation for balanced or anomaly-style evaluation in our cross-year tests. (v) The Feature Differential Module (absolute differences at equal layer depth) is a cheap change head we could reuse for stress-onset localization.
- **Limitations / caveats**: Fully supervised (needs 30 m NRCan labels resampled to 250 m — noisy mode-aggregated ground truth); coarse 250 m resolution limits field-level crops; transition matrix is hand-built from qualitative knowledge ("very likely/possible..."); Saskatchewan boreal/agricultural ecotone, not irrigated cropland; Mamba gains over Transformer ChangeSparse are small on the balanced set (0.11 F1); no SSL pretraining — labels drive everything.
- **Key numbers to quote**:
  - Change-class F1 93.26% (balanced) and 50.17% (imbalanced full set) — minority-class collapse under realistic imbalance vs ~90%+ on balanced data.
  - KAT-loss ablation: change-detection Kappa 94.76 → 91.94 when the transition prior is removed (−2.82).
  - Beats Mamba SOTA ChangeMamba by 0.70 F1 (balanced) and 7.01 F1 Change-class (imbalanced: 50.17 vs 43.16).
  - 16-day MODIS, 23 composites/year, 6 bands, 250 m — same temporal geometry as Landsat.



---


## FILE: 2025 Yu et al. - From Physics to Foundation Models - Review of AI-Driven Quantitative RS Inversion (arXiv).md
# From Physics to Foundation Models: A Review of AI-Driven Quantitative Remote Sensing Inversion

## Full citation
Yu, Z., Idna Idris, M. Y., Wang, H., Wang, P., Chen, J., & Wang, K. (2025). *From Physics to Foundation Models: A Review of AI-Driven Quantitative Remote Sensing Inversion*. arXiv:2507.09081 [cs.CV]. https://arxiv.org/abs/2507.09081

## Problem & setting
- Review paper (no new experiments): quantitative remote sensing (RS) inversion = estimating continuous surface variables (LAI, NDVI, FAPAR, FVC, AGB, canopy height, ET, soil moisture, LST, VPD, albedo, turbidity, AOD, etc.) from satellite observations.
- Framing: three-stage paradigm evolution — (1) physics-based models (PROSAIL, SCOPE, DART, Hydrolight, MODTRAN/6S, Penman–Monteith), (2) data-driven ML/DL (RF, SVR, XGBoost, CNN, LSTM/RNN, GNN, Transformer), (3) foundation models (SatMAE, GFM, mmEarth).
- Emphasizes inversion task attributes: continuous outputs with physical semantics, multi-scale (10–500 m), single- to multi-temporal sequences, multimodal heterogeneous sensors (MSI, HSI, SAR, TIR, LiDAR), cross-region domain shift.

## Method (survey structure / taxonomy)
- **Physics-based inverse strategies:** Look-Up Tables (no differentiability needed, poor OOD generalization, high cost in high dimensions); optimization-based estimation (least squares, MCMC, Kalman — sensitive to initialization/local minima); PINNs (physical equations as soft loss constraints; suited to weak supervision but training instability and loss-weighting sensitivity).
- **Foundation models for inversion (Table 5):**
  - SatMAE: MAE + ViT, multi-temporal Sentinel-2, masked autoencoding (mask + reconstruct); tasks NDVI/LAI/FAPAR.
  - GFM: multimodal Transformer, optical+SAR+DEM, self-supervised + multi-task; tasks AGB, canopy height, SIF, carbon stock.
  - mmEarth: cross-modal Transformer, HSI+SAR+DSM, masked + contrastive learning; tasks NDVI, biomass.
- Identified FM gaps for regression: regression heads are shallow MLPs under-explored; fine-tuning strategies not standardized; almost no physical constraints in pretraining objectives.

## Data & labels
- Benchmark dataset table: BigEarthNet (S1+S2, Europe, 10–20 m), SSL4EO-S12/L (global, 10–30 m, used for LAI/FAPAR/SIF), Satlas (S2+SMAP+meteo, soil moisture/AGB), Sen4AgriNet (S1/S2 + agronomic ground truth, Europe/Africa), Open-Canopy (France, RGB+LiDAR, 1–10 m, canopy height/AGB).
- Recurring theme: ground truth for inversion targets (AGB, SIF, SM) is sparse, expensive, temporally mismatched, and label-noisy; this motivates self-supervised pretraining and RTM-simulation-based weak supervision.
- Metrics: RMSE, MAE, R2, SSIM, PSNR.

## Results
- No quantitative benchmark of its own (review). Comparative qualitative claims: ML = interpretable, small-data friendly, but manual features and weak spatio-temporal context; DL = end-to-end, nonlinear, multimodal, but label-hungry and domain-shift sensitive; FMs = strong few-shot/multi-task transfer but high compute cost and unproven regression adaptation.

## What transfers to our thesis
- Directly relevant framing for the lit review: positions ET/LST/soil-moisture retrieval (our CWSI/ETa water-stress pathway) as "quantitative inversion," and argues self-supervised FM pretraining is the current answer to label scarcity — the exact gap our label-free sugarcane stress work targets.
- Supports the argument that SSL pretraining + lightweight regression/anomaly heads beats task-specific supervised models under label scarcity; also supports using physics constraints (energy balance, Penman–Monteith/CWSI relationships) as loss terms (PINN-style) — a concrete design option for our ETa-proxy-informed SSL.
- The claim that regression heads and fine-tuning protocol are under-studied in RS FMs justifies our choice of lightweight downstream heads (AE ensembles, small decoders) instead of heavy FM fine-tuning.
- Cross-region/cross-year domain shift is named as the core generalization bottleneck — aligns with our cross-year in-field model requirement.

## Limitations / caveats
- Pure review, mostly pre-2025 literature; no experiments, no quantitative comparison tables of methods' accuracy.
- Coverage of FMs for *time-series* inversion is thin (SatMAE/GFM/mmEarth are spatial/pixel-level; temporal SITS foundation models like Presto are not central).
- No treatment of anomaly-detection-style stress monitoring; all targets assume regression with some labels.
- Some citations are oddly off-topic (e.g., stealth/multimedia references), suggesting loose citation hygiene.

## Key numbers to quote in lit review
- Taxonomy of 5 inversion variable groups with variable→model mapping (e.g., ET: RF/LSTM → no FM yet; LST: XGBoost/CNN-LSTM → mmEarth) — useful as evidence that ET/SM inversion lacks mature FM solutions.
- 3-stage paradigm claim: physics → data-driven → foundation models, with label scarcity + domain shift cited as the two persistent blockers.
- Benchmark datasets span 1–30 m resolution; SSL4EO explicitly supports LAI/FAPAR/SIF self-supervised benchmarks.



---


## FILE: 2025 Yu et al. - OPTIMUS - Observing Persistent Transformations in Multi-Temporal Unlabeled Satellite Data, WACV 2025 (arXiv).md
# OPTIMUS: Observing Persistent Transformations in Multi-temporal Unlabeled Satellite-data

## Full citation
Yu, R., Han, P., Myers-Dean, J., Wolters, P., & Bastani, F. (2025). *OPTIMUS: Observing Persistent Transformations in Multi-temporal Unlabeled Satellite-data*. WACV 2025. arXiv:2506.13902 [cs.CV]. https://arxiv.org/abs/2506.13902

## Problem & setting
- Task: binary classification of satellite image time series — does a location contain a *persistent* (lasting >1 year), non-seasonal change (deforestation, urban expansion, lake recession, wildfire impacts) vs no change / only cyclic seasonal change?
- Data: Sentinel-2 (RGB bands B2/B3/B4 only, cloud-filtered <20%) and NAIP; 512×512 px at 10 m/px (5×5 km); 1,000,000 unlabeled time series for training, each 30–48 images spanning Jan 2016–Dec 2023 (8 years), minimum 2-month interval between images.
- Evaluation set: 300 labeled time series (~1/3 positive); a 100-series subset split into 1,600 128×128 patches with binary labels for localization. Global random sampling, deliberately non-urban-biased.

## Method
- **SSL pretext (temporal-order recovery):** hide timestamps; train a Siamese binary classifier on triplets (A1, A2, Q) to predict whether query image Q is temporally closer to anchor A1 or A2. Intuition: if long-term ordering of images is recoverable from appearance alone, a persistent change occurred; for purely seasonal/unchanged locations, cross-year ordering is indecipherable.
- Key design choices: (1) query Q is sampled *outside* the anchor interval (before A1 or after A2, equal probability) so visual similarity always matches temporal closeness — avoids mislabeling when change happens near an anchor; (2) each anchor = c=3 consecutive images (context size ablation: c=3 optimal, AUROC 0.877 vs 0.809 at c=1 and 0.817 at c=5); (3) BCE loss, AdamW lr 3e-4, batch 5, 5 epochs, ResNet-50 backbone (Satlas pretrained weights best: AUROC 0.876 vs 0.851 random init).
- **Change scoring at inference:** for a new series compute score sequence S = {b(I1, In, Ij)}; a "pivot score" = max over split index i of |mean(S before i) − mean(S after i)| (change-point statistic); pivot beats Spearman rank correlation (AUROC 0.877 vs 0.860).
- **Spatial localization:** iterative self-training — train on 512×512, keep top-50% highest-scoring series, retrain on 128×128 patches to boost change density (AUROC 0.9415 localized vs 0.8714 without iteration).

## Data & labels
- Training fully unsupervised (labels only emerge from temporal structure). Human binary labels used only for the 300-series evaluation set (annotated with geographic cross-reference via Google Maps/OSM; ~1/3 positive).

## Results
- Change/no-change AUROC: OPTIMUS 0.876 vs CaCo (OSCD-finetuned) 0.563, CaCo 0.494, SeCo 0.491; F1 0.760 vs 0.585 best baseline.
- Localization AUROC 0.9415 (iterative 512→128 training).
- Backbone ablation: ResNet-50 0.876, SwinBase-v2 0.865, ResNet-152 0.850 — method matters more than backbone.

## What transfers to our thesis
- The core pretext idea — recover hidden temporal ordering to detect *persistent, non-cyclic* deviations — is directly mappable to sugarcane stress: a chronically stressed (water/salinity) field has an anomalous, non-seasonal trajectory across years, while healthy fields share the seasonal rhythm. A temporal-ordering or "which year is this" pretext on Landsat 16-day series could flag cross-year stress trajectories without labels.
- Pivot-score change-point statistic is a cheap, threshold-free anomaly score usable per-field on our time series (e.g., detect onset of salinity decline across seasons).
- Demonstrates that SSL trained only on temporal structure can beat dedicated contrastive change methods (CaCo, SeCo) by a wide margin (0.876 vs 0.563 AUROC) — strong citation support for pretext-driven label-free anomaly detection over generic contrastive embeddings.
- Iterative self-filtering (train → select top-k anomalous → retrain) is a lightweight recipe to increase anomaly density in training data, applicable to our small in-field datasets.

## Limitations / caveats
- RGB-only Sentinel-2/NAIP, 10 m; no multispectral indices (NDVI/NDRE), no thermal/LST — direct transfer to Landsat optical+LST needs re-derivation of the pretext on band time series rather than images.
- Targets abrupt, visually obvious persistent change (roads, deforestation); slow subtle stress gradients (salinity) are untested and may be below the pivot-score sensitivity.
- Small evaluation set (300 series, 100 annotated for localization), binary labels only, some annotation errors acknowledged (one mislabeled row).
- Struggles with deserts/shadows/dune movement (false positives); seasonal-agriculture mixture cases are the hardest.

## Key numbers to quote in lit review
- AUROC 56.3% → 87.6% over prior unsupervised change-detection baselines (CaCo/SeCo family).
- Localization AUROC 0.9415 via iterative 512→128 retraining.
- Context size c=3 anchors optimal (AUROC 0.877 vs 0.809 c=1); pivot score > Spearman (0.877 vs 0.860).
- Training data: 1M time series × 30–48 images over 8 years, entirely label-free.



---


## FILE: 2025 Zhu et al. - Exact - Space-Time Perceptive Clues for Weakly Supervised SITS Segmentation, CVPR 2025 (CVF).md
# Exact: Exploring Space-Time Perceptive Clues for Weakly Supervised Satellite Image Time Series Semantic Segmentation

## Full citation
Zhu, H., Zhu, Y., Xiao, J., Xiao, T., Ma, Y., Zhang, Y., & Dai, F. (2025). *Exact: Exploring Space-Time Perceptive Clues for Weakly Supervised SITS Semantic Segmentation*. CVPR 2025 (CVF Open Access), pp. 14036–14045.

## Problem & setting
- Task: crop-type semantic segmentation on Satellite Image Time Series (SITS) with only **image-level** category labels (weakly supervised semantic segmentation, WSSS) — first WSSS work for SITS crop mapping.
- Two SITS-specific problems they identify: (1) **spatial noise perturbation** — parcels of the same crop look uniform, so intra-class compactness makes CAMs over-activate onto neighboring parcels; (2) **temporal erroneous semantic bias** — crops look alike in certain phenological windows, so anomalous (non-pivotal) temporal clips inject wrong activations.
- Data: Sentinel-2 time series. PASTIS (2,433 series, 128×128, 10 bands, 33–61 observations, 18 crops + background, fold-1) and Germany dataset (137k field parcels, 13 bands, 36 observations, 17 crops).

## Method
- Backbone: TSViT-style **temporal-spatio** scheme — temporal ViT encoder over acquisition times, then spatial ViT encoder over patch tokens; classification from global tokens, dense tokens feed both an auxiliary classifier (raw fused CAM) and a segmentation decoder.
- Three components beyond the CAM baseline:
  1. **Spatial perceptive clues (prototype/contrastive):** filter raw CAM with thresholds (µl=0.2, µh=0.4) into foreground/background/ignore; cluster temporal dense embeddings class-wise into positive and negative prototype sets (Np=2 prototypes/class) via optimal transport (Sinkhorn-Knopp), momentum-updated (α=0.999, no gradient); then **clue-based contrastive loss** pulls each pixel embedding to its class prototype and pushes from all other prototypes (cosine sim, τ=0.1).
  2. **Temporal-aware affinity propagation:** extract temporal-to-class attention Ã (T×K) free from the temporal encoder self-attention, reweight temporal sequence embeddings, build pairwise affinities and propagate on the raw CAM to suppress erroneous activations; alignment loss Ltap between raw and propagated CAM.
  3. **Clue-based CAM (CB-CAM):** pseudo-label = ReLU(max sim to positive prototypes − max sim to negative prototypes) per pixel, replacing classifier-weight CAMs.
- Total loss: L = Lcls + Laux_cls + 0.01·Lcbl + 0.015·Ltap. Segmentation net (TSViT + decoder) trained on CB-CAM pseudo-labels with standard fully supervised recipe.

## Data & labels
- Only image-level crop categories during pseudo-label generation (derived from PASTIS masks by patch majority); segmentation network uses generated pseudo-labels, never ground truth masks. Temporal embeddings carry more discriminative info than spatial ones (CAM ablation: temporal CAM mIoU 68.3 vs spatial 66.7 vs fused 69.5).

## Results
- Pseudo-label quality (PASTIS train): Exact 84.1% OA / 75.6% mIoU vs best adapted WSSS baseline 82.4/75.6→ baseline CAM 81.2/69.5; natural-image WSSS methods cap at ~53.2 mIoU on SITS.
- Final segmentation (PASTIS test, TSViT): 80.3% OA / 61.8% mIoU with weak labels = **95% of the fully supervised TSViT oracle (83.4/65.1)**; beats best adapted natural-image WSSS modules by +3.2 OA / +4.1 mIoU.
- Ablations: Lcbl alone +1.2 OA/+2.8 mIoU; +Ltap → 83.0/73.4; +CB-CAM → 84.8/75.6. Low-level color/intensity affinity helps far less than temporal-aware affinity (cloud/shadow noise). Np=2 prototypes optimal; more prototypes hurt (under-activation).

## What transfers to our thesis
- Demonstrates that temporal embeddings dominate spatial embeddings for crop-related SITS discrimination — supports our design choice of temporally-driven SSL on Landsat 16-day series rather than heavy spatial modeling.
- The prototype/contrastive regularization on temporal embeddings (few prototypes per class, momentum updates) is a lightweight mechanism that could be repurposed for label-free stress states: cluster field-level temporal embeddings into "normal vs stressed-season" prototypes and use prototype-similarity gaps as anomaly scores.
- Temporal-to-class attention extraction from a temporal encoder is a free XAI signal ("which acquisition dates matter") — directly reusable for our XAI requirement on Landsat time-series stress models (which dates/droughts drive the detection), without extra compute.
- The 95%-of-full-supervision result is a citable motivation for label-efficient pipelines on small in-field datasets where stress labels are absent.
- Affinity propagation in temporal embedding space suppresses cloud/shadow noise — relevant to Landsat cloud-contaminated 16-day series.

## Limitations / caveats
- Still weakly supervised (image-level labels required), not label-free; task is crop-type segmentation, not stress/anomaly detection.
- Sentinel-2 10 m, 10–13 bands; no thermal/LST modality; 8×RTX3090 training for the classification net (heavy relative to in-field constraints).
- CAM edge/boundary delineation remains weak (acknowledged); CB-CAM quality depends on CAM filtering thresholds (0.2/0.4) tuned per dataset.
- PASTIS fold-1 only; Germany used for pseudo-label comparison, generalization across years/regions not tested.

## Key numbers to quote in lit review
- Weakly supervised SITS segmentation reaches 95% of fully supervised TSViT performance (61.8 vs 65.1 mIoU, PASTIS).
- Natural-image WSSS methods fail on SITS: ≤53.2 mIoU vs 75.6 mIoU pseudo-label quality for Exact.
- Temporal dense embeddings beat spatial ones for CAM quality (68.3 vs 66.7 mIoU).
- Temporal-aware affinity >> low-level cue affinity for denoising (73.4 vs 71.8 mIoU) — cloud/shadow noise argument.



---


## FILE: 2026 - Adaptive DL Framework for Multi-Temporal Crop and Drought Stress Monitoring, Sentinel-2 CNN+ViT (Sci Rep).md
# An adaptive deep learning framework for multi-temporal crop and drought stress monitoring in precision agriculture

- **Full citation**: Yasmeen, G. & Ahmed, T. (2026). "An adaptive deep learning framework for multi-temporal crop and drought stress monitoring in precision agriculture." Scientific Reports (Article in Press), DOI: 10.1038/s41598-026-70304-z. Integral University, Lucknow, India. Code/data: Zenodo DOI 10.5281/zenodo.21470565 (MIT license).

- **Problem & setting**: Village-scale (190.81 ha, Haldharmau, Gonda District, Uttar Pradesh, India — subtropical, ~1552 mm rain, cropping intensity 157%, crops incl. paddy, wheat, mustard, maize, sugarcane) crop-mask plus crop-stress and drought-stress mapping across three Rabi seasons (Jan-Jun 2023, 2024, 2025). Monthly Sentinel-2 L2A imagery (10 m, pre-processed in SNAP v10: atmospheric/radiometric/geometric correction, resample to 10 m, reproject). 2024 = development, 2023 = testing, 2025 = validation.

- **Method** (supervised pipeline; no SSL): (1) Compute NDVI (B8/B4), NDWI (B8-B12)/(B8+B12), PSSR (B8/B4) index images; layer-stack the three as classification input. (2) Hybrid CNN+ViT land-cover classifier into 4 classes (crop, urban, water, bare soil): CNN with three conv layers (32/64/128 filters, ReLU, max-pool) for local features + ViT encoder with 4 MHSA heads and 2 encoder blocks for global context; 64x64 patches, 10 "spectral channels", Adam lr 1e-4, batch 32, 50 epochs, cross-entropy loss, flip/rotation augmentation, early stopping patience 10. (3) Build binary cropland mask (crop=1, else 0). (4) Stress maps by fixed index thresholds on cropland pixels only: crop stress = 0.2 < NDVI <= 0.5 stressed, NDVI > 0.5 healthy; drought stress = NDWI < 0.2 stressed, NDWI >= 0.2 healthy. (5) Monthly percentage statistics, macro-averaged precision/recall/F1/specificity, and year-level Mean Stress / SD / Coefficient of Variation.

- **Data & labels**: 18 Sentinel-2 L2A scenes (6 per year, Jan-Jun 2023/2024/2025, tile T44RNR). Ground-truth samples from field visits in all three years, manually digitized as pixel-level samples for supervised classification of the 4 land-cover classes. Stress labels are NOT learned — they come purely from fixed NDVI/NDWI thresholds applied to the classified crop mask.

- **Results**: CNN+ViT overall classification accuracy 89.64% (2023), 88.39% (2024), 90.42% (2025), Kappa > 0.7, outperforming SVM, MLE, NN, K-means, CNN, U-Net, CNN+U-Net baselines (Fig. 5, exact baseline numbers only as relative comparison). Macro-averaged: 2023 P=85.31/R=81.56/F1=81.25/specificity=93.87%; 2024 76.24/79.74/76.49/93.31%; 2025 75.98/74.00/73.70/91.17%. Stress dynamics: 2023 drought stress peaked 61.43% in April; 2024 milder (39.28% April, 42.58% June); 2025 earliest and most severe (36.59% March, 53.22% April, 46.56% May). Year-level mean stress 26.54% (2023), 23.01% (2024), 32.48% (2025); CV 67.7/52.82/47.20%. Stress patterns consistent with IMD heatwave/monsoon-delay reports.

- **What transfers to our thesis**:
  - Demonstrates the widely used threshold-based stress protocol (NDVI 0.2-0.5 stressed; NDWI < 0.2 water-stressed) on cropland masks — a cheap, label-free "pseudo-ground-truth" recipe that could generate weak supervision or evaluation proxies for sugarcane stress when in-situ labels are scarce; but for our thesis it is exactly the kind of fixed-threshold labeling an SSL approach should replace/generalize.
  - NDVI+NDWI combination separates "greenness stress" from "water/moisture stress" — mirrors our optical + LST (CWSI/ETa) multi-signal design; supports the argument that vegetation and water signals are complementary for stress detection.
  - The 4-class crop-mask-first-then-mask-stress pipeline is a direct analog to our parcel/field masking before stress analysis on Landsat series.
  - Cross-year consistency check (same thresholds/model 2023-2025) is a concrete evaluation protocol template for our cross-year Landsat experiments, though here no retraining was done — threshold transfer, not model transfer.
  - Village-scale single-region setup (190 ha) underlines the need for methods that generalize beyond one scene — our cross-year, multi-product, lightweight SSL models address this.

- **Limitations / caveats**: Fully supervised classifier (field-visit labels); stress thresholds are fixed, crop- and stage-agnostic (NDVI 0.2-0.5 conflates early-growth sparse canopy with stress; April "stress" is largely harvest/senescence, not physiological drought); single village, single crop season (Rabi wheat focus), no in-situ validation of the stress maps themselves (only consistency with meteorological reports); 2D per-image classification, no temporal modeling of the series; no LST/energy balance; classification metrics degrade on unseen years (F1 81% -> 74%); no comparison against temporal or SSL methods.

- **Key numbers to quote in lit review**:
  - CNN+ViT land-cover accuracy 88.4-90.4% (Kappa > 0.7) over 3 years, beating CNN, U-Net, CNN+U-Net, SVM, RF-type baselines.
  - NDWI-based drought stress peaked at 61.4% (2023), 39.3% (2024), 53.2% (2025) of cropland in April.
  - Year-level mean stress rose from 23.0% (2024) to 32.5% (2025) — stress severity ranking matched IMD heatwave reports without any stress ground truth.
  - Fixed thresholds only: NDVI 0.2-0.5 = stressed crop; NDWI < 0.2 = drought-stressed crop.



---


## FILE: 2026 - Crop Type Mapping in the Pre-Sentinel Era - Variable-Length Landsat Time-Series + SITS-BERT (Frontiers Remote Sensing).md
# Crop type mapping in the pre-Sentinel era using variable-length Landsat time-series and self-supervised learning

## Full citation
Wijesingha, J., & Beila, I. (2026). *Crop type mapping in the pre-Sentinel era using variable-length Landsat time-series and self-supervised learning*. Frontiers in Remote Sensing 7:1782148. DOI 10.3389/frsen.2026.1782148

## Problem & setting
- Task: crop-type mapping with **Landsat-only** satellite image time series (L-SITS) for the pre-Sentinel era (before 2014), where no 5–10-day revisit data exist. Two German districts (Ammerland, Vechta; Lower Saxony), 2010–2018 (2012 excluded due to cloud/Landsat 7-only gap).
- Input per field: variable-length series (5–25 observations/season, March–October) from Landsat 5/7/8 Collection-2 Level-2 SR; 6 bands (blue, green, red, NIR1, SWIR1, SWIR2) + 4 VIs (NDVI, EVI, OSAVI, NDMI) + day-of-year encoding. Field polygons ≥0.9 ha (≥10 Landsat pixels) from IACS data; ~27.5k fields/year. Classes: CTL1 (4 classes) and CTL2 (9 classes).
- Core problem: supervised models need fixed-length series (padding/truncation distorts sparse Landsat data) and labels are scarce; SSL + transformer handles variable length and reduces label needs.

## Method
- **SITS-BERT (Yuan & Lin 2021) re-implemented on Landsat:** observation embedding (value array + DoY positional encoding — DoY enables cross-year transfer) + standard transformer encoder (max length 64, 10 features, 8 attention heads, batch 256, lr 1e-4).
- **SSL pretext:** random observations are selected, noised/corrupted, and the model must reconstruct original values from the remaining sequence context; MSE loss between reconstructed and true corrupted values. Pre-trained on 5 years of unlabeled L-SITS (2011, 2013, 2014, 2016, 2017), 50 epochs; best model epoch 49, train MSE 0.01639, val MSE 0.01356.
- Fine-tuned with a classification head: Case I = single-year (2015, 28,176 field-observations), Case II = 3 years (2014–2016, 84,139). Baseline: Random Forest on fixed-length bi-monthly median series (40 features).
- Temporal transfer tested both directions: Scenario I (past: 2010–2011) and Scenario II (future: 2017–2018).

## Data & labels
- Labels: IACS/Government crop-declaration polygons (supervised fine-tuning only; pretraining label-free). Variable-length series preserve all cloud-free acquisitions (RF used 5–17% fewer data points due to fixed-length reconstruction).

## Results
- Case I (single year): SITS-BERT CTL1 OA 0.833 (past) / 0.784 (future) vs RF 0.752 / 0.724; CTL2 OA 0.759 / 0.644 vs RF 0.702 / 0.652. SSL-BERT clearly beats RF when labels/observations are limited.
- Case II (3 years): CTL1 OA 0.855 / 0.807; CTL2 0.771 / 0.725. Multi-year fine-tuning lifts worst-case CTL2 OA from 0.644 → 0.725 (~16% relative). With 3 years, RF narrows the gap or wins CTL2 (0.789/0.771).
- Accuracy vs number of observations: CTL1 accuracy >80% for ≥7 observations; even 5–6 observations stay usable (67–70%); worst cases trace to seasonally bunched acquisitions (5 obs all in July).
- Per-class: winter crops F1 0.909–0.941; maize F1 0.893–0.933; hard classes: winter wheat vs winter cereals, root crops/vegetables merged class (merging for sample size did not help).

## What transfers to our thesis
- Closest architectural template in this batch for our setting: **Landsat 16-day variable-length field-level time series + BERT-style masked/reconstruction SSL pretraining + lightweight fine-tuning head** — exactly our optical sensor, temporal density (5–25 obs/season matches Landsat-7/8 dual availability), and DoY positional encoding trick for cross-year transfer.
- Quantifies the cross-year transferability problem on Landsat: performance drops from training year to past/future years (0.855 → 0.807 CTL1, 3-year training), and multi-year fine-tuning mitigates — direct evidence for our cross-year model design (train on multiple years, evaluate on held-out years).
- Shows DoY-based temporal encoding (rather than index positions) is the mechanism that makes single-year-trained transformers transferable across years — adopt in our encoder.
- Accuracy degrades gracefully with sparse observations (>80% at ≥7 obs), supporting our premise that label-free monitoring is feasible with cloud-limited Landsat density.
- Sugar context: sugarcane multi-year ratoon cycles are analogous to their multi-year fine-tuning benefit; their case II design maps to our cross-year sugarcane model.

## Limitations / caveats
- Downstream task is supervised crop-type classification with IACS labels; SSL used only for pretraining, not for label-free anomaly/stress detection.
- Moderate accuracies (CTL2 0.64–0.78) well below Sentinel-2 equivalents (SITS-BERT original ~0.9+); sparse 16-day revisit is the bottleneck.
- No thermal band/LST; 30 m pixels force ≥0.9 ha field minimum — smallholder sugarcane plots may be excluded.
- 2012 single-satellite year unusable — our thesis must plan for degraded-years robustness.
- Two districts, temperate crops; no salinity/water stress, no arid region.

## Key numbers to quote in lit review
- First transformer-SSL application to Landsat-only SITS for crop mapping: OA 0.78–0.85 (4-class) and 0.64–0.78 (9-class) across single/multi-year and past/future transfer.
- Multi-year fine-tuning raises worst-case 9-class OA by ~16% relative (0.644 → 0.725).
- SITS-BERT with single-year labels beats RF on fixed-length series (CTL1: 0.833 vs 0.752 OA, past-year transfer).
- Variable-length Landsat series contain 5–25 cloud-free observations per March–October season; accuracy >80% for CTL1 with ≥7 observations.



---


## FILE: 2026 - DAS-SK - Lightweight Dual Atrous Separable + Selective Kernel CNN for Agriculture Semantic Segmentation (arXiv).md
# DAS-SK: An Adaptive Model Integrating Dual Atrous Separable and Selective Kernel CNN for Agriculture Semantic Segmentation

## Full citation
Chee, M. L., Akilan, T., Phalke, A. R., & Keisham, K. (2026). *DAS-SK: An Adaptive Model Integrating Dual Atrous Separable and Selective Kernel CNN for Agriculture Semantic Segmentation*. arXiv:2602.08168 [cs.CV] (preprint). https://arxiv.org/abs/2602.08168

## Problem & setting
- Task: supervised semantic segmentation of high-resolution agricultural/aerial imagery with an explicit accuracy-vs-efficiency objective for UAV/edge deployment.
- Benchmarks: LandCover.ai (25–50 cm/px, 5 classes, 512×512, 10,674 images), Varied Drone Dataset VDD (1.75–4.2 cm/px, 7 classes, 400 images), PhenoBench (0.1 cm/px, crop/weed/soil, 2,872 images at 1024×1024).
- Motivation: transformers beat CNNs in context modeling but are too heavy for real-time edge use; agricultural scenes have intra-class variability (phenology, illumination) that demands adaptive multi-scale receptive fields.

## Method (fully supervised — no SSL)
- **Architecture:** modified DeepLabV3 with dual backbone — main MobileNetV3-Large (2.894M params) + auxiliary truncated EfficientNet-B3 (first 6 blocks, 2.256M params) — fused 960-channel features feed an enhanced ASPP and a hierarchical decoder with multi-level skip connections.
- **DAS-SKConv module:** parallel atrous separable branch (depthwise atrous 3×3 + pointwise) and standard atrous 3×3 branch, concatenated; then Selective-Kernel attention — softmax channel/branch re-weighting over multiple receptive fields (adaptive kernel selection).
- **Enhanced ASPP:** 1×1 conv + six DAS-SKConv branches with dilations {4, 8, 12, 18, 22, 26} + strip pooling branch (long-range horizontal/vertical context for row-structured vegetation); concatenated and compressed to 256 channels.
- **Loss:** L_total = CE + Dice + Focal + Lovász (hard-sample weighting + direct mIoU optimization). SGD lr 0.001, cosine annealing, batch 8, early stopping patience 30.
- Efficiency metric defined: Efficiency = Diff_mIoU / (log(Params) · GFLOPs) × 100%.

## Data & labels
- Fully supervised with dense pixel masks on three public datasets; strong augmentation (flips, 90° rotations, ShiftScaleRotate, color jitter).

## Results
- LandCover.ai: 86.25% mIoU with 10.678M params / 11.25 GFLOPs / 40 FPS — second only to a 193.5M-param Ensemble UNet (88.02), best efficiency (49.70%); beats SegFormer MiT-B2 (84.40, 27.5M) and DeepLabV3 ResNet101 (83.00, 58.6M).
- PhenoBench: best mIoU 85.55% (crop IoU 94.16, weed 63.15), edging DeepLabV3+ ResNet101 (85.52) with ~4× fewer params.
- VDD: 79.45% mIoU vs Mask2Former 83.21 (47M params) — again best efficiency.
- Headline claim: up to 21× fewer parameters and 19× fewer GFLOPs than top transformer competitors.
- Ablation (LandCover.ai, 12 stages): baseline MobileNetV3 DeepLabV3 82.77 mIoU; DAS-Conv cut params −31% and GFLOPs −36% while adding +0.31 mIoU; auxiliary backbone +0.99; SK attention +0.28; parallel post-ASPP conv +0.49; ShiftScaleRotate augmentation +0.46 → final 86.25.

## What transfers to our thesis
- Directly supports the "lightweight multi-product in-field model" pillar: a ~10.7M-param CNN matches or beats 27–194M-param transformer baselines, at 40 FPS — evidence that in-field sugarcane stress models need not be transformers, and that a compact decoder design can run on edge hardware at field sites.
- The ablation quantifies which efficiency tricks actually pay off: atrous separable convolutions (−31% params, +accuracy), strip pooling for row-structured vegetation (sugarcane rows!), SK adaptive receptive fields. Strip pooling for elongated row crops is specifically transferable to sugarcane field segmentation/stress mapping.
- Multi-term loss (CE+Dice+Focal+Lovász) recipe is reusable for class-imbalanced stress/anomaly masks.
- NOTE: this paper is supervised, not SSL, and is single-image (no time series) — cite it as evidence for the lightweight-deployment constraint, not for label-free learning. Its authors themselves name SSL and domain adaptation under limited labels as future work.

## Limitations / caveats
- No SSL, no time series, no spectral-band time-series modeling — orthogonal to our core contribution; only the efficiency story transfers.
- RGB/high-res aerial or drone imagery, not satellite multispectral; no thermal/LST.
- Memory rises ~3× when the auxiliary backbone is added (1,549 MB vs 574 MB); SK module cost is non-trivial.
- Efficiency metric is custom (self-defined) — comparisons across papers are not standardized.
- VDD is a mixed urban/drone dataset, only weakly "agricultural"; PhenoBench weed IoU (63.15) shows fine-grained discrimination remains hard.

## Key numbers to quote in lit review
- 10.7M params / 11.25 GFLOPs / 40 FPS at 86.25% mIoU (LandCover.ai) — up to 21× fewer params, 19× fewer GFLOPs than transformer competitors.
- DAS-Conv swap: −31% parameters, −36% GFLOPs, +0.31 mIoU.
- PhenoBench best mIoU 85.55%, crop IoU 94.16 with ~4× fewer parameters than DeepLabV3+.
- Strip pooling improves mIoU +0.11 for row-structured agricultural patterns.



---


## FILE: 2026 - Hyper-Arid Seasonal Crop Mapping - SSL + Pseudo-Labels, Sentinel-1-2 2020-2024 (Frontiers in AI).md
# Mapping seasonal dynamics of forage and cereal crops in a hyper-arid environment using Sentinel-1 and Sentinel-2 time series

## Full citation
Alwahas, A., Johansen, K., Rodriguez, J., & McCabe, M. F. (2026). *Mapping seasonal dynamics of forage and cereal crops in a hyper-arid environment using Sentinel-1 and Sentinel-2 time series*. Frontiers in Artificial Intelligence 9:1803320. DOI 10.3389/frai.2026.1803320

## Problem & setting
- Task: seasonal, field-scale crop-type mapping (4 functional groups: fallow, cereal, vegetables, forage) in a label-scarce, irrigation-driven hyper-arid region — Wadi Al-Dawasir, Saudi Arabia (4,560 km², <50 mm rain/yr, center-pivot irrigation on non-renewable groundwater), 2020–2024.
- Challenges: irrigation (not rain) drives phenology so crop calendars shift between fields/years; field labels scarce (300 center pivots surveyed in 4 campaigns, 2023–2024); arid irrigated systems underrepresented in global products (WorldCereal, GFSAD).
- Data: biweekly (15-day median) stacks of Sentinel-2 NDVI + Sentinel-1 VH/VV ratio (dB), temporally aligned ±6 days, seasons Nov 2022–Oct 2024, tiles 128×128 with T=12 timesteps; NDVI-only vs NDVI+SAR ablation.

## Method
- **SSL pretraining (MAE-style, temporal masking):** per modality, 3-layer spatial encoder (conv + group norm + GELU) per frame → adaptive average pooling to a coarse spatial grid → spatiotemporal tokens + positional encodings → random **50% temporal masking** → transformer temporal encoder → modality-specific decoder reconstructs masked timesteps with a spatial prior (mean of encoder features over unmasked frames), upsampled to 128×128. Huber loss (δ=0.5) computed only on masked frames, summed over NDVI and VH/VV channels (L = L_NDVI + L_VH/VV). ~500 epochs, Adam lr 1e-4, batch 4, 11,721 train / 2,931 val tiles. Pre-training scope ablation: single season (S1) vs all seasons (S4).
- **Pseudo-labels:** K-means (K=8, chosen by scanning K=4–16 with label agreement + cluster purity/Shannon entropy) on full-season NDVI+VH/VV pixel series, restricted to agricultural mask (seasonal median NDVI > 0.5); clusters assigned to crop groups by majority of verified field labels; connected regions ≥100 px (0.1 ha) kept, rest ambiguous/unlabeled. Used only as auxiliary supervision in fine-tuning — never for pretraining, validation, or model selection.
- **Fine-tuning:** DeepLabV3+ segmentation (class-weighted CE, early stopping, grad clipping 1.0) and RF (600 trees, class-balanced) on frozen MAE encoder embeddings.
- **Uncertainty:** normalized predictive entropy maps (low-confidence flag ≤0.50 confidence), Bernoulli-variance-based uncertainty on area totals.

## Data & labels
- Ground truth: 300 center-pivot fields, 4 GPS field campaigns (winter/summer 2023, 2024); label QC — every "fallow" label cross-checked against the S2 NDVI trajectory and removed if the visit-day observation contradicted the seasonal signal (e.g., field idle only on visit day).

## Results
- Best config (S4-P, DeepLabV3, NDVI+VH/VV): mIoU 0.80, F1 0.88, OA 0.97. Pseudo-labels are the dominant factor: mIoU 43–45 → 77–80 (+~35 points), F1 55–56 → 86–88; pretraining scope (1→4 seasons) adds only ~2 points.
- **Optical-only ablation collapses: mIoU 0.35, F1 0.32, OA 0.64 vs 0.80/0.88/0.97 with SAR** — NDVI alone cannot separate crops in irrigated arid systems.
- Per class: fallow mIoU 0.95/0.97, forage 0.815/0.85, cereal 0.71 (F1 0.85), vegetables worst 0.506–0.52 (main confusion vegetables→cereal due to overlapping single-peak NDVI).
- External FM baselines under same protocol underperform: ScaleMAE decoder-only + field labels mIoU 46.8, Prithvi-EO-1.0 42.5 — far below the local MAE (80.1); pseudo-labels actually *hurt* the external FMs (mIoU ~29–31), showing pseudo-label benefit is representation/task-aligned, not universal.
- DeepLabV3 slightly beats RF (80.1 vs 77.2 mIoU). Uncertainty concentrated on vegetables, post-cut forage, field edges. Mapped area trends: forage peaked 17,441 ha (summer 2022) → 8,775 ha (2024); cereal rose to 15,076 ha (winter 2024).

## What transfers to our thesis
- Same climate/drought-relevant setting as our sugarcane work: irrigation-driven, water-stressed agriculture where rainfall-based calendars fail — validates our full-time-series (rather than fixed-calendar-date) approach to stress detection.
- The **temporal-masking MAE on biweekly NDVI+SAR time-series tiles** is architecturally the closest SSL recipe in this batch to a Landsat 16-day optical+LST version: swap S2 NDVI→Landsat NDVI/NDRE, VH/VV→LST, 15-day→16-day compositing. Their finding that masking-based temporal pretraining works with only ~12 timesteps/season is directly encouraging for Landsat's sparser series.
- Pseudo-label augmentation via unsupervised K-means clustering of seasonal time series (+35 mIoU) is a cheap semi-supervision strategy for our label-scarce sugarcane setting — cluster field temporal profiles first, expand supervision.
- Strong evidence for multimodality: NDVI-only ablation halves performance; supports our optical+LST (and potentially SAR) fusion claim for stress detection — single optical index streams are insufficient in irrigated arid fields.
- Entropy-based confidence maps + low-confidence flagging is a practical XAI/QC layer we can adopt for flagging uncertain stress predictions in-field.
- Negative result worth citing: external geospatial FMs (Prithvi, ScaleMAE) transfer poorly to a local hyper-arid task — supports training small local SSL models rather than fine-tuning giant FMs for in-field deployment.

## Limitations / caveats
- Crop-type classification (4 functional groups), not stress/anomaly detection; requires field labels for fine-tuning and pseudo-label cluster assignment.
- NDVI-only input choice justified pragmatically, not optimized (authors admit no full-multispectral comparison).
- Vegetables mIoU ~0.5 — phenologically overlapping classes remain unreliable; the same problem will affect separating mild vs severe stress stages.
- Only 300 labeled pivots from 2 years used for fine-tuning/validation; area uncertainty ignores spatial error correlation.
- Sentinel 5–12 day data, not 16-day Landsat; SAR VH/VV is unavailable in a Landsat-only scenario (Landsat has no SAR), so their multimodality gain needs re-derivation with LST/thermal as the second modality.

## Key numbers to quote in lit review
- SSL MAE + pseudo-labels + optical–radar: mIoU 0.80 / F1 0.88 / OA 0.97 vs NDVI-only mIoU 0.35 — a 2.3× mIoU drop without the second modality.
- Pseudo-label augmentation adds ~35 mIoU points; pretraining scope (1→4 seasons) adds only ~2.
- Local MAE (80.1 mIoU) crushes Prithvi-EO-1.0 (42.5) and ScaleMAE (46.8) under identical fine-tuning protocol.
- Label QC by NDVI-trajectory cross-checking removed visit-day-only "fallow" mislabels — a reusable label-cleaning practice.



---


## FILE: 2026 - Label-Free Deep Learning with Feature Adaptation for Crop Anomaly Detection on Small Datasets (MDPI Agriculture 16-8-854).md
# Label-Free Deep Learning with Feature Adaptation for Crop Anomaly Detection on Small Datasets

## Full citation
Yang, M.-D., Lee, T.-H., Tseng, H.-H., Su, T.-C., & Hsu, Y.-C. (2026). *Label-Free Deep Learning with Feature Adaptation for Crop Anomaly Detection on Small Datasets*. Agriculture 16(8), 854. DOI 10.3390/agriculture16080854

## Problem & setting
- Task: label-free (unsupervised) image-level anomaly detection + pixel-level localization of crop diseases/defects, adapted from industrial inspection, explicitly targeting **small datasets** (100–200 normal training images).
- Data: MVTec AD (industrial benchmark, 15 classes), PlantVillage subsets (Apple, Arjun, Cherry, Grape, Pongamia, Potato), Coffee Leaf Disease (79 train/51 test), and a custom real-world Sweet Potato dataset (157 train / 105 test; 5 defect types: black rot, southern blight, crack, mechanical damage, rat bite) collected in controlled factory conditions (RGB, vertical 450 mm).
- Motivation: agricultural intra-class variance from natural growth makes a pure "normal" baseline hard; supervised CNNs need thousands of labels.

## Method (EfficientAD — teacher-student + autoencoder, label-free)
- **Patch Description Network (PDN):** lightweight teacher distilled from ImageNet-pretrained WideResNet-101; deliberately narrow receptive field (33×33 px) for local texture anomalies; input 256×256.
- **Student–teacher (local anomalies):** student (same architecture, random init) trained to regress teacher features on normal-only images; anomaly signal = squared difference D(c,w,h); hard-example mining loss with p_hard=0.999 quantile + penalty term on out-of-distribution ImageNet samples to stop the student imitating the teacher off-target.
- **Autoencoder (logical/global anomalies):** AE reconstructs teacher feature maps (L_AE); student's extra channels predict AE output (L_STAE) to suppress AE false positives. Final anomaly map = quantile-normalized combination of local (T−S) and global (S′−A) maps; image score = max.
- Training: Adam lr 1e-4, 70,000 iterations, batch 1, no data augmentation. Metrics: AUROC (image level), AUPRO (pixel level, FPR limit 0.3).
- Background preprocessing strategies tested on Sweet Potato: Original, Background-Removed black (BGRM), Background-Replaced with out-of-distribution pure green (BGRP-G, RGB 0,255,0).

## Data & labels
- Only normal (defect-free) images used in training; disease/defect masks used solely for evaluation (AUPRO). Truly label-free training paradigm.

## Results
- MVTec AD mean AUROC 98.6%; PlantVillage up to 100% (Pongamia), Potato 99.0%, Coffee leaf 99.8%; Sweet Potato AUROC 88.9 (original) → 91.0 (BGRM) → **99.5 (BGRP-G)**.
- AUPRO localization much weaker: Sweet Potato 47.1 → 48.3 → 61.9; Coffee 75.3; per-defect: crack 82.3, southern blight 83.9 (BGRP-G), black rot only 37.7 (BGRM) → 47.6 (BGRP-G), mechanical damage 76.3, rat bite 72.2.
- Baseline comparison: EfficientAD dominates AnoGAN, Pix2Pix, InTra, Teacher–Student across datasets (e.g., MVTec Grid: 99.8 vs 50.9 best baseline).
- Deployment: S model 8.06M params / 75.94 GFLOPs / 104 MiB GPU; latency 1.153 ms (867 FPS RTX 6000 Ada), 476 FPS RTX 5000 Ada; M model 20.74M, 443 FPS.
- Failure analysis: dark black-rot boundaries suppressed by pure-black background mask (intensity collision); out-of-distribution green mask preserves dark lesion edges. Blurry/gradual lesion boundaries are the main weakness; t-SNE/DBSCAN shows "normal" crop features scatter into many sub-clusters — natural biological variance is treated as outliers, explaining the image-level vs pixel-level gap.

## What transfers to our thesis
- Core paradigm directly relevant: **train on normal-only fields, flag anomalies without any stress labels** — this is exactly our label-free sugarcane stress detection premise. EfficientAD's teacher-student + AE hybrid is a candidate lightweight architecture for field-level anomaly scoring on Landsat time-series features (embed field time series instead of image patches).
- The background-interference finding transfers to remote sensing: in satellite imagery, soil/road/water background consumes AE capacity. Their fix — replace background with out-of-distribution constant instead of black — is a concrete preprocessing trick for masking non-crop pixels (field mask with OOD fill) before anomaly modeling.
- Quantified caveat to carry into our thesis: image-level AUROC near-perfect (99.5) while pixel AUPRO only ~62 even after background correction — we should expect robust field-level "stressed vs normal" flags but weaker within-field localization, and should report AUPRO-style metrics, not just AUROC.
- Small-data claim (near-perfect AUROC from 100–200 normal samples, no augmentation) supports feasibility on limited sugarcane in-field datasets.
- 8–21M params and >400 FPS confirm edge deployment viability of student-teacher anomaly models — aligns with our lightweight multi-product model requirement.
- The dark-lesion/background-collision lesson generalizes: anomaly signals must not share feature space with masked regions (relevant when masking clouds/shadows in Landsat series).

## Limitations / caveats
- RGB close-range imagery of leaves/tubers, not satellite time series; no temporal dimension, no multispectral/LST — transfers only at the methodological level.
- Pixel localization weak on blurry/gradual symptoms (black rot 37.7 AUPRO) — water/salinity stress in sugarcane is exactly such a gradual signal; expect the same difficulty.
- Background strategies require a segmentation mask; for satellite data, field-boundary masks must come from somewhere (cadastral or SSL segmentation).
- Sweet Potato dataset captured under controlled factory lighting — not true field variability; specular reflections caused false activations even so.
- Needs a strictly "normal" training set — hard in agriculture where subclinical stress is widespread (authors note this inherent tension).

## Key numbers to quote in lit review
- Label-free EfficientAD reaches up to 100% AUROC on crop disease datasets with only 100–200 normal training images and no augmentation.
- Background-replaced (OOD green) preprocessing lifts Sweet Potato AUROC 88.9→99.5% and AUPRO 47.1→61.9%.
- Image-level vs pixel-level gap: ~99.5 AUROC but only ~62 AUPRO even after background correction — localization of gradual lesions remains the open problem.
- Efficiency: 8.06M params, 1.153 ms/image, 867 FPS (RTX 6000 Ada).
- EfficientAD mean AUROC 98.6% on MVTec AD vs ≤98.8 max for AnoGAN/Pix2Pix/InTra baselines (many below 60%).



---


## FILE: 2026 - Long-Term Analysis-Ready Rice Phenology Dataset, Yangtze River Plain 1981-2024 (Data in Brief) [BONUS].md
# A long-term, analysis-ready dataset of rice phenology in middle and lower reaches of the Yangtze River Plain of China from 1981 to 2024 [BONUS]

- **Full citation**: Zhang, Q.-J. & Wu, D.-L. (2026). "A long-term, analysis-ready dataset of rice phenology in middle and lower reaches of the Yangtze River Plain of China from 1981 to 2024." Data in Brief 69:113310, DOI: 10.1016/j.dib.2026.113310. Data: https://doi.org/10.57760/sciencedb.25297. China Meteorological Administration.

- **Problem & setting**: Provide a public, multi-decadal (44 years, 1981-2024), station-based rice phenology dataset with full growth-cycle coverage for the Middle and Lower Yangtze River Plain (MLYRP, >1/3 of China's rice area; Jiangsu, Zhejiang, Anhui, Jiangxi, Hubei, Hunan, Shanghai), designed for crop-model validation, climate-impact meta-analysis, and remote sensing product verification. Ground observations every 2 days (daily at heading/flowering) by 100+ certified observers under the national agrometeorological observation specification.

- **Method** (data paper; no ML/SSL): Pipeline: (1) collect 11 phenological stage dates per station-year — sowing, emergence, trefoil, transplanting, regreening, tillering, jointing, booting, heading, milking, maturity — converted to day-of-year (DOY), plus 3 growth-period lengths (SO-JO, JO-MA, SO-MA); (2) QC: automated completeness/duplication/range checks, ±3σ outlier flagging, then expert arbitration with spatial-coherence checks against adjacent stations and original logbooks (genuine climatic extremes retained); hierarchical gap-filling (adjacent years, then neighboring stations); (3) kernel density estimation (Scott's rule; Silverman used only as sensitivity check) and OLS univariate linear regression of DOY/GLs on year, with decadal trends = 10*k, two-tailed t-test at α = 0.05. Outputs: 2,432 high-resolution (1200 dpi) KDE/trend JPEGs (2.82 GB) + machine-readable Excel with slope, intercept, R2, mean square, F, p per station and variable.

- **Data & labels**: 95 CMA agrometeorological stations, 1981-2024, single-cropping and double-cropping late rice; standardized phenological criteria per stage (e.g., maturity = >80% (indica) / >90% (japonica) grain coloration); open access (CC-BY-NC). No satellite data used; purely in-situ phenology.

- **Results**: All 11 stages show significant advancement over 44 years: sowing -2.2 d/decade (R2=0.428), emergence -2.9 (R2=0.526), trefoil -2.8, transplanting -4.5 (R2=0.694), regreening -4.3, tillering -6.0 (R2=0.730), booting -2.9, heading -3.0, milking -1.3, maturity -2.1 d/decade (all P<0.01; jointing -0.4 d/decade, R2=0.008). Growth lengths: SO-JO extended +2.3 d/decade (R2=0.206), JO-MA shortened -1.9 d/decade (R2=0.220), SO-MA no significant trend. Mode dates: sowing DOY 90 through maturity DOY 201; modal GLs: SO-JO 61 d, JO-MA 50 d, SO-MA 111 d. Validation: leave-one-out cross-validation of the 44-year trend shows slopes stable to <±0.1 d/decade; p<0.01 for 78% of phenological stages.

- **What transfers to our thesis**:
  - Not directly methodologically relevant (no SSL, no satellite imagery) but demonstrates the value of long-term, ground-truthed phenological sequences as independent validation targets — the same role ground phenology could play for validating our unsupervised sugarcane phenology/stress staging on Landsat series.
  - Its explicit reuse case "validate long-term phenological trends derived from remote sensing products" supports our thesis framing that label-free SSL representations can be evaluated against sparse, independent agronomic observations (phenology dates, growth-stage lengths) rather than dense labels.
  - The ±3σ + expert-arbitration QC protocol and LOOCV trend-stability check (slopes stable <±0.1 d/decade) is a template for robustly assessing whether our SSL-derived temporal signals capture genuine interannual stress/anomaly signals vs observation noise.
  - Reinforces the phenology-stress link: stage-timing shifts (transplanting -4.5 d/decade, tillering -6.0 d/decade) are among the strongest climate fingerprints — argues that stress detection models should be phenology-aware (stage-conditional baselines), which motivates our sugarcane growth-stage conditioning.
  - Shows the reference phenomenon: growth-phase lengths (e.g., JO-MA -1.9 d/decade) respond to warming even when total season length does not — a caution that fixed-calendar windows in our Landsat series analysis can mask or fake stress signals; stage-adaptive temporal sampling is preferable.

- **Limitations / caveats**: Station point data (95 sites), not gridded or pixel-level; no satellite data or ML component; manual gap-filling introduces imputation; rice-specific (indica/japonica) phenology definitions do not transfer to sugarcane; trend analysis is univariate OLS (no multivariate climate attribution); China-region specific.

- **Key numbers to quote in lit review**:
  - 95 stations x 44 years (1981-2024), 11 phenological stages + 3 growth lengths, openly available.
  - Significant phenological advancement: transplanting -4.5 d/decade, tillering -6.0 d/decade (both R2>0.64, P<0.01).
  - Pre-maturity growth phase (JO-MA) shortened by -1.9 d/decade while sowing-to-jointing extended +2.3 d/decade.
  - LOOCV slope stability <±0.1 d/decade; p<0.01 for 78% of stage-level trends.



---


## FILE: 2026 - Multi-Scale Deep Multi-Task Network - Crop Classification + Stress + Yield Anomaly (Elsevier).md
# A multi-scale deep multi-task network for integrated crop classification, stress detection, and yield anomaly estimation using Sentinel-1 and Sentinel-2 data

- **Full citation**: Makinde, A.S. & Msigwa, A. (2026). "A multi-scale deep multi-task network for integrated crop classification, stress detection, and yield anomaly estimation using Sentinel-1 and Sentinel-2 data." Hydrology Research 57:100023, DOI: 10.1016/j.hydrch.2026.100023 (open access). Edo State University, Nigeria / NM-AIST, Tanzania.

- **Problem & setting**: Joint crop classification (6 classes: sorghum, millet, maize, rice, cowpea, groundnut), 4-level stress detection (Severe Drought, Moderate Drought, Heat Stress, No Stress), and yield-anomaly regression for semi-arid smallholder rainfed agriculture in Kano State, Nigeria (43,285 km2, Sudan savanna, May-Oct growing season, 800-1000 mm rain, 0.5-2 ha fields). Data 2020-2024, monthly median composites May-Oct (6 time steps), sampled at 100 m via GEE.

- **Method** (supervised multi-task learning — no SSL): MS-DMTN, three-stream architecture, ~180,203 parameters. Inputs: 96-dim feature space = 48 optical (8 VIs — NDVI, EVI, NDWI, SAVI, GCI, NDRE, MSI, PSRI x 6 months), 12 SAR (VV, VH + VH/VV ratio, RVI, NDRI, cross-pol ratio x 6 months), 36 hydro-climatic (18 ERA5-Land: T2m/precip/volumetric soil moisture layer 1 x 6 months; 6 CHIRPS monthly totals; 12 baseline means + derived anomalies). Three modality-specific MLP encoders (optical 48->256->128->64, SAR/hydro 12|36->128->64, ReLU+BN+dropout 0.2-0.3); gated attention fusion: three independent sigmoid gates (64x192 each) conditioned on concatenated 192-dim context, element-wise modulation, projection to 128 then 96-dim shared representation; three decoders (96->64->32) for 6-class crop softmax, 4-class stress softmax, linear yield output. Weighted multi-task loss: L = 2.0*L_crop + 1.5*L_stress + 0.5*L_yield (sparse CE + CE + MSE). Adam lr 1e-3, batch 32, up to 250 epochs, early stopping patience 25, ReduceLROnPlateau (x0.5, patience 8).

- **Data & labels**: 5,000 stratified random GEE points -> 4,734 valid agricultural samples (NDVImax >= 0.15); 60/20/20 train/val/test split (2840/947/947), stratified by crop. Key novelty: stress labels derived independently of spectral inputs, purely from ERA5-Land soil-moisture anomalies and CHIRPS precipitation anomalies with percentile thresholds (Severe: SM anom < 15th pct AND precip anom < 20th pct; Moderate: SM < 35th OR precip < 20th; Heat: T2m > 75th pct without moisture deficit). Crop labels from multi-source decision tree (VIs + SAR stats + soil moisture); yield target = blended anomaly index 0.6*climate_yield + 0.4*spectral_yield (peak NDVI), normalized [-1,1]. Label independence verified: agreement between climate-based and spectral (MSI-quartile) stress labels only 25.7% (binary 69.8%, Cohen's kappa 0.17); NDWI-soil moisture correlation -0.021.

- **Results**: Crop classification 95.99% acc / F1 0.96 (ST-DNN 89.65%, RF 89.23%, MLP 71.07%); stress detection 87.33% acc / F1 0.88 (RF 78.35%, ST-DNN 65.26%, MLP 66.95%); yield R2 = 0.92, RMSE 0.11, MAE 0.08 (ST-DNN R2 0.91, RF 0.84, MLP 0.35). All differences statistically significant (McNemar / Wilcoxon, alpha 0.01). Per-class: groundnut F1 0.98, maize 0.97, millet 0.94, rice 0.91 (n=18), cowpea 0.87, sorghum 0.87 (n=28); stress: No Stress F1 0.93, Moderate Drought 0.88, Heat Stress 0.65, Severe Drought 0.39 (n=15). Ablation: Optical-only crop 96.52% but stress 85.85%, yield R2 0.86; Hydro-only stress 93.03% (exceeds full model 87.33%) and yield R2 0.90, crop only 74.76%; SAR-only crop 83.21%, yield R2 0.65; No-Gated-Fusion yield R2 0.86 vs full 0.92 (gating matters most for regression). External validation: yield anomaly Pearson r = 0.835 (NBS Kano) and 0.831 (FAOSTAT), each year r > 0.82; crop proportions cosine similarity 0.91-0.94 vs SPAM/LSMS-ISA; stress prevalence within +/-8.6% of FEWS NET IPC; 90.7% agricultural-land agreement vs ESA WorldCover; ~46.2% modeled stress prevalence consistent with IPC 5-yr trend.

- **What transfers to our thesis**:
  - The independently-derived, climate-based stress labeling protocol (soil-moisture + precipitation anomaly percentiles, NOT spectral indices) is directly reusable for sugarcane water stress: it avoids circular validation when inputs and labels both come from optical data — highly relevant to our label-free setting where we need credible evaluation proxies.
  - Quantifies the central role of moisture/hydrological data for stress detection (Hydro-only 93.0% vs Optical-only 85.9%) — supports our thesis that LST/ETa/soil-moisture-adjacent channels (not just VIs) carry the water-stress signal on Landsat.
  - Compact model: ~180K parameters with gated multi-stream fusion — direct evidence that lightweight multi-product architectures (optical + thermal/meteorology) are viable for in-field deployment, matching our "lightweight multi-product" requirement.
  - Gated attention fusion benefits regression-style continuous stress/yield targets most (+0.06 R2) while classification is robust to fusion choice — informs how to fuse Landsat optical + LST streams for continuous CWSI/ETa-style outputs.
  - Multi-task regularization: joint crop + stress + yield learning improved yield over single-task; supports our joint stress + phenology/anomaly multi-task design.
  - Monthly 6-step compositing is coarse — a caution: monthly aggregation missed heat-stress discrimination (F1 0.65) and flash droughts; argues for our 16-day Landsat cadence instead.

- **Limitations / caveats**: No SSL, no true temporal encoding (features are hand-composited monthly medians; authors propose temporal Transformer/3D-CNN as future work); yield target partially circular (40% weight on peak NDVI, an input-side feature — authors acknowledge inflated R2); labels from stratified random sampling + decision trees, not field surveys (source-product errors propagate); severe-drought class only 15 test samples; no LST; Sentinel-based (10 m) not Landsat; spatial sampling at 100 m; cross-year generalization not tested (single pooled 2020-2024 split).

- **Key numbers to quote in lit review**:
  - Hydro-only stream reaches 93.03% stress accuracy vs 85.85% optical-only and 87.33% full model — soil-moisture/precipitation anomalies dominate agricultural drought detection.
  - Climate-defined vs spectral-defined stress labels agree only 25.7% (kappa 0.17) — spectral-index-based stress labels are largely non-circular proxies for hydro-climatic stress.
  - Full three-stream model: 95.99% crop accuracy, 87.33% stress accuracy, yield R2 0.92 with only ~180K parameters.
  - Gated attention fusion adds +0.06 yield R2 (0.92 vs 0.86 concatenation) — adaptive weighting matters most for continuous targets.
  - Yield anomalies validated against official statistics at r = 0.83 (p = 0.04) across all study years.



---


## FILE: 2026 - Temporal Data Explainability in Remote Sensing for Agriculture - Systematic Review (SSRN).md
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



---


## FILE: 2026 Ahmad - Embedding NDRE Trajectories into Contrastive Learning - Label-Free Physiology-Aware Crop-Stress Staging (arXiv).md
# Embedding NDRE Trajectories into Contrastive Learning for Label-Free, Physiology-Aware Crop-Stress Staging and DSS Outputs (EigenCL)

## Full citation
Ahmad, S. (2026). *Embedding NDRE Trajectories into Contrastive Learning for Label-Free, Physiology-Aware Crop-Stress Staging and DSS Outputs*. arXiv (preprint). (Companion/extension of the author's 2025 EigenCL paper.) Note: no arXiv ID printed in the extracted text; author-affiliated preprint, single author (Brandt Group of Companies, Canada).

## Problem & setting
- Task: **label-free crop drought-stress staging** into 4 physiological clusters (Healthy, Mild, Moderate, Severe) from Sentinel-2 NDRE (red-edge chlorophyll index) temporal trajectories — moving beyond single-date index thresholds and visual-similarity clustering.
- Data: 10,000 maize 100×100-px Sentinel-2 NDRE patches, Iowa 2020 (drought year), 5-day cadence July–September (5 dates → 5-D mean-NDRE vectors per patch). Test without retraining: 3,500 patches Nebraska 2023. Soil-moisture validation: 1,500 patches each for Iowa 2020/2022/2023 at 3 Iowa Mesonet stations (12–24-inch depth, daily). U.S. Drought Monitor polygons define objectively stressed zones; USDA county yields (2019–2024) confirm stress years (Buena Vista 2020, Monona 2022, Buchanan 2023 = lowest yields).

## Method
- **EigenCL = eigenvector-guided contrastive learning.** Build RBF (Gaussian) similarity matrix over raw NDRE 5-date trajectories; extract the **principal eigenvector** of this matrix (captures ~76.3% of variance; correlates r=0.95 with mean NDRE) as a continuous stress-severity proxy per patch.
- ResNet-50 encoder on NDRE patches → 2048-D embeddings → FC+BN+LeakyReLU projection head → L2 normalize. Cosine similarity matrix computed between embeddings.
- **Loss replaces visual augmentation/cosine targets with physiological similarity:** physiological score s = exp(−Δ/σ), Δ = |normalized eigen-weight difference|, σ=0.5 (text also gives smoothing σ=0.1 in Eq. 5 context). Pull loss (temperature-scaled log, τ=0.075) attracts pairs with high s; push loss (margin hinge, margin m=0.2, weight λ=4.0) repels low-s pairs. Total normalized over pairs; batch 256. Hyperparameters tuned by grid search maximizing Pearson correlation between embedding distance and NDRE stress trajectories + clustering metrics.
- Downstream: k-NN and logistic regression on frozen embeddings; cluster quality via Silhouette/DBI/CHI; validation via lagged Spearman correlations with soil moisture (0–14-day lags) and ARI against soil-quartile stress classes.

## Data & labels
- Fully label-free training; validation only via independent physical data (soil moisture, drought maps, yields). Datasets on Kaggle.

## Results
- Clustering (Iowa): EigenCL Silhouette 0.748, DBI 0.350, CHI 49,624 vs ablation (no eigenvector guidance) 0.533/0.618/33,446, K-Means 0.465/0.958/19,305, SimCLR 0.416/0.724/2,252, ProtoCLR 0.348/0.892/9,995.
- Clusters form a monotonic NDRE gradient; severe-stress cluster shows sharp NDRE decline starting mid-July = tasseling–silking (VT–R1), the known most drought-sensitive maize stage (up to 50% yield loss). Clusters with nearly equal mean NDRE (0.51 vs 0.52) separate by trajectory shape — temporal dynamics, not magnitude, drive separation.
- Cross-region transfer (Iowa 2020 → Nebraska 2023, no fine-tuning): modest metric decline, clustering structure retained.
- Soil-moisture validation: NDRE lags soil moisture 0–14 days; best-lag Spearman ρ = 0.525 (2020, 6-day lag), 0.721 (2022, 14-day), 0.608 (2023, 0-day); ARI vs soil-quartile stress labels 0.12–0.371 (best lag) vs ~0 same-day.
- Downstream classification on frozen embeddings: k-NN 89.1% acc / F1 0.87; logreg 85.2% / 0.82. ANOVA F=37,950, all Tukey pairwise cluster NDRE differences p<0.0001.

## What transfers to our thesis
- **Closest methodological template in this batch for our label-free stress staging:** contrastive learning whose positive/negative pairs are defined by an unsupervised physiological signal (index trajectory structure) rather than augmentation — directly adaptable to sugarcane with Landsat NDVI/NDRE + LST/CWSI trajectories as the guiding signal.
- Demonstrates the key argument that generic SSL (SimCLR, cosine) fails on spectral-temporal agricultural data (Silhouette 0.416 vs 0.748) — a citable justification for domain-aware SSL design in our proposal.
- Trajectory-shape > magnitude: clusters with equal mean NDRE but different dynamics separate — supports modeling the full 16-day Landsat time series (shape) rather than single-date thresholds for water/salinity stress.
- Cross-year, cross-region zero-shot transfer validated (Iowa 2020 → Nebraska 2023) — direct precedent for our cross-year in-field model evaluation.
- The 0–14-day soil-moisture-to-canopy lag finding is directly relevant to our ETa/CWSI water-stress pathway: canopy optical signals respond with a delay to root-zone water — informs lag-aware feature construction and validation design for sugarcane water stress.
- 4-tier staged output (Healthy→Severe) + DSS rule thresholds shows how label-free clusters become decision products — template for our "multi-product" in-field outputs.

## Limitations / caveats
- Preprint, single author, no peer review; some internal inconsistencies (σ reported as both 0.1 and 0.5; some tables lack numeric detail, e.g., yield table empty in extraction).
- Only 5 dates per trajectory (5-D vector) and one index (NDRE); no thermal/LST, no soil salinity; maize only, US Midwest only.
- Spectral clustering context: RBF + principal eigenvector is essentially spectral-embedding-guided contrast; sensitive to bandwidth γ and eigenvector choice (lower eigenvectors degraded performance — acknowledged).
- Validation against station soil moisture is point-scale (~50 km² windows) vs 10-m patches; ARI values (0.12–0.37) show only moderate label agreement.
- Severe cluster timing linked to VT–R1 qualitatively; per-cluster yield penalties "not yet quantified."

## Key numbers to quote in lit review
- EigenCL clustering: Silhouette 0.748 / DBI 0.35 / CHI 49,624 vs SimCLR 0.416 / 0.724 / 2,252 — generic SSL fails on physiological time series.
- NDRE tracks 12–24-inch soil moisture at 0–14-day lag with Spearman ρ up to 0.72.
- Zero-shot cross-state transfer (Iowa 2020 → Nebraska 2023) preserves stress-cluster structure without fine-tuning.
- k-NN on frozen embeddings: 89.1% accuracy / F1 0.87 for 4-stage stress classification.
- Principal eigenvector of NDRE-trajectory RBF matrix explains ~76% of variance and correlates r=0.95 with mean NDRE.



---


## FILE: 2026 Albahli and Shiraz - AgriFM - Multimodal Geospatial Foundation Model Anticipates Crop Stress and Yield Failure (Frontiers Plant Science).md
# AgriFM: A multimodal geospatial foundation model anticipates crop stress and yield failure across climates and species

## Full citation
Albahli, S., & Shiraz, M. (2026). *A multimodal geospatial foundation model anticipates crop stress and yield failure across climates and species*. Frontiers in Plant Science 17:1883297. DOI 10.3389/fpls.2026.1883297

## Problem & setting
- Task: retrospective early crop-stress detection (no stress / drought / heat / compound drought-heat) and yield-failure prediction (seasonal yield below crop-region 20th percentile), across 5 crops (maize, wheat, soybean, rice, sorghum) and 5 agroclimatic regions (North America, Europe, South Asia, East Africa, Latin America).
- Emphasis on transfer: random, geography-split, time-split, and crop-transfer evaluation regimes; deployment metrics include alert lead time, false alerts at matched recall, calibration.
- Data modalities: Sentinel-2 L2A optical, Sentinel-1 GRD radar, MODIS LST + ECOSTRESS thermal, ERA5-Land weather trajectories, SoilGrids soil, topography, sparse management proxies. Unit = field-season (or non-overlapping patch-season), with explicit modality/time masks for missingness.

## Method
- **AgriFM:** modality-specific encoders (spatial-temporal satellite encoder; weather-trajectory encoder with event tokens such as hot-day runs, rainfall-deficit windows, recovery periods; soil/static-context encoder) + **phenology-alignment module** that conditions cross-modal attention on estimated crop developmental stage (not calendar time) + multitask heads (stress class, yield failure, yield anomaly, auxiliary phenology).
- **SSL pretraining on 2.4M field-season sequences:** combination of (i) masked temporal reconstruction, (ii) masked spatial-patch prediction, (iii) cross-modal contrastive alignment, (iv) next-window forecasting. Exact hyperparameters/layer sizes were removed from the revised manuscript (not verifiable in archive).
- Fine-tuning: task-balanced batches, focal loss for rare stress classes, 5 seeds. Uncertainty: heteroscedastic prediction + 5-member deep ensemble + split-conformal calibration.
- Labels: retrospective rule-derived proxies — drought from precipitation/root-zone soil-moisture anomalies, heat from Tmax/Tmin/VPD, compound from overlap in the same phenology window, yield failure from historical 20th percentile; rule-outcome disagreements excluded from fine-tuning. No expert adjudication dataset.
- Explainability: integrated gradients, temporal diagnostics, counterfactual event-token suppression (presented as model-behavior diagnostics, not validated causal explanations).

## Data & labels
- Benchmark "AgriStress-Global": 186,214 labeled field-season records; 2.4M unlabeled sequences for SSL pretraining. Labels are proxy/rule-based, explicitly flagged as a limitation; no prospective field validation.

## Results
- Geography-split stress: AUROC 0.879 vs 0.821 best baseline (late-fusion multimodal transformer, +0.058); AUPRC 0.523 vs 0.418 (+0.105). Time-split yield failure: AUROC 0.891 vs 0.846; AUPRC 0.556 vs 0.428 (+0.128); ECE 0.038 vs 0.061.
- Baseline ladder: logistic regression (AUROC 0.742) < RF 0.761 < XGBoost 0.778 < crop-model hybrid 0.791 < satellite-only transformer 0.812 < late-fusion transformer 0.821 < AgriFM 0.879.
- **Ablations:** removing SSL pretraining = largest drop (stress AUROC −0.041, yield AUPRC −0.074, lead time −8 days); removing weather = −0.037 AUROC / −0.065 AUPRC; phenology conditioning −0.028 AUROC and lead time 24→18 days; radar −0.023; thermal −0.014; soil/terrain small discrimination effect but false-alert benefit 17.3%→13.8%.
- **Alert lead time:** AgriFM median 24 days vs 13 (late-fusion) and 8 (satellite-only); AUPRC advantage +0.11 at 3–4-week horizon; 17.3% false-alert reduction at matched recall via calibration; risk-coverage abstention preserves precision.
- Largest gains on compound drought+heat records: AgriFM alerts 18–24 days earlier than satellite-only baseline.

## What transfers to our thesis
- Confirms the thesis premise quantitatively: **multimodality (optical + thermal + weather) and SSL pretraining are the two largest performance factors** for stress detection under geographic/temporal shift — exactly our Landsat optical+LST cross-year setting. The SSL-removal ablation (−0.041 AUROC, −8 days lead time) is a directly quotable justification for SSL.
- Phenology-conditioned fusion (condition attention on developmental stage rather than calendar date) is a concrete design idea for sugarcane (tillering→grand growth→ripening stages shift with planting/ratoon dates; conditioning on stage rather than DOY should improve cross-year transfer).
- Alert lead time as an evaluation metric (median days before stress confirmation) is a strong addition to our evaluation protocol for early water/salinity stress detection — more decision-relevant than end-of-season accuracy.
- Uncertainty calibration (ensemble + conformal) reducing false alerts 17.3% at matched recall is a practical blueprint for in-field alerting where false positives cost scouting/irrigation effort.
- Rule-derived proxy labels (drought/heat/compound windows from weather+soil moisture) show how "pseudo ground truth" for stress can be constructed without field labels — a possible weak-validation strategy for our sugarcane case when in-field measurements are sparse.
- Counterfactual event-token suppression + integrated gradients = XAI methodology applicable to our XAI requirement (attributing stress alerts to specific drought/heat windows in the Landsat series).

## Limitations / caveats
- Severely weakened paper: the revised version removed all unverifiable details (architecture dims, optimizer, split manifests, per-crop tables, CIs, significance claims) — treat numbers as descriptive effect sizes, not validated results.
- Labels are rule-derived proxies, not physiological measurements; no expert adjudication; no prospective field trial — the authors themselves disclaim operational readiness.
- Sentinel/MODIS/ECOSTRESS mix, not Landsat-only; heavy FM scale (2.4M sequences) is the opposite of our lightweight in-field constraint.
- Management variables (irrigation class, planting window) were coarse proxies with attenuated contribution.
- AUPRC values (~0.42–0.56) show the task itself remains hard under class imbalance.

## Key numbers to quote in lit review
- Multimodal SSL pretraining beats late-fusion under geography shift: stress AUROC 0.879 vs 0.821, AUPRC 0.523 vs 0.418; time-split yield-failure AUPRC +0.128.
- Median alert lead time 24 days vs 13 (late-fusion) and 8 (satellite-only); alerts 18–24 days earlier on compound drought-heat events.
- Removing SSL pretraining is the largest single ablation hit (−0.041 AUROC, −0.074 AUPRC, −8 days lead time).
- Phenology-conditioned fusion beats calendar-time fusion (AUROC 0.879 vs 0.851; lead 24 vs 18 days).
- Conformal-calibrated uncertainty cuts false alerts 17.3% at matched recall; ECE 0.038 vs 0.061.



---


## FILE: 2026 Dalal et al. - STS-Net Spatio-Temporal Stress Network - Self-Supervised Crop Stress Detection from SITS (Sugarcane, arXiv).md
# STS-NET: Spatio-Temporal Stress Network for Self-Supervised Crop Stress Detection using Satellite Image Time Series

## Full citation
Dalal, P., Ranjan, R., Ghildiyal, S., Tamaskar, S., & Goel, N. (2026). *STS-NET: Spatio-Temporal Stress Network for Self-Supervised Crop Stress Detection using Satellite Image Time Series*. arXiv:2607.18791 [cs.CV] (preprint, IEEE member format). https://arxiv.org/abs/2607.18791

## Problem & setting
- Task: **sugarcane water stress, nitrogen stress, and combined water–nitrogen stress detection** from satellite image time series with minimal labels — the single most thesis-relevant paper in this batch (same crop, same stress types).
- Pretraining data (BSPT): PlanetScope imagery over Barnala district, Punjab, India (~196 km²), 32 time steps Feb 2023–Feb 2024 at 9–11-day intervals, <15% cloud, ~22M pixels, fully unlabeled.
- Evaluation data (LK dataset, from Ranjan et al./Plaksha): controlled 3-acre sugarcane experiment in Lakhimpur Kheri, Uttar Pradesh (28°27'N, 80°55'E); 62 plots, plant cane planted Feb 2023; 3 water blocks (50%/100%/150% of standard irrigation) × 3 nitrogen levels (0.2–1 kg fertilizer) imposed during tillering + grand-growth (April–September) → 9 combined stress classes; no ratoon.

## Method
- **Input:** per-pixel time series tensor (T=32 × C=5): RGB + NIR + Avg(NDVI, GNDVI, RECI, NDRE); mean-imputed missing values; min–max normalized.
- **SSL pretraining:** 3D convolutional autoencoder (3D-CAE) — stacked 3D conv encoder compresses the pixel-time-series into latent space, decoder reconstructs the original spectral sequence from surrounding space–time context; **MSE reconstruction loss** on unlabeled BSPT pixels. Adam lr 0.001, batch 256, ≤40 epochs, early stopping.
- **Fine-tuning:** decoder discarded, encoder frozen as feature extractor → 64-D latent vector per pixel → lightweight classifiers (RF / XGBoost / SVM) trained on labeled LK pixels for three separate multiclass tasks (water 3-class, nitrogen 3-class, combined 9-class). 80:20 stratified split.
- Model size: **19.2K parameters** (vs Presto ~400K).

## Data & labels
- Pretraining fully label-free (BSPT, 22M pixels). Fine-tuning labels come from the controlled LK field experiment (systematically induced stress = ground truth), pixel-level.

## Results
- Water stress: 3D-CAE+RF accuracy 0.97, precision 0.98 (claimed 97.98% precision), F1 0.98. Nitrogen: 3D-CAE+XGBoost acc 0.87, precision 0.87 (85.08% claimed). Combined 9-class: 3D-CAE+XGBoost acc 0.84, precision 0.85 (83.47% claimed).
- Baselines: supervised RF/SVM/XGBoost on raw series 0.44–0.60 (water), 0.28–0.31 (combined); supervised 2-layer CNN 0.54/0.52/0.28; **Presto (SSL foundation model) 0.82/0.81/0.72** — the domain-specific 3D-CAE beats the general-purpose Presto by 0.08–0.12 accuracy.
- Ablations: RGB+NIR+Avg(VIs) is the best channel config (97.98/85.08/83.47 vs RGB+NIR 86.32/72.14/68.21); temporal depth T: 8 steps (≈2 months) still gives 90.32% water accuracy, monotonic improvement to T=32 — stress signals visible within ~2 months.

## What transfers to our thesis
- **Direct recipe template:** self-supervised reconstruction autoencoder on pixel-level vegetation-index time series, pretrained on unlabeled regional data, frozen encoder + tiny classifier head — exactly the "lightweight SSL + in-field model" architecture class of our thesis, here demonstrated on sugarcane with water AND nitrogen stress simultaneously.
- Key competitive result to cite: a 19.2K-parameter domain-specific 3D-CAE outperforms Presto (400K params, globally pretrained) on sugarcane stress — supports the thesis argument that small agri-specific SSL models can beat large generic FMs for in-field deployment.
- Ablation evidence for channel selection: red-edge VIs (NDRE/RECI) + NIR + averaged VIs substantially outperform RGB/NIR alone (+11.7 pp water accuracy) — informs which Landsat-8/9 bands/indices (no red edge on Landsat, but NDVI/GNDVI analogs + thermal) to include.
- Temporal-depth ablation (T=8 → 32: 90.3→98.0 water accuracy) quantifies the value of dense temporal sampling; for Landsat 16-day series this sets expectations (fewer steps, lower ceiling) and justifies multi-year stacking.
- The LK controlled-experiment design (induced water×nitrogen factorial, 9 classes, tillering+grand-growth windows) is a validation-design blueprint for our sugarcane stress ground truth.
- Pixel-level (not field-level) formulation allows within-field stress heterogeneity mapping.

## Limitations / caveats
- Preprint, not peer-reviewed; arXiv ID 2607.18791 (July 2026).
- PlanetScope 3-m 9–11-day imagery, NOT Landsat 30-m 16-day; spatial resolution is a major driver of their accuracy — results will not transfer 1:1 to Landsat.
- No thermal band / LST / CWSI or ETa — water stress inferred only through optical VIs; the thesis's thermal pathway is complementary and untested here.
- Only one season, one site, plant cane only (no ratoon); pretraining region (Punjab) ≠ evaluation region (UP) but same broad agro-zone — cross-year and true cross-region transfer untested.
- Reconstruction-only pretext (no masking strategy, no contrastive term); MSE imputation of missing pixels may leak temporal smoothness.
- Ground truth = imposed treatment levels, not measured plant physiological stress (soil moisture, canopy temperature) — treatment≠stress severity assumption.

## Key numbers to quote in lit review
- First self-supervised 3D-CAE for crop stress detection from SITS: 97.98% precision (water), 85.08% (nitrogen), 83.47% (combined 9-class) on a controlled sugarcane experiment.
- 19.2K-parameter 3D-CAE beats Presto (400K params): accuracy 0.97 vs 0.82 (water), 0.87 vs 0.81 (nitrogen), 0.84 vs 0.72 (combined).
- Supervised baselines on raw series collapse on combined stress (0.23–0.31 accuracy) vs 0.84 with SSL features.
- Water stress detectable with only 8 time steps (~2 months, 90.3% accuracy); full 32 steps reach 98.0%.
- Red-edge VIs (NDRE/RECI averaged with NDVI/GNDVI) add +11.7 pp water-stress accuracy over RGB+NIR.



---


## FILE: 2026 Faran et al. - Spatio-Temporal Transformers for Long-Term NDVI Forecasting, Landsat 1984-2024 (arXiv).md
# Spatio-Temporal Transformers for Long-Term NDVI Forecasting (STT-LTF)

## Full citation
Faran, I., Netanyahu, N. S., & Shoshany, M. (2026). *Spatio-Temporal Transformers for Long-Term NDVI Forecasting*. arXiv:2602.01799 [cs.CV]. https://arxiv.org/abs/2602.01799 (extension of Faran et al. 2025, ICPRAM, "Self-supervised transformers for long-term prediction of Landsat NDVI time series").

## Problem & setting
- Task: self-supervised **long-term NDVI forecasting** on Landsat — predict NDVI at an arbitrary future timestamp (Δ up to years ahead) from multi-decade history, for a heterogeneous Mediterranean-to-arid gradient (SE Mediterranean basin, rainfall 250–450 mm/yr, shrubland→phrygana→desert; desertification monitoring motivation).
- Data: Landsat 5/7/8/9, 1984–2024, 30 m, GEE Level-2 SR; study area 53.94×37.35 km (1,798×1,245 px); bi-annual median composites (winter Oct–Apr "growing", summer May–Sep "dormant"); <20% cloud; **2,238,510 pixel time series**. Temporal split: 1984–2013 train/val, 2014–2024 test (true future generalization).

## Method
- **Formulation:** input O = {(NDVI patch Xt ∈ R^{N×N}, month Mt, year Yt, lat, lon) | t=0..T} plus target (M_{T+Δ}, Y_{T+Δ}); model f predicts NDVI at T+Δ directly — **non-autoregressive, target time as input parameter**, no recursive error accumulation.
- **Three SSL masking strategies (training augmentation):** (1) spatial masking — random spatial window n<N, zero outside central n×n (scale invariance); (2) temporal masking — random prefix truncation T′<T (robustness to irregular/missing observations); (3) future horizon sampling — Δ ~ Uniform{1..Ymax−T} (multi-horizon competence).
- **Embeddings:** linear projection of flattened N×N NDVI patch (128-D); cyclical month encoding (sin/cos 2πM/12); year normalized to dataset range and linearly projected; lat/lon converted to 3-D unit-sphere Cartesian coords then linear (8-D); sinusoidal positional encoding. Concatenated → 256-D.
- **Architecture:** 3 transformer encoder blocks, 8 attention heads, dropout 0.2; regression decoder (2-layer FC, ReLU, dropout) on the target-time token → scalar NDVI. **MAE (L1) loss**, Adam lr 2e-4, 150 epochs. Fully label-free (supervision = future observed NDVI).

## Data & labels
- No labels at all; ground truth for training/testing is the actual observed future NDVI from the archive. Temporal split enforces genuine forecasting evaluation.

## Results
- Best next-year prediction: **MAE 0.0328, R² 0.8412** (10-year input) — beats SVM (0.0456/0.746), CNN-1D (0.0391/0.781), FC (0.0383/0.795), LSTM (0.0363/0.809), vanilla Transformer (0.0361/0.818), TFT-configured baseline.
- Temporal depth dominates spatial extent: 20-year sequence, patch 1×1: MAE 0.025/R² 0.922; 1-year sequence: MAE ~0.098/R² ~0.03–0.09. Gains saturate after ~10–15 years. Patch size 1×1→9×9 changes little (R² 0.922→0.927 at 20 years); 7×7 px (~210 m) is the practical optimum — larger windows dilute with mixed land cover.
- Model captures seasonal + inter-annual trends but misses abrupt outliers (fires, sudden events) — deviation from trend is precisely the residual signal.

## What transfers to our thesis
- **Same sensor family and cadence as our thesis:** Landsat 5/7/8/9, 30 m, 16-day acquisitions composited — this paper demonstrates that 40 years of unlabeled Landsat NDVI alone can train a useful SSL forecaster; our sugarcane water/salinity setting can reuse the exact data pipeline (bi-annual/seasonal median composites, temporal split).
- Design elements directly adoptable: (1) **cyclical month + normalized-year encodings** for cross-year transfer; (2) **3-D Cartesian lat/lon location encoding**; (3) **target-time-as-input non-autoregressive heads** — lets one model answer "what should NDVI/NDRE be at date X?" in a single pass, which is exactly the backbone of an expected-vs-observed anomaly score for stress detection; (4) horizon sampling during training so the model handles irregular observation gaps.
- Forecast-residual anomaly detection: their model "struggles with unexpected outliers" — reframed, forecast error itself becomes a label-free stress/anomaly signal; a sugarcane field whose NDVI/LST trajectory departs from the 10-year learned expectation is a candidate stress flag. This is a concrete, lightweight alternative to contrastive pipelines.
- Quantitative guidance: temporal depth >> spatial context for vegetation prediction (R² 0.03→0.92 from 1→20 years vs +0.005 for 9×9 patches) — supports prioritizing long multi-year Landsat series over spatial neighborhood size for our per-field stress features; keep spatial patches small (≤7×7 px ≈ 210 m).
- The arid/Mediterranean gradient with drought cycles is climatically closer to our water-stress setting than temperate benchmarks.

## Limitations / caveats
- NDVI only — single index, no thermal/LST, no salinity signal; natural-vegetation focus (shrubland/desert margin), not cropland or sugarcane.
- Bi-annual composites (2 obs/year) discard the intra-seasonal dynamics that matter for stress timing; 16-day series would need adaptation.
- Forecast quality degrades with horizon; abrupt-event outliers unmodeled (they call it a weakness; we would exploit it for anomaly detection).
- Pixel-wise, no explicit field/parcel semantics; geographic transferability (other regions) left as future work — only temporal generalization is tested.
- MAE loss and regression head are simple; no uncertainty estimates.

## Key numbers to quote in lit review
- 40 years of unlabeled Landsat (2.24M pixel series) → next-year NDVI MAE 0.0328 / R² 0.8412, beating LSTM (0.0363/0.809) and TFT-style baselines.
- Temporal depth is decisive: R² rises from 0.09 (1-year history) to 0.92 (20-year history); spatial patches beyond 7×7 px (210 m) give negligible gains.
- 10-year history is the practical sweet spot before saturation.
- Non-autoregressive direct prediction at arbitrary future dates avoids recursive error accumulation.



---


## FILE: 2026 Hong et al. - Foundation Models in Remote Sensing - Evolving from Unimodality to Multimodality (arXiv).md
# Foundation Models in Remote Sensing: Evolving from Unimodality to Multimodality

## Full citation
Hong, D., Li, C., Li, X., Camps-Valls, G., & Chanussot, J. (2026). *Foundation Models in Remote Sensing: Evolving from Unimodality to Multimodality*. arXiv:2603.00988 [cs.CV]. https://arxiv.org/abs/2603.00988

## Problem & setting
- Comprehensive technical survey (no new model): answers what/why/how of foundation models (FMs) in remote sensing, organized around the field's evolution from **unimodal** (RGB, spectral, SAR) to **multimodal** FMs. Tutorial-style, aimed at guiding researchers; reviews ~105 FM papers (2018–2025), pretraining datasets, and downstream evaluation.

## Method (survey structure)
- **Learning paradigm:** "self-supervised pretraining + fine-tuning" as the dominant RS paradigm replacing supervised/feature-engineering pipelines; contrastive and generative (reconstruction) pretraining losses over MLP/CNN/RNN/ViT backbones; frozen-encoder or fine-tuned (decoder-emphasis) adaptation.
- **Pretraining datasets (Table II):** SeCo (~1M, spectral 10 m), SSL4EO-S12 (1,004,316 imgs, S1+S2 10–60 m), fMoW (1,047,691), MillionAID (400,695), **SSL4EO-L (Landsat, 30 m, 5 million scenes)**, Satlas (856K), GeoPile/GFM (587,954), DOFA-data (8,081,411), Prithvi (4.2M, spectral 30 m), Skysense (21.5M), MMEarth (1.2M).
- **Unimodal taxonomy:** RGB (MATTER, RVSA, Scale-MAE, GFM, SatMAE++, SAM adaptations); spectral (SatMAE grouping-mask, Prithvi channel masking, SpectralGPT 3D masking, HyperSIGMA spatial-spectral two-stream); SAR (FG-MAE, SAR-JEPA).
- **Multimodal taxonomy:** homogeneous multi-sensor (USat, SenPa-MAE, CSMAE); optical–SAR (RingMo, CROMA contrastive masked pretraining, DeCUR common/unique decoupling); optical/SAR/spectral/DSM (SkySense, DOFA dynamic band weighting, msGFM, MMEarth, OmniSat); time-series (SeCo seasonal positives/negatives, CACo temporal consistency, U-BARN BERT-style masked sequence reconstruction, A2-MAE anchor-aware masking + geo-encoding, **Prithvi-EO-2.0 channel-masking on Landsat+S2 time series**); geospatial-vision (GASSL, SatCLIP, GeoCLIP); vision-text/LMM (RemoteCLIP, GeoChat, TEOChat for time-series dialogue).
- **Quantitative multimodal evidence (PANGAEA-Bench, 11 datasets, 1.5–30 m, RGB/spectral/SAR):** multimodal FMs dominate top positions nearly everywhere — e.g., TerraMind best on BurnScars 82.42, MADOS 69.52, PASTIS 40.51, CTM-SS 55.80; DOFA best on AI4Farms 27.07 and Xview2 59.64; unimodal SSL4EO-MAE/MoCo/DINO trails (PASTIS 32–36).
- **Tutorial:** model selection criteria (pretraining-data/sensor alignment, architecture size vs resource constraints, temporal/multimodal features), environment setup, fine-tuning strategies (PEFT/LoRA), deployment.

## Data & labels
- Survey; synthesizes that RS labeling is the bottleneck (pixel-level annotation over large areas), justifying self-supervised pretraining on unlabeled archives.

## Results
- No original experiments; key synthesized findings: (1) multimodal > unimodal across classification/segmentation/change detection on PANGAEA; (2) statistical shift — multimodal FMs surged after 2024; arXiv dominates venues, then IEEE TGRS and CVPR; China leads country contributions; (3) agricultural datasets (PASTIS, AI4Farms) remain among the hardest for all FMs.

## What transfers to our thesis
- Positioning resource: cite for the field-level claim that multimodal SSL FMs are the current state of the art in RS representation learning, and that **optical+thermal time-series fusion sits inside the "heterogeneous → time-series" branch** (SeCo, CACo, U-BARN, A2-MAE, Prithvi-EO-2.0) our Landsat optical+LST work extends.
- PANGAEA table gives citable numbers that even top FMs underperform on agricultural benchmarks (PASTIS mIoU ~30–40; AI4Farms ~25–28) — evidence that agriculture, especially stress/anomaly tasks, is NOT solved by scale, motivating our crop-specific lightweight SSL approach.
- The survey's model-selection criteria (sensor/pretraining alignment, parameter count vs deployment constraints) map directly to our "lightweight multi-product in-field" argument: global FMs (Skysense 21.5M imgs, billion-param) are misaligned with 30-m Landsat in-field deployment.
- SSL4EO-L (5M Landsat 30-m scenes) is the natural pretraining corpus candidate if we ever pretrain on external Landsat data before fine-tuning to sugarcane fields.
- Future-directions section (robustness-aware/uncertainty-aware pretraining, sensor noise and domain shift modeling) aligns with our cross-year robustness and XAI/uncertainty needs.

## Limitations / caveats
- Survey breadth over depth: agricultural and time-series applications get limited space relative to vision-LMM trends; no anomaly/stress detection category at all.
- Benchmark synthesis limited to PANGAEA-Bench tasks (segmentation/CD/regression); no stress, ET, or anomaly benchmarks covered.
- Many cited models are arXiv-stage; the field's rapid churn means taxonomy dates quickly.
- No quantitative guidance on when small domain-specific SSL (e.g., 3D-CAE, SITS-BERT) beats large FMs — our thesis can fill that gap.

## Key numbers to quote in lit review
- 105 RS foundation models reviewed; multimodal FMs overtook unimodal after 2024.
- SSL4EO-L: 5M Landsat 30-m scenes exist as a dedicated SSL pretraining corpus; DOFA-data 8.08M and Skysense 21.5M images represent the scale frontier.
- PANGAEA-Bench: multimodal FMs (TerraMind, DOFA, CROMA) dominate 11 datasets, but agriculture benchmarks (PASTIS 40.51 best; AI4Farms 28.12 best) lag far behind — agriculture remains an open frontier.
- The paradigm claim: "self-supervised pretraining + fine-tuning" is now the dominant RS learning framework.



---


## FILE: 2026 Hu et al. - High-Efficiency Diffusion-Inspired Network for Pixel-Level Self-Supervised Hyperspectral Anomaly Change Detection (IEEE JSTARS).md
# A High-Efficiency Diffusion Model-Inspired Network for Pixel-Level Self-Supervised Hyperspectral Anomaly Change Detection (ELDI-Net)

- **Full citation**: Hu, X., Liu, X., Guo, C., Li, J., Duan, Q., Li, R., Cheng, J., & Zhang, D. (2026). "A High-Efficiency Diffusion Model-Inspired Network for Pixel-Level Self-Supervised Hyperspectral Anomaly Change Detection." IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing (JSTARS), Vol. 19, pp. 27891-27906, DOI: 10.1109/JSTARS.2026.3723417. University of Shanghai for Science and Technology et al.

- **Problem & setting**: Pixel-level self-supervised hyperspectral anomaly change detection (HACD) — detecting rare, small changes (appearing/disappearing/moving objects) between two co-registered HSIs without labels, while suppressing pseudo-changes (shadows, registration errors, illumination shifts). Benchmarks: Viareggio 2013 airborne HSIs (450x375 px, 127 bands, 400-1000 nm, 0.6 m GSD; EX-1 same-day pair, EX-2 cross-day pair with 3-5 px misalignment, nonlinear deformation, and 30-40% shadow-induced reflectance drops) and a simulated Hymap dataset (280x800x126, 453-2486 nm) with spatially correlated synthetic noise and an explicit 1-pixel registration offset.

- **Method** (self-supervised, label-free; the core SSL design): ELDI-Net replaces diffusion-model iterative denoising with a one-step latent manifold projection (OLMPF), motivated by denoising score matching (Vincent 2011): treat inter-temporal domain shifts, illumination change and anomalies as "temporal noise" on a clean background manifold, and learn a deterministic single-step projection onto the noise-free manifold. Architecture (weight-shared Siamese): (1) Encoder E with the SACP module — Efficient Channel Attention (1-D conv over globally pooled channel descriptors, adaptive kernel k = |log2(C)+b/gamma|_odd) plus 3x3x3 3-D conv — dynamically recalibrates spectral channels ("spectral denoising") at full spatial resolution (downsampling factor s=1, latent channels c=128); (2) decoder D acts as a one-step generative denoiser reconstructing the clean image; (3) projector g and predictor q (BYOL/SimSiam-style with stop-gradient) implement the Bidirectional Focal Alignment Mechanism (BFAM): asymmetric cross-prediction (predict the other date's projected features) plus self-prediction, weighted by focal cosine loss L_fc = -(2-S)^gamma * S (gamma=1), computed ONLY on high-confidence unchanged-pixel pseudolabels I generated a priori by CVA + Otsu thresholding. Total loss L = L_rec (MSE reconstruction, ELBO approximation) + L_align, equal 1:1 weighting. Inference: Geometric Consistency Inference (GCI) — average latent features over K=4 rotations/flips and their inverse transforms — then a classical Diff-RX statistical detector on the fused latent features produces the anomaly score map. Training: Adam lr 1e-4, cosine decay, 500 epochs, single RTX 4090.

- **Data & labels**: Three dual-temporal HSI benchmarks (Viareggio EX-1, EX-2, simulated Hymap). No ground-truth labels used in training — pseudo-labels of unchanged pixels only, from CVA+Otsu; ground truth used solely for AUC evaluation. Evaluation: ROC/AUC.

- **Results**: AUC: ELDI-Net 0.9366 (EX-1), 0.9264 (EX-2), 0.9912 (Hymap) — best on EX-1/EX-2 (beating HyperNet 0.9046/0.9147 by +0.0320/+0.0117), second on Hymap (HyperNet 0.9916). Baselines: CC, Diff-RX, USFA, SACD, SDACD, SDHACD, HACD, MTC-NET (patch 13/31), HyperNet. Efficiency: 42 FPS; FPS 3.63e4x MTC-NET, 10.69x HyperNet, 16.49x BSDM, 10.77x DWSDiff — one-step projection removes the Markov-chain O(T) inference cost of diffusion-based detectors. Ablations: adding BFAM first gives the largest jump (+0.0509 EX-1, +0.0464 EX-2, +0.0355 Hymap AUC over the reconstruction-only baseline), then SACP (channel calibration) and GCI (test-time geometric fusion) add further gains. Pseudo-label sensitivity: retaining only 20% of CVA+Otsu pseudolabels degrades AUC only to ~0.89 (EX-1/EX-2) and ~0.98 (Hymap) — robust to label noise.

- **What transfers to our thesis**:
  - The twin cross-prediction + stop-gradient alignment on pseudolabeled-unchanged background pixels is a directly transplantable SSL objective for label-free stress anomaly detection on Landsat SITS: treat normal/background time steps as "unchanged" and detect anomalous stress signatures as deviations from the aligned background manifold.
  - Focal cosine loss (upweighting hard-to-align samples such as shadow/illumination artifacts) is a concrete loss design for cross-year Landsat robustness where illumination, atmosphere and view-angle changes dominate pseudo-anomalies — exactly our cross-year setting.
  - The "one-step manifold projection" idea (replace iterative generative denoising with a deterministic encoder-projector-decoder trained by reconstruction + alignment) is a template for a lightweight, real-time anomaly head — matches our lightweight in-field deployment requirement.
  - GCI-style test-time geometric averaging (rotation-consistent latent fusion) is a free, architecture-agnostic robustness trick applicable to our Landsat anomaly maps.
  - Their emphasis on suppressing pseudo-changes (registration error, shadows) parallels our need to suppress phenological senescence/illumination artifacts vs genuine water/salinity stress anomalies in sugarcane; the CVA+Otsu pseudolabel + robustness analysis also offers an evaluation recipe when only coarse proxies exist.
  - Note the task structure: sparse rare anomalies vs dominant stable background — analogous to rare stressed fields within normal crop backgrounds; the information-bottleneck argument (anomalies are sparse, encoder learns dominant manifold) carries over.

- **Limitations / caveats**: HSI-only (126-127 bands), no multispectral/Landsat evaluation — band-count-dependent channel calibration may need redesign for 6-7 Landsat bands; still depends on initial CVA+Otsu pseudolabels (authors acknowledge low-quality pseudolabels bound final accuracy); detection head is not end-to-end (relies on classical Diff-RX backend); no temporal series (only two dates) — no handling of intra-season temporal dynamics; small images (450x375, 280x800) not wall-to-wall scenes; no agricultural application or crop-stress validation; military/urban anomaly focus.

- **Key numbers to quote in lit review**:
  - AUC 0.9366/0.9264/0.9912 on EX-1/EX-2/Hymap; +0.032 AUC over the best baseline on EX-1.
  - 42 FPS inference; 10.7x faster than self-supervised HyperNet, 16.5x faster than diffusion-based BSDM — one-step projection vs iterative diffusion sampling.
  - BFAM (bidirectional focal cross-prediction on pseudolabeled background) alone contributes +0.035 to +0.051 AUC — the largest single ablation gain.
  - Only 20% of pseudolabels retained -> AUC still ~0.89-0.98 — SSL objective is robust to pseudolabel noise.



---


## FILE: 2026 Khan and Atoofian - Quantum-Enhanced Multi-Scale CNN with Bi-Directional Mamba for Crop Field Analysis (arXiv).md
# Quantum-Enhanced Multi-Scale CNN with Bi-Directional Mamba for Crop Field Analysis (CNN-BiSpectralMamba-Quantum)

## Full citation
Khan, M. S., Atoofian, E., & Ahmed, S. B. (2026). *Quantum-Enhanced Multi-Scale CNN with Bi-Directional Mamba for Crop Field Analysis*. arXiv:2606.17222 [cs.CV] (preprint, June 2026, Lakehead University). https://arxiv.org/abs/2606.17222

## Problem & setting
- Task: supervised semantic segmentation/classification of UAV hyperspectral crop imagery — **UAV-HSI-Crop dataset** (China Agricultural University; Majiakou/Xijingmeng villages, Shenzhou, Hebei, China): 433 samples of 96×96 px, 200 spectral bands (400–1000 nm, Resonon Pika-L), ~0.1 m/px, 27–30 crop/land-cover classes with severe class imbalance and limited labels.
- Motivation: transformers reach ~100M+ params (HSI-TransUNet 110M) and need labels that agriculture lacks; Mamba gives linear-complexity sequence modeling but flattening the HSI cube destroys spatial geometry; quantum circuits as cheap global-context heads.

## Method (fully supervised; no SSL, no time series)
- Pipeline: per-band standardization (variance floor 1e-6) → **multi-scale CNN** (two 3×3 conv encoder blocks, 32→64 channels, stride-2 downsample, bilinear upsample + concat fusion) → **spectral Squeeze-and-Excitation** (reduction 16) → flatten to token sequence → **bidirectional Mamba** (forward + flipped-backward S6 selective state-space blocks, outputs summed) → two heads:
  - Classical: LayerNorm + linear → 2-D spatial classification map.
  - **Quantum head:** global average pooling → linear to 4 dims → **4-qubit variational quantum circuit** (PennyLane, angle embedding, 2 Basic Entangler Layers, Pauli-Z expectation values) → class logits; fused as Y_logits = Y_classical + tanh(α)·Y_quantum with learnable α (final α=0.2, init 0.0).
- Loss: λ-balanced (λ=0.5) **class-weighted CE + Log-Cosh Dice**; class weights = inverse-sqrt frequency with 0.7 power scaling. AdamW, lr 3e-4 (classical) / 5e-5 (quantum head), 100 epochs (baselines 200), batch 8, d_model 64.
- Total trainable parameters: **0.24M (246,793)**. Trained on 5×H100 GPUs, 8-hour windows; quantum circuit simulated on CPU.

## Data & labels
- Fully supervised on UAV-HSI-Crop ground-truth masks; no label-free component.

## Results
- Proposed: **OA 84.83%, Kappa 82.07** with 0.24M params vs HSI-TransUNet 86.05%/83.47 at 110M params, HRS-UNet 89.96%/88.14; TransUNet 78.64 (105M); UNet 76.07 (8M); SegNet 43.61 (29M); their earlier QPGF 81.92 (4.1M).
- Ablations: No BiMamba −5.33% OA (79.50) — bidirectional Mamba is the critical core; No Quantum −1.32% (83.51); No SE −0.46% (84.37); **Plain CE actually gives higher OA (85.24)** but sacrifices minority-class boundary fidelity — the hybrid Log-Cosh Dice trades 0.41% skewed global accuracy for equitable minority-crop mapping (Kappa framing).

## What transfers to our thesis
- **Primary transfer: the class-imbalance loss design** — hybrid CE + Log-Cosh Dice with inverse-sqrt frequency power-scaling weights (0.7 exponent) is directly reusable for imbalanced sugarcane stress/anomaly labels (stressed pixels are a minority class); their own ablation showing plain CE inflates OA by ignoring minority classes is a citable metric-methodology caution (report Kappa/IoU per class, not just OA).
- **Mamba/bidirectional SSM over spectral or temporal sequences** as a linear-complexity alternative to transformers supports the thesis interest in lightweight sequence encoders for Landsat time series (relevant to our "lightweight" pillar and to the SSM survey in the same batch).
- Efficiency headline: 0.24M params reaching 84.83% OA vs 110M-param transformer at 86.05% — a 450× parameter reduction for ~1.2 pp OA — strengthens the argument that small models suffice for crop tasks when designed well.
- Literature-review table is a compact digest of Mamba-for-HSI results (SS-Mamba, BiMambaHSI, EchoMamba, S2Mamba with OA 91–99% on standard HSI benchmarks) — useful background for a state-space-model paragraph.
- Honest limitations to echo: Mamba flattening destroys spatial geometry (they patch it with a CNN backbone); quantum head is simulated (no real quantum hardware advantage demonstrated).

## Limitations / caveats
- No SSL, no time series, no satellite data — UAV hyperspectral single-date imagery; far from Landsat 16-day label-free monitoring.
- The "quantum" component is a 4-qubit simulated variational circuit acting as a small global head; contribution is marginal (+1.32% OA) and the framing is inflated relative to the actual mechanics.
- Writing quality issues (promotional tone, "permanently/aggressively" rhetoric, references to GeeksforGeeks, table inconsistency: abstract says 30 classes, Table 1 says 27); preprint, not peer-reviewed.
- Lower OA than HRS-UNet and HSI-TransUNet — the win is parameter efficiency only.
- Baselines trained 200 epochs vs proposed 100 — comparison protocol not fully controlled.

## Key numbers to quote in lit review
- 0.24M-parameter hybrid CNN+BiMamba+4-qubit-quantum reaches 84.83% OA / Kappa 0.82 on UAV-HSI-Crop (27–30 classes) vs 110M-param HSI-TransUNet 86.05%.
- Bidirectional Mamba is the critical component: removing it drops OA 5.33 pp.
- Plain CE yields higher OA (85.24%) than the class-balanced hybrid loss (84.83%) — evidence that global accuracy masks minority-class failure under extreme imbalance.
- Survey-level: Mamba HSI classifiers (SS-Mamba, BiMambaHSI, S2Mamba) report 91.6–99.5% OA on standard benchmarks with linear sequence complexity.



---


## FILE: 2026 Li et al. - Global-Scale Self-Supervised Spatiotemporal Learning for NDVI Time-Series Reconstruction (arXiv).md
# GloSSR: Global-Scale Self-Supervised Spatiotemporal Learning for NDVI Time-Series Reconstruction

## Full citation
Li, A., Jiang, M., Guan, X., Chu, D., & Shen, H. (2026). *Global-Scale Self-Supervised Spatiotemporal Learning for NDVI Time-Series Reconstruction*. arXiv (preprint, Wuhan University; corresponding author Huanfeng Shen). No arXiv ID printed in text.

## Problem & setting
- Task: reconstruction of cloud-contaminated/noise-corrupted NDVI time series (gap filling + denoising) — a prerequisite step for any downstream vegetation/stress monitoring on optical satellite series.
- Data: MODIS MOD13A2 NDVI, 1 km, 23 images/year, 2001–2024, globally sampled tiles (training from low–mid-latitude vegetation-rich tiles; bare/desert/ice excluded). Artificial tests in East Asia, West Africa (persistent cloud), South America (Amazon, severe cloud), 10% random noise injection. Transfer test: AVHRR GIMMS-3G (~8 km, semi-monthly), no fine-tuning.
- Core bottleneck addressed: no paired clean/degraded NDVI exists at the same location — fixed-ratio random masking used by prior SSL does not mimic real cloud structure (spatially coherent, temporally persistent).

## Method
- **SSL sample construction (key idea):** pair relatively clean patches with genuinely cloud-affected patches (identified by pixel-level quality flags, 30% cloud threshold); replace clean pixels with the cloud-contaminated counterpart's values and inject mild noise into remaining pixels → realistic degraded inputs, with the original clean patch as self-supervised target. Trained on globally distributed samples across biomes/climate zones.
- **Network:** quality flags as extra input modulating NDVI features pixel-wise; **global-local spatiotemporal module** = bidirectional Transformer along time (long-range temporal dependencies) + bidirectional ConvLSTM (fine-grained spatiotemporal dynamics, past+future context), fused by conv; **temporal-channel dual attention** reconstruction module (AvgPool+MaxPool MLP sigmoid gates on both time steps and channels).
- **Loss:** L = L_cons + L_prior. Data consistency with three masked terms: fidelity (M1: clean pixels shared input/output), reconstruction (M2: artificially clouded pixels), uncertainty (M3: noised pixels), weights λ1=0.6, λ2=2, λ3=0.1. Prior loss = 0.1·spatial gradient loss + 0.4·temporal smoothness (second-order difference penalty for phenological plausibility).
- Patches 32×32×23 (T=23 images/year). Baselines: Savitzky–Golay, HANTS, ST-Tensor (variational tensor completion). Metrics: CC, RMSE, MAE.

## Data & labels
- Entirely self-supervised from real MODIS observations; clean observations used only for evaluation. Public data (MOD13A2, GIMMS-3G).

## Results
- Artificial degraded reconstruction: GloSSR best in all three regions, e.g., overall MAE 0.0124 (East Asia), 0.0098 (West Africa), 0.0150 (South America) vs ST-Tensor 0.0208/0.0192/0.0228 and SG ~0.028. Cloud removal in West Africa: CC 0.874 vs ST-Tensor 0.489 — huge gain under persistent cloud.
- Ablations (West Africa): removing Transformer/temporal attention/bidirectional structure all degrade; reconstruction loss term is the most critical for cloud removal (CC 0.874→0.761); removing temporal smoothness *improves* quantitative metrics (denoising MAE 0.0176→0.0127) but produces jagged curves — kept at ε=0.4 as phenological realism trade-off.
- Runtime: 24-year 800×800×529 reconstruction in 374 s (32 CPU cores) or **126 s on GPU** vs ST-Tensor ~9,863–11,470 s — ~80× faster.
- Long-term trend analysis (Theil–Sen + Mann–Kendall, 2001–2024): reconstructed series change trend classifications to better match known surface processes (cloudy mountains → significant increase; urbanizing Red River delta → weaker trend).
- Cross-sensor transfer to AVHRR GIMMS-3G without fine-tuning: CC 0.759 (cloud removal) vs ST-Tensor 0.672, RMSE/MAE reduced ~25%.

## What transfers to our thesis
- **Directly applicable preprocessing layer for Landsat 16-day sugarcane series:** cloud gaps are the central data-quality problem in tropical/subtropical Landsat monitoring; GloSSR shows a self-supervised gap-filler trained on realistic (quality-flag-derived) cloud patterns outperforms SG/HANTS, especially for long persistent cloudy segments that interannual methods can't fix. Adapting the pairing scheme (clean patch ↔ cloudy patch from same/neighbor region) to Landsat NDVI+LST series is straightforward and label-free.
- The **three-term data-consistency loss (fidelity / reconstruction / uncertainty)** is a template for any masked-reconstruction pretext on our series: keep fidelity on unmasked pixels, reconstruct masked ones, and add a noise-robustness term — more realistic than naive random masking (their critique of fixed-ratio masking aligns with the MIMRS caveats in this batch).
- The **temporal smoothness prior trade-off** is a warning directly relevant to stress detection: over-smoothing removes the very anomalies (stress dips) we want to detect — they found removing smoothness *improves* RMSE but creates unrealistic jaggedness; for stress work we would reduce ε or drop it, and validate that phenological troughs (harvest, dormancy) are preserved (their multi-peak preservation results).
- Cross-sensor zero-shot transfer (MODIS→AVHRR, CC +0.09) supports the claim that SSL trained on vegetation-dynamics priors generalizes across sensors — encouraging for cross-year/cross-region transfer of our models.
- GPU 126 s for 24-year reconstruction shows operational feasibility for wall-to-wall sugarcane estate monitoring.

## Limitations / caveats
- MODIS 1 km / 23 images per year — coarser and denser than Landsat 30 m / ~23 scenes per year but with far more cloud; spatial texture at 30 m (field level) untested; sugarcane fields smaller than 1 km.
- Reconstruction reproduces "expected" vegetation dynamics — by design it will smooth genuine stress signals; using it upstream of stress detection requires care (their smoothness prior fights anomaly preservation).
- NDVI only, no LST/thermal; loss weights (λ, δ, ε) empirically set and acknowledged as dataset-specific.
- Quantitative evaluation relies on artificial degradation; real-scene evaluation is qualitative/visual plus trend plausibility.
- Preprint (no journal DOI in text).

## Key numbers to quote in lit review
- GloSSR overall MAE 0.0098–0.0150 across three continents vs 0.019–0.028 for ST-Tensor/SG/HANTS; West Africa persistent-cloud CC 0.874 vs 0.489 (ST-Tensor).
- ~80× faster than ST-Tensor (126 s GPU vs ~11,470 s for 24-year reconstruction).
- Zero-shot MODIS→AVHRR transfer: CC 0.759 vs 0.672 (second-best), RMSE/MAE −25%.
- Realistic cloud-structured degradation beats random fixed-ratio masking for SSL reconstruction — a design lesson for all masked time-series pretraining.



---


## FILE: 2026 Ma et al. - Harvesting AlphaEarth - Benchmarking the Geospatial Foundation Model for Agricultural Downstream Tasks (arXiv).md
# Harvesting AlphaEarth: Benchmarking the Geospatial Foundation Model for Agricultural Downstream Tasks

## Full citation
Ma, Y., Shen, Y., Swatantran, A., & Lobell, D. B. (2026). *Harvesting AlphaEarth: Benchmarking the Geospatial Foundation Model for Agricultural Downstream Tasks*. arXiv (under review; Stanford University + Corteva Agriscience). Code: github.com/yuchima8/Harvest_AlphaEarth

## Problem & setting
- Task: first systematic evaluation of **Google DeepMind's AlphaEarth Foundations (AEF)** embeddings for agricultural downstream tasks — county- and field-level crop yield prediction (corn, soybean, winter wheat), spring tillage mapping (high vs low intensity), and cover crop mapping — across the U.S. Corn Belt (12 states), 2017–2024.
- AEF: ~480M-param GFM, pretrained on ~3B images from ~5M locations (Landsat 8/9, Sentinel-1/2, GEDI LiDAR, ERA5-Land climate, GRACE gravity, GLO-30 elevation, Wikipedia text) via a Space-Time Precision encoder + teacher–student framework; produces **annual 64-dim embeddings at 10 m**, public on Google Earth Engine 2017–2024, gap-free and cloud-immune.
- Ground truth: USDA-NASS county yields/statistics (2017/2022 Census), plus private Corteva field-level data (89,938 corn + 73,492 soybean fields 2017–2018, 20,401 winter wheat 2017–2022; 24,514 tillage records; 47,709 cover-crop field-years).

## Method
- Comparison: RF and XGBoost (200 trees) trained either on **AEF 64-dim embeddings** or on **handcrafted RS features**: 80 harmonic-regression features (2nd-order Fourier fit of 6 Landsat bands + NDVI + GCVI, with peak/b30/a30 partial-integral phenology metrics) for yield; 66 monthly features incl. tillage indices (NDTI, STI, CRC) + elevation for tillage; 144 monthly harmonic min/max features Oct–May for cover crops; plus ERA5-Land GDD/precipitation.
- **Evaluation schemes designed to prevent spatial autocorrelation inflation:** State/County-Year CV, Yearly CV (train all years, test held-out year), Scale-Transfer (county→field), Space-Transfer (EPA ecoregions: Eastern Temperate Forests ↔ Great Plains; plus U.S.→Argentina soybean).

## Data & labels
- Labels are supervised (government statistics + grower-submitted records); AEF embeddings themselves are the SSL-pretrained "label-free" representation being evaluated. RS features derived from Landsat C2 Tier 1 SR, quality-masked, crop-masked via CDL, aggregated to county/field means.

## Results
- Yield, county-level: AEF XGB R² 0.78/0.78/0.78 (corn/soy/wheat, State-Year CV) vs RS XGB 0.80/0.79/0.71 — competitive; under Yearly CV AEF consistently better (e.g., wheat 0.78 vs 0.69) → stronger temporal generalization.
- Yield, field-level: AEF ≈ RS under County-Year CV (corn 0.44 vs 0.46); **Scale-Transfer (county→field) AEF collapses: corn R² 0.25 vs RS 0.38; wheat −0.04 vs 0.22** — county-averaged embeddings dilute field-level signal.
- Tillage: county R² ~0.47–0.52 both; field-level accuracy/F1 ~0.70–0.80, RS slightly better; both struggle with high-intensity tillage (F1-0 < F1-1 — brief residue windows).
- Cover crop: RS-RF best (accuracy ~0.80–0.85); AEF good at detecting cover crops (F1-1) but misclassifies negatives; largest yearly variability.
- **Space-Transfer failure:** corn East→West AEF R² 0.02 (RS 0.66); soybean East→West −0.28 (RS 0.53); U.S.→Argentina soybean: AEF R² −2.13 (all years fail) vs RS 0.27. t-SNE shows marked ecoregion separation of AEF embeddings — geographic shift is intrinsic (static DEM/gravity reconstruction + region-specific Wikipedia text inputs suspected).
- Interpretability: AEF bands A00–A63 lack physical meaning (top feature "A05" unexplainable); RS features are interpretable (GCVI > NDVI > raw bands).
- Other limits: temporal variability under yearly CV similar to RS; annual embeddings cannot support in-season/time-critical prediction; but AEF provides better spatial coverage (AEF retrievable for 90,210 corn records vs 89,938 for RS features — cloud/gap losses).

## What transfers to our thesis
- **The key negative result for the FM-versus-lightweight-model debate:** a 480M-param, 3B-image FM's embeddings are *not* consistently better than 80 handcrafted harmonic features + RF for agricultural regression/classification, and are dramatically worse for spatial transfer and scale transfer. This directly supports our thesis choice of small domain-specific SSL models with interpretable spectral/temporal features for in-field sugarcane deployment, over FM embeddings.
- Their critique set — **spatial transferability, interpretability, temporal sensitivity** — is exactly the evaluation axes our cross-year sugarcane models must address; we can cite AEF's failures as motivation for explicit cross-year validation and XAI.
- Harmonic-regression feature engineering (2nd-order Fourier coefficients + peak-window integrals from Landsat series) is a proven, cheap, physically interpretable featurization of 16-day Landsat time series that beat a 480M-param FM — a strong candidate baseline/predictor set for our stress-detection models, and a feature family our SSL encoder should at least match.
- Two-year concatenated embeddings for cover crops (cross-season tasks spanning calendar-year boundaries) is a design pattern applicable to sugarcane ratoon cycles and off-season salinity/water stress.
- The GCVI > NDVI feature-importance finding (saturation of NDVI in high biomass — sugarcane is a high-biomass crop) supports choosing saturation-resistant indices for sugarcane monitoring.
- Yearly-CV protocol (train all years, test one held-out year, 5 seeds, report variability) is a clean evaluation template for our cross-year experiments.

## Limitations / caveats
- Under review (preprint); U.S.-centric (Corn Belt + Argentina test), temperate row crops, no stress/anomaly task, no sugarcane.
- Only RF/XGBoost on tabular features — no fine-tuning of AEF's encoder itself or DL heads on embeddings; conclusions apply to embedding-as-features use, not all FM usage.
- Annual embeddings discard intra-seasonal dynamics; the authors note in-season prediction is impossible with AEF v1 — precisely the granularity stress detection needs.
- Private Corteva labels not fully public; country-transfer test limited to soybean county yields.

## Key numbers to quote in lit review
- AEF (480M params, 3B pretraining images) vs 80 harmonic RS features: county yield R² 0.78 vs 0.80; but scale-transfer corn R² 0.25 vs 0.38 and East→West corn R² 0.02 vs 0.66.
- U.S.→Argentina soybean transfer: AEF R² −2.13 vs RS features 0.27 — FM embeddings failed completely across continents.
- GCVI outperformed NDVI in RF feature importance (NDVI saturation in high-biomass crops).
- AEF advantages: gap-free cloud-immune 10-m annual 64-dim embeddings 2017–2024 on GEE; retrieved features for 90,210 vs 89,938 corn records (272 records lost to Landsat gaps with RS features).



---


## FILE: 2026 Major, Razmadze and Shavit - When Does Self-Supervised Learning Transfer to Time-Series Tasks (arXiv).md
# When Does Self-Supervised Learning Transfer to Time-Series Tasks?

## Full citation
Major, N., Razmadze, K., & Shavit, Y. (2026). *When Does Self-Supervised Learning Transfer to Time-Series Tasks?* arXiv:2605.19462v2 [cs.LG] (preprint, Bar-Ilan University). https://arxiv.org/abs/2605.19462

## Problem & setting
- Controlled benchmark answering: when do time-series SSL pretraining gains actually materialize, decoupled from architecture/data confounds? Seven representative SSL methods across 5 paradigms (reconstruction MAE; generative NTP + Diffusion; invariance DINO; contrastive SoftCLT; JEPA + LeJEPA) on a **shared channel-independent patched Transformer encoder** (8 layers, d=128, 16 heads, context 336, patch 16, 20 pretraining epochs), evaluated on anomaly detection (SMD, PSM, MSL, SMAP, SWaT), classification (9 UEA datasets), forecasting (ETT×4, Weather, Electricity, Traffic; horizons 96–720).
- Pretraining data: Monash archive (~680K series), scale-matched synthetic (TimePFN), scaled synthetic (2.5M), hybrid; plus in-domain pretraining controls for forecasting.
- Three protocols: linear probing, MLP probing, full fine-tuning — each paired with **matched random controls** (frozen random encoder for probing; supervised-from-scratch for fine-tuning); "SSL transfer gain" Δ defined formally; 5 seeds.

## Method (benchmark protocol details)
- MAE: 40% random patch masking, MSE on masked patches. NTP: 21 context / 6 target patches, causal. Diffusion (TimeDART-style): denoise Gaussian-corrupted patches conditioned on clean causal context. DINO: 1-D multi-crop augmentations, EMA teacher, centering + temperature sharpening. SoftCLT: hard instance InfoNCE + soft temporal contrast with distance-weighted pairs, TS2Vec-style overlapping-crop views. JEPA: multi-block masking (2×25%), EMA teacher, VICReg variance/covariance penalties. LeJEPA: no EMA teacher, SIGReg (sketched isotropic Gaussian) regularization; new DWT-based augmentation protocol introduced to prevent collapse.
- Anomaly metrics deliberately tripled: point-adjusted F1 (F1Pa), event-wise F1 (F1Ev), affiliation F1 (F1Af) — because rankings are metric-dependent.

## Data & labels
- Pretraining label-free (Monash/synthetic); downstream tasks use their standard supervised labels; controls isolate SSL-specific gains.

## Results
- **Anomaly detection = clearest SSL win:** SSL beats random frozen features in 54–94% of linear-probe configs (F1Ev 94%, F1Pa 54%), up to 97% under MLP probing; JEPA/LeJEPA improve MSL/SMAP F1Pa by >250% relative. Exception: on SWaT every SSL method underperforms random features.
- **Classification = moderate/selective:** linear-probe win rate 46% (MLP 40%); fine-tuning raises SSL win rate to 67% — pretraining is a good initialization but not always better than scratch. Gains concentrated in handwriting/digit/gesture; negative on EthanolConcentration, JapaneseVowels. LeJEPA best under linear probing (5/9 datasets) but only 2/9 after fine-tuning.
- **Forecasting = little to negative transfer:** SSL beats random frozen encoder in only 18% of MSE configs (linear probing), 31% MLP; fine-tuning from scratch beats pretrained backbones in >90% of runs. LeJEPA catastrophically degrades forecasting (−101%). In-domain pretraining beats Monash/synthetic for forecasting (34–42 wins vs 7–14 losses).
- **No universal method:** semantic/discrete tasks favor latent-space invariance objectives (LeJEPA), continuous-trajectory tasks favor signal-space objectives (Diffusion leads ETTh2; NTP leads ETTm1/SMD).
- **Linear probing ≠ fine-tuning outcomes:** rankings flip across protocols (Diffusion loses linearly but lowest MSE on ~90% datasets with MLP head; LeJEPA's probe lead disappears).
- **Scaling findings:** doubling pretraining 20→40 epochs ≈ no change (ties within seed variance); deeper encoders degrade forecasting (2-layer beats 8-layer in 14/21 pairs; 24-layer beats 8-layer in only 3/21) — vision/NLP scaling laws do not transfer to time-series SSL at these scales. Scale-matched synthetic pretraining is competitive with real Monash data (for classification, synthetic even wins 34/29); adding synthetic to real data hurts forecasting.

## What transfers to our thesis
- **Direct empirical support for the thesis's central bet:** SSL pretraining transfers reliably to *anomaly detection* (up to 94–97% win rate vs controls) — our label-free sugarcane stress detection is exactly an anomaly-detection-style downstream task, whereas forecasting (e.g., yield or NDVI forecasting) shows near-zero SSL benefit. This is a citable, controlled justification for framing our pipeline as SSL-encoder → anomaly/stress head rather than SSL → forecasting.
- **Methodological checklist to adopt:** (1) always include matched random-encoder and from-scratch controls; (2) report SSL transfer gain Δ; (3) never trust linear probing alone — evaluate MLP probing and fine-tuning (rankings flip); (4) report multiple anomaly metrics (F1Pa can mask poor event localization; use event-wise and affiliation F1) — directly relevant to how we report sugarcane stress-event detection.
- **Anti-scaling evidence:** deeper encoders and longer pretraining did not help time-series SSL; 2–4-layer backbones suffice — supports our lightweight multi-product model claim and warns against over-parameterizing the Landsat time-series encoder.
- **Domain-aligned pretraining > corpus scale:** in-domain data beat the large generic Monash corpus for forecasting; scale-matched synthetic matched real data. For us: pretraining on sugarcane-region Landsat history (in-domain) is expected to beat generic EO corpora — consistent with the STS-Net result (19.2K-param agri-specific CAE beating Presto).
- Caution: gains are dataset-dependent (SWaT negative) — our evaluation should include negative-control datasets/years to prove genuine transfer.
- The DWT-based augmentation (invariance to high-frequency sensor noise while preserving temporal morphology) is an immediately reusable augmentation design for cloud/noise-corrupted Landsat series.

## Limitations / caveats
- Generic time-series benchmarks (ETT, UEA, MSL/SMAP...), not remote sensing or vegetation series; Landsat-specific properties (seasonality, cloud gaps, spatial context) untested.
- Single backbone family (Transformer encoder); authors note state-space/conv models may scale differently.
- Dataset scales are modest (680K–2.5M series); they concede larger multi-domain corpora might change conclusions.
- Point-adjusted F1 known to be a flawed metric (they cite the critique) — their multi-metric protocol is the remedy.
- Preprint; single-seed depth sweeps.

## Key numbers to quote in lit review
- SSL pretraining beats matched random controls in up to 94% (linear) / 97% (MLP) of anomaly-detection configs, but only 18% of forecasting MSE configs — SSL transfer is task-dependent.
- Fine-tuning from scratch beats pretrained encoders in >90% of forecasting runs, but SSL wins 67% of classification fine-tuning configs.
- Encoder depth hurts: 2-layer > 8-layer in 14/21 forecasting pairs; 24-layer beats 8-layer in only 3/21.
- Doubling pretraining epochs (20→40) yields only ties within seed variance.
- Point-adjusted F1 vs event-wise vs affiliation F1 produce different method rankings — anomaly-detection evaluation must be multi-metric.



---


## FILE: 2026 Nedungadi - Foundation Models Meet Agriculture - Challenges Beyond Pretraining (arXiv).md
# Foundation Models Meet Agriculture: Challenges Beyond Pretraining

## Full citation
Nedungadi, V., Xiong, X., Rußwurm, M., & Athanasiadis, I. N. (2026). *Foundation Models Meet Agriculture: Challenges Beyond Pretraining*. arXiv:2608.30392 [cs.LG] (preprint; Wageningen University, Zhejiang Academy of Agricultural Sciences, University of Bonn). Code: github.com/vishalned/CropBench

## Problem & setting
- Diagnostic benchmark: why do EO foundation models (FMs) underperform in agriculture? Two formalized challenges: (1) **pretraining–downstream modality gap** — agricultural tasks need non-imagery modalities (deep soil, agro-meteorology, daily weather) that EO FMs cannot natively ingest; (2) **task heterogeneity** — agricultural monitoring varies across five structural axes (spatial unit, farming system, split design, target type, dataset size), producing unstable model rankings.
- 7 real-world datasets / 3 tasks: crop-type mapping — CropHarvest Kenya (smallholder, maize-vs-rest, imbalanced) and Breizhcrops France (parcel, 9 classes, 45 temporal steps); phenology — BloomBench Germany (maize tassel-emergence time-to-event from 365 daily ERA5 meteo steps); yield — CY-Bench (Germany/US/Senegal, sub-national maize+wheat, 30 countries) and YieldSAT Argentina (pixel-level corn from harvester monitors, 24 Sentinel-2 steps); sizes 400–1.27M samples.
- Models: supervised baselines (RF 500 trees, LSTM 2×128, Transformer 2 layers trained from scratch); EO FMs — Galileo (pixel time-series FM) and CropFM (idealized Presto-extension ingesting more modalities at weekly steps); tabular FM — TabPFN (no geospatial priors, no modality constraints). Adaption: full fine-tuning (two-stage warm-up: 5 epochs head-only lr 1e-4, then 25 epochs joint lr 1e-3) vs frozen features + RF.

## Method (evaluation design)
- Modality Coverage Matrix: percentage of each dataset's curated modalities (S2, S1, NDVI, FAPAR, DEM, basic meteo, agro-meteo, surface soil moisture, deep soil) natively ingestible by each model. Coverage: 100% (Breizhcrops, phenology) down to 22–36% (YieldSAT, CY-Bench) for the FMs.
- Standardized temporal aggregation (weekly composites; monthly for Galileo due to sequence limits), fixed hyperparameters across datasets, 3 seeds, dataset-appropriate splits (spatial holdout for Breizhcrops; chronological holdout for phenology and YieldSAT; walk-forward validation over final 5 years for CY-Bench).

## Data & labels
- Public benchmarks; labels remain supervised for all downstream tasks (FM pretraining is the SSL component under test). AlphaEarth/TESSERA global embedding products excluded (temporal granularity misalignment) — flagged as needing dedicated study.

## Results
- **Modality mismatch penalty is real but non-uniform:** with coverage 22–47% (yield tasks Germany/US), both FMs underperform the unconstrained RF baseline (negative ΔR²); at lowest coverage (Argentina) results are volatile (Galileo Δ≈+0.05, CropFM Δ≈−0.21). Even at ~100% coverage (Kenya, France crop mapping) FMs still lose ~0.16 F1 to baselines — modality alignment is necessary but not sufficient.
- **Exception (Senegal, smallholder, data-scarce):** frozen FM features beat RF (Galileo ΔR²≈+0.15, CropFM +0.06) — pretraining helps most when downstream data is too scarce for the baseline to fit. TabPFN strongest there (Δ≈+0.22).
- **Rank instability:** TabPFN best on CY-US (R² 0.65) and CY-DE (0.53 tied); CropFM-FT best on YS-AR (R² 0.33, while LSTM collapses to −0.15); from-scratch Transformer best on both crop-mapping datasets (F1 0.89 Kenya, 0.60 France); RF strongest on France among RF-family (0.50). No model wins consistently.
- **Fine-tuning risk:** full fine-tuning of Galileo catastrophically forgets on small localized datasets (CY-DE R²=−0.85; phenology MAE 53.42 days vs ~7–10 for other models).
- Modality coverage percentages: Galileo 100/100/100/94/22/47/36 across the seven datasets; CropFM similar except yield tasks.

## What transfers to our thesis
- **Strongest citable evidence yet that "foundation models ≠ automatic win" in agriculture:** even a purpose-built crop FM (CropFM) loses to RF/TabPFN on several tasks, and generic FMs pay modality-mismatch penalties — precisely our argument for training small domain-specific SSL models on exactly the modalities our sugarcane task needs (Landsat optical + LST + ETa proxies) instead of relying on FMs pretrained on fixed modality sets.
- The **Senegal result is a key nuance to quote honestly:** pretraining helps most under extreme label scarcity (smallholder, low-data regime) — this is the regime of our in-field sugarcane data, so it directly supports SSL pretraining for us, while the RF/TabPFN wins in data-rich settings temper overclaiming.
- **Fine-tuning catastrophe (Galileo R²=−0.85)** quantifies the risk of fine-tuning large FMs on small localized datasets — motivates frozen-encoder + lightweight head designs and careful warm-up schedules in our pipeline.
- The five structural axes (spatial unit, farming system, split design, target type, dataset size) are a ready-made framework for structuring our own cross-year/cross-field evaluation and for the lit review's critique of agricultural benchmarking.
- Modality Coverage Matrix concept can be reused to argue our case: Landsat thermal/LST and CWSI/ETa are modalities most EO FMs simply do not ingest — a structural argument for custom SSL.
- Walk-forward chronological validation and strict spatial holdouts are the correct protocols to copy for cross-year sugarcane evaluation.

## Limitations / caveats
- Preprint; LLM tools used for drafting (disclosed); only two EO FMs tested (Galileo, CropFM) — no sweeping of the FM zoo; no stress/anomaly tasks (crop type, phenology, yield only).
- Fixed hyperparameters favor robustness over peak performance; some datasets tiny (phenology N≈400, Senegal N≈3.4k) making conclusions fragile.
- Authors list their own limitations: limited EO models applicable, not truly global, simple baselines, possible pretraining-bias/leakage confounds.
- Sentinel-based datasets mostly; Landsat/thermal not central; no multisensor fusion learning proposed.

## Key numbers to quote in lit review
- EO FMs lose ~0.16 F1 to a plain RF even at ~100% modality coverage (Kenya, France crop mapping); under 22–47% coverage (yield tasks) they lose to RF outright.
- Under extreme label scarcity (Senegal, N≈3.4k smallholder), frozen FM features flip the result: ΔR² +0.15 (Galileo) and TabPFN +0.22 vs unconstrained RF — pretraining pays off exactly in data-scarce regimes.
- Full fine-tuning of Galileo on small local data collapses to R² = −0.85 (catastrophic forgetting); frozen-encoder + RF avoids this.
- No single model ranks consistently across 7 agricultural datasets — TabPFN best on US/Germany yield (R² 0.65/0.53), Transformer best on crop mapping (F1 0.89/0.60), CropFM-FT best on Argentina (0.33).
- Modality coverage of FMs drops to 22–36% on soil/meteo-dependent yield tasks — EO FMs architecturally cannot ingest deep soil and agro-meteorological inputs.



---


## FILE: 2026 Nie et al. - Rice Cropping Sequence Mapping via Agronomic Knowledge Graphs + Phenology + Remote Sensing (Ecological Informatics) [BONUS].md
# Rice cropping sequence mapping in the tropical monsoon zone via agronomic knowledge graphs integrating phenology and remote sensing [BONUS]

- **Full citation**: Nie, H., Lin, Y., Luo, W., & Liu, G. (2025/2026). "Rice cropping sequence mapping in the tropical monsoon zone via agronomic knowledge graphs integrating phenology and remote sensing." Ecological Informatics 87:103075, DOI: 10.1016/j.ecoinf.2025.103075 (open access; published online 14 Feb 2025). South China Normal University / Beijing Normal University.

- **Problem & setting**: Map three rice cropping sequences — double-cropping rice (DCR), early rice–fallow–winter crop rotation (EOWR), winter crop–fallow–late rice rotation (WOLR) — in a small (5.82 x 7.14 km) tropical monsoon area of the Leizhou Peninsula, China, where rainy-season cloud cover makes dense optical time series unavailable. Data: Landsat-7/8 Level-2 (30 m, gaps filled for L7; L8 Jul/Aug 2021 scenes cloud-masked and fused in GEE) + Sentinel-2 L2A resampled to 30 m, at 5 key time windows (Jan 1, Mar 30, Jun 10/18, Jul 12/Aug 13, Sep 29/30, Dec 3, 2021); GF-1 (2 m pan / 8 m MS) for object segmentation only.

- **Method** (supervised, knowledge-guided feature selection — no SSL): An "agronomic remote sensing knowledge graph" ontology links crop growth processes -> 5 key phenological events (I: winter crop planting/SOS of early rice; II: early-rice maturation/NDVI peak; III: early-rice harvesting/EOS; IV: late-rice maturation/NDVI peak; V: winter crop planting/EOS of late rice) -> corresponding remote sensing time windows -> feature subsets. Feature ablation design: a control group with all five event windows and five experimental groups (e.g., Exp.1 = only windows II+IV; Exp.5 = I,II,IV,V), each with 6-band surface reflectance + NDVI features. Classification: Random Forest, pixel-based (ENVI/ENMAP-BOX) and object-based (eCognition, multiresolution segmentation at scale 124, shape 0.9, compactness 0.1, chosen via ESP-2 local-variance tool); trees 75-105, min node samples 5-20 tuned.

- **Data & labels**: 42 field-collected crop samples (Feb 2023) + farmer interviews to assign 2021 sequence labels per object; 400 random points (min 100 m apart) interpreted from learned spectral/texture/NDVI-profile priors; 13 mixed-pixel/edge points removed; 387 points split 30% train (116) / 70% validation (334, with 4 DCR / 19 EOWR / 35 WOLR / 5 Others test samples added for class balance). Labels are field-derived, small-N, and partly inferred from remote sensing priors.

- **Results**: Pixel-based OA 83.48-92.49% (kappa 0.769-0.895); object-based OA 84.98-92.80% (kappa 0.787-0.900), consistently above pixel-based. Best = control (all 5 windows): 92.49% pixel / 92.80% object. Crucially, Exp.1 with ONLY the two rice maturation windows (II + IV) already reached 83.48% pixel / 84.98% object OA — i.e., two phenologically chosen dates recover ~91-92% of the full-window accuracy; window III (early-rice harvesting) contributed least (Exp.5 only 1.2% below control). WOLR was the hardest class (PA as low as 57.1-69.4% in sparse-feature groups). DCR dominated area (~15.8-17.7 km2 of 41.9 km2 mapped area).

- **What transfers to our thesis**:
  - Central transferable finding: agronomic knowledge (phenology events) can compress the effective input space — two well-chosen phenological time windows beat many indiscriminate features and nearly match full time-series accuracy. For our sugarcane/Landsat work, this justifies stage-conditional sampling windows (e.g., tillering, grand growth, maturity) instead of full 16-day stacks, which also reduces model size (lightweight models) and cloud sensitivity.
  - Demonstrates on Landsat(-7/8) + Sentinel-2 30 m data that a handful of cloud-free acquisitions at phenologically optimal dates suffices under heavy monsoon cloud — directly relevant to Landsat 16-day series with cloud gaps; supports window-selection/embedded-time-step strategies in our SSL pretraining or fine-tuning.
  - The knowledge-graph framing (phenology events -> time windows -> feature sets) is a structured way to inject prior agronomic knowledge without labels — complements our SSL objective as a feature-space prior rather than a loss prior.
  - Object-based (parcel) processing outperformed pixel-based classification (+0.3 to +2.4% OA, less salt-and-pepper) — supports parcel-level aggregation for sugarcane field stress mapping.
  - Phenological windows also structure cross-year comparability: sequences are identified by NDVI peak/harvest timing, echoing the stage-based analysis our thesis needs for cross-year stress comparison.

- **Limitations / caveats**: Small study area (41.9 km2) and tiny labeled sample (116 training points, some classes with only 6-12 training samples); phenological event dates fixed from prior agronomic knowledge — must be re-derived per region/year under climate change (authors note this); supervised RF only, no temporal deep model, no SSL; winter-crop/other class confusion from heterogeneous object interiors; NDVI-only temporal signal (authors suggest LSWI/SAR for paddy transplanting); single year (2021) — no cross-year validation; "knowledge graph" is essentially a hand-built ontology/feature-selection scheme, not a learned or queryable KG.

- **Key numbers to quote in lit review**:
  - Two phenologically selected time windows (early- and late-rice maturation) alone yield 83.5% (pixel) / 85.0% (object) OA vs 92.5% / 92.8% for all five windows — agronomic knowledge enables ~91% of full accuracy from 2 of 5 acquisitions.
  - Object-based RF consistently beats pixel-based: OA 84.98-92.80% (kappa up to 0.900) vs 83.48-92.49% (kappa up to 0.895).
  - Harvest-window features (III) contributed least: omitting them costs only 1.2% OA.
  - Five key phenological events suffice to structure rice cropping-sequence identification in a cloud-prone tropical monsoon zone using Landsat-7/8 + Sentinel-2 at 30 m.



---


## FILE: 2026 Pai et al. - Explainable AI in Agriculture - Review of Applications and Methodologies (IOP Eng Res Express).md
# Explainable AI in Agriculture: Review of Applications, Methodologies, and Future Directions

## Full citation
Pai, D. G., Balachandra, M., & Kamath, R. (2025/2026). *Explainable AI in agriculture: review of applications, methodologies, and future directions*. Engineering Research Express 7, 032202. DOI 10.1088/2631-8695/ae086a (IOP, topical review, open access).

## Problem & setting
- Topical review of XAI in agriculture, covering peer-reviewed work from 2020 onwards. Domains: crop–weed discrimination, plant disease detection, precision farming/crop recommendation, yield forecasting, soil quality monitoring. Motivation: DL models in agriculture are black boxes; adoption by farmers, agronomists, and policymakers requires transparency.

## Method (survey structure)
- **XAI taxonomy:** white-box vs black-box; model-specific vs model-agnostic; global vs local; intrinsic vs post-hoc. Comparison tables of techniques with properties, tools, and agricultural data fit:
  - **Grad-CAM** (model-specific, CNN heatmaps — leaf disease, weed detection), LIME (model-agnostic, local, superpixels/tabular), SHAP (model-agnostic, global+local, game-theoretic feature attribution — yield prediction from soil/rainfall/fertilizer tabular data), saliency/SmoothGrad (image noise-averaged saliency), LightGBM (interpretable boosting), decision trees/feature importance, counterfactual explanations (Alibi, DiCE), attention mechanisms.
- **Evaluation metrics for XAI itself:** sensitivity(-n), faithfulness correlation/estimate, monotonicity, selectivity, infidelity.
- Reviewed studies tabulated with models (VGG, ResNet, EfficientNet, MobileNet, YOLO variants), datasets (PlantVillage, Plant Seedlings, VegNet, tea-leaf sets, CottonWeedDet12 with 16,944 images), and per-study limitations.

## Results (synthesis)
- **Frequency: LIME most used, then Grad-CAM, SHAP, LightGBM, SmoothGrad;** among DL backbones, ResNet most used, then VGG. Task distribution: plant/leaf disease classification dominates, then yield prediction; vegetation mapping and plant phenotyping least explored (complex environmental/spatial data).
- Example results cited: LIME-explained 38-disease classifier at 99.69% accuracy/precision/recall; EfficientNetV2S 91% for grapevine downy mildew in field conditions; PPLC-Net F1 98.44% with CAM-based validation; YOLOv5-CAcT 94.24% avg accuracy over 59 crop disease categories; YOLOv8-nano + Layer-CAM/Grad-CAM++/Eigen-CAM for 12-class cotton weed detection on edge devices.
- Guiding principle: visual attribution (Grad-CAM/saliency) for image tasks; SHAP/LIME/feature importance for tabular/sensor tasks; counterfactual and concept-based explanations gaining traction for agronomic plausibility.
- Claimed benefit: XAI-enabled precision agriculture systems can reduce water consumption 15–25% while improving yields (as stated in conclusion).
- Challenges: limited generalizability across datasets, dataset bias, real-world applicability unexplored, SHAP computational cost at scale, no standardized XAI evaluation, need for large annotated datasets, accessibility for non-expert users in resource-limited regions.

## What transfers to our thesis
- **Directly maps to the XAI pillar of the thesis:** for our Landsat time-series stress models, the review's modality rule suggests: Grad-CAM/attention-style visualizations for any spatial/temporal encoder components (which dates and which bands drive a stress flag), SHAP/feature-importance for any tabular field-level models (index statistics, ETa/CWSI features), and counterfactual explanations ("which weather/irrigation change would flip this alert") for farmer-facing outputs.
- The XAI-evaluation metrics (faithfulness, selectivity, sensitivity-n, infidelity, monotonicity) are concrete tools to *quantify* explanation quality in our thesis — most remote sensing XAI papers skip this; including them would strengthen the methodology chapter.
- Gap statement to cite: vegetation mapping/phenotyping are the least XAI-explored agricultural tasks, and **satellite time-series stress detection is essentially absent** from the reviewed literature — positioning our work as filling a documented gap.
- Supports using XAI not just post-hoc but as a validation tool: their cited works use CAM overlays to verify the model looks at lesion regions; analogously we can verify stress alerts attend to drought-period observations rather than cloud artifacts or harvest signatures.
- Edge/XAI integration discussion (RepAgrViT, YOLOv8-nano + CAM on edge) aligns with our lightweight in-field deployment requirement.

## Limitations / caveats
- Review quality is mixed: tables rely on secondary description, some entries lack details ("Not Applicable"), and metrics are reported inconsistently across the reviewed literature (the review itself flags this).
- Almost no coverage of remote sensing/satellite XAI, temporal explanation (time-series attribution), or anomaly-detection explanations — the very areas our thesis needs; the review is image- and tabular-centric.
- The 15–25% water-saving figure is asserted without a traceable source — use with caution.
- No quantitative meta-analysis (no effect sizes, no systematic PRISMA-style counts); qualitative categorization only.

## Key numbers to quote in lit review
- LIME and Grad-CAM are the most frequently used XAI methods in agriculture (2020–2025 literature), with SHAP third; ResNet the most common backbone.
- XAI applications cluster in disease classification and yield prediction; vegetation mapping and plant phenotyping are least explored — satellite time-series stress detection is an open gap.
- Example headline results: 99.69% accuracy on 38 plant diseases (LIME-explained); 94.24% avg accuracy on 59 disease categories (YOLOv5-CAcT).
- XAI quality should be evaluated with faithfulness/selectivity/sensitivity/infidelity metrics, not just visual plausibility.
- Claimed XAI-enabled precision agriculture benefit: 15–25% water-use reduction (uncited — verify before quoting).



---


## FILE: 2026 Samanta and Saha - Affordable Precision Agriculture - Low-Cost Edge AI and TinyML Review (arXiv).md
# Affordable Precision Agriculture: A Deployment-Oriented Review of Low-Cost, Low-Power Edge AI and TinyML for Resource-Constrained Farming Systems

## Full citation
Samanta, R., & Saha, B. (2026). *Affordable Precision Agriculture: A Deployment-Oriented Review of Low-Cost, Low-Power Edge AI and TinyML for Resource-Constrained Farming Systems*. arXiv:2603.15085 [cs.ET] (preprint, Techno India University / Sister Nivedita University, India). https://arxiv.org/abs/2603.15085

## Problem & setting
- Deployment-oriented review (2023–2026 literature; 45 candidates screened → 34 full-text → 28 included) of Edge AI and TinyML in resource-constrained/smallholder agriculture. Motivation: cloud-centric smart farming fails under Indian smallholder realities — 86.21% of operational holdings <2 ha (avg 1.08 ha, 2015–16 Census), <20% of farmers actively using digital tech, intermittent power, poor rural connectivity.
- Five application domains: plant disease detection, precision irrigation, soil monitoring, crop recommendation, UAV-assisted distributed intelligence.

## Method (review + synthesis)
- Systematic Boolean searches across Google Scholar/IEEE/ScienceDirect/Springer/ACM/Scopus; inclusion criteria require on-device or near-edge inference, explicit resource constraints (flash/RAM/latency/energy), embedded hardware, peer-reviewed validation.
- **Three deployment architectures synthesized:** fully on-device (ESP32-CAM CNN, 103.9 KB RAM, 850 ms latency, 92% disease accuracy; 6.2 KB quantized NN for irrigation anomaly detection; ESP-EYE UAV 90% acc), edge-assisted (LoRa/IoT coordinated sensing with optional cloud), distributed collaborative (split learning, up to 86% energy reduction vs centralized training).
- **Proposed 4-layer privacy-preserving architecture:** physical sensing → inference execution (TinyML vs SBC on-device, or offloading) → edge processing (fusion, split learning) → cloud training/management (lifecycle, retraining, threshold updates pushed back to edge).
- Resource-profiled hardware: microcontroller class dominates (ESP32, STM32U575, ATMega328P, Arduino BLE 33, ESP-EYE) plus SBC (Jetson Nano, DBLA-MobileNetV2 FP16+TensorRT 97.90% precision, 12.40 FPS).

## Data & labels
- Reviews existing deployments; catalogs benchmark datasets per domain: PlantVillage (54k leaf images, 38 diseases) and PlantDoc (field conditions) for disease; **OpenET (30 m satellite ETa, field scale)** and International Soil Moisture Network (2,800+ stations) for irrigation; LUCAS (~45k European topsoil samples) and WoSIS (228k+ profiles, 174 countries) for soil; Kaggle Crop Recommendation (NPK+climate, 22 crops); Agriculture-Vision (94,986 RGB-NIR aerial images, 10 cm, 8 anomaly conditions incl. weeds, nutrient deficiency, drydown) and its SSL-pretraining extension for UAV.

## Results (quantitative synthesis)
- **Quantization is the dominant optimization (~50% of works use INT8/quantization);** structured pruning appears in only 1 of 13 tabulated works; hardware-aware NAS and multi-objective compression essentially absent; lightweight architecture design is near-universal.
- Headline resource numbers: 6.2 KB model (irrigation anomaly detection on MCU); 51.8 mJ/inference for INT8 YOLOv8n on STM32 (flash 850.97 KB, RAM 677.30 KB); 7.6 ms latency CNN (344.7 KB flash, 726.6 KB RAM); 99% model-size reduction for RF crop recommendation on ATMega328P; DVFS scheduling −8.5% energy; split learning −86% energy.
- **Resource-profiling gap identified:** RAM, MAC counts, and energy-per-inference are rarely reported; most quantized deployments omit energy evaluation — a reproducibility failure the review formalizes.
- Structural pattern: **inference increasingly localized, training centralized** ("inference–training asymmetry") — on-device adaptivity, federated TinyML, and edge fine-tuning named as research frontiers.
- Field-validation gap: most systems validated on curated datasets; multi-season field trials measuring yield gain, water savings, or earlier detection vs conventional scouting are rare.

## What transfers to our thesis
- **The deployment constraint chapter of our thesis:** quantitative evidence that microcontroller/SBC-class inference (6.2 KB–1 MB models, 51.8 mJ/inference, ~8 ms latency) is feasible for agricultural anomaly detection — directly supports the "lightweight multi-product in-field model" requirement for sugarcane deployments with intermittent connectivity/power.
- The **inference–training asymmetry** maps exactly onto our SSL design: SSL pretraining (and supervised fine-tuning) happens offline/centrally on multi-year Landsat archives; only a tiny frozen encoder + anomaly head ships to the field for local inference — a pattern the review identifies as the dominant and pragmatic architecture.
- Their diagnosis of **missing resource metrics (flash, RAM, MACs, mJ/inference)** is a checklist our thesis should adopt for its deployment evaluation — differentiating contribution from accuracy-only agri-AI literature.
- The identified optimization gap (pruning/NAS underused; quantization overused) suggests our model-compression strategy should include structured pruning + quantization jointly, and report both.
- Field-validation critique (multi-season trials, agronomic outcomes like water saved per hectare, earlier detection vs scouting) defines what "in-field cross-year validation" should mean in our thesis — aligns with cross-year evaluation and water/salinity stress outcomes.
- OpenET (30 m satellite ETa) as reference data is directly relevant to our ETa/CWSI water-stress pathway — usable as a label-free proxy/validation source for sugarcane water stress.

## Limitations / caveats
- Review covers only 28 studies, mostly small Indian prototypes; many lack rigorous baselines; some cited works by the same author group (self-citation pattern visible).
- No satellite time-series/remote sensing inference case is deeply treated (UAV imagery is the closest); the Landsat/EO-to-edge pipeline (download → compress → field inference) is not analyzed.
- Accuracy claims (90–97%) come from laboratory datasets (PlantVillage); the review itself flags generalization concerns to real fields.
- The proposed 4-layer architecture is conceptual, not evaluated.
- Preprint; editorial quality issues (typos, "MoReover").

## Key numbers to quote in lit review
- ~50% of agricultural TinyML deployments rely on quantization; structured pruning appears in only 1/13 studies; hardware-aware NAS essentially absent.
- Deployed footprints: 6.2 KB anomaly-detection NN; 51.8 mJ/inference (INT8 YOLOv8n, STM32); 7.6 ms latency CNN; 99% model-size reduction (RF on ATMega328P).
- 86.21% of Indian operational holdings are <2 ha (avg 1.08 ha) and <20% of farmers actively use digital technology — the smallholder deployment gap.
- Split learning cuts distributed-training energy by up to 86%; DVFS scheduling saves 8.5%.
- Structural finding: inference is local, training stays cloud-central — the prevailing and pragmatic architecture for constrained farming.



---


## FILE: 2026 Shah et al. - Embedding-Based Anomaly Detection for Cleaning Global Crop-Type Reference Data, Presto Embeddings (arXiv).md
# Embeddings based Anomaly Detection for Cleaning Global Crop Type Reference Datasets (EBA detector)

## Full citation
Shah, S. R. A., Van Tricht, K., Butsko, C., Degerickx, J., & Szantoi, Z. (2026). *Embeddings based Anomaly Detection for Cleaning Global Crop Type Reference Datasets*. arXiv:2607.23908v2 [cs.CV] (VITO Remote Sensing + ESA; WorldCereal project, ESA grant 4000130569/20/I-NB). Code: github.com/WorldCereal/EBA_detector

## Problem & setting
- Task: **label-noise detection / reference-data cleaning** for global crop-type and land-cover mapping (WorldCereal Reference Data Module, several million samples from LPIS parcel registers, LUCAS surveys, national databases, map-derived labels — each with distinct error modes).
- Key conceptual distinction: an EO outlier can be a genuine extreme event (drought, flood — scientifically valuable) or a label error; this work targets the latter — samples anomalous *relative to same-class neighbours in the same locality*, which indicates mislabelling rather than real events.
- Data: WorldCereal reference points (field centroids) with S1/S2/meteo/terrain time series composited to 12 monthly steps; labels grouped into coarser legend (e.g., wheat merged); Presto (lightweight SSL EO time-series transformer, 128-d embeddings, official pretrained weights, embeddings aligned to valid crop time); AlphaEarth 64-d embeddings tested as alternative.

## Method
- **Locality-aware embedding-based anomaly (EBA) detection:** slices = H3 hexagonal grid cells (level L∈{1,2,3}) × label (+dataset id, year); min 50 samples/slice, merge or exclude undersized slices. Within each slice, per-sample anomaly score combines (1) cosine distance to a **trimmed (contamination-resistant) centroid** (iteratively discard farthest τ fraction to defeat masking/swamping), and (2) mean cosine distance to k nearest same-class neighbours. Normalize by slice-specific empirical percentiles → average; combine with rank-based score and MAD-based robust z-score into mean_score.
- **Flagging:** MAD rule — flag when score exceeds slice median by >k=4 MADs, capped at 10% of slice; graded as normal / flagged / suspect (Srank>0.98) / candidate (Srank>0.99).
- **Confidence weighting:** confidence_nonoutlier = accelerating exponential decay applied only to flagged points (knee t=0.975 default / 0.95 tightened, γ=0.30/0.23); unflagged points keep confidence 1.
- **Safeguards:** silhouette-style separability gate pulls flagged confidence back to 1 where the frozen encoder fails to separate classes (degenerate neighbourhoods); embeddings from official pretrained weights avoid label leakage.
- **Treatments swept on training split:** baseline / drop candidates / drop candidates+suspects / drop all flagged / down-weight / confidence-threshold filters (0.90/0.95). Held-out split fixed and spatially split (H3 + source dataset) to prevent leakage; metrics on three test views (full, candidates-removed, confidence-weighted).
- Evaluation: (1) synthetic label-noise injection (gross / subtle confusable-class / whole-dataset corruption); (2) model-independent test (re-score fixed trained models after removing/down-weighting flagged test points); (3) downstream WorldCereal dual-head model across 5 macro-regions; CatBoost proxy sweeps; manual visual audit.

## Results
- **Synthetic recovery:** planted gross errors concentrated 4.3–5.0× above chance in flagged sets (AUROC up to 0.84, top-5% lift to 9×); subtle confusable errors 3.0–3.8× (AUROC ≈0.72); detection strongest at low noise rates typical of real data; whole-dataset corruption correctly at chance (≈1.0×, AUROC 0.50) — a stated limitation of any local detector. Weakest region Eastern Africa (2.5×, smallholder mixed cropping).
- **Model-independent test:** down-weighting flagged test points raises measured macro-F1/accuracy in 54/55 (crop type) and 55/55 (land cover) of 55 trained models per configuration — essentially deterministic.
- **Downstream cleaning:** with the tightened detector, best treatment improves WorldCereal crop-type macro-F1 in all 5 regions (+1.2 to +3.4, mean +2.1) and land cover in all 5 (+0.3 to +1.7). **Conservative cleaning wins: candidate removal or confidence weighting best; dropping all flagged points is the worst policy** (discards hard-but-correct boundary samples); CatBoost proxy confirms (filter_0.90 +0.7; drop_flagged −1.1).
- **Gains concentrated in rare/confusable classes** (e.g., millet +15 F1 points in Southern Asia); majority crops unchanged.
- **Ablations:** H3 locality matters (removing it: gross AUROC 0.79→0.66); off-the-shelf Isolation Forest/LOF on the same embeddings sit at chance (0.50) — the class-conditional local formulation is the differentiator; fine-tuned WorldCereal encoder improves recovery (gross 4.3×→4.9×, AUROC 0.79→0.84); AlphaEarth embeddings surface analogous anomalies (encoder-agnostic pipeline); visual audit found 0% "wrong" flags for crop classes (only "good" or "uncertain").

## What transfers to our thesis
- **Directly reusable for our thesis's data quality problem:** our sugarcane field labels (and any stress ground truth) will contain noise from inconsistent surveyors, mixed pixels, and temporal mismatches. The EBA recipe — SSL-encoder embeddings + same-class locality slices + trimmed centroid + MAD flagging + confidence weighting, with conservative cleaning — is an operational, citable template for cleaning our training reference data before fitting the stress models.
- **Conceptual framing worth adopting:** the dual nature of outliers (genuine extreme events vs label errors). For our stress detection, "anomalous relative to same-crop same-locality peers" is exactly the right null model: a drought-stressed sugarcane field is anomalous vs healthy peers (genuine signal), whereas a field labeled stressed but embedding-identical to healthy peers is a suspect label. This same locality-aware scoring can double as our label-free stress anomaly score itself, not just label cleaning.
- Design lessons with quantitative backing: (1) locality slicing is essential (removing H3 halves detection AUROC 0.79→0.66); (2) generic detectors (Isolation Forest, LOF) on good embeddings are useless without class-conditional, local formulation (chance level); (3) trimmed centroid prevents outlier self-masking; (4) conservative cleaning > aggressive cleaning (over-cleaning hurts: −1.1 macro-F1).
- Embeddings from a stronger/fine-tuned encoder improve label-error recovery (4.3→4.9×) — supports our plan to fine-tune the SSL encoder on sugarcane-region data before using its embedding space for anomaly scoring.
- The confidence-weighting (soft down-weighting instead of deletion) is a practical compromise for small in-field datasets where deleting samples is costly.

## Limitations / caveats
- Monthly 12-step composites (Sentinel-based WorldCereal), not 16-day Landsat; crop-type/land-cover labels, not stress labels.
- Point-level (field centroid) detection; no spatial segmentation or within-field heterogeneity.
- Cannot detect whole-dataset/systematic legend corruption by construction (acknowledged); frozen-encoder separation limits flags where the encoder is uninformative (silhouette gate mitigates only).
- WorldCereal downstream runs use a single seed (~±0.8 macro-F1 noise floor) — region-level gains near the floor are "suggestive"; synthetic injection defines ground truth only for scattered errors.
- Flagged points may be legitimate rare management practices or mixed pixels; removal-vs-weighting is a precision/recall choice requiring application-specific tuning.

## Key numbers to quote in lit review
- Embedding-based, locality-aware (H3 slice) anomaly detection recovers injected label errors at 2.5–5× above chance (AUROC up to 0.84); Isolation Forest/LOF on the same embeddings sit at chance (0.50).
- Conservative cleaning (candidate removal / confidence weighting) improves WorldCereal crop-type macro-F1 in all 5 macro-regions (+1.2 to +3.4); aggressive removal of all flagged points is the worst policy.
- Down-weighting flagged test points improves measured macro-F1 in 54/55 models (crop type) and 55/55 (land cover) — model-independent evidence that flags concentrate unreliable labels.
- Removing H3 locality drops gross-error recovery AUROC from 0.79 to 0.66 — locality is the key design element.
- Gains concentrate on rare/confusable classes (millet +15 F1); majority crops unaffected.



---


## FILE: 2026 Yang et al. - State Space Models Meet Remote Sensing - A Survey (Sci China Inf Sci, arXiv).md
# State Space Models Meet Remote Sensing: A Survey

## Full citation
Yang, Q., Liu, C., Xu, J., Shi, Z., & Zou, Z. (2026). *State Space Models Meet Remote Sensing: A Survey*. Science China Information Sciences (under review) / arXiv:2606.25329 [cs.CV] (Beihang University). Tracking repo: github.com/QinzheYang/Awesome-RS-State-Space-Model. Structured search of >300 RS-SSM works (Mar 2024–Dec 2025).

## Problem & setting
- Comprehensive survey of State Space Models (SSMs / Mamba) in remote sensing. Motivation: RS tasks demand dense prediction over large extents, multi-modal fusion (HSI/MSI/Pan/SAR/multi-temporal), and long-sequence temporal modeling — all cases where Transformer quadratic attention is costly and SSMs' linear complexity fits.

## Method (survey structure)
- **Background:** S4 (2022, HiPPO memory, linear-time sequence mixing) → Mamba/S6 (Dec 2023: input-dependent selective parameters + hardware-aware scan; ~5× faster inference than Transformers at matching accuracy) → Vision Mamba/VMamba (Jan 2024: SS2D 2-D selective scan).
- **Task taxonomy with benchmark tables:**
  - Classification (HSI): HSIMamba, SpectralMamba, 3DSS-Mamba, DualMamba, S2Mamba, GraphMamba — Houston2013: DualMamba OA 99.57/κ 99.51, 3DSS-Mamba 98.37; Indian Pines: S2Mamba OA 97.92 — multi-directional scanning mitigates inter-class confusion and works well on tiny/imbalanced classes (some classes ≤10 samples).
  - Segmentation (LoveDA): UNetMamba MIoU 53.35 (best in table) vs RS3Mamba 50.62, TransUNet 48.31 — multi-scale U-Net-style construction compensates SSM's lack of native multi-scale features.
  - Change detection (WHU/LEVIR/LEVIR+): M-CD F1 95.3 (WHU), CDMamba 93.76; ChangeMamba's three spatio-temporal modeling modes (sequential / cross / parallel token ordering) set the paradigm.
  - Detection, super-resolution (Fourier/wavelet-embedded SSMs: FMSR, IRSRMamba), denoising/dehazing (HSIDMamba 8-direction scan), pan-sharpening (Pan-Mamba channel-exchange + cross-modal scan), meteorological downscaling (MambaDS).
- **Architecture-design synthesis (the survey's core contribution):** 23 scanning strategies cataloged (bidirectional, cross, SS2D, zigzag, Hilbert curve, multi-directional local, shuffle, hierarchical, spatial-spectral continuous scan with 6 orderings, spectral-priority/cross/parallel, **time cross scan, spatio-temporal sequential/parallel modeling** — Fig. 3 (t)–(w) for temporal data); high-level frameworks (backbone-centric vs U-Net-based); hybrid designs (SSM+CNN for local detail, SSM+Transformer for global context, SSM+GNN); redundancy removal via self/cross-guided gating; frequency-domain integration.
- **Trade-off synthesis:** scanning strategies suit sequential data (HSI) and linear cost but are weak on local texture; structural hybrids recover local detail at higher compute; hybrids are now the dominant paradigm but partially erode SSM's efficiency advantage.

## Data & labels
- Survey; benchmarks are standard supervised RS datasets (Houston2013, Indian Pines, LoveDA, WHU, LEVIR-CD).

## Results (synthesis)
- Statistics (as of Dec 2025): classification is the most-published RS-SSM task (~1,469 citations), then segmentation (~1,042), change detection (~759), detection (~307), SR (~249), pan-sharpening (~186), denoising (~134).
- Key qualitative claims: multi-directional scans reduce causal bias of 1-D unfolding; SSM handles small/imbalanced classes well (Indian Pines); U-Net+SSM decoders (UNetMamba) are the strongest segmentation config; hybrid SSM-CNN is the mainstream recipe.

## What transfers to our thesis
- **Temporal scanning strategies (Fig. 3 t–w) are directly relevant:** time cross scan, spatio-temporal sequential and parallel modeling were designed for multi-temporal RS images — a Mamba-based encoder over our Landsat 16-day NDVI/NDRE/LST sequences with temporal-aware scan orders is a state-of-the-art-supported, linear-complexity alternative to transformers for the "lightweight" pillar (relevant given Major et al.'s finding that deep transformers don't help time-series SSL).
- The survey quantifies the SSM-vs-Transformer efficiency argument for wide-area/dense prediction — citable when justifying sequence-model choice for multi-year Landsat series (hundreds of time steps per field across years).
- Benchmark tables give concrete numbers for a "sequence models in RS" paragraph: e.g., UNetMamba 53.35 MIoU on LoveDA vs TransUNet 48.31; ChangeMamba/CDMamba spatio-temporal token ordering as precedent for our multi-year time-series ordering (chronological vs seasonal-cross vs parallel arrangements).
- Future-directions section maps to our constraints: (1) SSM-based RS foundation models (linear complexity for dense/wide-area tasks); (2) **efficient SSMs for edge devices** — distillation/pruning/quantization for SSMs is named as an open need, aligning with our in-field deployment; (3) noted limitation that LoRA/adapters do not yet support SSM fine-tuning — a practical caveat if we consider PEFT on SSM backbones.
- Honest limitations to echo in our own discussion: SSMs struggle with scale variation, fine-grained texture, and long-sequence stability — exactly the properties of 40-year Landsat series with sensor changes (L5→L9), so hybrid or bidirectional designs with explicit multi-scale handling are advised.

## Limitations / caveats
- Survey covers to Dec 2025; temporal SITS modeling remains a small fraction of the RS-SSM literature (mostly change detection, not long crop time series) — our application is comparatively unexplored, which is both an opportunity and a risk.
- Benchmark tables are compiled from original papers (not re-run) — heterogeneous protocols; comparisons indicative only.
- No agricultural crop-time-series SSM (e.g., sugarcane phenology) exists in the survey; nearest relatives are ChangeMamba and meteorological MambaDS.
- For the thesis: no evidence yet that SSM beats lightweight CNN/AE on crop stress tasks (cf. STS-Net's 19.2K-param 3D-CAE) — SSM should be an ablation, not an assumption.

## Key numbers to quote in lit review
- >300 RS-SSM papers since March 2024; classification (1,469 citations) and segmentation (1,042) dominate; 23 distinct scanning strategies cataloged, including 4 temporal modes (time-cross, spatio-temporal sequential/parallel).
- Mamba/S6: ~5× faster inference than Transformers at comparable accuracy, with linear sequence complexity — the efficiency argument for long Landsat series.
- UNetMamba 53.35 MIoU on LoveDA vs TransUNet 48.31 — SSM+U-Net hybrid is the strongest segmentation recipe.
- DualMamba 99.57% OA (Houston2013 HSI); SSMs show minimal performance drops on tiny, imbalanced classes (Indian Pines classes with ≤10 samples).
- Open gaps: SSM foundation models, SSM edge acceleration (distillation/pruning/quantization), and PEFT (LoRA) incompatibility with SSMs.



---

