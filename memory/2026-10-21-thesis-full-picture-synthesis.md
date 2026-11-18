---
date: 2026-10-21
tags: [memory, synthesis, thesis-frame, literature, gaps, design, corrections]
---

# Memory — 2026-10-21: Full-Thesis Synthesis (Corpus 01–78 + Vault + Memory Logs)

## 0. What this pass did

Read, in full: `Thesis_Vault/Literature-Matrix.md` (78 rows), `00-Thesis-Overview.md`,
`03-Research-Gaps.md`, `04-Thesis-Design.md`, **all 78 vault notes** in `Thesis_Vault/papers/`,
the 10 files in `memory/`, `lit_review/00_thesis_literature_review.md`,
`proposal/draft/00-proposal-skeleton.md`, `todo.md`, and
`deep_researches/search_logs_2026-10-04.md`.

Purpose: consolidate the whole project state into one durable picture, and surface the
places where the matrix and the lit review still carry wording that the vault notes
already corrected.

**No files were changed except this memory log.** The matrix and lit review corrections
listed in §9 remain open.

---

## 1. The thesis, final frame

**Title.** *A Self-Supervised and Explainable CNN-Mamba Framework for Disentangling
Concurrent Water and Salinity Stress from Multi-Temporal Satellite Imagery.*

**Site.** Amirkabir Agro-Industrial Unit, Khuzestan, Iran. About 490 sugarcane fields,
~25 ha each. Landsat 7/8/9 L2, 2013–2025, ~88 sixteen-day composites.

**Research question.** Given a multi-temporal satellite time series, can a model identify
the probable drivers of crop stress (water deficit, salinity, or mixed), with
physiologically interpretable explanations?

**The defining pivot.** The first proposal asked for *causal attribution* of water vs.
salinity stress. The advisor rejected it as scientifically untenable (hidden confounders,
spectral overlap, no ground truth, interactive effects). The current frame asks for
**disentanglement with confidence**. The output is a diagnostic report with feature
importance rankings, not a causal claim.

**Four classes.** `Healthy | Water_Only | Salinity_Only | Mixed_Stress`.

**Target journals.** RSE → ISPRS J. → IEEE TGRS → CEA.

---

## 2. Corpus state (2026-10-21)

