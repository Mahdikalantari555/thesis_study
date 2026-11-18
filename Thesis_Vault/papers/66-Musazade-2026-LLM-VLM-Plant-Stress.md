# 66 — LLMs and VLMs in Plant-Stress Phenotyping: From Trait Recognition to Decision Support (Musazade et al., 2026)

**Full Citation:** Musazade, E., Mrisho, I. I., Gao, J., & Feng, X. (2026). Integration of LLMs and VLMs in plant stress phenotyping: From trait recognition to decision support. *Plant Phenomics*, *8*, 100161. https://doi.org/10.1016/j.plaphe.2025.100161
**DOI:** [10.1016/j.plaphe.2025.100161](https://doi.org/10.1016/j.plaphe.2025.100161) | Open Access (CC BY) | Plant Phenomics 8:100161; accepted 27 Dec 2025, online 29 Dec 2025
**Status:** ✅ Full read (2026-10-20, extracted text — applications, challenges, future directions, conclusion)
**Themes:** #Review #Agentic-RS #Stress-physiology

---

## What It Does

A critical narrative review of how **large language models (LLMs)** and **vision-language models (VLMs)** are applied to plant-stress phenotyping, from visual trait recognition through knowledge extraction to decision support. The authors argue that VLM visual recognition plus LLM semantic reasoning plus **RAG** grounding form a path to scalable, explainable, farmer-facing phenotyping, and close by proposing a forward-looking framework fusing LLMs, VLMs, knowledge graphs and multimodal sensor data (p. 1, p. 11). It is presented as "one of the first comprehensive reviews on this topic" (p. 1).

## Corpus & Scope

- **Type:** narrative / critical **review article** — *not* a PRISMA systematic review. The extracted text reports **no search protocol, database list, search string, inclusion/exclusion criteria, study count (n) or year window**; verified by absence across all 17 pages (searches for PRISMA, Web of Science, Scopus, screening and inclusion-criteria language return nothing). This differentiates it from matrix row #60 (Paul et al.), whose n = 163 and 2014–2024 window are explicit — the two reviews must not be cited interchangeably.
- **Evidence base as tabulated:** Table 1 ("Applications of VLMs in plant stress identification and management", pp. 7–8) catalogues primary studies by phenotyping task (image identification and classification → text mining → decision support).
- **Background framing (p. 1):** biotic stresses (pests, pathogens, weeds) cause **17 %–40 %** yield loss; abiotic stresses (drought, extreme temperatures, heavy-metal toxicity, **salinity**) can reduce yields by **up to 50 %**.
- **Model landscape (p. 2):** LLMs (GPT series, PaLM-E, LLaMA) for semantic reasoning and few-shot learning; VLMs pairing an image encoder (CNN, ViT, or "**MAMBA-based**" encoders) with a text encoder; CLIP and GroundingDINO as reference points.

## Key Methodology

### Taxonomy of LLM/VLM roles in phenotyping (Section 4, pp. 5–8)

1. **Image identification and classification (§4.1, p. 5)** — VLM as perception, LLM as verbaliser: ITLMLP on 3,200 cucumber-disease images (4 diseases) → 94.84 % accuracy; YOLOPC on 1,266 citrus images → 94.5 % with 75 % fewer parameters than YOLOv5-nano, with GPT-4 verbalising classifier outputs into diagnostic reports at **90 %** expert-agreement reasoning accuracy; Madaan et al. MobileNetV2/ResNet50 at 97–99 % plus LLM prevention advice; **AgEval** benchmark (12 stress tasks) → Gemini-pro-1.5 best zero-shot (F1 **50.45 %**), GPT-4o best few-shot (F1 **73.37 %**), Claude-3.5-sonnet best at classification/quantification (NMAE **12.78 %**), prompt example relevance worth **+15.38 %**; Lu et al. multimodal transformer (95 % precision / 92 % recall / 94 % accuracy); Hue et al. GPT-4 + Korean registry (1,420 host plants, 37,467 pesticides, 2,462 pathogen cases); Kumar et al. YOLOv8 + GPT-3.5 + RAG for coffee leaf disease.
2. **Text mining (§4.2, pp. 6–7)** — LLM as literature/trait extractor: Slimani et al. drone-imaging review; Zhang et al. trajectory mining for pathogen spread; PhenoBCBERT / PhenoGPT for ontology vocabulary; ChatAgri for agricultural text classification; Zhao et al. LLM + GNN + KG + neural-symbolic reasoning → **94 % precision / 92 % recall / 93 % accuracy**; **PlantDeBERTa** fine-tuned on 142 annotated lentil-stress abstracts → NER macro-F1 **82.69 %**; Dofitas et al. Agricultural-BERT + LLaMA-3.1 + BERT weighted-vote ensemble → 93 % accuracy, BLEU 53.8 %, ROUGE 70/55/61 %.
3. **Decision support systems (§4.3, pp. 7–8)** — LLM as advisor: pest-control decision support scored by GPT-4 as judge, reaching **72 %** accuracy with instruction prompting plus domain thresholds; LLM question-answering advisory platforms for farmers.

### Satellite / remote-sensing coverage — the decisive distinction for the thesis

- **The reviewed evidence is close-range, RGB, organ-level imagery.** The primary studies in §4 work on leaves, seeds, weeds, insects and detached plant organs — greenhouse, lab and field close-range captures — plus UAV/drone imagery (Slimani et al., p. 6) and one proximal hyperspectral example (Feng et al. 2021, rice disease > 88 % accuracy, p. 3).
- **Satellite / EO is not part of the reviewed evidence base**; it appears only as (a) an aspirational input in the general-advantage discussion — "outputs from vision encoders … can be synthesized with satellite imagery, sensor data, and textual field reports" (p. 4); (b) a data-integration problem in the challenges section, where heterogeneous sources "including satellite imagery, IoT sensors, weather data, and farm logs" are said to have incompatible formats that degrade LLM output (pp. 9–10); and (c) an explicit future direction — "the future trajectory of LLM-enhanced remote sensing envisions multimodal fusion frameworks that integrate satellite imagery, in-situ sensor data, and weather forecasts" (p. 11).
- **Corollary:** no study in this review applies an LLM/VLM to multi-temporal **satellite** crop-stress series, and the review reports no EO time-series, thermal or salinity-specific result — salinity appears only as a generic abiotic stressor in the yield-loss framing (p. 1) and in the ensemble generalisation argument (p. 11).

## Key Findings

- **Technical gaps (§5.1, p. 9):** scarce / fragmented domain data, silver-standard annotations, English-centric corpora, compute cost, hallucination (**RAG offered as the mitigation**), catastrophic forgetting (**EWC** proposed), weak handling of agricultural ontologies and taxonomies.
- **Implementation gaps (§5.2, p. 10):** pretrained VLMs see web-scale data and miss fine-grained stress features; proprietary-VLM access barriers; fragmented, format-inconsistent agricultural data with no standard sharing protocols; infrastructure limits; static models failing on unfamiliar crops, regional terminology and emerging stressors.
- **Future directions (§6, pp. 11–13):** (6.1) LLM ensembles + agricultural **knowledge graphs** with graph attention and agronomy-constrained losses (ITK-Net reported at > 99 % precision); (6.2) **AI + IoT at the edge** — hyperspectral imagery, soil moisture, pH and nutrients processed on-site, autonomous drone fleets, satellite-based hyperspectral, LLM-enhanced remote-sensing fusion; (6.3) accessibility, explainability, sustainability.
- **Mamba caveat:** Mamba appears only as a parenthetical in the VLM encoder taxonomy ("CNN, Vision Transformers (ViTs), or MAMBA-based encoders", p. 2) — no Mamba/SSM method section, no temporal modelling, no sequence-model prior art.

## Relevance to Thesis

**Low-Medium** — the closest agriculture-side bridge in the frozen GeoAI-agent cluster (frozen 2026-10-04); background / future-work material only, and no extension of that cluster is proposed:
- ✅ Confirms from an independent review that **RAG grounding is the accepted fix for LLM hallucination** in plant-stress advice, and that VLM perception + LLM verbalisation is the working recipe — framing for any agentic chapter.
- ✅ The AgEval-style result that **few-shot beats zero-shot by a wide margin** (F1 73.37 % vs 50.45 %) and that **prompt example relevance alone buys +15.38 %** — an argument for curated, domain-specific exemplars over generic prompting.
- ✅ Its own statement that the *next* step is LLM-enhanced remote sensing with satellite + in-situ + weather fusion (p. 11) is an independent, citable sign that the EO-scale agentic setting was still open — supporting the thesis's gap claim, not its method.
- ⚠️ Evidence base is close-range RGB/UAV only — **no satellite, thermal or multi-temporal stress study** — so it cannot support the thesis's labels, model or validation design.
- ⚠️ Salinity appears only as a generic stressor in the yield-loss statistic (up to 50 % for abiotic stresses); concurrent water-vs-salinity disentanglement is not addressed.
- ❌ No active learning, no self-supervised learning taxonomy, no foundation-model selection, no XAI methodology.
- ⚠️ The intake note (G20) rated this "Thesis relevance: HIGH" and proposed positioning the thesis at the "EO foundation models + LLM/VLM decision agents + AL for arid stress" intersection; that rating and extension proposal are superseded by the frozen-cluster calibration (Optional / Low-Medium) and are recorded only as a discrepancy.

## Key Takeaway

The most useful fact for the thesis is negative and clean: the LLM/VLM plant-stress phenotyping literature is **overwhelmingly close-range and RGB**, with satellite/EO appearing only as future work — corroborating, from the agentic-AI side, the same scarcity of satellite stress work that matrix rows #60 and #69 established from the DL-review and salinity-vs-drought sides. Cite it as the agentic-AI framing and gap-corroboration paper, never as a method source.

## Links

- Matrix row: #66
- Related: #60 (Paul et al. — PRISMA DL plant-stress review, n = 163; the complementary quantitative review), #67 (CottonBot — RAG + live soil-moisture agent), #69 (Wen et al. 2021 — the "drought and salinity not monitored simultaneously" problem-statement anchor), #64 (GeoAgentic-RAG — the geospatial-side agentic counterpart)

---

*Linked from: [[Literature-Matrix]]*
