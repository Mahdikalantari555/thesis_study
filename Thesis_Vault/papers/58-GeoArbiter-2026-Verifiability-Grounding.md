# 58 — GeoArbiter: Verifiability-Guided Grounding for Remote-Sensing Multimodal LLMs (Li, 2026)

**Full Citation:** Li, X. (2026). GeoArbiter: Verifiability-guided grounding for remote-sensing multimodal LLMs. *arXiv preprint arXiv:2608.00877*.
**DOI:** [10.48550/arXiv.2608.00877](https://doi.org/10.48550/arXiv.2608.00877) | arXiv:2608.00877v1 [cs.LG], 1 Aug 2026 | University of Minnesota, Twin Cities (single author) | 14 pp.
**Status:** ✅ Full read (2026-10-20)
**Themes:** #Agentic-RS #Data-quality #Benchmark

---

## What It Does

Argues that RS multimodal LLMs (MLLMs) fail in **two different ways that no single source-trust preference can fix** (p. 1): (a) **knowledge hallucinations** — asserting a facility's identity or institutional *function* that pixels cannot establish; and (b) **vision–knowledge conflict** — following an injected geographic record that contradicts visible evidence. The proposed criterion is **cross-modal verifiability**: records should dominate for attributes the image cannot verify (function, name), the image should dominate when a record disputes a visible structure (p. 1, §2). **GeoArbiter** operationalises this as a **training-free, deterministic, key-level content filter** that injects *only* the image-unverifiable subset of retrieved records (pp. 3–4) — replacing prompt-level arbitration, which the paper shows leaks across attribute types and biases yes/no responses.

## Key Methodology

- **Task formulation** (p. 3, §3.1): a **frozen** MLLM predicts ŷ = argmax_y p_θ(y | I, q, K), where the knowledge block K = τ(S) deterministically textualises retrieved records S. No parameters are updated — "the central design choice is which records to expose to the model".
- **Coordinate-keyed retrieval** (p. 3, §3.2): every OSM feature within r̄ = clamp(r, 300, 1500) m of the image centroid, from **dated Geofabrik extracts** plus a spatial grid index (reproducible, no live API calls); on 461 images reachable by both routes, local-vs-API feature counts correlate at **0.97**. Ablations add the nearest **GeoNames** toponym and the dominant **ESA WorldCover** class. Coordinates "identify ordinary as well as landmark locations and cannot return a visually similar but geographically unrelated site".
- **Verifiability label v on OSM primary tag keys** (p. 3, §3.3): **v = 0** = function/identity keys (amenity, shop, tourism, military, office, name) → **inject**; **v = 1** = physical-structure keys (building, highway, aeroway, natural, landuse) → **withhold**. "Verifiability belongs to the attribute, not the object: a building may be visible while its institutional role is not." Two predictions are tested (Eq. 1, p. 4): E[G | v=0] > E[G | v=1] and G(a | v=1, conflict) < 0.
- **Stratified injection** (Eq. 2, p. 4): S⁻ = {f ∈ R : v(κ(f)) = 0}, which **retains 11.1% of features**, textualised into a salience-ordered **1,200-character** block. "The filter requires no detector, extra model call, or per-image classifier."
- **Contrast arm** (§3.4, p. 4): **six** instruction-level arbitration prompts — image-first, database-first, stratified, question-keyed, and two paraphrases of the stratified instruction.
- **Data** (p. 4, §4): the complete **fMoW functional validation split — 28,087 images in 32 function-defined categories**, WGS84 coordinates, **2002–2017** acquisition times; OSM-derived QA/captions are avoided to prevent circularity. External benchmark: **2,000 four-way land-cover questions** built from a pan-European BigEarthNet subset via GEOBench (p. 5). RSHBench and RSHalluEval were unreleased at submission and are used only as qualitative context.
- **Models** (p. 4, all frozen, greedy decoding): **Qwen2.5-VL-7B-Instruct**, **InternVL3-8B**, **LLaVA-OneVision-7B**.
- **Metrics** (pp. 4–5): four-way land-use QA accuracy with **paired bootstrap (10k resamples)**; **claim-level hallucination rate** = CONTRADICTED share of atomic claims (~8.5–9 claims per description) from a frozen **Qwen2.5-7B-Instruct** judge, with claim types FUNCTION / NAME / physical CONTEXT / other; a **verifiable-existence probe** of **1,069 yes/no items from 400 images** (conflict cell adds a *fabricated* record for a manually verified absent, visually distinctive feature; control-absent and control-present cells isolate ordinary false positives and response-prior shifts); **retained gain** ρ = (a_filt − a_∅)/(a_rag − a_∅); probe **balanced accuracy** BA = ½(a_conf + a_pres).
- **Cost** (p. 4, §3.5; p. 7, §5.8): CPU-side retrieval/textualisation/caching — **4.9 ms** warm-cache assembly per image (p95 12.6 ms), **413 prompt tokens**, **0.56 s** mean generation latency on Qwen2.5-VL-7B.

## Key Findings

- **Retrieval lifts QA** (p. 5, §5.1): full OSM injection gave **+16.52 / +17.19 / +12.06 points** (Qwen / InternVL3 / LLaVA-OV, all p < 0.001). Raw coordinates added at most **+1.66** points, so the gain is 10.36–16.30× the location-disclosure effect; an image-blind OSM-tag decoder tops out at **70.6%**; blanking the image or swapping in another image's knowledge drops accuracy back toward `none`. LLaVA-OV, the strongest baseline, gained least — "as expected if retrieval fills a knowledge gap rather than adding a generic prior".
- **Injection reduces hallucination where verifiability predicts** (p. 5, §5.2): full injection cut claim-level hallucination by **51.74% / 23.93% / 23.56%**. For Qwen2.5-VL, FUNCTION fell **15.01% → 7.63%** and NAME **10.29% → 2.59%** (despite 2–5× more naming claims), while physical CONTEXT (starting at 1.01%) barely moved; the UNVERIFIABLE share fell **51.76% → 32.71%**, i.e. descriptions became more checkable, not merely shorter. Under the **source-blinded** judge the none→filtered reduction is **9.58–26.34%** (vs **19.28–45.19%** with the standard judge) and absolute rates roughly double — so the paper reports the blinded figure as the conservative one.
- **Fabricated records break every model and no prompt fixes it** (p. 6, §5.4): conflict-cell accuracy fell **88.75% → 72.00%** (Qwen), **75.75% → 62.25%** (InternVL3), **87.75% → 36.75%** (LLaVA-OV) — losses of **13.50–51.00 points**. All image-trust instructions cost **0.50–3.25 points** of all-function QA (bootstrap P(decrease) > 0.999 for the worst variant) and shifted the yes/no prior toward "no", so **no instruction recovered the no-knowledge balanced accuracy** (Table 2, p. 7).
- **GeoArbiter wins on both sides** (p. 6, §5.5): filtering discarded 88.9% of features yet retained **84.69–87.15%** of the QA gain and **81.82–91.09%** of the hallucination reduction, at a cost of at most **0.32 points**; conflict accuracy reached **93.25% / 90.50% / 91.25%** and balanced accuracy **80.08% / 80.54% / 82.02%** — above the no-knowledge baseline for every model. At a matched record budget, keeping the *image-verifiable* records instead drops conflict accuracy to **20.5–52.8%** (below full injection) while random selection stays robust: "the direction of selection, not the reduced context, is the lever".
- **Ecological view of retrieval** (p. 6, §5.3): injection changed **27% / 28% / 18%** of answers; among those, records corrected the image-only answer **72–77%** of the time and misled it **10–11%**. The most-rescued classes (places of worship, emergency services, gas stations, schools) are defined by functions invisible from orbit.
- **Baseline comparison** (p. 7, §5.7, 3,000-image subset): structured OSM **80.57 / 76.50 / 83.33%** vs Wikipedia GeoSearch **69.13 / 65.40 / 73.43%**, GeoNames **65.83 / 62.77 / 72.53%**, and a faithful RS-RAG reproduction **58.50 / 60.07 / 70.43%** (RS-RAG was neutral-to-harmful on ordinary scenes, **−5.30 points** for Qwen, because retrieved landmarks looked similar (0.90 ± 0.03) but had the wrong identity).
- **External validity** (p. 7, §5.8): BigEarthNet land-cover QA gains of **+7.95 / +4.25 / +4.10** points — smaller, "consistent with Eq. 1: land cover is largely image-verifiable, leaving less missing knowledge to supply".
- **Temporal mismatch ruled out** (p. 8, §6.3): retrieval gain was flat across map–image divergence quantiles (**−0.01 to −0.06, p ≥ 0.61**); a blinded audit found **93.9%** of features mapped after acquisition were already visible in the older image and only ~**1 in 22** scenes showed new construction — so the OSM–image gap "primarily measures mapping completion, not physical change".
- **Where the filter still costs** (p. 6, §5.5; p. 8, §6.4): key-level stratification drops useful evidence expressed under structural keys (hangars under `aeroway`, offices under `building`), accounting for the **12.85–15.31%** loss in retained gain; the diagnostic exception is **`amenity=parking`**, which survives the filter and fools models in **83–92%** of cases. The proposed refinement is an attribute-level (tag-value or question–attribute) policy.
- **Measurement validity** (p. 6, §5.6): two annotators on a stratified **198-claim** sample gave initial agreement of **78.3% (κ = 0.39)**; after adjudication (28 cases resolved, 15 excluded) the judge reached **84.2%** agreement (**κ = 0.61**, recall 0.88, precision 0.60) — absolute rates are therefore "conservative upper bounds" (p. 9).

## Relevance to Thesis

**Optional** — this paper belongs to the **frozen GeoAI-agent cluster** (matrix rows 47–59, 63–67; **cluster frozen 2026-10-04**) and is **background / future-work material only**. The cluster is **not** to be extended, and this note does not propose adding further agentic work to the thesis.

- ✅ The **attribute-level distinction it formalises — "can the image adjudicate this attribute or not?"** — is a clean, citable articulation of a distinction the thesis implicitly needs: crop-stress *labels* (soil EC, irrigation regime, in-situ water status) are exactly attributes the imagery cannot establish, whereas canopy structure is. That is a defensible framing for why ground truth must come from outside the image.
- ✅ The **verifiable-existence probe** design (inject a fabricated record for a manually verified absent feature; pair it with control-absent and control-present cells so that a yes/no prior shift cannot masquerade as robustness; report **balanced accuracy**) is a transferable evaluation idea for any thesis component where a model must defer to the image.
- ✅ The reporting discipline is worth imitating wherever the thesis uses an **LLM judge**: κ values, the "absolute rates are conservative upper bounds" framing, and emphasis on paired differences (p. 6, §5.6).
- ⚠️ **No crop, no stress, no temporal series**: everything is single-image land-use / existence reasoning on 7–8B open models over fMoW (2002–2017) and BigEarthNet, with English prompts. Transfer to a 2020s Sentinel-2 optical+thermal SITS in Khuzestan is unproven, and the paper itself notes RS-tuned or larger models "may follow different source priors" (p. 9).
- ⚠️ The filter is explicitly a **key-level approximation** the authors flag as their main limitation (p. 9), and it is a *record*-trust problem, not a *model*-trust problem — it never checks whether the model's stress reasoning is right.
- ❌ Provides no label design, no disentanglement method, no SSL/SSM architecture, no crop-stress or salinity metric, and **no agentic workflow at all** — this is single-turn MLLM prompting, not a multi-step pipeline.

## Discrepancies with intake note (G12)

- **Mechanism**: the intake says the method "withholds structure records **that conflict with** the model's visual evidence"; the PDF's filter is **deterministic and conflict-agnostic** — it withholds *all* physical-structure keys (v = 1) whether or not a record actually conflicts (pp. 3–4). This is a **stricter** mechanism than the intake summary implies, and the paper's own limitations section (p. 9) concedes the key-level map is an approximation (`amenity=parking` is plainly visible but kept).
- **Headline numbers**: the intake's "−9.58–26.34% (blinded) / −19.28–45.19% (standard)" **matches** the PDF, but the PDF also reports the *full-injection* reductions of **51.74% / 23.93% / 23.56%** (p. 5), which the intake omits. The two sets are **different comparisons** (full injection vs. filtered) and must not be conflated.
- **Framing**: the intake's "−13.50–51.00 points" is the *loss caused by fabricated records* on the conflict cell (p. 6, §5.4), not a reduction achieved by GeoArbiter.
- **No discrepancy** on the dataset and model lists: fMoW functional split of 28,087 images, Qwen2.5-VL / InternVL3 / LLaVA-OV, OSM + GeoNames sources (pp. 4–5) are all confirmed.

## Key Takeaway

The transferable idea is the **verifiability stratum**: treat external knowledge as trustworthy exactly for the attributes the image cannot check, and structurally prevent it from competing with perception for the attributes it can (pp. 3–4) — a stronger, content-level version of "don't let a plausible-sounding record override what the pixels show". The honest caveat is that the paper demonstrates this on single-image land-use classification with 7–8B open models and a key-level filter the authors themselves call approximate (p. 9), so it supports a *design principle and an evaluation design*, not any crop-stress method.

## Links

- Matrix row: #58
- Related: #56 (Munir et al. — the EO-native "verifiability before fluency" argument that this paper instantiates for retrieval), #50 (AgriWorld — verifiable agri/RS agents, the closest agri-agent bridge in the cluster)

---

*Linked from: [[Literature-Matrix]]*