- **78 papers**, slots 01–78, no gaps, no duplicates. **Every slot has a vault note.**
- Reading depth: full-read for every load-bearing paper. The 2026-10-04 P0 queue is closed.
- **Frozen agentic cluster: rows 47–59 and 63–67 (18 papers).** Future work only. Do not extend.
  Verdict in every note is "Optional" (Low-Medium for #50 AgriWorld and #66 Musazade).
- **Foundation models: 7 archived PDFs** (Prithvi-EO-2.0, Prithvi-1.0, TerraMind, AlphaEarth,
  Clay v1.5, SatMAE, FARM). Ablation/robustness-check only. **No vault notes** (user declined
  2026-10-20). `papers/ARCHIVED_Foundation_models/FARM.pdf` is truncated/corrupt.
- Negative searches are documented and auditable in `deep_researches/search_logs_2026-10-04.md`.
- Zotero library: 78 items imported, 7 manual items still to verify in the client (6, 10, 13, 25, 35, 36, 37).

---

## 3. The five load-bearing evidence chains

### 3.1 The problem is real, and only monitored descriptively

- **Wen 2021** (`papers/69`, RS 13:6): 1,184 records → 115 publications → 348 correlations.
  VIs "insufficiently accurate (0.02 ≤ R² ≤ 0.80)". Joint signals "overlapped spectrally,
  thereby significantly limiting" separate monitoring. **Zero VI–salinity correlations in the
  whole corpus** (all 171 VI–λ correlations are drought-only). Responses to drought and
  salinity are "identical at the early stage" (p.10). No ML anywhere in the 2005–2020 corpus.
  No sugarcane, no Iran, no arid irrigated field-scale study. NDVI deliberately excluded.
- **Wen 2022** (`papers/70`, HESS 26:4537): five S2 traits (LAI, FAPAR, FVC, Cab, Cw) at 10 m
  via PROSAIL in the SNAP biophysical processor (ANN on a simulated database).
  **No per-trait RMSE validation anywhere.** Two-way ANOVA on stress-class × date gives
  R² 0.326–0.796; date effects dominate; interaction > stress main effect. Drought beats
  salinity ("salinity impacts may have been overstated"). Labels are proxies
  (SPEI-3 + groundwater Cl⁻ at 250 m), never in-situ. 138.74 km², maize + potato.
- **Wen 2023** (`papers/71`, IJAEOG 122:103438): 8 crops, CONUS, single 2021 season.
  S2GM-2 60 m monthly composites → same 5 traits. **Pairwise matched-control design**
  (1-km cells, 30-km buffer, matched on crop/soil/climate/state). Combined > individual
  (exceptions: almond, sorghum). **Trait sequencing: LAI first → FVC/FAPAR → Cw/Cab last.**
  Literature tolerance classes failed to predict responses. **Still ANOVA-only. No accuracy
  metrics. Proxy labels. No per-field unit.** Claims only "a quantitative foundation for
  simultaneously assessing" stresses (p.9).

**Positioning rule (adopted 2026-10-04, must hold):** cite the Wen trilogy as *the* precedent
for satellite concurrent-stress monitoring, then state what it still does not do —
(1) no predictive model (the trilogy has **no machine learning at all**), (2) no per-field
stress-type *disentanglement* (mixed stress is a category contrasted against matched controls,
never a signal separated within a field), (3) multi-year per-field labels from in-situ
salinity, (4) arid irrigated sugarcane, (5) no explainability. Never write "nobody monitors
concurrent stress from satellites". Never quote Wen 2021's "has not yet been used" without
noting the same group's 2022/2023 follow-ups.

### 3.2 The thermal channel is physically ambiguous (the thesis's physics backbone)

- **Maes & Steppe 2012** (`papers/39`, JXB 63:4671): CWSI (eq. 41) is a one-dimensional
  functional of stomatal conductance. T_pot and T_dry come from the energy balance of a
  maximally transpiring and a non-transpiring canopy *of the same structure*, so every driver
  that lowers g_s (hydraulic, osmotic, cuticular) moves T_c along the same axis, while
  heat-driven stomatal opening moves it the other way. **The thermal signal is equifinal
  with respect to the driver.** ⚠️ This is a *derivation from the equations*, not a sentence
  the authors write. The review contains **no** salinity statement.
  Also: the empirical baselines a_pot/b_pot are not weather-independent (they drift with T_a,
  u, K_in, crop height, LAI) → argues for conditioning thermal features on meteorological
  co-drivers, not a fixed threshold.
- **Tardieu 2018** (`papers/41`, Annu. Rev. Plant Biol. 69): "a given field can belong to
  different scenarios in different years" (p.736) → a stress class belongs to a
  (field, time-window) pair. Trait effects **flip sign** across the 5 Table-1 scenarios.
  A given allele has a positive effect in at most half the fields → a binary label carries
  ≲50% correctness by construction. **Osmotic adjustment: ~30 min half-time, turgor held
  within 0.5 MPa** while growth and photosynthesis still deteriorate → under salinity the
  canopy temperature can stay near normal while the plant declines. The thermal channel is
  **structurally biased**, not merely noisy. "Reducing leaf area is not associated with a
  risk of heat stress" (p.742) → LAI trajectory is a thermal-safe discriminator.
- **Feller & Vaseva 2014** (`papers/40`, Front. Environ. Sci. 2:39): "heat and drought act in
  an opposite manner on stomates" (p.2). 5–10 °C within-canopy spread at identical water
  status. Minutes-scale stomatal lag after a light transition. Rubisco activase is impaired
  above 30 °C → a heat wave depresses assimilation with no water-status change. Salt shares
  the osmotic and oxidative injury class (p.8). ⚠️ The paper has **no non-additivity test**
  and no interaction statistic. Cite it as physiological rationale, not as a measured effect.
- **Motlagh-Ky 2026** (`papers/76`, AWM 330:110260), the author's own sentence:
  "salinity stress that also affect[s] canopy temperature could potentially confound
  interpretation." A local author in the target region admits the confound.
- **Gerhards 2019** (`papers/42`, RS 11:1240): "it remains difficult to detect and monitor
  plant water deficit based on a single plant response" (p.2), because responses are
  "modified by co-occurring plant stresses". Multi-sensor integration is the remedy
  (p.12, p.16). Landsat 8 TIRS at 100 m ≈ one field per pixel, 16-day revisit; the trade-off
  is 1–3 day / 1 km for MODIS-AVHRN-Sentinel-3. TIR is the most *sensitive* single domain
  (best in a comparative airborne study) — the failure is **specificity**, not sensitivity.
  ⚠️ The paper has **no salinity content** and no co-stress experiment. "CWSI fails under
  co-occurring stresses" is a thesis-level inference.
- **Ahmad, Alvino & Marino 2021** (`papers/68`, RS 13(20):4155 — issue is 20, not 16):
  seven-family sensor taxonomy with a named failure mode per family. Salinity appears only
  as "Soil Moisture and Ocean Salinity". No SSL, no SSM, no Mamba (October 2021 vintage).

**This chain is the strongest original argument in the project, and the matrix does not yet
carry it as a named chain.**

### 3.3 Salinity is the neglected axis (four-way documentation)

| Source | Salinity content |
|---|---|
| Waters 2025 (`papers/77`, CEA 229:109686) | **Zero mentions.** ~1 time-series study. DL named as *future* work. "Other moisture-based vegetation indices should be heavily considered." Only 1 of the reviewed studies applied BRDF correction. |
| Paul 2025 (`papers/60`, CEA 229:109734) | ~2 of 163 studies, both proximal. SSL = 3 studies, all leaf/canopy proximal. **Mamba/SSM entirely absent.** ~20–22 drought studies. |
| Berger 2022 (`papers/44`, RSE 280:113198) | **5.0% of 96** studies, never synthesized. |
| Wen 2021 (`papers/69`) | **Zero** VI–salinity correlations in the corpus. |

**Berger also carries the flagship G4 quote (p.3):** "no concept exists that uses multiple
spectral domains in an integrated way … to differentiate between crop stress types", and the
counter-warning (p.14): differentiation "will remain a challenge with purely RS-based
approaches because distinct stressors often lead to similar stress reactions".
Other Berger numbers: ~72% parametric methods; deep learning "is still missing" (p.11);
zero XAI in 23 pages; **VIS+NIR+SWIR+TIR — exactly the Landsat 8/9 suite — used in only
12/96 studies**; all five domains in 4/96. Their corpus **excludes single-sensor studies by
design** (so the claim is "compare not fuse" + 72% parametric, not "single-sensor dominates").
Their "hybrid" means RTM+ML, **not** SSL.

### 3.4 The site-specific advantage

| Constant | Value | Source |
|---|---|---|
| Yield baseline | Full-sample R² **0.93** / RMSE 5.38 t/ha (n=336); **independent test R² 0.821**, RMSE 7.56 (n=100) | Motlagh 2026 (`papers/09`) |
| Driver importance | CWSI 40.6% > salinity 27.1% > age 9.0% > water table 7.0% | Motlagh 2026 |
| Water×salinity synergy | 3.4 dS/m alone → modest loss; 3.4 dS/m + CWSI > 0.44 → "yield collapsed". **No interaction percentages exist** (PDPs only) | Motlagh 2026 |
| Salinity protocol | Weekly saturated-paste ECe, 0–90 cm, 128 wells, kriged; 1.7–8.0 dS/m; seasonal map 2.93–4.35; 1.7 dS/m is also the cited cane tolerance threshold | Motlagh 2026 |
| Ratoon vulnerability | Age 4–5 far more vulnerable to water deficit than age 1–2; salinity×age effect intensifies with age | Motlagh 2026 |
| CWSI trigger | 0.4–0.5 (conclusions: 0.5); own age tiers: young 0.40–0.45, old 0.30–0.35 | Zoratipour 2026 (`papers/10`) |
| Local Ky | 1.05 vs FAO-66 1.2 ("may prompt over-irrigation"); range 0.2–1.63; early-July peak Ky > 1.82; ET₀ ≈ 2,150 mm/yr | Motlagh-Ky (`papers/76`) |
| LST bias correction | RF best (test R² 0.86, RMSE 2.66 °C); CWSI R² 0.73→0.92 (+20.65%), rMBE −16%→−8%, nRMSE 23%→13% | Zoratipour 2025 (`papers/24`) |
| Sensor decision | Landsat thermal CWSI R² 0.78–0.92 / RMSE 0.08–0.11 vs S2 DMSI R² 0.74–0.89 / RMSE 0.14–0.15; peak stress 0.65 / 0.69 on 24 July 2024 | Zoratipour 2025 (`papers/25`) |
| CWSI timing | Peaks 10:00 and 14:00; daily minimum 2 days after irrigation; CWSI leads soil moisture by 1–2 days (r = −0.808) | Zoratipour 2026 (`papers/10`) |
| LAI / plant-water retrieval | LAI RMSE 0.48 m²/m² (37.8% RRMSE); leaf sheath moisture 2.91% RRMSE; LCC 5.85 μg/cm²; LNC 0.232%. 136 ESUs (not fields), BRANN 38/64 effective params, 201 bootstraps, "marginal gain" | Hajeb 2023 (`papers/11`) |
| Dual-Kc calibration | Kcb 0.15 / 1.11 / 0.49 vs FAO-56 0.15 / 1.20 / 0.70; 25–50% MAD maintain competitive yields; ET 11,708 vs 11,680 m³/ha | Malee 2026 (`papers/12`) — **Thailand, not Khuzestan; method template only** |

**No competitor paper has this level of site grounding.** Six papers come from the same unit,
the same agro-company group, and the Khuzestan Sugarcane Research and Training Institute.

### 3.5 The methodological frontier

- **SITSMamba 2024** (`papers/01`, arXiv:2409.09673): first Mamba for SITS — **crop type, not
  stress**. CNN stem (2× Conv2D 3×3, BN, ReLU, 128 filters) → one Mamba block over T →
  dual decoder (classification + auxiliary reconstruction). **PW is a linear loss re-weighting
  of the reconstruction MSE ({1/L … L/L}), not attention** (eq. 5). Training is
  **single-stage supervised multi-task (CE + w0·w1·L_p, w0 = 0.03, w1 = L_p/L_cla) — NOT SSL**;
  the paper positions itself *against* the two-step SSL paradigm. 0.25 M params, 56.53 GFLOPs.
  PASTIS32 OA 0.7416 / mIoU 0.5005 / mF1 0.6449; MTLCC OA 0.9104. Mamba is **temporal only**
  (no spatial scan, stated as a limitation). **Thermal insertion = one `input_dim` knob** in
  the released code, but the released file defines class `UMamba` with a U-shaped encoder,
  diverges from the paper, and references an undefined `down_blocks` → **treat the released
  model as possibly incomplete and verify it runs before building on it.**
- **STS-NET 2026** (`papers/14`, arXiv:2607.18791) — closest predecessor: 3D-CAE, 19.2 K params,
  T=32, input = RGB + NIR + mean-of-4-VIs (5 channels), PlanetScope ~3 m, pretrained on ~196 km²
  (Barnala, Punjab), evaluated on 62 sugarcane fields (Lakhimpur Kheri, UP, 2023, first-year
  plant cane). **97.98 / 85.08 / 83.47 are accuracy** (abstract mislabels them "precision").
  Combined = a 9-class water×nitrogen permutation task. **No salinity, no Mamba, no XAI, no
  multi-year, no moderate-resolution satellite.** A verified differentiation paragraph exists
  in the note.
- **Höhl 2024** (`papers/04`, arXiv:2402.13791): 207 studies (2017–2023); SHAP in 94;
  **over 90% evaluate anecdotally**, 15/207 use functional metrics; "we did not find any works
  that quantitatively evaluate their explanations" for the local-approximation family;
  "Real-world datasets lack a controlled ground truth for evaluating xAI methods".
  p.22: most xAI methods "do not explicitly consider temporal dependencies, making some of
  them unreliable or inaccurate". p.24 Conclusion: research call on temporal dependencies.
  **Precedent exists** — Rußwurm & Körner [158] measure temporal importance for crop
  classification; Dantas et al. do RS time-series counterfactuals. So the repo phrase
  "temporal XAI is virtually unexplored" is a **paraphrase, not a quote**.
- **Gracia Rojas 2026** (`papers/74`, RSASE 44:102279): PRISMA-2020, n=105 (2020–2025).
  CNN 78.2% of DL studies; RF 70.3% / SVM 29.7% / GBDT 27.0% of classical ML;
  Transformers/attention 5.5%. **Plant health & stress = only n=19, all UAV/proximal.**
  "Pure random k-fold persists and is insufficient for interannual/intersite generalisation."
  Calibrated uncertainty is underutilised. Sequence models are the accepted family for RS
  time series → third-party support for a sequence backbone.
- **Paul 2025** (`papers/60`): SSL = one subsection, 3 studies, all proximal. The Conclusion's
  data-scarcity toolkit **drops SSL**. Colour jitter degraded SSL pretraining on stress imagery
  (Nagasubramanian 2022, via Paul p.18) → prefer geometry/seasonal invariances.
  The field's remedy for overlapping stresses is an **"others" catch-all class** (Esgario
  2022 via Paul p.19) — avoidance, not disentanglement. A clean positioning contrast.
