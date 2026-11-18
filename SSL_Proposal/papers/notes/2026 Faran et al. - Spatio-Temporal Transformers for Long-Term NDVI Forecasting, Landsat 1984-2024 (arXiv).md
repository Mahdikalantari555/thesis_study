# Spatio-Temporal Transformers for Long-Term NDVI Forecasting (STT-LTF)

## Full citation
Faran, I., Netanyahu, N. S., & Shoshany, M. (2026). *Spatio-Temporal Transformers for Long-Term NDVI Forecasting*. arXiv:2602.01799 [cs.CV]. https://arxiv.org/abs/2602.01799 (extension of Faran et al. 2025, ICPRAM, "Self-supervised transformers for long-term prediction of Landsat NDVI time series").

## Problem & setting
- Task: self-supervised **long-term NDVI forecasting** on Landsat — predict NDVI at an arbitrary future timestamp (Δ up to years ahead) from multi-decade history, for a heterogeneous Mediterranean-to-arid gradient (SE Mediterranean basin, rainfall 250–450 mm/yr, shrubland→phrygana→desert; desertification monitoring motivation).
- Data: Landsat 5/7/8/9, 1984–2024, 30 m, GEE Level-2 SR; study area 53.94×37.35 km (1,798×1,245 px); bi-annual median composites (winter Oct–Apr "growing", summer May–Sep "dormant"); <20% cloud; **2,238,510 pixel time series**. Temporal split: 1984–2013 train/val, 2014–2024 test (true future generalization).

## Method
- **Formulation:** input O = {(NDVI patch Xt ∈ R^{N×N}, month Mt, year Yt, lat, lon) | t=0..T} plus target (M_{T+Δ}, Y_{T+Δ}); model f predicts NDVI at T+Δ directly — **non-autoregressive, target time as input parameter**, no recursive error accumulation.
- **Three SSL masking strategies (training augmentation):** (1) spatial masking — random spatial window n<N, zero outside central n×n (scale invariance); (2) temporal masking — random prefix truncation T′<T (robustness to irregular/missing observations); (3) future horizon sampling — Δ ~ Uniform{1..Ymax−T} (multi-horizon competence).
- **Embeddings:** linear projection of flattened N×N NDVI patch (128-D); cyclical month encoding (sin/cos 2πM/12); year normalized to dataset range and linearly projected; lat/lon converted to 3-D unit-sphere Cartesian coords then linear (8-D); sinusoidal positional encoding. Concatenated → 256-D.
- **Architecture:** 3 transformer encoder blocks, 8 attention heads, dropout 0.2; regression decoder (2-layer FC, ReLU, dropout) on the target-time token → scalar NDVI. **MAE (L1) loss**, Adam lr 2e-4, 150 epochs. Fully label-free (supervision = future observed NDVI).

## Data & labels
- No labels at all; ground truth for training/testing is the actual observed future NDVI from the archive. Temporal split enforces genuine forecasting evaluation.

## Results
- Best next-year prediction: **MAE 0.0328, R² 0.8412** (10-year input) — beats SVM (0.0456/0.746), CNN-1D (0.0391/0.781), FC (0.0383/0.795), LSTM (0.0363/0.809), vanilla Transformer (0.0361/0.818), TFT-configured baseline.
- Temporal depth dominates spatial extent: 20-year sequence, patch 1×1: MAE 0.025/R² 0.922; 1-year sequence: MAE ~0.098/R² ~0.03–0.09. Gains saturate after ~10–15 years. Patch size 1×1→9×9 changes little (R² 0.922→0.927 at 20 years); 7×7 px (~210 m) is the practical optimum — larger windows dilute with mixed land cover.
- Model captures seasonal + inter-annual trends but misses abrupt outliers (fires, sudden events) — deviation from trend is precisely the residual signal.

## What transfers to our thesis
- **Same sensor family and cadence as our thesis:** Landsat 5/7/8/9, 30 m, 16-day acquisitions composited — this paper demonstrates that 40 years of unlabeled Landsat NDVI alone can train a useful SSL forecaster; our sugarcane water/salinity setting can reuse the exact data pipeline (bi-annual/seasonal median composites, temporal split).
- Design elements directly adoptable: (1) **cyclical month + normalized-year encodings** for cross-year transfer; (2) **3-D Cartesian lat/lon location encoding**; (3) **target-time-as-input non-autoregressive heads** — lets one model answer "what should NDVI/NDRE be at date X?" in a single pass, which is exactly the backbone of an expected-vs-observed anomaly score for stress detection; (4) horizon sampling during training so the model handles irregular observation gaps.
- Forecast-residual anomaly detection: their model "struggles with unexpected outliers" — reframed, forecast error itself becomes a label-free stress/anomaly signal; a sugarcane field whose NDVI/LST trajectory departs from the 10-year learned expectation is a candidate stress flag. This is a concrete, lightweight alternative to contrastive pipelines.
- Quantitative guidance: temporal depth >> spatial context for vegetation prediction (R² 0.03→0.92 from 1→20 years vs +0.005 for 9×9 patches) — supports prioritizing long multi-year Landsat series over spatial neighborhood size for our per-field stress features; keep spatial patches small (≤7×7 px ≈ 210 m).
- The arid/Mediterranean gradient with drought cycles is climatically closer to our water-stress setting than temperate benchmarks.

## Limitations / caveats
- NDVI only — single index, no thermal/LST, no salinity signal; natural-vegetation focus (shrubland/desert margin), not cropland or sugarcane.
- Bi-annual composites (2 obs/year) discard the intra-seasonal dynamics that matter for stress timing; 16-day series would need adaptation.
- Forecast quality degrades with horizon; abrupt-event outliers unmodeled (they call it a weakness; we would exploit it for anomaly detection).
- Pixel-wise, no explicit field/parcel semantics; geographic transferability (other regions) left as future work — only temporal generalization is tested.
- MAE loss and regression head are simple; no uncertainty estimates.

## Key numbers to quote in lit review
- 40 years of unlabeled Landsat (2.24M pixel series) → next-year NDVI MAE 0.0328 / R² 0.8412, beating LSTM (0.0363/0.809) and TFT-style baselines.
- Temporal depth is decisive: R² rises from 0.09 (1-year history) to 0.92 (20-year history); spatial patches beyond 7×7 px (210 m) give negligible gains.
- 10-year history is the practical sweet spot before saturation.
- Non-autoregressive direct prediction at arbitrary future dates avoids recursive error accumulation.
