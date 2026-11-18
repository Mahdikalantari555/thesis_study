# Crop type mapping in the pre-Sentinel era using variable-length Landsat time-series and self-supervised learning

## Full citation
Wijesingha, J., & Beila, I. (2026). *Crop type mapping in the pre-Sentinel era using variable-length Landsat time-series and self-supervised learning*. Frontiers in Remote Sensing 7:1782148. DOI 10.3389/frsen.2026.1782148

## Problem & setting
- Task: crop-type mapping with **Landsat-only** satellite image time series (L-SITS) for the pre-Sentinel era (before 2014), where no 5–10-day revisit data exist. Two German districts (Ammerland, Vechta; Lower Saxony), 2010–2018 (2012 excluded due to cloud/Landsat 7-only gap).
- Input per field: variable-length series (5–25 observations/season, March–October) from Landsat 5/7/8 Collection-2 Level-2 SR; 6 bands (blue, green, red, NIR1, SWIR1, SWIR2) + 4 VIs (NDVI, EVI, OSAVI, NDMI) + day-of-year encoding. Field polygons ≥0.9 ha (≥10 Landsat pixels) from IACS data; ~27.5k fields/year. Classes: CTL1 (4 classes) and CTL2 (9 classes).
- Core problem: supervised models need fixed-length series (padding/truncation distorts sparse Landsat data) and labels are scarce; SSL + transformer handles variable length and reduces label needs.

## Method
- **SITS-BERT (Yuan & Lin 2021) re-implemented on Landsat:** observation embedding (value array + DoY positional encoding — DoY enables cross-year transfer) + standard transformer encoder (max length 64, 10 features, 8 attention heads, batch 256, lr 1e-4).
- **SSL pretext:** random observations are selected, noised/corrupted, and the model must reconstruct original values from the remaining sequence context; MSE loss between reconstructed and true corrupted values. Pre-trained on 5 years of unlabeled L-SITS (2011, 2013, 2014, 2016, 2017), 50 epochs; best model epoch 49, train MSE 0.01639, val MSE 0.01356.
- Fine-tuned with a classification head: Case I = single-year (2015, 28,176 field-observations), Case II = 3 years (2014–2016, 84,139). Baseline: Random Forest on fixed-length bi-monthly median series (40 features).
- Temporal transfer tested both directions: Scenario I (past: 2010–2011) and Scenario II (future: 2017–2018).

## Data & labels
- Labels: IACS/Government crop-declaration polygons (supervised fine-tuning only; pretraining label-free). Variable-length series preserve all cloud-free acquisitions (RF used 5–17% fewer data points due to fixed-length reconstruction).

## Results
- Case I (single year): SITS-BERT CTL1 OA 0.833 (past) / 0.784 (future) vs RF 0.752 / 0.724; CTL2 OA 0.759 / 0.644 vs RF 0.702 / 0.652. SSL-BERT clearly beats RF when labels/observations are limited.
- Case II (3 years): CTL1 OA 0.855 / 0.807; CTL2 0.771 / 0.725. Multi-year fine-tuning lifts worst-case CTL2 OA from 0.644 → 0.725 (~16% relative). With 3 years, RF narrows the gap or wins CTL2 (0.789/0.771).
- Accuracy vs number of observations: CTL1 accuracy >80% for ≥7 observations; even 5–6 observations stay usable (67–70%); worst cases trace to seasonally bunched acquisitions (5 obs all in July).
- Per-class: winter crops F1 0.909–0.941; maize F1 0.893–0.933; hard classes: winter wheat vs winter cereals, root crops/vegetables merged class (merging for sample size did not help).

## What transfers to our thesis
- Closest architectural template in this batch for our setting: **Landsat 16-day variable-length field-level time series + BERT-style masked/reconstruction SSL pretraining + lightweight fine-tuning head** — exactly our optical sensor, temporal density (5–25 obs/season matches Landsat-7/8 dual availability), and DoY positional encoding trick for cross-year transfer.
- Quantifies the cross-year transferability problem on Landsat: performance drops from training year to past/future years (0.855 → 0.807 CTL1, 3-year training), and multi-year fine-tuning mitigates — direct evidence for our cross-year model design (train on multiple years, evaluate on held-out years).
- Shows DoY-based temporal encoding (rather than index positions) is the mechanism that makes single-year-trained transformers transferable across years — adopt in our encoder.
- Accuracy degrades gracefully with sparse observations (>80% at ≥7 obs), supporting our premise that label-free monitoring is feasible with cloud-limited Landsat density.
- Sugar context: sugarcane multi-year ratoon cycles are analogous to their multi-year fine-tuning benefit; their case II design maps to our cross-year sugarcane model.

## Limitations / caveats
- Downstream task is supervised crop-type classification with IACS labels; SSL used only for pretraining, not for label-free anomaly/stress detection.
- Moderate accuracies (CTL2 0.64–0.78) well below Sentinel-2 equivalents (SITS-BERT original ~0.9+); sparse 16-day revisit is the bottleneck.
- No thermal band/LST; 30 m pixels force ≥0.9 ha field minimum — smallholder sugarcane plots may be excluded.
- 2012 single-satellite year unusable — our thesis must plan for degraded-years robustness.
- Two districts, temperate crops; no salinity/water stress, no arid region.

## Key numbers to quote in lit review
- First transformer-SSL application to Landsat-only SITS for crop mapping: OA 0.78–0.85 (4-class) and 0.64–0.78 (9-class) across single/multi-year and past/future transfer.
- Multi-year fine-tuning raises worst-case 9-class OA by ~16% relative (0.644 → 0.725).
- SITS-BERT with single-year labels beats RF on fixed-length series (CTL1: 0.833 vs 0.752 OA, past-year transfer).
- Variable-length Landsat series contain 5–25 cloud-free observations per March–October season; accuracy >80% for CTL1 with ≥7 observations.
