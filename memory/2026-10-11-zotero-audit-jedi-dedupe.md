# 2026-10-11 — Zotero collection audit + JEDI dedupe

## Trigger
User suspected the JEDI article had been "moved". Audited the full library via the Zotero web API
(`GET /users/21956537/...`, `Authorization: Bearer $ZOTERO_API_KEY`).

## Findings
- **JEDI was not moved — it was duplicated.** Two top-level items with identical title/authors
  (Bhaumik et al. 2026, arXiv:2609.07915):
  - `9AHE5DGE` — the **original** (added 2026-10-04): intact in collection `PC9ZNIU2`
    (Core-Method architecture-SSL-XAI), with abstract, arXiv ID, Extra `Matrix #33 | local PDF:
    papers/33-Bhaumik-2026-JEDI-Foundation-Model.pdf`, attachment `EEMJMPFT`. ✅ untouched.
  - `RTAZ5AMS` — a **bare stray** (added 2026-10-08): no abstract, no identifiers, no PDF,
    misfiled in collection `XEZW3BXC` (Salinity). Classic accidental connector re-import.
- Library-wide duplicate-title scan: **exactly 1 duplicate pair** (this one). Nothing else.
- Top-level count was 79 = 78-paper corpus + the stray; every item belonged to ≥1 collection
  (no orphans). Salinity collection otherwise coherent: 6 salinity papers (Shi 2022, Gupta 2025
  spectroscopic review, Dey 2025 DeepSalt, Paciolla 2025 LAI-DA, Smanov 2026 salt-tolerance
  review, Wang 2021 S2 ML) each with its PDF attached.

## Action
- `DELETE /users/21956537/items/RTAZ5AMS` with `If-Unmodified-Since-Version: 326` → **HTTP 204**.
  Item is in Zotero trash (recoverable 30 days), not permanently gone.
- Post-fix verification: **78 top-level items, 0 duplicate titles**, Salinity membership clean,
  original JEDI `9AHE5DGE` unchanged (version bumped on its own; attachment intact).

## Note
`include=trashed` is NOT a valid param on `/items` (HTTP 400); trashed items are simply hidden
from default reads (GET of a trashed key returns 404). Pagination: `/items?limit=100&start=N`
works; a single `limit=200` call silently under-returns — always paginate.
