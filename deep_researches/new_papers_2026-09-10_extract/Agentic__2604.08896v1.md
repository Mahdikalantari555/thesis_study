# 2604.08896v1.pdf

- Category: Agentic
- Pages: 19
- Path: D:\RS\Thesis\New_papers\Agentic\2604.08896v1.pdf

## Metadata

```json
{
  "/Author": "Aoran Xiao; Shihao Cheng; Yonghao Xu; Yexian Ren; Hongruixuan Chen; Naoto Yokoya",
  "/Creator": "arXiv GenPDF (tex2pdf:a6404ea)",
  "/DOI": "https://doi.org/10.48550/arXiv.2604.08896",
  "/License": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
  "/PTEX.Fullbanner": "This is pdfTeX, Version 3.141592653-2.6-1.40.28 (TeX Live 2025) kpathsea version 6.4.1",
  "/Producer": "pikepdf 8.15.1",
  "/Title": "GeoMMBench and GeoMMAgent: Toward Expert-Level Multimodal Intelligence in Geoscience and Remote Sensing",
  "/Trapped": "/False",
  "/arXivID": "https://arxiv.org/abs/2604.08896v1"
}
```

## First pages


===== PAGE 1 =====
GeoMMBench and GeoMMAgent: Toward Expert-Level
Multimodal Intelligence in Geoscience and Remote Sensing
Aoran Xiao∗,1,†, Shihao Cheng∗,2, Yonghao Xu3, Yexian Ren5, Hongruixuan Chen1,4, Naoto Yokoya1,4
1RIKEN AIP 2Wuhan University 3Link¨oping University 4University of Tokyo
5Nanjing University of Information Science and Technology
Abstract
Recent advances in multimodal large language models
(MLLMs) have accelerated progress in domain-oriented
AI, yet their development in geoscience and remote sens-
ing (RS) remains constrained by distinctive challenges:
wide-ranging disciplinary knowledge, heterogeneous sen-
sor modalities, and a fragmented spectrum of tasks. To
bridge these gaps, we introduce GeoMMBench, a compre-
hensive multimodal question-answering benchmark cover-
ing diverse RS disciplines, sensors, and tasks, enabling
broader and more rigorous evaluation than prior bench-
marks. Using GeoMMBench, we assess 36 open-source
and proprietary large language models, uncovering system-
atic deficiencies in domain knowledge, perceptual ground-
ing, and reasoning—capabilities essential for expert-level
geospatial interpretation. Beyond evaluation, we propose
GeoMMAgent, a multi-agent framework that strategically
integrates retrieval, perception, and reasoning through
domain-specific RS models and tools. Extensive experimen-
tal results demonstrate that GeoMMAgent significantly out-
performs standalone LLMs, underscoring the importance
of tool-augmented agents for dynamically tackling complex
geoscience and RS challenges. Project:https://geo-
mm-agi.github.io
1. Introduction
Recent progress in multimodal large language models
(MLLMs) has accelerated the pursuit of artificial general
intelligence (AGI), marking an important milestone with
the emergence of Expert AGI. This level of machine in-
telligence is characterized by performance comparable to
or exceeding that of skilled human experts at the 90th per-
centile across professional domains [35]. As research ad-
vances toward this stage, a growing collection of multi-
modal benchmarks has been introduced to assess reason-
ing, perception, and domain expertise across diverse disci-
plines [18, 23, 28, 56, 58]. These benchmarks serve as es-
∗ Equal contribution; † corresponding author
sential instruments for measuring progress and guiding the
development of more capable multimodal systems.
Despite these advances, the domain of geoscience and
remote sensing (RS) has received limited attention in cur-
rent benchmarking efforts. Existing studies [10, 20, 22, 42,
48] remain narrow in scope, focusing primarily on percep-
tion tasks such as classification, detection, or segmentation,
and are often restricted to a limited set of sensor modali-
ties, particularly optical imagery. In contrast, geoscience
requires the integration of multi-sensor data, spatiotemporal
reasoning, and multidisciplinary knowledge, which existing
benchmarks fail to adequately evaluate. This gap highlights
the need for a comprehensive and expert-level assessment
framework to systematically measure and advance AGI per-
formance within the RS domain.
To bridge this gap, we introduceGeoMMBench, a com-
prehensive domain-specific benchmark designed to eval-
uate the multidisciplinary and multimodal capabilities of
MLLMs in geoscience and RS. The benchmark contains
1,053 expert-level, image-based multiple-choice questions
that represent diverse and realistic challenges across the key
dimensions, as illustrated in Fig. 1.
GeoMMBench is characterized by three major proper-
ties that define its breadth and depth. (1)Multi-disciplinary
coverage: It spans multiple geospatial disciplines, includ-
ing RS, photogrammetry, geographic information systems
(GIS), and global navigation satellite systems (GNSS).
These areas draw upon foundational knowledge in math-
ematics, physics, cartography, spectroscopy, and geogra-
phy, mirroring the diverse expertise required for profes-
sional interpretation and decision-making. (2)Multi-sensor
modalities: The benchmark incorporates a wide range of
sensing sources such as optical imagery, synthetic aperture
radar (SAR), multispectral and hyperspectral data, LiDAR,
and digital elevation models (DEM). These complementary
modalities enable a realistic evaluation of multi-sensor in-
tegration skills crucial for expert-level analysis. (3)Diverse
task spectrum: GeoMMBench covers a continuum of com-
plexity, from theoretical and data-preprocessing concepts to
perception tasks and high-level geospatial applications, pro-
viding a holistic assessment of AGI capabilities in RS.
1
arXiv:2604.08896v1  [cs.CV]  10 Apr 2026
===== PAGE 2 =====
We conduct a comprehensive evaluation of 36 open-
source and proprietary MLLMs on GeoMMBench, reveal-
ing critical gaps in their ability to interpret geoscience data.
These limitations stem from the benchmark’s multidimen-
sional structure, high domain complexity, and requirement
for expert-level reasoning. To address these challenges, we
proposeGeoMMAgent, a multi-agent system that advances
MLLMs toward expert-level performance in geoscience
and RS. GeoMMAgent integrates large language models
(LLMs) with domain-specific tools and models within an
adaptive framework that plans, coordinates, and executes
tasks across three key functional stages: retrieval, percep-
tion, and reasoning. Through strategic task decomposition
and tool selection, GeoMMAgent enables models to ac-
cess external knowledge bases, analyze complex RS data,
and perform spatial reasoning beyond the intrinsic capac-
ity of general-purpose MLLMs. The framework supports
transparent and modular integration of various RS tools and
model components, promoting interpretability, scalability,
and future extensibility.
Our main contributions are summarized as follows.
First, we propose GeoMMBench, a comprehensive and
domain-specific benchmark, which evaluates the multidis-
ciplinary, multimodal, and multi-level reasoning capabili-
ties of MLLMs in geoscience and RS.Second, we develop
GeoMMAgent, a multi-agent system tailored to geoscience
and RS. It integrates MLLMs with domain-specific mod-
els and tools through structured task planning that spans
retrieval, perception, and reasoning stages, enabling adap-
tive coordination and expert-level task execution.Third, we
conduct an extensive evaluation of open-source and propri-
etary MLLMs on GeoMMBench, establishing the current
performance landscape, identifying key challenges in do-
main expertise, and demonstrating the effectiveness of Ge-
oMMAgent in bridging these capability gaps.
2. Related Works
MLLMs for Geoscience and Remote Sensing.Despite
rapid progress in MLLMs, their applications in geoscience
and RS remain limited [53, 55, 60]. Most recent RS stud-
ies focus on VQA over optical RGB imagery [34, 66].
GeoChat [22] fine-tunes LLaV A-1.5 [26] with detection-
based instruction data, while TeoChat [20] adapts tempo-
ral Earth observation data for change detection. LHRS-
Bot [36] and EarthVQA [48] further tailor multimodal
datasets for RS perception and pixel-level understanding.
However, these models remain task-specific and lack multi-
disciplinary knowledge integration, multi-sensor aware-
ness, and advanced reasoning, which are key capabilities
for expert-level intelligence in geoscience and RS.
Knowledge-driven Benchmarks for RS.Progress toward
Expert AGI [35] has inspired knowledge-oriented bench-
marks to assess professional expertise. Early textual eval-
Figure 1. Expert-level knowledge dimensions in geoscience and
RS covered in GeoMMBench.
uations such as AGIEval [65], ARC [5], and MMLU [15]
focus on standardized exams, while MMLU-Pro [51] in-
troduces higher-order reasoning. Multimodal extensions
like ScienceQA [31], MMMU [58], MMMU-Pro [59],
and Video-MMMU [17] broaden evaluation across images
and temporal sequences. In contrast, RS benchmarks still
concentrate on perception tasks such as scene classifica-
tion [8, 32, 52, 57], object detection [25, 41], and seman-
tic segmentation [25, 48], often using automatically gen-
erated descriptions instead of expert assessments. To the
best of our knowledge, GeoMMBench is the first expert-
crafted, knowledge-driven benchmark that spans multiple
disciplines, sensor modalities, and task hierarchies, bridg-
ing theoretical concepts and practical applications in geo-
science and RS.
3. GeoMMBench Benchmark
3.1. Overview
GeoMMBench is a rigorously designed benchmark that
evaluates the ability of MLLMs to comprehend geoscience
and RS concepts across multiple dimensions. Its primary
objective is to assess how effectively these models perceive
and interpret geospatial information across related disci-
plines while applying domain-specific knowledge and rea-
soning to solve complex geospatial problems.
The benchmark comprises 1,053 image-based multiple-
choice questions, each containing a single correct answer
derived from the provided imagery. The dataset was de-
veloped through collaborative efforts by domain experts in
geoscience and RS, including PhD researchers and doctoral
students, who engaged in extensive panel discussions to de-
fine the scope, content, and evaluation dimensions. Source
materials were drawn from a diverse range of authoritative
references, including educational resources, online reposi-
tories, and academic literature.
For evaluation purposes, the dataset is divided into aval
set of 37 questions and atestset of 1,016 questions. The
valset is intended for assessing human expert performance
and for model selection or hyperparameter tuning in future
2
===== PAGE 3 =====
A) It is often used in passive remote sensing.
B) It is suitable for thermal remote sensing.
C) It operates only during the day and is 
affected by weather conditions.
D) It can penetrate vegetation to detect 
subsurface targets.
Discipline: RS; Image Type: Diagram
Which of the following statements about Band ① is accurate?
A) Super-resolution
B) Motion compensation
C) Radiometric correction
D) Stereo image matching
Discipline: Photogrammetry;Image Type: PanchromaticImage
Which step in photogrammetry 
is illustrated in the image?
A) Select villages that intersect the buffer 
zone.
B) Find all points that have a spatial join.
C) Select point-in-polygon query.
D) Analyze the distance calculation.
Discipline: GIS; Image Type: Map
In the GIS project illustrated, whichspatial query is most appropriate 
for determining the number of villages located near the highway?
A) 𝑐(𝑡𝑟𝑐𝑣𝑒 +𝑡𝑒𝑖 +𝑋𝑖/𝑐𝑟)
B) 𝑐(𝑡𝑟𝑐𝑣𝑒 −𝑡𝑒𝑖 −𝑋𝑖/𝑐𝑟)
C) 𝑐(𝑡𝑟𝑐𝑣𝑒 +𝑡𝑒𝑖 −𝑋𝑖/𝑐𝑟)
D) 𝑐(−𝑡𝑟𝑐𝑣𝑒 +𝑡𝑒𝑖 −𝑋𝑖/𝑐𝑟)
Discipline: GNSS; Image Type: Diagram
Let 𝒄 be the speed of light, and 𝒄𝒓 be the C/A-code chipping rate. How 
is the pseudorange to a satellite calculated based on the given figure?
A. ①
B. ②
C. ③
D. ④
Modality: DEM; Image Type: DEM Image
In the provided DEM visualization, four areas 
(①, ②, ③, ④) are marked. Based on the 
terrain characteristics, which area is most 
likely to represent a valley?
A) The river (No. 10) registered a much lower 
temperature than both lakes (Nos. 3 and 4).
B) Lakes (Nos. 8 and 9) show low land surface 
temperature regions on the map.
C) There is a temperature difference between 
the central areas of both football grounds (Nos. 
3&4) due to their natural and artificial lawns.
D) In the residential area (No. 11), the average 
land surface temperature reaches up to 60°C.
Modality: Thermal; Image Type: Thermal image
Which of the following statements about the image is NOT correct?
A. Twisted Object
B. Blur
C. Stitching Misalignment
D. Strip Noise
Task: Image Quality Inspection;Image Type: Optical image
Does any quality issue appear in this 
remote sensing image?
A) East
B) Northeast
C) Northwest
D) West
Task: Spatial Relation Analysis; Image Type: Optical Image
In which direction from the hospital 
(marked by red box) is the parking lot 
(blue box) located?
A. Wetland converted to lake
B. River expanded to lake
C. Saline-alkali or sandy land 
converted to lake
D. Glacier
