# Agentic AI for Remote Sensing Technical Challenges and Research Directions.pdf

- Category: Agentic
- Pages: 31
- Path: D:\RS\Thesis\New_papers\Agentic\Agentic AI for Remote Sensing Technical Challenges and Research Directions.pdf

## Metadata

```json
{
  "/Author": "Muhammad Akhtar Munir; Muhammad Umer Sheikh; Akashah Shabbir; Muhammad Haris Khan; Fahad Khan; Xiao Xiang Zhu; Begüm Demir; Salman Khan",
  "/CreationDate": "D:20260602015210",
  "/Creator": "arXiv GenPDF (tex2pdf:a6404ea)",
  "/DOI": "https://doi.org/10.48550/arXiv.2604.24919",
  "/Keywords": "Agentic AI, Remote Sensing, Earth Observation, Geospatial Reasoning, Tool-Augmented AI, Vision-Language Models, Reinforcement Learning",
  "/License": "http://creativecommons.org/licenses/by/4.0/",
  "/ModDate": "D:20260602015210+00'00'",
  "/Producer": "pikepdf 8.15.1",
  "/Subject": "-  Computing methodologies  ->  Computer vision.Artificial intelligence.Reinforcement learning.-  Applied computing  ->  Earth and atmospheric sciences.",
  "/Title": "Agentic AI for Remote Sensing: Technical Challenges and Research Directions",
  "/arXivID": "https://arxiv.org/abs/2604.24919v3"
}
```

## First pages


