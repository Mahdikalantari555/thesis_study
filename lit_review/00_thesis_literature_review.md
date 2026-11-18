# Disentangling Concurrent Water and Salinity Stress from Satellite Image Time Series — Literature Review & Gap Analysis

**Author:** Kilo (research assistant) for a Master's thesis, 2026  
**Focus:** Label-efficient, explainable temporal deep learning (CNN-Mamba + SSL + temporal XAI) for concurrent water–salinity stress disentanglement in an arid irrigated sugarcane system (Amirkabir Agro-Industrial Unit, Khuzestan, Iran; Landsat 2013–2025, ~490 fields)  
**Scope:** 2012–2026 literature; current thesis frame adopted 2026-09-10 (advisor-approved redesign), fully reconciled 2026-10-04. The earlier foundation-model-era recommendation (Prithvi/AlphaEarth + active learning) was **rejected by the advisor**; FM material is retained only as ablation/background (§4.9).

> **Companion files:** `phase1_stress_detection_methods.md` (deep Phase-1 review, ~140 papers) · `papers_not_downloaded.md` (~96 remaining citations) · `Thesis_Vault/Literature-Matrix.md` (canonical matrix, rows 01–78) · `Thesis_Vault/03-Research-Gaps.md` (G1–G7 with evidence) · `Thesis_Vault/04-Thesis-Design.md` (methodology) · `Thesis_Vault/papers/` (per-paper notes; verified full-read notes marked ✅).
> **Corpus:** 78 numbered PDFs in `papers/` (01–78, complete as of 2026-10-04). Two intakes synthesized in `deep_researches/new_papers_intake_2026-09-10.md` (A1–A8 agricultural + G1–G21 agentic → `papers/39–67`) and `new_papers_intake_2026-10-04.md` (A9–A16 → `papers/68–75`), plus recovery papers 02–09, 13, 18, 43, 76–78 (`papers/INTAKE_LOG_2026-10-04.md`).

---

## 1. Executive Summary

This review serves one purpose: to justify and position the thesis — **predictive, per-field disentanglement of concurrent water and salinity stress from a 12-year Landsat archive using a self-supervised CNN-Mamba and physiologically validated temporal XAI**. Six findings structure the argument:

1. **Concurrent stress is a recognized, unsolved monitoring problem.** Wen et al.'s trilogy (RS 2021 → HESS 2022 → IJAEOG 2023) is the closest existing research program: joint drought+salinity spectral signals overlap individual-stress signals, "significantly limiting" remote separation; their five-trait Sentinel-2 pipeline shows combined effects that are exacerbated and strongly phenology-dependent, with drought sensitivity exceeding salinity. But the trilogy is **statistical (meta-review + ANOVA)** — no predictive model, no per-field stress-type disentanglement, no arid irrigated sugarcane. Physiology independently forces a **Mixed class**: combined stress is interactive, not additive (Angon 2022), heat confounds stomatal signatures (Feller 2014), and severity changes the response (Tardieu 2018).
2. **The water axis has a mature physics backbone to build on.** CWSI is operationally validated in the study region itself: Zoratipour et al. establish hourly/daily CWSI, ML bias correction of satellite CWSI (R² +20.65%, rMBE −50%), and the Landsat-vs-Sentinel-2 thermal comparison; local constants exist (Ky = 1.05 vs FAO 1.2; CWSI irrigation threshold 0.4–0.5). Thermal proxies track canopy water status but cannot alone separate osmotic from hydraulic stress (Maes & Steppe 2012; Gerhards 2019) — which is precisely why a disentanglement model, not another index, is needed.
3. **The salinity axis has proxies but no temporal disentanglement.** Satellite salinity mapping is dominated by supervised ML on indices (e.g., Wang 2021, S2-RF in arid China); Paciolla 2025 shows satellite LAI can infer salinity effects **without ground ECe** — the enabler for labeling 490 fields — and Smanov 2026 identifies the confounders (crop salt tolerance, ion composition, phenology) that any Khuzestan salinity branch must handle.
4. **SITS architectures have just crossed into Mamba/SSM territory — for crop type, not stress.** SITSMamba (2024) is the first CNN-Mamba for SITS (PASTIS crop classification); Rußwurm & Körner (2020) showed raw-band temporal models beat index-based ones. No Mamba/SSM application to stress classification exists (documented negative search: `deep_researches/search_logs_2026-10-04.md`).
5. **Label efficiency is the correct design constraint, and SSL is the tool.** The thesis has ~490 fields but expects only 50–100 expert labels; SSL (temporal contrastive, Barlow Twins–family) uses the full unlabeled archive. The corpus contains no EO-specific multi-modal SSL recipe (optical + thermal) — gap G3.
6. **Explainability is where the thesis claims its sharpest novelty — and where the field is weakest.** Höhl et al. 2024 (systematic review, 207 studies; verified by full read): RS-XAI overwhelmingly handles spatial data — most XAI methods "do not explicitly consider temporal dependencies, making some of them unreliable or inaccurate" (p.22) — and **over 90% of studies evaluate explanations only anecdotally** (15/207 use functional metrics). A precedent for temporal importance exists (Rußwurm & Körner, crop classification; cited by Höhl as [158]), and James et al. 2025 combine contrastive SITS with feature-level SHAP/Grad-CAM — but **no work provides timestep-level explanation of a deep SITS stress model, and none validates explanations against plant physiology** (documented in `deep_researches/search_logs_2026-10-04.md`).

