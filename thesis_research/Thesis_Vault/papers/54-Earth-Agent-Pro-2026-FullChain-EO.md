# 54 — Earth-Agent-Pro & Earth-Bench-Pro: Full-Chain Open-World EO Execution (Lv et al., 2026)

**Full Citation:** Lv, Z., Dang, C., Feng, Y., Gong, Y., Wang, X., Ye, J., He, C., & Li, W. (2026). Earth-Agent-Pro: Towards real-world full-chain Earth observation with agents. *arXiv preprint arXiv:2609.12533*.
**DOI:** [arXiv:2609.12533](https://arxiv.org/abs/2609.12533) | arXiv:2609.12533v1 [cs.CV], 11 Sep 2026 | Tsinghua SIGS / Sun Yat-Sen Univ. / SJTU / Shanghai AI Lab / Tianjin Univ. / HIT | Code + datasets *"will be released soon"* (p. 1)
**Status:** ✅ Full read (2026-10-20)
**Themes:** #Agentic-RS #Benchmark #Dataset #Foundation-model

---

## What It Does

Formalises **"open-world EO execution"**: the agent receives only a scientific request (phenomenon, region, period) and must itself **locate, acquire and preprocess runtime observations, run the domain computation, and produce an open-ended answer grounded in execution evidence** (pp. 1–2). Two paired artefacts: **Earth-Bench-Pro**, which keeps each of Earth-Bench's 248 scientific task cores fixed while removing the reference workflow and the prepared inputs, and **Earth-Agent-Pro**, a Plan-and-Execute agent with expert skills, workflow-centred structured memory, localised suffix repair and role-specialised training (Planner SFT + Executor GRPO) (pp. 1–2).

## Key Architecture

- **Expert skills (6)** covering spectral analysis, product-based computation and RGB perception; each specifies tool scope, operation order, argument constraints and repetition rules, and is **shared by Planner and Executor** (p. 6).
- **Two-stage routing** over a catalogue of **112 callable tools**: Skill Router selects a skill, Tool Router narrows to the skill-allowed subset (illustrated as **20–30 tools**), then the Planner composes a workflow over legal, task-relevant tools (p. 6, Fig. 5).
- **Planner:** a **four-role sequential debate** (EO workflow specialist → tool schema specialist → benchmark minimalist → skeptical moderator) plus a **catalog validator** (tool existence, active-skill membership) that returns errors and re-plans until a valid sequence is produced (p. 6).
- **Workflow-centred structured memory** `S_k = (W_k, M_k)`: dynamic workflow `W_k = (V_k, R_k)` (active nodes + revision archive) and execution memory `M_k`, a chronologically ordered list of **verified-only** evidence records `e_u = (A_tu, I_u, o_u, π_u)`; artifact provenance records variables, time, region, bands and batches (pp. 6–7).
- **Evidence-grounded execution & repair:** a ReAct loop **constrained to the current node**; a **hybrid verification gate** (deterministic checks for structural errors, error markers, batch coverage, then an LLM checker) returns accept / retry / replace; on persistent failure the Planner proposes a **replacement suffix** and the Executor installs it while **preserving the successful prefix** — `V_{k+1} = V_k[1:i−1] ⊕ δV_i` (p. 7). An **Answer Controller** separately audits required computations, spatiotemporal coverage, aggregation, units, numerical scale and non-finite results, writing the final answer **only from accepted evidence** (p. 7).
- **Role-specialised training** (pp. 7–9): *Planner* = sequence-level SFT (LoRA; autoregressive NLL over a JSON `tool_sequence` target with no arguments or observations) for workflow composition; *Executor* = node-level **GRPO**, **G = 4** sampled argument dictionaries, group-relative advantage, and a **rule-based reward** (parsed argument dictionary vs. the reference dictionary, ±1e-6 float tolerance) — no learned reward model.
- **Dependency-preserving data:** 248 seed workflows → **2,480 instantiated trajectories** via LLM-discovered replaceable slots (place, interim, parameter, time, file references) + expert-reviewed Python instantiation programs, mixed with the public OpenEarthAgent training set (p. 8).

## Benchmark Results

- **Earth-Bench-Pro = 744 questions = 3 matched regimes × 248 task cores**: Instruction-Following (496), Autonomous-Planning (496), **Open-World Execution (248)**; **5,295 reference tool calls** overall; the 248 OW workflows alone contain **1,765 tool calls, avg 7.1 per task, 84 distinct tools** (pp. 1, 5).
- **8 application domains** including **Agriculture & Drought**, plus urban & infrastructure, water & marine, vegetation & ecosystems, cryosphere & snow, atmosphere & climate, hazards & disasters, land cover & object mapping; **6 analysis types**: product statistics, spectral indices, thermal retrieval, brightness-temperature analysis, time-series analysis, RGB perception (p. 4). Coverage: all six inhabited continents, requested observation periods **1980–2025** (p. 4).
- **Expert annotation:** an 8-member team (2 CS experts, 3 RS specialists, 3 Earth-science specialists) re-executed each task in a shared EO environment and repaired inconsistencies between question, tool selection, arguments, dependencies and answer; **323 task-level acquisition specifications** (source, product, bands, extent, period, resolution, sampling interval, scaling) replace fixed local inputs for Product and Spectrum tasks, while **60 RGB tasks** keep user-provided visual inputs (p. 5). Quality control checks three relations along the evidence chain: query ↔ input requirements, data dependencies across calls, final answer ↔ execution evidence (p. 5).
- **Open-ended, not multiple choice:** all options removed; questions rewritten as self-contained requests. A numerical prediction counts as correct when its **relative error vs. ground truth is below 15%**; answers scored by **LLM-as-Judge**, ROUGE-L and embedding-based semantic matching (EM); trajectories by Efficiency, TAO, TIO, TEM, Parameter Accuracy (pp. 5, 9).

### Agriculture & Drought — concrete instances

- **TVDI drought-index task** (Fig. 4, p. 5): *"On 12 Jul 2021, what percentage of the Chengdu Plain had TVDI > 0.75?"* — download-first, **initial files: none**; inputs **MOD11A1 LST (scale 0.02)** and **MOD13Q1 NDVI (scale 1e-4)**, date 2021-07-12, **GSD 30 m**; AOI bbox **[103.800, 30.300, 104.500, 30.501]**; criterion TVDI > 0.75; required output = area ratio. Skill route *earth-acquire → thermal-retrieval*; workflow Download×2 → Scale×2 → **compute_tvdi** → threshold ratio; result **"Affected cropland 28.00%"**.
- **Vegetation-coverage change task** (Fig. 7 case 3, p. 15): Northeast Plain, 2021-04-01 → 2021-08-31, **MODIS/061/MOD13Q1 NDVI** → `apply_scale_offset(0.0001)` → `calc_batch_image_mean` → `percentage_change` → `max_value_and_index`; reference **72.1%**. The authors' own **failure case**: GPT-5 reached 72.17%, but Qwen-9B returned 14.1% and Earth-Agent-Pro 5.49% — correct upstream preparation, mis-selected downstream operation (p. 15).
- **Spectral thermal-retrieval task** (Fig. 7 case 1, p. 14): Urban Heat Island Index over Paris, 2020-06-28, **ASTER L1T TTM bands 10–12** → reference **UHII 43.3131 K**; GPT-5 skipped band extraction (24.25 K), Qwen-9B mis-grounded the thermal step (0 K).

## Key Findings

- **GPT-5 backbone on Earth-Bench-OW: 66.13% LLM-as-Judge — +20.95 pp over ReAct (45.18%) and +24.44 pp on Tools-In-Order (47.53 → 71.97); TAO 87.61 vs 70.47 (AFlow)** (p. 1, p. 12 Table VI). Same-backbone frameworks: ReAct 45.18, AFlow 40.16, OpenEarthAgent 41.53 (p. 12).
- **Role-specialised training lifts small backbones:** Qwen3.5-9B **38.31 → 50.00 (+11.69 pp)**; Qwen3.5-4B 32.26 → 43.15 (+10.89) (pp. 10, 13). Adapter composition: Base/Base 38.31, Base/Tuned 43.15, Tuned/Base 44.76, Tuned/Tuned 50.00 (p. 13, Table VIII).
- **Isolated evaluations separate the two roles** (p. 13): *planning-only*, tuned Planner reaches TAO 92.51 / TIO 83.35 / TEM 76.14 vs base 86.70 / 71.87 / 66.96 and GPT-5 88.86 / 76.38 / 70.03; *oracle-plan execution*, tuned Executor raises Judge 46.37 → 52.82 and parameter accuracy 34.19 → 37.20 (GPT-5 68.95 / 39.58).
- **Skills complement training rather than duplicate it** (p. 12, Table VII): adding skills to the base 9B raises TIO 61.94 → 74.57 and TEM 51.71 → 67.29; on the fine-tuned 9B it adds **+12.90 pp Judge**, +8.87 TAO, +10.18 TIO, +15.09 TEM.
- **vs. remote-sensing MLLMs** (p. 11, Table III; five TerraScope categories): Earth-Agent-Pro (Qwen3.5-9B) **50.58%** average vs TerraScope 42.60, TeoChat 31.16, GeoChat 31.02, EarthMind 30.74, LHRS-Bot 28.97, EarthDial 27.73. Distance Measurement ≈ 0 for every method (1.55 for Earth-Agent-Pro).
- **vs. general-purpose agents** (p. 12, Table V): Earth-Agent-Pro (GPT-5) **75.00%** average at **208.64 s** latency, vs Codex 46.67% / 268.73 s and Manus 43.33% / 291.00 s. **Cross-benchmark transfer** (p. 11, Table IV; OpenEarthAgent, GPT-5): answering accuracy **56.54**, +11.16 pp over the strongest GPT-5 baseline.
- **Stated limits** (p. 15): even the best TEM is **71.01%** and parameter accuracy **32.77%**; tool coverage is far easier than faithful parameter grounding; final-answer quality stays sensitive to backbone capability.

## Relevance to Thesis

**Optional** — belongs to the **frozen GeoAI-agent cluster (frozen 2026-10-04)**; background / future-work material only, and this cluster is not to be extended. (Intake note G8 rated this paper "High"; under the frozen-cluster calibration the verdict is **Optional**.)

- ✅ The **Agriculture & Drought** task is the closest published full-chain analogue to the thesis's index-assembly step: thermal (MOD11A1 LST) + optical (MOD13Q1 NDVI) → **TVDI** → threshold → area ratio over a fixed AOI, executed entirely at runtime with **no pre-supplied files** (p. 5). TVDI is a direct physical cousin of the thesis's CWSI-type thermal indices, and the 28.00% cropland result is a worked end-to-end example of the pipeline the thesis assembles by hand.
- ✅ Documents the evaluation design the thesis would need if it ever let an agent emit the final number: **open-ended answers, no distractors, 15% relative-error tolerance, LLM-as-Judge + ROUGE-L + embedding matching** (p. 9) — plus the observed failure that correct upstream preparation does not guarantee a correct downstream operation (p. 15).
- ⚠️ **LLM-as-Judge is far too coarse for stress-severity separation** — a 15% relative-error band and judged correctness cannot certify a water-vs-salinity distinction, and the paper's own agriculture/vegetation case fails (p. 15).
- ⚠️ Granularity is **regional aggregate** (area ratio, mean index, max change) over MODIS/ASTER resolution products; no parcel-level, per-season, concurrent-stress labelling and no XAI attribution.
- ❌ Contributes nothing to the thesis's actual method (EO foundation-model encoders, SSL on SITS, SSM/Mamba temporal encoder, active-learning label design, timestep-level XAI); the agent orchestrates pre-built tools over synthetic instantiations of 248 seed workflows.

## Key Takeaway

The most quotable artefact is the **Chengdu-Plain TVDI execution trace** (p. 5): a *complete, runtime-acquired* thermal + optical stress-index chain with explicit scaling factors, AOI, criterion and answer — existence proof that the thesis's optical + thermal index assembly is a recognised, benchmarked EO operation. The honest caveat: the benchmark scores the agent with an LLM judge and a 15% error band on regional aggregates, and the authors' own vegetation-index case fails — so it shows the chain is standard, not that it is reliable enough for stress discrimination.

## Links

- Matrix row: #54
- Related: #50 (AgriWorld — verifiable agri/RS agent tools, nearest agri-facing work in the frozen cluster), #53 (RSMeM — agent-side memory/refinement), #59 (REMSA — constraint-aware EO foundation-model selection)

---

*Linked from: [[Literature-Matrix]]*
