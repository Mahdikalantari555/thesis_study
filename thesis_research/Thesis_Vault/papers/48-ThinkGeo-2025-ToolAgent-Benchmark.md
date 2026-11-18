# 48 — ThinkGeo: Evaluating Tool-Augmented Agents for Remote Sensing Tasks (Shabbir et al., 2025)

**Full Citation:** Shabbir, A., Munir, M. A., Dudhane, A., Sheikh, M. U., Khan, M. H., Fraccaro, P., Moreno, J. B., Khan, F. S., & Khan, S. (2025). ThinkGeo: Evaluating tool-augmented agents for remote sensing tasks. *arXiv preprint arXiv:2505.23752*. https://arxiv.org/abs/2505.23752
**DOI:** [arXiv:2505.23752](https://arxiv.org/abs/2505.23752) (v3 [cs.CV], stamped 2 Apr 2026) | MBZUAI · IBM Research · Linköping University · Australian National University | Code: `https://github.com/mbzuai-oryx/ThinkGeo` (p. 1)
**Status:** ✅ Full read (2026-10-20, extracted text) — **frozen GeoAI-agent cluster**
**Themes:** #Agentic-RS #Benchmark #Dataset #Tool-orchestration

> **Frozen-cluster statement.** This paper belongs to the **GeoAI-agent cluster, frozen on 2026-10-04** (matrix rows 47–59, 63–67) as **background / future-work material**. The cluster is **not to be extended** by this note.

---

## What It Does

ThinkGeo is presented as the **first agentic benchmark built specifically for remote sensing**: instead of scoring final answers on general/web images, it grounds tool-augmented LLM agents in real EO imagery (optical RGB **and** SAR) and grades the *execution trace*. It assembles **486 agentic tasks** with **1,778 expert-verified reasoning steps**, exposes **14 deployed tools**, and reports both **step-wise execution metrics** and **final-answer correctness** for 11 LLM backbones. Its headline message is negative: the gap between competent tool use and correct geospatial answers is large — the best model reaches ~74% tool-selection accuracy but only **9.78%** final-answer accuracy.

## Key Methodology

- **Task suite**: 486 tasks — **436 optical RGB + 50 SAR** (p. 2); the SAR subset is 50 queries over **244 tool-reasoning steps** (p. 11). Queries are **step-implicit and tool-implicit** — the prompt never names a tool, so the agent must infer which perception / logic / operation modules to use and in what order (p. 4).
- **Tool set (14)**: extends **AgentLego** with two additions — **ChangeDetection** (multi-temporal) and **SegmentObjectPixels** (segmentation + pixel counting). Three functional categories: **Perception** (TextToBbox, ChangeDetection, ObjectDetection, …), **Logic** (Calculator, Solver), **Operation** (DrawBox, GoogleSearch, AddText, Plot, OCR, …) (p. 6).
- **Seven use-case categories** (Fig. 2, p. 4): Urban Planning; Disaster Assessment & Change Analysis; Environmental Monitoring; Transportation Analysis; Aviation Monitoring; Recreational Infrastructure; Industrial Sites.
- **Query-construction pipeline** (pp. 4–5): (1) expert guidelines + image sampling; (2) manual authoring of ReAct dialog traces with a GPT-API script fed per-image metadata (object types, GSD, bounding boxes); (3) two-stage validation — expert review plus script checks on tool-argument consistency, dialog structure, completeness; invalid cases manually refined. **1–5 queries per image**; most queries use **2–5 tools** (Fig. 4, p. 5). Difficulty (easy/hard) is assigned by count of complex keywords + number of reasoning steps (p. 5).
- **Source imagery — 11 public datasets** (Table 2, p. 6): optical — DOTA, NWPU-VHR-10, UCAS-AOD, AID, iSAID, xBD, FloodNet, Global-Dumpsite; SAR — SSDD, SADD, SIVED. Original images are reused; the agentic tasks are **newly annotated bottom-up**.
- **Annotation effort**: ≈**500 human hours**, 4-member team — 100 h sampling/drafting, 280 h image analysis + ReAct construction, 120 h validation (pp. 12–13).
- **Evaluation protocol** (pp. 6–7): two modes — **step-by-step** (GTA-derived InstAcc, ToolAcc, ArgAcc, SummAcc) and **end-to-end** (tool-category accuracy P/O/L, final-answer `Ans.`, answer accuracy under image grounding `Ans I`). Final-answer correctness uses **LLM-as-a-judge with gpt-4o-mini** rather than GTA's deterministic string matching, to avoid mis-scoring multi-fact answers (p. 6). **All main-table results are optical-RGB only**; SAR is in supplementary S1 (p. 7).

## Benchmark Results

| Model | Inst. | Tool. | Arg. | Summ. | P | O | L | Ans. | Ans I |
|---|---|---|---|---|---|---|---|---|---|
| GPT-4-1106 | **86.49** | **74.05** | **36.96** | 77.76 | 84.65 | 70.16 | 65.58 | 5.16 | 14.69 |
| GPT-4o | 82.33 | 67.73 | 34.75 | **84.00** | **89.78** | 74.74 | 67.84 | **9.78** | **20.40** |
| Claude-Sonnet | 22.31 | 27.31 | 0.00 | 76.15 | 66.67 | 71.54 | **76.80** | 8.97 | 7.57 |
| Qwen2.5-7B-Instruct | 64.88 | 51.04 | 20.08 | 76.40 | 29.29 | 34.00 | 35.98 | 7.34 | 6.40 |
| InternLM3-8B-Instruct | 50.53 | 45.37 | 21.38 | 48.33 | 38.43 | 36.23 | 30.72 | 8.15 | 9.15 |
| LLaMA3-1-8B-Instruct | 47.27 | 37.29 | 13.69 | 70.14 | 58.84 | 46.67 | 56.70 | 3.80 | 3.42 |
| Qwen3-8B (w/ reasoning) | 26.03 | 14.73 | 3.19 | 65.70 | 57.99 | 61.27 | 34.09 | 5.16 | 5.63 |

(Table 3, p. 7 — step-by-step: Inst./Tool./Arg./Summ.; end-to-end: P/O/L, Ans., Ans I.)

- **Tool selection correlates best with final-answer accuracy** among the step-wise metrics (Fig. 5, p. 7) — the paper's central evaluation-philosophy claim.
- **Tool-call error rates**: GPT-4o **44.46%**, GPT-4-1106 **30.86%**; open-source models invoke tools aggressively with high error rates (p. 7, Fig. 6).
- **Failure taxonomy** (Table A2, p. 11): planning errors dominated by `NoAction` (Yi-1.5-6B 81.33%, Qwen3-8B 77.21%, Phi-3-mini 59.60%, Mistral 55.47%); format errors dominated by *Invalid JSON* (Qwen1.5-7B 92.52%, LLaMA3-1-8B 82.36%) and *Final Answer (SingleStep)*, i.e. skipping the reasoning chain (Qwen1.5-7B 78.44%).
- **SAR** (Table A1, p. 11): GPT-4o Tool 77.87 / Ans. 5.56; GPT-4-1106 Tool 75.82 / Ans. 2.78 — **final-answer accuracy < 6% for every model**; "tool competence alone is not sufficient for reliable SAR understanding" (p. 11).
- **Runtime** (Table A4, p. 13): GPT-4o 12.10 s/query step-wise (12.01 end-to-end); GPT-4-1106 22.43 / 16.65; InternLM3-8B 22.68 / **27.01**.
- **Category mix** (Table A3, p. 13, optical subset): Disaster Assessment & Change Analysis **148** (95 easy / 53 hard); Transportation Analysis 90; Urban Planning 71; Recreational Infrastructure 41; Aviation Monitoring 40; Environmental Monitoring 31; Industrial Sites 15 — **Total 436 (281 easy / 155 hard)**.

### ⚠️ Discrepancies with the intake note (G2) — the PDF wins

1. **Model list.** The intake note (and the paper's own contribution bullet, p. 2) says "Claude-3"; Table 3 names the model **Claude-Sonnet** (p. 7). The evaluated set is **11 backbones** — GPT-4o, GPT-4-1106, Claude-Sonnet, Qwen1.5-7B, Qwen2.5-7B, InternLM3-8B, LLaMA3-1-8B, Phi-3-mini-4K, Mistral-7B-v0.2, Yi-1.5-6B, Qwen3-8B — not four.
2. **Per-model scores.** The intake note flags them as unavailable from a first-page extract; they are now verified from Table 3 (p. 7), SAR Table A1 (p. 11) and error Table A2 (p. 11).
3. **"1,778 expert-annotated steps"** → the paper says **expert-verified** reasoning steps (p. 1, p. 2). The 1,778 total spans the full 486-task suite; the SAR subset alone is 244 steps (p. 11).
4. **14 tools** — confirmed (p. 2, p. 6), with **ChangeDetection** and **SegmentObjectPixels** the two additions to AgentLego.

## Relevance to Thesis

**Optional** — background / future-work material in the **frozen GeoAI-agent cluster (frozen 2026-10-04)**; do not extend the cluster.

- ✅ Its **two-tier protocol (step-wise execution metrics + final-answer correctness)** and its **tool-selection↔answer-accuracy correlation** are the cleanest available template for evaluating an agentic wrapper, should the future-work chapter ever propose one.
- ✅ Its **tool-error taxonomy** (NoAction planning failures, invalid JSON argument formatting, premature single-step final answers) is directly quotable as evidence that RS agent brittleness is dominated by *argument formatting and tool selection*, not by perception quality.
- ⚠️ **Agriculture is essentially absent.** The only agri-adjacent content is "agricultural land-use impact assessments" inside Environmental Monitoring (p. 4) and the Global-Dumpsite imagery. There is **no crop-stress task, no vegetation-index time series, no water-stress/salinity task** — so transfer to the thesis domain would be an extrapolation, not a demonstrated capability.
- ❌ No multi-temporal *stress* reasoning, no thermal/CWSI, no salinity, no per-field trajectory metric tied to a physical stress variable.

## Key Takeaway

The most transferable idea is the **step-wise-vs-end-to-end scoring split**, because it makes the gap visible: the best model reaches ~74% tool accuracy but <10% correct answers on spatial-anchored questions (Table 3, p. 7). The honest caveat is that ThinkGeo tests *spatial-measurement* reasoning on urban/disaster imagery, so a crop-stress agent would face a different failure profile (temporal aggregation, physiological semantics) that this benchmark does not probe.

## Links

- Matrix row: #48
- Related: #47 (RS-Agent — the agent architecture this benchmark would evaluate), #49 (Talemi et al. — survey that places ThinkGeo among RS agent benchmarks), #56 (Munir et al. — EO-native agent design principles)
- Frozen cluster: rows 47–59, 63–67 — background / future-work only

---

*Linked from: [[Literature-Matrix]]*
