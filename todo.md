# TODO — Next Session(s)

**Created:** 2026-10-04 (after corpus completion + audit; see `deep_researches/corpus_audit_2026-10-04.md`)
**Goal path:** finish literature review → deep-read the most relevant papers → push resources to Zotero → start writing the proposal (Persian).

---

## 1. Finish the literature review

- [x] **Rewrite `lit_review/00_thesis_literature_review.md` to the current thesis frame** — done 2026-10-04 (CNN-Mamba + SSL + temporal XAI frame; FM content kept only as §3.9 ablation/background; G1–G7 aligned with the vault; reading order replaced).
- [x] **Add Literature-Matrix rows #39–77** — done 2026-10-04 (rows 39–78, incl. Wang #43 refill, Motlagh-Ky #76, Waters #77, Virnodkar #78; agentic cluster 47–67 marked frozen).
- [x] **Write vault notes #35–38** — done 2026-10-04 (Hornero, Sanchez-Virosta, Bai, Akbari; matrix numbers verified: #35 R²=0.526/0.517; #36 R²=0.86/0.68/0.70).
- [x] **Fix `Thesis_Vault/00-Thesis-Overview.md` broken references** — done 2026-10-04 (pointer table to real locations; memory logs; FM archive).
- [x] **Write `Thesis_Vault/04-Thesis-Design.md`** — done 2026-10-04 (positioning, architecture, 4 phases, label strategy, decisions table, validation protocol, advisor questions).
- [x] **Decide the agentic question** — decided 2026-10-04: **GeoAI agents = optional chapter / future work; cluster 47–67 frozen** (rationale in `04-Thesis-Design.md` §5). Override → revisit with Munir design principles.
- [x] **Document the negative searches** — done 2026-10-04: `deep_researches/search_logs_2026-10-04.md` (4 searches, verdicts, safe-wording table; one near-neighbor found: James et al. 2025 IEEE AsianCON → added to G2 evidence + `papers_not_downloaded.md`).
- [x] Reconcile superseded docs — done 2026-10-04 (`1.md` and `memory/2026-09-06-initial-findings.md` carry SUPERSEDED banners).

## 2. Deep-read the most relevant papers (full text — nothing has been full-read yet)

