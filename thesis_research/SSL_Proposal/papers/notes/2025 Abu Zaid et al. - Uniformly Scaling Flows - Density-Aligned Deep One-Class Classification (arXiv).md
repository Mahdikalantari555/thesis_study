# On Uniformly Scaling Flows: A Density-Aligned Approach to Deep One-Class Classification

## Full citation
Abu Zaid, F., Katzke, T., Müller, E., & Neider, D. (2025). "On Uniformly Scaling Flows: A Density-Aligned Approach to Deep One-Class Classification." arXiv:2510.09452v1 [cs.LG] (TU Dortmund, RC Trustworthy Data Science). Code basis: github.com/aai-institute/USFlows.

## Problem & setting
- Theory + practice for unsupervised anomaly detection: bridges Deep SVDD (one-class, compact hypersphere of normality, collapse-prone) and normalizing flows (exact likelihoods, but scores confounded by input-dependent log-Jacobian terms). Industrial AD benchmarks: MVTec AD and VisA (15 and 12 object classes), image-level and pixel-level AUC-ROC.

## Method
- **Uniformly Scaling Flow (USF)**: normalizing flow with constant Jacobian determinant, det J_phi(x) = kappa for all x. Built from masked **additive coupling layers** (volume preserving) + bijective affine transforms parameterized by LU-decomposed matrices (determinants cancel between adjoint blocks), via USFlows library; non-US counterpart differs only by affine coupling.
- **Core theorem**: training a USF by MLE with base N(c, 1/2 I) reduces exactly to a Deep SVDD one-class objective min E||phi(x)-c||^2 with a unique weight regularizer -ln psi_det(w) that penalizes volume collapse — inheriting both flow density faithfulness and one-class distance reasoning. Consequence: latent norm ||phi(x)-c|| is a provably faithful anomaly score (density monotonicity, p_X(x)<p_X(y) iff ||phi(x)||>||phi(y)||), which non-US flows and Deep SVDD violate (Proposition 1 shows Deep SVDD admits density-inverting minimizers).
- **Determinant regularization**: Bayesian log-normal prior on |det J| (per LU diagonal) prevents exploding determinants; MAP estimation.
- **VAE-USFlow hybrid**: USF as learnable VAE prior (latent z ~ phi^-1(N(0,I))) for explicit dimensionality reduction, combined with reconstruction score; Wide-ResNet50 encoder, transposed-conv decoder.
- **Drop-in experiments**: replace affine coupling with additive coupling inside FastFlow (ResNet-18 features), CFlow (Wide ResNet-50-2 + positional conditioning), U-Flow (MS-CaiT multi-scale); Anomalib v2.0, ImageNet-frozen backbones, 100 epochs, 3 seeds, no per-class tuning.

## Data & labels
- Unsupervised: trained only on normal samples (MVTec/VisA train splits); labels used only for AUC-ROC evaluation.

## Results
- Drop-in USF substitution: never hurts means, greatly reduces variance (often to ~±0.0-1.1). MVTec AD image AUC: CFlow 72.5±12.8 -> 90.8±1.1 (+18.3, near-eliminates training failures); U-Flow 92.7±4.6 -> 94.5±0.6; FastFlow 91.3 -> 91.0 (unchanged, more stable). MVTec pixel: 95.4-95.9 -> 96.6-97.0. VisA image: CFlow 82.5±8.3 -> 88.4±0.9; pixel FastFlow 96.3±0.7 -> 98.8±0.0.
- Toy experiments (Gaussian mixtures, d=2..128): only USFs keep monotonic likelihood-vs-latent-norm alignment up to 128 dims (Spearman rho/Kendall tau); non-US flows collapse at 128 dims with numerical instability; Deep SVDD latents inhomogeneous.
- VAE-USFlow proof of concept on MVTec: mean image AUC 81.54 (median 82.52, 0 failed runs) vs VAE-NonUSFlow 58.11 (53.68, 11 failed runs of 45).

## What transfers to our thesis
- Provides a principled **density-based anomaly detection option for label-free crop stress detection**: a flow (or USF) fitted on normal field embeddings (e.g., from an SSL encoder over Landsat 16-day series) yields exact likelihood-based stress scores with the theoretical guarantee that the latent norm alone ranks anomalies — simpler scoring than reconstruction error and immune to hypersphere collapse.
- The collapse analysis justifies design choices in our one-class baselines: Deep SVDD needs fixed non-zero center, no biases, unbounded activations, and benefits from USF-style regularization; latent-norm scoring is valid only for uniform-Jacobian transforms — a concrete recommendation if we try flow heads on top of Presto/SSL embeddings.
- Strong empirical message: **variance/stability gains** from USF substitution (std 12.8 -> 1.1) matter for cross-year deployment where retraining per year is required — a stable detector is more important than +1 AUC when models must transfer across seasons/regions without re-tuning thresholds.
- CFlow's positional conditioning idea (condition density on spatial index) is adaptable: condition on day-of-year/phenology stage so "normal density" is season-aware — relevant for 16-day seasonal stress baselines.

## Limitations / caveats
- Industrial images (MVTec/VisA) only — no remote sensing, no time series, no multispectral data; normal-only training assumed (agricultural archives contain anomalies).
- Flows are more expensive than plain encoders; hybrid VAE-USFlow still far from specialized detectors (81.5 vs ~99 AUC for FastFlow/CFlow+USF).
- USF requires equal input/latent dimensionality (diffeomorphism), so dimensionality reduction needs the VAE hybrid, which is the weakest variant.

## Key numbers to quote in lit review
- MLE training of a uniformly scaling flow is mathematically equivalent to Deep SVDD with a determinant regularizer — unifying one-class classification and density estimation.
- Drop-in USF substitution: CFlow MVTec image AUC 72.5±12.8 -> 90.8±1.1; VisA pixel FastFlow 96.3±0.7 -> 98.8±0.0; means never regress and variance collapses across 12 configurations.
- Only USFs preserve monotonic likelihood-latent-norm alignment up to 128 dimensions; non-US flows numerically fail there.
- VAE-USFlow 81.5 mean AUC with 0/45 failed runs vs 58.1 with 11 failed runs for the non-USF prior.
