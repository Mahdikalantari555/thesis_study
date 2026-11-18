# 53 — RSMeM: Knowledge-Enhanced Memory Evolution for RS Agents (Wu et al., 2026)

**Full Citation:** Wu, B., Zhang, Y., Guo, Z., Liu, T., Qian, C., Lu, Y., Du, X., Li, Y., Zhang, Y., Chen, C., Yao, L., & Sun, M. (2026). RSMeM: Knowledge-enhanced memory evolution for remote sensing agents with systematic evaluation. *arXiv preprint arXiv:2607.24772*.
**DOI:** [arXiv:2607.24772](https://arxiv.org/abs/2607.24772) | arXiv:2607.24772v2 [cs.AI], 22 Aug 2026 | CAS IGSNRR / Tsinghua Univ. / UCAS / China Univ. of Geosciences (Beijing) / AIRCAS / SJTU | Code (GitHub) + Demo (ModelScope Studio) linked in the paper
**Status:** ✅ Full read (2026-10-20)
**Themes:** #Agentic-RS #Benchmark #Label-design

---

## What It Does

**RSMeM** is a memory-evolution mechanism for tool-augmented RS agents coupling two processes: **(i) Hierarchical Knowledge Grounding (HKG)** — taxonomy-aware retrieval over an expert-curated geoscience knowledge base to guide planning and tool selection — and **(ii) Failure-Aware Experience Refinement (FAR)** — a symbolic critic that detects failed tool-use traces and distils them into reusable constraints steering the *next* attempt at the *same* instance (p. 1). It is a plug-and-play wrapper evaluated on **Earth-Bench** across four LLM backbones (p. 2).

## Key Architecture

- **Offline KB (HKG).** A three-level taxonomy — **3 geoscience domains → 12 sub-domains → 64 atomic analytical tasks** (pp. 2, 13). Each atomic task is a **Task Card** `s_i = {T_i, D_i, S_i}` (title, domain definition, standardised execution suggestion) (p. 4). Domains: **Urban Planning Development, Disaster Management, Environmental Monitoring**; sub-domains include Land Cover Mapping and Water Resources Management (p. 13). Experts also curated a per-sub-domain **keyword lexicon**; the KB was peer-reviewed (p. 13).
- **Stream A — HKG retrieval.** Hybrid score `Score(q, s_i) = cos(v_q, v_i) + I_T·Sr_T(q, T_i) + I_K·Sr_K(q, k_j) + I_C·Sr_C(q, S_i)`, where lexical bonuses (`I_T = 0.2`, `I_K = 0.08`, `I_C = 0.1`) rescue terminology the embedding space under-represents; the **top-1** card above threshold `I_min = 0.2` is returned (p. 4).
- **Stream B — Failure-Aware Memory (FAM).** A **deterministic instance-indexed lookup** of the *most recent* reflection for that instance, `c_i(t) = Latest(M_i^(t−1))` (p. 4). This is the label-free core: the correction is bound to the execution trace that produced it, not to a shared global label pool.
- **FAR loop.** (a) A **symbolic critic Φ** applies heuristic rules `R` — missing/malformed answer tags, empty responses, invalid option letters, refusal or incompleteness, hedging language — flagging failure **without access to ground-truth labels** (p. 5). (b) **GeoTraceCompress** type-aware-compresses the trace (lists keep first 3 + last 2 items, dicts cut to two key-value pairs, error messages get an elevated budget, reasoning text preserved in full), reducing trajectory length by an order of magnitude (p. 5). (c) A **Reflection Generator** (same-backbone LLM call) produces a structured **3–5 sentence diagnosis + corrective plan**, appended to the FAM: `M_i(t) = M_i^(t−1) ⊕ r_i(t)` (p. 5).
- **Setup.** **Earth-Bench**: 248 expert-annotated instances, three modalities (RGB, Spectrum, Earth Products); 104 tools; MSCN swapped for SiamCRNN; backbones **DeepSeek-V3.2, Kimi-K2, Qwen3-32B, Qwen3-8B**; **R@3** protocol (unsolved instances re-run; final accuracy by backward-overwriting with the latest successful attempt) (pp. 5–6). Decisively: *"We do not expose any ground-truth tool steps or answers to the agent during inference/refinement. Labels are reserved for evaluation only."* (p. 6)

## Key Findings

- **DeepSeek-V3.2 outcome accuracy 48.18 (EarthAgent R@1) → 51.82 (EarthAgent R@3) → 57.89 (RSMeM R@3) = +6.07 pp** (p. 5 Table 1, p. 8 Table 4). Other backbones: Qwen3-8B 31.98 → 42.11; Qwen3-32B 38.87 → 48.58; Kimi-K2 36.44 → 48.99 (p. 5).
- **Token cost is marginal:** total token share 6.23% → 6.97% for DeepSeek-V3.2 (p. 6, Table 2); the *reflection stage* consumes **0.35%** (DeepSeek), 0.37% (Kimi-K2), 0.85% (Qwen3-8B), 1.40% (Qwen3-32B) of the inference budget — **under 1.5% everywhere** (p. 16, Table 7). Trajectory Redundancy Index stays near 1.0 (p. 7).
- **Ablation** (p. 7, Table 3): HKG alone on DeepSeek raises AO 77.27 → 79.50 and IO 55.02 → 56.51 (global planning); FAR alone on Qwen3-8B raises **WS 0.0408 → 0.0763** (trajectory robustness). The **full framework is best on every backbone** (42.11% / 57.89% outcome accuracy).
- **Memory evolution** (p. 8, Table 4): GRF-only EM 25.85% / Acc 51.82% → Stage I EM 26.19% / Acc 55.87% (+4.05) → Stage II EM 27.01% / Acc 57.89% (+6.07); Experience Density rises 55.72 → 57.69, i.e. later stages **distil** rather than accumulate.
- **vs. generic retrieval** (p. 17, Table 9; 50 EarthBench tasks, DeepSeek-V3.2): ReAct + Simple RAG 36.73%, ReAct + Web Retrieval 48.98%, **RSMeM 53.06%** — **+16.33 pp over Simple RAG**, +0.3092 EM.
- **External generalisation** (p. 17, Table 8): ThinkGeo subset (n = 100, reformatted to MCQ with hint-free distractors) 32.0% → **49.0% (+17.0)**.
- **Per-domain** (p. 17, Table 10, DeepSeek-V3.2): Disaster Management 48.72 → 58.97 (**+10.25 pp**), Environmental Monitoring 51.77 → 58.45 (+6.68), Urban Planning & Dev. 53.73 → 55.22 (+1.49) — gains concentrate where workflows are standardised and multi-step.
- **Case study** (pp. 8–9, Fig. 5): a Landsat 8 thermal time-series LST question. Round 1 fails via an **invalid tool call** plus **target-variable drift** (raw BT10 brightness temperature used where emissivity-corrected LST was required); the reflection stores a *semantic* constraint (LST must be emissivity-aware) and a *procedural* constraint (one consistent 15-scene pipeline with explicit completion); Round 2 returns **5 days** — the correct option.
- **Limitations** (p. 9): cold start if the KB is sparse; generalisation to specialised or real-time streaming RS untested; refinement currently uses **failures only**, not sub-optimal successes.

## Relevance to Thesis

**Optional** — belongs to the **frozen GeoAI-agent cluster (frozen 2026-10-04)**; background / future-work material only, and this cluster is not to be extended. (Intake note G7 rated this paper "High"; under the frozen-cluster calibration the verdict is **Optional**, and the mechanism below is an *analogue* of the thesis's label-efficient branch, not a component of it.)

- ✅ **Closest published analogue to the thesis's label-efficient refinement branch.** The refinement signal is a *symbolic failure critic operating without ground-truth labels* (p. 5) plus a deterministic instance-indexed memory (p. 4) — the system re-queries and re-constrains itself using its own error evidence, with labels held back for evaluation only (p. 6). Conceptually parallel to active learning's "spend annotation only where the model is uncertain".
- ✅ Supplies a **quantified efficiency argument** of the form the thesis would need for any label-efficiency claim: **+6.07 pp outcome accuracy for +0.74 pp total tokens** (6.23 → 6.97%, p. 6), with the reflection stage under 1.5% of budget (p. 16).
- ⚠️ The analogy holds at the **protocol level (what gets re-attempted / re-constrained), not at the label level**: RSMeM re-uses *execution failures*, whereas the thesis's active learning re-uses *analyst-assigned stress-severity labels*. RSMeM never proposes *which new samples to label*.
- ⚠️ The knowledge base has **no agriculture domain** (p. 13) — a crop-stress KB spanning water vs. salinity discrimination would have to be built from scratch; the LST/thermal entries are the closest existing material.
- ❌ No optical + thermal **SITS** encoder, no EO foundation model, no salinity, no XAI attribution, no parcel-level or seasonal evaluation.

## Key Takeaway

The transferable idea is **"failure without labels"**: a rule-based critic detects a bad trajectory, compresses it, and writes a short, instance-bound corrective constraint injected into the next attempt — +6.07 pp for under 1% extra tokens (pp. 5–6, 16). The honest caveat: it is a *self-correction* loop, not an *annotation-strategy* loop, so it motivates but does not substitute for the thesis's own label-design and active-learning protocol.

## Links

- Matrix row: #53
- Related: #63 (Sun et al. — need-driven self-evolution for label-efficient RS detection, nearest peer in the frozen cluster), #50 (AgriWorld — verifiable agri/RS agent tooling), #47 (RS-Agent — the ReAct-style baseline RSMeM builds on)

---

*Linked from: [[Literature-Matrix]]*
