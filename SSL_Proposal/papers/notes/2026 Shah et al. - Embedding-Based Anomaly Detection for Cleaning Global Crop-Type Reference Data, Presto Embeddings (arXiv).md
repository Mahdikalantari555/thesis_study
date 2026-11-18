# Embeddings based Anomaly Detection for Cleaning Global Crop Type Reference Datasets (EBA detector)

## Full citation
Shah, S. R. A., Van Tricht, K., Butsko, C., Degerickx, J., & Szantoi, Z. (2026). *Embeddings based Anomaly Detection for Cleaning Global Crop Type Reference Datasets*. arXiv:2607.23908v2 [cs.CV] (VITO Remote Sensing + ESA; WorldCereal project, ESA grant 4000130569/20/I-NB). Code: github.com/WorldCereal/EBA_detector

## Problem & setting
- Task: **label-noise detection / reference-data cleaning** for global crop-type and land-cover mapping (WorldCereal Reference Data Module, several million samples from LPIS parcel registers, LUCAS surveys, national databases, map-derived labels — each with distinct error modes).
- Key conceptual distinction: an EO outlier can be a genuine extreme event (drought, flood — scientifically valuable) or a label error; this work targets the latter — samples anomalous *relative to same-class neighbours in the same locality*, which indicates mislabelling rather than real events.
- Data: WorldCereal reference points (field centroids) with S1/S2/meteo/terrain time series composited to 12 monthly steps; labels grouped into coarser legend (e.g., wheat merged); Presto (lightweight SSL EO time-series transformer, 128-d embeddings, official pretrained weights, embeddings aligned to valid crop time); AlphaEarth 64-d embeddings tested as alternative.

## Method
- **Locality-aware embedding-based anomaly (EBA) detection:** slices = H3 hexagonal grid cells (level L∈{1,2,3}) × label (+dataset id, year); min 50 samples/slice, merge or exclude undersized slices. Within each slice, per-sample anomaly score combines (1) cosine distance to a **trimmed (contamination-resistant) centroid** (iteratively discard farthest τ fraction to defeat masking/swamping), and (2) mean cosine distance to k nearest same-class neighbours. Normalize by slice-specific empirical percentiles → average; combine with rank-based score and MAD-based robust z-score into mean_score.
- **Flagging:** MAD rule — flag when score exceeds slice median by >k=4 MADs, capped at 10% of slice; graded as normal / flagged / suspect (Srank>0.98) / candidate (Srank>0.99).
- **Confidence weighting:** confidence_nonoutlier = accelerating exponential decay applied only to flagged points (knee t=0.975 default / 0.95 tightened, γ=0.30/0.23); unflagged points keep confidence 1.
- **Safeguards:** silhouette-style separability gate pulls flagged confidence back to 1 where the frozen encoder fails to separate classes (degenerate neighbourhoods); embeddings from official pretrained weights avoid label leakage.
- **Treatments swept on training split:** baseline / drop candidates / drop candidates+suspects / drop all flagged / down-weight / confidence-threshold filters (0.90/0.95). Held-out split fixed and spatially split (H3 + source dataset) to prevent leakage; metrics on three test views (full, candidates-removed, confidence-weighted).
- Evaluation: (1) synthetic label-noise injection (gross / subtle confusable-class / whole-dataset corruption); (2) model-independent test (re-score fixed trained models after removing/down-weighting flagged test points); (3) downstream WorldCereal dual-head model across 5 macro-regions; CatBoost proxy sweeps; manual visual audit.

