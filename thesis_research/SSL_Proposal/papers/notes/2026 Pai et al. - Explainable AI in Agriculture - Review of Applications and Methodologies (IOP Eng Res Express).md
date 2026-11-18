# Explainable AI in Agriculture: Review of Applications, Methodologies, and Future Directions

## Full citation
Pai, D. G., Balachandra, M., & Kamath, R. (2025/2026). *Explainable AI in agriculture: review of applications, methodologies, and future directions*. Engineering Research Express 7, 032202. DOI 10.1088/2631-8695/ae086a (IOP, topical review, open access).

## Problem & setting
- Topical review of XAI in agriculture, covering peer-reviewed work from 2020 onwards. Domains: crop–weed discrimination, plant disease detection, precision farming/crop recommendation, yield forecasting, soil quality monitoring. Motivation: DL models in agriculture are black boxes; adoption by farmers, agronomists, and policymakers requires transparency.

## Method (survey structure)
- **XAI taxonomy:** white-box vs black-box; model-specific vs model-agnostic; global vs local; intrinsic vs post-hoc. Comparison tables of techniques with properties, tools, and agricultural data fit:
  - **Grad-CAM** (model-specific, CNN heatmaps — leaf disease, weed detection), LIME (model-agnostic, local, superpixels/tabular), SHAP (model-agnostic, global+local, game-theoretic feature attribution — yield prediction from soil/rainfall/fertilizer tabular data), saliency/SmoothGrad (image noise-averaged saliency), LightGBM (interpretable boosting), decision trees/feature importance, counterfactual explanations (Alibi, DiCE), attention mechanisms.
- **Evaluation metrics for XAI itself:** sensitivity(-n), faithfulness correlation/estimate, monotonicity, selectivity, infidelity.
- Reviewed studies tabulated with models (VGG, ResNet, EfficientNet, MobileNet, YOLO variants), datasets (PlantVillage, Plant Seedlings, VegNet, tea-leaf sets, CottonWeedDet12 with 16,944 images), and per-study limitations.

## Results (synthesis)
- **Frequency: LIME most used, then Grad-CAM, SHAP, LightGBM, SmoothGrad;** among DL backbones, ResNet most used, then VGG. Task distribution: plant/leaf disease classification dominates, then yield prediction; vegetation mapping and plant phenotyping least explored (complex environmental/spatial data).
- Example results cited: LIME-explained 38-disease classifier at 99.69% accuracy/precision/recall; EfficientNetV2S 91% for grapevine downy mildew in field conditions; PPLC-Net F1 98.44% with CAM-based validation; YOLOv5-CAcT 94.24% avg accuracy over 59 crop disease categories; YOLOv8-nano + Layer-CAM/Grad-CAM++/Eigen-CAM for 12-class cotton weed detection on edge devices.
- Guiding principle: visual attribution (Grad-CAM/saliency) for image tasks; SHAP/LIME/feature importance for tabular/sensor tasks; counterfactual and concept-based explanations gaining traction for agronomic plausibility.
- Claimed benefit: XAI-enabled precision agriculture systems can reduce water consumption 15–25% while improving yields (as stated in conclusion).
- Challenges: limited generalizability across datasets, dataset bias, real-world applicability unexplored, SHAP computational cost at scale, no standardized XAI evaluation, need for large annotated datasets, accessibility for non-expert users in resource-limited regions.

## What transfers to our thesis
- **Directly maps to the XAI pillar of the thesis:** for our Landsat time-series stress models, the review's modality rule suggests: Grad-CAM/attention-style visualizations for any spatial/temporal encoder components (which dates and which bands drive a stress flag), SHAP/feature-importance for any tabular field-level models (index statistics, ETa/CWSI features), and counterfactual explanations ("which weather/irrigation change would flip this alert") for farmer-facing outputs.
- The XAI-evaluation metrics (faithfulness, selectivity, sensitivity-n, infidelity, monotonicity) are concrete tools to *quantify* explanation quality in our thesis — most remote sensing XAI papers skip this; including them would strengthen the methodology chapter.
- Gap statement to cite: vegetation mapping/phenotyping are the least XAI-explored agricultural tasks, and **satellite time-series stress detection is essentially absent** from the reviewed literature — positioning our work as filling a documented gap.
- Supports using XAI not just post-hoc but as a validation tool: their cited works use CAM overlays to verify the model looks at lesion regions; analogously we can verify stress alerts attend to drought-period observations rather than cloud artifacts or harvest signatures.
- Edge/XAI integration discussion (RepAgrViT, YOLOv8-nano + CAM on edge) aligns with our lightweight in-field deployment requirement.

## Limitations / caveats
- Review quality is mixed: tables rely on secondary description, some entries lack details ("Not Applicable"), and metrics are reported inconsistently across the reviewed literature (the review itself flags this).
- Almost no coverage of remote sensing/satellite XAI, temporal explanation (time-series attribution), or anomaly-detection explanations — the very areas our thesis needs; the review is image- and tabular-centric.
- The 15–25% water-saving figure is asserted without a traceable source — use with caution.
- No quantitative meta-analysis (no effect sizes, no systematic PRISMA-style counts); qualitative categorization only.

## Key numbers to quote in lit review
- LIME and Grad-CAM are the most frequently used XAI methods in agriculture (2020–2025 literature), with SHAP third; ResNet the most common backbone.
- XAI applications cluster in disease classification and yield prediction; vegetation mapping and plant phenotyping are least explored — satellite time-series stress detection is an open gap.
- Example headline results: 99.69% accuracy on 38 plant diseases (LIME-explained); 94.24% avg accuracy on 59 disease categories (YOLOv5-CAcT).
- XAI quality should be evaluated with faithfulness/selectivity/sensitivity/infidelity metrics, not just visual plausibility.
- Claimed XAI-enabled precision agriculture benefit: 15–25% water-use reduction (uncited — verify before quoting).
