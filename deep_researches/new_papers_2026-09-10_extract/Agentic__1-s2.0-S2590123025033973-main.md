# 1-s2.0-S2590123025033973-main.pdf

- Category: Agentic
- Pages: 16
- Path: D:\RS\Thesis\New_papers\Agentic\1-s2.0-S2590123025033973-main.pdf

## Metadata

```json
{
  "/Creator": "Elsevier",
  "/CrossMarkDomains[1]": "elsevier.com",
  "/CrossmarkMajorVersionDate": "2010-04-23",
  "/CreationDate--Text": "13th December 2025",
  "/ElsevierWebPDFSpecifications": "7.0.1",
  "/robots": "noindex",
  "/ModDate": "D:20251213110020Z",
  "/Author": "Muhammad Usman Tariq",
  "/doi": "10.1016/j.rineng.2025.107342",
  "/Title": "Edge-enabled smart agriculture framework: Integrating IoT, lightweight deep learning, and agentic AI for context-aware farming",
  "/Keywords": "Agentic AI,Edge computing,Internet of things (IoT),Low-power deep learning,Precision farming,Smart agriculture,Weather and crop classification",
  "/CreationDate": "D:20251213090556Z",
  "/Producer": "Acrobat Distiller 8.1.0 (Windows)",
  "/Subject": "Results in Engineering, 28 (2025) 107342. doi:10.1016/j.rineng.2025.107342",
  "/CrossMarkDomains[2]": "sciencedirect.com",
  "/CrossmarkDomainExclusive": "true"
}
```

## First pages


