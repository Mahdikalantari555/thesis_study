# Thesis Design — Methodology & Implementation Plan

**Created:** 2026-10-04 (consolidates the methodology previously scattered across `00-Thesis-Overview.md` diagram + `deep_researches/advisor_papers_analysis.md` §Implementation Path)  
**Frame:** *A Self-Supervised and Explainable CNN-Mamba Framework for Disentangling Concurrent Water and Salinity Stress from Multi-Temporal Satellite Imagery — Amirkabir Agro-Industrial Unit, Khuzestan, Iran (~490 sugarcane fields, 2013–2025)*  
**Companion docs:** `00-Thesis-Overview.md` (research question, key numbers) · `03-Research-Gaps.md` (G1–G7 evidence) · `Literature-Matrix.md` (rows 01–78)

---

## 1. Positioning (one sentence)

> Wen et al. monitor concurrent drought+salinity descriptively (plant traits + ANOVA, RS 2021 → HESS 2022 → IJAEOG 2023); this thesis adds **predictive, per-field disentanglement with temporal deep learning (CNN-Mamba + SSL) and physiologically-validated temporal XAI in an arid irrigated sugarcane system**.

What the closest program (Wen trilogy) does **not** do — verified against the full text of Wen 2022 (`papers/70-Wen-2022-HESS.md`): no predictive deep models (statistical ANOVA only), no per-pixel/per-field stress-type disentanglement (joint-class effects only), no arid irrigated sugarcane (temperate NL / US crop mix), no SSL, no XAI, and no per-trait retrieval-accuracy validation of their PROSAL/SNAP trait pipeline.

---

## 2. Architecture (planned)

```
Input per field: ~88 timesteps × 16-day composites (2013–2025)
  channels: Landsat 8/9 L2 raw bands (B2–B11) + LST (+ optionally NDVI/NDMI/NDWI)
      │
      ▼
[Per-timestep CNN encoder]  (ResNet-18-style stem — insertion point for LST channel)
      │
      ▼
[Mamba temporal encoder]  (selective SSM; SITSMamba-style Positional Weight)
      │
      ├──────────────────────────────┐
      ▼                              ▼
[SSL pre-training]            [Fine-tuning head]
 temporal contrastive          4 classes: Healthy / Water_Only /
 (positives: same field        Salinity_Only / Mixed_Stress
  across years; negatives:
  different fields, same season)
      │                              │
      └──────────────┬───────────────┘
                     ▼
[Temporal XAI]
 SHAP on Mamba selectivity vectors → which timesteps drive the prediction
 Temporal Grad-CAM → spatio-temporal evidence maps
 Counterfactual probes → "what would healthy look like?"
                     │
                     ▼
[Physiological validation] — explanations must match Angon-style response
 directions (gs↓, Ts↑, Na⁺↑, ROS↑, chlorophyll↓) + CWSI (Zoratipour) +
 LAI (Hajeb/Paciolla) + yield records (Motlagh R²=0.93 baseline)
```

**Architecture source of truth:** SITSMamba (`papers/01`, note `papers/01-SITSMamba.md`) — PW mechanism, reconstruction branch and loss to be pinned at implementation level after the full read; thermal-channel insertion point = CNN stem input channels.

## 3. Four implementation phases

