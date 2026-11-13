# 08 — Executive Synthesis

**Date:** 2026-10-24 · **Basis:** 84 verified papers (full-text reads: 8 deep PDF reads + 15 local full-PDF extractions; all others metadata+abstract-verified via arXiv/OpenAlex/Crossref). Full evidence in files 01–06.

---

## What SSL actually contributes (verified)

1. **Label efficiency, not magic accuracy.** SSL pretraining consistently beats from-scratch training when labels are scarce: 10% labels ≈ 50–100%-label supervised training (SSL4EO-S12 [FT]); SSL4EO-S12 weights beat ImageNet/SatlasPretrain by 3–27% F1 for crop mapping across five continents (Chang et al. [FT]); in-domain SSL with 1% labels outperformed ImageNet-100% (SeCo [FT]). With *abundant* labels the advantage shrinks to 1–6%.
2. **Task-dependent transfer.** For time series, SSL yields substantial gains in **anomaly detection**, effective initializations for classification, and no advantage for forecasting (Major et al. [FT]). This empirically supports the thesis's anomaly-detection-first framing.
3. **No family dominance.** Contrastive/distillation wins frozen evaluations; masked reconstruction wins scale and provides a native anomaly score; latent (JEPA) prediction handles acquisition-specific nuisance (clouds, illumination); multimodality helps when channels are aligned and *domain-relevant* — removing TerraClimate (climate water deficit, soil moisture, AET) from Galileo's pretraining hurt more than removing any other modality [FT].

## Which approaches are most relevant to satellite time series

The temporal-supervision lineage verified here: seasonal contrastive (SeCo, ICCV 2021) → temporally-aware masked reconstruction (SatMAE, SITS-Former, Presto, 2022–2024) → dual global/local masked modeling with month embeddings (Galileo, ICML 2025) → **time-gap-conditioned latent prediction** (T-JEPA, arXiv 2026), which treats irregular elapsed time as supervision and decodes cloud-free states at cloud-contaminated dates [FT]. Agriculture-specific pretexts (Time2Agri: future-frame, temporal-frequency, time-difference prediction) beat generic ones on SICKLE crop/yield tasks [FT]. For *field-level* representation, the pixel-set/trajectory lineage (PSE/TAE → EigenCL/STS-NET) matches the thesis's 490-polygon layout better than dense patch-sequence FMs.

## What is known about agricultural applications

Crop-type classification with SSL features is mature evidence: label-efficient transfer (EuroCropsML benchmark: SSL > from-scratch and standard transfer [ABS]), irrigation detection without labels (Agastya 2021 [FT-local]), weakly-supervised crop mapping at 95% of fully-supervised performance (Exact, CVPR 2025 [ABS]).

## What remains unproven for vegetation stress modeling

All direct stress evidence is 2024–2026 and preprint-stage: SSL features detect *imposed* stress under controlled plots (STS-NET: 97.98% water-stress precision, but needs labeled classifiers downstream), stage drought stress label-free with proxy validation (EigenCL: Silhouette 0.748, 12-day early detection, cross-year transfer, validated against soil moisture/USDM/yield — not field physiology), and detect generic field anomalies (MIM-AD; temporal inpainting). **No verified study**: label-free stress detection on a multi-year Landsat field-level archive; optical+LST temporal SSL; reconstruction-vs-contrastive-vs-one-class comparison for the same stress task; contamination-robust training for agri SITS; temporal XAI validated against physiology; comparison against CWSI/index-threshold baselines. Anomaly detection ≠ stress detection — the anomaly signal must be validated against independent ground truth (CWSI/ETa/yield/expert review) before the word "stress" is used.

## Five to eight evidence-backed research questions worth investigating

**RQ1 (core).** Can reconstruction-based SSL on a 13.5-year Landsat archive (raw bands + LST, 490 fields) produce field-level anomaly scores that agree with independent stress evidence (CWSI > 0.4–0.5, ETa, yield records, expert review) — and does it beat a z-scored CWSI/NDVI-threshold alarm at equal alert budgets? *(Gap G1+G2+G7; baselines verified to exist; no identical study found.)*

**RQ2.** Which SSL objective transfers best to SITS stress anomaly detection under matched parameter/data budgets — masked reconstruction, trajectory contrastive, or synthetic-anomaly degradation (AnomalyBERT-style)? *(Gap G3; Major et al.'s matched-budget protocol is the template [FT]; questionnaire Q2/Q5.)*

**RQ3.** Does adding LST as a pretraining channel measurably improve stress-relevant representations, or does it only help after fine-tuning? *(Gap G1; direct test of the thesis's differentiator vs STS-NET's indices-only design [FT]; Galileo's auxiliary-modality ablation shows the effect class is real [FT].)*

**RQ4.** How much does the SSL anomaly detector degrade as cloud-induced observation completeness drops (16-day → monthly composites; field × date masking), and does a date/Δt-conditioned encoder (SatMAE/Sadbhave/T-JEPA-style temporal encodings [FT]) mitigate this? *(Gap G8; evaluation contribution.)*

**RQ5.** Do SSL-derived anomaly scores detect stress earlier than index thresholds — the property that motivated EigenCL's 12-day-early result [FT] — on natural (non-experimental) fields with leave-one-year-out validation? *(Gap G5; Elbeltagi's independent-test-year protocol as the supervised template [FT].)*

**RQ6.** Are the learned features' anomaly attributions (temporal SHAP/Grad-CAM) physiologically coherent — pointing at the timesteps/bands that the Angon response directions (gs↓, Ts↑, Na⁺↑) predict — and are they faithful (deletion/insertion)? *(Gap G6; no verified competitor.)*

**RQ7 (optional arm).** Do the archive's SSL features encode environmental state beyond anomalies — i.e., can frozen features predict CWSI/ETa rasters (the 35 available products) better than raw-index regressions? *(Modeled on geospatial SSL probing with environmental signals [ABS]; cheap, high-value validation of representation quality.)*

**RQ8 (framing check).** Under the label-free ideal, what is the *false-alarm* structure of reconstruction-error anomaly scores — are flagged fields measurably contaminated by confounders (harvest dates, replanting, irrigation schedule changes)? *(Gap G4; contamination is the acknowledged open AD problem [Ruff FT]; MIM-AD and AnomalyBERT provide candidate mechanisms [FT].)*

## Recommended next step for the thesis

Proceed with the already-recorded plan (`SSL_Proposal/method_design_ssl.md`): reconstruction-based 3D/temporal-MAE primary arm on raw bands + LST at field level, contrastive trajectory arm as comparison (answers RQ2), CWSI/index baselines as non-negotiable comparators (RQ1), leave-one-year-out evaluation (RQ5), physiology-validated temporal XAI (RQ6). Two updates from this review: (1) add the **synthetic-anomaly degradation arm** — it is the only verified mechanism for the contamination problem inherent in the archive; (2) treat Presto and STS-NET as the mandatory SSL baselines and Galileo/T-JEPA as documented but non-comparable reference points (different corpora/protocols).

---

*Search-coverage limitations and selection bias: single-day search (2026-10-24); Google Scholar approximated via Semantic Scholar/OpenAlex/arXiv (S2 connector was down); forward-citation chasing was bounded (ranked discovery + recent-work sweeps instead of exhaustive citation graphs); non-English literature excluded; 2025–2026 preprints dominate the direct stress-evidence set and may still be under peer review — status labels are attached throughout.*
