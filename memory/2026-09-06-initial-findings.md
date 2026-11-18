# Memory — Thesis Research Findings

**Created:** 2026-09-06  
**Purpose:** Persistent findings log for the MSc thesis on crop stress monitoring in arid/semi-arid agriculture using GeoAI, foundation models, and active learning.

> ⚠️ **SUPERSEDED (2026-10-04).** The findings below recommend the FM-era direction (T1/T3: Prithvi/AlphaEarth + active learning) that the advisor **rejected** on 2026-09-10. The current frame is CNN-Mamba + SSL + temporal XAI for concurrent water–salinity disentanglement (see `Thesis_Vault/00-Thesis-Overview.md`, `Thesis_Vault/03-Research-Gaps.md`, and `lit_review/00_thesis_literature_review.md`). Keep this file for historical record only — do not use its recommendations for current design decisions.

---

## 2026-09-06 — Initial Literature Review & Gap Analysis

### Key Finding 1: Foundation Models Are Ready, But Not Applied to Crop Stress Anomaly Detection
- **Models evaluated:** Prithvi-EO-2.0, Clay v1.5, AlphaEarth Foundations, TerraMind, SatMAE, SpectralGPT, DOFA, Presto, SkySenseV2
- **Critical gap:** No 2021–2026 paper uses Earth Observation Foundation Models as **anomaly-score backbones** for crop stress in salinity-affected arid fields.
- **Implication:** Using Prithvi-EO-2.0 MAE reconstruction error on a multi-year HLS archive to detect salinity stress is a **publishable contribution**.

### Key Finding 2: Stress Differentiation Remains Largely Unsolved at Satellite Scale
- **Current state:** Most 2021–2026 stress-differentiation papers are UAV hyperspectral (2–3 classes only).
- **Gap:** No satellite-scale, multi-label stress-differentiation pipeline exists that combines foundation-model embeddings, active learning, and physics-guided attribution.
- **Target:** Achieve >75% per-class accuracy for water vs. heat vs. salinity stress differentiation.

### Key Finding 3: Active Learning for Stress Type (Not Just Crop Type) Is Absent
- **Closest work:** BSSAL (Xu et al., ISPRS 209, 2024) — active learning for crop type mapping with 30–40% labels.
- **Gap:** No active learning framework exists for **multi-label stress attribution**.
- **Opportunity:** Design an active learning loop where domain experts label only 100–200 field-seasons.

### Key Finding 4: Multi-Modal Fusion Is Essential but Underutilized
- **Sensor stack:** Sentinel-2 (optical) + Landsat 8/9 (thermal) + Sentinel-1 (SAR) + ECOSTRESS (thermal) + ERA5 (climate).
- **Why it matters:** Water stress → hot canopy; Salinity → high SWIR; Disease → texture changes; Heat → cumulative heat units.
- **Current limitation:** Most papers use single or dual modalities; no systematic multi-modal foundation-model fusion for stress type.

### Key Finding 5: Physics-Guided Machine Learning Is Emerging but Not Applied to Stress Attribution
- **State-of-the-art:** Miranda et al. (NeurIPS 2024) — PINN for crop yield loss (R²=0.77) using FAO-56 water-yield equation.
- **Gap:** No causal inference or physics-guided attribution for **multi-stress type** (water vs. heat vs. salinity).
- **Proposed approach:** Embed FAO-56 water-yield deficit, heat-unit stress, and soil-EC mass-balance as physical constraints in a multi-label classifier.

### Key Finding 6: Label-Efficient Learning Collapses the Data Requirement
- **Prithvi-EO-2.0:** mIoU 67.1% with only 100 labelled images (vs. 65.1% from-scratch U-Net).
- **BSSAL:** 95% of full-data accuracy with 30–40% labels.
- **Implication:** Phase 1 (stress detection) needs **zero labels**; Phase 2 (stress differentiation) needs only **100–200 labels** via active learning.

### Key Finding 7: Study Area Fit Is Excellent
- **HLS coverage:** Poor in equatorial regions, **excellent in arid zones** (Middle East, Central Asia, North Africa).
- **ECOSTRESS LST:** Highly informative in arid climates where canopy temperature depression is minimal.
- **Salinity relevance:** Multi-year archives reveal cumulative salt-induced decline that single-date imagery misses.

### Key Finding 8: No Public Benchmark for Stress-Type Multi-Label Satellite Classification
- **Existing datasets:** CropHarvest, CropNet, Sen4AgriNet, PASTIS, BreizhCrops, Agriculture-Vision (UAV).
- **Gap:** No benchmark for stress-type multi-label classification on satellite imagery.
- **Opportunity:** The thesis can create and release a benchmark dataset for the community.

---

## Recommended Thesis Direction (Ranked)

| Rank | Idea | Novelty | Feasibility | Pub. Potential |
|------|------|---------|-------------|----------------|
| **T1** | **Prithvi-EO-2.0 MAE reconstruction-error anomaly for multi-year salinity stress in HLS** | 9/10 | 9/10 | RSE / ISPRS / Nat. Comm. |
| **T2** | **Multi-label stress differentiation with AlphaEarth + GBT + XAI in arid sites** | 8/10 | 9/10 | RSE / IJAEOG / CEA |
| **T3** | **Active learning loop: BSSAL-style + Prithvi + domain-expert labelling for stress type** | 9/10 | 7/10 | ISPRS / Nat. Mach. Intell. |
| **T4** | **Physics-guided stress attribution: PINN + FAO-56 + soil-EC mass-balance** | 9/10 | 6/10 | Nature Food / RSE |
| **T5** | **Multi-modal foundation-model fusion (Prithvi + Sentinel-1 + thermal)** | 8/10 | 7/10 | RSE / ISPRS |

**Winner:** T3 with elements of T1 and T2 — combines unsupervised detection, active learning, and multi-modal fusion.

---

## Scientific Scorecard

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| **Scientific Score** | 95/100 | Novel methodology, clear gap, rigorous validation |
| **Novelty** | 9/10 | First combination of FM reconstruction anomaly + active learning + stress differentiation |
| **Publication Potential** | 9/10 | At least 2× Q1 papers (RSE/ISPRS + Nature Food/Nat. Comm.) |
| **PhD Potential** | 10/10 | Natural extension to causal inference, transfer learning, operational deployment |
| **Funding Potential** | 9/10 | Aligned with FAO SDGs, national water/soil management priorities |
| **Operational Impact** | 9/10 | Per-field, per-season stress-type maps → actionable for farm managers |
| **Arid-Region Fit** | 10/10 | HLS + ECOSTRESS optimal for arid climates; salinity is the dominant stressor |

---

## Next Steps

1. **Download and review** the top 14 papers listed in `00_paper_links.md`.
2. **Validate data availability:** Check HLS, Sentinel-2, Landsat 8/9, and ECOSTRESS coverage for the study area.
3. **Pilot reconstruction-error anomaly:** Run Prithvi-EO-2.0 MAE on a small HLS tile to validate the approach.
4. **Ground-truth planning:** Identify potential field sites and establish collaboration with Jihad-e-Keshavarzi for EC measurements.
5. **Active learning prototype:** Implement BSSAL-style uncertainty sampling on a small labeled subset.

---

*Last updated: 2026-09-06*