===== PAGE 1 =====
Research paper
Edge-enabled smart agriculture framework: Integrating IoT, lightweight 
deep learning, and agentic AI for context-aware farming
Muhammad Usman Tariq
a
, Sheikh Muhammad Saqib
b
, Tehseen Mazhar
c , j , *
,  
Muhammad Amir Khan
d
, Tariq Shahzad
e , *
, Habib Hamam
f , g , h , i
a
Department of Marketing, Operations, and Information Systems, College of Business, Abu Dhabi University, Abu Dhabi, United Arab Emirates
b
Department of Computing and Information Technology, Gomal University, Dera Ismail Khan 29050, Pakistan
c
School of Computer Science, National College of Business Administration and Economics, Lahore 54000, Pakistan
d
School of Computing Sciences, Faculty of Computer Science and Mathematics, Universiti Teknologi Mara, Shah Alam, 40450 Selangor, Malaysia
e
Department of Computer Engineering, COMSATS University Islamabad, Sahiwal Campus, Sahiwal, 57000, Pakistan
f
Faculty of Engineering, Uni de Moncton, Moncton, NB E1A3E9, Canada
g
School of Electrical Engineering, University of Johannesburg, Johannesburg 2006, South Africa
h
International Institute of Technology and Management (IITG), Av. Grandes Ecoles, Libreville BP 1989, Gabon
i
College of Computer Science and Engineering (Invited Prof.), University of Ha ’ il, Ha ’ il, SA 55476, Saudi Arabia
j
Department of Computer Science and Information Technology, School Education Department, Government of Punjab, Layyah 31200, Pakistan
ARTICLE INFO
Keywords:
Agentic AI
Edge computing
Internet of things (IoT)
Low-power deep learning
Precision farming
Smart agriculture
Weather and crop classification
ABSTRACT
Smart farming in connectivity-limited, energy-sensitive environments demands on-device perception and 
decision-making to reduce latency and cloud dependence. This article proposes an edge-enabled smart agri -
culture framework that integrates lightweight deep learning, rule-based agentic AI, and Internet of Things (IoT) 
devices for real-time, autonomous farming decisions. The system features two vision-based models — one for 
weather classification and one for crop identification — built on the MiT-B0 Vision Transformer architecture and 
optimized for low-resolution (128 × 128) image inputs. These models run on resource-constrained hardware 
suitable for rural deployment and support efficient, on-device processing. Weather prediction spans 11 classes (e. 
g., frost, lightning, rain, sandstorm), while crop classification covers 5 major crops. The system achieves an 
accuracy of 88 % for weather and 93 % for crops, with high F1-scores and low MAE, Kappa, and Hamming loss 
values.
Predictions are interpreted by a rule-based agentic AI layer that triggers actions across multiple IoT actuators, 
such as smart irrigation, NDVI sensors, frost alarms, drones, and pest detectors. The decision engine supports 
both joint rule logic (e.g., activating hail protectors when hail is detected in maize fields) and fallback single- 
condition rules. Python-implemented case studies show seamless model – AI – IoT interaction in combined and 
separate scenarios.
By minimizing cloud dependency, reducing communication overhead, and enabling low-power operation, the 
proposed framework addresses critical challenges in connectivity-limited, energy-sensitive agricultural contexts. 
It demonstrates the potential for scalable and intelligent smart farming, aligning with the goals of sustainable 
Agriculture 4.0.
1. Introduction
1.1. Context
In response to global pressures such as population growth, climate 
change, and the reduction of arable land, agriculture must rapidly 
evolve toward intelligent and sustainable production systems. Accord -
ing to the United Nations Food and Agriculture Organization [ 1 ], the 
global population is projected to reach 10 billion by 2050, and could 
exceed 11 billion by the end of the century [ 2 ]. This demographic surge 
demands a 70 % increase in food production [ 3 ], yet the global area of 
cultivable land continues to shrink — from around 20 million to 18 
* Corresponding authors.
E-mail addresses: tehseenmazhar719@gmail.com (T. Mazhar), tariq@cuisahiwal.edu.pk (T. Shahzad). 
Contents lists available at ScienceDirect
Results in Engineering
journal homepag e: www.sci encedirect.co m/journa l/results-in-eng ineering
https://doi.org/10.1016/j.rineng.2025.107342
Received 11 August 2025; Received in revised form 6 September 2025; Accepted 16 September 2025  
Results in Engineering 28 (2025) 107342 
Available online 17 September 2025 
2590-1230/© 2025 The Authors. Published by Elsevier B.V. This is an open access article under the CC BY-NC-ND license ( http://creativecommons.org/licenses/by- 
nc-nd/4.0/ ). 
===== PAGE 2 =====
million square miles — due to urban expansion and industrial develop -
ment [ 4 ]. These opposing trends underscore the urgency of modernizing 
agriculture using digital and autonomous technologies.
Traditional agricultural methods — largely labor-intensive and 
reliant on experiential knowledge — struggle to adapt to climate vola -
tility, resource constraints, and scalability requirements. Challenges 
such as unpredictable weather, erratic soil health, and inefficient input 
usage (e.g., water, fertilizers, pesticides) further compound the sector ’ s 
environmental and economic burdens [ 5 , 6 ]. While past agricultural 
phases — from manual operations (Agriculture 1.0) to mechanization 
and basic automation (Agriculture 3.0) — have improved productivity, 
they lack the intelligent, real-time decision-making capabilities that 
define the emerging paradigm of Agriculture 4.0.
To operationalize the goals of Agriculture 4.0 under intermittent 
connectivity and tight energy/bandwidth budgets, we adopt an edge- 
first architecture centered on two compact vision tasks — weather and 
crop identification — executing directly on resource-constrained devices. 
This dual-vision design is preferred over heavier multi-sensor fusion 
because it provides the minimal, actionable context needed for farm- 
level decisions while keeping hardware, integration, and maintenance 
overheads low. In particular: (i) Context sufficiency and actionabili -
ty — crossing a predicted weather state with the detected crop type maps 
directly to interventions (e.g., frost alert for wheat, hail protection for 
maize) without requiring external data streams; (ii) Edge suitabili -
ty — low-resolution inputs (128 × 128) and a lightweight MiT-B0 
transformer backbone enable low-latency, low-power inference with a 
global receptive field that preserves scene-level cues important for both 
sky conditions and field structure; (iii) Robustness and main -
tainability — avoiding heterogeneous sensor fusion removes calibration/ 
synchronization failure modes and allows each vision model to be 
updated, quantized, or replaced independently; (iv) Cost and priva -
cy — commodity cameras and on-device processing reduce bill of mate -
rials, bandwidth usage, and exposure of farm data. This rationale 
directly motivates the proposed system layout, in which the dual-vision 
outputs feed a rule-based agentic layer that triggers IoT actuators for 
closed-loop, context-aware control at the edge.
Despite increasing investments in rural Internet connectivity, many 
farming regions still face poor infrastructure, intermittent coverage, and 
energy limitations. To meet these challenges, this study proposes an 
edge-deployable, autonomous smart agriculture framework that fuses 
vision-based deep learning with agentic artificial intelligence and a 
network of real-time Internet of Things (IoT) devices. The system is built 
around two lightweight, transformer-based models: one trained for crop 
classification and another for weather condition detection. Both models 
use the efficient NVIDIA/mit-b0 backbone and operate on reduced- 
resolution (128 × 128) input images, enabling deployment in 
resource-constrained, low-power environments.
Live imagery from field-deployed cameras is processed every hour, 
generating real-time predictions. These are interpreted by a rule-based 
agentic AI layer that translates environmental and agronomic insights 
into automated actions via connected IoT actuators — such as irrigation 
controllers, drones, pest detectors, and environmental sensors. This 
closed-loop architecture transforms passive sensing into proactive field 
management, minimizing manual labor, reducing input waste, and 
increasing resilience to climate variability. The proposed system offers a 
scalable, cost-effective, and intelligent solution aligned with the goals of 
Agriculture 4.0 and the growing demands of sustainable food 
production.
1.2. Gap analysis: why existing edge-AI solutions fall short on contextual 
fusion
Despite notable progress, three persistent limitations motivate our 
design. First, context is rarely fused on-device: many edge deployments 
treat perception as single-task (e.g., crop or disease only) and defer 
cross-context reasoning — such as combining field state with imminent 
weather — to cloud services or manual post-processing, which is fragile 
under rural connectivity constraints. Second, when contextual fusion is 
attempted, it often relies on heterogeneous sensors whose calibration, 
time-synchronization, and bandwidth needs are brittle and costly to 
maintain at farm scale. Third, closed-loop autonomy is seldom realized: 
systems frequently stop at reporting classifier metrics without a verified, 
auditable path to actuation.
Our approach addresses these gaps as follows: (i) Context sufficiency 
at low cost — crossing two camera-derived signals (weather class and 
crop identity) yields actionable context for interventions (e.g., frost alert 
for a detected crop) without adding specialized sensors; (ii) Edge fea -
sibility — compact MiT-B0 models operating on 128 × 128 inputs 
execute efficiently on resource-constrained hardware, reducing latency 
and bandwidth and avoiding cloud dependence; (iii) Robustness and 
maintainability — two decoupled vision models eliminate multi-sensor 
calibration overhead and allow independent updates, quantization, or 
replacement; (iv) From perception to action — a rule-based agentic layer 
converts joint and fallback conditions into IoT actuation (e.g., irrigation 
control, frost alarms, drone dispatch), validated through Python- 
implemented case studies; (v) Privacy and scalability — on-device 
inference limits data exposure while enabling replication across fields 
without network upgrades.
1.3. Objectives
The primary objectives of this research are to design and implement 
a real-time, intelligent smart agriculture framework that meets the 
challenges of limited connectivity, energy constraints, and operational 
complexity in rural and resource-constrained farming environments. 
Specifically, the system aims to: 
- Develop an autonomous, edge-deployable smart agriculture system 
that seamlessly integrates deep learning, agentic AI, and Internet of 
Things (IoT) infrastructure for in-field decision-making.
- Classify crop types and assess weather conditions using two light -
weight, independently trained models based on the MiT-B0 Vision 
Transformer backbone optimized for low-resolution inputs.
- Implement a rule-based agentic AI engine that interprets model 
outputs to trigger precise, context-aware actions via a suite of con -
nected IoT devices.
- Ensure low-latency, energy-efficient inference and system scalability 
to support real-time actuation in connectivity-limited or serverless 
deployment scenarios.
1.4. Key contributions
The main contributions of this work are summarized as follows: 
- An edge-first smart agriculture framework that unites dual vision 
models (weather and crop) with a rule-based decision layer and IoT 
actuation for real-time, on-device control in connectivity- and 
energy-constrained settings.
- Lightweight MiT-B0 backbones at 128 × 128 enable CPU-only 
inference for 11 weather classes and 5 crop classes, support
