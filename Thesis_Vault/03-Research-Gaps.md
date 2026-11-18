# Research Gaps — Detailed Analysis

**Date:** 2026-09-10  
**Purpose:** Document the specific gaps our thesis addresses, with evidence from literature review.

---

## Confirmed Gaps (Evidence-Based)

### G1: No SSM/Mamba for Stress Classification in SITS
**Evidence:** 
- SITSMamba (Qin et al., 2024) — Mamba for crop type only
- Miller et al. (2024) review — SSMs mentioned as "emerging" but no stress applications
- No 2021–2026 paper applies Mamba to stress differentiation

**Our Contribution:** First CNN-Mamba for multi-class stress classification (Water/Salinity/Mixed)

---

### G2: No Temporal XAI for Remote Sensing
**Evidence:**
- Höhl et al. (2024) — **verified by full read 2026-10-04** (`papers/04-XAI-RS-Review.md`): the repo's "temporal XAI is virtually unexplored" is a **paraphrase, not a verbatim quote**. Actual (p.22): most XAI methods "do not explicitly consider temporal dependencies, making some of them unreliable or inaccurate"; Conclusion (p.24) encourages methods addressing "temporal dependencies in RS data". **Precedent exists** — Höhl cites Rußwurm & Körner measuring temporal importance of DL models for crop classification [158]. So G2 must NOT claim "no temporal XAI in RS at all".
- Evaluation-practice claim is **largely faithful**: >90% of 207 surveyed studies evaluate only anecdotally; 15/207 use functional metrics; no controlled ground truth for explanations in real-world RS.
- James et al. 2025 (IEEE AsianCON) — near-neighbor: contrastive SITS + SHAP/Grad-CAM at feature/region level per month (`deep_researches/search_logs_2026-10-04.md`).

**Our Contribution (precise wording):** first **timestep-level** temporal XAI (SHAP on Mamba selectivity vectors + temporal Grad-CAM) for a deep SITS **stress** model, **validated against plant physiology** — none of the existing precedents (Rußwurm temporal-importance for crop type; James feature-level) does this.

---

### G3: SSL for Multi-Modal SITS is Unexplored
**Evidence:**
- Balestriero et al. (2023): SSL cookbook is domain-agnostic
- EigenCL (2025): Contrastive SSL on S2 NDRE only (single modality)
- **Paul et al. 2025 (full read 2026-10-04, `papers/60`): across 163 DL plant-stress studies (PRISMA, 2014–2024), SSL = 1 subsection / 3 studies, all leaf-canopy proximal — no satellite, no thermal, no multi-temporal SSL; no SSL-algorithm taxonomy; the Conclusion's data-scarcity toolkit omits SSL.** Quantitative citable anchor for this gap as of Dec 2024.
- No recipe for optical + thermal + SAR contrastive learning

**Our Contribution:** Temporal contrastive SSL on multi-modal SITS (optical + LST + SAR). Design note: avoid strong color-jitter augmentation (degrades SSL on stress imagery — Nagasubramanian et al. 2022 via Paul p.18); prefer geometry/seasonal invariances.

---

### G4: Mixed-Stress Class Not Modeled
**Evidence:**
- Angon et al. (2022): Combined stress is interactive, not additive
- Motlagh et al. (2026): Synergistic interaction quantified (disproportionate yield loss)
- **Berger et al. 2022 (full read 2026-10-04, `papers/44`): "no concept exists that uses multiple spectral domains in an integrated way … to differentiate between crop stress types" (p.3); salinity = 5% of their 96 reviewed studies, never synthesized.** Caveat to address in our design chapter: they also warn differentiation "will remain a challenge with purely RS-based approaches" (p.14) — our answer is temporal selectivity from a 2013–2025 dense archive + physiologically validated XAI, not just a new index.
- **Wen trilogy (2021–2023, all full-read 2026-10-04): the closest existing work builds joint-stress *categories* and compares combined vs individual impacts (ANOVA, 1-km cells, proxy labels) — but never *disentangles* the mixed signal within a field, trains a predictive model, or reports accuracy.** Wen 2023 explicitly claims only "a quantitative foundation for simultaneously assessing" stresses (p.9). ⚠️ Do not cite Wen 2021's "has not yet been used to monitor both simultaneously" without this caveat.

**Our Contribution:** Explicit "Mixed_Stress" class with physiological validation — per-field predictive disentanglement (Healthy / Water / Salinity / Mixed) from multi-year SITS with temporal XAI

---

### G5: No Benchmark for Stress-Type Classification
**Evidence:**
- Existing benchmarks: CropHarvest, CropNet, PASTIS (crop type only)
- No public dataset for stress-type multi-label classification
- No standardized evaluation protocol

**Our Contribution:** Release Khuzestan stress classification dataset + benchmark

---

### G6: XAI Explanations Not Validated Physiologically
**Evidence:**
- Höhl et al. (2024): "Evaluation of XAI is weak — most papers don't validate against ground truth"
- Ahmed et al. (2025): Discusses physiological plausibility but for spectroscopy only
- No paper validates RS-XAI against known plant physiology

**Our Contribution:** SHAP outputs validated against Angon et al. (2022) physiological findings

---

### G7: Raw Bands vs. Indices Debate Unresolved
**Evidence:**
- Rußwurm & Körner (2020): Raw bands outperform indices for temporal models
- Most RS papers still use hand-crafted indices (NDVI, EVI, etc.)
- No systematic comparison in stress context

**Our Contribution:** Empirical test of raw bands vs. indices in CNN-Mamba framework

---

## Gaps Already Filled by Existing Papers (Avoid Redundancy)

| Gap | Already Addressed By | Our Different Angle |
|-----|---------------------|---------------------|
| CWSI computation | Zoratipour et al. (2026) | Extend from daily to temporal trajectory |
| LAI retrieval | Hajeb et al. (2023) | Use as proxy, not primary output |
| Ky calibration | Motlagh et al. (2026b) | Apply to deep learning framework |
| Yield baseline | Motlagh et al. (2026) | Exceed R²=0.93 with neural architecture |
| Soil salinity mapping | Multiple papers | Focus on temporal dynamics, not static maps |

---

## Novelty Scorecard

| Criterion | Score (1–10) | Justification |
|-----------|-------------|---------------|
| **Architecture novelty** | 9 | First CNN-Mamba for stress (not crop type) |
| **Method novelty** | 9 | Temporal XAI for SITS is unexplored |
| **Dataset novelty** | 8 | First multi-year stress-type dataset for arid irrigated systems |
| **Validation novelty** | 8 | Physiological validation of XAI outputs |
| **Practical impact** | 9 | Actionable for farm managers in Khuzestan |
| **Publication potential** | 9 | Q1 journals (RSE, ISPRS, TGRS) |

**Overall novelty: 8.7/10**

---

*Last updated: 2026-10-04 (negative-search evidence: `deep_researches/search_logs_2026-10-04.md`; Paciolla full-read correction noted under G4 label design — ECe-free labeling is only PARTIALLY supported: single-field study, see `papers/08-Salinity-LAI.md`)*
