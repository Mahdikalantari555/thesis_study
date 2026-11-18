# Papers Recovery — 2026-10-04 (corpus complete: 01–77)

**Trigger:** user asked to fill all missing PDFs after the corpus audit.

## Result
`papers/` now has **77 PDFs, slots 01–77 with zero gaps**. Full table in `papers/INTAKE_LOG_2026-10-04.md` § Recovery pass.

## What was done
- Downloaded directly: 02-Miller, 03-Balestriero, 04-Hohl, 05-Russwurm, 18-Miranda (arXiv); 08-Paciolla (Springer OA worked via `link.springer.com/content/pdf/<DOI>.pdf`); 77-Waters (arXiv).
- Recovered from repo: 13-Sapkota (promoted from `archived_duplicates/`); 07-Angon renamed from `43-…-DUP.pdf` → slot 07 canonical, slot 43 refilled.
- User-downloaded (elsevier browser): 09-Motlagh (yield baseline), 76-Motlagh (Ky), 43-Wang (S2 salinity arid China).

## Lessons (durable)
1. **Elsevier/AWM ScienceDirect blocks curl** (returns HTML block page) — user downloads via browser into `New_papers/`; works every time. Springer OA works via direct content-pdf URL; MDPI main site blocks curl but `res.mdpi.com/d_attachment/...` works with browser headers.
2. **Repo metadata error fixed:** the Wang salinity paper was indexed as RS 13:1517 — actually **RS 13(2):305** (doi 10.3390/rs13020305). A URL fetched from the wrong article number delivered a bauxite-mining paper; always validate first page against the expected title before filing.
3. **Sapkota venue corrected:** Scientia Horticulturae 339:113860 (not Agronomy as the matrix claimed); topic = almond orchards.
4. Angon renamed 43→07 (canonical advisor/matrix copy); slot 43 refilled with Wang 2021 to keep numbering contiguous.
5. Virnodkar et al. 2020 (the one paywalled holdout) was manually downloaded by the user on 2026-10-04 → `78-Virnodkar-2020-WaterStress-ML-Review.pdf`. **Final state: 78 PDFs, slots 01–78, no gaps — corpus complete.**

---
*Logged 2026-10-04.*
