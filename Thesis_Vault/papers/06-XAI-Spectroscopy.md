# 06 — XAI for Spectroscopic Agriculture (Ahmed et al., 2025)

**Full Citation:** Ahmed, M.T., Ahmed, M.W., & Kamruzzaman, M. (2025). A systematic review of explainable artificial intelligence for spectroscopic agricultural quality assessment. *Computers and Electronics in Agriculture*, 235, 110354.  
**DOI:** [10.1016/j.compag.2025.110354](https://doi.org/10.1016/j.compag.2025.110354) | **Open Access**  
**Status:** ✅ Read  
**Themes:** #XAI #Spectroscopy

---

## Note on Advisor's Description

Advisor described this as "systematic review of XAI for agriculture" — actual title is **"for spectroscopic agricultural quality assessment"**. Focuses on NIR, FTIR, Raman, HSI applications, not satellite RS.

## What It Does

PRISMA-guided systematic review of 17 XAI papers (2019–2024) applying SHAP, Grad-CAM, LIME, DeepLIFT, LRP, CAV to spectroscopic ML models.

## XAI Methods Covered

| Method | Use Case | Limitations Discussed |
|--------|----------|----------------------|
| **SHAP** | Feature importance (wavelength selection) | Computationally expensive |
| **Grad-CAM** | Saliency maps for HSI | Resolution issues |
| **LIME** | Local explanations | Instability across runs |
| **DeepLIFT** | Attribution for deep nets | Complex implementation |
| **LRP** | Layer-wise relevance | Limited to NN |
| **CAV** | Concept-based explanation | Requires concept definitions |

## Key Insight for Our Thesis

> The paper discusses **physiological plausibility** of explanations — whether XAI highlights biologically meaningful features. This is directly applicable to our need to validate SHAP outputs against known plant physiology (Angon et al.).

## Gap

None of the 17 reviewed papers apply XAI to **temporal satellite time series** — only to static spectral data.

---

*Linked from: [[Literature-Matrix]]*
