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
