# 06 — Research Gaps and Thesis Directions

**Basis:** the verified corpus in files 01–04 (84 matrix rows, `05_comparative_evidence_matrix.csv`). Each gap states what the literature shows, what is missing, and whether a "no identical paper found" claim is defensible. Facts, author-reported limitations, and our interpretation are separated.

---

## 1. Established findings (facts, with sources)

1. In-domain SSL pretraining beats ImageNet transfer for RS at low label counts — verified in SeCo (1% labels > ImageNet-100%) [FT], SSL4EO-S12 [FT], Chang et al. (SSL4EO-S12 weights win 3–27% F1 across five continents) [FT].
2. SSL's transfer benefit for time series is **task-dependent**: strongest for anomaly detection, real for classification (fine-tuning), absent for forecasting (Major et al.) [FT].
3. Combining reconstruction + contrastive objectives on aligned modalities outperforms either alone (CROMA ablations: MAE-only −7.5 avg, contrast-only −3.2) [FT]; multimodality with *climate/water* channels matters (Galileo: removing TerraClimate hurts most) [FT].
4. Temporal objectives have matured from seasonal invariance (SeCo 2021) → temporally-aware masking (SatMAE 2022, SITS-Former 2022) → time-gap-conditioned latent prediction (T-JEPA 2026), which also handles cloud-contaminated acquisition appearance [FT].
5. Label-free crop-stress anomaly detection on SITS is emerging and all recent (2024–2026), mostly preprints: STS-NET (controlled-stress, SSL features + light classifiers), EigenCL (label-free staging, proxy validation, cross-year transfer), Sadbhave (fully unsupervised clustering), MIM-AD (contaminated-normal handling), temporal inpainting (temporal-redundancy AD) [FT].

## 2. Verified gaps