- **EigenCL 2025** (`papers/15`): eigenvector-guided contrastive on temporal NDRE. Principal
  eigenvector captures 76% variance (r = 0.95); silhouette 0.748; k-NN 89.1%; detects 76% of
  stress cases up to 12 days before NDRE threshold crossing. Closest SSL analogue.
- **Sadbhave 2025** (`papers/16`): unsupervised 3D autoencoder on S2 sequences for sugar beet,
  with **acquisition-date temporal encodings** — reusable. Public code.
- **Rußwurm & Körner 2020** (`papers/05`): raw bands beat hand-crafted indices for temporal
  models; self-attention focuses on a few relevant timesteps; 262M processed S2 products.
- **DeepSalt 2025** (`papers/19`): teacher Transformer on lab FTIR → student on EnMAP HSI with
  knowledge distillation. R² 0.87 with KD vs 0.47 without. The label-scarcity route.
- **Negative searches** (`deep_researches/search_logs_2026-10-04.md`): G1 negative confirmed,
  G3 negative confirmed, core-niche negative confirmed. **One near-neighbor found**:
  James, Kansara & Agrawal 2025 (IEEE AsianCON, doi:10.1109/asiancon66527.2025.11281233) —
  SimCLR 3D encoder on S2 VI composites + SHAP/Grad-CAM at feature level per month, pseudo-labels,
  95.17% accuracy. It does not close the gap: no raw+thermal input, no water-vs-salinity typing,
  no timestep attribution, no physiology validation, conference paper.

