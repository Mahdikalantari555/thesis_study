# RS-Agent Automating Remote Sensing Tasks through Intelligent Agent.pdf

- Category: Agentic
- Pages: 22
- Path: D:\RS\Thesis\New_papers\Agentic\RS-Agent Automating Remote Sensing Tasks through Intelligent Agent.pdf

## Metadata

```json
{
  "/Author": "Wenjia Xu; Zijian Yu; Boyang Mu; Jiuniu Wang; Zhiwei Wei; Mugen Peng",
  "/Creator": "arXiv GenPDF (tex2pdf:8def8d8)",
  "/DOI": "https://doi.org/10.48550/arXiv.2406.07089",
  "/License": "http://arxiv.org/licenses/nonexclusive-distrib/1.0/",
  "/PTEX.Fullbanner": "This is pdfTeX, Version 3.141592653-2.6-1.40.28 (TeX Live 2025) kpathsea version 6.4.1",
  "/Producer": "pikepdf 8.15.1",
  "/Title": "RS-Agent: Automating Remote Sensing Tasks through Intelligent Agent",
  "/Trapped": "/False",
  "/arXivID": "https://arxiv.org/abs/2406.07089v4"
}
```

## First pages


===== PAGE 1 =====
SCIENCE CHINA
Information Sciences
. RESEARCH PAPER .
RS-Agent: Automating Remote Sensing Tasks through
Intelligent Agent
Wenjia Xu1†* , Zijian Yu1†, Boyang Mu1, Jiuniu Wang2, Zhiwei Wei3* & Mugen Peng1
1State Key Laboratory of Networking and Switching Technology, Beijing University of Posts and Telecommunications, Beijing 100876, China
2City University of HongKong, Hong Kong 999077, China
3School of Geographic Sciences, Hunan Normal University, Changsha 410081, China
AbstractThe unprecedented advancements in Multimodal Large Language Models (MLLMs) have demonstrated strong potential for
language–vision interaction in remote sensing tasks such as visual question answering and scene understanding. However, these models
are largely constrained to basic instruction-following or descriptive tasks, and struggle with real-world remote sensing scenarios where
multi-source data, fine-grained spatial semantics, and expert knowledge are indispensable. To address these limitations, we propose
RS-Agent, a domain-adapted intelligent agent that bridges user intent and professional remote sensing workflows through structured
task planning and tool orchestration. RS-Agent is built upon four key components that explicitly follow the typical workflow of remote
sensing applications: a LLM-based Central Controller for user intent understanding and analytical process planning, a dynamic toolkit
for tool execution, a Solution Space for task-specific expert guidance, and a Knowledge Space for domain-level knowledge support. To
further enhance the performance of RS-Agent, we introduce two novel mechanisms: Task-Aware Retrieval, which improves task planning
by explicitly inferring task types and retrieving expert-defined procedural solutions, rather than relying on query-level similarity or
ad-hoc tool chaining; and DualRAG, a weighted dual-path retrieval-augmented generation method, which enhances the relevance and
completeness of retrieved domain knowledge. RS-Agent natively supports multiple imaging modalities, including optical and SAR imagery.
For SAR tasks in particular, the agent plans and orchestrates dedicated SAR processing and analysis tools into executable workflows,
improving reliability and automation under underspecified requests. Extensive experiments across 9 datasets and 18 remote sensing tasks
demonstrate that RS-Agent significantly outperforms state-of-the-art MLLMs, achieving over 95% task planning accuracy and delivering
superior performance in tasks such as scene classification, object counting, and remote sensing visual question answering. These results
validate the effectiveness of a dedicated remote sensing agent that fuses LLM reasoning with domain expertise for geospatial intelligence.
Our work presents RS-Agent as a robust and extensible framework for advancing intelligent automation in remote sensing analysis. Our
code will be available at https://github.com/IntelliSensing/RS-Agent.
Keywordsremote sensing, large language model, AI agent, retrieval-augmented generation.
CitationRS-Agent: Automating Remote Sensing Tasks through Intelligent Agent. Sci China Inf Sci, for review
1 Introduction
By aligning visual and textual information, Multi-modal Large Language Models (MLLMs) [1, 2] have advanced
remote sensing image interpretation, including captioning [3], visual question answering [4], and scene understand-
ing [5,6], making remote sensing data more accessible to non-expert users.
However, remote sensing presents unique challenges. Its multi-modal, multi-temporal, and multi-resolution char-
acteristics—spanning optical, SAR, and multi-spectral imagery—demand expert-level interpretation that MLLMs
struggle to achieve. Moreover, most existing MLLMs are designed for instruction-following or descriptive tasks [7–
10], and thus fail to deliver the analytical reasoning required for geospatial interpretation. These limitations call
for domain-aware intelligent systems that understand user intent and autonomously orchestrate specialized models.
AI Agents [11], autonomous systems that interpret user intent, plan multi-step tasks, invoke tools, and refine
decisions from intermediate outcomes [12–14], offer a promising pathway for remote sensing intelligence. Recent
advancements in agent frameworks—often powered by large language models—have demonstrated strong potential
in coordinating multiple tools, decomposing complex tasks, and flexibly adapting to diverse user goals through
modular design [11,15], with successful adoption in domains such as next-generation wireless networks [16,17].
Although a few works in the remote sensing field use the term “agent” in their paper [18–20], most of them
are designed for narrowly scoped tasks and lack a unified architecture that can generalize across heterogeneous
remote sensing applications. A representative example is RS-ChatGPT [21], which integrates ChatGPT [22] with a
* Corresponding author (email: xuwenjia@bupt.edu.cn, trentonwei@whu.edu.cn)
arXiv:2406.07089v4  [cs.CV]  7 Jul 2026
===== PAGE 2 =====
Sci China Inf Sci2
Planning
Perception
Action
(i) Central Controller
Memory
(iii) Solution
Space
(ii) Toolkit
Image
Query
Image
Answer
(iv) Knowledge
Space
User
Semantic Segmentation Sea-land Segmentation
Figure 1The schematic diagram of the RS-Agent. RS-Agent consists of four main components: a Central Controller based on LLM, which
comprehends user queries, maintains historical context, plans tool usage, and aggregates results; a Solution Space that provides well-defined
solutions to user-submitted problems; a Knowledge Space offering domain-specific knowledge in remote sensing; and a Toolkit integrating state-
of-the-art methods for remote sensing tasks.
collection of pre-trained remote sensing networks to perform tasks such as object detection, scene classification, and
image captioning. However, RS-ChatGPT encounters difficulties when scaling to more diverse tools or addressing
problems that require structured procedural reasoning and specialized domain knowledge, revealing the absence of
a unified, domain-aware agent framework for real-world remote sensing analysis.
In this paper, we propose RS-Agent, a domain-specific AI agent designed to bridge this gap by integrating
LLM reasoning with expert knowledge for professional remote sensing applications. As shown in Fig. 1, RS-Agent
comprises four components that mirror the typical remote sensing workflow:(i)a LLM-based Central Controller
that interprets queries, plans tasks, executes tools, and aggregates results;(ii)a Toolkit of SOTA methods covering
tasks such as denoising, super-resolution, detection, captioning, and scene classification (Fig. 4);(iii)a Solution
Space that provides task-specific solutions to guide tool selection;(iv)a Knowledge Space that supplies domain
expertise for remote sensing tasks.
The core functionality of RS-Agent lies in interpreting user instructions and converting them into executable
workflows. To this end, we design a structured agent architecture that combines modular prompting with dynamic
context tracking, enabling the Central Controller to plan workflows adaptively from current inputs, tool outputs,
and contextual memory [23,24]. In the Solution Space, to enable RS-Agent to reason like a remote sensing analyst,
we build a Solution Database storing professional knowledge for tool use, and propose Task-Aware Retrieval, which
infers task types from user queries and retrieves expert-defined solution procedures for accurate tool selection and
step-by-step decomposition. To address the domain knowledge limitations of general-purpose models [22, 25, 26],
we develop a dedicated Knowledge Database, tailored to the remote sensing domain. Building on this, we propose
DualRAG, which combines weighted keyword-aware retrieval with global semantic search to enable the agent to
retrieve more relevant and accurate domain-specific knowledge.
We conduct extensive experiments across 9 datasets and 18 remote sensing tasks. RS-Agent achieves over 95% task
planning accuracy, substantially outperforming the SOTA baseline RS-ChatGPT [21], and consistently surpasses
single-model performance on scene classification, RS visual question answering, and object counting. The proposed
DualRAG further improves domain knowledge retrieval. RS-Agent is LLM-agnostic; we validate its generality with
ChatGPT [22], LLaMA [25], Qwen [27], and DeepSeek [28].
The contributions of this paper are summarized as follows:
•RS-Agent: A Comprehensive Agent Framework For Remote Sensing.We present RS-Agent, an archi-
tecture designed for remote sensing scenarios that interprets user queries and orchestrates diverse tools for accurate
task execution. Its four components—Central Controller, Toolkit, Solution Space, and Knowledge Space—work in
concert to enable robust performance across applications.
•Domain-Adapted Task Planning Solution Space with Task-Aware Retrieval method.To enhance
the agent’s task planning accuracy, we propose a domain-adapted Task-Aware Retrieval method. It exploits the
structured nature of remote sensing workflows by first inferring a task type and then retrieving expert-curated
===== PAGE 3 =====
Sci China Inf Sci3
solution templates as a planning prior. Leveraging domain-specific task knowledge, RS-Agent emulates the decision-
making and tool selection processes of professional remote sensing analysts for complex and multi-step tasks.
•Knowledge Space with DualRAG to Retrieve Professional Domain Knowledge.To strengthen RS-
Agent’s remote sensing domain knowledge, we propose DualRAG, a domain-adapted retrieval augmented generation
method that assigns weights to extracted keywords and performs dual path retrieval, thereby enhancing the accuracy
and relevance of knowledge retrieval for geospatial analysis tasks. Its dual-path design addresses the heterogeneous
nature of remote sensing queries that require both macro-level context and fine-grained technical details.
•Superior Performance on Various Applications.Extensive experiments demonstrate that RS-Agent
consistently surpasses prior SOTA MLLMs across remote sensing applications and substantially boosts task planning
accuracy, marking a step forward in adapting AI agents to remote sensing.
2 Related Works
2.1 Remote Sensing Multimodal Large Language Models
MLLMs have transformed human-AI interaction in earth observation by aligning visual and semantic features for
natural-language interpretation of remote sensing imagery. Early work focused on captioning [29,30] and VQA [31],
but lacked flexibility for open-ended queries, motivating general-purpose models. RSGPT [5] and GeoChat [6]
adapted LLaVA to remote sensing, supporting multiturn dialogue and visual geo-localization, while LHRS-Bot [32]
introduced a multi-level vision-language alignment for SOTA perception. EarthVQANet [33] and SkySenseGPT [34]
added multi-task learning and knowledge-graph integration to enhance reasoning. For temporal dynamics, Change-
CLIP [35] and SkyEyeGPT [36] extended to change captioning and video understanding, and UniRS [37] unified
single-frame, bi-temporal, and video inputs.
However, the end-to-end paradigm has intrinsic limitations: current MLLMs struggle with deep reasoning, often
hallucinate on quantitative tasks such as object counting, and rely on static knowledge that requires prohibitive
retraining to update [6]. RS-Agent addresses these issues by shifting to agentic orchestration—leveraging LLM
planning to invoke specialized tools and retrieve dynamic knowledge without retraining.
2.2 LLM-based Agents in Remote Sensing
LLM-based agents extend static MLLMs with autonomous planning and tool orchestration, perceiving environments
and refining decisions via feedback loops [13,38]. In remote sensing, such agents have evolved from single-task spe-
cialists to general-purpose frameworks. Early works targeted vertical applications: TreeGPT [18] tailors an expert
system for forestry with tree segmentation and ecological p
