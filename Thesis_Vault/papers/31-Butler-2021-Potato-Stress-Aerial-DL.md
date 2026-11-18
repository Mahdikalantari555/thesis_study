# 31 — Potato Crop Stress Identification in Aerial Images using DL Object Detection (Butler et al., 2021)

**Full Citation:** Butler, S., Vakanski, A., Duellman, K., Wang, H., & Mirkouei, A. (2021). Potato Crop Stress Identification in Aerial Images using Deep Learning-based Object Detection. *arXiv:2106.07770*.  
**Status:** Read

---

## What It Does

Deep learning object detection for drought stress identification in potato crops from aerial imagery.

## Key Model

- **Retina-UNet-Ag**: Variant of Retina-UNet with connections from low-level semantic maps to feature pyramid
- Trained on Parrot Sequoia camera imagery ( multispectral)
- Target: Healthy vs. stressed (premature senescence from drought) plants at individual plant level

## Results

- Average Dice Score Coefficient: 0.74
- Effective for distinguishing healthy/stressed plants in natural field conditions
- Dataset: Russet Burbank potato under drought stress

## Relevance to Thesis

**Low** — Shows limitations of pixel-wise vs. temporal approaches:
- ✅ Demonstrates plant-level stress detection works
- ⚠️ Aerial (UAV) imagery, not satellite
- ❌ No temporal component (single-date images)
- ❌ Single stress type (drought only)
- ❌ No SITS modeling
- ⚠️ Illustrates that pixel-wise/object-level approaches may miss systemic stress patterns detectable via time series

## Key Takeaway

Spatial object detection can identify stressed plants, but temporal dynamics (how stress evolves) provide complementary information about systemic water/salinity stress that single-date imagery cannot capture. This supports your argument for SITS-based approaches.

---

*Linked from: [[Literature-Matrix]]*
