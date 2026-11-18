# New Papers Intake â€” 29 PDFs from `D:\RS\Thesis\New_papers`

**Date:** 2026-09-10  
**Task:** Read all papers in `New_papers/` (Agentic + Agricultural), summarize each, and synthesize for the thesis redesign.

**Thesis frame:** *Disentanglement and explainability of concurrent waterâ€“salinity stress using Mamba + SSL (+ temporal XAI) on multi-year Landsat/HLS in salinity-affected sugarcane (Khuzestan, Iran), with optional GeoAI agent orchestration.*

**Source PDFs:** local only (not committed).  
**Extracts:** `deep_researches/new_papers_2026-09-10_extract/` (first ~4 pages per PDF).  
**Per-paper notes:** `deep_researches/new_papers_notes/` (one `.md` per paper).  
**Scope note:** Metadata and quantitative results are taken only from extracted text; fields beyond the extract window are marked unknown. No invented citations.

---

## 1. Executive summary

This intake covers **29 papers** in two intentional piles:

| Folder | n | Role in thesis |
|--------|---|----------------|
| **Agricultural** | 8 | Physiology, optical/TIR stress RS, CWSI, salinity mapping â€” methods and gap motivation for concurrent-stress disentanglement |
| **Agentic** | 21 | LLM/agent/RS-FM workflows, plant-stress phenotyping with LLMs/VLMs, tool-use benchmarks, irrigation RS hydrology |

### Headline conclusions

