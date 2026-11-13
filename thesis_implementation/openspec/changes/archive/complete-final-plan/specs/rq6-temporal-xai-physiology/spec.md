# Spec Delta

## Purpose

Delivers temporal SHAP, 1D Grad-CAM, Integrated Gradients, and sliding-window occlusion attributions for SSL anomaly scores, validated via deletion/insertion faithfulness AUC, weight-randomization sanity checks, and biophysical sign-direction alignment (RQ6).

## ADDED Requirements

### Requirement: Temporal SHAP, 1D Grad-CAM, and path-gradient attributions
The system SHALL compute phase-bin and channel attributions for SSL anomaly detections using coalition Temporal SHAP, 1D Temporal Grad-CAM over encoder layer activations, Integrated Gradients, and temporal window occlusion, aggregated into three coarse sugarcane growth stages.

#### Scenario: Temporal SHAP and Grad-CAM localize mid-cycle canopy-thermal anomaly
- **WHEN** `run_rq6_xai.py` explains an anomalous cycle with mid-season canopy loss and canopy warming
- **THEN** Temporal SHAP, 1D Grad-CAM, and Integrated Gradients produce finite `(T, D)` attribution maps peaking in the affected growth stage

### Requirement: Faithfulness AUC, weight-randomization sanity, and plant-physiology validation
The system SHALL compute deletion AUC, insertion AUC, weight-randomization attribution degradation, and plant-physiology direction concordance (verifying negative `NIR`/`NDVI`/`NDMI` and positive `LST`/`SWIR` directions under water/canopy stress).

#### Scenario: Physiology concordance and sanity check validate learned attributions
- **WHEN** attributions are evaluated on stress-corroborated cycles before and after randomizing model weights
- **THEN** trained attributions achieve positive physiology sign concordance above chance while weight randomization substantially reduces attribution rank correlation
