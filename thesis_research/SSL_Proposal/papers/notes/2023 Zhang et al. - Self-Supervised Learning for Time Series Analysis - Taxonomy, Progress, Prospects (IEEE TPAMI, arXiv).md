# Self-Supervised Learning for Time Series Analysis: Taxonomy, Progress, and Prospects

## Full citation
Zhang, K., Wen, Q., Zhang, C., Cai, R., Jin, M., Liu, Y., Zhang, J.Y., Liang, Y., Pang, G., Song, D., & Pan, S. (2023/2024). "Self-Supervised Learning for Time Series Analysis: Taxonomy, Progress, and Prospects." IEEE TPAMI, arXiv:2306.10125v4. Companion repo: github.com/qingsongedu/Awesome-SSL4TS.

## Problem & setting
- First comprehensive survey of SSL specifically for (multivariate) time series; motivated by the fact that CV/NLP pretext tasks do not transfer trivially (time series have seasonality/trend/frequency structure; image-style augmentation such as rotation/crop breaks temporal dependency; information concentrated in few variables).
- Covers four downstream tasks: anomaly detection, forecasting, classification, clustering.

## Method (taxonomy — precisely)
**Three top-level families, ten subcategories:**
1. **Generative-based** (pretext = generate data):
   - *Autoregressive-based forecasting (ARF)*: predict x[t+1:t+K] from x[1:t], MSE loss (THOC multi-resolution dilated RNN TSS; GDN graph forecasting; STraTS triple-representation transformer for irregular series).
   - *Autoencoder-based reconstruction*: BAE, DAE (Gaussian noise / zeroing timesteps), **MAE (loss only on masked part)**, VAE (reconstruction + KL). Masking for time series classified into time-step-wise, segment-wise (STEP; captures slow features/trends, shortens encoder input), variable-wise (VSF; sensor-absence forecasting), and attention-guided (TARNet). VAE variants: InterFusion, OmniAnomaly (+Planar NF), GRELEN/VGCRN (graph), LaST (disentangled seasonal-trend with MI constraints).
   - *Diffusion-based generation*: CSDI (imputation), TimeGrad, D3VAE, ImDiffusion (anomaly detection), SSSD (structured state space + diffusion).
2. **Contrastive-based** (classified by how positives/negatives are built):
   - *Sampling contrast*: temporal-neighborhood assumption (USRL); TNC uses ADF stationarity test + PU-learning weighting of possible false negatives; NCL adds supervised signal.
   - *Prediction contrast*: CPC/InfoNCE — predict future latent to maximize mutual information between context and future ("slow features"); TS-CP2 and Skip-Step CPC use TCN; Skip-step distance choice changes anomaly detection results; TS-TCC/CA-TCC cross-view context prediction; CMLF multi-granularity.
   - *Augmentation contrast*: SimCLR-style NT-Xent (eq. 25) with time-series augmentations — jitter/scale/permutation (TS-TCC strong vs weak), masking (TS2Vec), frequency-domain (CoST FFT seasonal-trend disentanglement; BTSF time-freq bilinear fusion; TF-C frequency perturbations beating TS2Vec/TS-TCC); DTW-based TimeCLR; DCdetector dual-attention patch contrast for anomaly detection; multi-scale views (MTFCC, MRLF).
   - *Prototype contrast*: cluster-center/prototype-based contrast (PCL, SwAV; TS: ShapeNet shapelet triplet, TapNet, DVSL, MHCCL hierarchical with outlier masking) — avoids the uniformity bias of instance discrimination.
   - *Expert-knowledge contrast*: priors select positives/negatives (DTW-distance labels; ExpCLR continuous pair loss; SleepPriorCL).
3. **Adversarial-based**: GAN generation/imputation (TimeGAN, TTS-GAN, E2GAN, GRUI) and auxiliary representation enhancement L = L_base + L_adv (USAD two-AE adversarial reconstruction error amplification; AnomalyTrans prior-vs-series association KL; BeatGAN; L = L_mse + lambda1*L_cluster + lambda2*L_adv).