===== PAGE 1 =====
Agentic AI for Remote Sensing: Technical Challenges and Research Directions
Muhammad Akhtar Munir1 Muhammad Umer Sheikh1 Akashah Shabbir1
Muhammad Haris Khan1 Fahad Khan1 Xiao Xiang Zhu2
Begüm Demir3 Salman Khan1
1Mohamed bin Zayed University of Artificial Intelligence, Abu Dhabi, UAE
2Technical University of Munich, Munich, Germany
3BIFOLD and Technische Universität Berlin, Berlin, Germany
EarthObservation(EO)ismovingbeyondstaticpredictiontowardmulti-stepanalyticalworkflowsthatrequirecoordinatedreasoning
over data, tools, and geospatial state. While foundation models and vision-language models have advanced representation learning
andlanguage-groundedinteractioninremotesensing,andagenticAIhasshownstrongpotentialforlong-horizonreasoningandtool
use,EOisnotastraightforwardextensionofgenericagenticAI.EOworkflowsoperateongeoreferenced,multi-modal,andtemporally
structured data, where operations such as reprojection, resampling,compositing, and aggregationtransform the underlying state and
can constrain later analysis. As a result, errors may propagate silently across steps, and correctness depends not only on internal
coherence but also on geospatial consistency, temporally valid comparisons, and physical validity. This position paper argues that
these challenges are structural rather than incidental. We examine the assumptions commonly made in generic agentic systems,
analyze how they break in geospatial workflows, and characterize failure modes in multi-step EO pipelines. We then outline design
principles for EO-native agents centered on structured geospatial state, tool-aware reasoning, verifier-guided execution, and validity-
aware learning and evaluation. Building reliable geospatial agents, therefore, requires rethinking agent design around the physical,
geospatial, and workflow constraints that govern EO analysis.
CCS Concepts: •Computing methodologies → Computer vision; Artificial intelligence; Reinforcement learning; • Applied
computing → Earth and atmospheric sciences.
Additional Key Words and Phrases: Agentic AI, Remote Sensing, Earth Observation, Geospatial Reasoning, Tool-Augmented AI,
Vision-Language Models, Reinforcement Learning
1 Introduction
1.1 From Predictive Models to Decision-Oriented Models
ç Earth Observation is not a single-step prediction problem.Itinvolvesasequenceofdecisionsoverdata,
tools, and geospatial state, demanding agentic models rather than standalone models.
Over the past decade, remote sensing (RS) has been transformed by deep learning models built for well-defined
EO tasks [5, 13, 27, 66, 73, 77]. These models substantially improved core applications such as land-cover and land-use
classification,objectdetectioninhigh-resolutionimagery,semanticsegmentation,andpixel-levelchangedetection[ 12,
40,114].Inpractice,thisprogresswasdrivenbybothstrongermodelfamiliesandstrongerbenchmarks:aerialdetectors,
encoder-decoder segmenters, and temporal change models matured alongside datasets such as DOTA, DIOR, NWPU
VHR-10,xBD,FloodNet,andBigEarthNet[ 4,12,20,23,27,38,57,86,87,89,114,121].Asaresult,task-specificpredictive
models became the backbone of many operational remote sensing workflows. Yet their strength is also their limitation:
Author’s Contact Information: Muhammad Akhtar Munir, akhtar.munir@mbzuai.ac.ae, Mohamed bin Zayed University of Artificial Intelligence, Abu
Dhabi, UAE.
1
arXiv:2604.24919v3  [cs.CV]  1 Jun 2026
===== PAGE 2 =====
2 Munir et al.
they are designed for predefined tasks with fixed inputs and outputs, and therefore provide limited support for multi-
step reasoning, adaptive tool use, or dynamically evolving analytical goals.
Building on task-specific models, the field has shifted toward EO foundation models that learn transferable geospa-
tialrepresentationsfromlargeunlabeleddata.EarlyworkssuchasS2MAE,CROMA,SatMAE,MMEarth,andOmniSat
highlight the need to capture EO-specific structure, including spatial-spectral organization, cross-sensor alignment,
and multimodal or semantically guided pretraining [2, 24, 36, 59, 80, 117]. This line of work has since expanded to-
ward broader geospatial settings across modalities, resolutions, and sensors, including models such as Galileo, AnySat,
Copernicus-FM, TerraFM, TerraMind, and Prithvi-2 [3, 26, 39, 49, 60, 104, 109, 112, 118, 135]. Parallel efforts em-
phasize temporal robustness, multi-scale learning, spectral and geometric biases, and efficient long-sequence model-
ing[28,33,43,44,61,81,88,99,107,125],supportedbyincreasinglylargedatasetsandmultimodalbenchmarks[ 6,8,9].
Overall, this transition moves EO toward more general and transferable representations, but it remains primarily fo-
cused on representation learning rather than workflow-level reasoning.
Inparallel,vision-languagemodelsintroducedmultimodalarchitecturesthatconnectvisualperceptionwithnatural
language interaction and reasoning [55, 56], and were rapidly adapted to EO through models such as SkySenseGPT,
GeoChat, SkyEyeGPT, LHRS-Bot, EarthGPT, and Falcon, enabling captioning, VQA, instruction following, and conver-
sational interaction over satellite imagery [7, 45, 53, 62, 71, 78, 126, 132, 134]. This paradigm broadened EO interac-
tion from task-specific outputs to language-driven interpretation. At the same time, EO representation learning was
strengthened through large-scale image-text alignment and CLIP-style transfer, alongside unified multimodal models
that integrate heterogeneous inputs such as cross-sensor data and metadata [30, 47, 64, 74, 95, 100, 119, 122, 129, 136].
Fine-grained capabilities also advanced from region-level grounding to pixel-level reasoning and unified grounding-
segmentation pipelines [58, 83, 93, 96, 115, 127, 133, 139], supported by benchmarks for VQA, VLM evaluation, and
ultra-high-resolutionunderstanding[ 25,72,113].Despitetheseadvances,EOVLMsstilllargelytreatanalysisasinput-
output prediction rather than sequential, tool-grounded reasoning over geospatial state.
Alongside advances in foundation models and EO vision-language models, agentic AI has emerged as a broader
framework for problems that require sequential reasoning, adaptive decision making, and interaction with external
tools. Rather than producing a single prediction, agentic models operate over trajectories of actions and observations:
they decompose goals, select tools, execute intermediate steps, and use the resulting outputs to guide subsequent rea-
soning. Across the broader agent literature, frameworks such as ToolOrchestra and VerlTool study tool orchestration
andreinforcement-learning-basedtooluse,whileOpenThinkIMG,SpaceTools,OctoTools,andDeepEyesexplorevisual
toolcalling,multimodalactionpolicies,andlong-horizonperception-actionloops[ 15,50,69,102,103,120,137].Collec-
tively, these works establish core ingredients of agentic AI, including tool use, sequential control, and trajectory-level
optimization, but typically in settings where tools are relatively abstract and domain constraints are limited.
Within remote sensing and geospatial analysis, a first wave of work has begun to translate these ideas into more
realistic EO settings. Some efforts focus on benchmark and environment design, showing that geospatial agents must
operate over realistic APIs, map-based interfaces, and long-horizon user commands rather than simplified question-
answertemplates,asinGeoLLM-QA,GeoLLM-Engine,andUnivEARTH[ 52,97,98].Othersdevelopgeospatialcopilots
and agentic frameworks that combine tool orchestration with retrieval, state-driven workflows, map interaction, and
domain knowledge, including RS-Agent, MapAgent, ThinkGeo, OpenEarthAgent, Earth-Agent, and REMSA [11, 32,
41, 91, 92, 101, 123]. A further set of models targets domain-specialized interactive analysis, including comprehensive
changeinterpretationandgeologicmapunderstandingthroughcoordinatedperception,reasoning,andexternalknowl-
edge, as in Change-Agent and PEACE [46, 63]. Collectively, these works mark an important transition from predictive
===== PAGE 3 =====
Agentic AI for Remote Sensing: Technical Challenges and Research Directions 3
Evolution of AI in Remote Sensing T oward Agentic Models
T ask-Specific Models EO FMs EO VL-Models Agentic Models
Methods:General:Faster-
RCNN [89], YOLO [87], Unet [90],
DeepLabV3+ [14]... EO-Specific:
DOTA [121], ROI Transformer [27],
ChangeFormer [5], SiamCRNN [13],
UNetFormer [114]...
Datasets:DOTA [121], DIOR [57],
NWPU VHR-10 [18], xBD [38],
FloodNet [86]...
Capability:Automated EO percep-
tion, Strong supervised learning,
Task level prediction
Limitations:No workflow reason-
ing, No decision-making capability
Methods:General:MAE [42],
DINO versions [10]... EO-FMs:
Galileo [110], CROMA [36], AnySat
[3], Prithvi-2 [104], Copernicus-FM,
TerraFM [26]...
Datasets:Sentinel-1/2 [29]
archives, GeoBench [54], Coperni-
cus data [29]...
Capability:Transferable representa-
tions, Multi-sensor learning
Limitations:Predictive inference,
No analytical decision process
Methods:General:GPT 5 [82],
LLaVAOneVision [55], Flamingo
[1], Kosmos-2 [84], Qwen 3 [124],
InternVL [17]... EO-VLMs:Sky-
SenseGPT [71], RemoteCLIP [64],
GeoChat [53], EarthDial [100],
TEOChat [47]...
Datasets:RSVQA [67], EarthDial
[100], GeoChat [53], UCM-Captions
[70], GeoBench-VLM [25]...
Capability:Natural language in-
teraction, Query-able geospatial
imagery, Multimodal grounding
Limitations:No persistent reason-
ing, No tool execution
Methods:General:ToolOrchestra
[102], VeriTool, TAPO [120], Open-
ThinkIMG [103], Agent-VL, ReAct
[128]... EO-Specific:ThinkGeo [91],
Earth-Agent [32], OpenEarthAgent
[92]...
Datasets:ThinkGeo [91], Earth-
Agent [32], OpenEarthAgent [92]...
Capability:Sequential reason-
ing, Tool orchestration, Decision-
oriented models
Limitations:Generic assumptions
fail in EO
Fig. 1. Evolution of AI paradigms in remote sensing toward agentic models. The field has progressed from task-specific predictive
models to EO foundation models, EO vision-language models, and emerging agentic frameworks. Each stage expands the capability
space from automated perception and transferable representation learning to language-grounded interaction and sequential tool
use. At the same time, this progression exposes a mismatch between generic agentic assumptions and EO workflow constraints,
motivating agentic models that reason over geospatial state, tool effects, and validity rather than final predictions alone.Drawings
from ChatGPT.
EO models toward workflow-aware geospatial reasoning. At the same time, they remain early steps: current models
are still limited in coverage, robustness, and validation, and they expose how far EO agents remain from geo-valid
and scientifically accountable long-horizon analysis. Figure1 summarizes this progression from task-specific predic-
tive models to foundation models, vision-language models, and emerging agentic frameworks, while also highlighting
where the mismatch between generic agentic assumptions and EO workflow realities begins to emerge.
ç An EO agent is a geospatial state updater.It selects parameterized tools, modifies structured EO state,
and must preserve geospatial and physical validity across intermediate transitions.
1.2 Why Agentic AI Requires Reconsideration in Remote Sensing
At first glance, agentic AI appears well aligned with EO workflows: both involve multi-step reasoning, tool use, and
sequential decision-making [15, 50, 103, 120]. However, many current agentic frameworks and benchmarks are devel-
oped in environments where tools behave like predictable functions, actions are largely recoverable, and errors can
often be detected before they substantially affect later steps [65, 102, 103]. Under these assumptions, supervision and
reward signals remain relatively stable because intermediate mistakes are often easier to identify or correct.
EO workflows break these assumptions in important ways. They operate over georeferenced, multi-modal, and
temporally structured data, and they rely on transformations suc
