# 40 — Drought + Heat Co-Stress Physiology in Agronomically Important Plants (Feller & Vaseva, 2014)

**Full Citation:** Feller, U., & Vaseva, I. I. (2014). Extreme climatic events: impacts of drought and high temperature on physiological processes in agronomically important plants. *Frontiers in Environmental Science*, *2*, 39. https://doi.org/10.3389/fenvs.2014.00039
**DOI:** [10.3389/fenvs.2014.00039](https://doi.org/10.3389/fenvs.2014.00039) | Open Access (Frontiers) | Review article, Agroecology and Land Use Systems section | 17 pp. (~9 pp. references)
**Status:** ✅ Full read (2026-10-20) — abstract, §stomatal regulation, §photosynthetic capacity, §Rubisco activase, §ROS, §photorespiration, §senescence, §stress-related proteins and §conclusions read in full
**Themes:** #Stress-physiology #Drought #Thermal #Concurrent-stress

---

## Corpus & Scope

- **Narrative (non-systematic) review** — no search protocol, no PRISMA, no corpus counts, no meta-analytic effect sizes. Organised by *physiological process* (stomata, cuticular wax, aquaporins, photosynthetic capacity, Rubisco activase, ROS, photorespiration, nitrogen metabolism, senescence, stress-related proteins), not by stress type, so drought × heat interactions surface throughout.
- 17 pages + 7 figures, several carrying the authors' own measurements from field plots near Bern, Switzerland (August 2003, an exceptionally hot and dry summer) and from leaf-segment laboratory assays.

## What It Does

Synthesises how drought and high temperature — separately and together — alter crop physiology: stomatal regulation, cuticular wax, aquaporin water flux, photosynthetic capacity and its reversibility, heat sensitivity of Rubisco activase, ROS accumulation, photorespiration, nitrogen transport, senescence and protective proteins (dehydrins, chaperones, proteases). Its contribution for remote sensing is the demonstration that **heat and drought act on stomata in opposite directions**, so canopy temperature is an *integrative, ambiguous* signal under concurrent drought and heat, and that the recovery phase after stress release carries its own information.

## Key Methodology

- Process-by-process synthesis framed around *reversibility* (reversible vs irreversible damage) and around the **recovery stage**, which the authors argue "is equally crucial for a proper evaluation of the overall performance" (p. 1).
- Own field measurements (Figs. 1, 2, 5): leaf temperature of **undisturbed** (non-contact, non-shadowed) leaves by infrared thermometer, paired with stomatal conductance of upper and lower leaf surfaces; photon flux densities 1300–1900 µmol m⁻² s⁻¹ for sun-exposed vs ~100 µmol m⁻² s⁻¹ for shaded leaves (p. 3); sugar-beet till vs no-till comparison in the hot, dry summer of 2003 (p. 6).
- Controlled leaf-segment assay (Fig. 4): stomatal opening of bean leaf segments in darkness at elevated temperature with (+ABA) and without (−ABA) 0.1 µM abscisic acid — opening at 47 °C, closure during recovery at 23 °C (p. 5).

## Key Findings

- **Heat and drought act on stomata in opposite directions — the core confound.** "ABA produced in roots exposed to soil with a low water potential, reaches the leaves via transpiration stream and causes stomatal closure. It has also been observed that ABA shifts the heat-induced stomatal opening toward a higher temperature. Thus, **heat and drought act in an opposite manner on stomates**" (p. 2). For thermal RS: heat raises energy demand (and opens stomata → cooling) while drought closes them (→ warming), so on a hot day a single-date CWSI/CTD can partly cancel a real water-stress signal, and the *sign* of the bias depends on which effect dominates. ABA also re-tunes the heat response, so the heat–water interaction is not even additive in the stomatal term.
- **Within-canopy temperature contrast matches the target signal.** Leaf temperature "may increase throughout the day reaching values above **40 °C** during the late afternoon in a sunny day in summer" (p. 2), and "temperature of fully sun-exposed leaves is often **5–10 °C** higher than the one of shady leaves from the same plant" (p. 2) — a 5–10 °C spread at *identical* water status, comparable to the canopy-to-air difference CWSI reads.
- **The "magic triangle" is under-determined:** leaf temperature, water status and stomatal conductance jointly govern the signal; any one alone is ambiguous (p. 2).
- **Thermal indices lag the physiology:** after a dark→high-light transition "leaf temperature rises immediately, while stomates react within several minutes which explains the delay in cooling via transpiration" (p. 2) — the window in which a thermal image reads a still-transpiring canopy as stressed.
- **Salinity shares drought's cellular injury class.** "Drought and high temperatures, together with other environmental factors like chemical pollutants, cold and **high salt concentrations** have similar effects on plants. They damage plant cell and lead to **osmotic and oxidative stress**" (p. 8) — the direct physiological warrant for the thesis's problem statement: salinity and water deficit damage the plant through the same pathway, so the plant-side signal does not self-separate them.
- **Heat has a lesion invisible to water indices.** Rubisco stays functional above 50 °C, but "Rubisco activase activity is negatively affected by temperatures above **30 °C**" depending on species, and the heat sensitivity of photosynthesis is caused by thermal denaturation of Rubisco activase (p. 5) → a heat wave depresses assimilation with no change in water status, so reflectance/fluorescence proxies can fire on heat while a purely thermal proxy does not.
- **Shared downstream damage:** heat and drought both raise photorespiration in C3 leaves (p. 7) and both increase ROS and damage proteins (pp. 6–9); cuticular wax deposition reduces transpiration and is **not fully reversible** after the drought period (pp. 2–3) → transpiration-based indices drift within a season independently of soil water.
- **Recovery carries information:** "The apparent significance of stress period for the crop productivity does not rule out the fact that subsequent recovery stages are equally crucial" (p. 1); "a plant with a poor performance during the stress phase may survive longer and recover more efficiently than a plant which initially remains productive" (p. 12) → a label assigned at one date discards the post-stress recovery signature, which is what a multi-temporal (SITS) design can use.
- ⚠️ **Discrepancy with the matrix/intake claim "combined stress ≠ sum of singles":** the PDF contains **no formal non-additivity test, no interaction statistic and no meta-analytic effect size**. Support is mechanistic and directional (opposite stomatal effects; shared ROS/protein damage; heat-sensitive Rubisco activase; the reversible/irreversible framing). Cite it as a *physiological rationale* for why a single-stress index is unsafe, never as a measured interaction effect.

## Relevance to Thesis

**Medium** — the physiological prior for treating heat as an explicit co-stressor covariate and for explaining why thermal indices are confounded; it supplies no RS/ML method, no quantitative effect sizes and no salinity measurement.
- ✅ Establishes the direction of the heat confound (heat *opposes* drought at the stomata, p. 2) → justifies carrying air temperature, VPD and radiation as explicit co-drivers alongside thermal features instead of reading canopy temperature as a pure water signal.
- ✅ Provides the shared-pathway argument for salinity vs drought (p. 8), underpinning the concurrent-stress framing.
- ✅ Shows leaf temperature alone cannot disambiguate stress (5–10 °C within-canopy contrast, minutes-scale stomatal lag, p. 2) → argues for canopy-level aggregation and multi-temporal features.
- ⚠️ Narrative review with no quantitative effect sizes: usable as justification, not as a benchmark number; its quantitative anchors are single-site Swiss measurements from 2003.
- ⚠️ Transfer condition: the physiology is species-general, but the *magnitude* of heat–water cancellation in an irrigated, saline sugarcane field in Khuzestan is unverified — nothing here measures that system.
- ❌ No remote sensing, no machine learning, no multi-temporal or sequence modelling, no label protocol, no salinity measurements.

## Key Takeaway

Feller & Vaseva give the thesis its co-stressor physiology in one sentence: heat and drought act on stomata in *opposite* directions (p. 2), so a canopy-temperature index is confounded by atmospheric demand in a way that can cancel, exaggerate or invert a water-stress signal, and drought, heat and high salt all converge on the same osmotic/oxidative cell damage (p. 8). Caveat: the "combined ≠ sum of singles" claim in our matrix is a mechanistic inference from this review, not a measured interaction effect.

## Links

- Matrix row: #40
- Related: #39 (the CWSI/CTD physics that heat breaks), #41 (Tardieu: hydraulics that decode the water-status half of the triangle), #07 (Angon: measured combined drought+salinity effects), #69 (Wen 2021: RS cannot monitor drought and salinity simultaneously), #44 (Berger: multi-sensor response to co-occurring stresses), #10 (Khuzestan CWSI trigger thresholds), #42 (Gerhards: thermal water-stress detection under co-occurring stresses)

---

*Linked from: [[Literature-Matrix]]*
