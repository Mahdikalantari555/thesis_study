# Memory Log — 2026-09-10: Advisor Feedback & Paper Analysis

## Advisor's Message (Translated from Persian)

The advisor confirmed that the original **attribution** framework is scientifically invalid. The redesigned direction is:

> **"Disentanglement and explainability of concurrent stresses using Mamba and SSL"**

This requires mastery of current literature to avoid conceptual重复 errors.

## 8 Mandatory Papers Identified

| # | Paper | Year | Status |
|---|-------|------|--------|
| 1 | SITSMamba for Crop Classification (Qin et al.) | 2024 | ✅ Full abstract retrieved |
| 2 | Deep Learning for SITS Analysis: Review (Miller et al.) | 2024 | ✅ Full abstract retrieved |
| 3 | A Cookbook of Self-Supervised Learning (Balestriero et al.) | 2023 | ✅ Full abstract retrieved |
| 4 | Opening the Black-Box: XAI in RS (Höhl et al.) | 2024 | ✅ Full abstract retrieved |
| 5 | Self-attention for raw optical SITS (Rußwurm & Körner) | 2020 | ✅ Full citation + key findings |
| 6 | Systematic review of XAI for agriculture (Ahmed et al.) | 2025 | ⚠️ DOI unresolved — needs manual lookup |
| 7 | How Do Plants Respond to Combined Drought and Salinity Stress (Angon et al.) | 2022 | ✅ DOI: 10.3390/plants11212884 (OA) |
| 8 | Salinity stress and water availability from satellite LAI (Paciolla et al.) | 2025 | ✅ DOI: 10.1007/s11119-025-10279-5 |

## Key Decisions from Analysis

### 1. Architecture: CNN-Mamba Hybrid (Confirmed)
- SITSMamba provides the blueprint: CNN spatial encoder → Mamba temporal encoder
- Positional Weight mechanism is critical for identifying stress-onset timing
- Must add thermal band (LST) to CNN input — SITSMamba only uses optical
- Reconstruction branch should predict stress-relevant indices (NDWI, CWSI anomalies), not raw bands

### 2. SSL Strategy: Temporal Contrastive Learning (New)
- Best pretext task: same-field, different-years positive pairs (captures phenology)
- Barlow Twins loss recommended (proven annotation-efficient in soybean stress study)
- Must extend to multi-modal (optical + thermal + SAR) — no existing recipe

### 3. XAI Contribution: Temporal XAI for SITS (Novel Gap)
- Höhl et al. confirm: most RS-XAI is spatial (2D saliency maps)
- **Temporal XAI is virtually unexplored in RS literature** — this is our contribution
- Apply SHAP to Mamba selectivity vectors + temporal Grad-CAM
- Validate explanations against known plant physiology (Angon et al.)

### 4. Stress Classes: Must Include "Mixed Stress" (Non-negotiable)
- Angon et al. proves combined stress is interactive, not additive
- Model output: `[Healthy, Water_Only, Salinity_Only, Mixed_Stress]`
- Mixed class has distinct spectral signature — cannot be inferred from pure classes
- Ground-truth labeling must include mixed-stress criteria

### 5. Validation: LAI-Based Indirect Validation (from Paciolla et al.)
- Don't need ECe for all 490 fields — use LAI as intermediate proxy
- Paciolla shows LAI reduction captures salinity effects without direct soil measurements
- ECLOW threshold = 1.7 dS/m (from their work) — use as validation benchmark

## Files Created

1. `thesis_research/deep_researches/advisor_papers_analysis.md` — Full paper-by-paper analysis with gap matrix and implementation plan
2. `thesis_research/deep_researches/advisor_papers_full_metadata.md` — Complete metadata for all 8 papers with citations, DOIs, abstracts
3. `thesis_research/scripts/fetch_advisor_papers.py` — Metadata fetch script (for reference)
4. This memory log

## Outstanding Items

- [ ] Get full text of Paper 6 (Ahmed et al. 2025) — need DOI from journal website
- [ ] Download full PDFs for Papers 5, 7, 8 for detailed methodology extraction
- [ ] Clone SITSMamba GitHub repo and review code
- [ ] Begin cloud masking + temporal resampling pipeline for Landsat 2013-2025
- [ ] Contact Shahid Beheshti University / Amirkabir Agro-Industrial for expert labeling collaboration

## Next Deliverable

**Literature Matrix Excel file** — one row per paper, columns for: research gap addressed, methodological contribution, limitations for our use case, applicable techniques.

---
*Last updated: 2026-09-10*
