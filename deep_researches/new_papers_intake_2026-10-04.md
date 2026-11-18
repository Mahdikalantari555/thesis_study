# New Papers Intake — 9 PDFs from `D:\RS\Thesis\New_papers` (flat folder)

**Date:** 2026-10-04
**Task:** Read all papers in `New_papers/`, summarize each, name/copy into `papers/`, and integrate into the lit review.

**Thesis frame:** *Disentanglement and explainability of concurrent water–salinity stress using Mamba + SSL (+ temporal XAI) on multi-year Landsat/HLS in salinity-affected sugarcane (Khuzestan, Iran), with optional GeoAI agent orchestration.*

**Source PDFs:** local only (not committed).
**Extracts:** `deep_researches/new_papers_2026-10-04_extract/` (first ~4 pages per PDF).
**Per-paper notes:** `deep_researches/new_papers_notes/` A9–A16.
**Scope note:** Summaries are based on first-page/abstract extracts; fields beyond the extract window are marked unknown. No invented citations.

---

## 1. Executive summary

This intake covers **9 papers**, all agricultural / stress-RS focused (no agentic papers this time). One is a **duplicate** of an already-indexed paper.

### Headline conclusions

1. **The Wen Wen trilogy (2021 → 2022 → 2023) is the closest existing research program to the thesis core.** RS 13:6 (review, meta-analysis) → HESS 26:4537 (Sentinel-2 five-trait validation, Netherlands) → IJAEOG 122:103438 (multi-crop upscaling, USA). Together they establish: (a) VIs are insufficient (R² 0.02–0.80) for drought/salinity characterization; (b) plant functional traits are the better monitoring target; (c) combined drought+salinity sensitivity exceeds either stress alone; (d) impacts are strongly phenology-dependent; (e) joint-stress spectral overlap is the central obstacle to separating the two stresses. **All three are statistical (ANOVA/meta-analysis) — no deep learning, no SSL, no disentanglement network — so the thesis methodological niche remains fully open.**
2. **Concurrent-stress papers now exist at satellite scale — cite them, don't claim their absence.** The thesis novelty claim must be sharpened: the gap is not "nobody maps concurrent drought+salinity from satellites" (Wen et al. did, descriptively) but "nobody *disentangles* concurrent water–salinity stress with deep temporal models + XAI at field scale." Update related-work framing accordingly.
3. **Haq et al. 2025 adds the angular/BRDF dimension** to Berger 2022's spectral synthesis: viewing geometry biases NDVI/PRI/SIF stress signals; multi-angle information is invisible to nadir-only archives. Relevant as an unmodeled confounder for HLS compositing, and as support for physics-aware AI framing.
4. **Water-stress ML benchmarks (UAV scale) are strong but fragmented:** Gokul et al. 2026 — RF R² > 0.575 (maize, stage-specific), XGBoost CWSI R² = 0.90 (cotton). Classical ML on engineered indices still dominates; representation learning absent.
5. **Gracia Rojas et al. 2026 (SLR, n = 105)** independently confirms: sequence models (LSTM/Transformer) are the accepted family for RS stress/yield time series, classical ML remains a competitive baseline, and the field lacks standardized validation + uncertainty reporting — a differentiator the thesis can adopt by design.
6. **Olawoyin et al. 2026** demonstrates a 24-year, in-situ-free CWSI workflow (LST–NDVI triangle) with strong ET–NDVI–rainfall correlations — a template for auxiliary water-stress covariates where ground data is sparse (Khuzestan-relevant).
7. **Ahmad et al. 2021 (RS 13:4155)** is the canonical single-stress water-stress sensor-taxonomy review. **Citation correction:** the repo previously attributed it to "Grill, J., et al." — actual authors are Ahmad, Alvino & Marino. Fixed in `00_paper_links.md` and `papers_not_downloaded.md`.
8. **No paper in this set** applies Mamba/SSL/foundation models or temporal XAI to concurrent water–salinity disentanglement in sugarcane. The core thesis niche is intact — but the related-work section must now be anchored on the Wen trilogy.

### One-line ranked "must-cite" shortlist (this folder)

| Rank | Paper | Why |
|------|-------|-----|
| 1 | Wen et al. 2021 (RS 13:6) | Gap-analysis review for concurrent drought+salinity RS — the thesis problem statement |
| 2 | Wen et al. 2022 (HESS) | Closest empirical design: five traits, combined-stress ANOVA, Sentinel-2 |
| 3 | Wen et al. 2023 (IJAEOG) | Multi-crop upscaling; combined > individual stress sensitivity; timing dependence |
| 4 | Haq et al. 2025 (SAT) | Spectral × angular × spatial synthesis; BRDF confounder; physics-aware AI |
| 5 | Ahmad et al. 2021 (RS 13:4155) | Canonical water-stress sensor taxonomy (authorship corrected) |
| 6 | Gracia Rojas et al. 2026 (RSASE) | SLR: sequence models for stress time series; reporting gaps |
| 7 | Gokul et al. 2026 (PST) | UAV CWSI/CEWT ML benchmarks; DSS integration gaps |
| 8 | Olawoyin et al. 2026 (H2Open) | 24-yr in-situ-free CWSI template (LST–NDVI triangle) |
| — | Berger et al. 2022 (RSE 280:113198) | **DUPLICATE** of repo paper #44 (A6) — do not double-count |