---

## 4. The seven gaps, with the wording that is safe to use

| Gap | Safe claim | Do not write |
|---|---|---|
| **G1** | No Mamba/SSM architecture has been applied to crop-stress classification from SITS | "Mamba is untested in agriculture" (ScopeMamba, detection, exists) |
| **G2** | No **timestep-level** temporal explanation of a deep SITS stress model exists, and none is physiologically validated | "XAI has never been combined with SITS stress analysis" (James 2025 does) |
| **G3** | No multi-modal (optical + thermal) SSL pre-training recipe for satellite time series exists | "SSL is unexplored for SITS" (SimCLR/CAE variants exist) |
| **G4** | Concurrent water–salinity has only been monitored **descriptively**; no predictive, per-field DL disentanglement exists at any scale, and none in arid irrigated sugarcane | "Nobody monitors concurrent stress from satellites" |
| **G5** | No public benchmark for stress-type classification (CropHarvest/PASTIS are crop-type only) | — |
| **G6** | XAI explanations in RS are not validated against plant physiology | — |
| **G7** | Raw bands vs. indices is unresolved in the stress-SITS context | — |

---

## 5. Design decisions and their current leans

| Decision | Lean | Reason |
|---|---|---|
| Input | **Raw Landsat bands + LST**; indices as an ablation arm | Rußwurm 2020; Berger 12/96; Waters moisture-index finding |
| SSL pretext | **Barlow Twins**, decided after a Phase-2 pilot | Small 490-field library; no negative-pair engineering |
| Cadence | **Landsat 16-day primary**; fused S2 as a robustness check | Uniform 2013–2025 archive + native TIRS LST; BRDF caveats (Haq 2025) |
| Architecture | CNN-Mamba. **Reimplementation decision pending** (released SITSMamba code diverges) | Linear complexity for a 12-year archive |
| Composition | **Geometry-aware compositing is a protocol must-do** | Haq 2025: viewing geometry "significantly affects" NDVI/PRI/SIF → "erroneous stress interpretation"; Waters 2025 same for sugarcane |
| Agents | **Frozen as future work / optional chapter** | 18/78 papers served an optional component while the claimed novelty had 2–3 |
| Foundation models | Ablation/robustness check only | Advisor decision 2026-09-10 |
| Validation | Leave-one-year-out (cross-year), uncertainty reporting by design | Gracia Rojas 2026 field-wide gap |
| Labels | Soft/mixture labels preferred over hard global classes | Tardieu 2018 |
| Baselines to beat | RF/XGBoost on indices; 3D-CAE à la STS-NET; LSTM/Transformer SITS encoders; **Motlagh test R² = 0.821** | 04-Thesis-Design §6 |

