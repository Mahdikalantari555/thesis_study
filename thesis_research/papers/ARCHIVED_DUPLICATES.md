# Archive Log — Duplicate Papers Removed
**Date:** 2026-09-14 (updated 2026-10-04)

## Duplicates Identified and Archived

| Ref- File | → Matrix ID | Reason |
|-----------|------------|--------|
| ref-Leveraging-RS-ML-Assessing.pdf | **#09** Motlagh et al. 2026 | Same paper, different source filename |
| ref-Enhancing-Water-Productivity-Sugarcane-Basal.pdf | **#12** Malee et al. 2026 | Same paper, different source filename |
| ref-Melanie-2025-ET-Crop-Water-Stress-Scientia.pdf | **#13** Sapkota et al. 2025 | Same paper, different source filename |

**Action taken:** Moved duplicates to `archived_duplicates/` subfolder.

## Cleanup pass — 2026-10-04

- `ref-Melanie-2025-ET-Crop-Water-Stress-Scientia.pdf` **deleted** — byte-identical (md5 `7502b460…`) to the promoted canonical copy `13-Sapkota-2025-ET-CWSI-NDVI-Almond.pdf`.
- `ref-Leveraging-RS-ML-Assessing.pdf` **retained** — its md5 (`cb0bd04a…`) differs from the canonical `09-Motlagh-2026-Sugarcane-Yield-Variability.pdf` (md5 `6456d12e…`, from the 2026-10-04 user download `1-s2.0-S2772375526006167-main.pdf`). It is kept as a possible different version (e.g. accepted manuscript) pending a version check; do not delete without diffing content first.
- `ref-Enhancing-Water-Productivity-Sugarcane-Basal.pdf` retained (canonical #12 exists; low value, but not blocking anything).

## Mis-file resolution — 2026-10-04 (second pass)

**Finding:** `papers/12-Malee-2026-Sugarcane-Crop-Coefficients.pdf` was NOT the Malee paper — page-1 check proved it is the Motlagh Ky paper (same title/authors as `76-Motlagh-2026-Ky-Derivation.pdf`; only file bytes differ). Because of this mis-file, matrix row #12 had inherited the Ky claims (Ky=1.05, "Khuzestan/Kcb") and `ref-Enhancing-Water-Productivity-Sugarcane-Basal.pdf` — the **real** Malee et al. 2026 paper (AWM 333:110529, Thailand, Kcb 0.15/1.11/0.49, lysimeters + SIMDualKc + AquaCrop) — had been wrongly archived as its duplicate.

**Actions:**
- `12-Malee-2026-Sugarcane-Crop-Coefficients.pdf` (Ky content) → moved to `archived_duplicates/`.
- `ref-Enhancing-Water-Productivity-Sugarcane-Basal.pdf` → **promoted** to `papers/12-Malee-2026-Kcb-DeficitIrrigation.pdf` (md5 `0b50592b…`).
- Matrix row #12 rewritten with the real Malee claims; row #11 corrected (IJAEOG not ISPRS; "Kcb" claim removed — it belonged to #12).
- Zotero item `FRBZ964I` (#12) patched with Crossref metadata + new linked-file attachment; broken attachment to the mis-filed PDF deleted. Item `EQI2E6UV` (#11) patched (title/creators/journal/DOI).
- Earlier entry in the table above ("ref-Enhancing … Same paper") is **superseded** by this resolution.
