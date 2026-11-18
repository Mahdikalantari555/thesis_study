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