**Four phases, 18 weeks.** Data pipeline (1–4) → SSL pre-training (5–8) → fine-tuning + XAI
(9–14) → writing (15–18).

**XAI plan.** SHAP on Mamba selectivity vectors + temporal Grad-CAM + counterfactual probes,
validated four ways: (a) physiological consistency against the Angon response directions
(gs↓, Na⁺↑, ROS↑, Chl a↓ — **note: Ts, proline and ABA were never measured in Angon**),
(b) faithfulness metrics on temporal attributions (deletion/insertion), (c) an expert review
round, (d) sanity checks per Höhl 2024. Plus the Wen 2023 trait-sequencing hypothesis as a
testable expectation: early-season structural saliency, late-season chlorophyll/water
saliency.

**The Mixed_Stress explanation must show**: gas-exchange/canopy-temperature features at
drought-like magnitude (S+D ≈ D for gs/A/E, ns at p=0.238/0.541/0.576), salt indicators at
salinity-like magnitude (S+D ≈ S for Na⁺/Cl⁻, ns at p=0.801/0.082), and the amplified
biomass drop (shoot DW −14%/−16% below both singles).

**Blocking advisor questions.** ① ECe ground-truth access for the 490 fields. ② Operational
Mixed_Stress criteria (no corpus paper defines them). ③ GPU local (~24 GB) vs. cloud.
④ Timeline approval + the benchmark-release promise (G5).

