---
date: 2026-10-20
tags: [memory, vault, literature, corpus-audit]
---

# 2026-10-20 — Vault note completion pass (corpus 01–78)

## What was done

The Obsidian vault `Thesis_Vault/papers/` held 50 notes while `thesis_research/papers/`
held **78 numbered PDFs** (slots 01–78, no gaps). **32 slots had no markdown note**:
39–43, 45–59, 61–68, 73–75, 78.

All 32 were written this pass. **Final `papers/` folder count: 78 markdown notes — exactly one
per PDF slot 01–78, no slot missing, no duplicates.** (The other vault notes — `00-Thesis-
Overview`, `03-Research-Gaps`, `04-Thesis-Design`, `Literature-Matrix` — sit at the vault
root, outside `papers/`.)

## Method

- Full text extracted from all 32 PDFs with `pypdf` (`scripts/extract_vault_text.py`)
  → `C:\Users\ASUS\AppData\Local\Temp\opencode\pdf_text\*.txt`, with `===== PAGE n =====`
  markers so page references stay verifiable.
- 9 parallel subagents wrote the notes against a single shared house-style spec
  (`VAULT_NOTE_SPEC.md`): H1 `NN — Title (Author et al., Year)`, `**Full Citation:**`
  (APA 7), `**DOI:**`, `**Status:**`, `**Themes:**`, then `## What It Does` /
  `## Key Methodology` / `## Key Findings` / `## Relevance to Thesis` (✅ ⚠️ ❌ bullets
  with a bold verdict) / `## Key Takeaway` / `## Links`, closing with
  `---` + `*Linked from: [[Literature-Matrix]]*`.
- `scripts/qa_vault_notes.py` checks structural compliance of the new notes only
  (the 46 pre-existing notes use a looser legacy heading style and are skipped).
  All 32 new notes pass.
- `scripts/update_matrix_notes.py` back-filled `Literature-Matrix.md`: every updated
  row now carries `` `papers/<note>.md` `` in its Notes column and a
  `✅ Full read (2026-10-20)` status (frozen-cluster rows get
  `✅ Full read (2026-10-20) — frozen-cluster background`).

## Cluster rules applied (unchanged from 2026-10-04)

- **Frozen agentic/GeoAI cluster** — rows 47–59 and 63–67. Every note uses verdict
  **Optional** (Low-Medium for #50 AgriWorld and #66 Musazade, which genuinely touch
  agriculture/water/plant stress), states the cluster is frozen as of 2026-10-04, and
  **proposes no extension**. Do not add further agentic work to the thesis.
- **Foundation models** — archived 2026-09-10 (`papers/ARCHIVAL_LOG.md`); ablation /
  robustness-check reference only, never the backbone. **The user declined vault notes
  for these on 2026-10-20** ("not necessary now, ignore them"), so they remain
  documented only in `lit_review/00_paper_links.md` §1–7 and
  `lit_review/phase1_stress_detection_methods.md`.

## Substantive corrections found while reading (important — several contradict the matrix)

These were verified against the PDFs and recorded in the new notes. The matrix's
"Key Findings" cells for these rows are now known to be wrong or imprecise:

