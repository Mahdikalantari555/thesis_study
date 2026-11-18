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