---

## 2. Inventory (file → paper)

| # | Original file (`New_papers/`) | Paper (short) | Year | Venue | Local PDF (`papers/`) | Note |
|---|------------------------------|---------------|------|-------|----------------------|------|
| A9 | `remotesensing-13-04155-v2.pdf` | Ahmad, Alvino & Marino — crop water stress assessment review | 2021 | *Remote Sensing* 13:4155 | `68-Ahmad-2021-CropWaterStress-Review.pdf` | `A9-Ahmad-2021-CWSI-assessment-review.md` |
| A10 | `remotesensing-13-00006-v2.pdf` | Wen et al. — salinity & drought RS challenges (meta-review) | 2021 | *Remote Sensing* 13:6 | `69-Wen-2021-Salinity-Drought-RS-Challenges.pdf` | `A10-Wen-2021-salinity-drought-RS-challenges.md` |
| A11 | `hess-26-4537-2022.pdf` | Wen et al. — combined drought+salinity monitoring, Netherlands | 2022 | *HESS* 26:4537 | `70-Wen-2022-Drought-Salinity-Combined-NL.pdf` | `A11-Wen-2022-drought-salinity-NL.md` |
| A12 | `1-s2.0-S1569843223002625-main.pdf` | Wen et al. — crop-specific salinity+drought responses, USA | 2023 | *IJAEOG* 122:103438 | `71-Wen-2023-Crop-Salinity-Drought-US.pdf` | `A12-Wen-2023-crop-salinity-drought-US.md` |
| A13 | `1-s2.0-S2772375525008147-main.pdf` | Haq et al. — multi-dimensional optical RS (spectral/angular/spatial) | 2025 | *Smart Agric. Technol.* 12:101583 | `72-Haq-2025-MultiDim-Optical-Stress.pdf` | `A13-Haq-2025-multidim-optical-stress.md` |
| A14 | `PST-ePrint-13057-article.pdf` | Gokul et al. — UAV crop water stress review | 2026 | *Plant Sci. Today* 13(sp2) | `73-Gokul-2026-UAV-CropWaterStress-Review.pdf` | `A14-Gokul-2026-UAV-crop-water-stress.md` |
| A15 | `1-s2.0-S235293852600412X-main.pdf` | Gracia Rojas et al. — ML/DL agri+forestry SLR 2020–2025 | 2026 | *RSASE* 44:102279 | `74-GraciaRojas-2026-ML-DL-AgriForestry-SLR.pdf` | `A15-GraciaRojas-2026-ML-DL-agri-forestry-SLR.md` |
| A16 | `1-s2.0-S2616651826001703-main.pdf` | Olawoyin et al. — Volta Basin ET & CWSI 2000–2023 | 2026 | *H2Open J.* 9:100024 | `75-Olawoyin-2026-Volta-ET-CWSI.pdf` | `A16-Olawoyin-2026-Volta-ET-CWSI.md` |
| — | `Multi-sensor spectral synergies for crop stress detection and monitoring.pdf` | Berger et al. — multi-sensor optical stress synergies | 2022 | *RSE* 280:113198 | **DUP of `44-Berger-2022-optical-stress-synergies.pdf`** — not re-copied | existing `A6-Berger-2022-optical-stress-synergies.md` |

---

## 3. Synthesis — what this pile changes for the thesis

### 3.1 The concurrent-stress state of the art, sharpened

```
Wen 2021 (review)      → VIs fail (R² 0.02–0.80); traits better; combined-stress
                         signals overlap spectrally → separation "significantly limited"
        │
Wen 2022 (HESS)        → five Sentinel-2 traits (LAI, FAPAR, FVC, Cab, Cw);
                         two-way ANOVA; combined effects exacerbated, stage-dependent;
                         drought sensitivity > salinity
        │
Wen 2023 (IJAEOG)      → multi-crop US upscaling; combined > individual sensitivity;
                         strong time dependence; tolerance is crop-specific
        │
        ▼
Thesis opportunity     → replace descriptive ANOVA attribution with learned,
                         temporally-aware disentanglement (Mamba + SSL + temporal XAI)
                         at field scale in an arid irrigated system (sugarcane, Khuzestan)
```

**Positioning rule for the proposal:** cite Wen 2021/2022/2023 as *the* precedent for satellite concurrent-stress trait monitoring, then state the three things they do not do: (1) predictive deep models (only ANOVA/meta-analysis), (2) per-pixel stress-type disentanglement (only joint class effects), (3) arid irrigated sugarcane (temperate NL / US crop mix).

### 3.2 Methodological imports

