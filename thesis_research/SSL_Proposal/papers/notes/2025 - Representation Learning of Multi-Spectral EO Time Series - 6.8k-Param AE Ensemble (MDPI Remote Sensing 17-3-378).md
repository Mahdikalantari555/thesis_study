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
