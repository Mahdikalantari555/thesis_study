# Memory — 2026-10-04: Literature Consolidation, Deep Reads, Zotero Import, Proposal Skeleton

**Session goal:** execute `todo.md` (post-corpus-audit plan). Everything below was done this session and verified on disk.

---

## 1. Literature review rewritten to the current frame

`lit_review/00_thesis_literature_review.md` fully rewritten (was FM-era, recommending the advisor-rejected direction). New structure: exec summary around the CNN-Mamba + SSL + temporal-XAI frame; per-pillar SOTA (concurrent stress / SITS architectures / SSL / CWSI-thermal / salinity / XAI / Khuzestan baselines); GeoAI agents §3.8 frozen as future work; FMs §3.9 ablation-only; gaps G1–G7 aligned with `Thesis_Vault/03-Research-Gaps.md`; new reading order. Old FM-era gaps retired to `phase1_stress_detection_methods.md`.

## 2. Literature-Matrix rows 39–78 added; vault repaired

- Matrix now covers all 78 papers (was 38). Agentic cluster 47–67 rows marked **frozen as background/future-work (decision 2026-10-04)** — do not extend.
- Vault notes 35–38 written (Hornero R²=0.526/0.517, Sanchez-Virosta R²=0.86/0.68/0.70, Bai, Akbari — matrix numbers verified against first pages).
- `00-Thesis-Overview.md` broken references fixed via a pointer table (advisor analysis, Khuzestan summary, memory logs, FM archive all repointed).
- `Thesis_Vault/04-Thesis-Design.md` written (methodology single-source-of-truth): positioning sentence, architecture, 4 phases, label strategy, decisions table (raw bands+LST lean; Barlow Twins lean; Landsat-16d lean; **agents frozen**), validation/XAI protocol, the 4 advisor questions.
- Superseded docs marked: `1.md` (root) and `memory/2026-09-06-initial-findings.md` carry SUPERSEDED banners.

## 3. All 8 P0 papers deep-read (extract → verified) — with claim corrections

Each has a `## Verified Full-Text Findings (2026-10-04)` section + repo-claim verification table in its vault note. **Corrections that change thesis decisions:**

1. **#09 Motlagh** — R²=0.93 is the *full-sample* fit; **independent test R²=0.821** is the honest baseline. No interaction percentages — synergy shown via PDPs (salinity ≈3.4 dS/m + CWSI>0.44 → yield collapse). ECe protocol verified (weekly saturated-paste, 0–90 cm, 128 wells, kriged; 1.7–8.0 dS/m). 336 Amirkabir fields, 2023 season. Own CWSI triggers: young 0.40–0.45, old 0.30–0.35.
2. **#08 Paciolla** — **single 21-ha maize field**, ensemble-KF DA (FEST-EWB-SAFY) of Landsat-8 LAI; **no LAI→EC regression** (salinity enters via FAO K_saltS, EC_LOW=1.7). "Justifies skipping ground ECe" only PARTIAL → advisor question ① (ECe access) is more critical than before.
3. **#70 Wen 2022** — PROSAIL via SNAP biophysical processor; **no per-trait RMSE validation**; two-way ANOVA is stress-class × date (R² 0.326–0.796 verified); stresses from SPEI-3 + groundwater Cl⁻ (no in-situ); drought > salinity; "salinity impacts may have been overstated".
4. **#01 SITSMamba** — **PW is a linear loss re-weighting (1/L→L/L) of the reconstruction MSE, not attention**; **single-stage supervised multi-task, NOT SSL** (matrix claim corrected); PASTIS32 OA 0.7416/mIoU 0.5005; GitHub code diverges from paper (UMamba, possibly incomplete) → reimplementation decision needed; thermal insertion = CNN stem input dim (LST normalize separately).
5. **#04 Höhl** — **"temporal XAI virtually unexplored" is NOT verbatim** (actual p.22: temporal dependencies make XAI "unreliable or inaccurate"; p.24 research call; precedent = Rußwurm [158]). Evaluation claim faithful: >90% anecdotal, 15/207 quantitative, no controlled ground truth. **G2 wording refined everywhere** (lit review, gaps doc, search log).
6. **#07 Angon** — response table verified with p-values; **Ts, proline, ABA were NOT measured** (repo's claimed table overstated); no operational labeling criteria (our ECe+CWSI rule is our own proposal, must be framed as such); no sugarcane; combined "cannot be predicted from single-stress responses" (p.2).
7. **#10/#24/#25 Zoratipour** — threshold 0.4–0.5 verified (#10; conclusions: 0.5 trigger; sensor Apogee SI-411); #24 RF bias correction R² 0.73→0.92 (+20.65%), rMBE −16→−8%; #25 Landsat 0.78–0.92 vs S2 0.74–0.89 (Persian body, 2024 campaign). **Salinity never measured in the whole series** → the disentanglement gap stands.
8. **#14 STS-NET** — 3D-CAE 19.2K params, reconstruction pretext, T=32 @9–11 d; input RGB+NIR+mean-VI PlanetScope ~3 m (**not UAV, not VI-only**); 62 sugarcane fields (UP India, 2023); **97.98/85.08/83.47 are accuracy** (abstract mislabels as precision); combined = 9-class water×nitrogen task; absences verified: no salinity/Mamba/XAI/multi-year. Differentiation paragraph drafted in the note.

