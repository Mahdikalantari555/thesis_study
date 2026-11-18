# 33 — JEDI: JEPA-to-Edge Distillation for Efficient Cropland Segmentation (Bhaumik et al., 2026)

**Full Citation:** Bhaumik, K.K., Santos, N.R., Chen, J., & Papalexakis, E.E. (2026). JEDI: JEPA-to-Edge Distillation for Efficient Cropland Segmentation from Satellite Imagery. *arXiv:2609.07915*.  
**Status:** Read

---

## What It Does

Knowledge distillation framework transferring representations from large Vision Transformer (ViT) teacher to compact student models for satellite imagery segmentation.

## Key Innovation

- **Persistent feature alignment**: Alignment objective remains active throughout task adaptation (not just pretraining)
- **Cross-architecture projection**: Handles teacher-student architectural differences
- **Two-stage framework**: (1) Align representations, (2) Joint optimization with segmentation loss + response distillation

## Results

- CalCROP21 dataset: JEDI-B0 achieves 68.0 mIoU with only 4.04M parameters
- 16-point gain over standalone student
- Within 2.0 points of 639M-parameter teacher
- Outperforms response-, structure-, channel-, and relational-distillation baselines

## Relevance to Thesis

**Low** — Foundation model direction:
- ✅ Demonstrates efficient distillation for RS tasks
- ⚠️ Semantic segmentation focus (not stress detection)
- ❌ No temporal modeling
- ❌ No SSL self-supervised pretraining component
- ⚠️ Could inform deployment considerations if your model needs edge deployment

## Key Takeaway

Persistent feature alignment during fine-tuning is crucial for effective distillation. If your CNN-Mamba needs to be deployed in resource-constrained environments, consider distillation strategies from this work.

---

*Linked from: [[Literature-Matrix]]*
