# 02 — SSL for Remote Sensing and Earth Observation

**Scope:** SSL methods and pretrained foundation models for satellite/aerial imagery; what each actually does (objective, modality, data scale), what it demonstrably achieves, and where the evaluation evidence is strong vs. thin. Companion: `03_satellite_time_series_ssl.md` (temporal methods).
**Search date:** 2026-10-24. Evidence levels: [FT] full text inspected; [ABS] abstract verified; [MO] metadata verified.

---

## 1. Why in-domain pretraining replaced ImageNet transfer

The domain gap argument is empirically settled. SeCo [FT]: SeCo ResNet-50 features beat ImageNet-supervised features on BigEarthNet under linear probing by ~8 mAP (78.56 vs 70.46) with 1M pretraining images, and with 1% BigEarthNet labels SeCo linear probing *outperformed ImageNet pretraining using 100% of labels* [FT, Fig. 3]. SSL4EO-S12 [FT]: SSL4EO pretraining beats ImageNet by ~10% (RGB linear probing, EuroSAT) and retains a ~5% margin even after fine-tuning (Tables V, XIX). Chang et al. (crop-type transfer, IGARSS 2025, arXiv:2409.09451) [FT]: Sentinel-2-specific SSL4EO-S12 weights beat ImageNet and SatlasPretrain weights in all five continental test regions by 3–27% F1.

## 2. Pretraining-data engineering (a first-class research problem)

- **SeCo** (Mañas, Lacoste, Giró-i-Nieto, Vazquez, Rodriguez; ICCV 2021; arXiv:2103.16607) [FT]: uncurated collection of ~1M Sentinel-2 patches (RGB used) from ~200K locations around the 10k most-populated cities; 5 dates per location at ~3-month spacing; <10% cloud filter. Ablation: Gaussian sampling around settlements beats uniform continental sampling by ~3 mAP [FT, Table 2].
- **SSL4EO-S12** (Wang, Ait Ali Braham, Xiong, Liu, Albrecht, Zhu; IEEE GRSM 2023; arXiv:2211.07044) [FT]: 251,079 locations × 4 seasonal timestamps × (S1 GRD + S2 L1C + S2 L2A) ≈ 3M patches, overlap-filtered (~3% residual overlap in dense Tokyo); ablations show seasonal augmentation > fixed season, dual product level (L1C+L2A) helps up to 4%, and pretraining-data scaling saturates near 750k–1M patches (BE-10%: 100K→64, 250K→73, 500K→78, 750K→81, 1M→82) [FT, Table XI].
- **Dataset curation also matters downstream:** Kerdreux et al. (CVPRW 2025; arXiv:2504.06962) [ABS] show dynamic dataset pruning improves SSL feature quality on Sentinel-1 archives; SSL4EO-S12 documents geographic bias from cloud filtering as an explicit limitation [FT].

## 3. Single-date multispectral SSL (the non-temporal core)

