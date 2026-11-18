# 52 — BSCTR: Bidirectional Semantic Complementary Tool Retrieval for RS Agents (Wang et al., 2026)

**Full Citation:** Wang, Z., Hou, D., Yang, C., Cui, X., Xu, L., Yu, B., Zhou, G., Li, Z., Liu, L., Ouyang, K., Guo, W., Zhu, L., & Tao, C. (2026). Bidirectional semantic complementary tool retrieval for remote sensing agents. *arXiv preprint arXiv:2606.07538*.
**DOI:** [arXiv:2606.07538](https://arxiv.org/abs/2606.07538) | arXiv:2606.07538v1 [cs.IR] | Central South Univ. / Hunan Prov. Inst. of Land & Resources Planning | Code + data: https://github.com/geox-lab/BSCTR
**Status:** ✅ Full read (2026-10-20)
**Themes:** #Agentic-RS #Benchmark #Foundation-model

---

## What It Does

Targets the **"semantic asymmetry"** of tool retrieval for RS agents: a user query states a **macro-level intention** ("analyze crop health", p. 8) carrying no functional semantics, while tool documentation gives **fine-grained technical specifics** but no **contextual semantics** about where the tool sits in a workflow (pp. 1–2). **BSCTR** closes the gap from *both* sides — a planning-based query enhancement on the query side, and a dynamic, continually-learning **tool dependency graph** on the tool side — and is evaluated on the RS benchmark **GeoPlan-bench** and the general-purpose **API-Bank** (p. 6).

## Key Methodology

- **Plan Module (query side):** Plan-and-Solve prompting decomposes the coarse query `Q_coarse` into sub-tasks `S = {s1…sn}`; each enhanced query is `q_enhance^(i) = Q_coarse ⊕ s_i` (textual concatenation), giving query representation `V_q` (p. 5).
- **Graph Module (tool side):** the tool library is a **directed graph** `G = (N, E)`, edge `(i,j)` meaning tool *i* is invoked immediately before tool *j*. The augmented adjacency `Ã_ω` supports three propagation modes — **Predecessor** (`Aᵀ+I`), **Successor** (`A+I`), **Symmetric** (`A+Aᵀ+I`) (p. 5). Context enters via an SGC/PPR-inspired multi-order linear aggregation `H^(k) = [(1−α)I + α(D_ω⁻¹Ã_ω)]^k X`, where **α** balances a tool's own functional semantics against neighbourhood context (p. 5).
- **Alignment:** cosine similarity between `V_q` and `H^(k)`; **top-k per sub-task**, then global re-ranking of the union by **Reciprocal Rank Fusion (RRF)** (p. 6).
- **Execution & evolution:** a **ReAct** loop runs over the recalled pool, recording trajectory `P`; trajectories that pass environment verification are marked for structural learning, **new edges are added for newly observed adjacent tool pairs**, and `H^(k)` is recomputed on the updated graph (p. 6).
- **Configuration:** Predecessor mode, **α = 0.5, k = 1**; LLM reasoning by **DeepSeek-V3.2**; embeddings by **nomic-embed-text:latest** (p. 7).
- **Metrics:** Recall@k, NDCG@k, F1; **Tool Call Recall**; **Tool Trajectory Similarity** = `|LCS(P,T)| / max(|P|,|T|)` (p. 7). Deliberately process-level — GeoPlan-bench has no objective end-result assessment (p. 6).

## Key Findings

- **GeoPlan-bench** (p. 6, Table I): 248 train / **996 test trajectories**, **104 tools**, max chain length 20, **avg length 10.67**; test split into Simple / Medium / Complex.
- **API-Bank Level-3** (p. 6): 50 APIs, max length 70, avg 2.62; train/test API sets are disjoint, so the tool graph is **cold-started** with no prior trajectories.
- **GeoPlan-bench overall** (p. 8, Table II) — BSCTR vs best baseline (Query Rewriting): Recall@k **0.7485** vs 0.7260; NDCG **0.6759** vs 0.6425; F1 **0.7057** vs 0.6805; Call Recall **0.6455** vs 0.6054; LCS **0.3237** vs 0.3038. Graph-based baseline 0.5054 Recall; Dense 0.1920; BM25 0.1232.
- **By difficulty** (p. 8): Recall 0.8191 (Simple) / 0.7295 (Medium) / 0.6970 (Complex).
- **Retrieval-scale sensitivity** (p. 8, Table III): at k = 5, NDCG **0.6053** (Query Rewriting 0.5448); Recall climbs 0.2897 (k=5) → 0.6752 (k=15).
- **API-Bank Level-3** (p. 10, Table IV): Recall@k **0.9067**, NDCG **0.8613**, F1 **0.8804**, Call Recall **0.7900**, LCS **0.6090** — best on every metric.
- **Ablation** (p. 10, Table V) on GeoPlan-bench: **w/o Planning collapses Recall@k to 0.1883** (from 0.7485), Call Recall 0.1662, LCS 0.1203; **w/o Tool Graph** keeps Recall 0.7506 but drops Call Recall to 0.6054 and LCS to 0.3074 — planning is the RS-critical half, the graph is the chain's "logical anchor".
- **Hyperparameters** (pp. 10–11): Recall peaks at **k = 1** (0.7485) and **α = 0.5** (0.7485), with over-smoothing either side; propagation modes — Predecessor **0.7486**, Symmetric 0.7485, Successor 0.7362 (upstream context beats downstream, because RS workflows are causally constrained by precursor steps).
- **Why the LCS is only 0.3237** (p. 9): ReAct's exploratory steps inflate trajectory length, RS workflows are *equifinal* (several valid step orders), and one divergence truncates the common subsequence in >10-step chains.

## Relevance to Thesis

**Optional** — belongs to the **frozen GeoAI-agent cluster (frozen 2026-10-04)**; background / future-work material only, and this cluster is not to be extended.

- ✅ Quantifies a constraint the thesis's own pipeline faces: an RS tool library (QGIS/OTB/GDAL) cannot be fully injected into a context window, so **retrieval of the right step subset is a hard prerequisite** for any multi-step crop-stress chain.
- ✅ The **Predecessor-mode** result (0.7486 vs 0.7362 successor, p. 11) is a published argument for ordering the thesis pipeline causally — radiometric/geometric correction and index computation *before* stress classification and XAI attribution — rather than by semantic similarity alone.
- ⚠️ The method is **text-centric**; the authors themselves list the lack of multi-modal cues (sensor specifications, visual metadata) as a limitation (p. 12). It cannot reason over an optical + thermal SITS cube.
- ⚠️ Correctness is judged on **tool-chain fidelity**, not on the scientific answer (p. 6), so the numbers say nothing about stress-detection accuracy.
- ❌ No agriculture/irrigation domain, no crop, salinity, drought or temporal content; the tool inventory is generic EO processing.

## Key Takeaway

The transferable idea is the **query–tool semantic asymmetry**: RS agent queries are macro-objectives that share almost no vocabulary with the technical tools they need (the authors' example is a query like "analyze forest cover changes" against tools like *Atmospheric Correction* or *NDVI Calculation*, p. 9), and the fix is to **decompose the objective into explicit sub-tasks before matching**. The honest caveat: this is frozen-cluster background — it justifies a modular, retrieval-friendly pipeline design, it adds no method or experiment to the thesis.

## Links

- Matrix row: #52
- Related: #47 (RS-Agent — the ReAct-style baseline whose tool library BSCTR must retrieve from), #53 (RSMeM — complementary: memory on the *execution* side vs. BSCTR's *retrieval* side), #59 (REMSA — constraint-aware EO foundation-model selection)

---

*Linked from: [[Literature-Matrix]]*
