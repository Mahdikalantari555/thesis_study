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
