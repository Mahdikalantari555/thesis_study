# 74 — RS + ML/DL for Agriculture & Forestry: Systematic Review 2020–2025 (Gracia Rojas et al., 2026)

**Full Citation:** Gracia Rojas, D. A., Gómez Díaz, H. J., & Gil Herrera, R. de J. (2026). Remote sensing-based machine learning and deep learning for agriculture and forestry: Yield estimation, land-cover mapping, and plant stress – A systematic review (2020–2025). *Remote Sensing Applications: Society and Environment*, *44*, 102279. https://doi.org/10.1016/j.rsase.2026.102279
**DOI:** [10.1016/j.rsase.2026.102279](https://doi.org/10.1016/j.rsase.2026.102279) | Open access (CC BY-NC-ND) | Received 11 May 2026; revised 05 Sep 2026; accepted 21 Sep 2026
**Status:** ✅ Full read (2026-10-20)
**Themes:** #Review #Review-methods #SITS #Benchmark

---

## What It Does

PRISMA-2020-reported **systematic literature review of n = 105** peer-reviewed articles (2020–2025) on **remote sensing + ML/DL for agriculture and forestry**, crossing three task domains (yield/biomass; land-cover classification & segmentation; plant health & stress) with four methodological dimensions (sensor modality & scale; model family; validation design; operational cost & latency). Its value to the thesis is not new numbers but a **taxonomy + reporting-practice audit** of the field the thesis enters.

## Corpus & Scope

- **n = 105** articles, 2020–2025 (p. 1, p. 11). Narrative/qualitative synthesis — **no meta-analysis** (p. 10): pooled means/CIs and climate-zone meta-analysis were judged methodologically inappropriate given heterogeneity in outcome definitions, units, class structures, spatial supports and validation designs; no formal risk-of-bias score was used (p. 10).
- **Search**: N = 7044 records across IEEE Xplore (1504), Scopus (2748), Web of Science (2132), ScienceDirect (660) (p. 8, Table 1); three concept blocks — *remote sensing* × *(machine learning OR deep learning)* × *(crops OR forestry)* — with DB-specific field tags; filter January 2020 → final 2025 search update.
- **Sampling**: proportional stratified allocation n = 105 → IEEE 22 / WoS 32 / Scopus 41 / ScienceDirect 10 (p. 9, Table 2); sample size from the finite-population-corrected formula, 95 % confidence (Z = 1.96), margin of error 7 %, expected-relevance p = 0.84 from a WoS pilot (42 of 50 screened records relevant) (pp. 7–8). Screening: 87 of the 105 sampled papers met eligibility, **+18** via Research Rabbit AI citation expansion → final 105 (pp. 8–9); PRISMA-like flow diagram (Fig. 3, p. 9).
- **Corpus profile** (pp. 11–12): 48 journals (33 Q1 / 8 Q2, SJR 2024); ~89 % agriculture / 11 % forestry; Asia 38 %, North America 28 %, Europe 20 %, South America 6 %, Oceania 6 %, Africa 2 %; sensors — satellite optical 63 %, SAR 25 %, UAV 18 %, LiDAR + HSI 19 % (non-exclusive); crops — corn ~15 %, wheat ~14 %, soybean ~13 %, rice ~11 %, ~27 % multi-crop.

## Key Methodology

- **Three-phase SLR protocol** after Brereton et al. (2007) + Tebes et al. (2020): planning → execution → documentation (p. 5, Fig. 2).
- **Coding**: each study coded into a three-domain matrix (yield/biomass · classification/segmentation · plant health/stress) × dominant model family × sensor configuration × validation design × operational constraints (p. 7). Sensor categories are **non-mutually exclusive**; validation is coded **hierarchically** — external or space-time-blocked > random holdout > cross-validation (p. 6) — so random k-fold is *not* treated as equivalent to blocked splits (p. 24). Metrics were taken from held-out tests, prioritising task-appropriate ones (RMSE/R², F1/OA, IoU) and kept at crop/region/season granularity (p. 11).

## Key Findings

- **Model-family taxonomy with prevalence (p. 13)** — the core deliverable. *Deep learning*: **CNN family 78.2 %** of DL studies (dominant in segmentation/mapping and optical–SAR fusion); **RNN — LSTM/GRU** for time series (yield, phenology); **Transformers / attention 5.5 %** (raw Sentinel-2 series, ViT weed classification, CNN–Transformer hybrids for change detection). *Classical ML*: **Random Forest 70.3 %**, **SVM/SVR 29.7 %**, **GBDT family 27.0 %** (GBDT/XGBoost/LightGBM/CatBoost), **ELM 10.8 %**, PLSR 2.7 %, GPR 2.7 %; ensembles/meta-classifiers 10.0 %; metaheuristic hyper-parameter optimisation 5.7 %; rare Bayesian networks (uncertainty) and deep RL.
- **Task split (p. 15)**: yield/biomass **n = 48** (26 DL / 14 ML / 8 hybrid); classification/segmentation **n = 38** (22 / 6 / 10); **plant health & stress n = 19** (10 DL / 4 ML / 5 hybrid). Stress studies remain **close-range**: UAV 6 and proximal/aerial 6, optical 4, HSI/LiDAR 2 — **no satellite-SITS stress family yet**.
- **Conclusions (p. 27)**: CNN for mapping/segmentation (3D extensions for multi-date/HSI), **LSTM + Transformer for time series**, RF/GBDT/SVM as **robust baselines when feature engineering is strong**; Bayesian uncertainty and hybrid CNN–RNN appear only in some scenarios.
- **Model-selection rule (p. 25)**: classical ML stays hard to beat for *small n, engineered phenological/texture features, low-to-moderate temporal density*; DL wins on *multimodality and high temporal density* — "task- and evidence-conditioned decision rules, not universal performance rankings."
- **Validation gap (p. 24)**: pure **random k-fold persists and is insufficient for interannual/intersite generalisation**; spatial and temporal autocorrelation cause leakage and inflated metrics; region/season-blocked schemes are recommended; **explicit uncertainty (Bayesian networks, Monte Carlo dropout) is underutilised**; few studies report inference cost; **missing per-class and lead-time metrics** block meta-analytic synthesis.
- **Uncertainty-reporting gap (pp. 24, 27)**: "Absent uncertainty, reliable decision thresholds for risk and operation cannot be established"; the lack of calibrated uncertainty plus interpretable drivers is the binding constraint on DSS integration. Priorities named: strict spatial-temporal validation protocols; integration of uncertainty (Bayesian approaches); self-supervision and few-shot learning for scarce labels; near-term: multi-site/multi-season validation, calibrated uncertainty, reproducible computational reporting (p. 27).
- **Optical–SAR fusion is conditional, not universal (p. 24)**: only a subset ran explicit single-modality ablations, so the evidence supports *conditional* complementarity — "it does not establish a pooled robustness gain across cloudy, humid, or arid climatic zones" — and climate-stratified comparisons are hindered by inconsistent climatic-zone reporting (p. 15). ⚠️ *This qualifies the intake note's flatter "fusion preserves structural information under cloud cover" claim.*
- **Thermal / SIF underused at regional scale (p. 26)**: promising for Kc/ET and chlorophyll/LAI for stress, but data availability, atmospheric + emissivity correction and cloud-driven SNR loss block scale-up — a direct caveat for the thesis' thermal branch. Case numbers: RF + UAV features → maize **Kc R² = 0.69**, cumulative **ET R² = 0.89**, root-zone soil moisture **R² = 0.85** (Shao et al. 2023, p. 23).
- **Emerging directions (p. 25)**: Transformers/self-attention on raw multispectral series; 3D architectures and deep fusion; pixel-scalable AI hybrids; few-shot/self-supervision; digital twins; **EO foundation embeddings — AlphaEarth Foundations (annual 10 m, 64-dimensional embedding fields) — included as future outlook and NOT counted among the 105**, appearing near the review's close as a technical preprint. STCCL (spatio-temporal contrastive self-supervision for yield) *is* counted (Qiao et al. 2025, p. 14).

## Relevance to Thesis

**Medium-High** — the taxonomy frames the thesis' method choice; the named validation/uncertainty gaps supply the differentiation:
- ✅ **Sequence-family evidence**: LSTM + Transformers are the accepted family for RS time-series tasks (p. 27) — third-party support for choosing a sequence backbone (and by extension an SSM/Mamba-style temporal encoder) over engineered-index models for multi-temporal SITS.
- ✅ **Classical ML stays competitive** (RF 70.3 %, GBDT 27.0 %, SVM 29.7 %; p. 13) when feature engineering is strong and n is limited (p. 25) — a citable justification for keeping RF/XGBoost as the benchmark rather than a strawman.
- ✅ **Two named differentiators**: blocked/space-time validation and calibrated uncertainty reporting are identified as field-wide deficits (pp. 24, 27) — exactly what the thesis claims to fix.
- ⚠️ The "accepted sequence family" claim covers **time-series tasks broadly (yield, phenology)**, not stress: stress studies are only n = 19 and remain UAV/proximal-dominated (p. 15), so the thesis' satellite-SITS stress setting is unrepresented.
- ⚠️ Narrative synthesis over a stratified 105-study corpus whose relevance prior (p = 0.84) was calibrated only in WoS (acknowledged sampling uncertainty, p. 8) — frequencies are "of this sample", as the authors insist (p. 11).
- ❌ No salinity-vs-water disentanglement, no concurrent-stress framing, no depth on SSL-for-stress (only STCCL for yield).

## Key Takeaway

The thesis' two bets — a **sequence model over SITS** and **explicit validation + uncertainty reporting** — are independently endorsed as the field's direction by a 2026 PRISMA-based review of 105 papers, and the field's two most-cited deficits (random k-fold validation, absent uncertainty) are precisely what the thesis claims to address. Caveat: a stratified 105-study corpus with no meta-analysis supports "the field currently does X", not effect-size claims.

## Links

- Matrix row: #74
- Related: #73 (UAV CWSI/CEWT ML benchmarks — proximal comparator), #78 (pre-2020 evolution anchor this review supersedes), #60 / #72 (reviews & framing), #77 (sugarcane-specific review)

---

*Linked from: [[Literature-Matrix]]*
