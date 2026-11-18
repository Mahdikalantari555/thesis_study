# Paper Archival Log — 2026-09-10

**Decision:** Move foundation model PDFs to archive based on advisor's redesigned thesis direction (CNN-Mamba + SSL + XAI for stress disentanglement).

## Archived (Moved to `papers/archived_foundation_models/`)

| File | Size | Reason for Archival |
|------|------|---------------------|
| AlphaEarth.pdf | 25.4 MB | FM embeddings — thesis now uses CNN-Mamba, not pre-computed embeddings |
| Clay-v1.5.pdf | 2.8 MB | FM pre-training — not the architecture choice |
| Prithvi-1.0.pdf | 8.6 MB | FM backbone — superseded by Mamba approach |
| Prithvi-EO-2.0.pdf | 16.8 MB | FM backbone — noted as reference only, not implementation target |
| SatMAE.pdf | 13.9 MB | Older FM — outperformed by Mamba for long sequences |
| TerraMind.pdf | 44.5 MB | Multimodal FM — too heavy, not aligned with thesis scope |
| FARM.pdf | 2.0 MB | Prithvi fine-tune for yield — adjacent but not core |

**Total archived:** ~114 MB of PDFs

## Remaining Papers (Active)

These are kept in `papers/` as directly relevant to the redesigned thesis:

| File | Relevance |
|------|-----------|
| Assessing-CWSI-as-an-indicator-of-water-stress-in-oak...pdf | CWSI validation for water stress indicator |
| Assessment-of-different-remote-sensing-techn_2025...pdf | Method comparison for stress detection |
| Comparative-analysis-of-evapotranspiration--ET---crop-water-stre...pdf | ET/CWSI relationship for water stress |
| Comparison-between-TVDI-and-CWSI-for-drought-monit...pdf | TVDI vs CWSI for drought — direct methodology reference |
| Deriving hourly and daily crop water stress index...pdf | CWSI computation at multiple temporal scales |
| Crop Mapping Using Random Forest...pdf | Baseline classifier for comparison |
| Derivation-of-crop-yield-response-factor--Ky...pdf | Agricultural context for stress-yield relationship |
| Enhancing water productivity in sugarcane...pdf | Arid-region irrigation context (similar to Khuzestan) |
| Leveraging remote sensing data and machine learning...pdf | ML methods for stress assessment |
| Simultaneous retrieval of sugarcane variables...pdf | Multi-variable stress retrieval from S2 |

## Future Reference

Foundation model papers are still cited in `lit_review/00_thesis_literature_review.md` and `advisor_papers_analysis.md` as background/context, but they are no longer the primary architectural choice. If needed for ablation or baseline comparison, they can be restored from `archived_foundation_models/`.

## Later same day — New_papers intake

29 additional PDFs from `D:\RS\Thesis\New_papers\` were copied in as `39`–`67`. See **`INTAKE_LOG_2026-09-10.md`** for the full index. These are active literature for concurrent-stress disentanglement + optional GeoAI agent layer (not foundation-model archive).

---
*Last updated: 2026-09-10*
