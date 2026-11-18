# 63 — Need-Driven Self-Evolution RS Agents (Sun et al., 2026)

**Full Citation:** Sun, B., Wang, X., Gao, M., Du, Y., & Dong, S. (2026). From evolution to autonomous modeling: need-driven self-system and intelligent agent self-evolution for remote sensing detection. *Egyptian Informatics Journal*, *35*, 101025. https://doi.org/10.1016/j.eij.2026.101025
**DOI:** [10.1016/j.eij.2026.101025](https://doi.org/10.1016/j.eij.2026.101025) | Open Access (CC BY-NC-ND) | Egyptian Informatics Journal 35 (2026) 101025 | online 1 Jul 2026 (accepted 27 Jun 2026)
**Status:** ✅ Full read (2026-10-20, extracted text)
**Themes:** #Agentic-RS #Label-design

---

## What It Does

Proposes a **Need-Driven Self-System** structural model — a formalisation of an organism's need-generation → perception → evaluation → task → execution → feedback loop — and combines it with reinforcement learning to build a **self-evolution model of intelligent agents** whose loss function is switched from MSE to **MAE** for robustness to outlier "needs" (pp. 1, 3–9). The framework is then used to *design* a SAR ship detector, **Auto-T-YOLO**, presented as label-light / unsupervised-learning-capable.

## Key Architecture

- **Self-system model** — differential equations for physiological-system evolution `dMi/dt = Pi(Mi, E)`, perception / decision / visual sub-networks, an attention mechanism `A(t) = Σ wi·Ni(t)`, abstract classification memory `M(t) = F(A(t))`, value/experience evaluation `V(t) = G(M, E)`, task generation `T(t) = H(V)`, and the need–task–execution–new-need cycle (pp. 3–6, Figs. 1–2).
- **Self-evolution agent** — actor–critic: needs `C` generate actions `A = π(C|θ, φ)`; the value network `V(C, a)` is compared against the environment's need `CE1` through target `yi = r(C, A) + γV(CE1, π)`; objective `J(θ, φ) = E[Σ γᵏ r]`. The **loss is MAE, not MSE** (Eq. 29), because self-needs occasionally deviate sharply from environmental needs and MSE penalises those outliers quadratically, destabilising convergence (p. 9).
- **Two-stage visual processing** (the detector's analogue of "need selection"): a **pre-attention** stage splits the images into sub-dataset A (only small targets) and sub-dataset B (all targets with area ≤ 32×32); an **attention** stage fuses features — for A the 3×3 conv block after SPP is replaced by **Multi-Head Self-Attention**, for B a **Transformer** module integrates global→local features; neck = SPP + FPN + PANet; head uses **CIoU-Loss** and **DIoU-NMS**; backbone **CSPDarknet53** (pp. 11–12, Fig. 8).
- **Agent RL demo** — 10×10 maze, +10 for the treasure, −1 per collision, 1 energy per step, ≤ 200 steps per episode, procedurally generated layouts; DDPG baseline (p. 10).
- **Detector setup** — **SSDD** (1,160 images, 2,456 ship targets, 2.12 ships/image, RadarSat-2 / TerraSAR-X / Sentinel-1, 1–15 m, HH/HV/VV/VH), 7:2:1 train/val/test split plus offshore and inshore test subsets; PyTorch 2.x, 2× CUDA RTX 3080Ti, 608×608 input, lr 0.001, momentum 0.9, 20,000 iterations to convergence (pp. 13–14).

## Key Findings

- **Maze experiment (Table 3, p. 14):** self-evolution agent vs DDPG — failures **467 vs 478**, iteration time **365.90 s vs 397.18 s**, optimal decision time **296.65 s vs 308.57 s**, **average reward 6.85 vs 6.13**; the gain is attributed to the MAE loss.
- **SSDD overall (Table 4, p. 14):** Auto-T-YOLO AP **96.3%**, recall **0.96**, precision **0.98**, F1 **0.98**, Pd 0.97, Pm 0.03, Pf 0.02, **20.9 FPS**, 247.8 M parameters — vs YOLOv3 91.84% (recall 0.90) and YOLOv4 90.15%. **YOLO-SRBD is higher at 97.4% AP** and LMSD-YOLO at 96.5%.
- **Offshore scenes (Table 5, p. 14):** Auto-T-YOLO AP **98.99%**, recall 0.98, precision 0.99, Pm/Pf 0.01 — YOLO-SRBD marginally higher at 99.1% AP.
- **Inshore scenes (Table 6, p. 15):** Auto-T-YOLO AP **91.78%**, recall 0.92, precision 0.91, Pm 0.08, Pf 0.09 — YOLO-SRBD higher at 94.23 AP, but against DAPN the proposed model reaches 91.78% vs 77.20% AP (p. 16).
- **Relative gains (p. 15):** versus YOLOv3, accuracy **+3.6%** and recall **+4%**, with the false-positive rate cut to one-fifth.
- **Paper-internal quirks (do not propagate):** Table 4's caption equates "AP (Accuracy)"; §3.2 says "Deep Q-network (DQN)" while the algorithm is DDPG / actor–critic; several baseline rows repeat identical values (e.g. YOLOv3 and DAPN share FPS 20.1 and 243.5 M params) (pp. 8, 14–15).
- ⚠️ **Label-efficiency caveat (the key discrepancy vs the intake note):** although the abstract claims "competitive performance without dependence on large-scale labelled data" (p. 1), the SAR experiment is a **fully supervised** YOLO trained on the 1,160-image labelled SSDD split. **No label-ablation is run anywhere**, and the maze experiment is a synthetic reward task. "Unsupervised / label-efficient" is a design claim, not a measured result.

## Relevance to Thesis

**Optional** — this paper belongs to the **frozen GeoAI-agent cluster (frozen 2026-10-04)** and is **background / future-work material only**; the cluster is not to be extended.

- ✅ It is the agentic-cluster paper **closest in concept to the thesis's active-learning component**: both replace external supervision with a self-generated internal evaluation signal (here a need-driven reward, in the thesis an acquisition function over EO-FM embeddings). Useful as a related-work contrast that makes the thesis's explicit, human-verified label protocol a deliberate choice rather than an oversight.
- ✅ One transferable technical idea: **MAE instead of MSE as an outlier-robust loss** for self-supervised / self-evolving objectives — a legitimate design option for a stress-label acquisition loss.
- ⚠️ The label-efficiency claim is **not substantiated** — the only remote-sensing experiment is fully supervised on SSDD with no annotation-budget ablation, so nothing here can be cited as evidence that the approach reduces annotation cost.
- ⚠️ Domain transfer is weak: SAR ship detection on a 1,160-image benchmark, with no crop, no multi-temporal series, no optical/thermal EO-FM features and no water- or salinity-stress task.
- ⚠️ Internal inconsistencies (AP/Accuracy conflation, DQN vs DDPG, duplicated baseline rows) mean the headline numbers should not be quoted as a benchmark reference.
- ❌ Provides no EO foundation model, no XAI, no active-learning acquisition function, and no agentic RS pipeline the thesis could adopt.

## Key Takeaway

The contribution is conceptual rather than quantitative: a self-generated "need" signal that supervises learning without a human in the loop, which sits one step away from the thesis's active-learning acquisition function and helps explain why keeping an explicit, human-verified label protocol is the right call. The caveat is that the label-efficiency claim is unmeasured — the remote-sensing experiment is fully supervised on SSDD, so no result here can be cited as evidence of reduced annotation cost.

## Links

- Matrix row: #63
- Related: #53 (RSMeM — memory evolution for RS agents, the closest active-learning-style refinement in the frozen cluster), #47 (RS-Agent — canonical agentic baseline), #50 (AgriWorld — verifiable agri/RS agent bridge)

---

*Linked from: [[Literature-Matrix]]*
