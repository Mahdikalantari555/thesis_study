# 72 — Multi-Dimensional Optical RS in Agriculture (Haq et al., 2025)

**Full Citation:** Haq, M.A. et al. (2025). Multi-dimensional optical remote sensing in agriculture: Spectral, angular, and spatial perspectives for crop stress detection (title as printed in SAT). *Smart Agricultural Technology*, 12, 101583.
**DOI:** [10.1016/j.atech.2025.101583](https://doi.org/10.1016/j.atech.2025.101583) | ~14 cites (external)
**Status:** ✅ Full read (2026-10-04, from extracted full text)
**Themes:** #Data-quality #BRDF #Physics-aware-AI #Review

---

## What It Does

Review of crop-stress optical RS organized by **three dimensions — spectral × angular × spatial**: synthesis of **138 records covering 47 unique sensor setups across 12 major crops** (proximal → UAV → satellite). Agenda: a hierarchical monitoring architecture with **physics-aware AI** addressing (1) temporal optimization for stress progression, (2) spatial integration across scales, (3) physics-informed fusion of the data.

## Verified Findings That Carry Thesis Weight

1. **Viewing geometry biases the core stress indices (verbatim):** "viewing geometry significantly affects vegetation indices (NDVI, PRI) and sun-induced fluorescence (SIF) measurements, requiring sophisticated angular correction methods for accurate stress assessment"; elsewhere: "induce bidirectional reflectance variations, impacting VI values and potentially leading to **erroneous stress interpretation**… BRDF correction models or multi-angle acquisition strategies are recommended to normalize spectral measurements." → **Protocol item for our 2013–2025 Landsat compositing: fix viewing geometry / apply BRDF normalization before per-field temporal stacking** (echoed sugarcane-specifically by Waters #77).
2. **BRDF anisotropy may itself separate stress types (novel, verified):** stress-illuminated canopy signatures differ — "water stress (increasing forward-scattering), nutrient deficiency (reduced anisotropy), and pathogen infection (asymmetric BRDF patterns)" (Fig. 9, field spectra + controlled experiments). → Directional/angular features are a candidate *disentanglement* signal, not just a nuisance to correct; worth a features-ablation slot in our design (Landsat is fixed-nadir, but sun-target-geometry varies across the 490 fields' acquisition geometries and seasons).
3. **Physics-aware AI agenda (verbatim):** "a unified framework that not only bridges spatial and angular resolution gaps but also incorporates physics-aware AI for scalable crop monitoring"; "integrating temporal, spatial, and spectral data via physics-aware machine learning". → matches our RTM/physics-as-priors discussion; cite as the field-level endorsement of physics–DL hybrids (note: their "physics-aware" = physics-informed ML, distinct from SSL — do not conflate).
4. **Stress staging (Fig. 2):** pre-symptomatic (SIF/xanthophyll changes) → early → advanced → chronic — a citable temporal staging frame for our label-severity design (labels anchored to stage windows, not just dates).
5. **Salinity: 3 incidental mentions only** (abiotic-stress list) — no salinity-specific synthesis; consistent with the salinity-neglect chain (Berger 5%, Paul ~2/163, Waters 0).

## Implications for the Thesis

- **Compositing protocol (must-do):** per-field temporal features must be built geometry-aware — consistent view geometry or BRDF-normalized composites — otherwise per-field index trajectories risk season-geometry artifacts that a deep model could latch onto spuriously (and XAI would faithfully explain the artifact).
- **Feature-space expansion candidate:** angular/anisotropy descriptors as auxiliary features for stress-type separation (from fixed-orbit Landsat: across-track view-angle variation + seasonal solar geometry as proxies).
- **Framing:** cite for the three-dimensional (spectral-angular-spatial) data-quality agenda and the physics-aware-AI endorsement.

## Quotable Verbatim (locations approximate — extracted text)

1. "viewing geometry significantly affects vegetation indices (NDVI, PRI) and sun-induced fluorescence (SIF) measurements, requiring sophisticated angular correction methods for accurate stress assessment." — Abstract/§1
2. "BRDF correction models or multi-angle acquisition strategies are recommended to normalize spectral measurements and improve stress signal stability across conditions." — §4.x
3. "…showing distinctive signatures for water stress (increasing forward-scattering), nutrient deficiency (reduced anisotropy), and pathogen infection (asymmetric BRDF patterns)." — §on multi-angle, Fig. 9 caption
4. "We propose a hierarchical monitoring architecture supported by physics-aware artificial intelligence models that address three fundamental challenges: temporal optimization for capturing stress progression dynamics, spatial integration…" — §conclusions/agenda

## Cautions

- Numbers (138 records / 47 setups / 12 crops) are from the review's own synthesis; the search window/method details are thin in the text we extracted — cite the counts as "the review reports", not as a PRISMA-grade pipeline.
- Quote by section, not page (extracted-text reading; published pagination unverified).

## Links

- Matrix row: #72 (verified 2026-10-04)
- Feeds 04-Thesis-Design (compositing protocol item), lit-review §3.1/§3.4; G4 salinity-neglect chain
