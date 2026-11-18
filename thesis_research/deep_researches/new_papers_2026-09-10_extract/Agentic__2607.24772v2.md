# 2607.24772v2.pdf

- Category: Agentic
- Pages: 18
- Path: D:\RS\Thesis\New_papers\Agentic\2607.24772v2.pdf

## Metadata

```json
{
  "/Author": "Bingxian Wu; Yu Zhang; Zonghao Guo; Tang Liu; Chen Qian; Yuxiang Lu; Xingbo Du; Yanghao Li; Yidan Zhang; Chi Chen; Ling Yao; Maosong Sun",
  "/Creator": "arXiv GenPDF (tex2pdf:4af3385)",
  "/DOI": "https://doi.org/10.48550/arXiv.2607.24772",
  "/License": "http://creativecommons.org/licenses/by/4.0/",
  "/PTEX.Fullbanner": "This is pdfTeX, Version 3.141592653-2.6-1.40.28 (TeX Live 2025) kpathsea version 6.4.1",
  "/Producer": "pikepdf 8.15.1",
  "/Title": "RSMeM: Knowledge-Enhanced Memory Evolution for Remote Sensing Agents with Systematic Evaluation",
  "/Trapped": "/False",
  "/arXivID": "https://arxiv.org/abs/2607.24772v2"
}
```

## First pages


===== PAGE 1 =====
RSMeM: Knowledge-Enhanced Memory Evolution for Remote Sensing
Agents with Systematic Evaluation
Code: GitHub•
 Demo: ModelScope Studio
