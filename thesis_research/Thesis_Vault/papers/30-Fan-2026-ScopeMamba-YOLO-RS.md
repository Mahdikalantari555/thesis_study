# 30 — ScopeMamba-YOLO: Mamba for Small Object Detection in RS Imagery (Fan et al., 2026)

**Full Citation:** Fan, J., Mai, Y., Wei, L., Rao, J., Bao, J., Jin, Q., Li, G., & Qi, Y. (2026). ScopeMamba-YOLO: Widening the Perceptual Scope Inward and Outward for Small Object Detection in Remote Sensing Imagery. *arXiv:2609.10156*.  
**Status:** Read

---

## What It Does

Applies Mamba (state space model) architecture to small object detection in UAV/remote sensing imagery.

## Key Architecture Innovations

- **Off-path selective scanning**: Decouples contextual modeling from convolutional stream
- **Cascaded Global-Context Module (CGCM)**: In backbone
- **Selective-Scan PAN (SS-PAN)**: In neck
- **Adaptive Multi-scale Strip (AMS) Block**: Reduces high-resolution feature cost
- **Scale-Adaptive DFL (SA-DFL) head**: Reallocates regression capacity across scales

## Performance

- VisDrone-2019: 50.8% mAP50 (ScopeMamba-S, 3.57M params)
- Exceeds YOLOv8s by 10.8 pp with 32% of parameters
- Significant improvements on very-tiny objects (<16×16 px)

## Relevance to Thesis

**Low** — Alternative Mamba implementation for inspiration:
- ✅ Demonstrates Mamba for RS object detection (not SITS time series)
- ✅ Shows off-path selective scanning preserves local cues
- ⚠️ Object detection focus, not pixel-wise stress detection
- ❌ No temporal sequence modeling
- ❌ No SSL/XAI component
- ⚠️ Could inspire architectural choices for your CNN-Mamba (e.g., how to integrate Mamba without losing local detail)

## Key Takeaway

Mamba can be effectively adapted for RS tasks while maintaining computational efficiency. The "off-path" design principle (decoupling global context from local features) could inform how you integrate Mamba with CNN branches in your stress detection model.

---

*Linked from: [[Literature-Matrix]]*
