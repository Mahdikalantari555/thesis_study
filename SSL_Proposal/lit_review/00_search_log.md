# 00 — Search Log (auditable)

**Review:** Deep SSL literature review for satellite image time series → vegetation stress / anomaly detection.
**Search date:** 2026-10-24 (single-day campaign; coverage = literature available up to this date).
**Output dir:** `SSL_Proposal/lit_review/` (files 01–08; this log is 00).
**Deliverables:** 01 foundations · 02 RS SSL · 03 SITS SSL (primary) · 04 agriculture/stress · 05 evidence matrix (84 rows) · 06 gaps · 07 BibTeX (~75 entries) · 08 synthesis.

---

## 1. Search plan (executed)

| Phase | Areas | Sources used | Outcome |
|---|---|---|---|
| P0 pilot | all | alphaXiv `discover_papers` (2×2 topics), local corpus (79 PDFs), existing `SSL_Proposal/literature_review_ssl.md` seeds | pilot set of ~35 papers confirmed relevant; expanded to 84 |
| P1 expand | A1+A2 | arXiv export API batch ID verification (33 IDs), OpenAlex title queries, alphaXiv PDF reads | canonical CV-SSL + RS-FM set verified; 13 wrong ID guesses corrected |
| P2 expand | A3 | arXiv author/title search (rounds 1–4), OpenAlex, alphaXiv PDF reads (Galileo, T-JEPA) | temporal-SSL cluster saturated for 2020–2026 |
| P3 expand | A4 | local corpus mining (pypdf, 22 PDFs), alphaXiv discovery, OpenAlex | direct vs indirect evidence separated |
| P4 verify | key papers | local pypdf extraction (11 SSL PDFs + corpus), alphaXiv `answer_pdf_queries` (8 full-text deep reads: SeCo, SSL4EO-S12, SatMAE, CROMA, Galileo, T-JEPA, AnomalyBERT, Chang et al.) | quantitative claims anchored to tables/sections |
| P5 synthesize | all | CSV built programmatically (`_build_matrix.py`); bib hand-verified | deliverables 01–08 |

**Targeted queries run** (task spec list, all executed via alphaXiv discovery / arXiv API / OpenAlex in equivalent form):
1. "self-supervised learning" + "satellite image time series" ✓ (discovery, 15 hits)
2. "self-supervised" + anomaly + crop stress/vegetation ✓ (discovery, 15 hits)
3. masked modeling + RS foundation models + Sentinel-2 ✓ (discovery, 15 hits)
4. SSL + time series + anomaly detection ✓ (discovery, 15 hits)
5. "self-supervised" + Sentinel-2 + agriculture — via arXiv `abs` queries (crop-stress-ssl, kNN-crop, drought-ssl-sits)
6. "Earth observation foundation model" + temporal — via discovery + Galileo/T-JEPA/Prithvi reads
7. "vegetation stress" + representation learning — via discovery B + arXiv abs:"crop stress"
8. "drought detection" + self-supervised — arXiv abs query returned 0 SITS-SSL hits (a finding in itself → gap G2)
9. "Landsat time series" + self-supervised — SSL4EO-L found; no temporal-SSL-on-Landsat paper found (gap G2 support)
10. Backward chasing: from SeCo/SatMAE/SSL4EO references in full texts (GASSL, CACo, data2vec, UTAE identified in-text)
11. Forward chasing: bounded — via alphaXiv ranked recency (2025–2026 papers citing the cluster) + "related work" sections of 2026 preprints (T-JEPA cites Prithvi-EO-2.0, Sat-JEPA-Diff, SeaMo; Galileo benchmarks 12 FMs). Not an exhaustive citation graph (S2 API was unavailable; OpenAlex `cites:` filter not exercised).

## 2. Query log (verbatim)

