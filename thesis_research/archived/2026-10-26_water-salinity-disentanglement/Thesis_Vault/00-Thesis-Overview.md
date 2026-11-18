# Thesis Overview — Disentangling Concurrent Water-Salinity Stress

**Project:** MSc Thesis in Remote Sensing / GeoAI  
**Topic:** *A Self-Supervised and Explainable Deep Learning Framework for Disentangling Concurrent Water and Salinity Stress from Multi-Temporal Satellite Imagery*  
**Study Area:** Amirkabir Agro-Industrial Unit, Khuzestan, Iran (~490 sugarcane fields, 2013–2025)  
**Status:** Design consolidated — methodology now maintained in `04-Thesis-Design.md`; deep reads in progress (2026-10-04)  
**Last Updated:** 2026-10-04

---

## 🎯 Research Question

> Given a multi-temporal remote sensing time series, can we develop a model that not only detects the presence of stress but also identifies the most likely contributing environmental drivers (water deficit vs. salinity vs. mixed), with explanations that are physiologically interpretable?

---

## 🔄 From Attribution to Disentanglement

### Original Proposal (REJECTED by Advisor)
- **Goal:** Definitive causal attribution of water vs. salinity stress from observational time series
- **Problem:** Scientifically untenable — hidden confounders, spectral overlap, no ground-truth labels, interactive stress effects
- **Verdict:** Would face immediate rejection from Q1 journals

### Redesigned Proposal (CURRENT)
- **Goal:** Disentanglement + explainability of concurrent stressors
- **Shift:** From "what caused this stress?" → "what are the probable drivers, and how confident are we?"
- **Output:** Diagnostic report with feature importance rankings, not causal claims

---

## 🧠 Proposed Methodology

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA INGESTION LAYER                         │
│  Landsat 8/9 L2 (2013–2025, ~12 years)                          │
│  + Sentinel-2 (for LAI fusion)                                  │
│  + ERA5-Land (climate: T, ET0, VPD, precipitation)              │
│  + SoilGrids (sand/silt/clay, EC proxies)                       │
│  + 490 field polygons (Amirkabir Agro-Industrial)               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 PHASE 1: PREPROCESSING                          │
│  1.1 Cloud masking (CFMASK / GEE)                               │
│  1.2 Temporal resampling to 16-day composites (cubic spline)    │
│  1.3 LST bias correction (RF, following Motlagh et al. 2026)   │
│  1.4 Feature stacking: Raw bands (B2–B11) + LST + indices       │
│  1.5 Field-level aggregation (zonal stats over 490 polygons)    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 2: SSL PRE-TRAINING                          │
│  Architecture: Hybrid CNN-Mamba (following SITSMamba)           │
│  ├─ CNN backbone (ResNet-18 style) per timestep                 │
│  ├─ Mamba temporal encoder (selective state space)              │
│  ├─ Positional Weight (PW) for temporal attention               │
│                                                                 │
│  Pretext task: Temporal contrastive learning                    │
│  ├─ Positive pair: Same field, different years (same season)    │
│  ├─ Negative pair: Different fields, same season                │
│  └─ Loss: Barlow Twins (annotation-efficient)                   │
│                                                                 │
│  Input: ~88 timesteps × [bands + LST] per field                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 3: FINE-TUNING + CLASSIFICATION              │
│  Labels: Expert-labeled subset (50–100 fields)                  │
│  Classes: [Healthy, Water_Only, Salinity_Only, Mixed_Stress]    │
│                                                                 │
│  Fine-tune entire CNN-Mamba end-to-end                          │
│  Add multi-label classification head                            │
│  Validate against:                                              │
│  ├─ CWSI thresholds (Zoratipour et al. 2026)                   │
│  ├─ Soil ECe (Motlagh et al. 2026)                             │
│  └─ Yield records (Motlagh et al. 2026, R²=0.93 baseline)      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 4: XAI + INTERPRETATION                      │
│  SHAP on Mamba selectivity vectors → which timesteps drive?     │
│  Temporal Grad-CAM → spatio-temporal attention maps             │
│  Counterfactual generation → "what if healthy?"                 │
│                                                                 │
│  Validation of explanations:                                    │
│  ├─ Compare against known physiology (Angon et al. 2022)        │
│  ├─ Expert review (Shahid Beheshti Univ.)                       │
│  └─ Physiological plausibility scoring                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Key Numbers from Literature

