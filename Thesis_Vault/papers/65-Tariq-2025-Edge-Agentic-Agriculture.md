# 65 — Edge-Enabled Smart Agriculture: IoT + Lightweight Deep Learning + Rule-Based Agentic AI (Tariq et al., 2025)

**Full Citation:** Tariq, M. U., Saqib, S. M., Mazhar, T., Khan, M. A., Shahzad, T., & Hamam, H. (2025). Edge-enabled smart agriculture framework: Integrating IoT, lightweight deep learning, and agentic AI for context-aware farming. *Results in Engineering*, *28*, 107342. https://doi.org/10.1016/j.rineng.2025.107342
**DOI:** [10.1016/j.rineng.2025.107342](https://doi.org/10.1016/j.rineng.2025.107342) | Open Access (CC BY-NC-ND) | Results in Engineering 28:107342; accepted 16 Sept 2025, online 17 Sept 2025
**Status:** ✅ Full read (2026-10-20, extracted text — methods, validation, results, conclusion)
**Themes:** #Agentic-RS #Irrigation #Dataset

---

## What It Does

An **edge-first smart-farming framework**: two small Vision-Transformer classifiers running on resource-constrained hardware feed a *rule-based* "agentic" layer that actuates IoT devices (irrigation, NDVI probe, frost alarm, drone dispatch, pest detector). The models are trained independently — one for **11 weather classes**, one for **5 crop types** — and their outputs are crossed in a weather × crop risk-action matrix so a single frame can trigger a coordinated intervention. The claim is autonomy of *action* under explicit, auditable policies at the edge, explicitly **not** LLM reasoning or learned planning (p. 4).

## Key Architecture

- **Backbone:** `nvidia/mit-b0` (MiT-B0) ViT for **both** models, input 128 × 128, CPU-only inference targeted (p. 5). Lightweight CNN backbones (MobileNet/EfficientNet-Lite) were *not* benchmarked (p. 14).
- **Datasets:** weather — **3,428 images**, 11 classes (dew 349, fog/smog 425, frost 237, ground-ice/"glaze" 319, hail 295, lightning 188, rain 263, rainbow 116, rime 580, sandstorm 346, snow 310; p. 5); crop — **804 images** (jute 160, maize 160, rice 160, sugarcane 160, wheat 164; p. 6).
- **Training (p. 5):** 10 epochs, Adam, lr 1 × 10⁻⁴, momentum 0.9, weight decay 1 × 10⁻⁵, batch 32, 4 workers; normalisation mean [0.48, 0.47, 0.42], std [0.226, 0.225, 0.227].
- **Agentic layer (p. 4):** closed **perception → decision → actuation** loop; the paper states it claims *no* learning-to-plan or stochastic policy optimisation — "agentic" means "autonomy of action under explicit, auditable policies deployed at the edge".
- **Policy encoding (6 steps, pp. 4–5):** action primitives → weather × crop risk-action matrix (with a default non-intervention row) → trigger spec + guardrails (joint rules when both models are confident, fallback single-condition rules, tie-breakers, debounce / minimum on-off / rate limiting) → table-driven verification → YAML/JSON policy table loaded at startup → change management (edit → lint/validate → re-run tests → deploy).
- **Edge protocol (p. 4):** ONNX export at 1 × 3 × 128 × 128 (FP32 reference, optional post-training quantisation); Raspberry Pi 4 (ONNX Runtime CPU) or Jetson Nano (TensorRT); GPIO actuation via `gpiozero` / `RPi.GPIO` / `Jetson.GPIO`; offline by default; configuration parity with the workstation studies.
- **Runtime environment (p. 4):** all Python case studies ran in **Google Colab** (Intel Xeon vCPU, 12–16 GB RAM, Ubuntu 20.04, Python 3.10, PyTorch 2.1.0, NVIDIA T4 GPU) — a GPU cloud VM, not the edge target.

## Key Findings

- **Crop model (pp. 7, 13–14):** accuracy **93 %**, precision 94 %, recall 93 %, F1 **0.93**, MAE 0.1116; Jute and Maize F1 = 0.95, Rice recall 0.98 (p. 7). Beats the compared literature range of 71–90 % accuracy (p. 13, Table 9).
- **Weather model (pp. 7, 13–14):** accuracy **88 %**, F1 0.88, MAE 0.5277; 'Rainbow'/'Rain' F1 ≈ 0.99 (p. 7). **Discrepancy:** §4.1 and Table 8 (p. 13) report the proposed WeatherModel at **87 %** accuracy with MAE "52.77 %", while the abstract, the contributions (p. 2) and the Conclusion (p. 14) report **88 %** and MAE 0.5277 — the paper never reconciles the two.
- **Decision behaviour (pp. 10–11):** applied example 1 (crop = Rice, weather = Rain) fires a combined rule → *pause irrigation* + *check for water saturation to avoid overflooding*; example 2 (wheat + fog/smog) falls back to separate single-condition rules.
- **Deployment claims are architectural, not measured (p. 14):** no Raspberry Pi / Jetson benchmarks exist; "our edge-deployment claims are architectural and software-completeness statements rather than performance measurements". No multi-season field trial and no physical hardware deployment — evaluation was limited to Python case studies on a workstation.
- **Other internal inconsistency:** the intro says live camera imagery is "processed every hour" (p. 2), while Table 10's merits column claims "real-time crop + weather imaging every 5 s" (p. 13).

## Relevance to Thesis

**Optional** — frozen GeoAI-agent cluster (frozen 2026-10-04); background / future-work material only, and no extension of that cluster is proposed:
- ✅ The only item in this cluster touching irrigation actuation: it documents the concrete edge-IoT loop shape (perceive → policy lookup → actuate → re-evaluate) and the guardrail vocabulary (debounce, minimum on/off duration, rate limiting) a fielded decision-support system would need.
- ✅ Sugarcane appears as one of the 5 crop classes — the thesis crop family — though only as a scene-classification label.
- ⚠️ No remote sensing, no multi-temporal data, no thermal/LST, no salinity, no EO foundation models, no active learning; the "agent" is deterministic rules, not an LLM (the paper explicitly prefers rule-based over "heavy edge LLM support", p. 13).
- ⚠️ The evaluation is a workstation case-study harness on a Colab T4 GPU with no field deployment, so the robustness claims do not transfer to arid, dusty, connectivity-limited Khuzestan conditions.
- ❌ Provides no stress-detection method, no label protocol and no validation design usable in the thesis; 128 × 128 RGB crop/weather classification is not a stress task.
- ⚠️ The intake note (G19) rated this "MEDIUM" and proposed coupling lightweight edge classifiers with EO-FM embeddings and LLM agents; that extension proposal is superseded by the frozen-cluster calibration and is recorded only as a discrepancy.

## Key Takeaway

The canonical *edge-side* reference point of the frozen agentic cluster — it shows what "agentic at the edge" means without LLMs, and how thin the supporting evidence is (no field trial, no hardware measurements, an 804-image crop dataset). Cite it as background for a deployment-oriented discussion, never as a method or validation source.

## Links

- Matrix row: #65
- Related: #67 (CottonBot — RAG + live soil-moisture tools, the other irrigation-decision paper in the cluster), #66 (Musazade et al. — LLM/VLM plant-stress review), #63 (Sun et al. — need-driven self-evolution RS agents), #73 (Gokul et al. — UAV CWSI review, the thesis-side proximal-validation anchor)

---

*Linked from: [[Literature-Matrix]]*