---

## 6. Threats to validity, with sources

1. **Equifinality of the thermal channel** — Maes 2012, Gerhards 2019, Tardieu 2018, Feller 2014.
2. **Salt tolerance as a spectral mediator** — Smanov 2026 (`papers/46`): the reflectance→EC
   mapping is **crop-dependent**; salinity is under-estimated under tolerant crops and
   over-estimated under sensitive ones. Three ignored variables: ion composition, root-zone
   vs. surface salinity, phenological stage. The review names **no sugarcane, Iran or
   Khuzestan** — so it supports the general argument, not a local one.
3. **Heat-wave confound** — Feller 2014 (opposite stomatal directions), Maes 2012 (weather-
   dependent baselines).
4. **Viewing geometry / BRDF** — Haq 2025 (`papers/72`), Waters 2025 (`papers/77`).
   Haq also reports BRDF anisotropy signatures that differ by stress type (water: forward
   scattering ↑; nutrient: reduced anisotropy; pathogen: asymmetric) → a candidate
   disentanglement feature, not only a nuisance.
5. **SITSMamba released code is unverified and possibly incomplete** — reimplementation decision.
6. **Paciolla's salinity fallback is single-field** — one 21-ha maize field; the paper has no
   LAI→EC regression and produces no salinity map; EC_LOW = 1.7 dS/m is an FAO maize
   parameter, not a fitted threshold. ECe-free labelling is **PARTIAL** support only.
7. **Satellite thermal CWSI for sugarcane caps at R² 0.42–0.78** (Veysi et al., via `papers/78`
   and `papers/73`). Cite the primary, not both reviews.
