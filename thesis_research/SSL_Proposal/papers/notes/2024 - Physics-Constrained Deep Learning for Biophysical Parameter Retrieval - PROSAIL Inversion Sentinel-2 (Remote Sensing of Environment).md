# Physics-constrained deep learning for biophysical parameter retrieval from Sentinel-2 images: Inversion of the PROSAIL model

## Full citation
Zérah, Y., Valero, S., Inglada, J. (2024). Physics-constrained deep learning for biophysical parameter retrieval from Sentinel-2 images: Inversion of the PROSAIL model. *Remote Sensing of Environment*, 312, 114309. DOI: 10.1016/j.rse.2024.114309. CESBIO (CNES/CNRS/INRAE/IRD/UT3 Toulouse).

## Problem & setting
- Task: probabilistic inversion of the PROSAIL radiative transfer model (RTM) to retrieve ALL input biophysical variables simultaneously (LAI, Cab/chlorophyll, Cw, Cm, Cc, Cb, N, leaf angle, soil parameters) from single-date Sentinel-2 surface reflectance (10/20 m bands upsampled to 10 m) + 3 observation angles.
- Setting: 14 western-European S2 MGRS tiles (THEIA, MAJA-corrected), acquisitions 2016–2019, 512×512 px ROIs over croplands and forests split into 128×128 patches (14 train / 1 val / 1 test per ROI).
- Motivation: hybrid (simulation-trained) inverters such as SNAP's BVNET Biophysical Processor degrade when simulated distributions mismatch reality; simulation design (distributions, inter-variable correlations, RTM version) is fragile and case-dependent.

## Method
- PROSAIL-VAE: a VAE whose decoder is a **differentiable PROSAIL** implementation. The encoder maps S2 reflectance (+angles) to the parameters of truncated-Normal distributions over the 11 PROSAIL input variables (latents ARE the physical parameters, constrained to physical ranges by rescaling to [0,1] bounds).
- Training is fully self-supervised on real unlabeled S2 images: sampled latent parameters are pushed through differentiable PROSAIL, converted to S2 bands via sensor response functions, and reconstruction loss = spectral reflectance matching + β_KL × KL divergence against uniform priors over the physical ranges. Loss: L = L_rec + β_KL·L_KL (β_KL ∈ {0,1,2}).
- Gradient backpropagates through the physics decoder into the encoder only — no simulations, no labels needed; only variable value ranges (min/max bounds) are prior knowledge, not full distributions (β_KL=0 config needs even less).
- Encoders: residual backbone, 3 residual blocks (2 layers each), 32 units wide, ReLU; two variants — pixel-wise MLP and a CNN ("spatial") whose first layer is 3×3 conv (rest 1×1).
- Baselines: BVNET (SNAP, 66-weight 2-layer ANN trained on PROSAIL simulations, MSE) and MPSR (same encoder architecture trained supervised on 3×10^5 simulated samples with NLL of truncated Gaussians).

## Data & labels
- Unlabeled training data: S2 patches from 14 tiles, Jan 2016–Dec 2019, cloud coverage <3%.
- Labels used ONLY for evaluation: 211 LAI + 121 CCC in-situ measurements from FRM4Veg/BelSAR campaigns at 3 sites (Las Tiesas-Barrax crops Spain, 2018 & 2021; Wytham Woods deciduous forest UK; BelSAR).
- Uncertainty evaluated via MPIW (mean prediction interval width) and PICP (coverage) at 2σ.

## Results
- Overall in-situ RMSE: PROSAIL-VAE LAI = 1.16 vs SNAP = 1.24; CCC = 42.33 vs SNAP = 88.08 μg/cm² (halves CCC error). CCC better than SNAP on ALL sites (e.g. Barrax 2021: 20.51 vs 84.53).
- Simulation-trained BVNET accuracy depended strongly on (i) PROSPECT version, (ii) LAI distribution choice, (iii) co-distribution strategy; best simulation config was case-dependent — direct evidence that simulation design does not transfer.
- PROSAIL-VAE-NP (β_KL=0, no distributional prior, only ranges) already accurate; priors on ALL variables (PROSAIL-VAE-AV) HURT accuracy — mild, targeted priors (LAI only, β_KL=2) were best (Pix-B2-L).
- PICP ≈ 0.95 target met for LAI (0.95 overall) and CCC (0.94). Spatial CNN encoder gave no measurable benefit over pixel-wise MLP (3×3 first layer too small; no spatial loss term).
- PROSAIL-VAE predictions saturated at CCC 250 μg/cm² and CWC 0.17 cm where SNAP overestimated CCC; LAI time series over a maize parcel matched double-logistic phenology and in-situ values.

## What transfers to our thesis
- Template for **physics-in-the-decoder SSL**: replace PROSAIL with a crop-growth/energy-balance or RTM forward model for Landsat; the encoder can output stress-relevant latent variables (e.g. Cw, Cab, LAI → water status proxies) trained with ZERO labels on Landsat time series — directly relevant to sugarcane water stress where Cw/CWC relates to drought.
- Shows unlabeled real satellite imagery (not simulations) can train an inverter that beats an operational simulation-trained product — supports our label-free premise and our cross-year generalization argument (no simulated distribution to mismatch).
- "Mild priors only" lesson: constrain latents to physical ranges, apply KL on few well-known variables; overly strong priors degrade accuracy — relevant when we encode ETa/CWSI priors.
- Probabilistic outputs (TN latents, PICP/MPIP calibration) give uncertainty — useful for in-field decision support products.
- Landsat analog: their angle-aware input + band-response conversion is directly reusable for Landsat 8/9 SR + thermal channels if a differentiable forward model for LST is used.

## Limitations / caveats
- Single-date inversion (no temporal model); Sentinel-2 only (10–20 m VNIR/SWIR), no thermal band — water-stress retrieval via Cw is indirect.
- Spatial encoder showed no gain; architecture/scale small (32-wide residual nets) — scaling behavior unknown.
- PROSAIL cannot model non-agricultural/heterogeneous canopies well (their own motivation); epistemic RTM error remains.
- CCC/CWC validation limited (121 points); saturation at high CCC.
- Requires differentiable reimplementation of the physics model — engineering cost.

## Key numbers to quote in lit review
- PROSAIL-VAE trained purely on unlabeled S2 images reaches overall RMSE 1.16 (LAI) and 42.33 μg/cm² (CCC) vs SNAP's 1.24 and 88.08 — CCC error halved with zero in-situ labels.
- Only 211 LAI / 121 CCC in-situ samples used, exclusively for evaluation.
- Latents are truncated-Normal distributions over the 11 PROSAIL physical parameters; loss = spectral reconstruction + β_KL·KL to uniform priors (best: β_KL=2, LAI prior only).
- Training set: unlabeled S2 patches, 14 MGRS tiles, 2016–2019, THEIA/MAJA surface reflectance.
