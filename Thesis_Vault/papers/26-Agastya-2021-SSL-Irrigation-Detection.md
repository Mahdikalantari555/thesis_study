# 10 — Self-Supervised Contrastive Learning for Irrigation Detection (Agastya et al., 2021)

**Full Citation:** Agastya, C.S., Ghebremusse, S., Anderson, I., Reed, C., Vahabi, H., & Todeschini, A. (2021). Self-supervised Contrastive Learning for Irrigation Detection in Satellite Imagery. *Tackling Climate Change with ML Workshop, ICML 2021*, arXiv:2108.05484.  
**PDF:** https://arxiv.org/pdf/2108.05484v1  
**Status:** Read  

## Key Contributions

- **SimCLR-S2**: Adapts SimCLR contrastive learning framework to Sentinel-2 satellite imagery
- Three-stage pipeline: (1) Pre-train on unlabeled Central Valley CA Sentinel-2, (2) Fine-tune on BigEarthNet-S2 labeled data, (3) Knowledge distillation to student model
- Tests cross-geography generalization (Europe → California → other countries)

## Architecture

```
Stage 1: SimCLR Pre-training
Sentinel-2 (10 bands) → Two augmentations → Contrastive loss (InfoNCE)
→ Pretrained encoder

Stage 2: Fine-tuning
Pretrained encoder + classification head → Binary irrigation detection
BigEarthNet-S2: 190-19,024 labeled samples

Stage 3: Knowledge Distillation
Teacher (fine-tuned) → Student (smaller CNN) → Bootstrap labels for unlabeled data
```

## Results

| Training Size | SimCLR-S2 F1 | Supervised Baseline F1 |
|--------------|-------------|----------------------|
| 1% (190 samples) | **0.99** | 0.11 |
| 3% (570 samples) | **1.00** | 0.20 |
| 10% (1,902 samples) | **0.99** | 0.36 |
| 25% (4,756 samples) | **0.98** | 0.95 |

**Generalization**: 99-100% precision on unseen California data vs. 11-47% for supervised baseline.

## Relevance to Thesis

**Medium** — SSL methodology reference:
- ✅ Proves SSL dramatically outperforms supervised learning with limited labels
- ✅ Cross-geography generalization concept applicable to your transfer learning needs
- ✅ Uses all 10 Sentinel-2 bands (not just VIs)
- ❌ Binary classification (irrigated vs. non-irrigated), not multi-class stress
- ❌ Single-date images, no time series
- ❌ Different task (irrigation detection vs. stress disentanglement)

## Key Insight

With only 1% of labeled data, SimCLR-S2 achieves 99% precision vs. 11% for supervised. This directly supports your argument for SSL pre-training: with only 490 labeled farms, SSL is essential.
