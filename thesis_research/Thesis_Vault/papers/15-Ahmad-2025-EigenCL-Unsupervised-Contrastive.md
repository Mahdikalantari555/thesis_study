# 05 — EigenCL: Unsupervised Stress Detection via Contrastive Learning on NDRE (Ahmad, 2025)

**Full Citation:** Ahmad, S. (2025). Temporal Vegetation Index-Based Unsupervised Crop Stress Detection via Eigenvector-Guided Contrastive Learning. *arXiv:2506.03394*.  
**PDF:** https://arxiv.org/pdf/2506.03394v1  
**Status:** Read  

## Key Contributions

- **EigenCL**: Novel unsupervised contrastive learning framework
- Uses temporal NDRE (Normalized Difference Red Edge) time series
- **Eigenvector-guided**: Principal eigenvector of RBF similarity matrix captures 76% variance, correlates r=0.95 with raw NDRE
- Biologically grounded supervision: pulls embeddings together based on similar stress trajectories, pushes apart divergent ones
- Tests on ~10,000 Sentinel-2 NDRE patches from Iowa drought-affected cornfields (2020)
- Validates on independent Nebraska dataset (2023) without retraining

## Architecture

```
Input: 5-point NDRE time series per patch (100×100 pixels, 10m resolution)
→ ResNet50 backbone → 2048-dim embeddings
→ RBF similarity matrix → Principal eigenvector → eigen weight ŵ_i
→ Contrastive loss: Pull (biological similarity) + Push (dissimilarity)
```

## Results

| Metric | EigenCL | Ablation (no eigen) | K-Means | SimCLR |
|--------|---------|---------------------|---------|--------|
| Silhouette Score | **0.748** | 0.533 | 0.465 | 0.416 |
| Davies-Bouldin Index | **0.35** | 0.618 | 0.958 | 0.724 |
| Calinski-Harabasz | **49,624** | 33,446 | 19,305 | 2,252 |

Downstream classifiers (no fine-tuning):
- k-NN: 89.1% accuracy, F1=0.87
- Logistic Regression: 85.2% accuracy, F1=0.82

**Early detection capability**: 76% of stress cases detected up to **12 days before** conventional NDRE threshold crossing.

## Relevance to Thesis

**High** — Methodological blueprint for SSL on vegetation indices:
- ✅ Purely unsupervised (no labels needed for pre-training)
- ✅ Uses NDRE (red-edge band) — directly relevant to Landsat Band 5/6
- ✅ Temporal trajectory-based (not just static snapshots)
- ✅ Proves VI time series alone can drive effective stress detection
- ❌ Drought-only (not salinity or mixed stress)
- ❌ No deep architecture (ResNet50 on VI values, not raw bands)
- ❌ No XAI component
- ❌ Corn, not sugarcane

## Key Insight

> "EigenCL clusters are not driven by static NDRE magnitude but by the trajectory shape, aligning with underlying stress dynamics."

This confirms that **temporal pattern** matters more than absolute VI value for stress detection — directly supports your 12-year Landsat time series approach.
