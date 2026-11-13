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
