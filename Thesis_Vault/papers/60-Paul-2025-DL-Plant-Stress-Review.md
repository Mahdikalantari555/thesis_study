# 60 — DL for Plant Stress Detection: Comprehensive Review (Paul et al., 2025)

**Full Citation:** Paul, N., Sunil, G.C., Horvath, D., & Sun, X. (2025). Deep learning for plant stress detection: A comprehensive review of technologies, challenges, and future directions. *Computers and Electronics in Agriculture*, 229, 109734.
**DOI:** [10.1016/j.compag.2024.109734](https://doi.org/10.1016/j.compag.2024.109734) | Open Access (CC BY-NC-ND) | **CrossRef citations: 88 (2026-10-04) — 2nd most-cited of our second-tier queue**
**Status:** ✅ Full read (2026-10-04)
**Themes:** #SSL #Label-scarcity #Stress-DL #Related-work

---

## What It Does

PRISMA systematic review (ScienceDirect + Scopus + WoS, 2014–2024) of deep learning for plant-stress detection: **1,645 records → 163 final studies**, organized by pipeline stage (acquisition → preprocessing → DL techniques) rather than by stress type.

## Verified Scope Numbers (p. 3, Tables 1–3)

| Statistic | Value | Source |
|-----------|-------|--------|
| Records identified | 1,645 (SD 1,345 / Scopus 162 / WoS 138) | p. 3 |
| Final studies reviewed | **163** (94 SD / 53 Scopus / 16 WoS) | p. 3 |
| Transfer-learning studies (Table 1) | ≈ 42 rows | pp. 8–9 |
| SOTA architectures (Table 2) | 38 rows | pp. 10–12 |
| Custom models (Table 3) | 77 rows | pp. 13–16 |
| **SSL studies cited** | **3** — all leaf/canopy proximal sensing | pp. 6–7 |
| FSL studies cited | 1 (Prototypical/Triplet nets, coffee leaves, 92.25%) | p. 7 |
| **Salinity studies** | **≈ 2 of 163** (Khoshimah 2022 SC-CAN 82–89%; Khoshimah 2023 MCE-ST 83.6% wheat) — *our tally from Tables 1–3; the paper gives no official per-stress counts* | pp. 14–15 |
| Drought/water studies | ≈ 20–22 (our tally) | pp. 8–16 |
| Satellite-imagery studies | 2–3 (Maxar Worldview-2 spruce beetle 95%; a Sentinel-2 mention; Sentinel-1 sugarcane) | pp. 5, 9, 13 |
| **Mamba / state-space models** | **0 — entirely absent** | all 23 pp. |
| Journal year | Volume 229 (2025); online 13 Dec 2024 — cite as **2025** | p. 1 |

## Why This Matters for the Thesis (verified findings)

1. **SSL is recognized but not established — citable gap evidence.** The abstract states SSL/FSL "may be better than transfer learning (TL)-based models for classifying plant stress when the number of labeled training images are scarce" (p. 1), yet the entire SSL treatment is one subsection (3.2.3.1, pp. 6–7) with 3 studies (CAE on UAS RGB soybean; 7-SSL-approach comparison on soybean hyperspectral; STNet tomato spectra). **No satellite, no thermal, no multi-temporal SSL anywhere in 163 studies** — and no SSL algorithm taxonomy (SimCLR/BYOL/MoCo/Barlow Twins/DINO never appear). The Conclusion's data-scarcity toolkit (p. 19) even drops SSL in favor of "data augmentation, transfer learning, and semi-supervised learning techniques (e.g., GAN)". → **This is the strongest citable evidence so far that G3 (no EO recipe for optical+thermal SSL under label scarcity) remained open as of Dec 2024.** Cite as *recognition* of SSL's promise, not as a survey of SSL methods.
2. **No Mamba prior-art conflict.** Sequence models are marginal (a dozen RNN-family rows, all UAV/lab imagery) and the "frontier" is Transformers (ViT, conformer, spectroformer). Our CNN-Mamba + SSL design has no competitor in this corpus.
3. **Salinity is near-invisible.** ~2/163 studies, both proximal hyperspectral leaf/canopy, single-timepoint. Combined with ~20 drought studies → concurrent water+salinity separation from satellite time series is far outside anything reviewed here (G4 support).
4. **The field's answer to overlapping stresses is avoidance, not disentanglement.** Challenge (p. 18): "Sometimes multiple stresses occur on a single leaf that can significantly alter the characteristics of symptoms, especially when they overlap. These symptom overlaps are rarely captured correctly, which leads to misclassifications." Their remedy (p. 19): train a similarity architecture that dumps unmatched symptoms into an **"others" class** (Esgario et al. 2022). Our thesis does the opposite — explicit Water/Salinity/Mixed separation — a clean positioning contrast.
5. **SSL augmentation design input.** "Nagasubramanian et al. (2022) avoided color jittering-based data augmentation during SSL pretraining with soybean disease images to avoid drop in performance" (p. 18) → supports favoring geometry/seasonal invariances over strong photometric jitter in our Barlow Twins augmentations (chlorosis/necrosis hues are the signal).
6. **Nearest sugarcane EO neighbor.** Vinnodkar et al. (2021) DenseResUNet on **Sentinel-1** for water-stressed sugarcane: 61.91% mIoU / 80.53% accuracy (p. 13, 17) — the only sugarcane satellite stress study in the corpus; useful positioning foil (SAR, single stress, pixel-level).
7. **Multimodal fusion helps.** "Miao et al. (2023) showed that multimodal (multi-spectral, thermal, and RGB) data fusion performed better than unimodal data" (p. 17); abstract endorses multimodal inputs — consistent with our raw-bands + LST design.

## Quotable Verbatim (for the lit review)

- "Self-supervised learning (SSL) and Few-shot learning (FSL)-based methods may be better than transfer learning (TL)-based models for classifying plant stress when the number of labeled training images are scarce." — Abstract, p. 1
- "SSL methods were robust to class imbalances, highly efficient and able to differentiate confounding stress classes with a smaller number of training images compared to supervised learning methods with ImageNet initialization." (summarizing Nagasubramanian et al. 2022) — p. 6
- "Sometimes multiple stresses occur on a single leaf that can significantly alter the characteristics of symptoms, especially when they overlap. These symptom overlaps are rarely captured correctly, which leads to misclassifications." — p. 18
- "Image labeling can also be a tedious, labor-intensive, and time-consuming process." — p. 18
- "Ensuring model interpretability and explainability is important for gaining insights into plant stress mechanisms and building trust in model predictions." — p. 19 (no XAI method offered — SHAP/Grad-CAM absent)

## Cautions

- Do **not** cite Paul et al. as evidence SSL for plant stress is mature — it is a ~1-page subsection.
- The salinity-vs-drought study counts are **our own tally** of Tables 1–3, not official figures.
- Minor paper-internal quirks (do not propagate): PRISMA arithmetic in Fig. 2 doesn't sum exactly (236→172→163); search string printed as "Bioc*"; satellite study dated 2023 in text but 2024 in Table 1; salinity author spelled "Khoshimah"/"Khotimah" inconsistently.

## Links

- Matrix row: `Thesis_Vault/Literature-Matrix.md` #60
- Feeds lit-review §3.3 (SSL) and §3.1 (concurrent stress); gap evidence for **G3, G4**
