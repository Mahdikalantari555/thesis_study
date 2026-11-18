# 45 — Toward Resilience in Broadacre Agriculture: A Methodological Review of RS for Crop Productivity, Phenology and Environmental Stress Detection (Shen et al., 2025)

**Full Citation:** Shen, J., Wang, H., & Tareque, H. (2025). Toward resilience in broadacre agriculture: A methodological review of remote sensing in crop productivity, phenology, and environmental stress detection. *Remote Sensing*, *17*(23), 3886. https://doi.org/10.3390/rs17233886
**DOI:** [10.3390/rs17233886](https://doi.org/10.3390/rs17233886) | Open Access (CC BY) | Published 29 November 2025 | Academic editor: Liang Sun | Crossref-verified 2026-10-20
**Status:** ✅ Full read (2026-10-20) — extracted text read across all 26 pages (methodology, thematic review, integration section, conclusions)
**Themes:** #Review #Review-methods #Concurrent-stress #Drought

---

## What It Does

Methodological review of remote sensing for **rainfed broadacre** cropping, organised around three themes — crop productivity (yield / yield gaps), crop phenology, and environmental stress — assembled from a semi-structured search into **70 peer-reviewed articles**. For the thesis the stress section is the payload: RS stress **detection** capability is now well established, but **specificity** — attributing the signal to a particular stressor — is not, and salinity–water co-occurrence is treated as the flagship case where spectral symptoms overlap. It closes by recommending multi-sensor/multi-scale fusion, RS–crop-model data assimilation and operational/big-data integration.

## Corpus & Scope

- **Search (p. 4, Table 1):** **Google Scholar as primary engine**; Web of Science and Scopus used only for **cross-referencing**. Boolean: `["remote sensing" OR "UAV" OR "UAS" OR "drones"] AND ["crop produc*" OR "yield" OR "crop phenology" OR "crop stress" OR "resilience"]`, with each of the three core themes searched separately.
- **Screening (p. 4):** title/abstract → full-text → inclusion/exclusion (peer-reviewed; broadacre crops such as wheat, maize, barley, soybean; ≥1 core theme; agronomic relevance) → **snowballing and expert recommendations**.
- **Final corpus: 70 peer-reviewed articles** (p. 4–5); **29 are review-type** and **4 do not fit the three themes** (broader methodological innovation) (p. 5).
- **Coverage:** 22 journals (top five: *Remote Sensing*, *RSE*, *Agricultural and Forest Meteorology*, *IJAEOG*, *Agricultural Water Management*); North America, South America, Australia, Asia, South Asia, Europe, Africa; **the majority of publications appeared 2018–2024** (p. 5–6). Scope framed as "methodological advances over the past two decades" (p. 2) — no explicit earliest year.
- **Thematic counts (p. 5, counted once per relevant theme):** productivity **n = 29**, phenology **n = 38**, stress detection **n = 31**; only **n = 7 addressed all three simultaneously**.
- **Tools (p. 6):** bibliometrics in R-4.4.1 (`ggplot2`, `VennDiagram`); GPT-4o used only for initial structure and later grammar checking. No external funding.

## Key Findings

- **Headline framing (abstract, p. 2):** "Thermal and multispectral indices support the early detection of abiotic (drought, heat, salinity) and biotic (pests, disease) stresses, **though specificity remains limited**."
- **Salinity–water co-occurrence treated explicitly (p. 15–16):** "Salinity stress, for example, often co-occurs with water deficits and produces **similar spectral symptoms** (e.g., reduced canopy moisture and greenness)." Citing Wen et al. (the thesis's #71 line), they report S2 biophysical variables (LAI, fractional cover, canopy water, chlorophyll) showing "far greater impacts under combined salinity-drought stress than under either stress alone", leaf area declining earlier and more severely — the *compounding* is detectable, the *cause* is not.
- **Stress-specificity diagnosis (p. 18):** "no single sensor or index can unravel the full complexity of stress physiology"; "Most practical scenarios involve multiple concurrent stressors—drought, heat, and biotic attacks overlapping—which can confound spectral signals." Berger et al. (#44) anchors the multi-domain fusion call.
- **Operational statement of the gap (p. 19):** "stress signals are often non-specific, making it difficult to distinguish overlapping causes **without ancillary data**"; adoption "also constrained by limited validation datasets."
- **Conclusion (p. 22):** "(3) Stress detection methods are hindered by the **non-specificity of spectral responses, the difficulty of identifying overlapping stressors**, and the limited availability of ground-truth data for validation."
- **Recommended remedies matching the thesis architecture (p. 19–20, Table 4):** multi-sensor/scale fusion (optical + SAR + thermal), RS–crop-model assimilation (LAI/NDVI into APSIM/DSSAT), operational/big-data integration — each with stated limitations (fusion must reconcile spatial-temporal mismatch; UAVs do not scale; AI platforms overfit and need large curated datasets).
- **Two directly reusable hooks:** (i) p. 17 — integrating thermal imagery with optical and **fluorescence** data "could provide a more specific diagnosis of **heat stress versus water stress** in crops"; (ii) p. 21 — a proposed composite "RS-resilience index" would include "top-soil moisture retention, **salinity dynamics**, erosion risks, and agricultural drought thresholds", which are "crop- and region-specific … yet remain **underrepresented in current remote sensing frameworks**".
- **Compositing cost (p. 19):** coarse revisit intervals and cloud contamination introduce errors of "**~7–15 days**".
- **Contextual numbers (secondary, review-cited):** broadacre systems are "nearly three-quarters of the world's cropland extent" (p. 3); climate change since 2000 cut average Australian grain-belt farm profitability by "about 22%" (p. 3); heatwaves and drought account for "roughly **20–49%** of global crop yield variability" (p. 3).
- **Review-level limitations:** corpus is **rainfed broadacre** (cereal/maize/rice/soybean), framed from a Western-Australian perspective with a case study from the authors' own projects (p. 6); **irrigated desert-oasis systems such as Khuzestan are not represented**; the co-stressor emphasised is heat + drought, not salinity + water; no PRISMA, no duplicate screening, no risk-of-bias appraisal.

### Note on the intake note (A7)

A7's quantitative claims all check out against the PDF (¾ of cropland, −22% profitability, 20–49% yield variability — all p. 3) and its "stress specificity remains limited despite adequate detection capability" matches the abstract (p. 2). One calibration point: A7 rates the paper "Thesis relevance: High" whereas matrix row #45 rates it **Medium** — I keep the matrix verdict (**Medium**), since the paper supplies framing rather than method, labels or benchmarks.

## Relevance to Thesis

**Medium** — related-work framing and context, not a method or label source:

- ✅ A **recent, independently-worded** confirmation of the thesis's problem statement: "the non-specificity of spectral responses, the difficulty of identifying overlapping stressors" (p. 22) is a second citable anchor beside Wen 2021 (#69) and Berger 2022 (#44), and salinity is named explicitly among the co-occurring stresses (p. 15–16).
- ✅ Supports the **multi-sensor fusion and RS–crop-model assimilation** positioning (p. 19–20) and the SIF-plus-thermal route to separating heat from water stress (p. 17) — citable evidence that thermal/optical fusion improves cause discrimination.
- ✅ The **7/70** figure (p. 5) is a usable number for the "integration across monitoring themes is rare" claim in the related-work chapter.
- ✅ The call to embed **salinity dynamics and soil-related indicators** into resilience frameworks (p. 21) is a citable endorsement that salinity is under-served in RS monitoring schemes generally.
- ⚠️ Transfer condition: **rainfed broadacre context**, not irrigated arid oasis; the co-stressor is heat + drought, so the framing transfers by analogy only, and every number is review-cited from primaries — verify against primaries before formal proposal use.
- ⚠️ Methodological caution: single primary search engine, keyword-string selection, no PRISMA, no risk-of-bias assessment; the 70-paper corpus is a convenience sample of the RS-for-agriculture literature.
- ❌ No threshold, no label protocol, no accuracy benchmark, no salinity-specific method, and no coverage of SSL, foundation models, Mamba or XAI.

## Key Takeaway

A citable, recent statement of the same gap the thesis targets — "stress detection methods are hindered by the non-specificity of spectral responses, the difficulty of identifying overlapping stressors" (p. 22), with salinity named as a co-occurring stressor producing "similar spectral symptoms" (p. 15–16) — usable as framing only: a rainfed-broadacre methodological review with no thresholds, labels or benchmarks for the thesis's design.

## Links

- Matrix row: #45
- Related: #44 (Berger 2022 — the multi-sensor synergy anchor this review leans on), #69 (Wen 2021 — the "monitor both simultaneously" gap quote), #71 (Wen 2023 — the combined salinity–drought study cited here as ref. [79]), #60 (Paul 2025 — DL/plant-stress review, 163 studies), #77 (Waters 2025 — sugarcane RS review), #70 (Wen 2022 — S2 biophysical traits under combined stress)

---

*Linked from: [[Literature-Matrix]]*
