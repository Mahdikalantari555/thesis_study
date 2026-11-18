# 05 — Self-Attention for Raw Optical SITS (Rußwurm & Körner, 2020)

**Full Citation:** Rußwurm, M., & Körner, M. (2020). Self-attention for raw optical Satellite Time Series Classification. *ISPRS Journal of Photogrammetry and Remote Sensing*, 169, 421-435.  
**DOI:** [10.1016/j.isprsjprs.2020.06.006](https://doi.org/10.1016/j.isprsjprs.2020.06.006) | arXiv: [1910.10536](https://arxiv.org/abs/1910.10536) | **332 citations**  
**Status:** ✅ Read  
**Themes:** #Architecture #Raw-bands

---

## What It Does

Compares CNN (MS-ResNet, TempCNN), LSTM, and Transformer on raw vs. preprocessed Sentinel-2 time series for crop type classification.

## Key Findings

| Model | Raw Data Accuracy | Preprocessed Accuracy | Gap |
|-------|------------------|----------------------|-----|
| Transformer | Best on raw | Best overall | Small |
| LSTM | 2nd best | 2nd best | Small |
| CNN (TempCNN) | Weakest | Comparable | 5% gap |
| RF baseline | Worst | Worst | Large |

### Critical Results
- **Self-attention focuses selectively on few classification-relevant time steps** — not diffuse
- **Gradient backpropagation feature importance** shows which spectral bands drive predictions
- **262M processed Sentinel-2 products** in 2018 used for evaluation
- Preprocessing still helped all models, but gap narrowed with attention/RNN

## Relevance to Thesis

| Finding | Application |
|---------|-------------|
| Raw bands > indices for temporal models | Feed raw Landsat bands into CNN, not pre-computed NDVI/EVI |
| Attention focuses on key time steps | Mamba's selectivity is the SSM equivalent |
| Gradient-based feature importance | Direct analogy to SHAP for our XAI pipeline |
| Outperformed CNN on raw data | Justifies attention/SSM over pure CNN |

## Gap for Our Thesis

- Uses 5-day S2 data for crop type
- We need 16-day Landsat for stress differentiation
- Longer gaps make Mamba's selectivity **more valuable** but require better gap-filling

---

*Linked from: [[Literature-Matrix]]*
