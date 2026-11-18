# 2505.23752v3.pdf

- Category: Agentic
- Pages: 14
- Path: D:\RS\Thesis\New_papers\Agentic\2505.23752v3.pdf

## Metadata

```json
{
  "/Author": "Akashah Shabbir; Muhammad Akhtar Munir; Akshay Dudhane; Muhammad Umer Sheikh; Muhammad Haris Khan; Paolo Fraccaro; Juan Bernabe Moreno; Fahad Shahbaz Khan; Salman Khan",
  "/Creator": "arXiv GenPDF (tex2pdf:a6404ea)",
  "/DOI": "https://doi.org/10.48550/arXiv.2505.23752",
  "/License": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
  "/PTEX.Fullbanner": "This is pdfTeX, Version 3.141592653-2.6-1.40.28 (TeX Live 2025) kpathsea version 6.4.1",
  "/Producer": "pikepdf 8.15.1",
  "/Title": "ThinkGeo: Evaluating Tool-Augmented Agents for Remote Sensing Tasks",
  "/Trapped": "/False",
  "/arXivID": "https://arxiv.org/abs/2505.23752v3"
}
```

## First pages


===== PAGE 1 =====
ThinkGeo
 : Evaluating Tool-Augmented Agents for Remote Sensing Tasks
Akashah Shabbir1* Muhammad Akhtar Munir1* Akshay Dudhane1*
Muhammad Umer Sheikh1 Muhammad Haris Khan1 Paolo Fraccaro2
Juan Bernabe Moreno2 Fahad Shahbaz Khan1,3 Salman Khan1,4
1Mohamed bin Zayed University of AI, 2IBM Research, 3Link¨oping University, 4Australian National University
/g♀behttps://github.com/mbzuai-oryx/ThinkGeo
Abstract
Recent progress in large language models (LLMs) has en-
abled tool-augmented agents capable of solving complex
real-world tasks through step-by-step reasoning. However,
existing evaluations often focus on general-purpose or mul-
timodal scenarios, leaving a gap in domain-specific bench-
marks that assess tool-use capabilities in complex remote
sensing use cases. We presentThinkGeo, an agentic bench-
mark designed to evaluate LLM-driven agents on remote
sensing tasks via structured tool use and multi-step planning.
Inspired by tool-interaction paradigms, ThinkGeo includes
human-curated queries spanning a wide range of real-world
applications such as urban planning, disaster assessment
and change analysis, environmental monitoring, transporta-
tion analysis, aviation monitoring, recreational infrastruc-
ture, and industrial site analysis. Queries are grounded
in satellite or aerial imagery, including both optical RGB
and SAR data, and require agents to reason through a di-
verse toolset. We implement a ReAct-style interaction loop
and evaluate both open and closed-source LLMs (e.g., GPT-
4o, Qwen2.5) on 486 structured agentic tasks with 1,778
expert-verified reasoning steps. The benchmark reports both
step-wise execution metrics and final answer correctness.
Our analysis reveals notable disparities in tool accuracy and
planning consistency across models. ThinkGeo provides the
first extensive testbed for evaluating how tool-enabled LLMs
handle spatial reasoning in remote sensing.
1. Introduction
Recent advances in LLMs have enabled the emergence of
tool-augmented agents, systems that can break down com-
plex tasks into step-by-step plans, invoke external tools (e.g.,
vision modules, calculators, and code interpreters), and rea-
*Equal Contribution
Benchmark RealqueriesDeployedtools MMinputsAnnotationchainsExecutioneval. RSimages
API-Bench [23] ✗ ✗ ✗ ✗ ✗ ✗ToolBench [24] ✗✓✗ ✗ ✗ ✗GAIA [21] ✓✗✓✗✓✗APIBank [18] ✗✓✗✓✗ ✗m&m’s [20] ✗✓ ✓ ✓ ✓✗GTA [29] ✓ ✓ ✓ ✓ ✓✗ThinkGeo (Ours) ✓ ✓ ✓ ✓ ✓ ✓
Table 1. Comparison of agentic benchmarks across key dimensions.
ThinkGeo is the only benchmark designed specifically for remote
sensing (RS), incorporating real EO imagery alongside ReAct-style
annotation chains and deployed tools. It uniquely supports spatial
reasoning and remote sensing-specific tasks through geospatial
grounded inputs and execution-level evaluation for studied models.
son across intermediate states [ 27, 36]. This paradigm,
popularized via ReAct-style frameworks [ 36], has shown
promise in general-purpose settings through benchmarks
like ToolBench [24], GAIA [21], and GTA [29], which eval-
uate agents on procedural correctness, tool use, and final
task outcomes. However, these benchmarks largely focus on
synthetic, open-domain, or web-grounded scenarios, leav-
ing the question of agentic capability in precision-critical,
spatially grounded domains, like remote sensing, largely un-
explored. Remote sensing (RS) is critical to a wide range
of applications, including environmental monitoring, urban
infrastructure and transportation analysis, disaster response,
and land-use mapping, with an ever-growing stream of high-
resolution imagery from earth observation (EO) satellites
and drones [ 15]. Despite advances in visual models for
detection, segmentation, and change analysis, current pro-
cessing pipelines remain brittle and manually engineered
across tasks. Integrating these capabilities into LLM-driven
agents demands reasoning over geodetic metadata, spatial
resolutions, temporal dynamics, and unit-aware calculations.
Existing agentic benchmarks (e.g., GTA [29], GAIA [21])
do not address these demands; they are built around general-
arXiv:2505.23752v3  [cs.CV]  2 Apr 2026
===== PAGE 2 =====
35.7%
Football stadium
User Queries
TextToBbox
ReActbased Reasoning/Execution Chain
Answer
Identify the type and color of all visible cars in the image. Cars àbounding boxes Blue MinivanWhite Sedan
RegionDescriptionDescription àType & color of vehicle
The white house in northwest corner of the image is flooded or not? is there any water around 10m radius of the house? GSD 0.015m/px.
House in northwest corner àBBox FloodedYesBBoxexpansion by 10m
Presence of water
Detect any markings in the image and give information about the facility, is it tennis court or football stadium?Image àBboxes& text “CenturylinkField”
OCR
 GoogleSearch
