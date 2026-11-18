# 01 — SSL Foundations

**Scope:** methodological families of self-supervised learning (SSL), their objectives, assumptions, strengths, limitations, and computational requirements — with emphasis on the properties that matter for satellite image time series (SITS) and anomaly detection.
**Search date:** 2026-10-24. **Evidence levels:** [FT] = full text inspected; [ABS] = abstract/metadata verified; [MO] = metadata only.

---

## 1. What SSL is and what it buys

SSL defines a *pretext task* from the data itself — "occlude or perturb part of the data and task the network with predicting it from the visible data" (SeCo, [FT] p.2) — so that the learned representation can transfer to downstream tasks with few or no labels. The canonical benefit is label efficiency: SSL4EO-S12 showed fine-tuning with 10% labels outperforming 50%-label supervised training, and (ViT-S/16) 50% labels beating 100%-label supervised training [FT, p.4–5]. The canonical cost is that pretext objectives encode *specific invariances* that may or may not match the downstream task: SeCo explicitly warns that seasonal invariance "can be beneficial for certain downstream tasks … but harmful for downstream tasks where seasonal variations are important (e.g. deforestation tracking, change detection)" [FT, p.2].

## 2. Family A — Contrastive learning (negative pairs)

**Objective.** Pull together representations of "positive" views of the same instance; push apart "negative" pairs from other instances, typically via the InfoNCE loss (SeCo [FT] Eq. 1).

- **SimCLR** (Chen et al., 2020, ICML; arXiv:2002.05709) [MO, canonical]: two augmented views, NT-Xent loss; requires very large batch sizes; introduced the projection head + strong-augmentation recipe.
- **MoCo** (He et al., 2020, CVPR; arXiv:1911.05722) [MO, canonical]: momentum encoder + negative queue, decouples negative-pair count from batch size; MoCo-v2 (arXiv:2003.04297) is the variant most RS works build on (SeCo, SSL4EO-S12 both use it [FT]).
- **SwAV** (Caron et al., 2020, NeurIPS; arXiv:2006.09882) [MO, verified via arXiv title search]: swaps cluster-assignment predictions between views instead of pairwise contrast.
- **DeCUR** (Wang, Albrecht, Ait Ali Braham, Liu, Xiong, Zhu; ECCV 2024; DOI 10.1007/978-3-031-73397-0_17; arXiv:2309.05300) [ABS via OpenAlex, 49 citations]: decouples *common* (cross-modal) and *unique* (modality-specific) representations for multimodal SSL — designed for Sentinel-1/2.

**Assumptions/strengths.** Instance-discrimination assumption (each instance is its own class); contrastive features are discriminative and transfer well under **linear probing** — SSL4EO-S12 found contrastive methods (MoCo, DINO) consistently beat masking-based methods (MAE, data2vec) under linear probing across EuroSAT/BigEarthNet/So2Sat [FT, Tables III–IV].

**Limitations.** (i) Contrastive objectives make representations *sensitive to how positives are built* — "contrastive approaches … make the representations they learn sensitive to how positive pairs are built" (CROMA [FT], p.2, citing Park et al.); (ii) negatives require large batches/queues; (iii) invariance choices encode task priors (see SeCo warning above).

## 3. Family B — Self-distillation / non-contrastive joint embedding

**Objective.** Match representations of two views **without negative pairs**, avoiding collapse via architectural asymmetry or statistics.

- **BYOL** (Grill et al., 2020, NeurIPS; arXiv:2006.07733) [ABS, OpenAlex, 3,845 citations]: online network predicts target network's representation; target = slow-moving average of online. Reported 74.3% top-1 linear-probe ImageNet (ResNet-50).
- **SimSiam** (Chen & He, 2021, CVPR; arXiv:2011.10566) [MO, verified via arXiv]: collapse prevention via stop-gradient alone.
- **Barlow Twins** (Zbontar et al., 2021, ICML; arXiv:2103.03230) [MO, verified via arXiv]: drive the cross-correlation matrix between two views' embeddings toward the identity — redundancy reduction without negatives. (The initially recommended candidate for this thesis, per `00_SSL_questionnaire.md` Q3.)
- **VICReg** (Bardes et al., 2022, ICLR; arXiv:2105.04906) [MO, verified via arXiv]: explicit variance–invariance–covariance regularization.
- **DINO** (Caron et al., 2021, ICCV; arXiv:2104.14294) [MO, verified via arXiv]: self-distillation with a student–teacher ViT; emergent attention-based segmentation; used as a benchmark SSL family in SSL4EO-S12 and Galileo [FT].
- **data2vec** (Baevski et al., 2022; arXiv:2202.03555) [MO]: unified masking+distillation-style teacher targets; benchmarked in SSL4EO-S12 [FT].

