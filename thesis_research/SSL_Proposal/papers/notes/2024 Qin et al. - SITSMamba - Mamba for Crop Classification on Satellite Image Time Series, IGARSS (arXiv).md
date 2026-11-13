# SITSMamba: Crop Classification based on Satellite Image Time Series with Mamba

## Full citation
Qin, X., Su, X., & Zhang, L. (2024). "SITSMamba for Crop Classification based on Satellite Image Time Series." IGARSS 2024, arXiv:2409.09673v2 (Wuhan University). Code: github.com/XiaoleiQinn/SITSMamba.

## Problem & setting
- SITS crop classification with long series (38-61 Sentinel-2 acquisitions in PASTIS); Transformer self-attention is quadratic in sequence length, limiting long time series; and standard supervised training uses only crop labels, under-exploiting temporal structure.
- First application of Mamba (selective SSM) as a SITS temporal encoder.

## Method
- **Architecture**: per-timestep CNN spatial encoder (UTAE's ConvBlock: 2x Conv2D 3x3, 128 filters, BN+ReLU) -> reshape to (H*W) x T x 128 -> **Mamba block** as temporal encoder (linear complexity, selective SSM with SiLU-gated branches).
- **Multi-task two-branch decoder** (key design):
  - *CBranch* (classification): temporal max-pool -> ConvBlock -> per-pixel crop map; cross-entropy L_cls.
  - *RBranch* (reconstruction): Linear layer maps encoded features back to the original SITS values; auxiliary self-supervised signal **integrated directly into supervised training** (not a two-stage pretrain-finetune). MSE loss with **Positional Weight (PW)** {1/L, 2/L, ..., L/L} — later timesteps weighted more (assumption: later positions are easier to predict, so early-season values dominate plain reconstruction otherwise).
  - Overall loss L = L_cls + w0 * w1 * L_tp, w0 = 0.03 (best in sweep 0.01-0.1), w1 = L_cls/L_tp (adaptive loss-ratio balancing).
- Inference uses only CBranch. Trained 100 epochs, Adam lr 1e-4, RTX 3090.

## Data & labels
- **PASTIS32**: PASTIS Sentinel-2 (4 tiles in France, Sep 2018-Nov 2019, 10 bands, 10 m, 38-61 acquisitions), clipped to 32x32 patches, 20 classes, folds 1/4/5 for train/val/test.
- **MTLCC**: Munich 102x42 km, Sentinel-2 2016, 13 bands, 30 timesteps, 6248 patches 48x48, 18 classes, split 4:1:1.
- Supervised labels for CBranch; SITS itself is the unlabeled supervision for RBranch.

## Results
- **PASTIS32**: SITSMamba OA 0.7416, mIoU 0.5005, mF1 0.6449 — beats UTAE (0.7349/0.4686/0.6107), TSVIT (0.7200/0.4561/0.5999), 3D U-Net, BCLSTM and ConvLSTM variants.
- **MTLCC**: OA 0.9104, mIoU 0.7639, mF1 0.8496 — beats UTAE (0.9063/0.7467/0.8391) and BUnetConvLSTM; best F1 in 9/17 classes.
- **Complexity**: only 0.25 M params and 56.5 GFLOPs vs UTAE 1.09 M / 28.8 GFLOPs, TSVIT 2.16 M / 84.4 GFLOPs, 3D U-Net 6.18 M / 274 GFLOPs — smallest model in the comparison.
- **Ablations (PASTIS32)**: full model mF1 0.6449; w/o PW 0.6401 (-0.5 pp); w/o w1 0.6250 (-2.0 pp); w/o RBranch entirely 0.6301 (-1.5 pp) — auxiliary reconstruction consistently helps; w1 (loss-ratio balancing) the most important component.
- Qualitative: better parcel boundary delineation in fragmented areas; better on hard classes (winter triticale F1 0.4632 vs UTAE 0.3407; sorghum 0.4139 vs 0.2697).

## What transfers to our thesis
- **Mamba as temporal encoder for long Landsat series**: linear-complexity sequence modeling fits 16-day composites spanning many years (hundreds of timesteps) where attention becomes expensive; 0.25 M params fits the "lightweight" requirement for in-field deployment.
- The **single-model multi-task design** (classification head + auxiliary reconstruction with positional weighting) is directly reusable: for stress detection, an auxiliary branch reconstructing the NDVI/LST/ETa series (or a forecasting branch) regularizes the encoder without extra labels; PW suggests up-weighting recent/recently-reconstructed timesteps.
- Benchmark context: Mamba ~+0.7-2.8 pp OA over UTAE/TSVIT on 20-class PASTIS with 38-61 timesteps — evidence for the SSM-vs-Transformer trade-off we can cite when justifying our backbone choice.
- Caveat they flag applies to us: reconstructing raw SITS reconstructs cloud/snow noise too — masking or cloud screening is needed; for our stress task, reconstructing *normal* phenology (e.g., on healthy years) is preferable to reconstructing raw inputs.

## Limitations / caveats
- Fully supervised crop classification (labels needed); no stress/anomaly task.
- Mamba only temporal; spatial context by a simple 2-layer CNN; no bidirectional scan (one-directional sequence).
- RBranch reconstructs noisy (cloudy) values — authors note this may harm optimization.
- Sentinel-2 only, 10 m; no Landsat, no thermal; accuracy numbers not directly comparable to full-resolution PASTIS benchmarks (32x32 clipping).

## Key numbers to quote in lit review
- SITSMamba: OA 74.16% (PASTIS32) and 91.04% (MTLCC), first Mamba-based SITS crop classifier.
- Smallest and fastest in comparison: 0.25 M params, 56.5 GFLOPs vs TSVIT 2.16 M / 84.4 GFLOPs.
- Auxiliary in-training reconstruction branch adds +1.5 pp mF1; position-weighted reconstruction loss adds another +0.5 pp.
- Linear-complexity SSMs beat quadratic Transformer temporal attention (UTAE, TSVIT) at 38-61 timesteps while using 4x fewer parameters.