8. **Heat + drought as a co-stressor in Khuzestan is unquantified** — the physiology is
   species-general; no study measures that system.
9. **Water-table depth 82–116 cm, 128 wells** — the salinity and water-table data come from a
   finite well network; spatial resolution of the kriged surfaces is a label-quality limit.
10. **Single-season local evidence** — Motlagh 2026 and Zoratipour 2025/2026 use 2023 and 2024.
    The thesis's 12-year archive is the fix, and cross-year validation is the proof.

---

## 7. The two strongest original arguments, in the corpus's own words

**Argument 1 — the thermal channel cannot separate the stressors, and the field's own
authors say so.** Maes: CWSI is one-dimensional in g_s, so osmotic and hydraulic closure
coincide. Tardieu: osmotic adjustment holds turgor, so salinity can leave CWSI near normal
while the plant deteriorates. Feller: heat opposes drought at the stomata. Motlagh-Ky: a
local author warns that salinity confounds canopy temperature. **No index pipeline can fix
this. Only a predictive temporal model with a second, non-thermal evidence channel can.**

**Argument 2 — the field has the data, the physics, the local constants and the models, but
never joined them.** Wen measured the joint stress and stopped at ANOVA. Motlagh measured
both axes in the target landscape and stopped at a Random Forest on CWSI and ECe. Haq,
Berger, Paul and Waters each counted the same absences: no salinity synthesis, no multi-domain
fusion, no deep learning, no XAI, no time series. STS-NET did SSL on sugar but with water and
nitrogen, at 3 m, in one season, without thermal and without explanations.
**The gap is not a missing component. It is a missing join.**

**The proposed join.** A Mamba temporal encoder over raw bands + LST, self-supervised on
490 fields across 12 years, fine-tuned on 50–100 expert labels into four classes, explained
at the timestep level, and validated against the physiology in `papers/07`, `papers/39`,
`papers/41` and `papers/40`.

---

## 8. Reusable method assets (do not re-derive these)

- **Preprocessing chain** (`papers/02`): CFMASK cloud mask → cubic-spline 16-day composites →
  STRFM gap-fill (Landsat + MODIS) → raw bands + LST + indices.
- **Date-as-auxiliary-input temporal encoding** (`papers/16`).
- **Phenological alignment by GDD + canopy chlorophyll** (`papers/32`): critical for a
  12–18 month sugarcane cycle.
- **XAI → VI design → retrain loop** (`papers/17`): SHAP/SVS band attribution → design
  indices → retrain (OA 67 → 70).
- **Teacher-student spectral adaptation** (`papers/19`): published spectral–salinity
  relationships as the teacher, a Landsat-scale student.
- **Satellite-only hot/cold-pixel CWSI** (`papers/78`, `papers/75`): no ground ancillary
  data needed; a ground-data-free covariate template.
- **Validation design** (`papers/36`, `papers/37`, `papers/61`): one ground truth, several
  estimation routes, pooled same-date correlation; an independent report subset at three scales.
- **Uncertainty propagation** (`papers/62`): forward Monte Carlo + Nataf; per-input CVs
  (rainfall 30–40%, ET₀ 10–15%, NDVI 20–50%).
- **RF + PSO feature selection** (`papers/38`): a classical-ML pruning baseline (OA +2.7–7.4%).
- **Multi-task heads on a shared representation** (`papers/22`): analogous to the
  water/salinity/mixed head design.
- **REMSA constraint schema** (`papers/59`): the procedure for justifying any FM ablation
  set (>160 RSFMs, 3,000 expert ratings).
- **RS-Agent / BSCTR ordering** (`papers/47`, `papers/52`): a citable argument for causally
  ordering the pipeline (correction → index → classification → XAI) if the agent chapter is
  ever revived.

---

## 9. Open inconsistencies that still need reconciliation

The 2026-10-20 pass wrote the corrections into the vault notes but did not rewrite the
matrix and the lit review. These are **still open**.

