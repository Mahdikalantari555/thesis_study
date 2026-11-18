# Foundation Models Meet Agriculture: Challenges Beyond Pretraining

## Full citation
Nedungadi, V., Xiong, X., Rußwurm, M., & Athanasiadis, I. N. (2026). *Foundation Models Meet Agriculture: Challenges Beyond Pretraining*. arXiv:2608.30392 [cs.LG] (preprint; Wageningen University, Zhejiang Academy of Agricultural Sciences, University of Bonn). Code: github.com/vishalned/CropBench

## Problem & setting
- Diagnostic benchmark: why do EO foundation models (FMs) underperform in agriculture? Two formalized challenges: (1) **pretraining–downstream modality gap** — agricultural tasks need non-imagery modalities (deep soil, agro-meteorology, daily weather) that EO FMs cannot natively ingest; (2) **task heterogeneity** — agricultural monitoring varies across five structural axes (spatial unit, farming system, split design, target type, dataset size), producing unstable model rankings.
- 7 real-world datasets / 3 tasks: crop-type mapping — CropHarvest Kenya (smallholder, maize-vs-rest, imbalanced) and Breizhcrops France (parcel, 9 classes, 45 temporal steps); phenology — BloomBench Germany (maize tassel-emergence time-to-event from 365 daily ERA5 meteo steps); yield — CY-Bench (Germany/US/Senegal, sub-national maize+wheat, 30 countries) and YieldSAT Argentina (pixel-level corn from harvester monitors, 24 Sentinel-2 steps); sizes 400–1.27M samples.
- Models: supervised baselines (RF 500 trees, LSTM 2×128, Transformer 2 layers trained from scratch); EO FMs — Galileo (pixel time-series FM) and CropFM (idealized Presto-extension ingesting more modalities at weekly steps); tabular FM — TabPFN (no geospatial priors, no modality constraints). Adaption: full fine-tuning (two-stage warm-up: 5 epochs head-only lr 1e-4, then 25 epochs joint lr 1e-3) vs frozen features + RF.

## Method (evaluation design)
- Modality Coverage Matrix: percentage of each dataset's curated modalities (S2, S1, NDVI, FAPAR, DEM, basic meteo, agro-meteo, surface soil moisture, deep soil) natively ingestible by each model. Coverage: 100% (Breizhcrops, phenology) down to 22–36% (YieldSAT, CY-Bench) for the FMs.
- Standardized temporal aggregation (weekly composites; monthly for Galileo due to sequence limits), fixed hyperparameters across datasets, 3 seeds, dataset-appropriate splits (spatial holdout for Breizhcrops; chronological holdout for phenology and YieldSAT; walk-forward validation over final 5 years for CY-Bench).

## Data & labels
- Public benchmarks; labels remain supervised for all downstream tasks (FM pretraining is the SSL component under test). AlphaEarth/TESSERA global embedding products excluded (temporal granularity misalignment) — flagged as needing dedicated study.

## Results
- **Modality mismatch penalty is real but non-uniform:** with coverage 22–47% (yield tasks Germany/US), both FMs underperform the unconstrained RF baseline (negative ΔR²); at lowest coverage (Argentina) results are volatile (Galileo Δ≈+0.05, CropFM Δ≈−0.21). Even at ~100% coverage (Kenya, France crop mapping) FMs still lose ~0.16 F1 to baselines — modality alignment is necessary but not sufficient.
- **Exception (Senegal, smallholder, data-scarce):** frozen FM features beat RF (Galileo ΔR²≈+0.15, CropFM +0.06) — pretraining helps most when downstream data is too scarce for the baseline to fit. TabPFN strongest there (Δ≈+0.22).
- **Rank instability:** TabPFN best on CY-US (R² 0.65) and CY-DE (0.53 tied); CropFM-FT best on YS-AR (R² 0.33, while LSTM collapses to −0.15); from-scratch Transformer best on both crop-mapping datasets (F1 0.89 Kenya, 0.60 France); RF strongest on France among RF-family (0.50). No model wins consistently.
- **Fine-tuning risk:** full fine-tuning of Galileo catastrophically forgets on small localized datasets (CY-DE R²=−0.85; phenology MAE 53.42 days vs ~7–10 for other models).
- Modality coverage percentages: Galileo 100/100/100/94/22/47/36 across the seven datasets; CropFM similar except yield tasks.

## What transfers to our thesis
- **Strongest citable evidence yet that "foundation models ≠ automatic win" in agriculture:** even a purpose-built crop FM (CropFM) loses to RF/TabPFN on several tasks, and generic FMs pay modality-mismatch penalties — precisely our argument for training small domain-specific SSL models on exactly the modalities our sugarcane task needs (Landsat optical + LST + ETa proxies) instead of relying on FMs pretrained on fixed modality sets.
- The **Senegal result is a key nuance to quote honestly:** pretraining helps most under extreme label scarcity (smallholder, low-data regime) — this is the regime of our in-field sugarcane data, so it directly supports SSL pretraining for us, while the RF/TabPFN wins in data-rich settings temper overclaiming.
- **Fine-tuning catastrophe (Galileo R²=−0.85)** quantifies the risk of fine-tuning large FMs on small localized datasets — motivates frozen-encoder + lightweight head designs and careful warm-up schedules in our pipeline.
- The five structural axes (spatial unit, farming system, split design, target type, dataset size) are a ready-made framework for structuring our own cross-year/cross-field evaluation and for the lit review's critique of agricultural benchmarking.
- Modality Coverage Matrix concept can be reused to argue our case: Landsat thermal/LST and CWSI/ETa are modalities most EO FMs simply do not ingest — a structural argument for custom SSL.
- Walk-forward chronological validation and strict spatial holdouts are the correct protocols to copy for cross-year sugarcane evaluation.

## Limitations / caveats
- Preprint; LLM tools used for drafting (disclosed); only two EO FMs tested (Galileo, CropFM) — no sweeping of the FM zoo; no stress/anomaly tasks (crop type, phenology, yield only).
- Fixed hyperparameters favor robustness over peak performance; some datasets tiny (phenology N≈400, Senegal N≈3.4k) making conclusions fragile.
- Authors list their own limitations: limited EO models applicable, not truly global, simple baselines, possible pretraining-bias/leakage confounds.
- Sentinel-based datasets mostly; Landsat/thermal not central; no multisensor fusion learning proposed.

## Key numbers to quote in lit review
- EO FMs lose ~0.16 F1 to a plain RF even at ~100% modality coverage (Kenya, France crop mapping); under 22–47% coverage (yield tasks) they lose to RF outright.
- Under extreme label scarcity (Senegal, N≈3.4k smallholder), frozen FM features flip the result: ΔR² +0.15 (Galileo) and TabPFN +0.22 vs unconstrained RF — pretraining pays off exactly in data-scarce regimes.
- Full fine-tuning of Galileo on small local data collapses to R² = −0.85 (catastrophic forgetting); frozen-encoder + RF avoids this.
- No single model ranks consistently across 7 agricultural datasets — TabPFN best on US/Germany yield (R² 0.65/0.53), Transformer best on crop mapping (F1 0.89/0.60), CropFM-FT best on Argentina (0.33).
- Modality coverage of FMs drops to 22–36% on soil/meteo-dependent yield tasks — EO FMs architecturally cannot ingest deep soil and agro-meteorological inputs.
