# 01 — SITSMamba (Qin et al., 2024)

**Full Citation:** Qin, X., Su, X., & Zhang, L. (2024). SITSMamba for Crop Classification based on Satellite Image Time Series. *arXiv:2409.09673*.  
**Status:** ✅ Full read (2026-10-04)  
**Themes:** #Mamba/SITS #Multi-task-Learning #Architecture *(tag corrected 2026-10-04: training is supervised multi-task, not SSL — see Repo-claim verification)*

---

## What It Does

First Mamba architecture applied to satellite image time series (SITS) for crop classification. Hybrid CNN-Mamba with dual-decoder branches.

## Architecture

```
Input: SITS (T × H × W × C)   [Fig. 2, p.4; text writes I ∈ R^(T×C×H×W), Sec. III-F, p.5]
    │
    ▼
┌──────────────────┐
│  ConvBlock       │  2× (Conv2D 3×3 pad-1 → BN → ReLU), 128 filters
│  (spatial enc.)  │  applied per timestep  [Fig. 2 inset; Sec. III-F, p.5]
└──────────────────┘
    │
    ▼  reshape T×C1×H×W → (H·W)×T×C1  (C1 = 128)   [Sec. III-F, p.5]
┌──────────────────┐
│  Mamba Temporal  │  ONE Mamba block over T, default params
│  Encoder         │  Linear→Conv1D→SiLU→SSM ⊗ (Linear→SiLU)→Linear
└──────────────────┘  [Fig. 3, p.4; Sec. III-C/F — temporal only, no spatial scan]
    │
    ├──► CBranch: MaxPool over T → ConvBlock(Conv2D C_cls + BN + ReLU) → crop map H×W×C_cls
    │            [Sec. III-F, p.5]
    │
    └──► RBranch: single Linear layer C1→C → reconstruct original input T×H×W×C
                 (PW applied to its MSE loss)  [Fig. 2; Sec. III-D, p.4–5]
```

*(Corrected 2026-10-04 from full read: the previous version of this diagram said "ResNet-style block" and "Hilbert curve scan path" — neither appears anywhere in the paper.)*

## Key Innovations

| Component | Purpose | Thesis Application |
|-----------|---------|-------------------|
| **Positional Weight (PW)** | Linearly increasing loss weight {1/L, …, L/L} over temporal positions of the reconstruction MSE (Eq. 5, Sec. III-D, p.5) | ✅ Directly applicable — learns which timesteps matter for stress |
| **Dual-branch decoder** | Classification + **auxiliary** reconstruction in single-stage supervised multi-task training (NOT SSL pretraining; Sec. I, p.2; Algorithm 1, p.5) | ✅ Use reconstruction for stress-relevant indices (not raw bands) |
| **Loss composition** | L = L_cla (CE) + w0·w1·L_p (PW-weighted MSE); **NO contrastive loss** (corrected 2026-10-04 — was wrongly listed as "contrastive loss between branches") | ✅ Adapt for stress phenology learning |
| **Two weighting factors** | w0 = 0.03 (fixed; Fig. 7 sweep, p.10); w1 = L_p/L_cla ratio for adaptive scale-matching (Sec. III-E, p.5) | ✅ Tunable for our stress-specific reconstruction target |

## Gaps for Our Thesis

