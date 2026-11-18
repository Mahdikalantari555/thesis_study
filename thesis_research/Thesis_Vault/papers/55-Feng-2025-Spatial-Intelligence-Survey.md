# 55 — LLM-Powered Spatial Intelligence Across Scales: Embodied, Urban, Earth (Feng et al., 2025)

**Full Citation:** Feng, J., Zeng, J., Long, Q., Chen, H., Zhao, J., Xi, Y., Zhou, Z., Yuan, Y., Wang, S., Zeng, Q., Li, S., Zhang, Y., Lin, Y., Li, T., Ding, J., Gao, C., Xu, F., & Li, Y. (2025). A survey of large language model-powered spatial intelligence across scales: Advances in embodied agents, smart cities, and Earth science. *arXiv preprint arXiv:2504.09848*.
**DOI:** [10.48550/arXiv.2504.09848](https://doi.org/10.48550/arXiv.2504.09848) | arXiv:2504.09848v1 [cs.AI], 14 Apr 2025 | Tsinghua University (BNRist / SIGS) + University of Helsinki | 14 pp. | No peer-reviewed venue stated
**Status:** ✅ Full read (2026-10-20)
**Themes:** #Agentic-RS #Review #Foundation-model #Problem-statement

---

## What It Does

Narrative survey (no new experiments) of **LLM-powered spatial intelligence**, organised along two axes: *scale* (**embodied → urban → Earth**, p. 2, Fig. 1) and *capability* (**spatial memory → spatial understanding → spatial reasoning → spatial intelligence**, p. 1). It (i) reviews human spatial cognition as the design inspiration — cognitive maps and spatial schema (pp. 2–3), (ii) the foundational LLM capabilities — spatial memory/knowledge and abstract spatial reasoning (pp. 3–5), (iii) real-world applications at the three scales (pp. 5–9), then (iv) states per-scale open challenges and the relation to world models (pp. 9–10). The contribution is the **unifying framework and taxonomy**, not empirical results.

## Corpus & Scope

- **Not a systematic review**: no PRISMA protocol, no search string, no inclusion criteria and **no reported corpus count** (grep for PRISMA/systematic-review/search-strategy terms returns nothing). The taxonomy figures are curated, with representative examples named in the captions (p. 3).
- Coverage is 2024–2025 LLM/RS literature (arXiv v1, Apr 2025) plus older EO-ML anchors (GenCast, Pangu-Weather, NowcastNet, Fuxi, p. 9).
- ⚠️ **Discrepancy with intake note G9**: the note rates thesis relevance "Medium"; the matrix row and the frozen-cluster rule both give **Optional** — **Optional** is used here.

## Key Findings — Taxonomy and Framing

- **Two-axis framework** (p. 3, Fig. 2): *foundational capabilities* = {spatial memory & knowledge (internally encoded / externally integrated), abstract spatial reasoning (qualitative, geometric, graph-theoretical)} × *real-world scale* = {embodied, urban, Earth}. Each cell lists representative systems (SpatialVLM, GeoChat, GeoReasoner, TorchSpatial, LLMDiff, GeoGPT, MineAgent, …).
- **Agent-as-spatial-reasoner framing** — the paper does **not** use the phrase "spacetime reasoner"; its own formulation is that embodied spatial intelligence is two sequential stages: **(1) spatial perception and understanding**, where agents acquire spatial information and *construct internal representations of the environment*, and **(2) spatial interaction and navigation**, where those representations are *leveraged for movement, task execution and decision-making* (p. 5, §4.1; schematic Fig. 5, p. 6). For Earth-scale work the survey distils LLM use into exactly two paradigms (p. 9, §4.3.4): **(i) align spatio-temporal features with prompt embeddings** and feed them to the LLM for prediction, and **(ii) design agentic workflows** for complex spatial reasoning.
- **Earth Spatial Intelligence (ESI)** (p. 8, §4.3) spans climate, geography, oceanography and geology, and is framed as uniting "natural language understanding, multimodal integration, and spatio-temporal reasoning". Fig. 7 (p. 8) splits each field into paradigms × tasks — e.g. climate: *"align multi-modal input data for VLM encoding"* and *"incorporate the pretrained transformer layer in LLM for time-series modeling"*; other disciplines: *"align spatial features with LLM input embeddings"* and *"design agentic workflow for complex spatial reasoning"*.
- **Location encoding evidence** (p. 8, §4.3.1, via the TorchSpatial benchmark): **Sphere2Vec-sphereC+** — a self-supervised 3D encoding preserving the order of any two points on Earth — is "the most effective and informative location encoding approach"; even the *lowest*-performing common method, direct tile-ID encoding, **"significantly outperforms GPT-4V"**. The authors read this as *"the discouraging applicability of large language models to explicit spatial learning tasks"*, while noting LLMs excel at few-shot/zero-shot use and multi-source flexibility.
- **Climate anchors** (p. 9): LLMDiff (frozen pre-trained LLM transformer block as universal visual encoder for precipitation nowcasting), CLLMate (LLM+VLM alignment of meteorological rasters), GenCast (15-day probabilistic ensemble forecasts), Pangu-Weather (3-D Earth-specific priors + hierarchical temporal aggregation), NowcastNet (extreme-precipitation nowcasting with lead times up to 3 h), Fuxi (39 years of ECMWF ERA5).
- **Stated open challenges** (pp. 9–10, §5): (i) *fundamental* — is language-based spatial reasoning the right form, or are graph/multimodal representations better? no unified cross-scale evaluation of general spatial intelligence (pp. 9); (ii) *embodied* — cognitive-science inspiration is "often superficial" with no systematic coupling, and it is an open question whether a **universal multi-grained model** can integrate manipulation-level and UAV-path-planning-level spatial intelligence (p. 9); (iii) *urban* — heterogeneous multimodal data not harmonised into unified spatial representations, LLM reliance on static training data, an interpretability gap in urban planning decisions, and three named directions (dynamic spatial modelling, causal spatial reasoning, spatial-bias auditing) (p. 10); (iv) *Earth* — bottlenecks in reasoning-intensive tasks (contextual deduction, advanced spatial analysis), domain-specific data integration and sparsity, plus transfer learning, benchmarking (OceanBench, GeoGPT), **human-in-the-loop and XAI frameworks**, and causal inference (p. 10).
- **World models** (p. 10, §5.5): the survey positions itself on the *representation* function of world models (internal representations to interpret mechanisms) rather than the generative one, and proposes integrating generative world models into spatial intelligence as a route past current foundation models' "lack of granularity in urban knowledge".
- **Conclusion** (p. 10): cross-domain, multi-scale spatial intelligence is forecast as a crucial future research area that will in turn inform AGI.

## Relevance to Thesis

**Optional** — this paper belongs to the **frozen GeoAI-agent cluster** (matrix rows 47–59, 63–67; **cluster frozen 2026-10-04**) and is **background / future-work framing material only**. The cluster is **not** to be extended, and nothing here should be read as a proposal to add further agentic/LLM work to the thesis.

- ✅ Supplies a citable, pre-existing frame for the introduction/related work: crop-stress GeoAI sits in the **Earth-scale branch** of LLM spatial intelligence, with a named progression (memory → understanding → reasoning → intelligence) and a named taxonomy (p. 3, Fig. 2) — preferable to inventing framing vocabulary.
- ✅ Provides the **Earth-scale paradigm vocabulary** (p. 9, §4.3.4) that a thesis "future work / agent layer" paragraph would reuse: align spatio-temporal features with the encoder, or orchestrate tools — with the honest caveat from p. 8 that LLMs are a poor fit for *explicit spatial learning*.
- ✅ The survey's own list of ESI needs — multi-modal alignment, spatio-temporal encoders, benchmarking, XAI and human-in-the-loop (p. 10) — is a citable statement that the *agentic* branch was still open, which is consistent with the thesis scoping its own contribution to the SSL/encoder/XAI branch.
- ⚠️ **No crop-stress content at all**: the Earth-scale examples are climate, geography, oceanography and geology. It cannot support any thesis-specific quantitative claim.
- ⚠️ **No experiments, no reproducible corpus, no reported n** — cite strictly as framing, never as evidence that any approach works.
- ❌ Provides no dataset, no protocol, no label design, no architecture, no metrics and no XAI results usable in the methods chapter.

## Key Takeaway

The most useful thing here is the **two-axis framing** (scale × capability) and the two Earth-scale LLM paradigms (p. 9) — enough to position the thesis's crop-stress work inside an existing, citable taxonomy instead of a bespoke one. The caveat is honest and worth carrying into the text: the survey itself reports that LLMs are poorly suited to explicit spatial learning (p. 8) and that Earth-scale reasoning bottlenecks persist (p. 10), which is an argument for keeping the thesis's load-bearing claims in the SSL / SSM-encoder / XAI branch rather than in an agent branch.

## Links

- Matrix row: #55
- Related: #49 (Talemi et al. — agentic-RS survey, the same cluster's RS-specific taxonomy), #50 (AgriWorld — verifiable agri/RS agents, the closest agri-agent bridge in the cluster), #45 (Shen et al. — broadacre RS resilience review, the domain-side framing to pair with this scale-side framing)

---

*Linked from: [[Literature-Matrix]]*