**Net finding:** A CNN-Mamba + SSL + temporal-XAI framework for **concurrent water–salinity disentanglement at field scale in an arid irrigated sugarcane system**, validated against the unique Khuzestan local baselines (CWSI thresholds, Ky, LAI retrieval, R² = 0.93 yield baseline), is novel on all four axes (architecture, SSL recipe, label design, XAI) and feasible with free data + one GPU. The full gap analysis is §5 (G1–G7); the design it motivates is `Thesis_Vault/04-Thesis-Design.md`.

---

## 2. Where the Load-Bearing Papers Sit

The canonical, per-paper matrix lives in `Thesis_Vault/Literature-Matrix.md` (rows 01–78, with status and notes). This section maps only the papers that carry the thesis's weight, by pillar:

| Pillar | Papers (matrix #) | Role |
|---|---|---|
| Concurrent water–salinity | 69 Wen 2021 · 70 Wen 2022 · 71 Wen 2023 · 43 Angon · 21 Li · 40 Feller · 41 Tardieu | Problem statement + physiology of the Mixed class |
| Salinity RS | 08 Paciolla · 19 DeepSalt · 20 Gupta · 27 Shi · 43 Wang 2021 · 46 Smanov | Salinity proxy + label strategy + confounders |
| CWSI / thermal | 39 Maes · 42 Gerhards · 68 Ahmad · 10/24/25 Zoratipour · 13 Sapkota · 35 Hornero · 36 Sanchez-Virosta · 37 Bai · 73 Gokul · 75 Olawoyin · 78 Virnodkar | Water-axis physics + validation design |
| Khuzestan local baselines | 09 Motlagh · 76 Motlagh-Ky · 12 Malee · 11 Hajeb · 23 Vinayaka · 77 Waters | Site-specific constants, thresholds, yield baseline |
| SITS / SSL / stress DL | 01 SITSMamba · 14 STS-NET · 15 EigenCL · 16 Sadbhave · 05 Rußwurm · 02 Miller · 60 Paul · 26 Agastya · 22 DroughtSet | Architecture blueprint + competitors |
| XAI | 04 Höhl · 06 Ahmed · 17 Najjar | Gap G2/G6 evidence + validation protocol inputs |
| Agentic GeoAI (frozen) | 47–67 | Future-work / optional chapter only (decision 2026-10-04) |

**Reading status (2026-10-04):** verified full reads completed for 70 (Wen 2022 HESS); P0 queue in progress: 09, 08, 01, 04, 07, 10/24/25, 14. All other notes are extract-level ("🆕") — quantitative claims below carry the reading status of their source note.

---

## 3. State of the Art by Pillar

### 3.1 Concurrent water–salinity stress — the problem statement

The canonical chain (verified against full text where marked):

- **Wen et al. 2021** (`papers/69`, RS 13:6, meta-review) — ✅ **full read 2026-10-04** (`Thesis_Vault/papers/69-Wen-2021-Salinity-Drought-RS-Challenges.md`): systematic review 2005–2020 (1,184 records → 115 pubs → 348 correlations); VIs "insufficiently accurate (0.02 ≤ R² ≤ 0.80)" and joint signals "overlapped spectrally, thereby significantly limiting" separate monitoring (**both verbatim, but the second is abstract-only wording** — the Discussion version is weaker); **zero VI–salinity correlations in the entire corpus (all 171 VI–wavelength correlations were drought-only)**; drought and salinity "cannot be seen independently"; plant responses to both "are identical at the early stage" (p.10); traits "have a big potential" but are "not necessarily stronger" than VIs — **osmotic/ionic traits are the real standout (all R² > 0.50) yet not directly RS-tractable**; recommends RTM multi-trait retrieval via multi-sensor frameworks; **no ML anywhere in the corpus, no sugarcane, NDVI deliberately excluded**. → *The thesis problem statement, with the caveat below.*
- **Wen et al. 2022** (`papers/70`, HESS 26:4537) — ✅ **full read 2026-10-04** (`Thesis_Vault/papers/70-Wen-2022-HESS.md`): five Sentinel-2-derived canopy traits (LAI, FAPAR, FVC, Cab, Cw) at 10 m via PROSAIL (SNAP biophysical processor, ANN on simulated database; **no independent per-trait accuracy assessment**); maize + potato, North Holland, 138.74 km²; stresses ground-defined from SPEI-3 (drought) and topsoil chloride from a 3D groundwater dataset (salinity) — **no in-situ measurements**; two-way ANOVA of stress-class × date per crop × trait: R² 0.326–0.796, date effects ≫ stress effects, interaction > stress main effect; drought dominates salinity despite FAO thresholds being surpassed ("salinity impacts may have been overstated"); effects strongly phenology-dependent. → *The statistical pipeline the thesis supersedes: descriptive trait ANOVA → predictive per-field disentanglement.*
- **Wen et al. 2023** (`papers/71`, IJAEOG 122:103438) — ✅ **full read 2026-10-04** (`Thesis_Vault/papers/71-Wen-2023-Crop-Salinity-Drought-US.md`): trilogy upscaling — 8 crops, contiguous USA, single 2021 season, S2GM-2 60 m composites → same 5 traits, new **pairwise matched-control design** (1-km cells, 30-km buffer, matched on crop/soil/climate/state); combined stress > individual impacts (exceptions: almond, sorghum); strongly time-dependent; **trait-response sequencing LAI first → FVC/FAPAR → Cw/Cab last** (a testable hypothesis for our temporal XAI); literature tolerance classes **failed** to predict responses; **still ANOVA-only (no ML, no accuracy metrics), proxy labels (SPEI-3 + static gNATSGO soil EC), no per-field unit**; explicitly claims "a quantitative foundation for simultaneously assessing" stresses. → *Positioning foil: assessment, not disentanglement; their matched-control logic is the statistical ancestor of contrastive SSL.*
- **Physiology of the Mixed class:** Angon et al. 2022 (`papers/07`, Plants 11:2884) — combined drought+salinity is **interactive, not additive**; Feller & Vaseva 2014 (`papers/40`) — heat reverses/confounds stomatal signatures; Tardieu et al. 2018 (`papers/41`) — severity changes trait expression → hard global classes are fragile, mixture/soft labels are safer. Li et al. 2025 (`papers/21`) extends the mechanism review.
- **Multi-sensor differentiation gap:** Berger et al. 2022 (`papers/44`, RSE 280:113198, ~290 cites) — ✅ **full read 2026-10-04** (`Thesis_Vault/papers/44-Berger-2022-Optical-Stress-Synergies.md`): 38-author review of 96 multi-domain studies; "**no concept exists that uses multiple spectral domains in an integrated way … to differentiate between crop stress types**" (p.3), and stress-type differentiation "will remain a challenge with purely RS-based approaches because distinct stressors often lead to similar stress reactions" (p.14); ~72% parametric/VI methods; deep learning "still missing" (p.11); zero XAI; **VIS+NIR+SWIR+TIR — exactly the Landsat 8/9 suite — used in only 12/96 studies**; salinity 5.0% of studies, never synthesized. → *Supports both the Landsat-only design and the G4 framing; also the warning that our gap statement must say HOW we attempt what they declare hard.*
- **Salinity–vegetation mediation:** Smanov et al. 2026 (`papers/46`) — crop salt tolerance mediates spectral–ECe relationships; ion composition and phenology are ignored in most models → the confounders a Khuzestan salinity branch must address.

**Positioning rule (adopted 2026-10-04, strengthened after the 2023 full read):** cite the Wen trilogy as *the* precedent for satellite concurrent-stress monitoring — including its own claim of "a quantitative foundation for simultaneously assessing" stresses (Wen 2023, p.9) — then state what it still does not do: (1) predictive deep models (all three papers are correlation/ANOVA-based; the trilogy contains **no machine learning at all**), (2) per-field stress-type **disentanglement** (mixed stress is a category contrasted against matched controls, never a signal to be separated within a field), (3) multi-year per-field labels from in-situ salinity (their labels are seasonal SPEI + static soil-EC/cloride proxies), (4) arid irrigated sugarcane, (5) explainability. Do **not** claim "nobody maps concurrent drought+salinity from satellites" — Wen et al. did, descriptively; and do not quote the Wen-2021 "has not yet been used" sentence without noting the same group's 2022/2023 follow-ups.

### 3.2 SITS architectures — from Transformers to Mamba

- **Rußwurm & Körner 2020** (`papers/05`): self-attention on **raw optical bands** beats manual-feature (VI) models for SITS crop classification → supports the raw-bands input decision (G7).
- **Miller et al. 2024** (`papers/02`): DL-for-SITS review — cloud gaps, irregular sampling, SSMs noted as "emerging" with no stress applications.
- **SITSMamba 2024** (`papers/01`, arXiv:2409.09673): first Mamba architecture for SITS (CNN feature extraction + Mamba temporal encoder + Positional Weight; reconstruction branch); SOTA on PASTIS — **for crop classification**. The thesis architecture blueprint; thermal-channel insertion point = CNN stem input channels (implementation-level detail pending full read).
- **Stress-adjacent SSL competitors:** **STS-NET** (Dalal 2026, `papers/14`, arXiv:2607.18791) — ✅ full read 2026-10-04: 3D-CAE SSL (reconstruction pretext, T=32) on RGB+NIR+mean-VI PlanetScope (~3 m satellite), pretrained on ~196 km² in Punjab, evaluated on 62 sugarcane fields (UP, 2023 season); accuracy 97.98% (water) / 85.08% (N) / 83.47% (combined — a 9-class water×nitrogen permutation task); **EigenCL** (Ahmad 2025, `papers/15`) — eigenvector contrastive on temporal NDRE, unsupervised, drought-only; **Sadbhave 2025** (`papers/16`) — 3D autoencoder on Sentinel-2 sequences for sugar beet. None uses Mamba, salinity, multi-year satellite archives, thermal channels, or XAI → the differentiation boundary (verified paragraph in `Thesis_Vault/papers/14-STSNET-SelfSupervised-Stress.md`).

### 3.3 SSL for label efficiency

Balestriero et al. 2023 (`papers/03`) is the domain-agnostic SSL foundation (cookbook). Agastya 2021 (`papers/26`) applied contrastive SSL to irrigation detection; Paul et al. 2025 (`papers/60`) — ✅ **full read 2026-10-04** (`Thesis_Vault/papers/60-Paul-2025-DL-Plant-Stress-Review.md`) — is the citable anchor for G3: across their 163-study PRISMA corpus, SSL occupies a single subsection with **3 studies, all leaf/canopy proximal sensing (no satellite, no thermal, no multi-temporal SSL), no SSL-algorithm taxonomy (SimCLR/BYOL/MoCo/Barlow Twins/DINO never appear), and the Conclusion drops SSL from its data-scarcity toolkit** — so "no EO-specific multi-modal (optical + thermal) SSL recipe exists" is now evidenced, not just asserted. Two further verified bonuses: **Mamba/state-space models are entirely absent** from all 163 studies (no prior-art conflict for our architecture; the sequence frontier there is Transformers), and the field's stated remedy for overlapping multi-stress symptoms is an "others" catch-all class (Esgario et al. 2022 via Paul p.19) — avoidance rather than the explicit disentanglement we propose. Design input: color-jitter augmentation degraded SSL pretraining on stress imagery (Nagasubramanian et al. 2022, via Paul p.18) → prefer geometry/seasonal invariances in our Barlow Twins augmentations. Gracia Rojas et al. 2026 (`papers/74`, SLR n=105) confirm sequence models (LSTM/Transformer) are the accepted family for RS stress/yield time series while classical ML remains competitive — and that **validation + uncertainty reporting are the field's weak spots** (the thesis adopts cross-year validation and uncertainty reporting by design). → G3.

### 3.4 CWSI and thermal physics — the water backbone

- **Physics:** Maes & Steppe 2012 (`papers/39`) — canonical ground-thermal CWSI reference; Gerhards et al. 2019 (`papers/42`) — TIR water-stress physics; single-index CWSI fails under co-occurring stresses. Ahmad, Alvino & Marino 2021 (`papers/68`) — canonical water-stress sensor taxonomy (authorship corrected from "Grill" 2026-10-04).
- **Local (Khuzestan) operational results:** Zoratipour et al. — hourly/daily CWSI and critical July–September window (`papers/10`), ML bias correction of satellite CWSI with RF/XGBoost/SVM (`papers/24`, AWM), Sentinel-2 MSI vs Landsat thermal (`papers/25`, Landsat thermal R² 0.78–0.92 vs S2 0.74–0.89 → sensor decision); Sapkota 2025 (`papers/13`) — ET/CWSI/NDVI comparison validating multi-metric scheduling.
- **Method-comparison context:** Bai 2017 (`papers/37`) — CWSI more reliable than TVDI; Hornero 2026 (`papers/35`) and Sanchez-Virosta 2025 (`papers/36`) — CWSI validation methodology (forest/almond, transferable protocols); Gokul 2026 (`papers/73`) — UAV CWSI/CEWT ML benchmarks (classical ML still dominant); Olawoyin 2026 (`papers/75`) — 24-yr in-situ-free LST–NDVI CWSI (template for sparse-ground-data covariates); Virnodkar 2020 (`papers/78`) — pre-2020 RS+ML baseline review.

**Implication:** the water axis enters the CNN-Mamba as **LST + raw bands**; CWSI thresholds (0.4–0.5) serve as external validators, not as inputs only.

### 3.5 Salinity RS — proxies and their limits

Supervised index-based ML dominates (Wang 2021 `papers/43`, R²≈0.78 arid China; Shi 2022 `papers/27`, 34-yr Bayesian; Dey 2025 DeepSalt `papers/19`, domain adaptation + distillation; Gupta 2025 `papers/20`, ground-based optical/thermal salinity signatures). **Paciolla et al. 2025** (`papers/08`, Precision Agriculture) is the load-bearing enabler: satellite LAI + data assimilation infers salinity stress **without ground ECe** — the fallback (or primary) salinity-label source for 490 fields if ECe access is denied (advisor question ①). Transfer conditions and risks documented in its note. Waters et al. 2024 (`papers/77`) — sugarcane health monitoring review, VI table → band selection (recovered 2026-10-04 after falling through every index).

### 3.6 XAI — the claimed novelty

- **Höhl et al. 2024** (`papers/04`, systematic review) — ✅ **full read 2026-10-04** (`Thesis_Vault/papers/04-XAI-RS-Review.md`): 207 studies (2017–2023); SHAP is the most-used single method (94 publications); **>90% of studies evaluate explanations only anecdotally** (15/207 quantitative; "we did not find any works that quantitatively evaluate their explanations" for the local-approximation family); real-world RS "lacks a controlled ground truth for evaluating xAI methods". Temporal dependencies are named as a drawback (p.22) and a Conclusion-level research call (p.24) — but note: the popular repo paraphrase "temporal XAI is virtually unexplored" is **not verbatim**, and Höhl cites a temporal-importance precedent (Rußwurm & Körner, crop classification, their ref [158]). → The G2 claim must be worded precisely (see §5 and `search_logs_2026-10-04.md`).
- Ahmed et al. 2025 (`papers/06`): XAI for agricultural spectroscopy (methodological analogy, not satellite SITS); Najjar et al. 2024 (`papers/17`): SHAP-guided vegetation-index enhancement (no temporal dimension).
- **Near-neighbor (added 2026-10-04):** James, Kansara & Agrawal 2025 (IEEE AsianCON, doi:10.1109/asiancon66527.2025.11281233) — SimCLR 3D encoder on S2 VI composites + SHAP/Grad-CAM for crop stress at feature/region level per month; pseudo-labels + separate ensemble classifier; no water-vs-salinity typing, no timestep-level attribution, no physiological validation.
- **No paper explains which timesteps drive a stress prediction, and none validates RS-XAI outputs against plant physiology** → the thesis's G2/G6 contribution (temporal SHAP on Mamba selectivity + temporal Grad-CAM, physiologically validated against Angon-style response directions).

### 3.7 Khuzestan local baselines — the site-specific advantage

Motlagh et al. 2026 (`papers/09`) — ✅ **full read 2026-10-04** (`Thesis_Vault/papers/09-Khuzestan-Yield.md`): RF on 336 Amirkabir fields (2023 season); **the headline R² = 0.93 is the full-sample fit — the independent test R² is 0.821 (RMSE 7.56 t/ha)**, which is the honest baseline to match/exceed; feature importance CWSI 40.6% > soil salinity 27.1% > crop age 9.0%; the water×salinity synergy appears as partial-dependence collapse (salinity ≈3.4 dS/m combined with CWSI > 0.44), not as interaction percentages; soil salinity was measured weekly as saturated-paste ECe (0–90 cm, 128 wells, kriged) spanning 1.7–8.0 dS/m — the salinity-label protocol our thesis can inherit; Motlagh et al. 2026b (`papers/76`): local Ky = 1.05 (FAO default 1.2 overestimates), peak sensitivity early July; Hajeb et al. 2023 (`papers/11`) — ✅ **full read 2026-10-04** (`Thesis_Vault/papers/11-Hajeb-2023-S2-Retrieval.md`): simultaneous 4-trait S2 retrieval (BRANN) **in the same Amir Kabir zone**; LAI RMSE 0.48 m²/m²; the plant-water proxy (leaf sheath moisture) retrieved to 2.91% RRMSE from multispectral bands — direct evidence the water-stress signal is recoverable in this landscape; 136 ESUs with destructive/SPAD/Kjeldahl protocols supplied by the Khuzestan Sugarcane Institute = our ground-campaign template; zero salinity or stress measurement (label proxies only); Malee et al. 2026 (`papers/12`): FAO-56 dual-Kc sugarcane coefficients + deficit irrigation (**Thailand**, Kcb mid-season 1.11 — transferable calibration context, not local); Vinayaka et al. 2025 (`papers/23`): AI/RS sugarcane review; Waters et al. 2024 (`papers/77`): sugarcane health monitoring (band-selection input). No competitor paper can claim this level of site-specific grounding — it is the thesis's strongest practical asset. *(Correction 2026-10-04: an earlier draft attributed "Kcb values" to Hajeb and placed Malee in Khuzestan — the papers/12-*.pdf had been mis-filed as the Motlagh-Ky paper; both fixed, matrix rows #11/#12 corrected.)*

### 3.8 GeoAI agents — frozen as future work (decision 2026-10-04)

The agentic RS stack (RS-Agent, Earth-Agent-Pro, REMSA, RSMeM, AgriWorld, CottonBot; `papers/47–67`, notes G1–G21) matured rapidly 2024–2026, but it **operationalizes** models rather than contributing the disentanglement science. Decision: **agents = optional chapter / future work; cluster 47–67 frozen** (rationale and revisit conditions in `Thesis_Vault/04-Thesis-Design.md` §5). If revived, adopt Munir's EO-native design principles + ThinkGeo-style step-wise evaluation.

### 3.9 Foundation models — retained as ablation/background only

The corpus holds the FM-era material (Prithvi-EO-2.0, Clay, TerraMind, AlphaEarth; PDFs in `papers/archived_foundation_models/`) and the full analysis in `phase1_stress_detection_methods.md`. In the current design, frozen-encoder FM ablations are a **robustness check**, not the contribution: FMs are pre-trained on optical-only modalities, none handles long single-site SITS with thermal, and their anomaly-score use for stress remains unproven. REMSA (`papers/59`) provides the constraint-aware FM-selection methodology if the ablation is run.

---

## 4. What Has and Has Not Worked Operationally

**Works:** daily/16-day field-scale water-stress indices in arid irrigated systems (Zoratipour series; Olawoyin); ML bias correction of thermal-derived indices; supervised index-based salinity mapping; SSL pre-training for crop type (SITSMamba, PASTIS).

**Does not (yet):** stress-*type* differentiation from satellite archives (labels + spectral overlap); distinguishing salinity from water stress without ground truth; transferring EU/US models to arid Iran; temporal explanation of stress predictions; operational mixed-stress labels.

---

## 5. Research Gap Analysis (aligned with `Thesis_Vault/03-Research-Gaps.md`)

| Gap | Statement | Severity | Evidence anchor |
|---|---|---|---|
| **G1** | No SSM/Mamba applied to stress classification in SITS | High | SITSMamba (crop type only); Miller review ("emerging"); negative searches documented `deep_researches/search_logs_2026-10-04.md` |
| **G2** | No temporal XAI for RS time series | Very High | Höhl 2024 (exact quotes in note); Ahmed 2025 |
| **G3** | No SSL recipe for multi-modal SITS (optical + thermal) | High | Balestriero (domain-agnostic); EigenCL (single index); STS-NET (VIs, UAV) |
| **G4** | Mixed-stress class not modeled operationally | Critical | Angon (interactive physiology); Motlagh (interaction); Wen trilogy (descriptive only) |
| **G5** | No public benchmark for stress-type classification | High | CropHarvest/PASTIS = crop type only |
| **G6** | XAI explanations not validated physiologically | High | Höhl (weak evaluation practice); Angon (physiology unused by RS) |
| **G7** | Raw bands vs indices unresolved for stress SITS | Medium | Rußwurm & Körner 2020 |

Superseded FM-era gaps (anomaly-score backbones, FM stress differentiation, AL for stress) are retained in `phase1_stress_detection_methods.md` for the record; they no longer structure the thesis.

---

## 6. Recommended Thesis Direction (replaces FM-era T1–T10)

> **"A self-supervised CNN-Mamba framework with physiologically validated temporal XAI for disentangling concurrent water and salinity stress in an arid irrigated sugarcane system (Amirkabir, Khuzestan) from a 12-year Landsat archive."**

Four-phase design (data pipeline → SSL pre-training → fine-tuning + XAI → writing), the decisions table (raw bands vs indices; Barlow Twins vs SimCLR; Landsat-16d vs fused-S2; agentic freeze), the label strategy, and the validation protocol are maintained in **`Thesis_Vault/04-Thesis-Design.md`** — single source of truth for methodology. Alternatives considered and rejected: FM anomaly-score backbone (advisor-rejected frame), causal attribution (scientifically untenable without labels/confounder control — hence *disentanglement with confidence*, not causation), active learning as a core pillar (demoted; label budget is small enough for SSL + expert labeling).

---

## 7. Recommended Reading Order (for the student, current frame)

1. Wen et al. 2021 (`papers/69`) — the problem statement.
2. Wen et al. 2022 (`papers/70`) — ✅ full read; the statistical baseline being superseded.
3. Angon et al. 2022 (`papers/07`) — physiology of the Mixed class.
4. Paciolla et al. 2025 (`papers/08`) — salinity label strategy without ECe.
5. SITSMamba (`papers/01`) — architecture blueprint (+ GitHub clone).
6. Höhl et al. 2024 (`papers/04`) — temporal-XAI gap + evaluation practice.
7. Zoratipour 2025/2026 (`papers/10/24/25`) — local CWSI physics + bias correction.
8. Motlagh 2026 (`papers/09`) — the R² = 0.93 baseline to match/exceed.
9. Dalal 2026 STS-NET (`papers/14`) — closest competitor; the differentiation paragraph.
10. Balestriero 2023 (`papers/03`) + Paul 2025 (`papers/60`) — SSL recipe background.
11. Rußwurm & Körner 2020 (`papers/05`) — raw-band input justification.
12. ~~Then: 71 (Wen 2023), 44 (Berger), 72 (Haq), 77 (Waters), 11 (Hajeb), 12 (Malee), 76 (Motlagh-Ky), 78 (Virnodkar).~~ **Done 2026-10-04** — all verified with notes (78/Virnodkar remains extract-level, pre-2020 anchor only).

---

*This document was fully rewritten on 2026-10-04 to the advisor-approved frame (CNN-Mamba + SSL + temporal XAI, concurrent water–salinity disentanglement, Amirkabir/Khuzestan); the previous FM-era recommendation is preserved only in §3.9 and in `phase1_stress_detection_methods.md`. Citations correspond to the numbered local corpus in `papers/` (01–78); reading depth per note is tracked in `Thesis_Vault/Literature-Matrix.md`. All quantitative claims above inherit the reading status of their source note — extract-level unless marked ✅ full read.*