| Row | Matrix says | PDF actually says |
|-----|--------------|-------------------|
| 43 Wang 2021 | "RF on S2 indices, R²≈0.78" | **SVM is the best model, verification R²=0.88; RF verification R²=0.27.** The 0.783 is an unattributed Discussion comparison (p. 11). **No salt-vegetation index exists in the paper.** S2A/S2B inconsistency between p. 1 and p. 4. |
| 68 Ahmad 2021 | "Remote Sens. 13(16):4155" | Issue is **13(20)**, not 13(16). Authorship Ahmad, Alvino & Marino confirmed. The review's taxonomy is **sensor-based** (7 families) — TVDI/VDI/NDI do **not** appear; only CWSI, WDI, NGRDI. |
| 61 Zhang 2026 | "Arizona analog" | Study area is **mainland China**, not Arizona (that is #62). |
| 39 Maes 2012 | — | The review contains **no** salinity/osmotic-stress statement. The intake note A1 claim was contradicted; the "thermal index cannot separate osmotic from hydraulic closure" point is a **derivation from the equations (eq. 41)**, not a quotation — cite accordingly. |
| 42 Gerhards 2019 | "single-index CWSI fails under co-occurring stresses" | The paper has **no salinity content**; that claim is a thesis-level inference, not the paper's finding. |
| 40 Feller 2014 | "combined stress ≠ sum of singles" | The paper argues **mechanistically**; there is **no non-additivity test**. Heat acts on stomata *oppositely* to drought (p. 2). |
| 63 Sun 2026 | "label-efficient / self-evolving for label-efficient RS detection" | The SSDD evaluation is **fully supervised**; there is no annotation-budget ablation, so "label-efficient" is unmeasured. |
| 65 Tariq 2025 | — | Internal inconsistency in the paper itself: weather accuracy 88 % (abstract) vs 87 % (Table 8); MAE 0.5277 vs "52.77 %"; "every hour" (p. 2) vs "every 5 s" (Table 10). No field trial, no edge-hardware measurements. |
| 67 CottonBot 2025 | — | The field trial is **still planned for 2026**, not performed. |
| 66 Musazade 2026 | — | Narrative review with **no PRISMA / no n / no year window / no search protocol**. Evidence base is close-range RGB/UAV only; satellite appears only as future work (p. 11). |
| 47 RS-Agent | "27 tools / 18 tasks", "Sci China Inf Sci" | "Sci China Inf Sci" is the **review** venue only; the paper itself is arXiv:2406.07089. ">95 % planning accuracy" is **backbone-dependent** (48.00–98.50 % on the 10-task set). |
| 50 AgriWorld | — | The PDF itself reports three different accuracies for the full system (57.6 % / 73.84 % / 73.8 %). AGROBENCH is built on an unnamed existing benchmark; no code URL. |
| 49 Talemi 2026 | — | MapBot is intro-only, **not in Table 1**; "copilots vs orchestrators" is Fig. 1 caption wording only. |

Also confirmed/added: #45 Shen 2025 is a **semi-structured** review (n=70 articles,
2018–2024), only 7/70 integrate all three themes; #46 Smanov 2026 is a PRISMA-2020
review (58 Scopus studies, 1994–2024) naming three ignored variables (ion composition,
root-zone vs surface salinity, phenology) — and it names **no sugarcane, Iran or
Khuzestan**; #73 Gokul 2026's CEWT = *canopy equivalent water thickness*, not "crop
evapotranspiration water stress"; #74 GraciaRojas 2026 is PRISMA-2020, n=105; #75
Olawoyin 2026 is a 24-yr in-situ-free LST–NDVI triangular CWSI with an internal
Table 4 vs Fig. 9 coefficient conflict.

## New thesis-relevant content worth carrying forward

- **#39 Maes 2012 — the equifinality argument.** CWSI/CTD are one-dimensional functionals
  of stomatal conductance (eq. 41): because T_pot and T_dry are defined by the energy
  balance of a maximally transpiring and a non-transpiring canopy *of the same
  structure*, every driver that reduces g_s (hydraulic, osmotic, cuticular) moves T_c
  along the same axis, while heat-driven stomatal *opening* moves it the other way.
  The thermal signal is **equifinal with respect to the driver**. This is the physics
  backbone of the thesis problem statement, and it also predicts a **heat-wave confound**
  for any CWSI-threshold rule.
- **#41 Tardieu 2018** — a "scenario" is a **time-course, not a place** (p. 736); trait
  signs flip across the 5 Table-1 scenarios; osmotic adjustment (≈30 min half-time,
  ≈0.5 MPa) lets salinity hold turgor — and therefore CWSI — near normal. Supports
  soft/mixture labels over hard global stress classes.
- **#46 Smanov 2026** — crop salt tolerance is a **spectral mediator**, so spectral–EC
  relationships are crop-specific. Directly threatens a Khuzestan transfer if the
  cultivar/phenology mix is not documented.
- **#53 RSMeM** — failure-aware memory with a **label-free symbolic failure critic** is
  the closest published analogue to label-efficient refinement (an *analogue* of the
  active-learning branch, not a component of it).

## Housekeeping

- `scripts/extract_vault_text.py` — reusable PDF→text extractor with page markers.
- `scripts/qa_vault_notes.py` — structural QA for the new notes.
- `scripts/update_matrix_notes.py` — idempotent matrix back-fill.
- `papers/archived_foundation_models/FARM.pdf` is **truncated/corrupt** (no xref/trailer);
  `pypdf` and `pdftotext` both fail. Text was recovered by scanning raw FlateDecode
  streams (`recover_farm.py` logic) but with broken word spacing. **Re-download needed**
  if a note is ever wanted for it.

## Next actions (not done here)

- The matrix's "Key Findings" cells for rows 43, 68, 61, 63, 65, 66, 67, 47, 50, 49
  still carry the pre-verification wording above. They were **not** rewritten in this
  pass (the notes carry the corrections) — reconcile if the matrix is to be authoritative.
- `Literature-Matrix.md` "Quick Filter" lists still show the old reading priorities.

---
*Logged 2026-10-20. Repository branch: `main`.*
