# 18 — Informed Learning for Drought Stress Estimation (Miranda et al., 2025)

**Full Citation:** Miranda, et al. (2025). Informed Learning for Drought Stress Estimation. *arXiv:2510.18648*.  
**Status:** 🆕

---

## What It Does

Combines crop simulation models (physical/process-based) with machine learning in a physics-informed neural network (PINN) style framework for drought stress estimation.

## Key Approach

- Integrates physical crop growth models with data-driven ML
- Uses process-based constraints as regularization
- Aims to improve generalization beyond training data

## Relevance to Thesis

**Medium** — Physics-informed learning philosophy:
- ✅ Demonstrates hybrid physics+ML approach for agricultural stress
- ✅ Could inspire physics-constrained losses in your architecture
- ⚠️ Focused on drought only (not water-salinity disentanglement)
- ❌ Not satellite-based (model-based rather than RS-based)
- ❌ No temporal XAI component
- ❌ Different domain (crop simulation vs. remote sensing)

## Key Takeaway

Hybrid approaches combining physical understanding with data-driven methods can improve generalization. Consider whether your CNN-Mamba could benefit from physically-informed constraints (e.g., energy balance equations for CWSI).

---

*Linked from: [[Literature-Matrix]]*