1. **The concurrent-stress gap is still open.** Berger et al. (2022, RSE), Gerhards et al. (2019), Shen et al. (2025), and Smanov et al. (2026) all document that optical/TIR stress RS remains largely **single-stress / single-source / single-index**. None operationalize deep temporal disentanglement of water Ã— salinity on multi-year satellite time series.
2. **Physiology still forces a Mixed class.** Angon et al. (2022; advisor paper #7 â€” **duplicate in this folder**) + Feller & Vaseva (2014) + Tardieu et al. (2018) show combined stress is interactive, scenario-dependent, and confounded by heat. Labels should support mixtures, not only hard single classes.
3. **CWSI and thermal physics remain the water-deficit backbone.** Maes & Steppe (2012) is the canonical ground-thermal/CWSI reference; Gerhards et al. (2019) and Berger et al. (2022) argue multi-sensor synergy is required under mixed stress. Satellite thermal at Landsat scale is usable as auxiliary/validated features, not a free lunch.
4. **Smanov et al. (2026) is the closest salinity-RS conceptual match:** crop salt tolerance mediates spectralâ€“ECe relationships; ion composition and phenology are ignored in most models â€” exactly the confounders Khuzestan sugarcane will face.
5. **The agentic RS stack matured rapidly (2024â€“2026).** RS-Agent (task planning + DualRAG), Earth-Agent-Pro (full-chain open-world EO), RSMeM (failure-aware memory), REMSA (RSFM selection over >160 models), ThinkGeo / GeoMMBench / Earth-Bench-Pro (evaluation), and Munir et al.â€™s position paper on EO-native agents form a coherent systems literature.
6. **Closest agri-agent bridge to crop stress:** AgriWorld (verifiable RS time-series + stress/yield tools + what-if irrigation), CottonBot (RAG + live soil-moisture tools), Musazade et al. (LLM/VLM/RAG plant-stress phenotyping review), Paul et al. (DL plant-stress survey with SSL/FSL under label scarcity).
7. **Irrigation RS hydrology is complementary, not central:** Zhang et al. (2026 AWM) and Khamseh & Danesh-Yazdi (2026 AWM) provide pixel-wise IWU and ET-resolution uncertainty useful as covariates and data-quality design notes for arid irrigation systems (Arizona / China â€” analogs, not Khuzestan).
8. **No paper in this set trains CNN-Mamba + SSL + temporal XAI on HLS/Landsat for concurrent waterâ€“salinity stress in sugarcane.** That remains the thesis niche; this intake strengthens related-work framing and agent-side options rather than closing the core gap.

### One-line ranked â€œmust-citeâ€ shortlist (this folder)

| Rank | Paper | Why |
|------|-------|-----|
| 1 | Berger et al. 2022 (RSE) | Optical multi-sensor stress RS state-of-art + synergy gap |
| 2 | Smanov et al. 2026 (RS) | Salinity Ã— irrigated arid + crop-physiology mediation |
| 3 | REMSA (Chen et al. 2026) | Constraint-aware RSFM selection agent |
| 4 | RS-Agent (Xu et al.) | Canonical agentic RS baseline |
| 5 | Earth-Agent-Pro (Lv et al. 2026) | Full-chain EO agents + Agriculture & Drought domain |
| 6 | Munir et al. 2026 (Agentic AI for RS) | Why generic agents fail on geospatial state |
| 7 | Gerhards et al. 2019 (RS) | Water-stress TIR physics + multi-stress confounding |
| 8 | Maes & Steppe 2012 (JXB) | CWSI / ground thermal validation design |
| 9 | Musazade et al. 2026 (Plant Phenomics) | LLM/VLM/RAG for plant stress phenotyping |
| 10 | AgriWorld (Zhang et al. 2026) | Verifiable agri/RS reasoning with stress tools |
| 11 | RSMeM (Wu et al. 2026) | Failure-aware agent memory (AL-adjacent) |
| 12 | Paul et al. 2025 (CEA) | DL plant-stress + SSL/FSL review |
| â€” | Angon et al. 2022 | **Already advisor #7** â€” do not double-count |

---

## 2. Inventory (file â†’ paper)

### Agricultural (8)

| # | Local file | Paper (short) | Year | Venue | Note file |
|---|------------|---------------|------|-------|-----------|
| A1 | `ers165.pdf` | Maes & Steppe â€” ground thermal ET/drought/CWSI review | 2012 | *J. Exp. Bot.* | `A1-Maes-2012-CWSI-ground-thermal.md` |
| A2 | `fenvs-02-00039.pdf` | Feller & Vaseva â€” drought + heat physiology | 2014 | *Front. Environ. Sci.* | `A2-Feller-2014-drought-heat-physiology.md` |
| A3 | `annurev-arplant-042817-040218.pdf` | Tardieu et al. â€” scenario-dependent drought tolerance | 2018 | *Annu. Rev. Plant Biol.* | `A3-Tardieu-2018-drought-probabilistic.md` |
| A4 | `remotesensing-11-01240.pdf` | Gerhards et al. â€” multi/hyperspectral TIR water stress | 2019 | *Remote Sensing* | `A4-Gerhards-2019-TIR-water-stress.md` |
| A5 | `plants-11-02884.pdf` | Angon et al. â€” combined drought+salinity meta-analysis | 2022 | *Plants* | `A5-Angon-2022-combined-stress-DUP.md` |
| A6 | `1-s2.0-S003442572200308X-main.pdf` | Berger et al. â€” multi-sensor optical stress synergies | 2022 | *Remote Sens. Environ.* | `A6-Berger-2022-optical-stress-synergies.md` |
| A7 | `Stress Detection.pdf` | Shen et al. â€” broadacre RS resilience methodological review | 2025 | *Remote Sensing* | `A7-Shen-2025-broadacre-resilience.md` |
| A8 | `remotesensing-18-01420-v2.pdf` | Smanov et al. â€” crop salt tolerance Ã— RS salinity mapping | 2026 | *Remote Sensing* | `A8-Smanov-2026-salt-tolerance-salinity-RS.md` |

### Agentic (21)

| # | Local file | Paper (short) | Year | Venue | Note file |
|---|------------|---------------|------|-------|-----------|
| G1 | `RS-Agent Automating Remote Sensing Tasks through Intelligent Agent.pdf` | RS-Agent | 2024â€“26 | *Sci. China Inf. Sci.* / arXiv | `G1-RS-Agent.md` |
| G2 | `2505.23752v3.pdf` | ThinkGeo â€” tool-augmented RS agents benchmark | 2025â€“26 | arXiv | `G2-ThinkGeo.md` |
| G3 | `2601.01891v1.pdf` | Talemi et al. â€” Agentic AI in RS survey | 2026 | arXiv | `G3-Talemi-2026-agentic-RS-survey.md` |
| G4 | `2602.15325v1.pdf` | AgriWorld / Agro-Reflective | 2026 | arXiv | `G4-AgriWorld.md` |
| G5 | `2604.08896v1.pdf` | GeoMMBench + GeoMMAgent | 2026 | arXiv | `G5-GeoMMBench-GeoMMAgent.md` |
| G6 | `2606.07538v1.pdf` | BSCTR â€” tool retrieval for RS agents | 2026 | arXiv | `G6-BSCTR-tool-retrieval.md` |
| G7 | `2607.24772v2.pdf` | RSMeM â€” memory evolution for RS agents | 2026 | arXiv | `G7-RSMeM-memory-evolution.md` |
| G8 | `2609.12533v1.pdf` | Earth-Agent-Pro + Earth-Bench-Pro | 2026 | arXiv | `G8-Earth-Agent-Pro.md` |
| G9 | `A Survey of Large Language Model-Powered Spatial Intelligence Across Scales....pdf` | LLM spatial intelligence survey | 2025 | arXiv | `G9-spatial-intelligence-survey.md` |
| G10 | `Agentic AI for Remote Sensing Technical Challenges and Research Directions.pdf` | Munir et al. â€” position paper | 2026 | arXiv | `G10-Munir-2026-agentic-AI-RS-position.md` |
| G11 | `An LLM-based multi-agent system for remote sensing analysis.pdf` | ExpertsRS | 2026 | *Big Earth Data* | `G11-ExpertsRS.md` |
| G12 | `GeoArbiter Verifiability-Guided Grounding for Remote-Sensing Multimodal LLMs.pdf` | GeoArbiter | 2026 | arXiv | `G12-GeoArbiter.md` |
| G13 | `REMSA Foundation Model Selection for Remote Sensing via a Constraint-Aware Agent.pdf` | REMSA + RS-FMD | 2025â€“26 | arXiv | `G13-REMSA-foundation-model-selection.md` |
| G14 | `1-s2.0-S0168169924011256-main.pdf` | Paul et al. â€” DL plant stress detection review | 2025 | *Comput. Electron. Agric.* | `G14-Paul-2025-DL-plant-stress.md` |
| G15 | `1-s2.0-S0378377425007917-main.pdf` | Zhang et al. â€” pixel-wise IWU framework | 2026 | *Agric. Water Manage.* | `G15-Zhang-2026-pixel-IWU.md` |
| G16 | `1-s2.0-S0378377426003252-main.pdf` | Khamseh & Danesh-Yazdi â€” IWU uncertainty | 2026 | *Agric. Water Manage.* | `G16-Khamseh-2026-IWU-uncertainty.md` |
| G17 | `1-s2.0-S1110866526001428-main.pdf` | Sun et al. â€” need-driven self-evolution RS agents | 2026 | *Egypt. Inform. J.* | `G17-Sun-2026-self-evolution-agents.md` |
| G18 | `1-s2.0-S1569843226001111-main.pdf` | GeoAgentic-RAG | 2026 | *IJAEOG* | `G18-GeoAgentic-RAG.md` |
| G19 | `1-s2.0-S2590123025033973-main.pdf` | Tariq et al. â€” edge agentic smart agriculture | 2025 | *Results Eng.* | `G19-Tariq-2025-edge-agentic-agriculture.md` |
| G20 | `1-s2.0-S2643651525001670-main.pdf` | Musazade et al. â€” LLM/VLM plant stress phenotyping | 2026 | *Plant Phenomics* | `G20-Musazade-2026-LLM-VLM-phenotyping.md` |
| G21 | `1-s2.0-S2772375525008718-main.pdf` | CottonBot | 2025 | *Smart Agric. Technol.* | `G21-CottonBot.md` |

---

## 3. Agricultural synthesis (methods + gap)

### 3.1 What the stack argues together

```
Physiology (Angon, Feller, Tardieu)
        â”‚
        â–¼  mixed stress â‰  sum of single stresses
Spectral / thermal proxies (Maes&Steppe, Gerhards, Berger, Shen)
        â”‚
        â–¼  single-index CWSI/NDVI fails under co-occurrence
Salinity-specific mediation (Smanov)
        â”‚
        â–¼  crop tolerance, ions, phenology, root zone ignored
Thesis opportunity
```

**Shared claims**

- **Non-additivity:** Combined drought+salinity is worse and differently structured than either alone (Angon). Heat can reverse or confound stomatal signatures (Feller).
- **Scenario dependence:** Trait expression depends on mild vs severe deficit and organ-level hydraulics (Tardieu) â†’ hard global classes are fragile; probabilistic/mixture labels are safer.
- **Proxy incompleteness:** Thermal (CWSI) tracks canopy water status but cannot alone separate osmotic (salinity) vs hydraulic (drought) stress (Maes & Steppe; Gerhards).
- **Integration still rare:** Bergerâ€™s 96-study optical review and Shenâ€™s broadacre review both find multi-sensor / multi-response designs under-used; specificity remains limited.

### 3.2 What to adopt methodologically

| Idea | Source | Thesis use |
|------|--------|------------|
| Shared-vs-unique stress response map (gsâ†“, Tsâ†‘, Naâºâ†‘, ROS, chlorophyllâ†“) | Angon + Gerhards + Feller | Prior for disentanglement heads; XAI validation checklist |
| Ground CWSI / CTD as external validator | Maes & Steppe (+ Zoratipour Khuzestan series already in repo) | Check that model â€œwaterâ€ branch is physically plausible |
| Crop salt-tolerance thresholds as covariates | Smanov | Label construction; transferability strata across fields/years |
| Soft / mixture labels | Tardieu | Concurrent-stress training targets |
| Multi-domain SSL design (multi-index sequences, not per-index models) | Berger | SSL pretraining structure even if thermal is sparse |
| Ion-composition limitation | Smanov | Threats-to-validity section for remote salinity vs drought separation |
| Heat as co-stressor covariate | Feller | Meteorological drivers in labels and agent tool inputs |

### 3.3 Gaps still open after this pile

- No Mamba / SSL foundation model / temporal XAI in any Agricultural extract.
- No sugarcane-specific deep temporal stress disentanglement.
- No operational concurrent waterâ€“salinity classification at satellite scale.

---

## 4. Agentic synthesis (systems + gap)

### 4.1 Taxonomy of this pile

| Cluster | Papers | Thesis relevance |
|---------|--------|------------------|
| **Canonical RS agents** | RS-Agent, ExpertsRS, GeoAgentic-RAG, Earth-Agent-Pro | Architectural templates for a crop-stress GeoAI layer |
| **Foundation model selection** | REMSA (+ RS-FMD) | Choose Prithvi / CROMA / SatMAE / Galileo / etc. under modality & compute constraints |
| **Memory / continual improvement** | RSMeM, Sun self-evolution | Failure-aware loops â‰ˆ active-learning style refinement without continuous human labels |
| **Trust & grounding** | GeoArbiter, BSCTR | Hallucination control; tool retrieval in long RS tool chains |
| **Benchmarks** | ThinkGeo, GeoMMBench, Earth-Bench-Pro, AgroBench (in AgriWorld) | Evaluation protocols beyond free-form text |
| **Surveys / position** | Munir et al., Talemi et al., Spatial Intelligence survey, Musazade, Paul | Related-work backbone |
| **Agriculture-specific agents** | AgriWorld, CottonBot, Tariq edge ag | Closest end-to-end agri deployments |
| **Irrigation RS hydrology** | Zhang IWU, Khamseh IWU uncertainty | Environmental covariates; ET product resolution lessons |

### 4.2 Design principles worth importing (Munir et al. + peers)

1. **Geospatial state must be structured** â€” CRS, resolution, valid-time are first-class; silent reprojection/compositing errors are the main agent failure mode in EO.
2. **Tool chains are coupled** â€” atmospheric correction â†’ geometry â†’ indices â†’ model adapters need dependency-aware retrieval (BSCTR).
3. **Trajectory quality â‰  final answer** â€” ThinkGeo / Earth-Bench-Pro evaluate step-wise tool use; thesis agent eval should log plans, not only stress maps.
4. **Verifiability before fluency** â€” GeoArbiter: inject only facts the image cannot check; withhold conflicting inventories. For stress: weather/soil DBs are tools, not free hallucinated context.
5. **RSFM selection is a product problem** â€” REMSA shows free-text constraints â†’ schema-grounded ranking; thesis can cite this when justifying FM choice methodology (not only GEO-Bench scores).

### 4.3 Where agents fit the thesis (optional Chapter / future work)

The **core scientific contribution** remains CNN-Mamba + SSL + temporal XAI for concurrent stress. Agents can sit as:

- **Lab assistant:** RS-Agent / Earth-Agent-Pro-style pipeline to fetch HLS, run indices, package model inputs.
- **Active-learning coordinator:** RSMeM-style failure memory + human-in-the-loop label queue.
- **Decision support:** CottonBot / AgriWorld-style RAG over agronomic guides + live CWSI/sensor tools for irrigation advice after stress maps exist.
- **FM librarian:** REMSA-style selection among EO-FMs for the frozen multi-temporal encoder ablation.

None of these replace the disentanglement model; they operationalize it.

### 4.4 Gaps still open after this pile

- Almost no agentic system couples **EO FMs + active learning + temporal XAI + multi-stress crop labels**.
- Agentic RS remains dominated by urban/disaster/GIS QA; **arid irrigated crop stress** is rare.
- Mamba appears in reviews (Musazade) as encoder option, not as a deployed stress agent backbone.

---

## 5. Cross-pile synthesis â†’ thesis positioning

### 5.1 What strengthens the current redesign

| Thesis element | Support from this intake |
|----------------|--------------------------|
| Mixed / concurrent stress class | Angon (DUP), Feller, Tardieu, Berger, Gerhards |
| Water-deficit backbone | Maes & Steppe, Gerhards, Zoratipour (already in repo) |
| Salinity confounders | Smanov (ions, phenology, crop tolerance) |
| Label efficiency / SSL | Paul, Musazade, Berger (hybrid ML need) |
| Multi-year temporal models | Berger (time-series stress phase), Tardieu (multi-scale feedbacks) |
| Optional GeoAI agents | RS-Agent â†’ Earth-Agent-Pro â†’ RSMeM â†’ REMSA â†’ AgriWorld / CottonBot |
| Data quality in arid irrigation RS | Khamseh (ET resolution bias), Zhang (IWU ensemble) |

### 5.2 What does **not** change

- Do not re-intake Angon as new (already advisor #7).
- Do not treat irrigation IWU papers as stress-detection methods.
- Do not let agentic surveys dilute the scientific core: concurrent-stress disentanglement on SITS remains the novelty claim.

### 5.3 Recommended insertion into existing repo files

| File | Action |
|------|--------|
| `lit_review/00_paper_links.md` | Append sections: Optical/TIR stress RS; Agentic RS; Agri agents; Irrigation RS hydrology |
| `lit_review/00_thesis_literature_review.md` | Later: fold Berger/Smanov/Gerhards/Maes into stress-methods sections; Munir/RS-Agent/REMSA into GeoAI-agent section |
| `deep_researches/advisor_papers_analysis.md` | Note A5 = paper #7 duplicate (optional pointer) |
| `memory/` | New log `2026-09-10-new-papers-intake.md` (this intake) |
| `papers/` | Optional: copy PDFs locally; **do not commit** |

---

## 6. Methods of this intake

1. Enumerated 29 PDFs under `New_papers/Agentic` and `New_papers/Agricultural`.
2. Extracted first ~4 pages + PDF metadata via `scripts/extract_new_papers.py` (pypdf).
3. Three parallel literature agents produced structured entries (APA fields, contribution, architecture, quantitative results visible in extract, relevance).
4. Main agent synthesized themes, ranked papers, and wrote per-paper notes + this document.

**Limitations**

- Many quantitative tables sit beyond page 4; marked unknown.
- Elsevier filename PII mapping for Agricultural A6/A7 assumed from venue/DOI fit; verify if needed before formal citation tables.
- `ers165.pdf` extract may concatenate an unrelated first-page fragment; cite only Maes & Steppe DOI `10.1093/jxb/ers165`.

---

## 7. Outstanding follow-ups

- [ ] Re-read full PDFs for Berger, Smanov, REMSA, RS-Agent, Earth-Agent-Pro when writing formal literature-matrix rows. → matrix rows 44/46/59/47/54 written 2026-10-04 (extract-level); **full reads still pending** (not in P0 queue)
- [x] Promote Berger 2022 + Smanov 2026 into `lit_review/00_thesis_literature_review.md` stress and salinity sections. → done in the 2026-10-04 rewrite (§3.1, §3.5)
- [x] Decide whether GeoAI agents are core methods or future-work chapter. → **decided 2026-10-04: future-work/optional chapter; cluster 47–67 frozen** (`Thesis_Vault/04-Thesis-Design.md` §5)
- [x] Copy high-priority PDFs into `papers/` (local) and add URLs to `00_paper_links.md`. → done (corpus complete 01–78 on 2026-10-04)
- [x] Keep Angon only once in knowledge base. → canonical copy `papers/07` (slot 43 refilled with Wang 2021)

---

*Last updated: 2026-09-10*  
*Companion notes: `deep_researches/new_papers_notes/`*  
*Extracts: `deep_researches/new_papers_2026-09-10_extract/`*