| Idea | Source | Thesis use |
|------|--------|------------|
| Multi-trait labels (LAI, FAPAR, FVC, Cab, Cw) instead of VI classes | Wen 2022 | Feature set / multi-task targets for disentanglement heads |
| Phenology-dependence of stress impacts | Wen 2022/2023, Gokul 2026 | Growth-stage conditioning in the temporal model; stratified validation |
| Combined > individual sensitivity | Wen 2023 | Motivation paragraph for mixed-stress labels |
| Spectral overlap of joint stress | Wen 2021 | The core problem statement |
| BRDF/viewing-geometry confounder | Haq 2025 | Compositing protocol; threats-to-validity; possible angular covariate |
| Physics-aware AI framing | Haq 2025 | Justifies coupling sequence model with stress-physiology priors |
| LST–NDVI triangular CWSI, in-situ-free | Olawoyin 2026 | Auxiliary water-stress covariate/validator for Khuzestan |
| LSTM/Transformer = accepted time-series family; validation/uncertainty gaps | Gracia Rojas 2026 | Related-work taxonomy; thesis differentiators (cross-year validation, uncertainty) |
| UAV CWSI/CEWT benchmarks (RF/XGBoost) | Gokul 2026 | Proximal validation anchors; baseline comparators |

### 3.3 What does **not** change

- The core novelty claim survives: no Mamba/SSL/temporal-XAI concurrent water–salinity disentanglement on multi-year HLS in sugarcane.
- Do not re-index Berger 2022 (duplicate of #44 / A6).
- Gokul (UAV) and Olawoyin (MODIS basin) remain supporting citations, not core methods.
- The agentic stack (2026-09-10 intake) is unaffected; this intake adds zero agentic papers.

### 3.4 Gaps still open after this pile

- No deep-learning disentanglement of water × salinity at any scale (Wen trilogy is statistical).
- No sugarcane concurrent-stress study (maize, potato, US crop mix, cotton, basin-scale mixed vegetation).
- No foundation-model / SSL approach to trait-based concurrent-stress monitoring.
- Field-scale (< 30 m effective) concurrent-stress mapping unattempted; Olawoyin is 250–1000 m, Wen 2022 is parcel-level statistics only.

---

## 4. Recommended insertion into existing repo files (done in this pass)

| File | Action |
|------|--------|
| `papers/` | PDFs copied as `68`–`75` (local only, gitignored) |
| `papers/INTAKE_LOG_2026-10-04.md` | New intake log |
| `lit_review/00_paper_links.md` | New section "New Intake 2026-10-04" (N30–N37); **fix #45 author Grill → Ahmad** |
| `lit_review/papers_not_downloaded.md` | **Fix #50 author Grill → Ahmad**; mark as now-downloaded |
| `lit_review/00_thesis_literature_review.md` | Intake note line + fold Wen trilogy / Haq / Ahmad into §6 Stress Differentiation |
| `lit_review/phase1_stress_detection_methods.md` | Resolve PII S2772375525008147 → Haq et al. 2025 with local filename; add Wen trio to salinity/concurrent-stress thread |
| `lit_review/README.md` | Counts and companion-file pointers |
| `memory/2026-10-04-new-papers-intake.md` | Memory log |

---

## 5. Methods of this intake

1. Enumerated 9 PDFs in `D:\RS\Thesis\New_papers\` (flat folder, no subfolders this time).
2. Extracted first ~4 pages per PDF with `pdftotext -layout` → `deep_researches/new_papers_2026-10-04_extract/`.
3. Identified duplicates against `papers/` and `lit_review/` indexes (Berger 2022 DUP of #44; Ahmad 2021 already indexed under wrong author; Haq 2025 PII resolved).
4. Wrote per-paper notes A9–A16 and this synthesis.
5. Updated lit-review indexes and main review; logged to `memory/`.

**Limitations**

- Summaries rely on first-page/abstract extracts; quantitative fields beyond page 4 are unknown.
- Page-number-level results (full tables) not verified — re-check before formal citation in the proposal.

---

## 6. Outstanding follow-ups

- [x] Read the Wen 2022 HESS full text (Methods §2–3) before designing the Khuzestan trait-retrieval pipeline — the RTM used for the five traits matters. → **done 2026-10-04**: PROSAIL via SNAP biophysical processor; note `Thesis_Vault/papers/70-Wen-2022-HESS.md`
- [x] Decide the thesis positioning sentence re: Wen trilogy (descriptive concurrent-stress monitoring) vs thesis (predictive disentanglement). → **done**: `Thesis_Vault/04-Thesis-Design.md` §1
- [x] Fold Haq 2025 BRDF caveat into the HLS compositing protocol notes. → **done**: recorded as a design decision (`04-Thesis-Design.md` §5 cadence row); fold into the compositing script docs when Phase-1 code exists
- [ ] Re-check Ahmad 2021 sensor taxonomy when writing the water-stress chapter (correct authorship in all downstream documents).
- [x] Keep Berger only once in the knowledge base (#44 / A6).

---

*Last updated: 2026-10-04*
*Companion notes: `deep_researches/new_papers_notes/` (A9–A16)*
*Extracts: `deep_researches/new_papers_2026-10-04_extract/`*
