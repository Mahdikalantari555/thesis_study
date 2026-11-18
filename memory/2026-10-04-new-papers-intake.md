# New Papers Intake — 2026-10-04 (9 PDFs, concurrent stress / crop water stress)

**Source:** `D:\RS\Thesis\New_papers\` (flat folder)
**Outcome:** 8 papers filed as `papers/68`–`75`; 1 duplicate detected (Berger 2022 = #44).

## What arrived
1. **Wen et al. trilogy (Leiden Univ.)** — the big find of this batch:
   - Wen 2021, *RS* 13:6 — meta-review: VIs insufficient (R² 0.02–0.80); traits better; **joint drought+salinity signals spectrally overlap** → remote separation "significantly limited".
   - Wen 2022, *HESS* 26:4537 — Sentinel-2 five traits (LAI, FAPAR, FVC, Cab, Cw), maize+potato, NL, 138.74 km²; ANOVA R² 0.326–0.796; drought > salinity sensitivity; combined effects stage-dependent.
   - Wen 2023, *IJAEOG* 122:103438 — multi-crop US; combined sensitivity > individual; strong time dependence.
2. **Haq et al. 2025** (Smart Agric. Technol. 12:101583) — 138-study review; adds angular/BRDF dimension to Berger 2022; physics-aware AI agenda. Resolves previously PII-only reference in phase1.
3. **Ahmad et al. 2021** (RS 13:4155) — canonical CWSI/water-stress sensor taxonomy review.
4. **Gokul et al. 2026** (Plant Sci. Today) — UAV CWS review; RF maize R²>0.575; XGBoost cotton CWSI R²=0.90.
5. **Gracia Rojas et al. 2026** (RSASE 44:102279) — SLR n=105; CNN→mapping, LSTM/Transformer→time series; classical ML competitive; validation/uncertainty gaps.
6. **Olawoyin et al. 2026** (H2Open 9:100024) — Volta Basin 2000–2023; LST–NDVI triangular CWSI; r(ET,NDVI)≈0.96.
7. **Berger 2022 duplicate** — received again; kept single copy (#44/A6).

## Decisions & implications
- **Positioning sharpened (important):** the claim "nobody maps concurrent drought+salinity from satellites" is now **false** — Wen et al. did (descriptively, via traits + ANOVA). The thesis claim must be: "nobody **disentangles** concurrent water–salinity stress with deep temporal models (Mamba) + SSL + XAI at field scale in an arid irrigated system." Wen trilogy = mandatory related-work anchor; cite as precedent, then differentiate (no DL, no per-pixel type disentanglement, no arid sugarcane).
- **Citation fixed:** RS 13:4155 was attributed to "Grill, J., et al." in `00_paper_links.md` #45 and `papers_not_downloaded.md` #50 — actual authors **Ahmad, Alvino & Marino**. Corrected in both files.
- Phase-1 PII `S2772375525008147` resolved → Haq et al. 2025, downloaded as `papers/72`.
- G3 gap justification in `00_thesis_literature_review.md` updated to acknowledge the trilogy.

## Files touched
- `papers/68`–`75` + `papers/INTAKE_LOG_2026-10-04.md` (local)
- `deep_researches/new_papers_intake_2026-10-04.md` (synthesis)
- `deep_researches/new_papers_notes/A9`–`A16` (8 notes)
- `deep_researches/new_papers_2026-10-04_extract/` (9 extracts incl. duplicate)
- `lit_review/00_paper_links.md`, `papers_not_downloaded.md`, `00_thesis_literature_review.md`, `phase1_stress_detection_methods.md`, `README.md`

## Open follow-ups
- [ ] Read Wen 2022 HESS Methods before designing the Khuzestan trait-retrieval pipeline (which RTM produced the five traits matters).
- [ ] Decide the exact positioning sentence vs. Wen trilogy in the proposal.
- [ ] Fold Haq 2025 BRDF caveat into HLS compositing protocol.

---
*Logged 2026-10-04.*
