# XAI-Guided Enhancement of Vegetation Indices for Crop Mapping

## Full citation
Najjar, H., Mena, F., Nuske, M., & Dengel, A. (2024). "XAI-Guided Enhancement of Vegetation Indices for Crop Mapping." IGARSS 2024, arXiv:2407.08298v1 (RPTU Kaiserslautern-Landau / DFKI).

## Problem & setting
- Crop-type classification from Sentinel-2 time series in Ghana + South Sudan (Rustowicz et al. 2019 African crop dataset), Jan-Dec 2016, 10 m, 10 S2 bands + cloud-coverage channel; classes with >10k pixels: maize (329,847 px), groundnut (101,314), rice (98,986), soybean (67,638), sorghum (65,185), yam (22,091).
- Goal: use XAI feature attribution (not SSL) to find which bands matter, then design/select vegetation indices (VIs) that compress the model input.

## Method
- **Supervised pipeline, XAI-guided feature engineering**: (1) train a GRU (pre-padded to length 228, weighted sampler for imbalance) on all 10 bands; (2) attribute band importance with **Shapley Value Sampling (SVS)** — up to 10,000 correctly classified pixels per class, attributions grouped over time per band, negatives suppressed, per-pixel normalized to sum 1, averaged globally and per class; (3) select/modify VIs to cover high-attribution bands; (4) retrain on individual VIs or pairs of two.
- Newly proposed indices: n-NDVI (n-NIR instead of NIR), NDRE2 (RE2), NDRE3 (RE3), NDMI2 (SWIR2). Constraint: each index contains at least one 10 m band.

## Data & labels
- Fully supervised; labels from the public African crop segmentation dataset; 5% validation split, patch-disjoint (pixels of the same image patch never split across train/val).

## Results
- Baseline GRU on 10 bands: OA 67%, weighted F1 0.67 (rice 0.84, sorghum 0.86, yam only 0.27).
- Attribution ranking (global): SWIR1 and RE1 each ~20% of total importance, then red, SWIR2, n-NIR, NIR; cloud mask channel marginal (no leakage).
- Single VI: NDMI (NIR-SWIR1) best, OA 0.65 (-2 pp vs baseline) but beats baseline on sorghum, groundnut, yam; NDMI2 (SWIR2) best for rice (0.76); NDVI best for maize/soybean.
- Two VIs: **NDRE + NDMI2 = OA 0.70 / F1 0.70, +3 pp over the all-band baseline**, best for sorghum (0.88), maize (0.70), rice (0.83), and beats baseline on groundnut and yam. NDMI + n-NDVI comparable (0.68). NDRE+n-NDVI worst.
- Proposed NDMI2 > NDMI for rice confirms the SWIR2 attribution; NDRE2/NDRE3 underperform NDRE except for soybean/sorghum, matching their RE2/RE3 attributions.

## What transfers to our thesis
- **Recipe for our XAI thread**: train model on raw bands -> Shapley Value Sampling per band (temporal aggregation) -> design minimal indices. Translates directly to Landsat: e.g., verify whether an ETa/CWSI-proxy index (thermal + SWIR-based, Landsat lacks red-edge) plus one SWIR/water index suffices for sugarcane water/salinity stress.
- Justifies **lightweight multi-product models**: two VIs (2 channels instead of 10 bands) gave +3 pp over the full-band baseline in medium-sized datasets — supports our claim that compact, index-based inputs (NDVI + LST/NDMI/NDWI-like) can outperform band-stacks on moderate data, easing in-field deployment.
- For stress (not just type): SWIR1/SWIR2 importance for water-related discrimination (rice/yam) supports using NDMI/NDWI-style and thermal indices in salinity/water-stress detection; note Landsat has SWIR1/SWIR2 and thermal, but no red-edge — XAI-guided index design must be sensor-aware.
- Caveat they explicitly state: explanation quality is bounded by model accuracy (OA 67% baseline) — in our thesis, XAI on SSL embeddings needs a validated downstream task first.

## Limitations / caveats
- Supervised only — no SSL, no label-free setting; single year (2016), two countries; medium-size data with heavy class imbalance (yam 22k px).
- SVS on 10k pixels/class is computationally heavy and attribution-to-VI mapping is partially inconsistent (soybean/yam RE behavior contradicts attributions).
- Baseline GRU accuracy modest (67%), so attribution reliability is limited by model quality (acknowledged by authors).

## Key numbers to quote in lit review
- Two XAI-selected indices (NDRE + NDMI2) beat the 10-band baseline: OA 70% vs 67% (+3 pp) on African crop mapping.
- Single NDMI index alone reaches OA 65% (-2 pp only) — vegetation-index compression retains most signal.
- SVS attribution: SWIR1 and red-edge-1 carry ~20% importance each for crop discrimination in S2 time series.
- Landsat-relevant: SWIR2 (NDMI2) was the single best index for rice (water-associated) — supports SWIR/thermal indices for water-stress detection on Landsat.
