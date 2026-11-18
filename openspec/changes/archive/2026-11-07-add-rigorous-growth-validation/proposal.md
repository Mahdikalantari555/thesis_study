# Forward-only growth-anomaly validation

## Why
Reconstruction loss and LOYO using future years cannot establish prospective anomaly detection. Existing synthetic scripts sometimes fabricate whole normal cycles, and weak weather proxies are not stress ground truth. We need an auditable baseline for sensitivity to defined changes in real held-out observations, separate from claims about physiological causes.

## What changes
Add complete-cycle chronological and held-out-field partitions, validation-only quantile thresholds, phase-aware median/MAD and trailing-window Isolation Forest, and a paired five-mechanism injection sensitivity benchmark with per-field, point and event reporting. Provide a Zarr/cycle adapter, tests, evidence review and operational documentation. All results are explicitly synthetic perturbation sensitivity, not real stress validation.

## Scope and follow-up
The delivered slice is retrospective and NDVI-focused; it is not the final thesis study. Future work includes SSL adapters, genuinely causal data preparation, field-cluster uncertainty, geographic block selection, independent weather/agronomy evidence, and formal event precision/affiliation metrics. Do not tune or redesign the protocol on final test outcomes.
