# SAKG: Mitigating data constraints in crop mapping — self-supervised framework integrating adaptive clustering, graph convolution and global spatiotemporal attention

## Full citation
Xie, L., You, S., Liu, A., He, Y., Huang, C., Deng, J. (2025). Mitigating data constraints in crop mapping: A self-supervised framework integrating adaptive clustering, graph convolution and global spatiotemporal attention. *International Journal of Applied Earth Observation and Geoinformation*, 144, 104951. DOI: 10.1016/j.jag.2025.104951. Zhejiang University + Land Satellite RS Application Center (MNR, China). Code: github.com/LijianXie/SAKG-net.

## Problem & setting
- Task: SSL-pretrained crop mapping (corn / soybean / other) from Sentinel-2 time series, explicitly evaluated for cross-spatial, cross-temporal, and cross-spatiotemporal transfer.
- Study areas: USA Corn Belt (Grant+Stevens MN, Kossuth IA, Iroquois IL, Jay+Randolph IN) and China (Kedong, Heilongjiang; Si County, Anhui); S2 April–Oct 2019–2021; 10 S2 bands + NDVI + NDMI; 15-day median composites → 14 steps/year; cloud-masked, missing marked 0 (no interpolation); labels from CDL (30 m, resampled 10 m, >95% confidence pixels) and Li et al. China corn/soybean product.

## Method
- Two-branch SSL pretraining (Barlow-Twins-style):
  - Encoder branch: 4 conv layers (3×3, pool, ReLU) each followed by spatiotemporal self-attention (1×1 conv Q/K/V, scaled dot-product, dk=C/8).
  - **Adaptive clustering + graph convolution branch**: 3×3 conv embedding → adaptive K-means (cluster count Kb adapted per sample from feature variance: Kb∈[2, √n], penalty α(Kb−K̂b)², α=0.1; soft one-hot membership weighted features instead of hard labels) → 4 GCN layers (Kipf-Welling propagation) at multiple scales.
  - **Adaptive feature fusion**: Ffused = W1⊙Fc + W2⊙Fg, W1+W2=1, weights from softmax(1×1 conv on concatenated features).
- Pretraining loss (Loss1) = Barlow Twins cross-correlation: Σ(1−Cii)² + λΣΣ_{i≠j}Cij² — diagonal = invariance to augmentation; off-diagonal = band-feature redundancy reduction (explicitly framed as per-band decorrelation for spectral sensitivity).
- Augmentations simulate illumination/cloud/seasonal change (optical domain perturbations).
- Fine-tuning: same trunk + attention-decoder (4 upsampling layers with skip connections), cross-entropy Loss2. lr 0.001, batch 4, Adam, 100 epochs; 7:2:1 split.
- Baselines: SVM, RF, ViT, Swin-UNet, STCLN (SSL), AKG = same architecture WITHOUT pretraining.

## Data & labels
- Pretraining: unlabeled S2 time series patches (all pixels). Labels (CDL / Chinese product) used only for fine-tuning and evaluation.

## Results
- Same-year 2021 US test: SAKG best everywhere — OA 0.9203 (MN), 0.9381 (IA), 0.9184 (IL), 0.9012 (IN); Kappa up to 0.9010; beats STCLN by ~+1.4 OA (MN 0.9067→0.9203) and AKG by ~+0.9–1.8; ViT collapses (OA 0.74–0.81).
- Cross-temporal (2019→2020 same region): SAKG OA 0.8570 (MN) to 0.9015 (IA); best in all 4 states; >80% stable accuracy for every crop.
- Cross-spatial: IN→MN OA 0.8753/Kappa 0.8108; cross-country 2019MN→2019HLJ OA 0.7804 (Kappa 0.6657); HLJ→IL OA 0.7406.
- Cross spatiotemporal (2019→2020, different region): MN→IA OA 0.8338 (Kappa 0.7386); HLJ→MN OA 0.8592; hardest AH→IN OA 0.6860 (Kappa 0.5375) — still best of 7 models.
- Ablation (Iowa 2021): clustering-GCN branch adds +1.89% mF1; + adaptive fusion + self-attention gives +3.09% mIoU; full stack + SSL pretraining +3.79% mIoU over base.
- Label-efficiency: at 10% labels, SSL pretraining gives +1–3% OA and +2% mIoU vs no pretraining.
- t-SNE: post-model features align source and target domain distributions.

## What transfers to our thesis
- Closest architectural analogue to our plan (SSL pretraining + temporal-spatial encoder + cross-year/cross-region transfer on optical time series), with a rigorous three-way transfer protocol we should mirror (spatial / temporal / spatiotemporal) for sugarcane cross-year models.
- **Adaptive K-means → GCN** over clustered pixels: a cheap way to inject spatial structure at field/parcel scale with controlled compute; directly reusable over our field-level Landsat embeddings (cluster fields, propagate features via GCN).
- Bandwise decorrelation (off-diagonal Barlow loss) framed for spectral sensitivity — applicable to our 6–7 Landsat bands + LST with multispectral channels as embedding dims.
- 15-day compositing with 0-fill missing (no interpolation) — same cadence class as Landsat 16-day; shows SSL works with incomplete series.
- Label-efficiency evidence: pretraining helps most at ~10% labels — supports our claim that SSL relieves the label bottleneck for multi-product in-field models.

## Limitations / caveats
- SSL pretraining still followed by supervised fine-tuning (not end-label-free); only 3 classes (corn/soy/other); S2 10 m, no thermal/LST.
- Cross-country transfer degrades notably (AH→IN OA 0.686) — phenology/latitude mismatch; authors recommend similar-latitude transfer.
- GCN cost bounded only via clustering; "other" class heterogeneous; CDL-derived labels carry product noise.
- No stress/anomaly task; small batch (4); no comparison with masked-modeling SSL baselines (only STCLN contrastive).

## Key numbers to quote in lit review
- SSL pretraining (Barlow-style + clustering-GCN) lifts corn/soybean mapping OA to 0.90–0.94 across 4 US Corn Belt counties and wins all cross-spatial, cross-temporal and cross-spatiotemporal transfers.
- Cross spatiotemporal 2019→2020 different-region: OA 0.8338–0.8592 domestically, 0.686–0.786 cross-country (China↔USA).
- At 10% training labels, SSL pretraining adds +1–3% OA and +2% mIoU over training from scratch.
- Ablation: adaptive clustering-GCN +1.89% mF1; full framework +3.79% mIoU vs base encoder.
