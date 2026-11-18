# Quantum-Enhanced Multi-Scale CNN with Bi-Directional Mamba for Crop Field Analysis (CNN-BiSpectralMamba-Quantum)

## Full citation
Khan, M. S., Atoofian, E., & Ahmed, S. B. (2026). *Quantum-Enhanced Multi-Scale CNN with Bi-Directional Mamba for Crop Field Analysis*. arXiv:2606.17222 [cs.CV] (preprint, June 2026, Lakehead University). https://arxiv.org/abs/2606.17222

## Problem & setting
- Task: supervised semantic segmentation/classification of UAV hyperspectral crop imagery — **UAV-HSI-Crop dataset** (China Agricultural University; Majiakou/Xijingmeng villages, Shenzhou, Hebei, China): 433 samples of 96×96 px, 200 spectral bands (400–1000 nm, Resonon Pika-L), ~0.1 m/px, 27–30 crop/land-cover classes with severe class imbalance and limited labels.
- Motivation: transformers reach ~100M+ params (HSI-TransUNet 110M) and need labels that agriculture lacks; Mamba gives linear-complexity sequence modeling but flattening the HSI cube destroys spatial geometry; quantum circuits as cheap global-context heads.

## Method (fully supervised; no SSL, no time series)
- Pipeline: per-band standardization (variance floor 1e-6) → **multi-scale CNN** (two 3×3 conv encoder blocks, 32→64 channels, stride-2 downsample, bilinear upsample + concat fusion) → **spectral Squeeze-and-Excitation** (reduction 16) → flatten to token sequence → **bidirectional Mamba** (forward + flipped-backward S6 selective state-space blocks, outputs summed) → two heads:
  - Classical: LayerNorm + linear → 2-D spatial classification map.
  - **Quantum head:** global average pooling → linear to 4 dims → **4-qubit variational quantum circuit** (PennyLane, angle embedding, 2 Basic Entangler Layers, Pauli-Z expectation values) → class logits; fused as Y_logits = Y_classical + tanh(α)·Y_quantum with learnable α (final α=0.2, init 0.0).
- Loss: λ-balanced (λ=0.5) **class-weighted CE + Log-Cosh Dice**; class weights = inverse-sqrt frequency with 0.7 power scaling. AdamW, lr 3e-4 (classical) / 5e-5 (quantum head), 100 epochs (baselines 200), batch 8, d_model 64.
- Total trainable parameters: **0.24M (246,793)**. Trained on 5×H100 GPUs, 8-hour windows; quantum circuit simulated on CPU.

## Data & labels
- Fully supervised on UAV-HSI-Crop ground-truth masks; no label-free component.

## Results
- Proposed: **OA 84.83%, Kappa 82.07** with 0.24M params vs HSI-TransUNet 86.05%/83.47 at 110M params, HRS-UNet 89.96%/88.14; TransUNet 78.64 (105M); UNet 76.07 (8M); SegNet 43.61 (29M); their earlier QPGF 81.92 (4.1M).
- Ablations: No BiMamba −5.33% OA (79.50) — bidirectional Mamba is the critical core; No Quantum −1.32% (83.51); No SE −0.46% (84.37); **Plain CE actually gives higher OA (85.24)** but sacrifices minority-class boundary fidelity — the hybrid Log-Cosh Dice trades 0.41% skewed global accuracy for equitable minority-crop mapping (Kappa framing).

## What transfers to our thesis
- **Primary transfer: the class-imbalance loss design** — hybrid CE + Log-Cosh Dice with inverse-sqrt frequency power-scaling weights (0.7 exponent) is directly reusable for imbalanced sugarcane stress/anomaly labels (stressed pixels are a minority class); their own ablation showing plain CE inflates OA by ignoring minority classes is a citable metric-methodology caution (report Kappa/IoU per class, not just OA).
- **Mamba/bidirectional SSM over spectral or temporal sequences** as a linear-complexity alternative to transformers supports the thesis interest in lightweight sequence encoders for Landsat time series (relevant to our "lightweight" pillar and to the SSM survey in the same batch).
- Efficiency headline: 0.24M params reaching 84.83% OA vs 110M-param transformer at 86.05% — a 450× parameter reduction for ~1.2 pp OA — strengthens the argument that small models suffice for crop tasks when designed well.
- Literature-review table is a compact digest of Mamba-for-HSI results (SS-Mamba, BiMambaHSI, EchoMamba, S2Mamba with OA 91–99% on standard HSI benchmarks) — useful background for a state-space-model paragraph.
- Honest limitations to echo: Mamba flattening destroys spatial geometry (they patch it with a CNN backbone); quantum head is simulated (no real quantum hardware advantage demonstrated).

## Limitations / caveats
- No SSL, no time series, no satellite data — UAV hyperspectral single-date imagery; far from Landsat 16-day label-free monitoring.
- The "quantum" component is a 4-qubit simulated variational circuit acting as a small global head; contribution is marginal (+1.32% OA) and the framing is inflated relative to the actual mechanics.
- Writing quality issues (promotional tone, "permanently/aggressively" rhetoric, references to GeeksforGeeks, table inconsistency: abstract says 30 classes, Table 1 says 27); preprint, not peer-reviewed.
- Lower OA than HRS-UNet and HSI-TransUNet — the win is parameter efficiency only.
- Baselines trained 200 epochs vs proposed 100 — comparison protocol not fully controlled.

## Key numbers to quote in lit review
- 0.24M-parameter hybrid CNN+BiMamba+4-qubit-quantum reaches 84.83% OA / Kappa 0.82 on UAV-HSI-Crop (27–30 classes) vs 110M-param HSI-TransUNet 86.05%.
- Bidirectional Mamba is the critical component: removing it drops OA 5.33 pp.
- Plain CE yields higher OA (85.24%) than the class-balanced hybrid loss (84.83%) — evidence that global accuracy masks minority-class failure under extreme imbalance.
- Survey-level: Mamba HSI classifiers (SS-Mamba, BiMambaHSI, S2Mamba) report 91.6–99.5% OA on standard benchmarks with linear sequence complexity.
