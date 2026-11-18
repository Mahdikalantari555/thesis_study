# 2606.07538v1.pdf

- Category: Agentic
- Pages: 13
- Path: D:\RS\Thesis\New_papers\Agentic\2606.07538v1.pdf

## Metadata

```json
{
  "/Author": "Zeyuan Wang; Dongyang Hou; Cheng Yang; Xuezhi Cui; Linrui Xu; Bo Yu; Gaozhi Zhou; Ziyu Li; Liangtian Liu; Kai Ouyang; Wang Guo; Lili Zhu; Chao Tao",
  "/Creator": "arXiv GenPDF (tex2pdf:a6404ea)",
  "/DOI": "https://doi.org/10.48550/arXiv.2606.07538",
  "/License": "http://creativecommons.org/licenses/by/4.0/",
  "/PTEX.Fullbanner": "This is pdfTeX, Version 3.141592653-2.6-1.40.28 (TeX Live 2025) kpathsea version 6.4.1",
  "/Producer": "pikepdf 8.15.1",
  "/Title": "Bidirectional Semantic Complementary Tool Retrieval for Remote Sensing Agents",
  "/Trapped": "/False",
  "/arXivID": "https://arxiv.org/abs/2606.07538v1"
}
```

## First pages


===== PAGE 1 =====
1
Bidirectional Semantic Complementary Tool
Retrieval for Remote Sensing Agents
Zeyuan Wang1, Dongyang Hou 1, Cheng Yang1, Xuezhi Cui 1, Linrui Xu 1, Bo Yu1, Gaozhi Zhou 2,
Ziyu Li1, Liangtian Liu 1, Kai Ouyang 1, Wang Guo1, Lili Zhu 3, Chao Tao1
Abstract—Large language model (LLM)-based agents provide
a novel paradigm for the automated processing of remote sensing
(RS) data. Their success in complex RS tasks rely on extensive
specialized tool libraries. However, tool documentation often
exceeds the context window limits of LLMs, making precise
tool retrieval essential for agentic workflows. Existing tool re-
trieval methods face “semantic asymmetry” bottleneck: natural
language queries typically express macro-level intentions lacking
tool-specific semantics, while tool documentation provides fine-
grained technical descriptions lacking operational context for
workflows. To bridge this semantic gap, this paper proposes
a bidirectional semantic complementary tool retrieval method.
First, on the query side, we introduce a planning-based query
enhancement mechanism that leverages the reasoning capabilities
of agents to decompose abstract intentions into logical sub-
tasks, thereby actively supplementing the query with missing
functional semantics. Second, on the tool side, addressing the
strong coupling characteristics of RS tool chains, we construct
a dynamic tool dependency graph with continual learning capa-
bilities. By employing a neighborhood information aggregation
mechanism, contextual information from precursor tools is ex-
plicitly injected into the current node representation, enriching
tool descriptions with contextual semantics. Experimental results
on the RS dataset GeoPlan-bench and the general-purpose
dataset API- Bank demonstrate that the proposed method not
only significantly improves tool retrieval accuracy for complex
RS tasks but also exhibits robust extensibility for transfer to
general-domain tasks. The source code and dataset are available
at https://github.com/geox-lab/BSCTR.
Index Terms—Remote sensing, Large Language Model Agents,
Tool retrieval.
I. INTRODUCTION
W
ITH the rapid advancement of satellite technology,
Earth observation capabilities have been markedly im-
proved, leading to a marked increase in image acquisition
efficiency. However, the efficiency of image interpretation
is far behind, exacerbating the contradiction between “mas-
sive data” and“scant information”. Faced with multi-modal
remote sensing (RS) observation data with varying spatio-
temporal resolutions, diverse application scenarios impose
distinct requirements on interpretation tasks. Consequently,
systems must be capable of invoking specific combinations
of models and algorithms to precisely address these varying
needs. Nevertheless, in current practice, automated workflows
1School of Geosciences and Info-Physics, Central South University, Chang-
sha 410083, China.
2School of Mechanical and Electrical Engineering, Central South Univer-
sity, Changsha 410083, China.
3Hunan Key Laboratory of Land Resources Evaluation and Utilization, Hu-
nan Provincial Institute of Land and Resources Planning, Changsha 410013,
China.
relying on expert-defined templates struggle to flexibly adjust
tool selection and composition according to dynamic task
requirements, which has become a major bottleneck restricting
the automation of RS interpretation.
To overcome this limitation, Large Language Model (LLM)-
driven agents have emerged as a promising research direc-
tion. Benefiting from breakthroughs in intent understanding,
autonomous decision-making, and tool invocation capabili-
ties [1], [2], LLM-based agents can flexibly handle complex
scenarios that traditional workflows find difficult to adapt
to through logical reasoning. Accordingly, researchers in the
RS field have begun to introduce the agent paradigm. For
instance, the RS-Agent team proposed RS-Agent [3], which
aims to achieve autonomous scheduling of specialized models
through natural language interaction. For more complex long-
chain tasks, the Earth-Agent team [4] proposed a hierarchical
multi-agent architecture to achieve task planning and execu-
tion following domain-specific processing workflows. These
studies demonstrate that agents, with their flexible reasoning
and planning capabilities, are providing a novel processing
paradigm for RS interpretation tasks.
However, remote sensing agents still face severe challenges.
RS image analysis tasks typically involve highly specialized
tool-chains, encompassing a series of intricate steps from
data preprocessing and radiometric calibration to geometric
correction and feature extraction. To tackle complex image
analysis tasks, agents must be equipped with extensive open-
source tool libraries—such as QGIS, Orfeo ToolBox (OTB),
and GDAL—which comprise hundreds of specialized func-
tions. In early practices, researchers tended to adopt a “full-
tool registration” strategy, where functional descriptions of
all available tools were directly injected into the agent’s
system prompts [5]. However, constrained by the finite context
window capacity of LLMs, excessive tool descriptions often
lead to a significant degradation in the agent’s task execution
performance [6]. Consequently, when dealing with extensive
tool-sets, the tool retrieval paradigm has emerged as the
mainstream approach. This paradigm dynamically recalls the
most relevant tool subset by calculating the semantic similarity
between user queries and tool descriptions, thereby facilitating
precise tool supply within a limited context [7], [8].
Although retrieval methods mitigate the aforementioned
capacity constraints, their accuracy is significantly hindered
by the “semantic misalignment” between user queries and tool
descriptions. Essentially, tool retrieval is a task of alignment
within the semantic space. Drawing upon the foundational
theories of semiotician Charles W. Morris [9], we redefine the
arXiv:2606.07538v1  [cs.IR]  29 Apr 2026
===== PAGE 2 =====
2
Fig. 1. Comparison of tool retrieval paradigms for the remote sensing agent. (a)Current Paradigm: Semantic mismatch occurs due to missing functional
and contextual semantics, leading to task execution failure. (b)Ours: Bidirectional semantic alignment effectively bridges the gap by supplementing both
semantics, ensuring successful retrieval of all necessary tools.
semantics of tool retrieval in the context of agent-based tool
invocation into two dimensions: “functional semantics” and
“contextual semantics.” Specifically, functional semantics fo-
cus on a tool’s technical implementation and execution objects,
whereas contextual semantics emphasize its role and usage
within a specific task workflow. Existing retrieval paradigms
face a distinct “semantic misalignment”: user queries are typ-
ically coarse-grained macro-intentions that lack the functional
semantic descriptions of specific technical means; conversely,
tool documentation provides fine-grained technical specifica-
tions that define inputs and outputs but lack the contextual
semantics of real-world application scenarios(as conceptually
illustrated in Fig. 1(a)). Current literature has only addressed
this issue from a single perspective. For instance, [10], [11]
focus on the query side by rewriting user queries to supple-
ment functional semantics, while [12], [13] construct graph
connections to enrich contextual information on the tool side.
However, these efforts fail to fully bridge the fundamental
semantic gap that exists between query descriptions and tool
specifications.
Within the field of RS, we observe distinct “strong cou-
pling” characteristics among specialized tools. Specific steps in
RS tasks typically adhere to established operational paradigms;
for instance, atmospheric correction is usually followed by
geometric correction. Consequently, the outputs of precursor
tools often impose hard constraints on the selection of sub-
sequent tools. We contend that these domain-specific tool-
chain dependencies constitute the contextual semantics of
a tool—that is, the profound meaning of a tool is inher-
ently embedded within the context of its entire operational
workflow. Building upon this hypothesis, this paper proposes
aBidirectional Semantic Complementary Tool Retrieval
(BSCTR) method, which effectively aligns the missing se-
mantics from both sides (see Fig. 1(b)). On the query side,
leveraging the robust reasoning and planning capabilities of
contemporary agents [2], we introduce a planning-based query
enhancement mechanism. This mechanism drives the agent
to logically decompose and reason through coarse-grained
user intentions, autonomously excavating and supplementing
missing functional semantics within the query. On the tool
side, we construct a dynamic tool dependency graph with con-
tinual learning capabilities. Initially, topological connections
between tools are initialized based on historical trajectories.
Then, inspired by the information aggregation mechanism
of Simplified Graph Convolution [14], we perform linear
aggregation of neighborhood features in the vector space. This
explicitly injects contextual information from precursor tools
into the current tool node representations, thereby enriching
the contextual semantics of tool descriptions. To ensure the
graph’s generalization capability, the system autonomously es-
tablishes new connections between tools invoked sequentially
in successful task executions. This bi-directional enhancement
effectively bridges the semantic misalignment between user
queries and tool descriptions.
The primary contributions of this work are summarized as
follows:
•Bidirectional Complementary Framework:We pro-
pose theBidirectional Semantic Complementary Tool
===== PAGE 3 =====
3
Retrievalframework, which establishes a novel paradigm
for bridging the “semantic asymmetry” in RS agent tasks.
By synergizing planning-based query enhancement and
tool-side contextual injection, the framework effectively
aligns macro-level user intentions with fine-grained tech-
nical specifications.
•Graph-based Contextual Modeling:We design a dy-
namic tool dependency graph mechanism that explicitly
encodes pragmatic contexts into node representations.
Through a neighborhood information aggregation mecha-
nism in the vector space, the framework injects precursor
contextual semantics into tool descriptions, capturing
the strong coupling characteristics and sequential logic
inherent in professional RS workflows.
•Empirical Validation:We validate the superiority of the
proposed method on the specialized RS datasetGeoPlan-
bench[4]. Moreover, evaluations on the general-purpose
API-Bank[15] demonstrate the robust domain scalability
and generalization capabilities of our mechanism.
II. RELATED WORK
This section systematically reviews the research progress
of large language models (LLMs) within the remote sens-
ing (RS) domain and the field of tool selection from three
distinct dimensions. Subsection II-A traces the evolutionary
trajectory of RS agents, elucidating the paradigm shift from
early multi-modal perception to advanced intelligent systems
equipped with logical planning and autonomous tool selec-
tion capabilities. Subsection II-B investigates tool retrieval
strategies based on query rewriting, analyzing how researchers
supplement missing functional semantics on the query side by
reformulating user intentions. Subsection II-C summarizes tool
retrieval methods leveraging tool graphs, exploring the current
landscape of enriching tool contextual semantics through the
modeling of topological dependencies.
A. Remote sensing agents based on large language models
In recent years, the integration of LLMs and multi-modal
technologies has reshaped the processing paradigms for RS
imagery. Early research primarily focused on constructing
RS multi-modal foundation models to enhance the percep-
tion and understanding of domain-specific knowledge. For
example,GeoChat[16] empow