## Results
- **Synthetic recovery:** planted gross errors concentrated 4.3–5.0× above chance in flagged sets (AUROC up to 0.84, top-5% lift to 9×); subtle confusable errors 3.0–3.8× (AUROC ≈0.72); detection strongest at low noise rates typical of real data; whole-dataset corruption correctly at chance (≈1.0×, AUROC 0.50) — a stated limitation of any local detector. Weakest region Eastern Africa (2.5×, smallholder mixed cropping).
- **Model-independent test:** down-weighting flagged test points raises measured macro-F1/accuracy in 54/55 (crop type) and 55/55 (land cover) of 55 trained models per configuration — essentially deterministic.
- **Downstream cleaning:** with the tightened detector, best treatment improves WorldCereal crop-type macro-F1 in all 5 regions (+1.2 to +3.4, mean +2.1) and land cover in all 5 (+0.3 to +1.7). **Conservative cleaning wins: candidate removal or confidence weighting best; dropping all flagged points is the worst policy** (discards hard-but-correct boundary samples); CatBoost proxy confirms (filter_0.90 +0.7; drop_flagged −1.1).
- **Gains concentrated in rare/confusable classes** (e.g., millet +15 F1 points in Southern Asia); majority crops unchanged.
- **Ablations:** H3 locality matters (removing it: gross AUROC 0.79→0.66); off-the-shelf Isolation Forest/LOF on the same embeddings sit at chance (0.50) — the class-conditional local formulation is the differentiator; fine-tuned WorldCereal encoder improves recovery (gross 4.3×→4.9×, AUROC 0.79→0.84); AlphaEarth embeddings surface analogous anomalies (encoder-agnostic pipeline); visual audit found 0% "wrong" flags for crop classes (only "good" or "uncertain").

## What transfers to our thesis
- **Directly reusable for our thesis's data quality problem:** our sugarcane field labels (and any stress ground truth) will contain noise from inconsistent surveyors, mixed pixels, and temporal mismatches. The EBA recipe — SSL-encoder embeddings + same-class locality slices + trimmed centroid + MAD flagging + confidence weighting, with conservative cleaning — is an operational, citable template for cleaning our training reference data before fitting the stress models.
- **Conceptual framing worth adopting:** the dual nature of outliers (genuine extreme events vs label errors). For our stress detection, "anomalous relative to same-crop same-locality peers" is exactly the right null model: a drought-stressed sugarcane field is anomalous vs healthy peers (genuine signal), whereas a field labeled stressed but embedding-identical to healthy peers is a suspect label. This same locality-aware scoring can double as our label-free stress anomaly score itself, not just label cleaning.
- Design lessons with quantitative backing: (1) locality slicing is essential (removing H3 halves detection AUROC 0.79→0.66); (2) generic detectors (Isolation Forest, LOF) on good embeddings are useless without class-conditional, local formulation (chance level); (3) trimmed centroid prevents outlier self-masking; (4) conservative cleaning > aggressive cleaning (over-cleaning hurts: −1.1 macro-F1).
- Embeddings from a stronger/fine-tuned encoder improve label-error recovery (4.3→4.9×) — supports our plan to fine-tune the SSL encoder on sugarcane-region data before using its embedding space for anomaly scoring.
- The confidence-weighting (soft down-weighting instead of deletion) is a practical compromise for small in-field datasets where deleting samples is costly.

## Limitations / caveats
- Monthly 12-step composites (Sentinel-based WorldCereal), not 16-day Landsat; crop-type/land-cover labels, not stress labels.
- Point-level (field centroid) detection; no spatial segmentation or within-field heterogeneity.
- Cannot detect whole-dataset/systematic legend corruption by construction (acknowledged); frozen-encoder separation limits flags where the encoder is uninformative (silhouette gate mitigates only).
- WorldCereal downstream runs use a single seed (~±0.8 macro-F1 noise floor) — region-level gains near the floor are "suggestive"; synthetic injection defines ground truth only for scattered errors.
- Flagged points may be legitimate rare management practices or mixed pixels; removal-vs-weighting is a precision/recall choice requiring application-specific tuning.

## Key numbers to quote in lit review
- Embedding-based, locality-aware (H3 slice) anomaly detection recovers injected label errors at 2.5–5× above chance (AUROC up to 0.84); Isolation Forest/LOF on the same embeddings sit at chance (0.50).
- Conservative cleaning (candidate removal / confidence weighting) improves WorldCereal crop-type macro-F1 in all 5 macro-regions (+1.2 to +3.4); aggressive removal of all flagged points is the worst policy.
- Down-weighting flagged test points improves measured macro-F1 in 54/55 models (crop type) and 55/55 (land cover) — model-independent evidence that flags concentrate unreliable labels.
- Removing H3 locality drops gross-error recovery AUROC from 0.79 to 0.66 — locality is the key design element.
- Gains concentrate on rare/confusable classes (millet +15 F1); majority crops unaffected.
