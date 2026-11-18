# 2601.01891v1.pdf

- Category: Agentic
- Pages: 17
- Path: D:\RS\Thesis\New_papers\Agentic\2601.01891v1.pdf

## Metadata

```json
{
  "/Author": "Niloufar Alipour Talemi; Julia Boone; Fatemeh Afghah",
  "/Creator": "arXiv GenPDF (tex2pdf:57610bf)",
  "/DOI": "https://doi.org/10.48550/arXiv.2601.01891",
  "/License": "http://arxiv.org/licenses/nonexclusive-distrib/1.0/",
  "/PTEX.Fullbanner": "This is pdfTeX, Version 3.141592653-2.6-1.40.28 (TeX Live 2025) kpathsea version 6.4.1",
  "/Producer": "pikepdf 8.15.1",
  "/Title": "Agentic AI in Remote Sensing: Foundations, Taxonomy, and Emerging Systems",
  "/Trapped": "/False",
  "/arXivID": "https://arxiv.org/abs/2601.01891v1"
}
```

## First pages


===== PAGE 1 =====
Agentic AI in Remote Sensing: Foundations, Taxonomy, and Emerging Systems
Niloufar Alipour Talemi Julia Boone Fatemeh Afghah
Clemson University
{nalipou, jcboone, fafghah}@clemson.edu
Figure 1. Overview of the Agentic AI ecosystem in remote sensing. The proposed framework consists of four key components: 1)
Foundations: Data acquisition and foundation models; 2) Agents: A classification of systems into single-agent copilots vs. multi-agent
orchestrators; 3) Systems: The technological stack (RAG, Tools, Memory) empowering the agents; and 4) Evaluation: Benchmarks for
assessing planning and reasoning capabilities. The figure also maps these components to specific Earth observation applications.
Abstract
The paradigm of Earth Observation analysis is shifting from
static deep learning models to autonomous agentic AI. Al-
though recent vision foundation models and multimodal
large language models advance representation learning,
they often lack the sequential planning and active tool
orchestration required for complex geospatial workflows.
This survey presents the first comprehensive review of agen-
tic AI in remote sensing. We introduce a unified taxonomy
distinguishing between single-agent copilots and multi-
agent systems while analyzing architectural foundations
such as planning mechanisms, retrieval-augmented gener-
ation, and memory structures. Furthermore, we review
emerging benchmarks that move the evaluation from pixel-
level accuracy to trajectory-aware reasoning correctness.
By critically examining limitations in grounding, safety, and
orchestration, this work outlines a strategic roadmap for the
development of robust, autonomous geospatial intelligence.
1. Introduction
Earth observation (EO) technologies have generated mas-
sive multi-modal remote sensing (RS) archives [153], rang-
ing from very high resolution (VHR) optical imagery to
synthetic-aperture radar (SAR) [92], infrared [95], and hy-
1
arXiv:2601.01891v1  [cs.CV]  5 Jan 2026
===== PAGE 2 =====
perspectral data [121]. These data streams underpin crit-
ical applications in environmental monitoring [98], disas-
ter management [86], and resource exploration, making au-
tomated analysis essential. Deep learning models are the
primary tools for interpreting such data, widely applied
to scene classification [151], anomaly detection [60, 127],
change detection [30], and localization [62]. As the field
scales, there is a shift toward vision foundation models
(VFMs) trained on diverse datasets to learn general-purpose
representations [27, 33], with representative examples in-
cluding SimCLR [21] and masked autoencoders (MAE)
[47]. Vision transformers (ViTs) [34] facilitate this by ap-
plying self-attention to image patches [122], a capability
successfully adapted to RS tasks [90, 102, 132]. Despite
this progress, standard foundation models exhibit limita-
tions. Analyses indicate that MAE-style RS models of-
ten prioritize low-level textures over global spatial structure
[63, 139], reducing robustness under distribution shifts [97].
Furthermore, many existing models rely heavily on anno-
tated data and task-specific fine-tuning. To mitigate this
annotation dependence, vision-language models (VLMs)
such as CLIP [100] align image and text encoders to en-
able open-vocabulary detection and zero-shot segmentation
[20, 75, 113]. Extending these capabilities, multimodal
large language models (MLLMs) [5, 58, 130] couple visual
encoders with large language models (LLMs) [9, 17] to sup-
port complex reasoning. However, general-purpose models
often degrade when applied directly to RS data due to dif-
ferences in sensors, viewing geometries, and semantics.
To bridge this domain gap, recent research has devel-
oped RS-specific MLLMs such as GeoChat [67], LHRS-
Bot [93], RS-LLaV A [11], SkySenseGPT [81], and Ring-
MoGPT [54]. These systems adapt architectures like
LLaV A [76] or BLIP-2 [70], often using low-rank adap-
tation [52] to fine-tune on geospatial instructions for cap-
tioning and visual question answering (VQA). Yet, these
models remain static; while they answer single-turn queries,
they lack the native capacity for long-horizon memory, se-
quential planning, or dynamic interaction with geospatial li-
braries. Consequently, they fall short of handling the multi-
step workflows that involve retrieval, preprocessing, and
analysis and that characterize real-world geospatial opera-
tions. This limitation highlights the need to transition from
static MLLMs to agentic systems.
AI agents are autonomous entities that perceive inputs,
reason about tasks, and plan actions to achieve goals. In
LLM-centric architectures, an agent combines a planner, a
tool interface, and memory within a perception-reasoning-
action loop, a paradigm that has transformed workflows in
healthcare [4] and operating systems [1, 89]. In geospa-
tial AI, systems such as RS-Agent [140], GeoAgent [56],
Change-Agent [74], and MapBot [134] instantiate this by
employing LLM controllers to interpret queries and orches-
trate tools for classification, segmentation, and map edit-
ing. Beyond single-agent copilots, the field is expand-
ing toward multi-agent orchestration and realistic environ-
ments. Notable developments include GeoLLM-Engine
[112], the multi-agent GeoLLM-Squad [114], and special-
ized pipelines such as RingMo-Agent [54] and MineAgent
[144]. While existing surveys focus on RS foundation mod-
els and MLLMs, they typically overlook the autonomous
capabilities of RS agentic systems. To the best of our
knowledge, this work is the first survey dedicated to agen-
tic AI in RS, providing a taxonomy of agent types, a com-
parative analysis of models and applications, and a system-
level view of tools, retrieval-augmented generation (RAG)
pipelines, memory mechanisms, datasets, and benchmarks.
Moreover, we connect these components to emerging eval-
uation protocols for planning, and safety, and we articulate
open challenges and future directions in geospatial ground-
ing, long-horizon memory, and trustworthy RS agents.
2. Background
2.1. Sensors, Data, and Applications
RS observations are acquired by heterogeneous sensors de-
ployed on satellites, crewed aircraft, UA Vs or drones, and
ground-based systems, including optical RGB and infrared
cameras, multispectral and hyperspectral images, thermal
sensors, LiDAR, and SAR/InSAR instruments [26, 124].
Each sensor type captures complementary aspects of the
Earth’s surface, such as geometry from LiDAR, backscat-
ter from SAR, or reflectance signatures from multispectral
and hyperspectral instruments, yielding distinct noise char-
acteristics, spatial resolutions, and radiometric properties
that strongly influence model design and fusion strategies
[105]. Platform differences in altitude, viewing geometry,
coverage, and revisit time induce trade-offs between spatial
resolution, temporal frequency, and swath width that must
be considered when defining realistic benchmarks and when
designing foundation models that can generalize across or-
bital, aerial, and ground perspectives [84, 129]. The combi-
nation of diverse sensors and platforms produces inherently
multi-modal data, including optical and infrared images, Li-
DAR point clouds, hyperspectral and multispectral cubes,
thermal imagery, SAR/InSAR products, and associated tex-
tual metadata or annotations [29, 50, 85]. Each modality
captures distinct geophysical processes; joint exploitation
significantly improves robustness and disambiguates chal-
lenging scenes, such as cloud-covered optical imagery that
remains visible in SAR. These multi-modal representations
support a various downstream tasks, including land-cover
classification, segmentation, object detection, and change
detection, as well as higher-level applications such as dis-
aster management, urban planning, environmental monitor-
ing, and RS question answering.
2
===== PAGE 3 =====
2.2. Vision and Multimodal Foundation Models
Foundation models [6, 7, 14, 36, 116] are large neural
networks pre-trained on broad, heterogeneous data with
generic objectives and then adapted to many downstream
tasks, forming the backbone of modern vision, language,
and multimodal systems. Convolutional networks such as
AlexNet [66], VGG [111], and ResNet [46] pre-trained on
ImageNet [104] established transfer learning as a standard
paradigm. Transformer-based VFMs such as ViT [34], built
on the transformer [122], and self-supervised methods such
as SimCLR [21], MAE [47], and SimMIM [138] enable
scalable pretraining and learn transferable representations
without dense labels, which is crucial for label-scarce EO
and RS settings. Language foundations such as GPT-family
autoregressive LLMs [9, 17] extend these ideas to web-scale
text through next-token prediction and instruction tuning.
Multimodal foundation models jointly learn from images
and text: contrastive vision–language models such as CLIP
[100] train paired image and text encoders, while MLLMs
such as Flamingo [5] and LLaV A [76] couple a visual en-
coder with an LLM operating on unified visual–textual to-
kens for captioning and VQA. These mechanisms for rep-
resentation learning, image–text alignment, and instruction
following underpin RS-specific encoders such as SatMAE
[27] and RingMo [54] and geospatial MLLMs.
3. Remote Sensing Foundation Models
The paradigm shift initiated by large-scale pre-trained mod-
els in natural language processing and computer vision has
rapidly extended to the RS domain. RS foundation mod-
els target key characteristics of geospatial data, including
high-dimensional multispectral and hyperspectral signals,
heterogeneous modalities such as optical imagery, SAR and
LiDAR, and limited labels. Building on general VFMs such
as ViT [34] and VLMs like CLIP [100], the RS commu-
nity has converged on two main adaptation strategies. The
first adapts VFMs, including the segment anything model
[61], with self-supervised learning (SSL) techniques such as
masked image modeling (MIM) [49] and contrastive learn-
ing [53] on large unlabeled RS corpora. The second designs
multimodal integration frameworks that fuse RS imagery
with auxiliary data, notably natural language, to construct
vision-language and MLLMs for geospatial reasoning.
3.1. Vision Foundations in Remote Sensing
In RS, VFMs must handle modalities beyond RGB, includ-
ing multispectral and hyperspectral imagery, SAR, thermal
data, and LiDAR point clouds. Most RS models still ini-
tialize from ImageNet [104], despite its clear domain gap in
modality, viewpoint, and spatial structure. RS-specific pre-
training reduces this gap: MillionAID [126] improves over
ImageNet, and Satlas [10] shows unified multitask pretrain-
ing yields consistent gains. Because RS and EO data are
abundant but labels are scarce and costly, SSL and and MIM
has become the primary strategy. RS-oriented contrastive
methods such as Seasonal Contrast [88], Geography-Aware
SSL [8], and SatMAE-CL [27] learn platform-invariant,
geometry-aware features across temporal and cross-sensor
views. MIM approaches such as SatMAE [27] and RingMo
[54] reconstruct masked spatial or spectral content essen-
tial for multispectral and hyperspectral data. Collectively,
these SSL paradigms drive modern RS representation learn-
ing and improve generalization across downstream tasks.
3.2. Multi-Modal Foundations in Remote Sensing
MLLMs extend VLMs by feeding images and other inputs,
such as video and point clouds, into a language model back-
bone that processes a unified token sequence [100]. Visual
encoders project images into the language space for joint
multimodal reasoning and dialogue [1], supporting tasks
such as VQA and instruction following [19]. MLLMs in-
herit strong reasoning ability, flexible I/O formats, and lan-
guage coverage [45], enabling open-world interaction [91],
multimodal assistants [147], and geospatial dialogue sys-
tems [67]. In RS, MLLMs adapt this architecture to satellite
and aerial imagery
