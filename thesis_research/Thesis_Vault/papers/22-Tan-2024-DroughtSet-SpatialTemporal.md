# 09 — DroughtSet: Spatial-Temporal Drought Learning (Tan et al., 2024)

**Full Citation:** Tan, X., Zhao, Q., Liu, Y., & Zhang, X. (2024). DroughtSet: Understanding Drought Through Spatial-Temporal Learning. *AAAI 2025*, arXiv:2412.15075.  
**PDF:** https://arxiv.org/pdf/2412.15075v1  
**Status:** Read  

## Key Contributions

- **DroughtSet**: Benchmark dataset for drought prediction (CONUS, 2003-2013, 11 years)
- Three drought types: Soil moisture (SM), Ecohydrological (ESI), Ecological (SIF)
- Features: 11 dynamic climate predictors + 9 static geographic features
- Model: **SPDrought** — spatial-temporal Transformer for multi-task drought prediction

## Architecture

```
Spatial Fusion: Attention over 5×5 neighborhood (static features → spatial weights)
↓
Static Feature Rep: MLP (numeric) + Embedding (categorical) → f_s
Dynamic Feature Rep: Transformer Encoder (positional encoding) → f_t(t)
↓
Concatenate → Transformer Decoder → 26-week forecast
↓
3 Task-specific regressors (SM, ESI, SIF)
```

## Interpretability

Uses **Integrated Gradient (IG)** to quantify feature importance over time:
- Identifies which predictors matter most at each lead time
- Reveals spatial correlation patterns across regions
- Provides mechanistic insights into drought development

## Relevance to Thesis

**Low-Medium** — Methodology reference for temporal modeling:
- ✅ 11-year temporal scale (comparable to your 12-year Landsat)
- ✅ Multi-task learning (predict multiple drought types simultaneously)
- ✅ Spatial attention mechanism (could inspire spatial component of your model)
- ✅ Integrated Gradient for interpretability (XAI methodology)
- ❌ Continental scale (4km resolution), not field-scale (30m)
- ❌ Meteorological drought, not plant-level stress
- ❌ No vegetation spectral data (uses climate reanalysis)

## Key Insight

The **multi-task prediction** approach (predicting SM, ESI, and SIF simultaneously) is directly analogous to your goal of predicting water stress, salinity stress, and mixed stress classes. The shared representation + task-specific heads design could be adapted for your stress disentanglement objective.
