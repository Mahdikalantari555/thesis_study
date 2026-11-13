# Method Design — SSL Anomaly Detection for Sugarcane Stress (Amirkabir, Khuzestan)

**Frame:** Label-free detection of anomalous (stressed) vs. normal sugarcane fields from a 12-year Landsat SITS archive, with optional typing into Water_Only / Salinity_Only / Mixed_Stress via 50–100 expert labels.  
**Companion:** `literature_review_ssl.md`, `00_SSL_questionnaire.md`, `Thesis_Vault/04-Thesis-Design.md`.

---

## 1. Pipeline

```
Landsat 8/9 L2 (2013–2026, 539 overpasses)
    ↓
CFMASK cloud mask → 16-day composites (cubic-spline) → geometry-aware / BRDF normalization
    ↓
Zonal aggregation over 490 field polygons → field×date matrix (raw bands + LST + indices)
    ↓
SSL pre-training on unlabeled archive (reconstruction-based; temporal MAE / 3D-CAE)
    ↓
Anomaly score per field per date = reconstruction error (MSE)
    ↓
Threshold → normal / anomalous; anomalous runs flagged for review
    ↓
(Optional) Fine-tune typing head on 50–100 expert labels → 4 classes
    ↓
Temporal XAI (SHAP on selectivity vectors + temporal Grad-CAM) + physiology validation
```

## 2. Architecture choice (lean)

- **Primary:** 3D-CAE / temporal MAE reconstruction (STS-NET-style), encoder as feature extractor, field-level aggregation. Justification: generative methods dominate anomaly detection (taxonomy); reconstruction error is an interpretable anomaly score.
- **Comparison arm:** contrastive trajectory embedding (NDRE/VI trajectories) — 2608.25888.
- **Backbone:** CNN-Mamba (per thesis frame) with Mamba temporal encoder; reconstruction branch on top. Reimplementation decision pending (SITSMamba code unverified).
- **Input:** raw bands + LST (channels: Blue, Green, Red, NIR, SWIR1, SWIR2, Thermal/LST). Indices (NDVI, NDRE, EVI, SAVI, CWSI) as ablation arm only.
- **Cadence:** Landsat 16-day (539 overpasses, 2013–2026).
- **Level:** field-level (one score per field per date).

## 3. Anomaly score & thresholding

- Per-field reconstruction MSE over the temporal stack; standardized per season (z-score) to remove phenology baseline.
- Threshold: robust (median + k·MAD) or percentile; flag fields whose score exceeds threshold for ≥ N consecutive dates.
- Validation: agreement with CWSI > 0.4–0.5 (Zoratipour), LAI proxy (Paciolla), yield records (Motlagh), and expert review.

## 4. Baselines to beat

RF/XGBoost on indices; LSTM/Transformer SITS encoders; 3D-CAE (STS-NET); supervised CNN-Mamba without SSL; Presto features.

## 5. XAI plan

SHAP on Mamba selectivity vectors + temporal Grad-CAM + counterfactuals; validated by (a) physiological consistency (Angon directions), (b) faithfulness (deletion/insertion on timesteps), (c) expert review, (d) Höhl 2024 sanity checks.

## 6. Open decisions (advisor)

ECe ground-truth access; operational Mixed_Stress criteria; GPU local vs cloud; 18-week timeline + benchmark (G5) release promise.