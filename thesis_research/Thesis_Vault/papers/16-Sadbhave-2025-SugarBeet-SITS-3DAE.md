# 16 — Sugar-Beet Stress Detection Using SITS (3D-Autoencoder) (Sadbhave et al., 2025)

**Full Citation:** Sadbhave, B.L., Vaeth, P., Dejon, D., Schorcht, G., & Gregorová, M. (2025). Sugar-Beet Stress Detection using Satellite Image Time Series. *arXiv:2507.13514*.  
**PDF:** https://arxiv.org/pdf/2507.13514v1  
**Status:** Read

---

## What It Does

Fully unsupervised stress detection in sugar-beet fields using Sentinel-2 SITS data and a 3D convolutional autoencoder.

## Architecture

```
Input: Sentinel-2 sequences (H×W×C×T) where C=10 bands, T=7 timepoints
→ 3D Convolutional Autoencoder (spatiotemporal feature extraction)
→ Acquisition-date-specific temporal encodings (phenology-aware)
→ Latent representations → Clustering (stress vs. healthy)
```

## Key Technical Features

- **3D CNN**: Captures spatial-spectral-temporal patterns jointly
- **Temporal encodings**: Acquisition date features help distinguish growth stages
- **Unsupervised**: No labels needed for training; only used for evaluation
- **Cross-year generalization**: Model trained on 2019 data applies to other years

## Results

- Evaluated on 35 stressed + 26 healthy sugar-beet fields (2019)
- 10 spectral bands (excluding Band 1, 9, 10 for redundancy/cloud mask)
- Resampled to 10m resolution
- Code available at: https://github.com/bhumikasadbhave/Sugar-beet-Stress-Detection-System.git

## Relevance to Thesis

**High** — Direct methodological parallel:
- ✅ Unsupervised SITS approach (matches your SSL requirement)
- ✅ 3D CNN for spatiotemporal feature extraction (similar to your CNN-Mamba idea)
- ✅ Temporal encoding strategy (acquisition dates → phenology awareness)
- ✅ Same crop family (sugar-beet ≈ sugarcane in structure)
- ✅ Public codebase for reference implementation
- ❌ No salinity stress component
- ❌ No XAI/explainability
- ❌ No contrastive learning (uses autoencoder reconstruction)

## Key Insight for Your Thesis

The temporal encoding approach (adding acquisition date as auxiliary input) is directly transferable to your CNN-Mamba model. Consider implementing similar date-aware temporal modeling for your SITS inputs.

---

*Linked from: [[Literature-Matrix]]*
