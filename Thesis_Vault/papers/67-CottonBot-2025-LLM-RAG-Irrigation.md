# 67 — CottonBot: LLM-RAG + Live Soil-Moisture Agentic Tools for Cotton Irrigation Advice (Kandamali et al., 2025)

**Full Citation:** Kandamali, D. F., Porter, W. M., Porter, E., McLemore, A., & Rains, G. C. (2025). CottonBot: An AI-driven cotton farming assistant and irrigation advisor using LLM-RAG and agentic AI tools. *Smart Agricultural Technology*, *12*, 101640. https://doi.org/10.1016/j.atech.2025.101640
**DOI:** [10.1016/j.atech.2025.101640](https://doi.org/10.1016/j.atech.2025.101640) | Open Access (CC BY) | Smart Agricultural Technology 12:101640; accepted 13 Nov 2025, online 14 Nov 2025 | Funded by USDA-NIFA Award No. 2023-68016-39403 (p. 11)
**Status:** ✅ Full read (2026-10-20, extracted text)
**Themes:** #Agentic-RS #Irrigation #Benchmark

---

## What It Does

CottonBot is a domain-specific conversational assistant for cotton farmers pairing a **static RAG pipeline** over an extension handbook with **three agentic LLM tools** that read live field data. Unlike static agricultural chatbots (AgroLLM, BeefBot) that only paraphrase documents, CottonBot calls a soil-moisture monitoring tool, a weather-forecast tool and an irrigation-decision tool, so its advice is conditioned on the actual moisture profile of the specific field and the coming week's forecast. Everything runs **locally** on open-weight models through Ollama, for cost, privacy and rural-connectivity reasons (pp. 1–2).

## Key Architecture

- **Knowledge base (p. 2):** the **2024 Georgia cotton production guide** (UGA Extension / Georgia Cotton Commission) — varieties, planting, fertilisation, irrigation scheduling, IPM (weeds, insects, diseases/nematodes), harvest/defoliation; decision thresholds plus narrative. Processed with **LangChain**, chunked to **1,000 characters with 100-character overlap**, embedded with **all-MiniLM-L6-v2**, indexed in a vector store (p. 3).
- **Retrieval/generation (p. 3):** top-**5** chunks by cosine similarity → chunks + query → **Llama 3** via **Ollama**, prompted as an agricultural expert; a custom prompt template anchors responses to the retrieved context to suppress hallucination (p. 4).
- **Vector stores (p. 3):** **Chroma** chosen for deployment (built-in persistence, developer-friendly, seamless LangChain integration for the mobile app); **FAISS** used as the benchmarked alternative.
- **Models compared (Table 1, p. 4):** 7 open-weight 4-bit LLMs — Deepseek-r1 7.6B, Llama3 8.0B, Llama2 6.7B, **Llama3.1 8.0B (131,072 ctx, tool calling)**, Phi3 3.8B, **Mistral 7.2B (tool calling)**, Gemma3 4.3B (vision); 6 embedding models (all-MiniLM-L6-v2, jina-embeddings-v2-base-en, e5-base, e5-mistral-7b-instruct, bge-base-en-v1.5, bge-m3).
- **Tool 1 — soil-moisture monitoring (p. 5):** RealmFive watermark sensors on the **South Pivot** field of the D.A.T.A. farm at 8-, 16- and 24-inch depth; per-depth averages combined into a **DAP-aware root-zone weighted index** (Table 2, p. 4): DAP 0 → 0.00/0.00/0.00 (not germinated); 1–12 → 0.80/0.20/0.00; 13–23 → 0.60/0.30/0.10; 24–27 → 0.50/0.30/0.20; 28–34 → 0.50/0.25/0.25; 35–160 → 0.40/0.30/0.30. The weights follow UGA Extension guidance, which warns that equal weighting across depths misrepresents crop water status, causing premature stress early and over-irrigation later (p. 4).
- **Tool 2 — weather forecast (p. 5):** OpenWeatherMap temperature/humidity/precipitation out to **7 days** — defers irrigation when rain is forecast, increases it under heat/drought, raises alerts.
- **Tool 3 — irrigation decision (p. 5):** weighted soil-water tension vs. a cotton threshold of **45 kPa** → *Irrigate* if the weighted index ≤ 45 kPa, else *Wait*; refined by the 7-day forecast and the forward soil-moisture prediction.
- **Prediction model:** an **existing hybrid LSTM soil-moisture model** (cited prior work, ref. 28) forecasting the DAP-aware weighted index **up to 7 days ahead at over 98 % R²** (p. 5).
- **Deployment (pp. 5–6):** **FastAPI** backend + **Flutter** front end (Android/iOS/web), Firebase authentication, HTTPS/TLS, local caching of query/response history for offline fallback, GDPR-like data handling; a Streamlit prototype served as the RAG evaluation harness (p. 6).
- **Geographic setting (p. 2):** the **(D.A.T.A) 4D-Project farm, Abraham Baldwin Agricultural College, Tifton, Georgia, USA** — 4 fields (North Pivot, South Pivot, Front Field, West Field), **12 soil-moisture sensors**, one shared weather station. (The PDF's allocation sentence is internally inconsistent — North and South pivots get 4 sensors each, then it says "the front and south pivots have two each", i.e. South Pivot is counted twice — so only the 12-sensor total and the South Pivot instrumentation are unambiguous.) Humid subtropical southeastern-US cotton, **not** arid or semi-arid.

## Key Findings

- **Retriever (Table 3, p. 9):** best combination **all-MiniLM-L6-v2 + FAISS** — MRR **0.8855**, Recall@5 **0.9476**, Precision@5 **0.9285**; the same model on Chroma gives MRR 0.8715 / R@5 0.9375 / P@5 0.9175. **FAISS consistently outperformed Chroma across all six embedding models** (p. 9). Next best on FAISS: bge-base-en-v1.5 (MRR 0.8805); weakest: e5-base (MRR 0.8225).
- **Generator (Table 4, p. 9):** **Llama3.1 8B** best — faithfulness **0.9681**, cosine similarity **0.9523**, **6.2 s**/query; Llama3 close (0.9617 / 0.9517 / 6.2 s); Deepseek-r1 0.9412 / 0.9388 / 6.4 s; Llama2 worst (faithfulness **0.8088**); fastest were Phi3 (2.3 s) and Gemma3 (3.4 s) but less faithful (0.8792 / 0.8529).
- **Agentic-tool evaluation (p. 8):** CottonBot's 1-day-ahead soil-moisture-tension forecast achieves **MAE < 1.0** versus **MAE 1.4** for the manual heuristic baseline, with **100 % agreement** with sensor-based irrigate/wait decisions at the 1-day horizon. Sample output: weighted root-zone tension **52.3 kPa** → "Apply 0.75 inches of irrigation within the next 24 hours", no rain in the next 48 h.
- **Field-trial status — no on-farm results exist yet (p. 8):** "CottonBot's irrigation logic and agentic reasoning tools have been validated computationally, large-scale on-field validation remains ongoing"; planned **2026 growing-season** experiments at the ABAC Tifton 4D-Farm will measure irrigation frequency, soil-water recovery rate and yield improvement against farmer practice (repeated as future work, p. 10). The paper therefore reports a **computational evaluation and a planned field trial, not a completed field trial**.
- **Hallucination handling (pp. 9–10):** responses grounded in retrieved chunks with citation-fidelity prompts, plus a logging layer for retrieval overlaps and confidence signals; LLM-as-a-judge and automated fact-checking are future work.

## Relevance to Thesis

**Optional** — frozen GeoAI-agent cluster (frozen 2026-10-04); background / future-work material only, and no extension of that cluster is proposed:
- ✅ The most directly transferable *design* in the cluster for a decision-support artefact: RAG for static agronomic knowledge + a few deterministic tools over live measurements, with the LLM only orchestrating and verbalising (p. 5).
- ✅ The **DAP-aware depth-weighted root-zone index** (Table 2, p. 4) is a transferable, literature-anchored way to turn a soil-moisture profile into a crop-stage-specific scalar — an explicit alternative to index-based CWSI on the thesis's water-stress side.
- ⚠️ No remote sensing: no EO imagery, no thermal, no multi-temporal analysis; the only EO reference is an aside that competing chatbots rely on static document corpora (pp. 2, 10).
- ⚠️ Humid Georgia cotton, single farm, 12 sensors — transfer to arid irrigated sugarcane in Khuzestan (different soil texture, salinity regime, irrigation practice) is untested, and the 45 kPa tension threshold is cotton- and soil-specific.
- ⚠️ The decision is a single-threshold rule on a weighted scalar with **no mechanism for concurrent or competing stresses** (e.g. salinity raising soil-water tension independently of crop water demand) — exactly the thesis's problem statement.
- ❌ No stress-detection method, no label protocol, no foundation model, no active learning, no XAI; the promised field-trial evidence does not exist yet.
- ⚠️ The intake note (G21) framed the system as a "decision-support template" without noting that the field-trial evaluation was unexecuted; the PDF is the authority.

## Key Takeaway

CottonBot demonstrates the pattern a thesis decision-support layer would imitate — ground a conversational agent in a curated knowledge base and let a few deterministic, physics-anchored tools (here: DAP-weighted root-zone tension vs. 45 kPa plus a 7-day forecast) do the actual reasoning — while its own numbers show the limits: single-threshold irrigation logic, no EO input, and a field trial still pending for 2026. Cite it as a design precedent and open-source stack reference, not as validation evidence.

## Links

- Matrix row: #67
- Related: #65 (Tariq et al. — the other edge-IoT decision-loop paper in the cluster), #66 (Musazade et al. — LLM/VLM plant-stress review), #73 (Gokul et al. — UAV CWSI review), #61 (Zhang et al. — pixel-wise irrigation water use, the thesis-side irrigation-hydrology anchor)

---

*Linked from: [[Literature-Matrix]]*
