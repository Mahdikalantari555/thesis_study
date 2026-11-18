# 04 — XAI in Remote Sensing Review (Höhl et al., 2024)

**Full Citation:** Höhl, A., Obadic, I., Fernández-Torres, M.Á., Najjar, H., Oliveira, D., Akata, Z., Dengel, A., & Zhu, X.X. (2024). Opening the Black-Box: A Systematic Review on Explainable AI in Remote Sensing. *arXiv:2402.13791*.  
**Status:** ✅ Full read (2026-10-04)  
**Themes:** #XAI #Review

---

## What It Does

Systematic review of XAI methods in RS, categorizing by type, application, and evaluation approach.

## XAI Taxonomy

| Type | Methods | Models |
|------|---------|--------|
| **Feature-based** | SHAP, SAGE, CAM, Grad-CAM, DeepLIFT | Linear/non-linear, CNN |
| **Global** | Saliency maps, GAM, DAM | Neural networks |
| **Surrogate** | LIME | Linear/non-linear |
| **Pixel-based** | LRP | Neural networks |
| **Concept-based** | CAV | Neural networks |

## Critical Findings

1. **Most RS-XAI is spatial (2D)** — temporal XAI is virtually unexplored
2. **XAI evaluation is weak** — most papers don't validate against ground truth
3. **Domain adaptation is common but inappropriate** — medical XAI ≠ RS XAI without modification

## Our Contribution Gap

> "None of the reviewed papers apply XAI to **temporal satellite data** — only to static hyperspectral/spectroscopic data."

This is our novel contribution: **temporal XAI for SITS**.

## Verified Full-Text Findings (2026-10-04)

Full 52-page read (arXiv v2, 6 Nov 2024). Page numbers refer to the PDF.

**Survey scope (verified):** 207 studies included via PRISMA — 147 from databases (Scopus n=335, Springer n=616, IEEE n=120 → 1075 records, 964 screened) + 60 from the authors' private libraries (Fig. 12, p. 44). Window: papers published 01.01.2017–31.10.2023 — "our review comprises more than six years" (p. 43, Appendix A; Conclusion p. 23: "covering the last 6 years"). Method usage (p. 9, §IV-A + Fig. 4): local approximation most frequent (94 publications), backpropagation next (72 papers, dominated by CAM/Grad-CAM variants), perturbation 56, interpretable-by-design 15; "Most RS studies rely on local approximation approaches, particularly the SHAP method" (Fig. 4 caption, p. 9). Actual taxonomy (Fig. 2, p. 3): Feature Attribution / Distillation / Intrinsic / Contrastive Examples (+ feature selection treated separately) — *not* the simplified table above.

### Exact quotes

**Temporal XAI:**

- p. 22, §V-B2 (Remote Sensing Properties): "However, most xAI methods were originally designed for images and do not explicitly consider temporal dependencies, making some of them unreliable or inaccurate [329]."
- p. 21, Fig. 10 caption: "As well as the dependencies from the temporal dimension and topology, which are often not considered by traditional xAI methods."
- p. 19, §V-A1: "These assumptions can often be violated when applying the xAI methods in RS, particularly due to the specific properties of RS data related to scale, temporal dependencies, and geographical confounders (described below in Section V-B2)."
- p. 24, Conclusion: "Therefore, we encourage the development of methods to address those drawbacks related to scale, topology, and temporal dependencies in RS data."
- BUT temporal XAI is not absent from the survey — p. 13, §IV-B: "Rubwurm and Körner use the gradient method to measure the temporal importance assigned by various DL models for crop classification [158]." Also p. 13: attention weights "select the key dates for crop discrimination"; p. 14 (Kim et al. [156]): "An inconsistency metric is introduced to measure the similarity of the attribution maps"; Table I (pp. 15–18) lists temporal LSTM/ConvLSTM/transformer models with XAI.

**Evaluation practice:**