**G1 — No optical+thermal (LST) temporal SSL recipe.**
Every temporal-SSL method verified here consumes optical (RGB/NIR/SWIR/red-edge) and optionally SAR/weather/elevation; none ingests LST or TIR bands as a pretraining channel (checked across SatMAE, Galileo, CROMA, T-JEPA, SITS-Former, Presto, TiMo). Meanwhile the entire operational water-stress literature (CWSI lineage, corpus #10/#13/#25/#36/#39/#42/#75/#76) is thermal-based, and Galileo shows auxiliary water-relevant channels (TerraClimate: climate water deficit, soil moisture, AET) provide the largest measured pretraining benefit [FT]. *Defensible novelty claim:* a temporal SSL pretraining recipe with raw Landsat bands + LST for stress-relevant representations. (Not novel in the loose sense — MMEarth/DOFA fuse modalities — but no one has combined optical+LST+temporal+stress.)

**G2 — Label-free stress AD on Landsat archives does not exist.**
The five direct-evidence works use PlanetScope (STS-NET), Sentinel-2 (EigenCL, Sadbhave, inpainting), or UAV (MIM-AD). SSL4EO-L exists [MO] but is scene-level and not stress-oriented. No verified study does field-level, label-free anomaly detection over a multi-year Landsat 16-day archive. *Defensible.* Our 539-product, 13.5-year, 490-field Amirkabir corpus is genuinely unstudied territory — provided the claim is framed as "first on a long Landsat field-level archive," not "first label-free crop-stress AD" (EigenCL and Sadbhave are prior label-free work and must be cited as such).

**G3 — Reconstruction vs contrastive vs one-class for SITS stress AD: no controlled comparison.**
The TS-SSL transfer study (Major et al.) compares paradigms for generic TS-AD [FT], but in agriculture each paper uses one paradigm (STS-NET reconstruction; EigenCL contrastive; Sadbhave reconstruction+clustering) with different data. No study compares 2–3 SSL objectives for the *same* crop-stress AD task under one protocol. *Defensible* — and it is exactly the thesis's planned comparison arm (questionnaire Q4 recommendation).

**G4 — Contaminated "normal" training sets are acknowledged but unsolved in agri-AD.**
Ruff et al. flag contamination as a core AD challenge [FT]; AnomalyBERT solves it for sensor streams via synthetic-anomaly degradation [FT]; MIM-AD's anomaly-suppression loss handles it for single-date UAV images [FT]. No SITS crop-stress paper addresses contamination (the Amirkibar archive inevitably contains stressed fields). *Defensible*; the synthetic-anomaly degradation scheme transplanted to temporal crop series is a concrete, evidence-backed methodological contribution.

**G5 — Cross-year / cross-region generalization is demonstrated once, with proxies.**
EigenCL's Iowa 2020 → Nebraska 2023 transfer [FT] is the only verified cross-year, cross-region label-free stress result; its validation is soil moisture/USDM/yield proxies, not field physiology. Elbeltagi et al. use an independent test-year split, but supervised [FT]. Leave-one-year-out SSL evaluation for stress detection is unpublished. *Defensible*; the thesis's leave-one-year-out design (questionnaire Q14) directly answers this.

**G6 — XAI on SSL temporal representations is essentially unstudied.**
The RS-SSL corpus contains representation *probing* (environmental signals, arXiv:2607.05207 [ABS]; t-SNE analyses [FT]) but no temporal attribution method (which timesteps/bands drove an anomaly score) validated against plant physiology. The thesis's SHAP-on-selectivity + temporal Grad-CAM plan (Angon-style physiological direction checks) has no verified competitor. *Defensible*, with the caveat that XAI-on-SSL is methodologically risky (faithfulness of attributions on self-supervised features is itself an open problem — Höhl 2024, corpus #04).

**G7 — Stress-AD is evaluated against the wrong baselines (or none).**
No verified SSL-stress paper compares against cheap operational baselines (RF/XGBoost on CWSI/NDVI thresholds, z-scored index anomalies). STS-NET compares to Presto features; EigenCL to SimCLR/K-Means [FT]. The scientific question "does temporal SSL beat a CWSI-threshold alarm?" is unanswered. *Defensible* and mandatory for the thesis's credibility with agronomy reviewers.

**G8 — Cloud/missing-acquisition robustness in SSL pretraining is a design aspiration, not a measured property.**
Verified strategies: filter (SeCo/SSL4EO-S12 <10% cloud [FT]), tolerate via latent objectives (T-JEPA argues and *qualitatively* shows cloud-free decodings [FT]), repair via generative densification (arXiv:2605.04239 [ABS]). No paper quantifies AD performance as a function of cloud-induced missingness for Landsat composites. *Defensible* as an evaluation contribution (ablation: performance vs observation completeness), not as a method contribution.

## 3. Methodological trade-offs the thesis must decide (evidence-grounded)

| Decision | Evidence for | Evidence against | Lean |
|---|---|---|---|
| Reconstruction as primary pretext | anomaly-score-native; MIM-AD +6.3% mIoU [FT]; TS-SSL gains largest for AD [FT]; Sadbhave runs label-free | weak frozen features vs contrastive (SSL4EO-S12) [FT] | reconstruction primary (matches questionnaire rec.) |
| Contrastive/one-class comparison arm | EigenCL's discriminative trajectory space works label-free [FT]; contrastive wins linear probing [FT] | positives design is delicate (SeCo invariance warning) [FT] | keep as second arm |
| Synthetic-anomaly degradation (AnomalyBERT-style) | solves contamination without normal-only split [FT]; realistic stress signatures exist (progressive NDRE/NDVI decline, EigenCL clusters) | synthetic-realistic gap; unproven on SITS | evaluate as third arm |
| Raw bands + LST input | Galileo: water-relevant auxiliaries pay off [FT]; G1 novelty; STS-NET used indices only → differentiation | indices carry less nuisance variance (SIGMAE direction [ABS]) | raw + LST primary, indices ablation (matches Q3) |
| Field-level zonal aggregation | matches data layout; parcel/trajectory lineage works (PSE/TAE, EigenCL) [MO/FT] | loses within-field spatial pattern (patch-level alternatives) | field-level (matches Q6) |
| Latent (JEPA-style) temporal objective | T-JEPA SoTA on matched corpus; cloud robustness [FT] | +220% FLOPs; very new; no agri evidence | track as extension, not v1 |

## 4. Candidate thesis directions (ranked by evidence support × gap size)

1. **Label-free reconstruction-based anomaly detection over the Amirkabir Landsat archive (raw bands + LST), leave-one-year-out, benchmarked against CWSI/index baselines and RF/XGBoost** — strongest combination of G1+G2+G7; all required baselines verified to exist; the comparison itself is novel.
2. **Controlled pretext comparison (reconstruction vs trajectory-contrastive vs synthetic-anomaly degradation) on the same SITS stress task** — G3; directly resolves questionnaire Q2/Q5; Major et al.'s protocol (matched budgets, AD task) is the template [FT].
3. **Temporal XAI validated against physiology (Angon directions + faithfulness metrics)** — G6; differentiates from all five direct-evidence papers, none of which do XAI.
4. **Robustness-to-contamination ablation** — G4; MIM-AD's suppression loss and AnomalyBERT's degradation scheme are ready-made mechanisms [FT].
5. **What do SSL features encode? Environmental probing of the archive's features against CWSI/ETa/weather rasters** (the 35 raster products available) — G6/G7-adjacent; cheap, high-review-value side contribution modeled on arXiv:2607.05207 [ABS].

## 5. Explicit non-claims (to keep the proposal honest)

- Do **not** claim "first label-free crop-stress detection" — EigenCL (2025) and Sadbhave (2025) exist; claim "first on a long Landsat field-level archive with optical+thermal inputs."
- Do **not** claim SSL is proven for vegetation stress — state the evidence status as in `04` (controlled/proxy-validated only).
- Do **not** equate anomaly detection with stress detection; the anomaly must be validated against CWSI/ETa/yield/expert review before being called stress.
- Do **not** use T-JEPA/Galileo numbers as expected performance — they are different corpora (Sentinel-2 RGB, global), not comparable to a 490-field Landsat archive (protocol-incomparability rule).

---

*All bracketed evidence tags refer to the verified reads documented in files 01–04 and `00_search_log.md`.*