Detect the construction waste and draw a bounding box over it. Draw Bboxon Image
Construction waste àBBox
DrawBox
What percentage of buildings in the post image were completely destroyed?
 ChangeDet
Pre How many damaged buildings àBuilding countCompute %
10642.72 m sq, 46957.28 m sq
Calc
 Compute GSD area​ Assume GSD is 0.4 m/px. Detect all houses in the image and compute their total built-up area in square meters versus the remaining open space in the 600x600 image.
Post
ChangeDet
TextToBbox
TextToBbox
TextToBbox
Calc
 Calc
RegionDescription
Bboxà# pixelsHouses àBbox
Calc
Total #pixel –# BBoxpixel
How many buildings were destroyed àBuilding count
NoIs there any land between the 3 ships? Compute new box, expanded àBbox
Check land in new bboxàhas land?Detect all ships àBboxTextToBbox
 RegionDescription
Solver
Figure 1. Representative samples from the ThinkGeo benchmark. Each row illustrates a user query grounded in real RS imagery, followed
by a ReAct-based execution chain comprising tool calls and reasoning steps, and concludes with the resulting answer. The examples span
diverse use cases, including transportation analysis, urban planning, disaster assessment and change analysis, recreational infrastructure, and
environmental monitoring, highlighting multi-tool reasoning and spatial task complexity.
purpose or web-grounded images, lacking the spatial fidelity
and grounding required for geospatial workflows. Conse-
quently, there is a pressing need for a benchmark that evalu-
ates tool-augmented agents in remote sensing contexts, for
reasoning over real EO imagery, coordination of general-
purpose visual tools, and handling spatially grounded multi-
step tasks. In this work, we introduceThinkGeo, the first
agentic benchmark specifically designed to evaluate tool-
augmented LLM agents on realistic remote sensing tasks.
As shown in Table 1, unlike existing agentic benchmarks
built on general or web-grounded images,ThinkGeo focuses
on spatially grounded reasoning, requiring agents to plan
and execute multi-step workflows using satellite and aerial
imagery. Each query is coupled with an executable tool en-
vironment and annotated with structured evaluation signals,
enabling rigorous assessment of perception, planning, and
geospatial reasoning under tool-based execution constraints.
Our main contributions are as follows:
• Task Suite & Dataset:A curated set of 486 agentic tasks
with 1,778 expert-verified reasoning steps over medium
to high-resolution optical RGB (436 tasks) and SAR (50
tasks) images, spanning urban, environmental, transporta-
tion, aviation, industrial, change detection, and disaster-
related scenarios. Examples are shown in Fig 1.
• Executable Tool Set:An extended suite of 14 tools
designed to simulate real-world RS workflows. This
includes perception modules (e.g., ObjectDetection,
SegmentObjectPixels, ChangeDetection),
logic and numeric tools (e.g., Calculator, Solver,
Plot), and visualization aids (e.g., DrawBox,
AddText).
• Evaluation Protocol:We propose two evaluation modes,
step-by-step and end-to-end, paired with fine-grained met-
rics to assess instruction adherence, tool use correctness,
argument formatting, multi-step reasoning, and final an-
swer accuracy.
• Benchmarking Study:A comparative evaluation of
state-of-the-art LLM agents, including GPT-4o, Claude-
3, Qwen-2.5, and LLaMA-3, revealing persistent gaps in
multimodal tool reasoning and execution trace alignment,
even among top-performing models.
By grounding agentic evaluation in real EO imagery
===== PAGE 3 =====
and requiring interpretable, tool-based interaction tracking,
ThinkGeo provides a new foundation for benchmarking and
ultimately providing insights to improving spatially-aware,
tool-augmented LLM agents for geospatial analysis.
2. Related Work
Tool-augmented LLM Agents and Benchmarks:Integrat-
ing large language models (LLMs) with executable tools has
recently become a central focus in agent research. Early
work presented tool use as an alternating planning and ex-
ecution. ReAct, for instance, interleaves ”thought” tokens
with structured tool calls, enabling a single LLM to both
reason and act [ 36]. Subsequent systems generalized this
idea to larger tool repertoires. HuggingGPT employs a GPT
controller to select from hundreds of vision, speech, and lan-
guage models exposed as functions [27], while Visual Chat-
GPT and MM-ReAct demonstrate analogous pipelines for
multimodal perception tasks [31, 35]. To measure tool-use
proficiency, several benchmarks have been proposed. Tool-
Bench, APIBench, and API-Bank evaluate single-step API
invocation within synthetic prompts [ 18, 23, 24]; m&m’s
extends this to multi-step multimodal settings [20]. More re-
cently, GAIA [21] and GTA [29] introduced human-written,
step-implicit tasks paired with executable tool chains, reveal-
ing substantial performance gaps: GPT-4 completes fewer
than half of GTA queries once real tools and intermediate
checks are enforced. MLGym casts the agent problem into
a Gym environment for open-ended AI-research workflows,
highlighting long-horizon planning and code execution and
also without geospatial imagery [22].
Remote Sensing Agents:Recent efforts to extend LLM
agents into EO have produced diverse tool-augmented
pipelines, yet planning transparency, and step-level reason-
ing fidelity remain limited. Remote Sensing ChatGPT [ 9]
and RS-Agent [34] represent early vision-language pipelines
that chain pretrained detectors, segmenters, and geospatial
utilities under GPT-based planners. However, they typically
report only final answer accuracy, omitting structured ReAct-
style trace evaluation or step-wise error attribution. TreeGPT
and GeoMap-Agent [7, 11] introduce domain-specific agents
for forestry and geological mapping, respectively. While
these systems operate over visual maps and structured vi-
sual inputs, they rely on template-grounded or qualitative
responses and do not implement formal multi-step evalu-
ation. UnivEARTH [ 15], by contrast, employs a purely
language-based framework that requires LLMs to generate
valid Google Earth Engine (GEE) code, revealing that over
58% of completions fail to execute and that even the best
agents answer only around 33% of geospatial queries cor-
rectly. Together, these works suggest that while EO agents
can interface with rich toolsets, failures in tool selection,
argument grounding, and spatial unit reasoning persist, un-
derscoring the need for benchmarks that explicitly evaluate
tool-level correctness alongside geospatial task outcomes.
Evaluation Protocols:Early benchmarks for tool-
augmented LLMs, such as ToolBench [24], APIBench [23],
and API-Bank [18], primarily evaluate single-step tool usage
in synthetic or isolated API call settings. While useful for
measuring basic tool and argument prediction, these setups
lack support for multi-tool planning, intermediate tracking,
or long-horizon reasoning. To address these limitations, GTA
[29] presents a tightly scoped yet richly instrumented bench-
mark requiring sequential tool usage across perception, logic,
operation, and generation modules. GTA adopts a ReAct-
style interface and introduces 
