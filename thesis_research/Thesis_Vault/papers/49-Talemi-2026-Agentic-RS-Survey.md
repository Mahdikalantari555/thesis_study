# 49 — Agentic AI in Remote Sensing: Foundations, Taxonomy, and Emerging Systems (Talemi et al., 2026)

**Full Citation:** Talemi, N. A., Boone, J., & Afghah, F. (2026). Agentic AI in remote sensing: Foundations, taxonomy, and emerging systems. *arXiv preprint arXiv:2601.01891*. https://arxiv.org/abs/2601.01891
**DOI:** [arXiv:2601.01891](https://arxiv.org/abs/2601.01891) (v1 [cs.CV], stamped 5 Jan 2026) | Clemson University | 8 pp. + supplementary; **no code or data release URL given**
**Status:** ✅ Full read (2026-10-20, extracted text) — **frozen GeoAI-agent cluster**
**Themes:** #Agentic-RS #Review

> **Frozen-cluster statement.** This paper belongs to the **GeoAI-agent cluster, frozen on 2026-10-04** (matrix rows 47–59, 63–67) as **background / future-work material**. The cluster is **not to be extended** by this note.

---

## What It Does

Presented as the **first survey dedicated to agentic AI in remote sensing** (rather than to RS foundation models or MLLMs), the paper organises the field around a four-part ecosystem (Fig. 1, p. 1): **Foundations** (data + VFMs/MLLMs), **Agents** (single-agent vs. multi-agent), **Systems** (RAG, tools, memory), and **Evaluation** (benchmarks for planning and reasoning). It contributes no new experiments — its output is a **unified taxonomy**, a tabulated inventory of RS agents with their applications and benchmarks, a review of the RAG / tool-orchestration / memory stacks, and an explicit list of open problems.

## Corpus & Scope

- **Qualitative literature synthesis** — no new dataset, no new experiments, no meta-analysis with recorded counts. The only quantitative-like artefact is the tabulated inventory below.
- **Taxonomy** (§4, p. 3): **single-agent systems (SA)** vs. **multi-agent systems (MA)**; Fig. 1 words the same split as "single-agent copilots vs. multi-agent orchestrators".
- **Tabulated inventory** (Table 1, p. 5): **23 agentic RS systems** — parsed as **13 single-agent and 10 multi-agent** — each with taxonomy, application, system design, and associated datasets/benchmarks.
- **Application taxonomy** (§4.2, pp. 4–6) — **8 domains**: Earth Observation Assistants; Forest and Ecosystem Monitoring; Climate and Earth System Services; Wildfire and Disaster Monitoring; Urban Change Monitoring; Map Design and Planning; Geological Mapping and Mineral Exploration; Satellite Scheduling and UAV Missions.
- **System stack** (§5, pp. 6–7): 5.1 *Knowledge Representation and RAG* (domain knowledge bases; RAG over documents/exemplars/scripts; graph- and topology-aware retrieval e.g. GeoGraphRAG); 5.2 *Tool Integration and API Orchestration* (monolithic tool ecosystems; domain-specialized planner–executor patterns; memory & long-term coherence).
- **Benchmarks** (§6.1, p. 7), in three groups: *pre-training / instruction-tuning datasets* (RS-VL3M, RemoteCLIP, GeoRSMLLM, LHRS-Bot-Nova, OmniGeo); *geospatial planning & tool-use benchmarks* (GeoLLM-Engine, GeoCode — **19,000 tasks across 28 libraries**; GeoBenchX; GTChain-Eval; GeoTool-GPT; GeoGraphRAG); *reasoning benchmarks* (Earth-Bench, ThinkGeo, GeoChat grounding, LHRS-Bench, RescueADI, ChangeGPT, MineBench, ShapefileGPT, GeoJSON Agents, CORE / ToolEmu).
- **Surveyed model families**: RS VFMs (SatMAE, RingMo, MillionAID, Satlas, RemoteCLIP) and RS MLLMs (GeoChat, LHRS-Bot, RS-LLaVA, SkySenseGPT, RingMoGPT, H2RSVLM, SkyEyeGPT, RSGPT, EarthGPT) (pp. 2–3).

## Key Findings

- **Definition of an agent** (p. 2): *"AI agents are autonomous entities that perceive inputs, reason about tasks, and plan actions to achieve goals. In LLM-centric architectures, an agent combines a planner, a tool interface, and memory within a perception-reasoning-action loop."* Instantiated in RS by RS-Agent, GeoAgent, Change-Agent and MapBot, which "employ LLM controllers to interpret queries and orchestrate tools for classification, segmentation, and map editing".
- **Evaluation paradigm** (§6.2, pp. 7–8): the paper's headline conceptual move is **full-path vs. end-to-end** evaluation. **CORE** formalises full-path checking with Deterministic Finite Automata over valid state graphs to detect forbidden transitions; **Earth-Agent** and **ThinkGeo** use dual-level scoring plus LLM-as-a-Judge. Step-wise metrics named: **Tool Accuracy** (said to correlate strongly with final-answer accuracy) and **Argument Accuracy**; code-generating agents are scored with **Pass@k** and **Task Completion Rate** plus failure types such as API hallucination and stagnation loops. RS-side measures are kept alongside: F1, mAP@0.5, accuracy, relative error; **GeoLLM-Squad** adds a mean-square percentage error to track error propagation into land-surface temperature and tree loss.
- **Five stated limitations of current agentic RS** (§7.1, p. 8): (1) **Limited Geospatial Grounding** — RS-Agent/GeoAgent work largely on RGB and vector data, with little spectral-product or SAR support; Earth-Agent reports degradation on non-RGB products and quantitative queries; (2) **Fragile Tool Orchestration** — errors in tool selection and argument formatting across ThinkGeo/GeoBenchX/GeoCode/GTChain-Eval; CORE/ToolEmu show agents ignore preconditions, repeat failing calls, or trigger inappropriate tools; (3) **Shallow Temporal Memory** — agents keep only short context and flat tool-call logs, so Earth-Bench and ThinkGeo report repeated downloads, redundant computation and inconsistent reuse of intermediates; multi-temporal stacks and mission context are seldom stored in structured, queryable memory; (4) **Fragmented Evaluation Protocols** — no unified protocol measuring planning quality, perception accuracy and safety together, and most evaluations report only final answers, often on synthetic scenarios; (5) **Compute Constraints** — dependence on large proprietary LLMs and cloud infrastructure, with open-source alternatives lagging on planning and multi-tool code generation.
- **Two future directions** (§7.2, p. 8): **Foundations and Memory** (EO-native foundation models instead of adapting natural-image systems; multi-sensor encoders over optical, SAR and thermal; physics-informed surrogates and simulators; hierarchical memory blending vector stores, geo knowledge graphs and workflows) and **Safety, Efficiency, Equity** (extend ThinkGeo/GeoBenchX/Earth-Bench with harder negatives and stress tests for distribution shift, adversarial prompts and unsolvable queries; standardise reporting of trajectory metrics, harmful-call rates and resource consumption; distilled SLM planners for edge deployment).

### ⚠️ Discrepancies with the intake note (G3) — the PDF wins

1. **Taxonomy wording.** The intake note's "single-agent copilots vs. multi-agent orchestrators" is **Fig. 1's caption phrasing only**; the body (§4.1, p. 3) says **"single-agent systems" vs. "multi-agent systems"**. Use the body wording, or present the caption phrase as a figure caption.
2. **MapBot is not tabulated.** The intake note lists MapBot among surveyed agentic systems; in the PDF MapBot [134] appears **only in the introduction** (p. 2) and is **not** one of the 23 systems in Table 1 (p. 5).
3. **Counts are absent from the intake note.** The paper does give an inventory — 23 systems in Table 1 (13 SA / 10 MA, our count of the table rows) and 8 application domains (§4.2). No other totals are stated, so the "n studies" figure for this survey is effectively n/a.
4. The intake note's claim that the survey "reviews … RS foundation models (SatMAE, RingMo)" is correct (§3.1–3.2, pp. 2–3), and "no new experiments" is confirmed.

## Relevance to Thesis

**Optional** — related-work taxonomy, i.e. **background / future-work material in the frozen GeoAI-agent cluster (frozen 2026-10-04)**; do not extend the cluster.

- ✅ Its **limitations list is the most citable evidence that the agentic-RS field is immature in exactly the three places the thesis cares about**: spectral/thermal non-RGB grounding, temporal memory, and evaluation protocol (p. 8) — useful for a future-work "why agents are not yet ready for stress time series" argument.
- ✅ Its **evaluation philosophy** (trajectory-aware reasoning correctness instead of pixel accuracy) is a ready-made framing for how a stress-agent would be judged, and its citation of CORE / ToolEmu / GeoLLM-Squad gives the reviewer-facing vocabulary.
- ⚠️ **The survey contains no crop-stress work.** Its application taxonomy (p. 4) covers forests, wildfire, urban change, geology, cartography, satellite scheduling — agriculture appears only indirectly via the standalone benchmark rows, so nothing here is directly citable as prior art on stress agents.
- ❌ No quantitative evidence the thesis can reuse: no accuracy numbers, no datasets, no ablation. It is a narrative taxonomy, not a meta-analysis, so it cannot be used to make "X % of agentic studies do Y" claims.

## Key Takeaway

The most useful single artefact is the **five-item limitation list (p. 8)** — particularly *limited geospatial grounding* (RGB-only tool stacks) and *shallow temporal memory* — which gives a citable, survey-level justification that a multi-temporal optical+thermal crop-stress agent is not a solved problem. The caveat is that a narrative survey with no counted corpus cannot be used for quantitative gap claims; it can only frame terms.

## Links

- Matrix row: #49
- Related: #47 (RS-Agent — one of the 23 tabulated systems), #48 (ThinkGeo — reviewed as a reasoning benchmark), #56 (Munir et al. — complementary position paper on EO-native agent design), #57 (ExpertsRS — multi-agent RS analysis)
- Frozen cluster: rows 47–59, 63–67 — background / future-work only

---

*Linked from: [[Literature-Matrix]]*
