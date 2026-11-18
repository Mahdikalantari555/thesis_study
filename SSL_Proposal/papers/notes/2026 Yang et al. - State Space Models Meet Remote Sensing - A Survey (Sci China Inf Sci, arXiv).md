# State Space Models Meet Remote Sensing: A Survey

## Full citation
Yang, Q., Liu, C., Xu, J., Shi, Z., & Zou, Z. (2026). *State Space Models Meet Remote Sensing: A Survey*. Science China Information Sciences (under review) / arXiv:2606.25329 [cs.CV] (Beihang University). Tracking repo: github.com/QinzheYang/Awesome-RS-State-Space-Model. Structured search of >300 RS-SSM works (Mar 2024–Dec 2025).

## Problem & setting
- Comprehensive survey of State Space Models (SSMs / Mamba) in remote sensing. Motivation: RS tasks demand dense prediction over large extents, multi-modal fusion (HSI/MSI/Pan/SAR/multi-temporal), and long-sequence temporal modeling — all cases where Transformer quadratic attention is costly and SSMs' linear complexity fits.

## Method (survey structure)
- **Background:** S4 (2022, HiPPO memory, linear-time sequence mixing) → Mamba/S6 (Dec 2023: input-dependent selective parameters + hardware-aware scan; ~5× faster inference than Transformers at matching accuracy) → Vision Mamba/VMamba (Jan 2024: SS2D 2-D selective scan).
- **Task taxonomy with benchmark tables:**
  - Classification (HSI): HSIMamba, SpectralMamba, 3DSS-Mamba, DualMamba, S2Mamba, GraphMamba — Houston2013: DualMamba OA 99.57/κ 99.51, 3DSS-Mamba 98.37; Indian Pines: S2Mamba OA 97.92 — multi-directional scanning mitigates inter-class confusion and works well on tiny/imbalanced classes (some classes ≤10 samples).
  - Segmentation (LoveDA): UNetMamba MIoU 53.35 (best in table) vs RS3Mamba 50.62, TransUNet 48.31 — multi-scale U-Net-style construction compensates SSM's lack of native multi-scale features.
  - Change detection (WHU/LEVIR/LEVIR+): M-CD F1 95.3 (WHU), CDMamba 93.76; ChangeMamba's three spatio-temporal modeling modes (sequential / cross / parallel token ordering) set the paradigm.
  - Detection, super-resolution (Fourier/wavelet-embedded SSMs: FMSR, IRSRMamba), denoising/dehazing (HSIDMamba 8-direction scan), pan-sharpening (Pan-Mamba channel-exchange + cross-modal scan), meteorological downscaling (MambaDS).
- **Architecture-design synthesis (the survey's core contribution):** 23 scanning strategies cataloged (bidirectional, cross, SS2D, zigzag, Hilbert curve, multi-directional local, shuffle, hierarchical, spatial-spectral continuous scan with 6 orderings, spectral-priority/cross/parallel, **time cross scan, spatio-temporal sequential/parallel modeling** — Fig. 3 (t)–(w) for temporal data); high-level frameworks (backbone-centric vs U-Net-based); hybrid designs (SSM+CNN for local detail, SSM+Transformer for global context, SSM+GNN); redundancy removal via self/cross-guided gating; frequency-domain integration.
- **Trade-off synthesis:** scanning strategies suit sequential data (HSI) and linear cost but are weak on local texture; structural hybrids recover local detail at higher compute; hybrids are now the dominant paradigm but partially erode SSM's efficiency advantage.

## Data & labels
- Survey; benchmarks are standard supervised RS datasets (Houston2013, Indian Pines, LoveDA, WHU, LEVIR-CD).

## Results (synthesis)
- Statistics (as of Dec 2025): classification is the most-published RS-SSM task (~1,469 citations), then segmentation (~1,042), change detection (~759), detection (~307), SR (~249), pan-sharpening (~186), denoising (~134).
- Key qualitative claims: multi-directional scans reduce causal bias of 1-D unfolding; SSM handles small/imbalanced classes well (Indian Pines); U-Net+SSM decoders (UNetMamba) are the strongest segmentation config; hybrid SSM-CNN is the mainstream recipe.

## What transfers to our thesis
- **Temporal scanning strategies (Fig. 3 t–w) are directly relevant:** time cross scan, spatio-temporal sequential and parallel modeling were designed for multi-temporal RS images — a Mamba-based encoder over our Landsat 16-day NDVI/NDRE/LST sequences with temporal-aware scan orders is a state-of-the-art-supported, linear-complexity alternative to transformers for the "lightweight" pillar (relevant given Major et al.'s finding that deep transformers don't help time-series SSL).
- The survey quantifies the SSM-vs-Transformer efficiency argument for wide-area/dense prediction — citable when justifying sequence-model choice for multi-year Landsat series (hundreds of time steps per field across years).
- Benchmark tables give concrete numbers for a "sequence models in RS" paragraph: e.g., UNetMamba 53.35 MIoU on LoveDA vs TransUNet 48.31; ChangeMamba/CDMamba spatio-temporal token ordering as precedent for our multi-year time-series ordering (chronological vs seasonal-cross vs parallel arrangements).
- Future-directions section maps to our constraints: (1) SSM-based RS foundation models (linear complexity for dense/wide-area tasks); (2) **efficient SSMs for edge devices** — distillation/pruning/quantization for SSMs is named as an open need, aligning with our in-field deployment; (3) noted limitation that LoRA/adapters do not yet support SSM fine-tuning — a practical caveat if we consider PEFT on SSM backbones.
- Honest limitations to echo in our own discussion: SSMs struggle with scale variation, fine-grained texture, and long-sequence stability — exactly the properties of 40-year Landsat series with sensor changes (L5→L9), so hybrid or bidirectional designs with explicit multi-scale handling are advised.

## Limitations / caveats
- Survey covers to Dec 2025; temporal SITS modeling remains a small fraction of the RS-SSM literature (mostly change detection, not long crop time series) — our application is comparatively unexplored, which is both an opportunity and a risk.
- Benchmark tables are compiled from original papers (not re-run) — heterogeneous protocols; comparisons indicative only.
- No agricultural crop-time-series SSM (e.g., sugarcane phenology) exists in the survey; nearest relatives are ChangeMamba and meteorological MambaDS.
- For the thesis: no evidence yet that SSM beats lightweight CNN/AE on crop stress tasks (cf. STS-Net's 19.2K-param 3D-CAE) — SSM should be an ablation, not an assumption.

## Key numbers to quote in lit review
- >300 RS-SSM papers since March 2024; classification (1,469 citations) and segmentation (1,042) dominate; 23 distinct scanning strategies cataloged, including 4 temporal modes (time-cross, spatio-temporal sequential/parallel).
- Mamba/S6: ~5× faster inference than Transformers at comparable accuracy, with linear sequence complexity — the efficiency argument for long Landsat series.
- UNetMamba 53.35 MIoU on LoveDA vs TransUNet 48.31 — SSM+U-Net hybrid is the strongest segmentation recipe.
- DualMamba 99.57% OA (Houston2013 HSI); SSMs show minimal performance drops on tiny, imbalanced classes (Indian Pines classes with ≤10 samples).
- Open gaps: SSM foundation models, SSM edge acceleration (distillation/pruning/quantization), and PEFT (LoRA) incompatibility with SSMs.
