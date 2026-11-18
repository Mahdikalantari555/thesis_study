# Application of Multimodal Data Fusion and Explainable AI for Classifying Water Stress in Sweet Potatoes

## Full citation
Choi, J.W., Cho, S.B., Hidayat, M.S., Hwang, W.-H., Cho, Y.-S., Lee, H., Cho, B.-K., & Kim, G. (2025). "Application of multimodal data fusion and explainable AI for classifying water stress in sweet potatoes." Frontiers in Plant Science 16:1681915. DOI: 10.3389/fpls.2025.1681915 (Gyeongsang National University et al., Korea).

## Problem & setting
- Water-stress level classification of field-grown sweet potato (cv. Jinyulmi) using low-altitude RGB + thermal (TRI) imagery and growth indicators; two 320 m2 plots, May-Sep 2024; five VWC-based stress classes (Severe Dry <=10%, Dry 20±2%, Optimal 30±3%, Wet 40±3%, Severe Wet 50% volumetric water content), subsurface drip irrigation, TDR soil moisture at 20 cm.
- Aim: practical, low-cost, interpretable water monitoring without specialized hyperspectral/UAV equipment.

## Method
- **ML branch**: features per growth stage (June early, July tuber bulking, August late): leaf temperature (FLIR A65 640x512, emissivity 0.9, ~1.05 m height, 6-7 a.m., mean of 3 manually-selected leaf regions), modified CWSI, stem length, NDVI, SPAD, chlorophyll fluorescence. RF-based feature importance selects top-4 per stage (e.g., July: CWSI 0.271, leaf temp 0.161, SPAD 0.172, NDVI 0.152); classifiers LR/RF/KNN/MLP/SVM on 300 samples (50/stage, O doubled 1:1:2:1:1), 80/20 split + 5-fold stratified CV.
- **Modified CWSI** (key contribution): replaces unmeasurable T_wet/T_dry with field-observable variables — correction coefficient d = 2 + 0.1*|soil moisture - 30| + 2*(1 - RH/100), capped at 6; T_wet = T_a - d; T_dry fixed at 34 degC (max observed); CWSI = (T_c - T_wet)/(T_dry - T_wet), clipped to [0.05, 1].
- **DL branch**: CNN+ViT (~220k trainable params; fused system ~30.5 M incl. GUI) — separate CNNs for RGB (128x128, color-calibrated) and thermal (grayscale), thermal channels filtered by mean activation >0.1, GAP + channel-concat fusion, Transformer block, 3-class output. 904 images (452 thermal + 452 RGB), Adam 1e-3, batch 64, up to 100 epochs, early stopping patience 10, 5-fold CV.
- **Deployment**: Tkinter GUI ("sweet potato water monitor system") — averages KNN + CNN-ViT predictions, shows Grad-CAM attention maps for RGB and thermal separately, ~30.5 M params, near real-time on CPU.

## Data & labels
- Labels: irrigation-treatment VWC classes (SD/D/O/W/SW); 2,374 leaf-temperature observations (after +/-3-sigma outlier removal from 2,399); ANOVA leaf temp across classes F=2.376 (text) / 12.57 (table), p<0.05.

## Results
- ML: KNN best at all stages — June test acc 1.0 (CV 0.94), July 1.0 (CV 0.96), August 1.0 (CV 0.94); RF/LR/SVM ~0.84 in June/Aug; misclassifications concentrated at adjacent/mid classes (O confused with W or SD).
- DL: 5-class CNN+ViT accuracy only 0.75 (loss 0.7); merging to 3 classes (Severe Dry, Optimal, Severe Wet) raises accuracy to 0.92 (0.97 in confusion matrix: SD 100%, SW 100%, O 97%), 5-fold CV 0.91.
- Grad-CAM visualizations localize stress-relevant canopy regions per modality; GUI merges both models for decision support (irrigate/maintain/reduce).

## What transfers to our thesis
- **CWSI is the thermal anchor of our thesis** — this paper shows the CWSI's main practical bottleneck (needing T_wet/T_dry) can be circumvented by redefining it with field-observable/measurable variables. For Landsat: LST + air temperature reanalysis + soil moisture/precipitation products can define an analogous CWSI proxy without in-situ wet/dry reference — a concrete design for our ETa/CWSI multi-product input.
- Confirms **thermal signal alone separates extreme water stress classes perfectly (100% SD and SW)** but struggles with intermediate stress — supports our thesis framing of stress detection as early/anomaly detection (deviation from normal) rather than fine-grained multi-class staging.
- Supports **coarse class schemes** (3 levels: deficit/optimal/excess) as both more accurate and more actionable — matches operational irrigation decisions for sugarcane.
- Grad-CAM per-modality maps: template for the XAI component of our thesis (which bands/dates drive stress predictions); shows the GUI/deployment pattern for farmer-facing lightweight tools.
- Cites the sugarcane-relevant prior: de Melo et al. 2022 (Inception-ResNet-v2 on thermal images for sugarcane water deficit, +23/17/14% accuracy at AWC 25/50/100%) — useful related-work anchor.

## Limitations / caveats
- Small scale: one cultivar, one field, one season, ~300 tabular samples / 452 image pairs; near-perfect accuracies on tiny test sets (20% of 300) with doubled optimal class — overfitting risk; no external validation.
- Static single-date imagery; authors explicitly note no temporal stress accumulation modeling — the gap our 16-day time-series thesis fills.
- Ground-level 1.05 m thermal imaging, not satellite; leaf temp extraction is manual (3 hand-drawn ROIs); CWSI modification is ad hoc (fixed T_dry 34 degC, heuristic d formula) — not validated against standard Idso/Jackson CWSI or ETa.
- Supervised only; no SSL; label noise from VWC classes defined by irrigation treatment.

## Key numbers to quote in lit review
- Modified CWSI using field-observable variables (air temp, RH, soil moisture) enables CWSI computation without wet/dry reference surfaces.
- Thermal+RGB CNN-ViT: 5-class accuracy 0.75 vs 3-class 0.92 (CV 0.91); extreme classes classified with 100% accuracy, optimal 97%.
- KNN on growth indicators + CWSI + leaf temperature: CV accuracy 0.94-0.96 across growth stages; CWSI the most important feature at tuber bulking (importance 0.271) and late growth (0.265).
- 30.5M-parameter fused system runs near real-time on CPU with on-the-fly Grad-CAM — feasibility evidence for lightweight in-field deployment.