**Quantitative takeaways (Appendix I):**
- Anomaly detection (PSM/SMD/MSL/SMAP/SWaT, point-adjusted F1): best methods are contrastive + association-based — DCdetector (PSM F1 97.94, SMAP 97.02, SWaT 96.33), Skip-CPC (PSM 98.55), ImDiffusion (PSM 97.81, SMD 94.88), AnomalyTrans; key ingredients: global/local association modeling (anomalies associate weakly with the whole series) + adversarial regularization to amplify anomaly scores. USAD (SMD F1 93.82) remains a strong simple baseline.
- Forecasting: disentangled seasonal-trend SSL methods (LaST, CoST) dominate (e.g., LaST ETTh-24h MSE 0.324, CoST 0.386 vs CPC 0.728, TS2Vec 0.590).
- Classification/clustering: contrastive methods dominate; no single method wins across 30 UCR/UEA/HAR datasets — model choice must be data-dependent.
- Survey's stated correlation: generative SSL suits anomaly detection + forecasting; contrastive SSL suits classification + clustering.

## Data & labels
- Standard benchmarks tabulated: AD — PSM (26 dim, 27.8% anomaly), SMD (38 dim, 4.16%), MSL/SMAP (NASA), SWaT/WADI (water treatment); Forecasting — ETTh/ETTm, Electricity (321 dim), Weather, Traffic (862 dim); C&C — HAR, UCR-128, UEA-30. All SSL pretraining label-free; metrics: P/R/F1 (with point-adjustment for AD), MSE/MAE, accuracy.

## What transfers to our thesis
- Provides the taxonomy vocabulary for the thesis lit review: our Landsat field-time-series work can be framed as **generative (masked reconstruction/forecasting) + contrastive** hybrid; the survey's guidance that generative/forecasting objectives suit anomaly detection supports our "predict future 16-day NDVI/LST, flag unpredictability as stress" design.
- Key anomaly-detection design principle to cite: anomalies are hard to associate/predict from the rest of the series (association-discrepancy and unpredictability objectives outperform plain reconstruction on PSM/SMD/SWAT).
- Sampling-contrast pitfall directly relevant to crop phenology: neighboring timesteps of a sugarcane series are NOT always similar (seasonality); TNC's stationarity-tested neighborhoods and PU-weighted negatives show how to avoid false-negative contrastive pairs — analogous to not contrasting winter vs summer composites as "negatives".
- Seasonal-trend disentanglement (CoST/LaST) is attractive for stress detection: stress signal is a deviation from the normal seasonal component, so disentangled representations could separate phenology from stress.
- Future directions that justify thesis novelty: SSL for irregular/sparse series without interpolation (cloud gaps in Landsat), inductive bias/prior injection (physics of ETa), large pre-trained time-series models, benchmark evaluation.

## Limitations / caveats
- General-purpose time series (industrial/medical/traffic) — no remote sensing/agricultural case studies; all benchmarks are 1-D sensor series, not spatio-temporal image time series.
- Point-adjustment F1 protocol in many AD benchmarks is known to inflate scores; numbers not comparable to spatial (per-pixel) anomaly detection.
- Survey snapshot to early 2024; no coverage of Mamba/SSM backbones, foundation models for EO, or masked spectral-spatial modeling.

## Key numbers to quote in lit review
- Taxonomy: 3 families, 10 subcategories; contrastive split into sampling/prediction/augmentation/prototype/expert-knowledge; masking into time-step-, segment-, variable-wise.
- Best AD F1 on PSM: DCdetector 97.94%, Skip-CPC 98.55%, ImDiffusion 97.81% — all exploit "anomalies are poorly associated/predicted with the rest of the series".
- USAD's adversarial two-AE amplification reaches F1 93.82% on SMD with a simple reconstruction objective.
- Seasonal-trend disentanglement SSL (LaST) cuts ETTh-24h forecasting MSE from 0.590 (TS2Vec) to 0.324.
- No contrastive model wins across all 30 classification datasets — augmentation choice is task-dependent (jitter/scale/permutation/masking/frequency).
