# Negative / Near-Neighbor Search Logs — 2026-10-04

**Purpose:** Make the novelty claims G1–G3 (and the concurrent-stress gap, G4-adjacent) auditable. Each search below records: date, database(s), exact query, hits returned, and the verdict drawn. Search tooling: `paper-search` MCP (arXiv API + OpenAlex). Semantic Scholar was unavailable (403) — consistent with prior sessions.

**Method note:** queries deliberately combine the method term with the application term. A "negative" verdict means: no paper combining both appears in the top-10 results; the nearest neighbors are listed explicitly with why they do not close the gap.

---

## Search 1 — Mamba / SSM × crop stress (supports G1)

- **Date:** 2026-10-04
- **Query (arXiv):** `Mamba state space model crop stress satellite time series`
- **Hits:** 10 returned. Mamba applications found: generic time-series forecasting (Bi-Mamba+ 2024, SOR-Mamba 2024), infrared small-target detection (MiM-ISTD 2024), crop classification (SITSMamba 2024 — our matrix #01), SSL stress detection via 3D-CAE (STS-NET 2026 — our #14, **not** an SSM).
- **Verdict:** **Negative confirmed.** No Mamba/SSM paper applies to crop-stress classification/detection from SITS. Nearest neighbors: SITSMamba (crop type only) and STS-NET (stress, but 3D-CNN autoencoder on VIs).
- **Caveat:** arXiv-only for this query; a second pass on OpenAlex/Crossref for "state space model" + "crop stress" is advisable before final proposal submission.

## Search 2 — Temporal XAI × satellite time series (supports G2) — **one near-neighbor found**

- **Date:** 2026-10-04
- **Query (OpenAlex):** `temporal explainable AI satellite image time series vegetation stress`
- **Hits:** 10 returned. Relevant:
  1. **James, Kansara & Agrawal (2025), "Temporal Crop Stress Analysis on Multi-Spectral Vegetation Indices using Contrastive Learning and Explainable Ensemble Models", IEEE AsianCON 2025, doi:10.1109/asiancon66527.2025.11281233** — SimCLR-trained 3D-conv encoder on Sentinel-2 composites of five VIs (NDVI, EVI, MSI, NDWI, SAVI); Isolation-Forest pseudo-labels; SVM+LightGBM stacking (95.17% acc); SHAP on features per month + Grad-CAM heatmaps on embeddings. **This is a genuine near-neighbor for G2/G3 and must be cited.** Why it does not close the gap: VI-composite input (not raw bands + thermal); pseudo-labels + separate classifier (not end-to-end disentanglement); stress level/presence, not water-vs-salinity type; XAI is feature/region-level per month, not timestep-level attribution over the season; no physiology validation; conference paper (IEEE AsianCON), single region.
  2. Liu et al. 2026 (post-wildfire recovery, SHAP on RF over time-series features) — temporal XAI on tabular features, classical ML, not deep SITS.
- **Verdict:** **Negative holds with a refinement:** no *timestep-level* XAI for deep SITS stress models exists; but "XAI + contrastive SITS stress" at feature level now exists (James 2025) → the G2 claim must be worded precisely ("no temporal-step-level explanation of a deep SITS stress model, validated against physiology") and James 2025 added to related work.
- **Action:** fetch PDF via institution if possible; add to `papers_not_downloaded.md` (done 2026-10-04).

## Search 3 — Multi-modal SSL × SITS (optical + thermal) (supports G3)

- **Date:** 2026-10-04
- **Query (arXiv):** `self-supervised multimodal satellite time series thermal optical contrastive learning agriculture`
- **Hits:** 10 returned. All generic SSL-for-time-series (survey 2306.10125, SelfMatch, data2vec-style self-distillation, speech/skeleton contrastive variants). Nothing EO-specific; nothing coupling optical + thermal modalities for SITS pre-training.
- **Verdict:** **Negative confirmed.** No multi-modal (optical+thermal) SSL recipe for satellite time series in agriculture. Corroborates the corpus finding (Berger 2022; EigenCL = single index; STS-NET = VIs only).

## Search 4 — Deep-learning disentanglement × concurrent drought–salinity (supports the core niche)

- **Date:** 2026-10-04
- **Query (OpenAlex):** `deep learning disentanglement concurrent drought salinity stress crop remote sensing`
- **Hits:** 10 returned. No DL disentanglement of water×salinity from satellite data. Nearest: Webber et al. 2022 (crop-model framework for multiple stressors — process models, not RS/DL); combined-stress physiology reviews (peanut roots 2026, drought–heat phenomics 2025 — drought+*heat*, not drought+*salinity*, and not predictive per-field models). Bonus: the search surfaced the **Motlagh et al. 2026 abstract** (our #09; Artif. Intell. Agric., doi:10.1016/j.atech.2026.102391) confirming: 336 fields, RF 70:30, R²=0.93, RMSE 5.38 t/ha, CWSI = dominant yield driver (40.6% importance) ahead of soil salinity (27.1%) and crop age (9.0%), strong synergistic water×salinity interaction ("disproportionate yield losses", especially high salinity × high CWSI in ratoon fields) — pending full-text read for exact synergy numbers.
- **Verdict:** **Negative confirmed** — the Wen trilogy (statistical) remains the closest program; no predictive DL disentanglement exists at any scale.

---

## Implications for the gap claims (wording rules)

| Gap | Safe claim (post-search wording) | Do NOT claim |
|---|---|---|
| G1 | "No Mamba/SSM architecture has been applied to crop-stress classification from SITS" | "Mamba is untested in agriculture" (ScopeMamba, detection, exists) |
| G2 | "No timestep-level temporal explanation of a deep SITS stress model exists, and none is physiologically validated" | "XAI has never been combined with SITS stress analysis" (James 2025 combines them at feature level) |
| G3 | "No multi-modal (optical+thermal) SSL pre-training recipe exists for satellite time series" | "SSL is unexplored for SITS" (SimCLR/CAE variants exist) |
| Core niche | "Concurrent water–salinity stress has only been monitored descriptively (Wen trilogy); no predictive, per-field DL disentanglement exists at any scale, and none in arid irrigated sugarcane" | "Nobody monitors concurrent stress from satellites" |

**Follow-up searches to run before proposal submission:** Crossref/OpenAlex pass on "state space model"+"crop stress"; Scopus (institutional) for 2026 in-press items; citation-chasing on James 2025 and SITSMamba.

---
*Searches executed 2026-10-04 by ZCode agent; raw hit lists retained in the session log. Semantic Scholar skipped (403).*
