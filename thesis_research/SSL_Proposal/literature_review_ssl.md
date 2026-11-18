# Literature Review — Self-Supervised Learning (SSL) for Crop-Stress Anomaly Detection from Satellite Image Time Series

**Scope:** SSL methods that enable *label-free / label-scarce* detection of anomalous (stressed) vs. normal agricultural fields from satellite image time series (SITS), with emphasis on sugarcane and arid/semi-arid irrigated systems.  
**Companion:** `00_SSL_questionnaire.md` (framework decisions), `Thesis_Vault/04-Thesis-Design.md` §2–§5.  
**Date:** 2026-10-24. **Language:** English (lit review convention).

---

## 1. Why SSL for anomaly detection here

The thesis data (Amirkabir, Khuzestan) provide **539 Landsat 8/9 overpasses (2013–2026) over 490 sugarcane fields** but only a handful of expert labels (target 50–100). Ground-truth stress labels (ECe, CWSI, yield) are scarce and expensive. SSL pre-training on the unlabeled archive lets the model learn a notion of "normal" canopy development and flag deviations as anomalies **without labels**, which is the ideal the user set: *the model should work in a no-label situation, with label scarcity treated as a benefit, not a blocker.*

Two anomaly-detection paradigms recur in the literature and are both relevant:

1. **Reconstruction-based:** train an autoencoder (3D-CAE / MAE) to reconstruct normal SITS; high reconstruction error ⇒ anomaly. STS-NET is the closest analogue.
2. **Contrastive / one-class:** learn an embedding space where normal fields cluster; anomaly = distance from the normal cluster. The NDRE-trajectory contrastive work and Presto follow this.

---

## 2. Closest analogue — STS-NET (Dalal et al., 2026)

**STS-NET: Spatio-Temporal Stress Network for Self-Supervised Crop Stress Detection using Satellite Image Time Series** (arXiv:2607.18791, Dalal, Ranjan, Ghildiyal, Tamaskar, Goel). Directly on point for this thesis:

- **Method:** self-supervised 3D-convolutional autoencoder (3D-CAE) pretrained on unlabeled SITS, then used as a frozen feature extractor feeding RF/XGBoost classifiers.
- **Input:** 4 VIs (NDVI, GNDVI, RECI, NDRE) + RGB + NIR, averaged VI channel; T = 32 timesteps; pixel-level time series `x ∈ R^{1×1×T×C}` (C=5).
- **Pre-training data:** BSPT dataset — ~196 km², Barnala (Punjab), PlanetScope, 32 images (Feb 2023–Feb 2024), 9–11 day cadence, <15% cloud, ~22 M pixels.
- **Evaluation:** 62 sugarcane plots, Lakhimpur Kheri (UP, India), controlled water × nitrogen stress (9 classes). Water stress 97.98% precision, nitrogen 85.08%, combined 83.47%.
- **Efficiency:** 19.2 K parameters vs. Presto's 400 K.
- **Ablation:** RGB + NIR + Avg(NDVI, NDRE, RECI, GNDVI) at T=32 is optimal; robust even at T=8 (2 months). 8 timesteps ⇒ 90.32% water / 70.97% N.
- **Positioning vs. our thesis:** STS-NET uses *indices* (not raw bands + LST), PlanetScope (3 m, not Landsat 30 m), and a *supervised fine-tuning head on controlled labels* — not label-free anomaly scoring. It is a strong **baseline to beat** and a template for the 3D-CAE reconstruction approach, but our contribution (raw bands + LST, 12-year archive, label-free anomaly, XAI, physiology validation) remains distinct. Also note its combined-stress class is a 9-class permutation, not a concurrent water–salinity disentanglement.

**Reusable assets:** preprocessing chain (mosaic → mean imputation → VI computation), MSE reconstruction loss, encoder-as-feature-extractor pattern, ablation design (temporal depth × VI set).

---

## 3. Contrastive / trajectory-based SSL

**"Embedding NDRE Trajectories into Contrastive Learning for Label-Free, Physiology-Aware Crop-Stress Staging and DSS Outputs"** (arXiv:2608.25888, 2026-08-26). Directly states the label-free, physiology-aware framing that matches our thesis:

- Embeds NDRE temporal trajectories into a contrastive space for crop-stress staging **without labels**, producing decision-support outputs.
- Closest conceptual sibling to "normal vs anomalous farm" discovery; worth a full read for the trajectory-embedding design and how it avoids label dependence.

**Time2Agri: Temporal Pretext Tasks for Agricultural Monitoring** (arXiv:2507.04366, Plaksha, 2025-07). Surveys temporal pretext tasks for RSFMs (SatMAE, SpectralGPT, etc.) applied to agriculture — useful for selecting a temporal pretext (masking, ordering, prediction) for our CNN-Mamba backbone.

**Presto** (Tseng et al., arXiv:2304.14065) — self-supervised transformer on pixel-level RS time series; used as a feature extractor in STS-NET (82/81/72% on water/N/combined). Benchmark competitor and a candidate "foundation-model ablation" (advisor allows FMs only as ablation/robustness).

---

## 4. Label-free anomaly detection (non-crop, transferable design)

**"Label-free Anomaly Detection in Aerial Agricultural Images with Masked Image Modeling"** (arXiv:2404.08931, Plaksha, 2024-04). Masked image modeling for anomaly detection in agricultural imagery without labels — design reference for the reconstruction-error-as-anomaly-score approach, though aerial (not SITS). Transfers to our SITS setting as a spatial anomaly prior.

