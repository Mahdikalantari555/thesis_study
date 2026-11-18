# Affordable Precision Agriculture: A Deployment-Oriented Review of Low-Cost, Low-Power Edge AI and TinyML for Resource-Constrained Farming Systems

## Full citation
Samanta, R., & Saha, B. (2026). *Affordable Precision Agriculture: A Deployment-Oriented Review of Low-Cost, Low-Power Edge AI and TinyML for Resource-Constrained Farming Systems*. arXiv:2603.15085 [cs.ET] (preprint, Techno India University / Sister Nivedita University, India). https://arxiv.org/abs/2603.15085

## Problem & setting
- Deployment-oriented review (2023–2026 literature; 45 candidates screened → 34 full-text → 28 included) of Edge AI and TinyML in resource-constrained/smallholder agriculture. Motivation: cloud-centric smart farming fails under Indian smallholder realities — 86.21% of operational holdings <2 ha (avg 1.08 ha, 2015–16 Census), <20% of farmers actively using digital tech, intermittent power, poor rural connectivity.
- Five application domains: plant disease detection, precision irrigation, soil monitoring, crop recommendation, UAV-assisted distributed intelligence.

## Method (review + synthesis)
- Systematic Boolean searches across Google Scholar/IEEE/ScienceDirect/Springer/ACM/Scopus; inclusion criteria require on-device or near-edge inference, explicit resource constraints (flash/RAM/latency/energy), embedded hardware, peer-reviewed validation.
- **Three deployment architectures synthesized:** fully on-device (ESP32-CAM CNN, 103.9 KB RAM, 850 ms latency, 92% disease accuracy; 6.2 KB quantized NN for irrigation anomaly detection; ESP-EYE UAV 90% acc), edge-assisted (LoRa/IoT coordinated sensing with optional cloud), distributed collaborative (split learning, up to 86% energy reduction vs centralized training).
- **Proposed 4-layer privacy-preserving architecture:** physical sensing → inference execution (TinyML vs SBC on-device, or offloading) → edge processing (fusion, split learning) → cloud training/management (lifecycle, retraining, threshold updates pushed back to edge).
- Resource-profiled hardware: microcontroller class dominates (ESP32, STM32U575, ATMega328P, Arduino BLE 33, ESP-EYE) plus SBC (Jetson Nano, DBLA-MobileNetV2 FP16+TensorRT 97.90% precision, 12.40 FPS).

## Data & labels
- Reviews existing deployments; catalogs benchmark datasets per domain: PlantVillage (54k leaf images, 38 diseases) and PlantDoc (field conditions) for disease; **OpenET (30 m satellite ETa, field scale)** and International Soil Moisture Network (2,800+ stations) for irrigation; LUCAS (~45k European topsoil samples) and WoSIS (228k+ profiles, 174 countries) for soil; Kaggle Crop Recommendation (NPK+climate, 22 crops); Agriculture-Vision (94,986 RGB-NIR aerial images, 10 cm, 8 anomaly conditions incl. weeds, nutrient deficiency, drydown) and its SSL-pretraining extension for UAV.

## Results (quantitative synthesis)
- **Quantization is the dominant optimization (~50% of works use INT8/quantization);** structured pruning appears in only 1 of 13 tabulated works; hardware-aware NAS and multi-objective compression essentially absent; lightweight architecture design is near-universal.
- Headline resource numbers: 6.2 KB model (irrigation anomaly detection on MCU); 51.8 mJ/inference for INT8 YOLOv8n on STM32 (flash 850.97 KB, RAM 677.30 KB); 7.6 ms latency CNN (344.7 KB flash, 726.6 KB RAM); 99% model-size reduction for RF crop recommendation on ATMega328P; DVFS scheduling −8.5% energy; split learning −86% energy.
- **Resource-profiling gap identified:** RAM, MAC counts, and energy-per-inference are rarely reported; most quantized deployments omit energy evaluation — a reproducibility failure the review formalizes.
- Structural pattern: **inference increasingly localized, training centralized** ("inference–training asymmetry") — on-device adaptivity, federated TinyML, and edge fine-tuning named as research frontiers.
- Field-validation gap: most systems validated on curated datasets; multi-season field trials measuring yield gain, water savings, or earlier detection vs conventional scouting are rare.

## What transfers to our thesis
- **The deployment constraint chapter of our thesis:** quantitative evidence that microcontroller/SBC-class inference (6.2 KB–1 MB models, 51.8 mJ/inference, ~8 ms latency) is feasible for agricultural anomaly detection — directly supports the "lightweight multi-product in-field model" requirement for sugarcane deployments with intermittent connectivity/power.
- The **inference–training asymmetry** maps exactly onto our SSL design: SSL pretraining (and supervised fine-tuning) happens offline/centrally on multi-year Landsat archives; only a tiny frozen encoder + anomaly head ships to the field for local inference — a pattern the review identifies as the dominant and pragmatic architecture.
- Their diagnosis of **missing resource metrics (flash, RAM, MACs, mJ/inference)** is a checklist our thesis should adopt for its deployment evaluation — differentiating contribution from accuracy-only agri-AI literature.
- The identified optimization gap (pruning/NAS underused; quantization overused) suggests our model-compression strategy should include structured pruning + quantization jointly, and report both.
- Field-validation critique (multi-season trials, agronomic outcomes like water saved per hectare, earlier detection vs scouting) defines what "in-field cross-year validation" should mean in our thesis — aligns with cross-year evaluation and water/salinity stress outcomes.
- OpenET (30 m satellite ETa) as reference data is directly relevant to our ETa/CWSI water-stress pathway — usable as a label-free proxy/validation source for sugarcane water stress.

## Limitations / caveats
- Review covers only 28 studies, mostly small Indian prototypes; many lack rigorous baselines; some cited works by the same author group (self-citation pattern visible).
- No satellite time-series/remote sensing inference case is deeply treated (UAV imagery is the closest); the Landsat/EO-to-edge pipeline (download → compress → field inference) is not analyzed.
- Accuracy claims (90–97%) come from laboratory datasets (PlantVillage); the review itself flags generalization concerns to real fields.
- The proposed 4-layer architecture is conceptual, not evaluated.
- Preprint; editorial quality issues (typos, "MoReover").

## Key numbers to quote in lit review
- ~50% of agricultural TinyML deployments rely on quantization; structured pruning appears in only 1/13 studies; hardware-aware NAS essentially absent.
- Deployed footprints: 6.2 KB anomaly-detection NN; 51.8 mJ/inference (INT8 YOLOv8n, STM32); 7.6 ms latency CNN; 99% model-size reduction (RF on ATMega328P).
- 86.21% of Indian operational holdings are <2 ha (avg 1.08 ha) and <20% of farmers actively use digital technology — the smallholder deployment gap.
- Split learning cuts distributed-training energy by up to 86%; DVFS scheduling saves 8.5%.
- Structural finding: inference is local, training stays cloud-central — the prevailing and pragmatic architecture for constrained farming.