| Phase | Weeks | Content | Gate to pass |
|---|---|---|---|
| **1. Data pipeline** | 1–4 | CFMASK cloud masking (GEE); 16-day composites via cubic-spline resampling; **geometry-aware compositing — consistent viewing geometry / BRDF normalization before temporal stacking (Haq #72: viewing geometry "significantly affects" NDVI/PRI/SIF → "erroneous stress interpretation"; Waters #77: same, sugarcane-specific)**; LST bias correction (RF, following Zoratipour #24); feature stacking raw bands + LST (+ indices as ablation arm; **moisture-accentuating SWIR indices per Waters #77's "heavily considered" finding; angular/anisotropy descriptors as candidate stress-type features per Haq #72 Fig. 9**); zonal aggregation over 490 field polygons | Field×date matrix complete, QC'd cloud gaps < 20%/season |
| **2. SSL pre-training** | 5–8 | CNN-Mamba implementation; temporal contrastive pre-training on all 490 fields × 12 years (no labels needed); Barlow Twins vs SimCLR decision (§5) | Linear-probe / kNN stress-relevant feature quality check |
| **3. Fine-tuning + XAI** | 9–14 | Fine-tune on 50–100 expert-labeled fields; 4-class head; SHAP on selectivity vectors + temporal Grad-CAM; counterfactuals | ≥ competitor baselines (RF on indices; 3D-CAE à la STS-NET; LSTM) + XAI validated (§6) |
| **4. Writing** | 15–18 | Methods/results; Persian thesis chapters + Q1 manuscript draft (RSE / ISPRS / TGRS / CEA) | Advisor sign-off |

## 4. Labels — the design-critical question

- **Classes:** Healthy / Water_Only / Salinity_Only / Mixed_Stress (explicit Mixed class; combined stress is interactive, not additive — Angon et al. 2022, `papers/07`).
- **Candidate label sources** (to be combined; advisor input required — see §7):
  1. Ground ECe measurements for the 490 fields (if accessible — question ①);
  2. Satellite-LAI salinity proxy without ground ECe (Paciolla 2025, `papers/08`) — highest-risk methodological bet; transfer conditions documented in its note;
  3. CWSI thresholds 0.4–0.5 (Zoratipour series `papers/10/24/25`) for the water axis;
  4. Yield records + water×salinity interaction (Motlagh 2026, `papers/09`) for validation and mixed-class consistency;
  5. Operational Mixed_Stress criteria (question ②) — no paper in the corpus defines these; physiology (Angon) gives response directions, not thresholds.
- Soft/mixture labels are preferred over hard classes under severity uncertainty (Tardieu 2018, `papers/41`).

## 5. Decisions to justify in the proposal (currently open, leaning as noted)

| Decision | Options | Current lean + reason |
|---|---|---|
| Raw bands vs indices input (G7) | Raw bands (Rußwurm & Körner 2020) vs VIs | **Raw bands + LST primary, indices as ablation arm** — temporal models learn from raw spectra; indices keep the classical-ML baseline honest |
| SSL pretext | Barlow Twins vs SimCLR | **Barlow Twins lean** — no negative-pair engineering on a small field library (490 fields); decide after Phase-2 pilot |
| Cadence | Landsat-16d vs fused S2 (HLS-like) | **Landsat-16d primary** (uniform 2013–2025 archive, TIRS LST native); fused-S2 as robustness check — BRDF/compositing caveats per Haq 2025 (`papers/72`) |
| Agentic GeoAI (decided 2026-10-04) | Core chapter vs future work | **FROZEN AS FUTURE WORK / optional chapter.** Rationale: 18/78 PDFs (23%) serve an optional component while the claimed novelty (temporal XAI) had 2–3 supporting papers; overview labels agents "optional orchestration"; the 2026-09-10 intake itself framed agents as operationalizers, not contributors. Cluster 47–67 frozen — do not acquire more; G1–G21 notes = background. If the advisor wants it as a core chapter, revisit with Munir design principles + ThinkGeo-style eval. |

## 6. Validation & XAI protocol (draft)

1. **Predictive:** per-class precision/recall/F1 with cross-year (leave-one-year-out) validation — adopted deliberately because the field lacks standardized validation (Gracia Rojas 2026, `papers/74`); uncertainty reporting by design.
2. **Baselines to beat:** RF/XGBoost on indices (Gokul 2026 benchmarks; Zoratipour #24 pipeline); 3D-CAE SSL on VIs (STS-NET, `papers/14`); LSTM/Transformer SITS encoders.
3. **Explainability quality:** (a) physiological consistency — explanation maps must match response directions (gs↓, Ts↑, Na⁺↑, ROS, chlorophyll↓ — Angon `papers/07`); (b) faithfulness metrics on temporal attributions (deletion/insertion on timesteps); (c) expert review round; (d) sanity checks per Höhl 2024 evaluation-practice findings (`papers/04` — exact quotes in its note).
4. **External anchors:** CWSI (Zoratipour 0.4–0.5; Motlagh's own: young 0.40–0.45 / old 0.30–0.35), LAI (Hajeb RMSE 0.48; Paciolla proxy — partial support only), yield (**Motlagh: match/exceed the independent-test R² = 0.821**; headline 0.93 is the full-sample fit), local Ky = 1.05 (Motlagh-Ky, `papers/76`), salinity-label protocol: weekly saturated-paste ECe 0–90 cm (Motlagh's 128-well kriged design).

## 7. Open questions blocking design (advisor — ask FIRST)

1. **ECe ground-truth access** for the 490 fields? (determines salinity-label strategy; Paciolla fallback otherwise)
2. **Operational criteria for labeling "Mixed_Stress"?** (no corpus paper defines them; propose expert-elicited thresholds on CWSI + ECe/LAI-proxy + yield loss)
3. **GPU workstation vs cloud?** (CNN-Mamba pre-training needs ~1×24 GB GPU; GEE covers the pipeline either way)
4. **Timeline approval** for the 4-phase plan (18 weeks) and the release promise of a Khuzestan stress-classification benchmark (G5)?

## 8. Data & assets

- Landsat 7/8/9 L2, 2013–2025, via GEE; Sentinel-2 for LAI fusion; ERA5-Land climate; SoilGrids proxies; 490 Amirkabir field polygons; yield + agronomic records from the agro-industrial unit.
- Repo implementation skeletons to create: `scripts/preprocessing|features|models` (currently empty); SITSMamba reference repo to clone: https://github.com/XiaoleiQinn/SITSMamba.

---

*Last updated: 2026-10-04. Maintenance: update §5 table as decisions are made; tick §7 questions as the advisor answers.*
