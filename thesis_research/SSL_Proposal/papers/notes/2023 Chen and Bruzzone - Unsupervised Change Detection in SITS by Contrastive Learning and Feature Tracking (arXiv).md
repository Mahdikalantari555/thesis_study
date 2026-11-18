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