- `discover_papers`: ["self-supervised learning","satellite image time series","temporal pretraining"] → 15 results
- `discover_papers`: ["self-supervised learning","anomaly detection","crop stress","vegetation"] → 15 results
- `discover_papers`: ["masked image modeling","remote sensing","foundation model","Sentinel-2"] → 15 results
- `discover_papers`: ["self-supervised learning","time series","anomaly detection"] → 15 results
- `search_papers` (semantic): 4 canonical titles → 0 results (S2 connector down; switched to OpenAlex/arXiv)
- `search_papers` (openalex): "Bootstrap your own latent…" ✓; "Seasonal Contrast…" (noisy); "SITS-Former…" ✓ (JAG DOI found); TSViT/PANOPTIC/CropHarvest/DeCUR/GASSL batches — mixed precision
- arXiv export API: `id_list` batch of 33 IDs (13 mismatches caught & corrected); title/author search rounds: TSViT/CROMA/SITS-Former/AnySat/U-TAE/PSE/SwAV/TS-TCC/SimMTM/MMEarth/OmniSat/Galileo/GASSL/ReSNet/PANOPTIC/CropHarvest; round 3: Tarasiou/SITS-Former/Garnot+Landrieu/CropHarvest-abs/Ayana/DeCUR/kNN-crop/crop-stress-ssl/drought-ssl-sits; round 4: TSViT-pheno/PANOPTIC/GASSL2/DeCUR2/Tseng-dataset; round 5: GASSL(ti)/Agastya/Russwurm-attn/DroughtSet/EigenCL-2506
- WebSearch: CropHarvest (→ NeurIPS 2021 D&B + arXiv:2112.06540), PANOPTIC (→ resolved as U-TAE's module, not a separate paper)
- WebFetch: none needed (alphaXiv page extraction served as full-text access)

## 3. Screening decisions / exclusions

| Item | Decision | Reason |
|---|---|---|
| "PANOPTIC pretraining paper" (my initial seed) | **excluded** | resolved: PANOPTIC is the temporal-attention *module* in Garnot & Landrieu ICCV 2021 (U-TAE); no separate pretraining paper exists — avoided a phantom citation |
| GASSL (initial wrong ID 2101.05968) | corrected to Ayush et al. arXiv:2011.09980 | arXiv title-search verification |
| 12 further guessed IDs (TSViT, CROMA, AnySat, U-TAE, PSE, SwAV, TS-TCC, SimMTM, MMEarth, OmniSat, Galileo, CropHarvest, DOFA) | corrected via search | IDs off by digits or misremembered; all now verified |
| EigenCL arXiv:2506.03394 vs arXiv:2608.25888 | **deduplicated** (same work, short + extended versions, same author Shafqaat Ahmad/Brandt) | local PDF first-page comparison |
| Cheng Wei et al. (Frontiers fpls-16-1576756) | retained **with explicit quality caveat** | multimodal AD topic matches, but generic framing + author background → weak evidence flag (04 §C) |
| Agastya et al. 2021 | retained, venue/arXiv flagged `[not independently verified]` | local PDF is full-text verified; external metadata not found |
| Elbeltagi 2026 (#79) | retained, journal/DOI flagged `[not verified]` | corpus PDF verified; external record not re-checked |
| FLORO, OceanMAE, Arctic FM, Change-Agent, VLM surveys, HLS-GPT, SwissCrop25, VistaFormer, TSINR/PatchTrAD/PaAno/ProtoX-AD/VACE/CARLA/NeuCoReClass AD, MV-Match, electrophysiology water stress, AgroBench, PLANTED, SigMAE-adjacent | **excluded** | out of scope (non-agriculture domains, VLM/agents, hyperspectral proximal sensing) or redundant with retained exemplars of the same family; discovered during searches but not needed for the evidence map |
| ReSNet-kNN crop paper (memory of it) | **excluded** | could not be located with verified metadata in this search; replaced by Chang et al. + EuroCropsML benchmark which carry the same evidential weight with full verification |
| SATLAS / SatlasPretrain | cited only via Chang et al. [FT] | not independently full-read |

## 4. Coverage limitations & selection bias

1. Single-day window; ~84 papers — a map, not a census. Foundational CV papers verified at metadata level only.
2. Google Scholar not directly accessible; approximated with alphaXiv ranking + OpenAlex + arXiv API — may under-sample engineering-journal (MDPI/Elsevier) SSL-for-agriculture work.
3. Semantic Scholar API unavailable during the session; forward-citation sweeps bounded.
4. alphaXiv discovery ranks by community votes+recency → recency bias toward 2024–2026 preprints; older peer-reviewed SITS-SSL (e.g., IR/remote-sensing journal variants) may be under-represented.
5. Non-English literature excluded.
6. 8 full-text deep reads + 15 local full-PDF extractions vs ~60 abstract-level inclusions: quantitative claims in 01–08 are quoted only from [FT] sources; [ABS]/[MO] rows carry no numbers unless from their abstracts.
7. Several bib entries carry `[Author list to be completed]` / `[DOI not verified]` flags — resolved deliberately as UNVERIFIED per AGENTS.md citation rules; complete them before formal proposal use.

## 5. Pilot-set validation (P0 record)

Pilot seeds (9 from the prior stub) all validated and expanded: STS-NET, EigenCL, Time2Agri, MIM-AD, temporal inpainting, Zhang taxonomy, transfer study, Presto, Ruff 2021. Validation criterion (abstract confirms SSL × {RS | SITS | agriculture | AD}) passed for all; metadata verified to the level shown in `05_comparative_evidence_matrix.csv` (evidence_level column).
