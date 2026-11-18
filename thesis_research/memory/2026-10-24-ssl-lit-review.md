# 2026-10-24 — Deep SSL Literature Review Complete (84 papers, 8 deliverables)

**Task:** Evidence-based SSL literature review (foundations → RS → SITS → agriculture/stress → gaps), per user brief. Literature only — no implementation.

## Deliverables (all in `SSL_Proposal/lit_review/`)

- `00_search_log.md` — verbatim query log, screening decisions, ~25 exclusions with reasons, 13 ID corrections, coverage limitations, pilot validation.
- `01_ssl_foundations.md` — SimCLR/MoCo/SwAV, BYOL/SimSiam/DINO/data2vec, MAE/BEiT, I-JEPA/V-JEPA/T-JEPA, TS-SSL, AD-SSL.
- `02_remote_sensing_ssl.md` — domain-gap evidence (SeCo, SSL4EO, DeCUR), single-date SSL, evaluation pitfalls (probing vs fine-tuning rank methods differently; pretrain/downstream similarity dominance).
- `03_satellite_time_series_ssl.md` (most detailed) — T1–T6 temporal-supervision taxonomy; SatMAE/Presto/SeCo/Galileo/T-JEPA/Time2Agri/TiMo deep-dives; irregular sampling/clouds table.
- `04_agriculture_vegetation_stress.md` — direct vs indirect evidence separation; ground-truth quality column.
- `05_comparative_evidence_matrix.csv` — 84 rows × 19 cols, machine-readable, validated (no ragged rows/dupes).
- `06_research_gaps_and_thesis_directions.md` — gaps G1–G8, trade-off table, 5 ranked directions, explicit non-claims.
- `07_verified_bibliography.bib` — 87 entries, braces balanced; residual [UNVERIFIED]/[not verified] flags: Agastya, Elbeltagi, several 2026 discovery papers.
- `08_executive_synthesis.md` — RQ1–RQ8 + recommended next step.

## Key findings (evidence-anchored)

1. **No verified temporal-SSL paper uses Landsat 16-day composites** — the Landsat-archive gap (G2) is real and defensible.
2. **No verified label-free SSL stress detection with independent field-level physiological ground truth exists.** All direct stress evidence is 2024–2026 preprints: STS-NET (controlled stress, supervised head), EigenCL (label-free staging, proxy validation, cross-year transfer), Sadbhave (fully unsupervised), MIM-AD (contaminated-normal handling), temporal inpainting (~3× sensitivity).
3. **Defensible novelty claim:** "first label-free stress AD on a long Landsat field-level archive with optical+LST" — NOT "first label-free crop-stress AD".
4. **No verified temporal-SSL model consumes LST** (G1) — optical+thermal SSL recipe is open.
5. Contamination of "normal" training data is unsolved in agri-AD (G4); synthetic-anomaly / AnomalyBERT-style degradation self-supervision is the candidate remedy.
6. Label efficiency is SSL's sweet spot; linear probing vs fine-tuning rank methods differently — protocol must be fixed and stated.

## Recommended method updates (for `method_design_ssl.md`)

- Add a **synthetic-anomaly degradation arm** (inject anomalies into training series, train detector to flag them — AnomalyBERT-style) alongside reconstruction and contrastive arms.
- **Presto and STS-NET as mandatory baselines** (not optional).
- Update `literature_review_ssl.md` (the 9-seed stub) — superseded by the deep review; kept as stub for now, could be replaced by a pointer to `lit_review/`.

## Verification status

- arXiv IDs verified in batch via export API (13+ wrong IDs caught and corrected, e.g. CROMA 2311.00566, Galileo 2502.09356, GASSL 2011.09980).
- "PANOPTIC pretraining paper" = phantom (it's the attention module in Garnot & Landrieu ICCV 2021) — excluded, not fabricated.
- EigenCL 2506.03394 = short version of 2608.25888 — deduplicated.
- [UNVERIFIED] flags remain on: Agastya, Elbeltagi 2026 metadata, several 2026 discovery papers (author lists incomplete in bib).

## Files

- Scratch/audit artifacts kept in `SSL_Proposal/lit_review/`: `scripts_mine_pdfs.py`, `_build_matrix.py`, `_pdf_mining.json`, `_arxiv_batch1.xml` (reproducibility trail).
- No PDFs committed.
- Resolves questionnaire deferred items: Q2 (pretext), Q5 (SSL goal), Q9 (baselines), Q10 (XAI validation), Q11 (compute) now decidable from `08_executive_synthesis.md`.
