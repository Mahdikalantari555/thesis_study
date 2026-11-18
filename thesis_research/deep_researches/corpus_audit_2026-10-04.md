# Corpus Audit — Reading Gaps & Unfinished Work

**Date:** 2026-10-04
**Scope:** Full inventory cross-check of `thesis_research/`: PDFs ↔ matrix ↔ vault notes ↔ intake notes ↔ link indexes ↔ memory logs.
**Question answered:** What work is unfinished, and where are the gaps in reading the papers we have?

---

## 0. Headline findings

1. **Not a single paper in the corpus has been deep-read full-text.** Every summary in the repo is abstract-level or first-4-pages-level. The Literature-Matrix legend defines "✅ Read" as *"full abstract read"*; all 37 intake notes (A1–A16, G1–G21) carry the footer *"written from first-page extract — verify numbers in full PDF."* With 66 active PDFs on disk, reading depth — not acquisition — is now the binding constraint on the literature review.
2. **5 of the advisor's 8 mandatory papers have no local PDF** (Miller, Balestriero, Höhl, Rußwurm, Paciolla) — including the two that anchor the validation design: **Paciolla 2025** (LAI-as-salinity-proxy, removes the ECe requirement) and **Höhl 2024** (temporal-XAI gap evidence).
3. **The single most load-bearing local paper has no canonical PDF:** Motlagh et al. 2026 (matrix #09, the R² = 0.93 yield/CWSI baseline for Amirkabir). Its only copy sits misfiled in `papers/archived_duplicates/` after the 2026-09-14 dedup assumed a numbered copy existed. Same for **Sapkota 2025** (#13).
4. **The main literature review still recommends the thesis direction the advisor rejected.** `lit_review/00_thesis_literature_review.md` §8/§10 ranks "T3 with elements of T1 and T2" (Prithvi/AlphaEarth + active learning) as the winner — this is the pre-redesign FM-era frame, written 2026-09-06 and never reconciled with the 2026-09-10 pivot to CNN-Mamba + SSL + XAI.
5. **Two knowledge systems have silently diverged:** the Obsidian `Literature-Matrix.md` stops at paper #38; the 37 papers from the two intakes (39–75) exist as PDFs + A/G notes but have no matrix rows and no vault notes. The vault's own navigation references 6 files that do not exist.
6. **The agentic cluster is over-weighted relative to the redesigned thesis:** 18 of 66 active PDFs (27%) are LLM-agent papers for a component the overview labels "optional GeoAI agent orchestration" — while temporal XAI (the claimed novelty) is supported by 2 papers, one of which has no local PDF.

---

## 1. Physical inventory (verified 2026-10-04)

| Asset | Count | Location | Status |
|---|---|---|---|
| Active numbered PDFs | **66** (`01–75`, 9 numbers missing) | `papers/` | on disk, gitignored |
| Archived foundation-model PDFs | 7 | `papers/archived_foundation_models/` | on disk |
| Archived duplicate PDFs | 3 | `papers/archived_duplicates/` | **2 of them are the only copies of #09, #13** |
| Literature-Matrix rows | 38 (17 "Read", 21 "🆕 needs full text") | `Thesis_Vault/Literature-Matrix.md` | **stops at #38** |
| Vault paper notes | 34 (`01–34`) | `Thesis_Vault/papers/` | abstract-level |
| Intake notes | 37 (A1–A16 agricultural, G1–G21 agentic) | `deep_researches/new_papers_notes/` | first-4-pages level |
| Extract folders | 29 + 9 files | `deep_researches/new_papers_*_extract/` | page 1–4 text |
| Link index entries | ~60 legacy + N1–N37 | `lit_review/00_paper_links.md` | 5 critical papers absent |
| Not-downloaded citations | ~96 remaining | `lit_review/papers_not_downloaded.md` | never fetched |
| `New_papers/` staging folder | 9 PDFs | `D:\RS\Thesis\New_papers\` | **all already copied into `papers/68–75` — safe to delete** |

**The 9 missing PDF numbers:** 02 (Miller DL-SITS review), 03 (Balestriero SSL cookbook), 04 (Höhl XAI review), 05 (Rußwurm & Körner self-attention), 07 (Angon — covered by `43-Angon-2022-combined-stress-DUP.pdf`), 08 (Paciolla), 09 (Motlagh), 13 (Sapkota), 18 (Miranda PINN). `papers_new/` (the earlier download target) is now empty, so 6 of these exist nowhere in the workspace.

---

## 2. Reading-depth gap — the core problem

| Layer | What exists | Actual depth |
|---|---|---|
| Advisor's 8 papers | `advisor_papers_analysis.md` (detailed per-paper analysis) | Metadata + abstract + secondhand summaries; open item "download full PDFs for papers 5, 7, 8" still unchecked; Paciolla/Höhl/Miller/Balestriero/Rußwurm have no PDF |
| Khuzestan 5 papers | `khuzestan_sugarcane_papers_summary.md` | Numbers extracted (R²=0.93, Ky=1.05, CWSI 0.4–0.5, LAI RMSE 0.48) but Methods sections never verified |
| Matrix 01–34 | Vault notes | Abstract-level by the matrix's own legend |
| Matrix 35–38 | Matrix rows only | No vault note at all |
| Intake 39–75 | A/G notes + extracts | First-4-pages; quantitative tables beyond page 4 explicitly unverified |

**Consequence:** the thesis-critical numbers circulating in the repo (R² = 0.93 baseline; EC_LOWW = 1.7 dS/m; Barlow Twins suitability; SITSMamba PW mechanics; Wen trilogy trait RTM) are **single-source, unverified, extract-level claims**. AGENTS.md §3.2 requires verified citations; §3.6 requires quantitative specificity — both are currently met only at abstract depth.

**Priority full-text reads (P0), chosen by decision impact:**

| # | Paper | Why it must be read in full first |
|---|---|---|
| 1 | Motlagh et al. 2026 (#09) | Every validation target (R²=0.93, water×salinity synergy %) hangs on it; also defines the label source for "Mixed_Stress" |
| 2 | Paciolla et al. 2025 (#08) | Justifies skipping ground ECe for 490 fields — the highest-risk methodological bet in the redesign |
| 3 | Wen et al. 2022 HESS (`papers/70`) | Which RTM produced the five traits; the closest competitor's actual methods |
| 4 | SITSMamba (#01 + GitHub repo) | The architecture blueprint — PW mechanism and reconstruction branch must be understood at implementation level |
| 5 | Höhl et al. 2024 (#04) | The temporal-XAI gap claim is quoted from it; novelty claim G2 rests on one review |
| 6 | Angon et al. 2022 (`papers/43`) | Mixed-class physiology and labeling criteria come from it |
| 7 | Zoratipour et al. 2026 (#10) + 2025 (#24) | CWSI threshold and bias-correction pipeline reused as validation |
| 8 | Dalal STS-NET 2026 (#14) | Closest methodological competitor (SSL+SITS+stress) — differentiation must be precise |

---

## 3. Inventory-integrity gaps

1. **Misfiled unique copies:** `archived_duplicates/ref-Leveraging-RS-ML-Assessing.pdf` (→ Motlagh #09) and `ref-Melanie-2025-ET-Crop-Water-Stress-Scientia.pdf` (→ Sapkota #13) should be promoted to `papers/09-…` / `papers/13-…`; they are currently catalogued as duplicates of files that don't exist.
2. **Five thesis-critical papers missing from `00_paper_links.md`** (no download URL recorded anywhere in `lit_review/`): Miller et al. 2024 (arXiv:2404.03936), Balestriero et al. 2023 (arXiv:2304.12210), Rußwurm & Körner 2020 (arXiv:1910.10536), Motlagh et al. 2026, Paciolla et al. 2025 (doi:10.1007/s11119-025-10279-5). If the missing PDFs can't be recovered, there is no link to re-fetch them from.
3. **Waters et al. 2024 sugarcane satellite-spectroscopy review** — flagged in `knowledge_base_extended_literature.md` as the most relevant review for the study crop (its VI table feeds band selection) — is **not in the matrix, not in the link index, not downloaded**. It exists only inside two discovery docs. It has fallen through every crack.
4. **Vault navigation is broken:** `00-Thesis-Overview.md` references `01-Advisor-Papers-Analysis.md`, `02-Khuzestan-Sugarcane-Papers.md`, `04-Thesis-Design.md`, `papers/FM-Prithvi-EO-2.0.md`, and two memory logs — none exist. `04-Thesis-Design.md` was never written (methodology lives scattered across the overview diagram + advisor analysis §Implementation Path).
5. **Stale checkbox:** advisor memory says "get full text of Paper 6 (Ahmed)" — it has been downloaded (`papers/06`) since 2026-09-10; the item was never closed.

---

## 4. Unintegrated / contradictory documents

| Document | Problem |
|---|---|
| `lit_review/00_thesis_literature_review.md` (main deliverable) | Still pre-redesign: exec summary, gap table (G1–G10), ranked ideas T1–T10, §9 architecture (Prithvi MAE + AlphaEarth + active learning), §10 final recommendation, §11 reading order — all FM-era. **Its §10 recommendation contradicts the advisor-approved CNN-Mamba redesign.** Wen trilogy was added to §6 (2026-10-04) but the surrounding frame is stale. |
| `Thesis_Vault/Literature-Matrix.md` | Missing rows for #39–75 (two full intakes). Missing vault notes for #35–38. |
| `memory/2026-09-06-initial-findings.md` | Recommends T1/T3 FM direction — superseded, unmarked. |
| `1.md` (workspace root, 1447 lines, Persian) | The old FM-era proposal draft (2026-09-06). Superseded by the redesign; not referenced by anything in the repo; risk of being mistaken for current. |
| Agentic intake (G1–G21) | 21 papers summarized but never folded into any `lit_review/` section — the 2026-09-10 intake doc itself lists "decide whether GeoAI agents are core or future-work" as an open checkbox. |
| Advisor open questions | 4 unanswered items that block design: ECe ground-truth access for 490 fields; mixed-stress labeling criteria; GPU vs cloud compute; timeline approval. |
| Advisor-requested deliverable | "Literature Matrix **Excel** file" (2026-09-10) — never produced; the markdown matrix is the only tracking artifact. |

**Not started at all** (folders exist, contents empty): `proposal/` (no Persian draft — AGENTS.md requires formal docs in Persian), `data/raw|processed`, `notebooks/`, `outputs/`, `scripts/preprocessing|features|models|active_learning`. No SITSMamba repo clone, no GEE pipeline, no benchmark planning despite gap G5 promising a released dataset.

---

## 5. Corpus coverage analysis (66 active PDFs)

### 5.1 Cluster map

| Cluster | Papers (matrix #) | n | Depth |
|---|---|---|---|
| Khuzestan sugarcane (local baselines) | 09†, 10, 11, 12, 23, 24, 25 | 7 | abstract only; †PDF misfiled |
| CWSI / thermal water stress | 35, 36, 37, 39, 42, 68, 73, 75 (+10, 24, 25 above) | 11 | extract only |
| Salinity mapping / estimation | 19, 20, 27, 46 (+08†) | 5 | extract only; †PDF missing |
| **Concurrent water×salinity** | 43, 69, 70, 71 | 4 | extract only |
| Stress physiology | 21, 40, 41 | 3 | extract only |
| General stress-RS reviews | 29, 44, 45, 60, 72, 74 | 6 | extract only |
| SITS / SSL / stress DL | 01, 14, 15, 16, 22, 26, 31, 32 | 8 | extract only |
| XAI | 06, 17 (+04†) | 3 | abstract/extract; †PDF missing |
| Mamba / SSM | 01, 30 | 2 | abstract only |
| SSL theory | 03† | 1 | †PDF missing |
| Crop mapping / ML misc | 28, 38 | 2 | extract only |
| Agentic / LLM-RS | 47–59, 63–67 | 18 | extract only |
| Irrigation RS hydrology | 61, 62 | 2 | extract only |

### 5.2 Strengths (well covered for the redesigned thesis)

- **Local validation cluster** — 7 Amirkabir/Khuzestan papers give CWSI thresholds, Ky, LAI retrieval accuracy, and a yield baseline. Rare advantage; no competitor paper can claim the same site-specific grounding.
- **Concurrent-stress framing** — post-2026-10-04 intake: Angon (physiology) + Wen trilogy (satellite traits, descriptive) + Paciolla (LAI proxy, PDF missing) = a defensible, well-cited problem statement.
- **CWSI/thermal physics** — 11 papers spanning ground (Maes), TIR physics (Gerhards), UAV (Gokul, Sanchez-Virosta), and satellite (Zoratipour series).
- **SITS-SSL competitors identified** — STS-NET, EigenCL, Sadbhave give a precise differentiation boundary.

### 5.3 Weak spots (thin evidence where the thesis makes its claims)

| Thesis pillar | Corpus support | Assessment |
|---|---|---|
| **Temporal XAI for SITS (claimed novelty G2/G6)** | Höhl 2024 (missing PDF) + Ahmed 2025 + Najjar 2024 | 3 papers, none applied to SITS — good for the gap claim, but the thesis needs methodological anchors for *temporal* SHAP/Grad-CAM that the corpus does not yet contain (e.g., time-series XAI literature from other domains) |
| **Mamba/SSM for stress (G1)** | SITSMamba + ScopeMamba (detection, not SITS-stress) | Only 1 directly relevant paper; the novelty claim currently rests on a negative search — the search itself is undocumented (no search log for "Mamba + stress") |
| **SSL recipe for multi-modal SITS (G3)** | Balestriero cookbook (missing PDF) | Zero EO-specific multi-modal SSL papers in corpus; gap claim plausible but thin |
| **Optical + thermal DL fusion for stress** | none dedicated | The redesign feeds LST into the CNN input, but no corpus paper does optical+LST DL fusion for stress — needs 2–3 supporting papers or an explicit novelty claim |
| **Mixed-stress labels in practice** | Angon (physiology) + Motlagh (interaction %) | No paper anywhere defines *operational labeling criteria* for a Mixed class — the advisor question remains the design blocker |
| **Benchmark/dataset papers (G5)** | 0 downloaded | CropHarvest/PASTIS etc. exist only as links in `00_paper_links.md` |
| **Active learning** | 0 downloaded (BSSAL link only) | Post-redesign this pillar was demoted — decide whether to keep or prune, then align the corpus |

### 5.4 Balance issues

- **Agentic overweight:** 27% of active PDFs serve an optional chapter; they also dominate the most recent intake. If agents stay optional, stop acquiring in this cluster and mark G1–G21 "background — do not extend."
- **Venue skew:** the corpus is heavy on MDPI/review venues; empirical Q1 DL-for-stress papers (RSE/ISPRS/TGRS) are under-represented among owned PDFs — several are sitting un-fetched in `papers_not_downloaded.md`.
- **~96 known-relevant citations never downloaded** (`papers_not_downloaded.md`), including all dataset/benchmark papers and the entire salinity-hyperspectral block (#29–39 of the link index) that the salinity branch of the thesis will need.

---

## 6. Prioritized action plan

**P0 — this week (blocks everything else)**
1. Recover Motlagh (#09) and Sapkota (#13) from `archived_duplicates/` into canonical `papers/` names; add their DOIs to `00_paper_links.md`.
2. Re-fetch the 5 missing advisor papers (4 have arXiv links; Paciolla via Springer OA check); add their links to `00_paper_links.md` — they are currently unrecoverable from the index.
3. Acquire and index Waters et al. 2024 sugarcane review.
4. Full-text read the 8 P0 papers in §2, upgrading their notes from extract-level to verified level (numbers + methods sections).

**P1 — before proposal drafting**
5. Rewrite `00_thesis_literature_review.md` around the CNN-Mamba + SSL + XAI frame (exec summary, gaps G1–G7 from `03-Research-Gaps.md`, replace T1–T10 with the redesign; keep FM content as ablation background).
6. Add matrix rows 39–75 + vault notes 35–38; fill the 6 missing vault files (or fix the overview's links); write the missing `04-Thesis-Design.md`.
7. Get the advisor's 4 answers (ECe access, mixed-label criteria, compute, timeline) — these gate the label design and the benchmark promise (G5).
8. Decide the agentic question (core chapter vs future work) and prune/keep accordingly.

**P2 — as time allows**
9. Produce the advisor-requested Excel literature matrix (export from the markdown matrix).
10. Work through `papers_not_downloaded.md` selectively (dataset/benchmark + salinity-hyperspectral blocks first).
11. Document negative searches (Mamba+stress, temporal-XAI+SITS, multi-modal SSL SITS) as dated search logs so the novelty claims in G1–G3 are auditable.
12. Archive or clearly label `1.md` and the 2026-09-06 memory as superseded.
13. Delete `New_papers/` contents (all 9 files already copied into `papers/68–75`).

---

*Audit performed 2026-10-04. Every claim above was verified against the files on disk on this date.*
