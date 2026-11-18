# 44 — Multi-Sensor Spectral Synergies for Crop Stress Detection (Berger et al., 2022)

**Full Citation:** Berger, K., Machwitz, M., Kycko, M., Kefauver, S.C., et al. (38 authors) (2022). Multi-sensor spectral synergies for crop stress detection and monitoring in the optical domain: A review. *Remote Sensing of Environment*, 280, 113198.
**DOI:** [10.1016/j.rse.2022.113198](https://doi.org/10.1016/j.rse.2022.113198) | Open Access (CC BY-NC) | **~290 citations — most-cited paper of our second tier**
**Status:** ✅ Full read (2026-10-04)
**Themes:** #Multi-sensor #Stress-RS-review #Thermal #Deep-learning-gap

---

## What It Does

Flagship 38-author review of **optical-domain** (VIS/NIR/SWIR reflectance, SIF, TIR 8–14 µm) crop-stress RS. Four-step systematic review (keyword search 1994–2021, WoS): ~300 records → 133 after screening → **96 studies** after excluding yield/soil-focused and **single-sensor/domain** studies. Taxonomy: stress phases (early minutes–hours / medium hours–days / long days–weeks), trait groups (flux / biochemical / structural), five spectral domains (VIS, SIF, NIR, SWIR, TIR), method classes (parametric / nonparametric / RTM / SEBM / hybrid).

## Verified Key Numbers

| Statistic | Value | Source |
|-----------|-------|--------|
| Final studies | 96 (of ~300 → 133) | §4.1, p.10 |
| Parametric (VI-based) methods | **~72%** | §4.4, p.11 |
| Nonparametric linear / nonlinear (ML) | 22% / ~17% | §4.4, p.11 |
| Deep learning | **"the exploration of deep learning algorithms is still missing"** | §4.4, p.11 |
| Largest domain combo | VIS+NIR+TIR = 33 studies | Fig. 9, p.12 |
| **VIS+NIR+SWIR+TIR (the Landsat 8/9 combo)** | **12 studies** | Fig. 9, p.12 |
| All five domains (incl. SIF) | **only 4 studies** | §4.6, p.12 |
| **Salinity studies** | **5.0% of 96** — never synthesized | Fig. 10, p.13 |
| Drought studies | 52.1% (dominant stress type) | Fig. 10, p.13 |
| XAI content | **zero** (no SHAP/Grad-CAM/attention anywhere) | all 23 pp. |

## Why This Matters for the Thesis (verified)

1. **Our Landsat-only design exploits a barely-explored combination.** Landsat 8/9 delivers VIS+NIR+SWIR+TIR in one platform — a combo only **12/96** reviewed studies used (and only 4/96 used five domains). A per-field, multi-year Landsat time series covering structural + water + thermal domains is at the under-explored edge of their corpus.
2. **The differentiation gap, stated by the field's flagship review (p.3, §1):** "The main gap is that currently **no concept exists that uses multiple spectral domains in an integrated way** for a complete view of crop conditions **to differentiate between crop stress types** and to understand the degree of stress severity." — the single most citable sentence for our G4/concurrent-stress framing.
3. **But the warning cuts both ways (p.14, §4.8/§5.1):** "the differentiation between distinct types of stresses (e.g. water-deficit or nutrient stress) **will remain a challenge with purely RS-based approaches** because distinct stressors often lead to similar stress reactions." Our gap statement must say *how* we attempt what Berger et al. declare hard (dense 2013–2025 temporal selectivity + XAI validation), not just that nobody did it.
4. **Deep learning + XAI novelty:** a 290-cite review states DL exploration is "still missing" (p.11) and contains zero explainability content — both our contributions are absent from this literature stream.
5. **Salinity = 5% of studies, zero synthesis** — supports "salinity is EO-neglected" alongside Paul 2025 (~2/163) and Wen 2021 (zero VI–salinity correlations).
6. **Protocol input (their way-forward #1, p.14):** ≥1 sensor/method **per trait group** at varying time scales. Concretely for us: functional/thermal proxy (LST/CWSI family) + biochemical proxy (pigment/chlorosis VIs) + structural/water proxy (SWIR-based SIWSI/LWCI-type) across compositing windows.

## ⚠️ Rewording Requirements (our matrix row was imprecise)

- **"Single-index/single-sensor designs dominate" — WRONG as stated.** Their 96-study corpus **excludes single-sensor studies by design**. The correct separate claims: (a) "The majority of reviewed studies **compared** stress proxies calculated from single-source sensor domains rather than using data in a synergistic way" (abstract, p.2); (b) "~72% were based on parametric approaches" = VI/parametric dominance (§4.4, p.11).
- **"Temporal stress phase under-exploited" is NOT the paper's wording.** Supported only indirectly: "capturing the temporal dynamics and interaction of traits as stress proxies" is a recognized challenge (p.3), temporal-sensitivity studies are "still scarce" (p.14). Use: *"capturing temporal stress dynamics remains a recognized challenge and temporal-sensitivity studies are scarce (Berger et al., 2022)"*.
- **"Hybrid" collision:** in Berger et al., hybrid = RTM-generated training data + ML — **not** self-supervised learning. Avoid the unqualified word "hybrid" in our methods positioning, or define it.
- Don't propagate the paper's internal citation typo "Damm et al., 2022" for the drought claim (no such reference-list entry).

## Quotable Verbatim (with pages)

1. "The main gap is that currently no concept exists that uses multiple spectral domains in an integrated way for a complete view of crop conditions to differentiate between crop stress types and to understand the degree of stress severity." — §1, p.3
2. "The majority of reviewed studies compared stress proxies calculated from single-source sensor domains rather than using data in a synergistic way." — Abstract, p.2
3. "Although it may be promising for stress detection, the exploration of deep learning algorithms is still missing." — §4.4, p.11
4. "In total, only four studies concurrently exploited all five main domains (i.e., VIS, SIF, NIR, SWIR and TIR)." — §4.6, p.12
5. "the differentiation between distinct types of stresses (e.g. water-deficit or nutrient stress) will remain a challenge with purely RS-based approaches because distinct stressors often lead to similar stress reactions." — §4.8/§5.1, p.14
6. "There has been a long interest in using canopy temperature as a remote indicator of plant water stress." — §3.1.2, p.8 (thermal/CWSI family incl. Idso/Jackson CWSI, WDI reviewed here)

## Links

- Matrix row: #44 (verified 2026-10-04)
- Feeds lit-review §3.1 (differentiation gap) and §3.6 (thermal/CWSI); gap **G4** + multi-sensor protocol design
- Companion evidence: Paul 2025 (#60, DL/SSL absent in 163 studies), Wen 2021 (#69, zero VI–salinity correlations)
