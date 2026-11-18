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