**"Anomaly detection in satellite imagery through temporal inpainting"** (arXiv:2512.23986, 2025-12). Temporal inpainting (reconstruct masked timesteps) as the anomaly signal — directly applicable to SITS and a candidate pretext for our Mamba encoder.

**"Global-Scale Self-Supervised Spatiotemporal Learning for NDVI Time-Series Reconstruction"** (arXiv:2608.02322, 2026-08). NDVI reconstruction at global scale — supports the "reconstruction of normal phenology, flag deviations" paradigm and provides a reconstruction-error baseline.

---

## 5. Time-series SSL taxonomy (method-selection reference)

**"Self-Supervised Learning for Time Series Analysis: Taxonomy, Progress, and Prospects"** (Zhang et al., arXiv:2306.10125, 2023; updated 2024). Comprehensive taxonomy: generative-based, contrastive-based, adversarial-based, with 10 subcategories. **Use this to justify the pretext-task choice** (Q2/Q5 deferred to lit review). Key takeaway for anomaly detection: generative (reconstruction) methods dominate anomaly detection; contrastive methods dominate classification/clustering.

**"When Does Self-Supervised Learning Transfer to Time-Series Tasks?"** (arXiv:2605.19462, 2026-05). Empirical study of transfer conditions — relevant to whether our Landsat 12-year archive SSL transfers to the 50–100 label fine-tuning set.

---

## 6. Deep anomaly-detection foundations (design priors)

**Ruff et al., "A Unifying Review of Deep and Shallow Anomaly Detection"** (Proc. IEEE 2021, 1032 citations). Unifies generative, one-class, and reconstruction approaches; gives the anomaly-score definitions (reconstruction error, latent distance, density) and the open challenges (contaminated training data, high-dimensional inputs, explainability). **Design prior:** our "normal" training set will be contaminated by stressed fields; need robust-to-contamination objectives (e.g., trimmed loss, one-class SVM on SSL features).

**"Deep learning-based anomaly detection for precision field crop protection"** (Cheng et al., Frontiers in Plant Science 2025, 23 citations). Multimodal fusion (UAV + satellite + weather) for field-level anomaly detection — supports our multi-channel (raw bands + LST + weather) design.

---

## 7. Synthesis — recommended SSL direction for this thesis

Given the data (Landsat 8/9, 30 m, 490 fields, 13.5 years, 35 raster products incl. LST/CWSI/ETa) and the label-free ideal:

| Decision | Recommendation | Evidence |
|---|---|---|
| **Objective** | Reconstruction-based anomaly detection (3D-CAE / temporal MAE) as primary, with contrastive as comparison | STS-NET (3D-CAE, reconstruction) + taxonomy (generative dominates AD); anomaly score = reconstruction error per field per date |
| **Secondary** | Contrastive trajectory embedding (NDRE/VI trajectories) as a second arm | 2608.25888 label-free staging |
| **Input** | Raw bands + LST (+ optional indices ablation) | Rußwurm 2020; G7; STS-NET used indices only → our raw+LST is the differentiator |
| **Level** | Field-level zonal aggregation → one anomaly score per field per date | 490 polygons; matches data layout |
| **Cadence** | Landsat 16-day composites (existing 539 overpasses) | DATA_SUMMARY; uniform 2013–2026 |
| **Anomaly score** | Reconstruction error (MSE) over the field's temporal stack; thresholded into normal/anomalous, then (optionally) typed via fine-tuning on 50–100 labels | STS-NET pattern + label-free ideal |
| **Validation** | (a) physiological consistency of anomalous periods (Angon directions), (b) faithfulness of temporal attributions, (c) expert review, (d) comparison vs. CWSI/ETa thresholds and yield | Thesis design §6 |
| **Baselines to beat** | RF/XGBoost on indices, LSTM/Transformer SITS, 3D-CAE (STS-NET), supervised CNN-Mamba without SSL, Presto features | Thesis design §6 |

**Key novelty claim (defensible):** label-free anomaly detection on a **12-year Landsat archive with raw bands + LST** for **sugarcane water–salinity disentanglement**, with **temporal XAI validated against plant physiology** — STS-NET does indices/PlanetScope/controlled labels and no XAI; the NDRE-contrastive work does staging but not water-vs-salinity typing. The gap (G3) holds: no multi-modal (optical + thermal) SSL pre-training recipe for satellite time series exists.

---

## 8. Open items (deferred from questionnaire)

- Pretext choice among reconstruction/contrastive/one-class (Q5) — lean: reconstruction primary + contrastive comparison.
- Augmentation policy (Q4) — lean: physics/spectral + temporal, **no** color jitter (Paul 2025).
- Baseline set (Q9), XAI validation (Q10), compute (Q11) — lean per thesis design §5–§6.

---

## 9. Candidate reading list (priority)

1. STS-NET — Dalal et al., arXiv:2607.18791 (2026) — 3D-CAE reconstruction baseline.
2. NDRE-trajectory contrastive — arXiv:2608.25888 (2026) — label-free staging.
3. Time2Agri — arXiv:2507.04366 (2025) — temporal pretext tasks.
4. Label-free MIM anomaly — arXiv:2404.08931 (2024).
5. Temporal inpainting anomaly — arXiv:2512.23986 (2025).
6. Time-series SSL taxonomy — Zhang et al., arXiv:2306.10125 (2023/24).
7. Transfer conditions — arXiv:2605.19462 (2026).
8. Presto — Tseng et al., arXiv:2304.14065 (2023).
9. Deep AD unifying review — Ruff et al., Proc. IEEE (2021).

---

*Written 2026-10-24 from alphaxiv + paper-search discovery. Citations verified against arXiv IDs; full-text reads pending for items 2–9.*