## 4. Negative searches documented (auditable)

`deep_researches/search_logs_2026-10-04.md`: 4 dated searches (arXiv + OpenAlex; Semantic Scholar 403). G1 negative confirmed (no Mamba+stress). G3 negative confirmed (no multi-modal optical+thermal SSL for SITS). Core-niche negative confirmed (no DL disentanglement of water×salinity; bonus: Motlagh abstract cross-verified via OpenAlex). **G2 needed refinement: near-neighbor James et al. 2025 (IEEE AsianCON, doi:10.1109/asiancon66527.2025.11281233) combines SimCLR on S2 VI composites + SHAP/Grad-CAM at feature level** — added to `papers_not_downloaded.md` (#64) and G2 evidence; the safe wording is now "no timestep-level XAI for deep SITS stress models, physiologically validated".

## 5. Zotero — corpus imported (hybrid web + local API)

- Write access was already configured (env vars). 7 subcollections created under `Thesis`.
- All **78 items** imported with linked-file PDF attachments. Metadata via Crossref (DOIs) + arXiv batch API (~67 items); 11 manual-flagged items to verify in client (ids 6, 10, 11, 12, 13*, 25, 35, 36, 37, 59†, 77† — *Sapkota DOI 404s on Crossref; † REMSA/Waters arXiv IDs 404).
- **War story:** the web API rate-limited hard; root causes found were (a) Zotero tags must be `[{"tag": …}]` objects, (b) **arXiv IDs contain a dot** so `"." in ident` misrouted every arXiv item to Crossref (404) — the reason arXiv items silently never imported in early runs. Fixed by switching to the Zotero **desktop local API** (`localhost:23119/api/users/0/...`, needs `Zotero-Server-ID` header from any GET response; accepts anonymous writes up to a quota then 401s) with web-API fallback. Scripts: `scripts/zotero_import_2026-10-04.py`, `scripts/zotero_local_finish_2026-10-04.py` (idempotent, dedupe by `Matrix #NN` in `extra`).
- 10-item spot verification printed by the script; titles/authors match sources.

## 6. Proposal skeleton (Persian)

`proposal/draft/00-proposal-skeleton.md` — full section skeleton with the positioning sentence, verified local numbers (test R²=0.821 baseline; PDP synergy; ECe protocol), decisions with leans, and the 4 advisor questions marked ⛔. Word export deferred.

## 7. Housekeeping

`New_papers/` emptied+removed (md5-verified copies); `archived_duplicates/ref-Melanie` deleted (md5 match); `ref-Leveraging` **kept** (checksum differs from canonical #09 — possible version variant, see ARCHIVED_DUPLICATES.md). Intake-doc follow-up boxes ticked.

## Open items → next session

1. Advisor's 4 answers (ECe access ↑priority, Mixed criteria, GPU, timeline).
2. Full reads: 69/71, 44, 72, 60, 77, 11, 12, 76.
3. Verify/fix the 11 manual Zotero items in the client; import legacy link-index papers if wanted.
4. Fetch James 2025 (near-neighbor) PDF.
5. Crossref/OpenAlex second pass on "state space model"+"crop stress" before proposal submission.
6. Excel export of the Literature-Matrix (advisor request).

---
*Logged 2026-10-04. All file claims verified on disk this session.*

---

## 6. Second pass (same day): all 9 second-tier papers deep-read → verified

Trigger: user asked to "continue to read-deep more papers that are more valid and cited". Candidates ranked by OpenAlex citations: **Berger #44 (290) > Paul #60 (88, DOI 10.1016/j.compag.2024.109734) > Wen21 #69 (77) > Wen23 #71 (19) > Hajeb #11 (16) > Haq #72 (14) > Waters #77 (published: CEA 229:109686) > Motlagh-Ky #76 (0, too new)**. Five reads ran as background agents; the last four after subagent quota ran out — finished by direct pypdf text extraction + targeted mining (agents: Berger, Paul, Wen21, Wen23, Hajeb; self-read: Haq, Waters, Ky, Malee).

### Load-bearing outcomes

1. **#60 Paul (CEA 229:109734)** — PRISMA 163 studies: SSL = 1 subsection / 3 studies (all leaf/canopy proximal; no satellite/thermal/temporal SSL; no SSL-algorithm taxonomy; Conclusion drops SSL) → **G3 now has a citable quantitative anchor**; **Mamba/SSM entirely absent** (no prior-art conflict); salinity ≈2/163 (our tally); overlapping-stress remedy = "others" class (avoidance, not disentanglement); color-jitter degraded SSL pretraining (p.18) → Barlow Twins augmentation guidance. Note: `Thesis_Vault/papers/60-Paul-2025-DL-Plant-Stress-Review.md`.
2. **#69 Wen 2021 (RS 13:6)** — all three problem-statement quotes **verbatim**; title ends "…Drought **Threats**"; "traits better" overstated (osmotic traits standout but In-RS only); "significantly limiting" is **abstract-only**; **zero VI–salinity correlations in the corpus (p.4)**; no ML anywhere; NDVI deliberately excluded. Note: `papers/69-Wen-2021-Salinity-Drought-RS-Challenges.md`.
3. **#71 Wen 2023 (IJAEOG 122:103438)** — pairwise matched-control design (1-km cells, 30-km buffer); combined>individual (exceptions: almond, sorghum); trait sequencing LAI→FVC/FAPAR→Cw/Cab = **testable XAI hypothesis**; **no ML, no accuracy metrics, proxy labels (SPEI-3 + static gNATSGO EC), single 2021 season**; claims "quantitative foundation for simultaneously assessing" → **G4 reworded everywhere**: per-field *disentanglement* + predictive DL + XAI is our niche, NOT "simultaneous monitoring never done" (positioning rule strengthened in lit review + 03-Research-Gaps + 04-Design). Note: `papers/71-Wen-2023-Crop-Salinity-Drought-US.md`.
4. **#44 Berger (RSE 280:113198, ~290 cites)** — rewordings required: their 96-study corpus **excludes single-sensor studies by design** (real claims: "compare not fuse" + 72% parametric); "temporal phase under-exploited" not their wording; **"no concept exists that uses multiple spectral domains in an integrated way … to differentiate between crop stress types" (p.3)** = flagship G4 quote; DL "still missing" (p.11); **zero XAI**; **VIS+NIR+SWIR+TIR = exactly our Landsat 8/9 combo — only 12/96 studies**; salinity 5.0% never synthesized; "hybrid" = RTM+ML (not SSL). Note: `papers/44-Berger-2022-Optical-Stress-Synergies.md`.
5. **#11 Hajeb (IJAEOG 116:103168)** — same study area confirmed (Amir Kabir, ~400 fields implied, never states count); **136 ESUs (not fields)**; LAI RMSE 0.48 = simultaneous median; **LSM (plant-water proxy) to 2.91% RRMSE** — water signal learnable here; simultaneous>individual = authors' own "marginal gain"; **Kcb claim confirmed absent** (was mis-attributed from #12); zero salinity/stress measurement; ground-protocol template (destructive LAI, SPAD+Markwell, Kjeldahl, sheath FW/DW). Note: `papers/11-Hajeb-2023-S2-Retrieval.md`.
6. **#12 Malee (AWM 333:110529)** — REAL paper recovered from `archived_duplicates/` (mis-file saga: the PDF at papers/12-*.pdf was the Ky paper #76; see ARCHIVED_DUPLICATES.md). Thailand (Aw), KK3, 2 weighing lysimeters, SIMDualKc-calibrated **Kcb 0.15/1.11/0.49**, AquaCrop scenarios: **25–50% MAD maintain competitive yields**; ET ~equal under deficit (11,680 vs 11,708 m³/ha) → Water_Only class must accommodate *planned* deficit. Note: `papers/12-Malee-2026-Kcb-DeficitIrrigation.md`.
7. **#76 Motlagh-Ky (AWM 330:110260)** — all extract numbers verified (Ky 1.05 vs FAO-66 1.2; range 0.2–1.63; early-July peak Ky>1.82; LST RF correction; CWSI RMSE 0.05; 12 field points; dekadal scale); **author's own confound warning: "salinity stress that also affect[s] canopy temperature could potentially confound interpretation"** — citable motivation for disentanglement over CWSI-only pipelines. Note: `papers/76-Motlagh-2026-Ky-Derivation.md`.
8. **#72 Haq (SAT 12:101583)** — 138 records/47 setups/12 crops; **viewing geometry "significantly affects" NDVI/PRI/SIF → BRDF correction before temporal stacking = protocol MUST**; **BRDF anisotropy signatures differ by stress type** (water: forward-scattering ↑) → angular features as candidate disentanglement signal; physics-aware AI agenda. Note: `papers/72-Haq-2025-MultiDim-Optical-Stress.md`.
9. **#77 Waters (CEA 229:109686, 2025 — arXiv preprint read; published version verified via arXiv API)** — **ZERO salinity mentions in the sugarcane-specific review** (completes the 4-way salinity-neglect chain: Waters 0 / Paul 2/163 / Berger 5% / Wen21 zero-correlations); ~1 study uses time series; DL named *future* work; **"other moisture-based vegetation indices should be heavily considered"** → SWIR water indices into our feature set; BRDF/consistent-viewing-geometry recommendation. Note: `papers/77-Waters-2025-Sugarcane-Health-Review.md`.

### Docs updated in the second pass

Matrix rows 11/12/44/60/69/71/72/76/77 (all ✅ Full read with corrections); lit review §3.1 (Wen trilogy bullets + Berger bullet + strengthened positioning rule), §3.3 (Paul SSL anchor), §3.7 (Hajeb verified + Malee Thailand fix), reading-order item 12 closed; `03-Research-Gaps.md` G3 (Paul evidence + jitter guidance) and G4 (Berger p.3 quote + Wen-trilogy caveat + counter-warning); `04-Thesis-Design.md` Phase-1 row (geometry-aware compositing, moisture indices, angular features); `ARCHIVED_DUPLICATES.md` (mis-file resolution); `papers_not_downloaded.md` unchanged (Malee recovered — no browser fetch needed).

### Zotero fixes (web API PATCH, scripts in scripts/)

`zotero_fix_11_12_web.py` (items EQI2E6UV #11 + FRBZ964I #12 patched with Crossref metadata; broken #12 attachment deleted, real Malee PDF re-attached as linked file) and `zotero_fix_59_77_2026-10-04.py` (#59 REMSA = arXiv:2511.17442 verified — import-time 404 was transient; #77 = published CEA 229:109686). **Manual-flag list now: 6, 10, 13, 25, 35, 36, 37 (7 remaining).**

### Remaining for the corpus

- 78/Virnodkar stays extract-level (pre-2020 anchor). Frozen agentic cluster stays 🆕 by design.
- Advisor 4 answers still gate proposal §methods/§labels; Excel matrix export pending.
