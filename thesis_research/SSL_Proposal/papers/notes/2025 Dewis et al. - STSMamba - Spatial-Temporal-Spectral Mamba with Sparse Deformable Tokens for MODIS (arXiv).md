# STSMamba: Spatial-Temporal-Spectral Mamba with Sparse Deformable Token Sequence for Enhanced MODIS Time Series Classification

## Full citation
Dewis, Z.*, Xu, Z.*, Zhu, Y., Alkayid, M., Heffring, M., & Xu, L.L. (2025). "Spatial-Temporal-Spectral Mamba with Sparse Deformable Token Sequence for Enhanced MODIS Time Series Classification." arXiv:2508.02839v1 [eess.IV] (University of Calgary; NSERC-funded).

## Problem & setting
- Land-cover classification from MODIS MOD13Q1 time series (250 m, 16-day revisit, 23 timesteps/year, 6 bands: blue, red, NIR, MIR, NDVI, EVI) — same 16-day cadence as Landsat; challenges: high temporal dimensionality, mixed pixels, spatial-temporal-spectral coupling.
- Data: Saskatchewan 2010 (11 classes, 100 train/100 val/1000 test per class, 13x13 patches, homogeneous-pixel filtering with 5x5 filter); Alberta 2010 as unseen-province generalization test (10.6M pixels mapped); ground truth NRCan 30 m LCLU resampled to 250 m.

## Method
- **Temporal Grouped Stem (TGS)**: per-timestep 3x3 conv + BN + GELU (6 bands -> 18 features/timestep) to disentangle temporal-spectral coupling before sequencing.
- **Sparse Deformable Mamba Sequencing (SDMS)**: instead of feeding full rigid token sequences to a Mamba block, compute an attention matrix (learnable), take mean over rows, sort descending, keep top floor(lambda*T) tokens, run Mamba on the re-ordered sparse sequence, then scatter outputs back (residual connection) — sequence order is learnable ("deformable") and length sparse.
- **Three dedicated modules**: SDTM (temporal: 23 -> 6 tokens), SDSpeM (spectral: 18 -> 6 tokens), SDSpaM (spatial: HW -> 4 tokens, using arccos similarity to central pixel, sparsity ratio lambda=0.3). Reduces redundancy, correlation decay in long sequences, and compute.
- Training: batch 1024, 100 epochs, RTX A6000 Ada; supervised classification head.

## Data & labels
- Supervised; labels from NRCan map (only for training/eval). No SSL — but architecture directly applicable to SSL pretraining over 16-day multi-band cubes.

## Results
- Saskatchewan: STSMamba OA 97.59%, AA 96.01%, Kappa 96.76% — beats SSRN 96.28/96.51/93.91, ConvNeXt 95.64, ViT 95.26, SwinT 93.72, LSTM 92.51, MambaHSI 93.04. +3-8 pp over MambaHSI; +3.8/6.2/4.0 pp over SwinT.
- Alberta (spatial transfer, unseen province): STSMamba best again — outperforms MambaHSI by ~7.2 (OA), 12.4 (AA), 4.4 (Kappa) pp and SwinT by 7.0/8.4/21.1 pp; all methods drop vs in-domain as expected.
- Sparsity ablation: temporal sparsity ratio 0.3 best (preserves phenology while cutting redundancy); spectral sparsity better at 0.8 (spectral richness critical).
- Per-class: biggest gains on subtle classes — polar shrubland 93.73 (vs 84-92 baselines), cropland 97.96, wetland 98.12.

## What transfers to our thesis
- **Same temporal sampling as our target**: MOD13Q1 16-day/23-steps is structurally identical to Landsat 16-day composites (~23 scenes/year); the TGS per-timestep stem + separated temporal/spectral Mamba streams transfer directly to Landsat optical+LST stacks (treat LST as extra bands in the spectral stream).
- The **decoupling of spatial-temporal-spectral streams** is the paper's core insight: bands with opposite seasonality (NDVI summer peak vs red/NIR winter snow peak) get entangled in mixed sequences — for sugarcane, NDVI/NDWI (phenology) vs LST/CWSI (stress) seasonality similarly differ, so decoupled streams are preferable to a single mixed token stream.
- Sparse deformable sequencing (top-k attention-guided token selection) is a concrete mechanism for lightweight models: keep only the most informative timesteps (e.g., peak-season composites) — reduces compute for in-field deployment and mitigates correlation decay on multi-year series.
- Cross-province generalization protocol (train Saskatchewan -> test Alberta) mirrors our cross-year/cross-field evaluation design; sparse+deformable model showed the strongest transfer.
- Note: supervised only — our thesis would wrap this encoder in a masked-reconstruction or contrastive pretext.

## Limitations / caveats
- Supervised classification only (NRCan labels); no SSL pretext, no anomaly/stress task; no thermal band.
- 250 m MODIS (no Landsat 30 m test); ground truth resampled 30 m -> 250 m introduces label impurity despite filtering.
- Sparsity ratios hand-tuned; spatial module keeps only 4 tokens per patch — questionable for fine-grained within-field stress gradients; no code link stated; AA vs Kappa table consistency unclear.

## Key numbers to quote in lit review
- STSMamba: OA 97.59% / Kappa 96.76 on 23-step 16-day MODIS series, +3-8 pp over prior Mamba (MambaHSI) and +3.8 pp over Swin Transformer.
- Spatial generalization to an unseen province: best of 9 models (e.g., +7.0 pp OA over SwinT, +21.1 pp Kappa), showing disentangled SSM encoders transfer across regions.
- Optimal sparsity: temporal 0.3 (phenology preserved) vs spectral 0.8 (spectral richness matters) — guidance for timestep-subsampling in lightweight time-series models.
- Decoupled temporal/spectral/spatial Mamba streams outperform mixed long sequences when bands have opposing seasonal patterns.
