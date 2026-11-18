# 2609.12533v1.pdf

- Category: Agentic
- Pages: 18
- Path: D:\RS\Thesis\New_papers\Agentic\2609.12533v1.pdf

## Metadata

```json
{
  "/Author": "Zhutao Lv; Chenhao Dang; Yi Feng; Yanpei Gong; Xiaolei Wang; Junyan Ye; Conghui He; Weijia Li",
  "/Creator": "arXiv GenPDF (tex2pdf:0d14211)",
  "/DOI": "https://doi.org/10.48550/arXiv.2609.12533",
  "/License": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
  "/PTEX.Fullbanner": "This is pdfTeX, Version 3.141592653-2.6-1.40.28 (TeX Live 2025) kpathsea version 6.4.1",
  "/Producer": "pikepdf 8.15.1",
  "/Title": "Earth-Agent-Pro: Towards Real-World Full-Chain Earth Observation with Agents",
  "/Trapped": "/False",
  "/arXivID": "https://arxiv.org/abs/2609.12533v1"
}
```

## First pages


===== PAGE 1 =====
1
Earth-Agent-Pro: Towards Real-World Full-Chain
Earth Observation with Agents
Zhutao Lv1,2, Chenhao Dang 3,4* , Yi Feng 5* , Yanpei Gong6* , Xiaolei Wang2,
Junyan Ye2, Conghui He 4, Weijia Li1,4†
1Tsinghua Shenzhen International Graduate School, Tsinghua University, 2Sun Yat-Sen University,
3Shanghai Jiao Tong University, 4Shanghai Artificial Intelligence Laboratory,
5Tianjin University, 6Harbin Institute of Technology
Abstract—Real-world Earth observation (EO) analysis requires
agents to be capable of translating high-level scientific questions
into executable workflows for acquiring observations, preparing
data, performing domain computations, and deriving conclusions
from runtime evidence. However, existing EO agents and bench-
marks generally cover only part of this chain: agents typically
start from supplied observations, whereas benchmarks typically
provide prepared inputs or candidate answers, leaving full-chain
open-world EO execution largely untested. We present Earth-
Agent-Pro, an execution-adaptive Plan-and-Execute framework
that uses expert-authored skills to constrain workflow planning
and runtime tool use. It records planned steps, accepted evidence,
and their dependency links in workflow-centered structured
memory, then repairs only the affected workflow suffix when
runtime evidence invalidates a step. Role-specific training adapts
the underlying large language model (LLM) through separate
planner and executor adapters: sequence-level supervised fine-
tuning targets planner workflow composition, while node-level
group relative policy optimization with locally verifiable rewards
targets executor tool-argument grounding. To evaluate full-chain
open-world EO execution, we introduce Earth-Bench-Pro, a 744-
question EO agent benchmark that instantiates 248 expert-
curated task cores under three matched regimes. Across RGB
imagery, spectral observations, and remote sensing products, its
248 Open-World Execution questions pair high-level requests
with runtime data requirements, executable trajectories, and
open-ended answers grounded in execution evidence. Under a
shared GPT-5 backbone, Earth-Agent-Pro reaches 66.13% LLM-
as-Judge accuracy, outperforming ReAct by 20.95 points in LLM-
as-Judge accuracy and 24.44 points in Tools-In-Order. Jointly
tuning the Planner and Executor adapters raises Qwen3.5-9B
LLM-as-Judge accuracy from 38.31% to 50.00%, an 11.69-point
gain over the untuned configuration. Planning-only evaluation
and execution with the reference workflow further show that the
adapters improve workflow composition and argument ground-
ing, respectively. In conclusion, Earth-Bench-Pro and Earth-
Agent-Pro support evaluation and training of EO agents from
user requests to evidence-grounded scientific answers. The code
and datasets of this work will be released soon.
Index Terms—Earth observation, remote sensing agents, open-
world execution
I. INTRODUCTION
Earth observation (EO) turns satellite and aerial measure-
ments into quantitative evidence for agricultural monitoring,
disaster assessment, urban analysis, and environmental change
research [1]–[15]. Producing such evidence from an EO ques-
tion remains expert-intensive [16]–[18]. An EO analysis begins
*Equal contribution. †Corresponding author.
by matching the target phenomenon, region, and period to
suitable observations. Analysts then choose the data source,
product, bands, and sampling parameters before acquiring and
preprocessing the data. The prepared observations enter a
domain-specific computation pipeline that yields the requested
scientific quantities. Completing this workflow requires ex-
pertise in sensors, data products, geospatial processing, and
domain science, which raises the entry barrier for users outside
the EO community and limits access to reproducible analysis.
Recent work has expanded EO capabilities beyond inter-
preting supplied observations to include multistep analysis
execution. Vision-language models interpret supplied images
and image sequences [19]–[21], while tool-augmented agents
select operations, execute code, and construct multistep work-
flows [22]–[26]. Benchmarks now span fixed-input question
answering, multistep geographic information system (GIS)
tool use, and open-environment pipeline construction [27]–
[30]. Together, these methods and benchmarks cover more
of the request-to-answer chain, but evaluations differ in their
scientific tasks, input assumptions, and answer formats. Mea-
suring progress toward autonomy therefore requires a matched
evaluation that removes expert scaffolding while keeping the
scientific objective fixed.
Our prior Earth-Agent and Earth-Bench provide the task and
evaluation foundation for this comparison [31]. Earth-Agent
connects a language model to EO tools through the Model
Context Protocol, while Earth-Bench evaluates final answers
and reference trajectories across red-green-blue (RGB) im-
agery, spectral observations, and remote sensing products. This
pairing evaluates both the scientific result and the execution
path. Earth-Bench, however, begins with expert-prepared local
inputs and multiple-choice questions, leaving runtime data
discovery and open-ended answer generation outside its eval-
uation boundary. We build on this foundation by preserving
each of Earth-Bench’s 248 scientific objectives as a fixed
task core and moving runtime data discovery, acquisition, and
open-ended answer generation into the evaluated workflow.
The resulting request-to-answer setting, which we callopen-
world EO execution, starts from a request that specifies
a phenomenon, region, and period. The agent must locate
runtime inputs, acquire suitable observations when required,
prepare them, perform domain computations, and derive an
answer from runtime evidence. Files, intermediate artifacts,
and tool results appear only during execution, so later op-
arXiv:2609.12533v1  [cs.CV]  11 Sep 2026
===== PAGE 2 =====
2
Existing EO BenchmarksQ: Calculate the distance between A and B.(A) 0m   (B) 30m(C) 80m (D) 200mMultiple ChoicePick from  optionsEasier
The distance between A and B is 79.95 meters.Open-ended
No reference optionsMuch HarderDrawbacks1. Data acquisition is skipped2. Answers are reduced to multiple choice3. Actual numeric/date/unit errors can be hidden4. Has a gap from the real-world EO needs
Pre-collected dataSameWorkflowExisting EO AgentsLocal ToolsExternal Knowledge
Tool ATool BTool CAnswerTool DTool BDrawbacks1. Tool selection lacks systematic constraints2. Planning paths become redundant or indirect3. General-purpose models lack EO-specialized trainingOurs (Earth-Bench-Pro & Earth-Agent-Pro)744 expert-curated open-ended tasks
IntroduceData Download
Search Data Source
Download Series
ExtraGeneratedData for Model TrainingSkill-guided Agent?
Open EO task
Planner
Skill 1Skill 2Skill 3Skill n…WorkflowExecutor
Lightweight 
Model
Advantages1. Open-world benchmark with open-ended EO tasks2. Skill-guided agent for full-chain EO workflows3. Trained lightweight agent for planning and execution
Answer
Unrestricted tools / informationEarth-Bench-ProEarth-Agent-Pro!Redundant Path
Fig. 1.Overview of our work.Existing EO benchmarks rely on pre-collected data and multiple-choice evaluation, while existing EO agents suffer from
unconstrained tool use and redundant planning. Our work introduces an open-ended EO benchmark (Earth-Bench-Pro) and a trained skill-guided agent (Earth-
Agent-Pro) for full-chain EO task planning and execution.
010203040506070
OursGEMMA-4(E4B-it)Mistralai-v03-7BInternLM3-8BQwen3.5-9BLlama-33-70B-InstructGPT-oss-120b
Score (%)Instruction FollowingAutonomous PlanningOpen-World Execution
Fig. 2. LLM-as-Judge accuracy across Earth-Bench-Pro’s three regimes.Ours
is our role-specialized Qwen3.5-9B.
erations depend on accepted upstream evidence. The agent
must track workflow dependencies, ground each operation in
the evolving state, and revise affected future operations when
evidence invalidates the current plan.
We developEarth-Bench-ProandEarth-Agent-Proas
a paired benchmark and agent for open-world EO execu-
tion. Earth-Bench-Pro holds each scientific objective fixed
across matched regimes that progressively remove the refer-
ence workflow and prepared inputs. Earth-Agent-Pro separates
workflow planning from runtime operation grounding and
constrains both stages with expert-authored skills. Workflow-
centered structured memory links pending operations to ac-
cepted evidence, allowing the agent to preserve a valid prefix
and repair only an invalidated workflow suffix. The training
pipeline specializes the Planner for workflow composition and
the Executor for runtime argument grounding.
Earth-Bench-Pro exposes a consistent difficulty gap: Open-
World Execution remains the hardest regime across backbones
(Figure 2). On Earth-Bench-OW, with a shared GPT-5 back-
bone, tool set, and skill set, Earth-Agent-Pro reaches 66.13%
accuracy under a large language model (LLM) judge, 20.95
percentage points above ReAct, and leads ReAct by 24.44
points on Tools-In-Order. Combining the Planner and Executor
adapters raises Qwen3.5-9B LLM-as-Judge accuracy by 11.69
points; planning-only and oracle-plan evaluations separately
measure workflow composition and argument grounding.
Our contributions are:
•Open-world execution task and benchmark.We for-
mulate open-world EO execution and operationalize it
with 248 Open-World Execution questions in Earth-
Bench-Pro. Product and Spectrum tasks require runtime
observation acquisition and preparation, and all questions
require open-ended answers grounded in execution evi-
dence. Together with 496 matched Instruction-Following
and Autonomous-Planning questions, the released suite
contains over 700 evaluation questions.
•Open-world EO agent framework.Earth-Agent-Pro
uses expert skill guidance to constrain workflow con-
struction and runtime tool use, while its execution-
adaptive dynamic workflow maintains the plan, accepted
evidence, and their dependencies. Under a shared back-
bone, tool set, and skill set, Earth-Agent-Pro outperforms
ReAct, AFlow, and OpenEarthAgent on final-answer and
workflow-order metrics in controlled comparisons.
•Dependency-preserving data and role training.From
248 seed workflows, we construct 2,480 dependency-
preserving trajectories and combine them with examples
from the public OpenEarthAgent training set [25] to form
a balanced mixture for Planner SFT and Executor GRPO.
Combining the two adapters raises Qwen3.5-9B LLM-as-
Judge accuracy by 11.69 points on Earth-Bench-OW.
II. RELATEDWORK
A. Earth Observation Benchmarks and Datasets
Earth observation (EO) datasets provide perception and
multimodal evaluation on fixed inputs [32]. RSVQA [27] and
VRSBench [28] assess visual question answering; GeoBench-
VLM [33] and CHOICE [34] evaluate geospatial multimodal
===== PAGE 3 =====
3
Task uses136
1980 1990 2000 2010 2020 2025
Relative task density: lower - higher(b) Global Spatiotemporal&Temporal CoverageProduct Stats.Spectral IndexThermal Retr.BT Temp.Time-SeriesRGB Perception
Agriculture &
Drought
Urban &
Infrastructure
Water & Marine
Vegetation &
Ecosystems
Cryosphere & Snow
Atmosphere &
Climate
Hazards &Disasters
Land Cover &
Object Mapping
Lower share Higher shareApplication domain
(a) Benchmark Composition
Fig. 3.Earth-Bench-Pro Overview.(a) Task composition across application domains and task families. (b) Global spatial distribution and temporal coverage.
capabilities; VLEO-Bench [35], XLRS-Bench [36], URBench
[4], DisasterM3 [37], and TerraScope [21] extend evaluation to
fine-grained, ultra-high-resolution, urban, disaster, and pixel-
grounded reasoning. These benchmarks mainly score final
outputs rather than agent interactions, tool-use trajectories, or
intermediate artifacts. Complementary EO benchmarks target
specific agentic operations: RescueADI [38] evaluates se-
quential disaster interpretation; GeoLLM-Engine [39] provides
analyst-style API and interface interactio