| Metric | Value | Source |
|--------|-------|--------|
| Current yield prediction R² (RF baseline) | 0.93 full-sample; **0.821 independent test** | Motlagh et al. 2026 (verified full read 2026-10-04) |
| CWSI threshold for irrigation | 0.4–0.5 (Zoratipour 2026); Motlagh's own: young 0.40–0.45, old 0.30–0.35 | Zoratipour et al. 2026; Motlagh et al. 2026 (both verified full read) |
| Local Ky for sugarcane | 1.05 (FAO default: 1.2) | Motlagh et al. 2026b |
| Peak stress sensitivity period | Early July (Ky > 1.82) | Motlagh et al. 2026b |
| Soil salinity range in study area | 1.7–8.0 dS/m (weekly saturated-paste ECe, 0–90 cm, 128 wells, kriged) | Motlagh et al. 2026 (verified full read) |
| LAI retrieval RMSE (S2) | 0.48 m²/m² | Hajeb et al. 2023 |
| Fields available | ~490 | Amirkabir Agro-Industrial |
| Labels needed (with SSL) | 50–100 fields | Best practice in RS |
| Archive span | 2013–2025 (12 years) | Landsat 7/8/9 |

---

## 🔬 Research Gaps Filled by This Thesis

| Gap | Severity | How Thesis Addresses It |
|-----|----------|------------------------|
| No SSM/Mamba for stress (vs. crop type) in SITS | High | CNN-Mamba applied to stress classification |
| No temporal XAI for remote sensing | Very High | SHAP on Mamba selectivity + temporal Grad-CAM |
| SSL for multi-modal SITS unexplored | High | Contrastive SSL on optical+thermal SITS |
| Mixed-stress class not modeled | Critical | Explicit "Mixed_Stress" class (Angon et al.) |
| Raw bands vs. indices debate | Medium | Test both empirically |
| XAI not validated physiologically | High | SHAP outputs validated against plant physiology |
| No benchmark for stress-type classification | High | Release Khuzestan stress dataset |

---

## 📁 Vault Structure

```
Thesis_Vault/
├── Literature-Matrix.md          ← Living matrix (UPDATE THIS; rows 01–78 as of 2026-10-04)
├── 00-Thesis-Overview.md         ← This file
├── 03-Research-Gaps.md           ← Detailed gap analysis (G1–G7)
├── 04-Thesis-Design.md           ← Methodology + implementation plan + agentic decision
├── papers/                       ← Individual paper summaries (linked from matrix)
│   ├── 01-SITSMamba.md … 38-Akbari-2020-RF-PSO.md
│   ├── 70-Wen-2022-HESS.md       ← first verified full-read note (2026-10-04)
│   └── … (new intake papers: see deep_researches/new_papers_notes/ A1–A16, G1–G21)
└── memory/                       ← dated research logs
    └── 2026-09-10-thesis-redesign-complete.md
```

**Pointers to companion analyses outside the vault** (referenced here by earlier versions as vault files — corrected 2026-10-04):

| Content | Actual location |
|---|---|
| 8 advisor-mandatory-papers deep analysis | `deep_researches/advisor_papers_analysis.md` |
| 5 Khuzestan sugarcane papers summary | `deep_researches/khuzestan_sugarcane_papers_summary.md` |
| Advisor feedback log | `memory/2026-09-10-advisor-feedback-paper-analysis.md` |
| Khuzestan papers log | `memory/2026-09-10-khuzestan-sugarcane-papers-summary.md` |
| Foundation-model PDFs (Prithvi, SatMAE, Clay, …) | `papers/archived_foundation_models/` + `papers/ARCHIVAL_LOG.md` (archived 2026-09-14 — FM-era material kept only as ablation/background) |
| 39–78 intake syntheses | `deep_researches/new_papers_intake_2026-09-10.md` / `_2026-10-04.md` |

---

## 🚀 Next Steps (Implementation Roadmap)

| Phase | Timeline | Tasks |
|-------|----------|-------|
| **Phase 1: Data Pipeline** | Weeks 1–4 | Cloud masking, temporal resampling, feature stacking, field aggregation |
| **Phase 2: SSL Pre-training** | Weeks 5–8 | Implement CNN-Mamba, temporal contrastive loss, pre-train on 490 fields |
| **Phase 3: Fine-tuning + XAI** | Weeks 9–14 | Expert labeling (50–100 fields), fine-tune, SHAP + Grad-CAM |
| **Phase 4: Writing** | Weeks 15–18 | Draft methods/results, prepare manuscript for RSE/ISPRS |

---

## 🏆 Target Journals

1. **Primary:** *Remote Sensing of Environment* (Q1, ~12 IF)
2. **Secondary:** *ISPRS Journal of Photogrammetry and Remote Sensing* (Q1, ~10 IF)
3. **Alternative:** *IEEE Transactions on Geoscience and Remote Sensing* (Q1, ~8 IF)
4. **Application-focused:** *Computers and Electronics in Agriculture* (Q1, ~7.5 IF)

---

*This document is the central navigation for the thesis research project. Update it as the project evolves.*
