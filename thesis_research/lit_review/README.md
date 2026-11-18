# Literature Review — Crop Stress Monitoring in Arid / Semi-Arid Agriculture

**Purpose:** Supporting material for a Master's thesis on operational, multi-year, label-efficient crop stress monitoring in salinity-affected arid / semi-arid irrigated systems.

**Compiled:** September 2026 — by Kilo, an interactive research assistant.

---

## Folder Structure

```
lit_review/
├── README.md                                  ← this file
├── 00_thesis_literature_review.md            ← MAIN deliverable: full 11-section review
├── 00_paper_links.md                          ← 60+ download URLs + New Intake 2026-09-10 (N1–N29) + New Intake 2026-10-04 (N30–N37)
├── phase1_stress_detection_methods.md         ← Detailed Phase-1 review (447 lines, ~140 papers)
└── papers_not_downloaded.md                   ← 98+ citations with links (organized by topic)

Companion (not in lit_review/):
├── papers/39–75*.pdf                          ← local PDFs from the two New_papers intakes (gitignored)
├── papers/INTAKE_LOG_2026-09-10.md            ← file index for 39–67
├── papers/INTAKE_LOG_2026-10-04.md            ← file index for 68–75
├── deep_researches/new_papers_intake_2026-09-10.md  ← synthesis of 29 new papers
├── deep_researches/new_papers_intake_2026-10-04.md  ← synthesis of 9 new papers (Wen trilogy, Haq, Ahmad, …)
└── deep_researches/new_papers_notes/          ← one note per paper (A1–A8, G1–G21, A9–A16)
```

**PDFs are intentionally not committed** — see `00_paper_links.md` for direct URLs.

---

## How to Use These Files

1. **Start with `00_thesis_literature_review.md`** — the executive summary, literature matrix, gap analysis, and 10 ranked thesis ideas.
2. **Read `phase1_stress_detection_methods.md`** if you are doing a deep dive on Phase 1 (stress detection methods, label-free, multi-year).
3. **Open `papers_not_downloaded.md`** and try to fetch the missing papers via your institution's library (most are open-access anyway).
4. **Read the PDFs in `papers/`** as the seed for the literature review. They cover the top 14 most-important papers for the thesis.

---

## Key Conclusions (TL;DR)

1. **Foundation Models for EO are production-ready** (Prithvi-EO-2.0, Clay v1.5, AlphaEarth, TerraMind). They collapse the label requirement from thousands of labels to dozens.
2. **No 2021–2026 paper uses FMs for crop stress anomaly detection in salinity-affected arid fields** — this is the #1 thesis opportunity.
3. **Stress *type* differentiation at satellite scale is essentially unsolved** — only UAV hyperspectral works (and only 2-3 classes).
4. **Active learning for *stress* (not crop type) is a gap** — only Xu et al. 2024 (BSSAL) does it for crop type.
5. **All data and models are free** (HLS, GEE, ERA5, ECOSTRESS, model weights on Hugging Face) — no funding needed.
6. **Recommended thesis:** Prithvi-EO-2.0 reconstruction-error anomaly + AlphaEarth embeddings + active learning + physics-guided multi-label stress differentiation on multi-year HLS archive in arid/semi-arid irrigated fields.

---

## Suggested Citation Style

```bibtex
@article{szwarcman2024prithvi,
  title={Prithvi-EO-2.0: A Versatile Multi-Temporal Foundation Model for Earth Observation Applications},
  author={Szwarcman, Daniela and Roy, Sujit and Fraccaro, Paolo and others},
  journal={arXiv preprint arXiv:2412.02732},
  year={2024}
}
```

(See `papers_not_downloaded.md` for the full citation table for ~150 papers.)

---

## License

This is a working document for academic use. If you reuse it, please cite the original papers (not this synthesis).
