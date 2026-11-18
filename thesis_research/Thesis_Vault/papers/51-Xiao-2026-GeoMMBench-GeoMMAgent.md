# 51 — GeoMMBench & GeoMMAgent: Expert-Level Multimodal Geoscience/RS Benchmark and Agent (Xiao et al., 2026)

**Full Citation:** Xiao, A., Cheng, S., Xu, Y., Ren, Y., Chen, H., & Yokoya, N. (2026). GeoMMBench and GeoMMAgent: Toward expert-level multimodal intelligence in geoscience and remote sensing. *arXiv preprint arXiv:2604.08896*.
**DOI:** [arXiv:2604.08896](https://arxiv.org/abs/2604.08896) | arXiv:2604.08896v1 [cs.CV], 10 Apr 2026 | Project page: https://geo-mm-agi.github.io | RIKEN AIP / Wuhan Univ. / Linköping Univ. / Univ. of Tokyo / Nanjing Univ. of Info. Sci. & Tech.
**Status:** ✅ Full read (2026-10-20)
**Themes:** #Benchmark #Agentic-RS #Dataset #Foundation-model

---

## What It Does

Two coupled contributions. **GeoMMBench** is an **expert-crafted** multimodal QA benchmark for geoscience and remote sensing: **1,053 image-based multiple-choice questions**, each with one correct answer, spanning four disciplines, six sensor modality groups and a four-level task hierarchy (p. 1, p. 3). **GeoMMAgent** is a **multi-agent orchestration framework** that closes the gap the benchmark exposes, integrating retrieval, perception and reasoning tools through a plan → execute → self-evaluate loop (p. 5). The paper benchmarks **36 open-source and proprietary MLLMs** and shows tool-augmented agents approach human-expert accuracy while standalone MLLMs do not (pp. 2, 6).

## Key Architecture

- **Composition:** 1,053 MCQs — **val set 37 questions, test set 1,016** (p. 2). Disciplines: **RS, photogrammetry, GIS, GNSS**; modalities: **MSI/HSI, SAR, LiDAR, DEM, optical, thermal** (p. 3).
- **Four-level task spectrum** (p. 3): (1) theoretical knowledge; (2) low-level perception — image quality assessment and RS-specific corrections (atmospheric, radiometric, geometric); (3) mid-level geospatial recognition — scene/object recognition, geospatial relationship analysis, temporal change detection; (4) high-level applications — environmental monitoring, **agriculture**, economic analysis, RS mapping products.
- **Expert annotation:** a panel of PhD researchers and doctoral students defined the dimensions and knowledge points, then wrote items from textbooks, online resources and academic literature; every item was peer-reviewed to strip **text-only inference bias** and to fix ambiguous phrasing, misleading distractors or wrong solutions (pp. 3–4).
- **GeoMMAgent, three stages** (p. 5): *Planning* (coordinator decomposes into subgoals, required agents, execution order/dependencies); *Multi-Agent Execution* (retrieval / perception / reasoning agents returning structured outputs); *Self-Evaluation* (logic, spatial reasoning, domain validity, accuracy → Excellent = output, Fair = re-execution).
- **Tool library** (p. 5; details p. 15): Knowledge = Wikipedia/Google search + **GME** multimodal retrieval with provenance; Perception = YOLOv11-CSPNet scene classifier on Million-AID (**51 scene/land-cover classes**), YOLOv11-CSPNet oriented-box detector on DOTA-v2, DeepLabv3+ (Xception) segmenter on LoveDA; Reasoning = **Qwen-VL-Max**. All tools exposed via **MCP**.
- **Protocol:** zero-shot, no fine-tuning; rule-based regex extraction of option letters (invalid outputs = incorrect); micro-averaged accuracy; LMMs-Eval toolkit; NVIDIA A100 GPUs; random-choice baseline (p. 6).

## Benchmark Results

- **Human expert baseline 86.5%** (master's-degree holders, no search engines or AI assistants) — far above every foundation model (p. 6).
- **GeoMMAgent: 88.4% test, 86.5% val** — matching the human expert on val, surpassing all MLLMs (pp. 6–7, Table 2).
- Best closed-source: **Gemini-1.5 Pro 70.7%**, Gemini-2.0-flash 70.1%, GPT-4o 68.5%, GPT-o1 65.8%; best open-source **Qwen3-VL-30B 66.7%** (p. 7).
- **Geospatial-specialist MLLMs underperform** generic ones: GeoChat 21.6%, TeoChat 24.3%, SkySenseGPT 18.9%, LHRS-Bot 27.0%, VHM 37.8%; text-only GPT-4 24.3%; random baseline 20.8% (p. 7).
- **Component ablation** (p. 19, Table A3, val/test): full 86.5/88.4; w/o Knowledge 83.8/87.4; w/o Perception 83.8/80.3; **w/o Reasoning 59.5/67.3** (largest drop); w/o Self-evaluation 81.1/80.1.
- **Error taxonomy** (pp. 6–8): visual-linguistic misalignment (models answer correctly in text but fail on the same content in image form), geospatial-relation misinterpretation, sensor-modality confusion, specialized-discipline deficiency, image-perception failure.

## Relevance to Thesis

**Optional** — belongs to the **frozen GeoAI-agent cluster (frozen 2026-10-04)**; background / future-work material only, and this cluster is not to be extended.

- ✅ Supplies the documented baseline of what standalone MLLMs (including RS-tuned MLLMs) achieve on multi-sensor geoscience reasoning — framing evidence for treating EO foundation models as encoders rather than reasoning agents.
- ✅ Documents the agent-vs-standalone gap (88.4% vs 70.7% best MLLM, pp. 6–7) that underpins any future GeoAI-agent framing of the thesis.
- ⚠️ Format is **single-image multiple choice**; it tests no open-ended multi-temporal stress-trajectory reasoning, calibration or label design.
- ❌ Contains **no crop, water-stress, salinity, phenology or time-series content**; agriculture appears only as a generic "high-level geospatial applications" task category (p. 3).

## Key Takeaway

The transferable artefact is the **error taxonomy** — it documents, with numbers, that RS MLLMs fail specifically on **thermal and SAR imagery** because their encoders are RGB-biased (p. 7), reinforcing the thesis's use of explicit optical + thermal branches rather than end-to-end multimodal input. This is frozen-cluster background: it justifies *why* the thesis uses EO foundation models as encoders; it does not extend the agentic cluster.

## Links

- Matrix row: #51
- Related: #48 (ThinkGeo — step-wise RS tool-use benchmark), #50 (AgriWorld — verifiable agri/RS agent tools), #53 (RSMeM — agent memory evolution)

---

*Linked from: [[Literature-Matrix]]*