| Gap | Impact | Our Fix |
|-----|--------|---------|
| Trained on **crop type**, not stress | Architecture transferable but objective differs | Swap auxiliary task to stress-index reconstruction (paper's auxiliary task is raw-band reconstruction; it has no contrastive/pretext stage) |
| Uses **Sentinel-2** (5-day revisit) | We use Landsat (16-day) — longer gaps | Mamba's selectivity is *more* valuable with longer gaps |
| **No thermal bands** | Water stress needs LST/CWSI | Add thermal channel to CNN input |
| Reconstruction predicts **raw bands** | Not stress-relevant | Predict stress indices (NDWI, CWSI anomalies) instead |

## Code

- GitHub: https://github.com/XiaoleiQinn/SITSMamba — `Model/SITSMamba.py` + `Main_SITSMamba.py` only; no license, no weights, no dataloaders (see Verified findings §5)
- PASTIS dataset (France) — not directly transferable to Khuzestan

## Key Quote

> "The quadratic complexity of self-attention in Transformer poses challenges for classifying long time series. While Mamba has demonstrated strength in various domains... its capacity to learn temporal representations in SITS data remains unexplored."

## Action Items

- [x] Clone GitHub repo and review code structure *(done via web review 2026-10-04: model file exists but may be incomplete — run it before adopting; see Repo-claim verification)*
- [ ] Adapt CNN backbone for Landsat bands + LST *(single `input_dim` change in released code — see Thermal-channel insertion point)*
- [ ] Replace reconstruction target from raw bands to stress indices
- [ ] Implement Positional Weight for temporal attention visualization *(note: PW is a loss re-weighting, not attention — Eq. 5)*

## Verified Full-Text Findings (2026-10-04)

Full read of arXiv:2409.09673v2 (12-page PDF: `papers/01-Qin-2024-SITSMamba.pdf`). Every number below cites its Sec./Eq./Table/Fig./page in that PDF. Repo checked same day at https://github.com/XiaoleiQinn/SITSMamba.

### 1. Positional Weight (PW) — verified
- **Formulation:** per-timestep weights {1/L, 2/L, …, (L−1)/L, L/L} multiplying the squared reconstruction error of each temporal position: L_p(X,T) = Σ_n [ (1/L)(X_n^0−T_n^0)² + (2/L)(X_n^1−T_n^1)² + … + (L/L)(X_n^{L−1}−T_n^{L−1})² ] — **Eq. 5, Sec. III-D, p.5**.
- **Rationale (paper's own):** "the earlier the position in the sequence, the more difficult it is to predict its value" → early timesteps are *down*-weighted; weight grows linearly with temporal order (Sec. III-D, p.5; contribution 3, Sec. I, p.2; abstract).
- **Scope:** PW is applied only to the RBranch MSE loss — it is a loss re-weighting, not an attention mechanism or anything inside the encoder (Fig. 2, p.4).
- **Ablation (PASTIS32):** w/o PW → OA 0.7406 / mIoU 0.4970 / mF1 0.6401 (−0.74% mF1 vs 0.6449); w/o w1 → 0.7351/0.4828/0.6250; w/o RBranch entirely → 0.7337/0.4875/0.6301 (**Table VII, Sec. IV-F, p.9**). w0 sweep: best at 0.03 across OA/mIoU/mF1; higher values (0.05–0.1) degrade — too much RBranch weight disrupts CBranch training (**Fig. 7, Sec. IV-F, p.10**).

### 2. Training scheme & loss — verified (and "SSL" verdict)
- **Single-stage supervised multi-task learning — NOT self-supervised pretraining-then-finetune.** The paper explicitly contrasts itself with SSL: "Different from the two-step frameworks typical in SSL, we integrate the SITS reconstruction task directly into the crop classification workflow and developed a multi-task framework" (**Sec. I, p.2**; restated in Related Work, Sec. II-A-1, p.3).
- **Algorithm 1 ("Training and Testing of SITSMamba", p.5):** training input = "Image time series *I* and crop label *Y* in the training dataset"; one pass: S=ConvBlock(I) → S_R=Reshape(S) → T=Mamba(S_R) → T_max=Reshape(Maxpool(T)) → O_cls=ConvBlock(T_max), O_rec=Linear(T); loss = L_cla(Y, O_cls, L) + w0·w1·L_rec; Adam update. At inference only the CBranch is used; RBranch is ignored (**Sec. III-A, p.3–4**).
- **Loss composition:** classification = cross-entropy L_cla (**Eq. 6, Sec. III-E, p.5**); reconstruction = PW-weighted MSE L_p (Eq. 5); overall **L(Y,Ŷ,X,T) = L_cla + w0·w1·L_p** (**Eq. 7, Sec. III-E, p.5**).
- **The two weighting factors:** **w0 = 0.03** (Sec. III-E, p.5; confirmed as best in Fig. 7 sweep, p.10); **w1 = L_p/L_cla** — the running ratio of the two losses, used to scale L_p adaptively ("We also use the ratio of the two losses, w1 = L_p/L_cla, to control the scale of L_p", Sec. III-E, p.5).
- **Implementation details:** 100 epochs, Adam, lr 0.0001, batch 8 (PASTIS32) / 4 (MTLCC); PASTIS sequences padded to equal length per minibatch, MTLCC temporally sampled to 30 steps; NVIDIA RTX 3090 (**Sec. IV-D, p.7**). Mamba block "configured with its default parameter settings" (**Sec. III-F, p.5**).

### 3. Architecture dimensions — verified
- **Input format:** Fig. 2 (p.4) labels the input T×H×W×C; the text writes I ∈ R^{T×C×H×W} (**Sec. III-F, p.5**) — same tensor, order of labels differs between figure and text. C = 10 bands (PASTIS32) or 13 bands (MTLCC); T = 38–61 observations per site for PASTIS (padded), 30 for MTLCC (**Sec. IV-A, p.5–6**).
- **Spatial encoder (ConvBlock):** two Conv2D layers, each 3×3, padding 1, BN + ReLU, **128 filters** → T×C1×H×W with C1=128; then reshaped to (H·W)×T×C1 (**Sec. III-F, p.5**; Fig. 2 inset: "3×3 conv, 128 / BN / ReLU").
- **Temporal encoder:** one Mamba block over T; block structure = Linear → Conv1D → SiLU → SSM, multiplied (⊗) with a second Linear→SiLU branch, then a final Linear (**Fig. 3, p.4**; Sec. III-C). Mamba is **temporal only** — the authors state as a limitation that "our current implementation of Mamba focuses solely on the temporal dimension" (**Sec. V-B, p.10–11**). No spatial scan, no Hilbert curve.
- **CBranch:** MaxPool over T → H×W×C1 → ConvBlock (Conv2D with C_cls filters + BN + ReLU) → crop map H×W×C_cls (**Sec. III-F, p.5**).
- **RBranch:** a **single Linear layer** C1→C predicting the original input values, output T×H×W×C (**Sec. III-D, p.4–5**; Fig. 2, p.4).
- **Complexity:** 0.25 M params (smallest of all compared models; BCLSTM 0.29 M, TSViT 2.16 M, 3D U-Net 6.18 M) and 56.53 GFLOPs (UTAE is cheaper at 29.77) (**Table VIII, Sec. V-A, p.10**).

### 4. Benchmarks — verified
Datasets (**Sec. IV-A, p.5–6; Tables I–II, p.6**):
- **PASTIS32** — PASTIS (France; Sentinel-2, Sep 2018–Nov 2019; 10 bands; 128×128 px patches) clipped to 32×32; 20 classes; 5 folds, fold-1 train / fold-4 val / fold-5 test.
- **MTLCC** — Munich, Germany (102×42 km); Sentinel-2 from 2016; 48×48 px; 13 bands; 30 time steps; 4:1:1 train/val/test; 17 classes evaluated (Table II lists 17 crop classes + background).

Metrics: OA, IoU, F1; mIoU and mF1 average equally over classes (**Sec. IV-C, p.6**).

| Dataset | Model | OA | mIoU | mF1 |
|---|---|---|---|---|
| PASTIS32 (**Table III, p.7**) | **SITSMamba** | **0.7416** | **0.5005** | **0.6449** |
| | UTAE (best baseline) | 0.7349 | 0.4686 | 0.6107 |
| | TSViT | 0.7200 | 0.4361 | 0.5999 |
| | BUnetConvLSTM | 0.7155 | 0.4025 | 0.5401 |
| | 3D U-Net | 0.7057 | 0.3999 | 0.5358 |
| | BAtrousConvLSTM | 0.7024 | 0.3917 | 0.5327 |
| | BCLSTM | 0.6697 | 0.3057 | 0.4282 |
| MTLCC (**Table IV, p.7**) | **SITSMamba** | **0.9104** | **0.7639** | **0.8496** |
| | BUnetConvLSTM | 0.9070 | 0.7390 | 0.8344 |
| | UTAE | 0.9063 | 0.7467 | 0.8391 |
| | BAtrousConvLSTM | 0.9010 | 0.7328 | 0.8262 |
| | TSViT | 0.8954 | 0.7358 | 0.8299 |
| | 3D U-Net | 0.8926 | 0.6801 | 0.7908 |
| | BCLSTM | 0.8829 | 0.6353 | 0.7449 |

- Headline (abstract, p.1): OA **0.7416** (PASTIS32) and **0.9104** (MTLCC).
- Takeaway of the paper's own comparison: Transformer-based methods (UTAE, TSViT) beat the LSTM-based ones; SITSMamba beats all three metric columns on both datasets (**Sec. IV-E, p.7–8**). SITSMamba is best on 9 of 17 MTLCC classes (**Table VI, p.8**); hardest PASTIS classes are 6, 10, 12, 18 (**Sec. IV-E, p.7**, Table V, p.8).

### 5. Code availability (repo checked 2026-10-04)
- **Contents:** `Model/SITSMamba.py` (model code), `Main_SITSMamba.py` (main/training script), `Pics/` (incl. `Architecture.jpg`), `README.md`. **No license file**, **no pretrained weights/checkpoints**, no config files, no dataloaders (README delegates PASTIS/MTLCC loading to the `pastis-benchmark` and `MTLCC-pytorch` repos, incl. `eval.tileids`).
- **Provenance (README credits):** ConvBlock adapted from **UTAE** (utae-paps); Mamba block from **state-spaces/mamba**. Environment: conda env `mamba`, Python 3.8, PyTorch 2.2.1, prebuilt `mamba_ssm` 1.2.2 wheel (Linux x86_64, cu122/torch2.2) — Linux/GPU-only as documented.
- **Released code ≠ paper description:** the file defines class `UMamba` with a U-shaped multi-stage spatial encoder (`encoder_widths=[64,64,64,128]`, `decoder_widths=[32,32,64,128]`, `out_conv=[32,20]`), `Mamba(d_model=128, d_state=32, d_conv=4, expand=2)`, and reconstruction `nn.Linear(decoder_widths[0]=32 → input_dim)` — whereas the paper describes a flat 2-layer ConvBlock with 128 filters and an RBranch Linear from C1=128 (**Sec. III-F, p.5**). The fetched file's forward pass also references `self.down_blocks`, which appears not to be defined in `__init__` — treat the released model file as possibly incomplete; verify it runs before building on it.
- Loss code (Eqs. 5–7): NOT FOUND in the fetched snippets — loss implementation is presumably in `Main_SITSMamba.py`, not inspected.

### Repo-claim verification
- Literature-Matrix row for this paper claims **"CNN + Mamba SSL"**.
  - **CNN + Mamba: accurate** — ConvBlock spatial encoder + Mamba temporal encoder (Sec. III-A, p.3).
  - **"SSL": inaccurate as a training-scheme label.** Training is single-stage supervised multi-task learning with crop labels; the reconstruction branch is an auxiliary loss. The paper itself positions SITSMamba *against* the SSL two-step (pretrain-then-finetune) paradigm (Sec. I, p.2; Sec. II-A-1, p.3). Accurate label: **supervised multi-task learning with a self-supervised-style auxiliary reconstruction loss** (the SITS itself is the extra supervision signal, but no pretext/pretraining stage exists).
  - Related correction: this note previously claimed a "contrastive loss between branches" — **NOT FOUND** anywhere in the paper; the only branch coupling is the weighted-sum loss of Eq. 7. Fixed in the tables above.

### Thermal-channel insertion point
- **Paper-level stem:** the first Conv2D of the ConvBlock consumes C channels of I ∈ R^{T×C×H×W} (**Sec. III-F, p.5**), C = 10 (PASTIS32) / 13 (MTLCC). Adding an LST band ⇒ stack it as channel C+1 (C→11/14); both the stem conv and the RBranch target (Linear C1→C, Sec. III-D) are dimensioned by C, so RBranch would automatically also reconstruct the LST band unless it is masked out of the reconstruction target.
- **Released code:** a single knob — `input_dim` in `UMamba.__init__` (`Model/SITSMamba.py`). The stem conv list starts with `input_dim` and `rec_linear = nn.Linear(32, input_dim)`, both derived from it, so `input_dim = 11` (S2 10 bands + LST) or `14` (MTLCC) needs no other model-code change.
- **What does NOT change:** the Mamba block's d_model is set by the encoder width (128 in both paper and code), not by band count, and there is no spatial Mamba scan (Sec. V-B, p.10–11) — the temporal encoder is untouched by adding a band.
- **Caution — loss balance:** PW-weighted MSE (Eq. 5) treats all channels/timesteps uniformly; the paper says nothing about per-channel loss weights or normalization for heterogeneous inputs (NOT FOUND). LST (Kelvin-scale) vs reflectance will dominate L_p unless independently normalized.
- **Caution — pipeline:** the repo has no dataloader, so band stacking for LST happens in your dataset pipeline (pastis-benchmark/MTLCC-pytorch side), and the released model file should be run once first (possible `down_blocks` incompleteness, see Code availability).

---

*Linked from: [[Literature-Matrix]]*