- **GASSL / Geography-Aware SSL** (Ayush et al.; ICCV 2021; arXiv:2011.09980 — ID verified) [MO]: location-based positives/negatives with a triplet objective on Landsat data; historically the first widely cited "geography as augmentation" RS-SSL method; used as a baseline in SatMAE's tables [FT].
- **SatMAE** (Cong, Khanna, Meng, Liu, Rozi, He, Burke, Lobell, Ermon; NeurIPS 2022; arXiv:2207.08051) [FT]: MAE for temporal *and* multispectral imagery — temporal positional encoding split across year/month/hour, independent masking across time, spectral band groups (RGB+NIR / red-edge / SWIR) with group encodings. Pretraining: fMoW RGB and new **fMoW-Sentinel** (712,874 training images). Results: temporal fMoW classification 81.49 top-1 (+4.48% over prior SOTA GASSL 74.11); fMoW-Sentinel 61.48 (scratch 54.46); EuroSAT 98.94; BigEarthNet-10% mAP 82.13; NAIP 71.77; SpaceNet v1 78.07 mIoU [FT, Tables 1–9]. Ablations: temporal encoding + independent masking drive the temporal gains; 0.75 mask ratio optimal (0.9 viable for multispectral with independent masking) [FT, Tables 4, 12–13]. Author-acknowledged limits: token-sequence length strains compute; optimal positional encodings/band groups unresolved [FT].
- **Scale-MAE** (Reed et al.; ICCV 2023; arXiv:2212.14532) [MO, verified via arXiv]: scale-aware MAE with Laplacian-pyramid reconstruction and GiT positional encoding for multi-scale geospatial data.
- **SpectralGPT** (Hong et al.; IEEE TPAMI 2024; DOI 10.1109/TPAMI.2024.3362475; arXiv:2311.07113) [MO+DOI verified]: 3D GPT-style masked reconstruction over spectral patches for multispectral time-series-cube inputs.
- **MMEarth** (Nedungadi et al.; arXiv:2405.02771) [MO, verified via arXiv]: multi-modal pretext tasks grounded on paired modalities.
- **SIGMAE** (arXiv:2603.07463) [ABS]: spectral-index-guided MAE — directly relevant to the raw-bands-vs-indices design question.
- **DINO-family for RS:** SatDINO (arXiv:2508.21402) [ABS] investigates DINO pretraining for RS; "Embedding Earth" (arXiv:2203.06041) [MO, verified via arXiv] uses contrastive pretraining for dense land-cover classification.
- **DeCUR** (ECCV 2024; DOI 10.1007/978-3-031-73397-0_17) [ABS]: decouples common/unique representations for S1/S2 SSL.
- **DOFA** (Xiong et al.; arXiv:2403.15356) [MO, verified via arXiv]: one-for-all dynamic-weighting multimodal FM; benchmarked in Galileo [FT].

## 4. Multimodal radar–optical foundation models

- **CROMA** (Fuller, Millard, Green; NeurIPS 2023; arXiv:2311.00566) [FT]: three encoders (radar ViT, optical ViT, joint cross-attention encoder); radar↔optical InfoNCE on masked unimodal encodings + multimodal MAE reconstruction (75% independent masking); 2D-ALiBi / X-ALiBi relative position biases enable test-time extrapolation to images up to 17.6× larger. Pretrained on SSL4EO (1M paired S1/S2-L2A 264×264 samples). Beats SatMAE under identical conditions on 4 classification benchmarks (e.g., BigEarthNet-10% linear mAP 85.04 ViT-B; Canadian Cropland — a **crop-type** benchmark — linear probe 63.39) and 3 segmentation benchmarks (+6.4% avg) [FT, Tables 1–2]. Ablation: both objectives needed (MAE-only −7.5 avg; contrast-only −3.2) [FT, Table 6]. Code: github.com/antofuller/CROMA.
- **AnySat** (Astruc et al., 2024; arXiv:2412.14123 — ID verified via title search) [MO]: one model for many resolutions, scales, and modalities; JEPA-style latent prediction per Galileo's taxonomy figure [FT, Fig. 5].

## 5. Landsat & other archives

- **SSL4EO-L** (Stewart et al., NeurIPS 2024; arXiv:2306.09424) [MO, verified via arXiv title]: Landsat datasets + foundation models — the only verified large-scale Landsat SSL corpus; notable because the thesis works on Landsat 8/9 archives (most SSL work is Sentinel-centric).
- **SatlasPretrain** (Bastani et al., ICCV 2023) [MO, cited in Chang et al.]: large multi-sensor corpus incl. Landsat 8/9 + NAIP; underperformed SSL4EO-S12 for crop-type transfer, plausibly because it accepts only 9 of 13 S2 bands [FT, Chang et al. §IV-A].
- **Prithvi** (Jakubik et al., NASA/IBM; arXiv:2310.18660; SSRN preprint DOI 10.2139/ssrn.4804009) [MO]: HLS-based geospatial FM; **Prithvi-EO-2.0** (Szwarcman et al., arXiv:2412.02732, cited by T-JEPA [FT]) adds multi-temporal context — used as a strong baseline T-JEPA matches/beats [FT].
- **Nereus-SAR** (Kerdreux et al., arXiv:2504.06962) [ABS]: 10-year Sentinel-1 Wave Mode archive SSL with dataset pruning.
- **FLORO** (KAUST; arXiv:2605.28174) [ABS]: ecological RS FM across sensors/scales (adjacent evidence that sensor-flexible designs are an active 2026 direction).