**Strengths.** No negatives → no huge batches; strong transfer; DINO-family features are clustered and interpretable (SSL4EO-S12 t-SNE shows SSL features well-clustered without labels [FT, Fig. 5]).
**Limitations.** Collapse risk is structural (EMA/stop-gradient dynamics are delicate — Galileo reports its PatchDisc contrastive variant "remains prone to collapse" [FT, p.8]); invariance still dictated by augmentation choice — directly relevant to the thesis, since Paul et al. 2025 report color jitter degrading stress-relevant information [FT, corpus #60].

## 4. Family C — Masked image modeling / generative reconstruction

**Objective.** Mask part of the input; reconstruct it (or a representation of it) from the rest.

- **MAE** (He et al., 2022, CVPR; arXiv:2111.06377) [MO, canonical; full mechanism verified via SatMAE's description [FT]]: mask 75% of patches; asymmetric encoder (visible only) + lightweight decoder; MSE on masked pixels. Galileo's summary: reconstruction models "learn to capture as much information as possible [and] do not rely on multiple views and scale incredibly well, but learn representations that require significant finetuning to be useful" [FT, p.2].
- **BEiT** (Bao et al., 2022, ICLR; arXiv:2106.08254) [MO, verified via arXiv]: predicts discrete visual tokens (dVAE) — BERT-for-images.
- **SimMIM** (Xie et al., 2022, CVPR; arXiv:2111.09886) [MO, verified via arXiv]: simple pixel regression with direct masking on hierarchical backbones.
- **SITS instantiations:** SITS-Former (missing-patch imputation; Yuan et al., JAG 2022, DOI 10.1016/j.jag.2021.102651) [ABS, 85 citations]; SatMAE (temporal groups + spectral groups) [FT]; Sadbhave et al. 3D-convolutional autoencoder for sugar-beet stress [FT local PDF].

**Strengths.** Scales; no augmentation engineering; **anomaly-score-native** — reconstruction error on abnormal inputs is high, which is exactly the signal used by agricultural masked-modeling AD (Label-free MIM aerial AD [FT]; temporal inpainting AD [FT]).
**Limitations.** Representation quality under frozen evaluation is weaker than contrastive/distillation methods (SSL4EO-S12: masking-based methods lag under linear probing [FT]); features may retain nuisance detail (clouds, illumination) unless the target space is chosen carefully — T-JEPA argues pixel-space targets are "ill-suited to EO sequences" because acquisition-specific factors "introduce substantial uncertainty and instability into pixel-level supervision" [FT, p.2].

## 5. Family D — Predictive / latent-space (JEPA) self-supervision

**Objective.** Predict the *representation* of a target view from a source view, in latent space, instead of pixels.

- **I-JEPA** (Assran et al., 2023; referenced as SoTA framework in CROMA comparisons [FT]) [MO]; **V-JEPA** (Bardes et al., 2024) [MO, via T-JEPA].
- **T-JEPA** (Peng, Liu, Liu, Li, Zhou; NUDT; arXiv:2610.05731, Oct 2026) [FT]: treats the **actual elapsed time between acquisitions as supervision** — a temporal predictor estimates the complete target latent field from a masked source latent + time-gap embedding (AdaLN conditioning); asymmetric metadata injection (online encoder sees metadata with dropout p=0.5, EMA target encoder is metadata-free) to prevent shortcut learning; direct all-pair transition supervision beats recursive rollout; complemented by a masked-reconstruction branch. Under matched pretraining (CACo corpus, 200K Sentinel-2 locations), T-JEPA beat 9 baselines incl. Prithvi-EO-2.0-TL and SatMAE: BigEarthNet-1% linear mAP 66.0 (Prithvi 62.4), PASTIS T=8 classification mAP 50.7, DFC20 mIoU 39.4, OSCD F1 60.3 [FT, Table 1]. Time-conditioned probe: Target R@1 87.5% vs SatMAE 68.75% [FT, Table 3].
- **Galileo** (Tseng, Fuller, Reil, Herzog, Beukema, Bastani, Green, Shelhamer, Kerner, Rolnick; ICML 2025 PMLR 267; arXiv:2502.09356) [FT]: dual global/local masked modeling — global = deep targets + structured space-time masking; local = shallow linear-projection targets + unstructured masking; within-sample token contrastive (PatchDisc^B). Nine modalities incl. Sentinel-1/2, SRTM, ERA5, TerraClimate, nightlights; 127,155 globally sampled instances; outperforms SatMAE/CROMA/Presto across 11 benchmarks [FT].

**Strengths.** Latent prediction filters acquisition-specific nuisance (clouds, illumination) — the most principled answer to cloud contamination; time-gap conditioning is a natural fit for irregular satellite cadence.
**Limitations.** Newer and less battle-tested; T-JEPA's own overhead analysis: +220.9% forward FLOPs vs MAE (72.4% from the EMA target forward), though wall-clock +20% [FT, supp.]; requires careful design to avoid metadata shortcuts.

## 6. Multimodal / cross-modal self-supervision

**CLIP** (Radford et al., 2021, ICML; arXiv:2103.00020) [MO, verified via arXiv]: image–text contrastive alignment — the archetypal cross-modal objective.
**RS multimodal:** CROMA (radar↔optical InfoNCE + multimodal MAE; "these objectives are complementary when leveraged on spatially aligned multimodal data" [FT, abstract]; ablation: removing either objective degrades accuracy, MAE-only −7.5 avg mAP/mIoU, contrast-only −3.2 [FT, Table 6]); DeCUR (common/unique decomposition) [ABS]; SSL4EO-S12 multimodal pretraining (early fusion + RandomSensorDrop) improved BigEarthNet-1% by 1–3% [FT, Table VIII]; DOFA ("Neural Plasticity-Inspired Multimodal Foundation Model for Earth Observation," arXiv:2403.15356) [MO, verified via arXiv]; MMEarth (multi-modal pretext tasks; arXiv:2405.02771) [MO, verified via arXiv]; Galileo (nine modalities; removing TerraClimate or VIIRS from pretraining hurt downstream most in its ablation [FT, Table 11]).

**Evidence for the thesis:** fusing auxiliary modalities (SAR, weather, elevation) measurably improves representations; Galileo's ablation is the cleanest demonstration that *domain-relevant auxiliary modalities pay off* — direct support for including LST/weather alongside optical bands in pretraining.

## 7. SSL for time series (the abstract bridge to SITS)

**Zhang et al., "Self-Supervised Learning for Time Series Analysis: Taxonomy, Progress, and Prospects" (TPAMI; arXiv:2306.10125) [FT, local PDF]:** taxonomy of **generative-based, contrastive-based, adversarial-based** methods, with 10 subcategories; notes the pretrain-then-finetune strategy "even a small amount of labeled data can achieve high performance."
**Representative TS-SSL methods:** TS2Vec (Yue et al., AAAI 2022; arXiv:2106.10466) [MO, verified via arXiv]; TS-TCC (Eldele et al., ICML 2021; arXiv:2106.14112) [MO, verified via arXiv — ID corrected from 2106.14111]; SimMTM (masked trajectory modeling; arXiv:2302.00861) [MO, verified via arXiv].
**Transfer conditions:** Major, Razmadze & Shavit (Bar-Ilan), "When Does Self-Supervised Learning Transfer to Time-Series Tasks?" (arXiv:2605.19462) [FT, local PDF]: benchmarking 7 SSL methods across 5 paradigms under matched budgets — **SSL yields substantial gains in anomaly detection; effective initializations for classification under fine-tuning; limited to no advantage over non-pretrained controls in forecasting.** Linear probing does not reliably predict fine-tuning performance; synthetic pretraining is often competitive with real-world corpora; scaling encoder depth degrades forecasting.

## 8. SSL for anomaly detection (the thesis's target task family)

**Ruff et al., "A Unifying Review of Deep and Shallow Anomaly Detection" (Proc. IEEE 109(5), 2021; accepted Jan 7, 2021) [FT, local PDF]:** connects classical (density, one-class, reconstruction) and deep AD; defines anomaly scores as reconstruction error, latent distance, density. Key design prior: classical methods assume a *clean* normal training set; deep methods degrade under contamination — the thesis's 490-field archive will be contaminated by stressed fields.
**DeepSVDD** (Ruff et al., ICML 2018, PMLR) [MO, canonical]: one-class deep objective minimizing hypersphere volume.
**Synthetic-anomaly self-supervision — AnomalyBERT** (Jeong, Yang, Ryu, Park, Kang; Seoul National University; ICLR 2023 ML4IoT workshop; arXiv:2305.04468) [FT]: replaces masked-MLM with a **data-degradation scheme** — four synthetic outlier types (soft replacement, uniform replacement, length adjustment, peak noise) injected into windows; transformer with 1D relative position bias predicts a per-point anomaly score; trained with BCE against the injected mask. Best F1 on 5 benchmarks (SWaT 0.854, WADI 0.580, MSL 0.302, SMAP 0.457, SMD 0.535) — notably robust when *training data contain unlabeled outliers* (MSL/SMAP). This directly addresses the contamination problem and requires **no "normal-only" training set** — the most transferable design idea for the thesis among the TSAD papers.
**Anomaly Transformer** (Xu et al., ICLR 2022; arXiv:2110.02642) [ABS via discovery, 1,605 alphaXiv views]: association-discrepancy criterion.
**DCdetector** (Yang et al., KDD 2023; arXiv:2306.10347) [ABS via discovery, 832 views]: dual-attention contrastive representation for TSAD.
**MAD** (Masked Anomaly Detection task; arXiv:2205.02100) [ABS via discovery]: masked modeling as a general SSL-AD task for multivariate TS.
**Reviews:** Zhang et al. DL-for-TSAD survey (arXiv:2211.05244, Monash/Griffith/IBM) [ABS]; "A Review on Self-Supervised Learning for Time Series Anomaly Detection: Recent Advances and Open Challenges" (arXiv:2501.15196, UPV/EHU/BCAM, 2025) [ABS] — open challenges include generalization and label scarcity.

## 9. Cross-family synthesis (what this review concludes for the field)

1. **No single SSL family dominates.** Contrastive/distillation win frozen evaluations; masking wins scale and gives native anomaly scores; latent prediction (JEPA) handles acquisition-specific nuisance; multimodality consistently helps when modalities are spatially aligned (CROMA, SSL4EO-S12, Galileo).
2. **Evaluation protocol changes the ranking.** SSL4EO-S12: contrastive > masking under linear probing, but all SSL families beat supervised from scratch by 1–6% under fine-tuning [FT]. Major et al.: SSL's transfer benefit is *task-dependent* — strongest for AD [FT].
3. **Pretext choice is an invariance-choice problem, not a free lunch.** SeCo's seasonal-invariance warning and Paul et al.'s augmentation-caution both show SSL can *delete* the signal a stress-monitoring task needs.
4. **Contamination of the "normal" set is the open AD problem** (Ruff 2021); synthetic-anomaly schemes (AnomalyBERT) are the most direct remedy published so far.

---

*Verification note: [FT] items were read in full text (local PDFs or alphaXiv page extraction) on 2026-10-24; [ABS] items verified against arXiv/OpenAlex records with abstract; [MO] canonical papers verified via arXiv export API title match (IDs corrected where initially guessed wrong: TS-TCC 2106.14112, SwAV 2006.09882, SimMTM 2302.00861). Numbers quoted are from the cited tables/sections of the inspected papers.*
