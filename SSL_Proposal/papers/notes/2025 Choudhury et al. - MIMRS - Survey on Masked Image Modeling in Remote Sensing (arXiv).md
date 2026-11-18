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
