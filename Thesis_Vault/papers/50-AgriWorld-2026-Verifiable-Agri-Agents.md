# 50 — AgriWorld: A World–Tools–Protocol Framework for Verifiable Agricultural Reasoning with Code-Executing LLM Agents (Zhang et al., 2026)

**Full Citation:** Zhang, Z., Zhang, J., Liu, H., Lv, Q., Yang, J., Cai, K., & Wang, K. (2026). AgriWorld: A World–Tools–Protocol framework for verifiable agricultural reasoning with code-executing LLM agents. *arXiv preprint arXiv:2602.15325*. https://arxiv.org/abs/2602.15325
**DOI:** [arXiv:2602.15325](https://arxiv.org/abs/2602.15325) (v1 [cs.AI], stamped 17 Feb 2026) | Sun Yat-sen University | **no code or data-availability URL given in the PDF**
**Status:** ✅ Full read (2026-10-20, extracted text) — **frozen GeoAI-agent cluster**
**Themes:** #Agentic-RS #Irrigation #Benchmark #Dataset

> **Frozen-cluster statement.** This paper belongs to the **GeoAI-agent cluster, frozen on 2026-10-04** (matrix rows 47–59, 63–67) as **background / future-work material**. It is the closest agricultural bridge in that cluster, but the cluster is **not to be extended** by this note.

---

## What It Does

AgriWorld argues that agricultural questions cannot be answered from text: they require **parcel–pixel–grid alignment, stage-specific temporal windows, unit-sensitive computation and simulator runs**. It therefore packages agriculture as a **World–Tools–Protocol** stack: a **Python execution environment (AGRIWORLD)** that exposes typed, unified APIs over field parcels, raster time series, soil/terrain grids, weather streams and management logs; an **execute–observe–refine LLM agent (AGRO-REFLECTIVE)** that writes code, reads back inspectable artifacts, and self-corrects; and a **verifiable protocol** whose checkers test schema, numeric tolerance, causal direction and physical sanity. Evaluation uses **AGROBENCH**, a verifiable suite converted from an existing agricultural benchmark into tool-grounded instances with deterministic reference programs.

## Key Methodology

- **AGRIWORLD state space S — five typed entities** (p. 3): **Parcels P** (polygon geometry, CRS, attributes such as crop type); **Raster Time Series R** (4-D tensors, grid map M: ℝ^{2×T} → ℝ^k, spectral bands + validity mask for cloud cover); **Grid Fields G** (static layers — soil texture, DEM — on a canonical grid); **Weather Streams W** (time series of exogenous drivers: precipitation, radiation); **Management Logs M** (discrete event sequences, e.g. irrigation events with quantities).
- **Tool execution as a state transition producing an auditable artifact** (p. 3): (v̂, α) = f(s_in; θ), with α = ⟨type, payload, meta, prov⟩; **meta** carries units/CRS/resolution and **prov = H(f, s_in, θ)** is a cryptographic hash of inputs and tool version, "ensuring strict reproducibility of scientific claims".
- **Canonical alignment operator** Π(x) = (T_resample ∘ S_reproject)(x): reproject to a task CRS (e.g. EPSG:3857 for metric calculation) and resample to a canonical temporal frequency (e.g. daily) with defined nearest/linear policies (p. 3).
- **Robust zonal statistics** with validity mask (p. 3): µ(p,r) = Σ m_i r_i / Σ m_i, validity ratio ν(p,r) = Σ m_i / |Z(p)|; a **LowCoverageError** is raised when ν < τ_min, "preventing hallucinations based on corrupted data".
- **Tool inventory (Table 1, p. 4)** — five families:
  - *Geospatial Querying*: `geo.filter_parcels(region, crop, area_range)`, `geo.sjoin(parcels, sensor_footprints)`
  - *Remote-Sensing Analytics*: `rs.load(index, time_range, region)`, `rs.zonal_stats(raster_ts, parcels, stat={mean,…})`, `rs.anomaly(ts, baseline_window, method)`
  - *Soil/Terrain Access*: `grid.sample(gridfield, parcels)`, `grid.aggregate(gridfield, region)`
  - *Weather Variables*: `wx.get(station/region, time_range)`, `wx.rolling_sum/degree_days(…)`
  - *Simulation & Predictors*: `sim.run(parcels, wx, soil, mgmt, intervention)`, `pred.stress/yield/disease(…)`
- **AGRO-REFLECTIVE agent** (p. 4): policy π_θ(c_t | m_{t−1}); observation (o_t, O_t) ← E(c_t); trace τ_t = ⟨(c_1,o_1,O_1),…⟩; reflection as diagnostic ρ: c_{t+1} = ρ(c_t, d_t, M(α_t)), classifying errors (e.g. **SpatialMisalignment**, **UnitError**) and proposing targeted patches. Algorithm 1 (p. 5) runs an **execute–observe–refine loop with max budget T = 20**, early-stopping as soon as the checker V passes.
- **Verifiable protocol V — four hierarchical constraint levels** (pp. 4–5): **Schema Validity** (strict JSON schema S_out); **Numeric Tolerance** (|ŷ − y*| < δ against a reference simulator); **Counterfactual Consistency** (M(s,a_intervene) − M(s,a_baseline) ≤ −Δ, i.e. the causal direction must be right); **Physical Sanity** (dimensional homogeneity of units, and valid-pixel coverage ν > τ_min). The framework additionally enforces *Pattern Validity*, *Numerical Conservation*, *Semantic Consistency* and *Temporal Error* fixing (p. 3, Fig. 1).
- **AGROBENCH** (pp. 2, 5): built **on top of an existing agricultural benchmark** (never named in the PDF), converted into tool-grounded instances with deterministic reference code and executable checkers. Four capability families: **lookups** (indices, phenology, resource use), **forecasting/monitoring**, **anomaly detection**, **counterfactual "what-if" intervention analysis**. QA domains: **Animal, Plant, Aquatic, Herb**. Metrics: exact-match accuracy (lookups), **NRMSE** (forecasting), **Spatial IoU** for anomaly masks against ground truth "derived from Sentinel-2 satellite imagery" (e.g. identifying water-stress zones), and **Causal Consistency** for counterfactuals.
- **Baselines & setup** (p. 5): Qwen3 (8B / 32B) fine-tuned with **LoRA**; compared against text-only, one-shot "Code Interpreter" (AgriWorld-Direct), and external backbones Qwen3, DeepSeek-V3, Yi-1.5-34B, LLaMA 3, GPT-4o, Gemini-2.0.

## Key Findings

| Result | Value | Source |
|---|---|---|
| Ablation (avg. accuracy) | Text-Only **21.9%**; AgriWorld-Direct one-shot **48.2%** (1.0 turn); w/o RS 41.5% (2.4 turns); w/o Alignment 51.3% (3.1 turns); w/o Reflection 50.6%; **Agro-Reflective (full) 57.6%** (3.5 turns) | Table 2, p. 4 |
| Main benchmark (Qwen3-32B-LoRA-Reflective) | QA **7.72/541** (Animal 7.45/118, Plant 7.76/325, Aquatic 7.68/74, Herb 8.66/24); choice accuracy **73.84%** | Table 3, p. 7 |
| Same system, 8B | QA 6.25/541; choice **41.34%** | Table 3, p. 7 |
| Base-model controls | Qwen3-32B-LoRA 7.42/541, 67.25%; Qwen3-8B-LoRA 5.84/541, 57.55%; Qwen3-32B 5.67/541, 39.67% | Table 3, p. 7 |
| Proprietary baselines (150-task subset) | GPT-4o 7.07, **36.75%**; Gemini-2.0-Flash 3.90, 55.33%; DeepSeek-V3 4.17, 57.43%; Yi-1.5-34B-Chat 5.67, 35.38% | Table 3, p. 7 |
| Task-type breakdown | Lookup 41.2 → 82.5 → **86.7%**; Forecasting NRMSE 0.89 → 0.34 → **0.18** (≈47% error reduction); Anomaly IoU 0.12 → 0.51 → **0.68**; Counterfactual success 14.5 → 43.8 → **71.4%** (text-only / one-shot / reflective) | Table 4, p. 7; §4.2, p. 6 |
| Removing the RS module | crop-monitoring task performance **dropped by over 40%** | §4.3, p. 6 |
| Removing canonical alignment | "surge in runtime errors" — WGS84 GPS joined against projected UTM rasters yields **empty intersection sets** | §4.3, p. 6 |
| Value of the reflection loop | **35%** of initial code generations contained bugs; the loop recovered **92%** of them | §4.3, p. 6 |
| Budget scaling | T = 1 → 4: 48.2% → **68.5%**; T = 4 → 20: +5.3%; **average convergence in 3.5 turns** despite a T = 20 budget | Fig. 2, §4.4, p. 6 |
| OOD robustness (IID → spatial OOD → temporal OOD) | Text-Only 41.2 → 18.5 (**−55%**) → 22.1 (−46%); One-shot 48.2 → 26.4 (−45%) → 35.8 (−26%); **Agro-Reflective 73.8 → 64.5 (−12%) → 69.2 (−6%)** | Table 5, p. 7 |
| OOD settings | Spatial = **Brazil vs. California** (Southern-Hemisphere crop calendar); Temporal = **2023, an El Niño year** | §4.5, p. 7 |

### Which agricultural tasks and datasets it actually covers

- **Crops/parcels:** crop-type lookup per parcel, phenology, resource use, yield forecasting, **stress** and **disease** predictors, and crop growth simulation with **counterfactual interventions** (`sim.run(..., intervention)`; `pred.stress/yield/disease`). Irrigation appears as both a management-log event and the counterfactual lever ("Does irrigation *I* reduce stress?", p. 4).
- **Water:** the motivating question is literally "Which parcels are likely to experience **water stress** next week, and what irrigation adjustment would mitigate the risk?" (p. 1); anomaly detection targets **water-stress zones** scored by IoU against Sentinel-2 ground truth (p. 5); "soil moisture" is one of the forecasting targets (p. 5) and the canonical hallucination example (inventing `get_soil_moisture()` instead of the real `grid.sample()`, pp. 5–6).
- **Datasets:** the PDF names **no** soil, weather or crop dataset — no USDA/Cropland Data Layer/ERA5-style sources are cited. The only remote-sensing dataset named anywhere is **Sentinel-2**, and only as the anomaly-detection ground truth (p. 5). Geography: **California** in-distribution, **Brazil** as spatial OOD.
- **Not present:** salinity, thermal/LST, CWSI, multi-temporal SITS deep learning, sugarcane, any explainability method, and any salinity/water disentanglement.

### ⚠️ Discrepancies with the intake note (G4) — the PDF wins

1. **"Exact tables and scores not available in first-page extract"** — now resolved: Tables 2–5 give full numbers (see above). The intake note's "qualitative superiority" is in fact **quantified**.
2. **"AgroBench, a verifiable agricultural QA benchmark"** is right, but the PDF adds that it is built **on top of an existing agricultural benchmark** (p. 2) — and **never names that benchmark**. Treat AGROBENCH's provenance as unspecified.
3. **Intake omits half the toolset and the whole state model**: it lists "geospatial parcel queries, RS time series, crop simulation, yield/stress/disease predictors" but misses the **soil/terrain grid** and **weather** tool families (Table 1, p. 4) and the five typed state entities (p. 3).
4. **Internal inconsistency in the PDF itself** (flag, do not propagate): the *full* Agro-Reflective system is reported at three different accuracies — **57.6%** (Table 2, p. 4), **73.84%** choice accuracy (Table 3, p. 7) and **73.8%** IID accuracy (Table 5, p. 7) — and Table 2 also lists two distinct one-shot variants (48.2% "AgriWorld-Direct" vs. 50.6% "w/o Reflection") with no stated distinction. Cite the table and its metric alongside any number.
5. **Task-instance tuple is garbled in the extraction**: I = ⟨q, B, S_out, V, B⟩ uses the same symbol `B` for both the *bindings* (parcel IDs, time intervals, sensor products) and the *computational budget* (p. 3). Reconstruct from the prose, not the symbol list.

## Relevance to Thesis

**Low-Medium** — it genuinely touches agriculture and water, but it is still **background / future-work material in the frozen GeoAI-agent cluster (frozen 2026-10-04)**; do not extend the cluster.

- ✅ The most credible agri-agent bridge in the corpus, and the only one whose *evaluation* is executable: unit-consistency checks, validity-ratio (`ν`) guards against cloud-corrupted pixels, and IoU-scored water-stress anomaly masks are all transferable *protocol* ideas for the thesis's label/validation design (p. 3, p. 5).
- ✅ Its **spatial-OOD / temporal-OOD stress test** (California → Brazil; 2023 El Niño year, Table 5, p. 7) is a directly reusable robustness design for multi-region, multi-year validation.
- ✅ The **alignment-and-unit-error analysis** (WGS84 × UTM joins producing empty intersections, p. 6) is a concrete warning about exactly the parcel-level join the thesis needs for Khuzestan field polygons.
- ⚠️ **The numbers do not transfer.** Even the best system reaches only **57.6%** average accuracy in the ablation and **73.84%** choice accuracy on the benchmark; the related ThinkGeo benchmark shows <6% final-answer accuracy on SAR. The claims rest on *retrieval and simulation over an existing benchmark*, not on a learned stress representation — there is no trained crop-stress model to borrow.
- ❌ No salinity, no thermal, no SITS encoder, no XAI, no Iran/Khuzestan, no in-situ salinity ground truth. It offers **zero** support for the concurrent water-vs-salinity disentanglement claim.

## Key Takeaway

The single most useful element is the **"validity ratio" + executable-checker protocol** — computing parcel statistics only over valid pixels and raising `LowCoverageError` below τ_min (p. 3) is precisely the guard a cloud-prone optical stress pipeline needs, and it pairs naturally with the thesis's own data-quality concerns. The honest caveat: AgriWorld is an *orchestration* contribution evaluated on a converted general-agriculture benchmark, its imagery provenance is essentially undocumented, and it contains nothing on salinity, thermal physics or temporal stress modelling.

## Links

- Matrix row: #50
- Related: #47 (RS-Agent — the generalist RS agent whose orchestration layer AgriWorld generalises), #48 (ThinkGeo — the step-wise benchmark for the same agent family), #66 (LLM/VLM plant-stress phenotyping review), #67 (CottonBot — RAG irrigation agent), #54 (Earth-Agent-Pro — Agriculture & Drought domain)
- Frozen cluster: rows 47–59, 63–67 — background / future-work only

---

*Linked from: [[Literature-Matrix]]*