- pp. 23–24, Conclusion: "as over 90% of the studies conduct only anecdotal evaluation, verifying the reliability of the xAI outputs supports future work on quantitative evaluation and user studies."
- p. 12, §IV-B2: "In remote sensing, most of the literature relies on anecdotal evidence, often involving the visualization of arbitrarily selected or cherry-picked examples."
- p. 12: "When it comes to the quantitative evaluation, we identified 15 studies testing the xAI methods on RS problems with functional metrics." (15 of 207 ≈ 7%; Fig. 7 caption p. 12: "quantitative evaluation is rare", "A single work relies on user studies for agriculture, and three studies apply their methods to toy tasks.")
- p. 13: "Despite the high number of the local approximation methods in RS, we did not find any works that quantitatively evaluate their explanations."
- p. 20, §V-A3: "Until now, there is no standard way to evaluate xAI and discussions on how to do it properly are still ongoing."
- p. 20, §V-A4: "Real-world datasets lack a controlled ground truth for evaluating xAI methods and a regulated environment is needed to lay the foundation for fully transparent datasets."
- p. 23, §V-B5: "Furthermore, no standardized and objective evaluation for xAI methods has been established, posing a challenge for potential practitioners outside the xAI domain."
- Metrics named in the survey: max-sensitivity, file size, computation time, MoReF, class sensitivity, drop/increase in confidence, model/data randomization tests (p. 12); robustness, faithfulness, randomization, complexity, localization (p. 20, Börner et al. [309]); counterfactual closeness, sparsity, stability, plausibility (p. 13, Dantas et al. [157]).

### Repo-claim verification

| Repo claim | Verdict | Evidence |
|---|---|---|
| "Most RS-XAI works are spatial (2D image saliency maps) — temporal XAI is virtually unexplored" | **PARTIALLY FAITHFUL.** Spatial dominance and "most xAI methods... do not explicitly consider temporal dependencies" are supported (p. 22; p. 24; Fig. 10, p. 21), but the review never says temporal XAI is "virtually unexplored" — it documents temporal XAI studies ([158] p. 13, [157] p. 13, [156] p. 14, also [103], [48]). | Quotes above |
| "None of the reviewed papers apply XAI to temporal satellite data — only to static hyperspectral/spectroscopic data" (Our Contribution Gap, below) | **NOT SUPPORTED — contradicted.** Rubwurm & Körner [158] explain raw optical satellite time series (p. 13); Dantas et al. [157] do counterfactuals for RS time series (p. 13); Table I includes temporal LSTM/transformer models (pp. 15–18). | p. 13 quote above |
| "XAI evaluation is weak — most papers don't validate against ground truth" | **LARGELY FAITHFUL.** ">90% of the studies conduct only anecdotal evaluation" (pp. 23–24); 15/207 studies use functional metrics (p. 12); no standard evaluation exists (pp. 20, 23); "Real-world datasets lack a controlled ground truth for evaluating xAI methods" (p. 20). Minor nuance: some papers validate against domain knowledge (pp. 12–13), and 15 do quantify. | Quotes above |

### Inputs for our XAI validation protocol

- Report quantitative faithfulness metrics for every explanation output — e.g., max-sensitivity, MoReF, drop/increase in confidence when top features are masked (p. 12). >90% of RS-XAI papers are anecdotal-only (pp. 23–24): a quantified protocol directly fills the stated gap and is our differentiator.
- Run sanity checks: model/data randomization tests (Adebayo et al.; Grad-CAM shown sensitive to weight/label randomization, p. 12; §V-A3, pp. 19–20) and quantify robustness across multiple seeds/initializations (p. 19).
- Validate temporal attribution against domain knowledge / ground truth: check that temporal importance aligns with known phenology or stress onset (cf. Rubwurm & Körner [158], p. 13) — for us: stress-treatment timing in the water+salinity experiments.
- Quantitatively evaluate SHAP/LIME outputs — the review "did not find any works that quantitatively evaluate their explanations" for local approximation (p. 13), so quantitative SHAP validation on our Mamba selectivity vectors is novel per their audit.
- Use controlled ground truth: simulation/synthetic data for xAI benchmarking (p. 20), or benchmark on tasks where reliable ground truth exists (p. 12).
- Compare 2–3 xAI methods ("no single method that fits every problem", p. 19); consider a small expert/user study ("a promising research direction", p. 20); score counterfactuals with closeness, sparsity, stability, plausibility (p. 13, Dantas et al. [157]).

**Caveat for novelty claims:** counterfactual explanations for RS time series already exist (Dantas et al. [157], p. 13) — do not claim counterfactuals as wholesale novelty; our edge must be the temporal stress-specific validation, not the method itself.

## XAI Methods for Our Pipeline

| Method | Application | Source |
|--------|-------------|--------|
| **SHAP** | Feature importance on Mamba selectivity vectors | Höhl et al. (Table 1) |
| **Grad-CAM** | Spatio-temporal attention maps | Extend from 2D to 3D |
| **LIME** | Local explanations for individual predictions | Ahmed et al. (2025) |
| **Counterfactuals** | "What if healthy?" generation | Proposed novelty |

---

*Linked from: [[Literature-Matrix]]*