## 6. What do RS-SSL representations actually encode?

- **Probing with environmental signals** (JHU APL; arXiv:2607.05207) [ABS]: most geospatial SSL benchmarks evaluate static land-cover classes only; this work probes representations against environmental variables — an underused evaluation style.
- **Ecology transfer:** SSL satellite features predict below-ground fungal biodiversity (arXiv:2604.09818, Cambridge/SPUN/VU) [ABS] — evidence that SSL features carry biologically meaningful environmental signal beyond land cover.
- **Downstream behavior:** "How do Self-Supervised Remote Sensing Vision Models Transfer to Downstream Tasks?" (arXiv:2606.13896) [ABS] and "Do Satellite Tasks Need Special Pretraining?" (arXiv:2510.17014, YerevaNN/UIUC) [ABS] — controlled comparisons questioning how much of RS-FM gains come from special pretraining; treat SoTA claims critically.

## 7. Evaluation protocols and their pitfalls (verified findings)

1. **Linear probing vs fine-tuning rank methods differently.** SSL4EO-S12: contrastive methods dominate linear probing; masking methods catch up under fine-tuning [FT, Tables III–IV]. Major et al.: linear probing is an unreliable predictor of fine-tuned performance for time-series SSL [FT].
2. **Pretraining/downstream similarity dominates comparisons.** CROMA notes SatMAE's fine-tuning win on fMoW-Sentinel reflects pretrain-downstream co-location, not representation quality [FT, §3.1]; SSL4EO-S12 loses to SEN12MS on DFC2020 because DFC2020 is built from SEN12MS [FT, Table VI].
3. **Label-efficiency is the SSL sweet spot.** Consistent finding across SeCo (1% labels > ImageNet-100%) [FT], SSL4EO-S12 (10% ≈ supervised-50–100%) [FT], and Chang et al. (100 ID images already yield high overall accuracy; 900 needed for class-imbalance-robust average accuracy) [FT].
4. **Surveys to consult:** Wang et al., "Self-Supervised Learning in Remote Sensing: A Review" (IEEE GRSM 2022, cited as [1] in SSL4EO-S12) [MO]; Lu et al., "Vision Foundation Models in Remote Sensing: A Survey" (IEEE GRSM 2025; DOI 10.1109/mgrs.2025.3541952; arXiv:2408.03464, 132 citations) [ABS].

## 8. Interpretation (ours, clearly separated from author claims)

The verified evidence supports three planning conclusions for a small-lab, Landsat-based project: (a) in-domain pretraining over a domain-matched archive beats generic weights by margins (3–10%) that matter at low label counts; (b) pretraining-data *design* (seasonal coverage, product levels, sampling diversity, curation) has measured effects of the same magnitude as method choice — a cheap lever for a 490-field archive; (c) published FMs cannot be used as-is for the thesis's core need (Landsat 16-day, raw bands + LST, field-level): SSL4EO-S12/L are Sentinel/Landsat *scene* corpora without thermal channels in the temporal-SSL models verified here, and none of the deep-read models consume LST. Foundation models are therefore **ablation/robustness arms** (as the advisor stipulated), not the main vehicle.

---

*Verification note: [FT] = full text read via alphaXiv page extraction on 2026-10-24 (SeCo, SSL4EO-S12, SatMAE, CROMA, Galileo, T-JEPA + Chang et al.); [ABS] = abstract verified via alphaXiv discovery or OpenAlex; [MO] = metadata verified via arXiv export API / Crossref. One initially suspected method ("PANOPTIC pretraining paper") was resolved as the attention module inside Garnot & Landrieu's ICCV 2021 U-TAE paper and is not cited as a separate method; a separate "GASSL = generalist model" reading was corrected to Ayush et al.'s Geography-Aware SSL (arXiv:2011.09980).*
