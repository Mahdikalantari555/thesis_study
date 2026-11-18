# When Does Self-Supervised Learning Transfer to Time-Series Tasks?

## Full citation
Major, N., Razmadze, K., & Shavit, Y. (2026). *When Does Self-Supervised Learning Transfer to Time-Series Tasks?* arXiv:2605.19462v2 [cs.LG] (preprint, Bar-Ilan University). https://arxiv.org/abs/2605.19462

## Problem & setting
- Controlled benchmark answering: when do time-series SSL pretraining gains actually materialize, decoupled from architecture/data confounds? Seven representative SSL methods across 5 paradigms (reconstruction MAE; generative NTP + Diffusion; invariance DINO; contrastive SoftCLT; JEPA + LeJEPA) on a **shared channel-independent patched Transformer encoder** (8 layers, d=128, 16 heads, context 336, patch 16, 20 pretraining epochs), evaluated on anomaly detection (SMD, PSM, MSL, SMAP, SWaT), classification (9 UEA datasets), forecasting (ETT×4, Weather, Electricity, Traffic; horizons 96–720).
- Pretraining data: Monash archive (~680K series), scale-matched synthetic (TimePFN), scaled synthetic (2.5M), hybrid; plus in-domain pretraining controls for forecasting.
- Three protocols: linear probing, MLP probing, full fine-tuning — each paired with **matched random controls** (frozen random encoder for probing; supervised-from-scratch for fine-tuning); "SSL transfer gain" Δ defined formally; 5 seeds.

## Method (benchmark protocol details)
- MAE: 40% random patch masking, MSE on masked patches. NTP: 21 context / 6 target patches, causal. Diffusion (TimeDART-style): denoise Gaussian-corrupted patches conditioned on clean causal context. DINO: 1-D multi-crop augmentations, EMA teacher, centering + temperature sharpening. SoftCLT: hard instance InfoNCE + soft temporal contrast with distance-weighted pairs, TS2Vec-style overlapping-crop views. JEPA: multi-block masking (2×25%), EMA teacher, VICReg variance/covariance penalties. LeJEPA: no EMA teacher, SIGReg (sketched isotropic Gaussian) regularization; new DWT-based augmentation protocol introduced to prevent collapse.
- Anomaly metrics deliberately tripled: point-adjusted F1 (F1Pa), event-wise F1 (F1Ev), affiliation F1 (F1Af) — because rankings are metric-dependent.

## Data & labels
- Pretraining label-free (Monash/synthetic); downstream tasks use their standard supervised labels; controls isolate SSL-specific gains.

## Results
- **Anomaly detection = clearest SSL win:** SSL beats random frozen features in 54–94% of linear-probe configs (F1Ev 94%, F1Pa 54%), up to 97% under MLP probing; JEPA/LeJEPA improve MSL/SMAP F1Pa by >250% relative. Exception: on SWaT every SSL method underperforms random features.
- **Classification = moderate/selective:** linear-probe win rate 46% (MLP 40%); fine-tuning raises SSL win rate to 67% — pretraining is a good initialization but not always better than scratch. Gains concentrated in handwriting/digit/gesture; negative on EthanolConcentration, JapaneseVowels. LeJEPA best under linear probing (5/9 datasets) but only 2/9 after fine-tuning.
- **Forecasting = little to negative transfer:** SSL beats random frozen encoder in only 18% of MSE configs (linear probing), 31% MLP; fine-tuning from scratch beats pretrained backbones in >90% of runs. LeJEPA catastrophically degrades forecasting (−101%). In-domain pretraining beats Monash/synthetic for forecasting (34–42 wins vs 7–14 losses).
- **No universal method:** semantic/discrete tasks favor latent-space invariance objectives (LeJEPA), continuous-trajectory tasks favor signal-space objectives (Diffusion leads ETTh2; NTP leads ETTm1/SMD).
- **Linear probing ≠ fine-tuning outcomes:** rankings flip across protocols (Diffusion loses linearly but lowest MSE on ~90% datasets with MLP head; LeJEPA's probe lead disappears).
- **Scaling findings:** doubling pretraining 20→40 epochs ≈ no change (ties within seed variance); deeper encoders degrade forecasting (2-layer beats 8-layer in 14/21 pairs; 24-layer beats 8-layer in only 3/21) — vision/NLP scaling laws do not transfer to time-series SSL at these scales. Scale-matched synthetic pretraining is competitive with real Monash data (for classification, synthetic even wins 34/29); adding synthetic to real data hurts forecasting.

## What transfers to our thesis
- **Direct empirical support for the thesis's central bet:** SSL pretraining transfers reliably to *anomaly detection* (up to 94–97% win rate vs controls) — our label-free sugarcane stress detection is exactly an anomaly-detection-style downstream task, whereas forecasting (e.g., yield or NDVI forecasting) shows near-zero SSL benefit. This is a citable, controlled justification for framing our pipeline as SSL-encoder → anomaly/stress head rather than SSL → forecasting.
- **Methodological checklist to adopt:** (1) always include matched random-encoder and from-scratch controls; (2) report SSL transfer gain Δ; (3) never trust linear probing alone — evaluate MLP probing and fine-tuning (rankings flip); (4) report multiple anomaly metrics (F1Pa can mask poor event localization; use event-wise and affiliation F1) — directly relevant to how we report sugarcane stress-event detection.
- **Anti-scaling evidence:** deeper encoders and longer pretraining did not help time-series SSL; 2–4-layer backbones suffice — supports our lightweight multi-product model claim and warns against over-parameterizing the Landsat time-series encoder.
- **Domain-aligned pretraining > corpus scale:** in-domain data beat the large generic Monash corpus for forecasting; scale-matched synthetic matched real data. For us: pretraining on sugarcane-region Landsat history (in-domain) is expected to beat generic EO corpora — consistent with the STS-Net result (19.2K-param agri-specific CAE beating Presto).
- Caution: gains are dataset-dependent (SWaT negative) — our evaluation should include negative-control datasets/years to prove genuine transfer.
- The DWT-based augmentation (invariance to high-frequency sensor noise while preserving temporal morphology) is an immediately reusable augmentation design for cloud/noise-corrupted Landsat series.

## Limitations / caveats
- Generic time-series benchmarks (ETT, UEA, MSL/SMAP...), not remote sensing or vegetation series; Landsat-specific properties (seasonality, cloud gaps, spatial context) untested.
- Single backbone family (Transformer encoder); authors note state-space/conv models may scale differently.
- Dataset scales are modest (680K–2.5M series); they concede larger multi-domain corpora might change conclusions.
- Point-adjusted F1 known to be a flawed metric (they cite the critique) — their multi-metric protocol is the remedy.
- Preprint; single-seed depth sweeps.

## Key numbers to quote in lit review
- SSL pretraining beats matched random controls in up to 94% (linear) / 97% (MLP) of anomaly-detection configs, but only 18% of forecasting MSE configs — SSL transfer is task-dependent.
- Fine-tuning from scratch beats pretrained encoders in >90% of forecasting runs, but SSL wins 67% of classification fine-tuning configs.
- Encoder depth hurts: 2-layer > 8-layer in 14/21 forecasting pairs; 24-layer beats 8-layer in only 3/21.
- Doubling pretraining epochs (20→40) yields only ties within seed variance.
- Point-adjusted F1 vs event-wise vs affiliation F1 produce different method rankings — anomaly-detection evaluation must be multi-metric.