**Literature-Matrix.md:**
| Row | Matrix still says | The PDF says |
|---|---|---|
| 43 Wang 2021 | "RF on S2 indices, R² ≈ 0.78" | **SVM is best (verification R² 0.88); RF verification R² 0.27.** The 0.783 is an unattributed Discussion comparison. No salt-vegetation index in the paper. S2A/S2B inconsistency pp.1 vs 4. |
| 68 Ahmad 2021 | "Remote Sens. 13(16):4155" | Issue is **13(20)**. Authorship Ahmad, Alvino & Marino confirmed. |
| 61 Zhang 2026 | "Arizona analog" | Study area is **mainland China**. Arizona is #62. |
| 39 Maes 2012 | (implied salinity claim) | **No salinity statement in the paper.** The equifinality point is a derivation from eq. 41. |
| 42 Gerhards 2019 | "single-index CWSI fails under co-occurring stresses" | A thesis-level inference. The paper's documented CWSI failure is **meteorological**; no salinity content. |
| 40 Feller 2014 | "combined stress ≠ sum of singles" | Mechanistic argument only. No non-additivity test. |
| 63 Sun 2026 | "label-efficient / self-evolving for label-efficient RS detection" | The SSDD evaluation is **fully supervised**; no annotation-budget ablation. |
| 65 Tariq 2025 | — | Internal inconsistency in the paper (88% vs 87%; "every hour" vs "every 5 s"). No field trial, no edge benchmarks. |
| 66 Musazade 2026 | — | No PRISMA, no n, no year window. Satellite is future work only. |
| 67 CottonBot 2025 | — | The field trial is **still planned for 2026**, not performed. |
| 47 RS-Agent | "27 tools / 18 tasks", "Sci China Inf Sci" | The paper is arXiv:2406.07089; "Sci China Inf Sci" is the review venue. ">95%" is backbone-dependent (48.00–98.50%). |
| 50 AgriWorld | — | The PDF reports three different accuracies for the full system (57.6 / 73.84 / 73.8%). AGROBENCH has no named source, no code URL. |
| 49 Talemi 2026 | — | MapBot is intro-only, not in Table 1. |
| — | **Quick Filter section** | Still lists the old reading priorities. All P0 items are closed. |

**lit_review/00_thesis_literature_review.md:**
- §3.4 still says "single-index CWSI fails under co-occurring stresses (Gerhards 2019)" —
  the note at `papers/42` explicitly contradicts this.
- §2 "Reading status" still says all non-P0 notes are extract-level. Outdated since 2026-10-20.

**Thesis_Vault/00-Thesis-Overview.md:**
- Line 59: "Positional Weight (PW) for temporal attention". **PW is a loss re-weighting**
  (corrected in `papers/01`).
- "Vault Structure" still lists papers 01–38 plus 70.

**Thesis_Vault/03-Research-Gaps.md:**
- G3 still lists **SAR** in the contribution ("optical + LST + SAR", "optical + thermal + SAR").
  The design dropped SAR. The Landsat-only design is **optical + thermal**.

---

## 10. Other open items (unchanged from `todo.md`)

1. **Advisor's 4 answers** — these gate §methods and §labels of the proposal. ECe access is
   the most urgent, because without it the salinity labels lean on a single-field proxy.
2. **Zotero**: verify 7 manual items in the client (6, 10, 13, 25, 35, 36, 37); optionally
   import the ~60 legacy link-index papers; **Excel export of the Literature-Matrix** (advisor request).
3. **James 2025 PDF** (IEEE AsianCON) — fetch it for the G2 near-neighbor.
4. **Second Crossref/OpenAlex pass** on "state space model" + "crop stress" before submission.
5. **Proposal export** to Word-ready markdown as sections stabilize.
6. **SITSMamba reimplementation decision** — verify the released repo runs, or reimplement from
   the paper. This is a Phase-2 blocker and it is not yet on the todo list.
7. **`papers/ARCHIVED_Foundation_models/FARM.pdf` is truncated** — re-download if a note is ever wanted.
8. `papers/03-Balestriero-2023-SSL-Cookbook.md` is a placeholder — **no PDF in the repo**.
   Download from arXiv before citing it for any methodological detail.

---

*Logged 2026-10-21. All numbers above were read from the vault notes and the matrix, which
carry page-level provenance for each claim. Repository branch: `main`.*
