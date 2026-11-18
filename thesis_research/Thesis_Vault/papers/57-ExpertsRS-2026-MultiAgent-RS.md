# 57 — ExpertsRS: An LLM-Based Multi-Agent System for Remote Sensing Analysis (Sun et al., 2026)

**Full Citation:** Sun, Z., Zhou, Y., & Yang, J. (2026). An LLM-based multi-agent system for remote sensing analysis. *Big Earth Data*. Advance online publication (published online 8 January 2026). https://doi.org/10.1080/20964471.2025.2600178
**DOI:** [10.1080/20964471.2025.2600178](https://doi.org/10.1080/20964471.2025.2600178) | Open Access (CC BY-NC 4.0) | Big Earth Data (Taylor & Francis / International Society for Digital Earth) | Received 2 Jun 2025, accepted 8 Nov 2025, published online 8 Jan 2026 | Article views 3,011; citing articles 4 (as printed on the article page, p. 1) | 26 pp.
**Status:** ✅ Full read (2026-10-20)
**Themes:** #Agentic-RS #Benchmark #Foundation-model

---

## What It Does

Presents **ExpertsRS**, a prototype LLM **multi-agent system for remote-sensing analysis aimed at non-expert end users** (p. 2). The underlying framework has three modules (p. 6, §2.2): **Data** (optical/SAR imagery, pre-processed products such as vegetation indices, LST and DEMs, plus vector and socio-economic auxiliary data), **Tools** (GDAL/Rasterio/ArcPy, PyTorch/TensorFlow/scikit-learn, RS foundation models — **Prithvi** and **AlphaEarth Foundation** — and cloud platforms GEE, Colab, Planetary Computer), and **Brain** (LLM-driven language understanding, reasoning, task coordination and retrieval). The prototype instantiates the framework with **three role-specialised agents** that convert vague natural-language requests into structured, executable RS workflows.

## Key Architecture

- **Orchestration on the StateFlow model** (p. 8, §3.1) — a state machine whose phases advance only when conditions are met; transitions are keyword-driven and a maximum-interaction cap keeps the run bounded.
- **Four-state workflow** (p. 8, Fig. 3): **Clarify** (multi-round dialogue to pin down timeframe, ROI, resolution) → **Define** (structured problem statement: required data, methods, visualisation) → **Solve** (plan → subtask decomposition → executable code → iterative error correction) → **Report** (analysis process, maps, computed metrics).
- **Three agents** (Table 1, p. 8): **M1 User Interface** (engage user, classify requests, explain results), **M2 Problem Analyst** (refine a request into a well-defined executable research problem), **M3 Task Solver** (task decomposition + tool utilisation). In the prototype these are instantiated as **Manager**, **Scientist** and **Engineer**, plus an **Executor** execution environment and a **shared message pool** (p. 12, Fig. 5). The multi-agent formalism is a graph G(V, E) over agents, plugins and messages (p. 7, §2.3).
- **Prompting stack** (pp. 8–9): **Expert Prompting**, **In-Text Learning**, **Chain-of-Thought** (especially in the Solve stage), plus example instructions and hard constraints.
- **Implementation**: built on **AutoGen**; backbone LLM **DeepSeek-V3**; data = **Sentinel-2** hosted on Google Earth Engine, scene `20230718T025529_20230718T030322_T50TMK` (least cloud in 1 Jun–31 Aug 2023); ROI = **Dongcheng District, Beijing** (pp. 10, 12).

## Key Findings

- **Case 1 — urban green-space mapping** from a deliberately vague request ("I am an official in the urban greening department…"): the system produced a thematic map with a **green-space coverage rate of 22.13%**, matching the human expert's result because both used the same NDVI threshold (p. 12). The Manager also answered follow-up questions about the threshold rationale.
- **Case 2 — urban vegetation health**: the system produced **Moisture Stress Index (MSI)** and **Chlorophyll Index (CI)** maps, again matching the human expert's outputs (p. 13).
- **Quantitative evaluation setup** (p. 10, §3.2.2): a validation set of **20 user requests (10 single-step + 10 multi-step)**, same scene and ROI as the case studies; two human-judged metrics — **planning correctness rate** (is the plan logically sound, executable and consistent with expert reasoning?) and **result correctness rate** (are the final maps/indices/values accurate?) — rated by an RS PhD student; plus **average token consumption** as the cost proxy. Two baselines: (1) **Base LLM** = DeepSeek-V3 with a minimal prompt; (2) **Single-Agent System** = AutoGen with one assistant agent, a simplified expert prompt and iterative trial-and-error code execution.
- **Table 2 results** (p. 16):

| Task | Configuration | Planning % | Result % | Avg tokens |
|---|---|---|---|---|
| Single-step | Base LLM | 50 | 5 | 1,487 |
| Single-step | Single agent | 70 | 40 | 15,031 |
| Single-step | **ExpertsRS** | **80** | **60** | 23,530 |
| Multi-step | Base LLM | 20 | 0 | 1,971 |
| Multi-step | Single agent | 20 | 0 | 13,823 |
| Multi-step | **ExpertsRS** | **50** | **40** | 29,826 |
| **Total** | Base LLM | 35 | 5 | 1,729 |
| **Total** | Single agent | 45 | 20 | 14,424 |
| **Total** | **ExpertsRS** | **65** | **50** | 26,678 |

- **Token economics** (p. 13): at DeepSeek-V3 pricing of **US$0.27 per million input tokens and US$1.10 per million output tokens**, the ExpertsRS-vs-single-agent cost gap is **"less than one US cent per task"** — the authors' justification for the overhead.
- **Stated limitations** (p. 17, §5.2): **cascading hallucination** in multi-agent systems (an inappropriate NDVI threshold produced inaccurate green-space areas); adding a quality-check agent creates feedback loops that raise latency and token use; Matplotlib output lacks map furniture (north arrow, legend) and needs extra hand-coded styling; token cost grows with role count and collaboration complexity.
- **Future directions** (pp. 17–18): automated data acquisition via platform APIs, cartographic output through PyQGIS / ArcGIS Python API, a **Model Context Protocol (MCP)**-style unified model-agnostic agent–tool interface, RSFM integration to constrain the LLM, knowledge-graph/RAG domain grounding, structured role hierarchies, expanded case libraries and validation sets, and a **trustworthiness** framework (robustness, explainability, accessibility, risk) plus disclaimers on data limitations, resolution constraints and bias in the report stage.

## Relevance to Thesis

**Optional** — this paper belongs to the **frozen GeoAI-agent cluster** (matrix rows 47–59, 63–67; **cluster frozen 2026-10-04**) and is **background / future-work material only**. The cluster is **not** to be extended, and this note does not propose adding further agentic work to the thesis.

- ✅ A **concrete, published interaction design** for "a non-expert asks in plain language, the system returns an executed EO analysis" — the closest thing in the cluster to a user-facing template for a crop-stress assistant, and the paper's argument for *interactive, user-guided* refinement over one-shot prompting (p. 13) is directly reusable framing.
- ✅ The **four-state decomposition** (Clarify → Define → Solve → Report) is a reusable pipeline sketch, and the Report stage's explicit inclusion of **data limitations, resolution constraints and potential bias** as disclaimers (p. 18) is a borrowable trust practice for any thesis-facing deliverable.
- ✅ The tool catalogue names **Prithvi** and **AlphaEarth Foundation** (p. 6) as drop-in RSFM tools, and the limitations section explicitly proposes pairing the LLM with RSFMs to add domain constraints and curb cascading hallucination (p. 17) — the same coupling the thesis's EO-FM branch already assumes.
- ✅ It supplies a **negative, citable case** of multi-agent fragility (cascading hallucination across roles, p. 17) that an EO-agent design must answer — a fair use for the thesis's discussion of agent risk, if it is ever needed.
- ⚠️ **The absolute accuracies are weak and the "human expert" is not independent**: multi-step result correctness is only **40%** (p. 16), and the expert benchmark is a single RS PhD student re-running *the same method* (same NDVI threshold), so "outputs comparable to those of human experts" is **same-method agreement, not an accuracy claim** (pp. 12–13, 15).
- ⚠️ **Domain mismatch**: urban vegetation in Beijing on a single Sentinel-2 scene; the only stress-adjacent products are MSI and CI static maps. No multi-temporal series, no thermal, no salinity, no EO-FM weights actually used, no active learning.
- ⚠️ Token overhead is **~1.85× the single-agent configuration** (26,678 vs 14,424 average tokens, p. 16) — "modest" (the abstract's word) is the authors' framing, and only holds because DeepSeek-V3 output tokens are cheap.
- ❌ Provides no disentanglement method, no temporal/SSM architecture, no label protocol, no XAI, and no crop-stress or salinity evaluation.

## Discrepancies with intake note (G11)

- **Year**: the intake note cites **2025**; the PDF states "To cite this article: Zhelun Sun, Yuyu Zhou & Jun Yang (08 Jan 2026)" and "Published online: 08 Jan 2026" (p. 1) → **cite as 2026** (matching the matrix row). The "2025" inside the DOI string is a Taylor & Francis article-number convention, not a publication year.
- **Token overhead**: the intake note says only "modest"; the PDF gives the exact averages in Table 2 (p. 16) — quoted above.
- **Missing architecture detail in the intake note**: the intake mentions three agents and DeepSeek-V3 but omits the **StateFlow** orchestration, the **four-state** workflow, the **Executor** environment and the shared message pool — the actual pipeline (pp. 8, 12).
- **Relevance**: the intake rates it "HIGH"; the matrix verdict and the frozen-cluster rule give **Optional** — **Optional** is used here.

## Key Takeaway

The most useful thing is the **published, runnable interaction skeleton** (AutoGen + DeepSeek-V3 + three role agents + StateFlow four-state workflow) and its honest failure modes — cascading hallucination and token blow-up (p. 17) — which are citable evidence that an RS assistant needs domain constraints and an explicit trust/disclaimer stage. The caveat is decisive: multi-step result correctness is only 40% and the "expert" agreement is same-method, so this paper supports a *design template and a risk warning*, never an accuracy claim.

## Links

- Matrix row: #57
- Related: #56 (Munir et al. — the EO-native critique of exactly this kind of stateful multi-agent design), #48 (ThinkGeo — tool-augmented RS agent evaluation; the step-wise evaluation this paper lacks), #50 (AgriWorld — verifiable agri/RS agents, the closest agri-agent bridge in the cluster)

---

*Linked from: [[Literature-Matrix]]*
