# GWSC-SegMamba: Gate Wavelet Spatial Convolution Enhanced State Space Model for Multi-Temporal Agricultural Land Segmentation

## Full citation
Hestrio, Y. F., Mantau, A. J., Jatmiko, W. (2025). GWSC-SegMamba: Gate Wavelet Spatial Convolution Enhanced State Space Model for Multi-Temporal Agricultural Land Segmentation. *IEEE Access*, 13, 133246–133274. DOI: 10.1109/ACCESS.2025.3593389. University of Indonesia + BRIN.

## Problem & setting
- Task: supervised multi-temporal agricultural land / crop segmentation with linear-complexity sequence modeling; targets spectrally analogous crops and minority classes.
- Datasets (all Sentinel-2 time series): Munich (8,610 patches; 17 crop classes; 2016–17), Lombardia (29,962 patches; 7 classes; 9 bands B2–B8,B11,B12 + MSA VI; 4 years 2016–2019, two test sets A and Y), PASTIS (2,433 patches of 128×128; 20 French crop classes; 10 S2 bands).

## Method
- GWSC-SegMamba: SegMamba (3D Mamba segmentation backbone) extended with two gating modules:
  - **GWC (Gate Wavelet Convolution)**: discrete wavelet transform multi-resolution decomposition — low-frequency = seasonal phenology, high-frequency = texture; intended to sharpen discrimination of spectrally similar crops.
  - **GSC (Gate Spatial Convolution)**: dual-path 3×3 conv (local) + 1×1 conv (global context) for field-boundary delineation.
- Complexity of additions is additive: O(HWD·(3C²+4CD+W+S)) vs base SegMamba O(HWD·(3C²+4CD)); SSM temporal scan keeps linear cost in sequence length, vs Swin-UNETR's window-quadratic term.
- Loss: Dice-Focal (α Dice overlap + β focal weighting γ for hard examples), compared against CE and Dice-CE; 200 epochs, cosine annealing, weight decay 1e-3; systematic search over optimizers (SGD/Adam/AdamW), batch sizes, LRs, depths, feature sizes; V100 GPUs; flip augmentation only.
- Extensive statistics: independent t-tests + bootstrap (n=1000), 95% CIs, Cohen's d.
- Fully supervised; no SSL component. The paper also contains a long theoretical section (information-theoretic theorems, PAC-Bayes bounds) — mostly decorative.

## Data & labels
- Standard public benchmarks with per-pixel crop labels; no labels avoided — purely supervised segmentation.

## Results
- Headline gains vs SegMamba: +7.65% mIoU (claimed), vs Swin-UNETR +4.43%; minority-class IoU +53.13% (winter triticale claimed).
- Per-dataset (measured): PASTIS — biggest benefit: OA ≈0.82 (+7.66% vs Swin-UNETR, p=0.002, Cohen's d=4.12), Kappa +9.08%, weighted precision +11.81%; mIoU gain +2.39% NOT significant (p=0.078). Munich — OA +1.79% (d=0.85), Kappa +2.24%, weighted F1 +1.79%; but mIoU significantly WORSE than Swin-UNETR (−5.02%, p=0.003). Lombardia — NO significant difference on any of 7 metrics; baseline SegMamba beat GWSC on per-class F1 (rice 0.34 vs FPN 0.62).
- Ablation: GWC positive on Munich (+2.42% OA) and PASTIS (+7.24% OA, +25.93% RAcc); GSC positive mainly on PASTIS; BOTH components negative or neutral on Lombardia. mIoU consistently lower than baseline SegMamba on Munich (0.790 baseline best) and PASTIS (0.423 baseline best) — the extra components trade per-class balance for overall accuracy.
- Failure modes: F1 = 0.00 for winter spelt (Munich), and for small grain cereals, spring barley, soy (PASTIS), where U-Net 3D still scored 0.47–0.79.
- Overhead: ~8–10% compute over base SegMamba; linear scaling retained.

## What transfers to our thesis
- The **wavelet (frequency) decomposition of temporal features** — low-frequency = phenology, high-frequency = intra-season events — is a transferable idea for sugarcane stress: water/salinity stress signatures may live in specific frequency bands of the NDVI/LST time series; a wavelet-gated module over Landsat time series could separate slow phenology from stress-induced anomalies.
- Linear-cost Mamba backbone for multi-year Landsat stacks (long T) is reinforced; ~8–10% overhead quantifies the cost of adding multi-resolution gating.
- The honest negative results are instructive: architecture add-ons are dataset-dependent, and boosting OA can silently degrade minority-class mIoU — for our rare stress events we should report per-class/IoU-style metrics, not just accuracy.
- Bootstrap + Cohen's d evaluation protocol is a good template for our cross-year comparisons.

## Limitations / caveats
- Supervised only; no SSL; no Landsat/thermal; Sentinel-2 5-day dense series.
- Gains inconsistent across datasets (none on Lombardia); several total class failures (F1=0); mIoU of the full model often WORSE than baselines — the abstract's headline numbers are cherry-picked relative to specific baselines.
- Heavy pseudo-theoretical section (PAC-Bayes, information theorems) adds no empirical value.
- No temporal-length ablation, no param count table for the models, no cross-year holdout within dataset.

## Key numbers to quote in lit review
- GWSC-SegMamba on PASTIS: OA +7.66% over Swin-UNETR (Cohen's d=4.12), Kappa +9.08%, weighted precision +11.81%; but mIoU gain insignificant (+2.39%, p=0.078).
- Component overhead only ~8–10% over base SegMamba with linear temporal complexity O(HWD·(3C²+4CD+W+S)).
- Claimed +53.13% IoU for hard minority class (winter triticale), yet the full model scores F1=0.00 on three other PASTIS classes — architecture gains are class-dependent.
- Wavelet gating premise: low-frequency components encode seasonal phenology, high-frequency encode texture/detail — separable for spectrally similar crops.