Priority order and what to extract (upgrade each paper's note from extract-level to verified):

- [x] **#09 Motlagh 2026** — ✅ full read: R²=0.93 is the **full-sample fit; independent test R²=0.821**; synergy via PDPs (salinity ≈3.4 dS/m × CWSI>0.44 → collapse), **no interaction percentages exist**; ECe protocol verified (weekly saturated-paste, 0–90 cm, 128 wells, kriged; 1.7–8.0 dS/m); own CWSI triggers young 0.40–0.45 / old 0.30–0.35; 336 Amirkabir fields, 2023 season.
- [x] **#08 Paciolla 2025** — ✅ full read: ensemble-KF DA (FEST-EWB-SAFY) of Landsat-8 LAI; **single 21-ha maize field**; **no LAI→EC regression** — salinity effects emerge implicitly; ECe-free labeling only PARTIALLY supported (transfer conditions in note). High-risk bet downgraded — advisor question ① more important.
- [x] **#70 Wen 2022 HESS** — ✅ full read: PROSAIL via SNAP biophysical processor (ANN, Weiss/Baret ATBD); **no per-trait RMSE validation anywhere**; two-way ANOVA = stress-class × date (R² 0.326–0.796 verified); stresses ground-defined from SPEI-3 + groundwater Cl⁻, no in-situ; drought > salinity; "salinity impacts may have been overstated".
- [x] **#01 SITSMamba** — ✅ full read (+ repo): **PW = linear loss re-weighting of reconstruction MSE (1/L→L/L), not attention**; **single-stage supervised multi-task (CE + w0·w1·L_p), NOT SSL** — matrix claim corrected; PASTIS32 OA 0.7416/mIoU 0.5005; GitHub code diverges from paper (UMamba U-shaped) and may be incomplete — decide reimplementation strategy.
- [x] **#04 Höhl 2024** — ✅ full read: **"temporal XAI virtually unexplored" is a paraphrase, NOT verbatim** (actual: p.22 temporal-dependencies drawback + p.24 research call; precedent Rußwurm [158]); evaluation claim faithful (>90% anecdotal; 15/207 quantitative). G2 wording refined everywhere.
- [x] **#07 Angon 2022** — ✅ full read: response table verified with p-values (SDW −14/−16%, root −39% vs D, chl-a −25% vs D, gs S+D≈D, Na⁺/Cl⁻ S+D≈S, H₂O₂ +52%); **Ts, proline, ABA NOT measured** (repo table overstated); **no operational labeling criteria** — our ECe+CWSI rule is our own proposal; no sugarcane.
- [x] **#10/#24/#25 Zoratipour series** — ✅ full reads: threshold 0.4–0.5 verified (#10, Amir Kabir site, sensor SI-411); #24 gains verified (R² 0.73→0.92, rMBE −16→−8%); #25 Landsat 0.78–0.92 vs S2 0.74–0.89 verified (Persian body, 2024 campaign); **salinity never measured anywhere in the series**.
- [x] **#14 Dalal STS-NET** — ✅ full read: 3D-CAE (19.2K params), reconstruction pretext, T=32; input = RGB+NIR+mean-VI PlanetScope (~3 m satellite, **not UAV, not VI-only**); 62 sugarcane fields; **97.98/85.08/83.47 are accuracy (abstract mislabels "precision")**; combined = 9-class water×N task; no salinity/Mamba/XAI/multi-year. Differentiation paragraph drafted in note.
- [x] Then: 69/71 (Wen 2021/2023), 44-Berger, 72-Haq, 60-Paul, 77-Waters, 11-Hajeb, 12-Malee, 76-Motlagh-Ky — **✅ all 9 done 2026-10-04 (second pass)**. Highlights: Paul = 163-study corpus with SSL=3 studies (none EO), zero Mamba → G3 citable anchor; Wen-2021 all three anchor quotes verbatim + zero VI–salinity correlations (title gains "Threats"); Wen-2023 partially closes the naive joint-monitoring gap (ANOVA/proxy-labels only → G4 refined); Berger needs rewording (corpus excludes single-sensor; "compare-not-fuse" + 72% parametric is the claim) + "no concept exists… differentiate between crop stress types" (p.3); Hajeb = 136 ESUs, LSM (plant-water proxy) to 2.91% RRMSE, zero salinity; Waters = **zero salinity mentions** in the sugarcane review + DL named *future* work + moisture-index recommendation; Haq = BRDF/viewing-geometry protocol item + anisotropy-by-stress-type signature finding; Motlagh-Ky = all numbers verified + author's own salinity-confounds-CWSI warning; Malee = real paper recovered from archive (Kcb 0.15/1.11/0.49, Thailand, 25–50% MAD).
- [x] After each read: update vault note + matrix Status — done for all 8 P0 papers (intake-doc follow-up boxes ticked too) and all 9 second-tier papers (second pass 2026-10-04; #12 mis-file saga resolved — real PDF promoted from archive, wrong PDF archived, Zotero items #11/#12/#59/#77 patched via web API).

## 3. Zotero — add all good resources

- [x] **Write access** — confirmed working (env vars `ZOTERO_API_KEY` / `ZOTERO_USER_ID`, user `mahdi555`, full write+files; pyzotero in the `geo` env).
- [x] **Collection structure created** — `Thesis / {Core-Method (architecture-SSL-XAI), Concurrent-Stress, Salinity, CWSI-Thermal, Khuzestan-Local, Agentic-Optional, Datasets-Benchmarks}`.
- [x] **Corpus imported** — all 78 numbered papers as items (2026-10-04; scripts `scripts/zotero_import_2026-10-04.py` + `zotero_local_finish_2026-10-04.py`; hybrid web-API + desktop local-API route after web rate limits). Metadata from Crossref (DOI) / arXiv batch API for ~67 items; 11 items were manual-flagged (6, 10, 11, 12, 13, 25, 35, 36, 37, 59, 77). *(Update 2026-10-04 second pass: 11, 12 fixed with Crossref metadata — #12 turned out to be the real Malee AWM 333:110529 paper after the mis-filed PDF was unmasked; 59 fixed as arXiv:2511.17442 (import-time 404 was transient); 77 fixed to the PUBLISHED version CEA 229:109686. Remaining manual items to verify: 6, 10, 13, 25, 35, 36, 37.)* Legacy key papers from `00_paper_links.md` sections not yet imported (see below).
- [x] **Local PDFs attached as linked-file attachments** (paths, not uploads).
- [ ] **Verify the 7 remaining manual items + 10 random others in the Zotero client** and fix metadata by hand / "Add by identifier". Also import the ~60 legacy link-index papers (R1–R8, dataset/benchmark block) if wanted.
- [x] Virnodkar et al. 2020 — downloaded (now `papers/78`) and imported.

## 4. Start writing the proposal (Persian, per AGENTS.md)

- [ ] Get the advisor's 4 answers FIRST (they shape §methods and §labels): ① ECe ground-truth access for the 490 fields? ② operational criteria for labeling "Mixed_Stress"? ③ GPU workstation vs cloud? ④ timeline approval for the 4-phase plan. *(More urgent after the Paciolla full read: its ECe-free method is single-field only — without ECe access the salinity labels lean on a weaker proxy.)*
- [x] Positioning sentence — drafted 2026-10-04 (`Thesis_Vault/04-Thesis-Design.md` §1; reproduced in the proposal skeleton).
- [x] Draft skeleton in `proposal/draft/00-proposal-skeleton.md` (Persian) — intro → problem statement → related work → methodology (4 phases) → data & study area → expected contributions → timeline → the 4 advisor questions. Sections marked ⛔ await advisor answers.
- [~] Decide and justify: raw bands vs indices (lean: raw bands + LST, indices as ablation), Barlow Twins vs SimCLR (lean: Barlow Twins, pilot decides), Landsat-16d vs fused-S2 (lean: Landsat-16d primary) — leans documented in `04-Thesis-Design.md` §5; finalize after advisor answers.
- [ ] Export to Word-ready markdown as sections stabilize.

---

## Housekeeping (quick wins)

- [x] `New_papers/` — emptied and folder removed 2026-10-04 (all 4 remaining PDFs md5-verified identical to canonical `papers/` copies 09/43/76/78 first).
- [x] `papers/archived_duplicates/` — `ref-Melanie…` (#13) deleted after md5 match with the canonical copy; `ref-Leveraging…` (#09) **retained** — its checksum differs from the canonical user-download copy (possible version variant; see `papers/ARCHIVED_DUPLICATES.md` cleanup note). Log updated.
- [x] MCP/tools check — paper-search MCP works (used for the negative searches); Semantic Scholar still 403 (OpenAlex/Crossref used instead); Zotero web API + desktop local API both working.

---

*After any task: update `memory/` (repo log), tick the boxes here, and commit with conventional commits (branch: `main`).*