Bingxian Wu1,3*, Yu Zhang2*, Zonghao Guo2† , Tang Liu1, Chen Qian1,3, Yuxiang Lu4,
Xingbo Du6,Yanghao Li 2,Yidan Zhang 3,5,Chi Chen 2,Ling Yao 3,Maosong Sun 2
1Institute of Geographic Sciences and Natural Resources Research, CAS 2Tsinghua University
3University of Chinese Academy of Sciences 4China University of Geosciences, Beijing
5Aerospace Information Research Institute, CAS 6Shanghai Jiao Tong University
wubingxian24@mails.ucas.edu.cn, guozonghao96@outlook.com
Abstract
Geoscience research requires complex analy-
sis and domain expertise, with remote sens-
ing (RS) observations as a key foundation.
However, existing RS agents built on general-
purpose LLMs remain largely domain-agnostic,
resulting in brittle and error-prone workflows.
Moreover, these failures are seldom consoli-
dated into a reusable experience for subsequent
analyses. To address this issue, we introduce
RSMeM, a knowledge-enhanced memory evo-
lution mechanism that bootstraps RS agents
with pre-distilled domain knowledge and it-
eratively integrates online experience for ro-
bust multi-step tool execution. RSMeM is
composed of two components: (i) Hierarchi-
cal Knowledge Grounding, which performs
taxonomy-aware retrieval over a hierarchical
domain corpus to guide planning and tool se-
lection; and (ii) Failure-Aware Experience Re-
finement, which distills failure-annotated tool-
use traces into reusable constraints for next-
round tool execution. By iteratively employing
these two processes, RS agents can evolve to
absorb task-level domain knowledge and effec-
tively translate it into instance-level execution
experience. Extensive experiments on Earth-
Bench demonstrate that RSMeM consistently
improves tool-use performance and end-to-end
answer across a diverse set of LLM backbones.
Notably, RSMeM achieves a 6% accuracy im-
provement on DeepSeek-V3.2 with less than
1% additional experience tokens, demonstrat-
ing the strong knowledge density of our dis-
tilled experience.
1 Introduction
Advances in large language models (LLMs) and
tool-augmented agents have demonstrated promis-
ing capabilities in task planning, reasoning, and ex-
ternal tool use (Su et al., 2024; Tang et al., 2025). In
*Equal contribution
†Corresponding authors
（c） Agents w/ Evolving RSMeM (Ours)
User
Query
Evolving
RSMeM
Execute & Reflect 
Higher success on complex RS Tasks
Retrieval Guidance & Experience
Domain
Guidance
Instance-level
Experience
Iterative Retrieval & Reflection Cycle 
• Low marginal cost: Memory grows automatically
• Better generalization: reusable guidance + experience
• Iterative learning across trials
Update
（b） Agents w/ RS-Workflow  (e.g., RS-Agent )
User
Query
Retrieval Expert 
Templates 
Workflow stitched 
into prompt 
High Expert Curation Cost
Low Flexibility
Quality Depends on Expert Templates
Works When Templates Match
（a）Agents w/o Domain Knowledge
User
Query
Empty
LLM + Tools
No reusable RS domain Memory 
Lack of Domain Memory
Brittle on complex RS workflows
Figure 1: Comparison of RS agent architectures. (a)
Agents w/o Domain Knowledge lack reusable mem-
ory, leading to brittle workflows. (b) Agents w/ RS-
Workflow rely on static expert templates, which are
inflexible and costly to curate. (c) Agent w/ Evolving
RSMeM (Ours) integrates hierarchical grounding with
failure-aware reflection, enabling iterative knowledge
evolution and robust execution for complex RS tasks.
parallel, geoscience research has witnessed grow-
ing interest in deploying RS agents (Xu et al.,
2025a; Shabbir et al., 2025; Feng et al., 2025) for
in-depth analysis of remote sensing imagery.
One line of RS agents (Shabbir et al., 2025; Feng
et al., 2025) leverages general-purpose LLMs with
ReAct-style tool-use to perform multi-step analy-
sis. Yet, because these agents are largely domain-
agnostic, they often struggle with domain-specific
concepts (e.g., NDVI, BSI or land-surface tem-
perature interactions), which makes their tool-use
trajectories brittle and prone to cascading errors,
such as premature termination or incorrect tool in-
vocation, shown in Fig. 1(a). The other paradigm
adopts semi-automated, expert-authored solution
arXiv:2607.24772v2  [cs.AI]  22 Aug 2026
===== PAGE 2 =====
templates or workflow programs (Xu et al., 2025a;
Chen et al., 2025) to guide LLMs planning and
tool-calling, as shown in Fig. 1(b). While effective
for narrowly scoped tasks, such workflow-centric
designs are labor-intensive to construct and main-
tain. Moreover, these task-specific procedural de-
tails largely serve as external references, rather than
enabling the agent to internalize corrections from
execution failures and improve its behavior over
time.
To enable agents to learn from mistakes on con-
crete tasks, prior work has explored reflection-
driven improvements (Shinn et al., 2023; Zhang
et al., 2025b; Fang et al., 2025; Zhang et al., 2025a).
However, in geoscience settings, reflection alone
is limited, as agents without domain knowledge
often misdiagnose failures and fail to turn errors
into procedural fixes.
To tackle this challenge, we present RSMeM,
a memory-evolution framework that seeds RS
agents with pre-distilled domain knowledge and
continually incorporates online experience to en-
able robust multi-step tool execution, shown in
Fig. 1(c). Following prior task taxonomies in geo-
science (Kucharczyk and Hugenholtz, 2021; Ma
et al., 2024; Yuan et al., 2020; Ma and Mei, 2021),
we construct a set of geoscience knowledge cor-
pus that covers 3 application domains, 12 subdo-
mains and 64 task formulations. We further re-
fine the corpus with manual, professional feed-
back to form a distilled knowledge base for boot-
strapping RSMeM. RSMeM comprises two pro-
cesses.(i) Hierarchical Knowledge Grounding
conducts taxonomy-aware retrieval over a hierar-
chical corpus by encoding each knowledge item
into retrievable units (keywords, task definitions,
and semantic embeddings) and conditioning re-
trieval on the user query to inform LLM plan-
ning and tool selection.(ii) Failure-Aware Ex-
perience Refinementleverages a failure-critique
environment to identify erroneous tool-use trajec-
tories and distill them into reusable constraints
that are stored as experience memory. By iter-
ating between knowledge grounding and experi-
ence refinement, RSMeM injects both retrieved
knowledge and failure-derived constraints into sub-
sequent planning and tool invocation, enabling RS
agents to progressively acquire instance-level exe-
cution competence from task-level domain knowl-
edge. Extensive experiments on EarthBench (Feng
et al., 2025) demonstrate that RSMeM consistently
improves tool-use performance and end-to-end an-
swer quality across diverse LLM backbones, in-
cluding DeepSeek V3.2 (DeepSeek-AI et al., 2025),
Kimi-K2 (Team et al., 2025), Qwen3-32B (Yang
et al., 2025) and Qwen3-8B (Yang et al., 2025). No-
tably, RSMeM yields a 6.07% absolute accuracy
improvement on DeepSeek-V3.2 with less than
1% additional experience tokens, whose efficiency
arises from its ability to distill raw execution traces
into high-density, reusable geoscience expertise.
Rather than relying on resource-intensive context
expansion, RSMeM prioritizes the synthesis of op-
timized workflow experiences, ensuring a superior
performance-to-cost ratio for complex earth obser-
vation tasks.
We further observe that stronger backbones ben-
efit more from RSMeM, as they exhibit greater
capacity to summarize domain knowledge and di-
agnose execution errors, surfacing domain-level
corrections during iterative refinement.
We summarize our contributions as follows:
• We propose a taxonomy-driven construction
and retrieval scheme for structured geoscience
knowledge, enabling RS agents to ground
their reasoning in domain taxonomy thereby
perform more reliable geoscience inference.
• We propose a knowledge-enhanced memory
evolution framework to iteratively couple
knowledge grounding with failure-aware ex-
perience refinement, enabling RS agents to
transform domain knowledge into reusable
execution experience.
• We propose RSMeM, a plug-and-play frame-
work that can be seamlessly applied to diverse
LLM backbones and consistently improves
both tool-use and end-to-end performance on
challenging remote sensing tasks.
2 Related Works
Remote Sensing Agents.Recently, agent-based
Earth observation research has gained significant
attention (Luo et al., 2025; Kim et al., 2025).
Tool-augmented agents excel in tasks such as
code generation (Huang et al., 2024), multi-app
collaboration (Wang et al., 2024), and video
understanding (Fan et al., 2024); however, their
application in Earth observation remains in its
infancy (Kao et al., 2025a). Early works, such
as Change-Agent (Liu et al., 2024), focused on
bi-temporal remote sensing change detection. In
contrast, RS-ChatGPT (Guo et al., 2024) and
===== PAGE 3 =====
A.Offline:Knowledge Base Construction C.Online：Iterative Experience Refinement
User Query(q) Failure-Aware Memory Retrieval(if any)
3 Domains →12Subdomains→64TasksGeoscience Literature /expert curation
TaskCards
StreamA(from KB)
RSMeM
Hierarchical KB(static,offline)
Failure-AwareMemory(dynamic,online)StreamB(from FAM) Context 2:Instance-levelReflections ReAct-styleAgent 
Task profile/Constraints/Tool hints
Hierarchical Knowledge GroundingContext 1:Task LevelGuidance
ReadB.Online:Dual-Stream GroundingDual-stream retrieval from RSMeM
Prompt Builder[q; guidance; memory]
GeoTraceCompress•Keep full reasoning•Bound tool (geo-aware truncation) •Preserve exceptions
FailureCritique(Ω, heuristic rules R)
ReflectionGenerator
Outcome(↑)Tool Calling(↑)Efficiency(↑)Update
Task-LevelDecomposition
Write
External RS Tools
Instance-levelExperience•Errordiagnosis•Domainknowledge•Actionableplan
Issue?Yes No
FinalAnswer
Rerun
(Executed at each round)
raw trajectory(τ)
Figure 2: Overview of the RSMeM framework. The architecture consists of three main stages: (1) Offline
Knowledge Base Construction: Systematically distilling geoscience literature into a hierarchical domain knowledge
base and task-specific cards. (2) Online Task Solving via Dual-Stream Retrieval: The RS-Agent processes user
queries and RS observations by retrieving task-level guidance through Hierarchical Knowledge Grounding (Stream
A) and instance-level reflections from the Failure-Aware Memory (FAM) (Stream B). (3) Iterative Self-improvement:
Based on the tool-use trace, a reflection generator synthesizes feedback to update the FAM, enabling the agent to
evolve its experience and achieve higher accuracy and more reliable trajectories in subsequent tasks.
RS-Agent (Xu et al., 2025a) integrated large
language models with remote sensing tools for
scene classification and object detection. Recent
methods like ThinkGeo (Shabbir et al., 2025)
introduced geospatial computing workflows,
and UnivEarth (Kao et al., 2025b) incorporated
geo-environmental encoding for spectral analysis;
however, high failure rates limit their practical
use. To overcome the overreliance on RGB data
and underutilization of spectral information, Earth-
Agent (Feng et al., 2025) integrates multispectral
and hyperspectral data into a unified multimodal
pipeline, supporting complex tasks like parameter
inversion and time-series analysis, along with
the Earth-Bench benchmark for evaluation. For
structured geospatial workflows, the HTAM
framework (Li et al., 2025) employs a task-aware
hierarchical architecture to enable multi-step
problem decomposition, instantiated as EarthA-
gent and evaluated through GeoPlan-Bench with
metrics for tool selection and logical consistency.
The CangLing-KnowFlow (Chen et al., 2025)
introduces a Process Knowledge Base (PKB)
and an evolutionary memory module to mitigate
hallucinations.
Memory-Augmented Experience Learning.
Memory enables language agents to retain and
reuse information across interac
