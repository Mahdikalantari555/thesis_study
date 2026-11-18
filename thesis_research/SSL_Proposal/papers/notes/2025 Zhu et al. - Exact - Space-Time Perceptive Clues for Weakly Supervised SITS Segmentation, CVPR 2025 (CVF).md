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
