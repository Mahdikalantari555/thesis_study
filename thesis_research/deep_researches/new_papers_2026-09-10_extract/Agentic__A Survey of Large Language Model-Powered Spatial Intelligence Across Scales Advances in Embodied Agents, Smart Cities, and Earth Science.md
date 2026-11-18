# A Survey of Large Language Model-Powered Spatial Intelligence Across Scales Advances in Embodied Agents, Smart Cities, and Earth Science.pdf

- Category: Agentic
- Pages: 14
- Path: D:\RS\Thesis\New_papers\Agentic\A Survey of Large Language Model-Powered Spatial Intelligence Across Scales Advances in Embodied Agents, Smart Cities, and Earth Science.pdf

## Metadata

```json
{
  "/Author": "",
  "/CreationDate": "D:20250415012154Z",
  "/Creator": "LaTeX with hyperref",
  "/Keywords": "",
  "/ModDate": "D:20250415012154Z",
  "/PTEX.Fullbanner": "This is pdfTeX, Version 3.141592653-2.6-1.40.25 (TeX Live 2023) kpathsea version 6.3.5",
  "/Producer": "pdfTeX-1.40.25",
  "/Subject": "",
  "/TemplateVersion": "IJCAI.2025.0",
  "/Title": "",
  "/Trapped": "/False"
}
```

## First pages


===== PAGE 1 =====
A Survey of Large Language Model-Powered Spatial Intelligence Across Scales:
Advances in Embodied Agents, Smart Cities, and Earth Science
Jie Feng, Jinwei Zeng, Qingyue Long,βHongyi Chen, Jie Zhao,†Yanxin Xi, Zhilun Zhou,
Yuan Yuan,§Shengyuan Wang, Qingbin Zeng, Songwei Li, Yunke Zhang,
Yuming Lin, Tong Li, Jingtao Ding, Chen Gao, Fengli Xu, Yong Li
Department of Electronic Engineering, BNRist, Tsinghua University, Beijing, China,
β Shenzhen International Graduate School, Tsinghua University, Shenzhen, China,
§Department of Computer Science, Tsinghua University, Beijing, China,
†Department of Computer Science, University of Helsinki, Helsinki, Finland
{fengjie, liyong07}@tsinghua.edu.cn
Abstract
Over the past year, the development of large lan-
guage models (LLMs) has brought spatial intelli-
gence into focus, with much attention on vision-
based embodied intelligence. However, spatial in-
telligence spans a broader range of disciplines and
scales, from navigation and urban planning to re-
mote sensing and earth science. What are the differ-
ences and connections between spatial intelligence
across these fields? In this paper, we first review
human spatial cognition and its implications for spa-
tial intelligence in LLMs. We then examine spatial
memory, knowledge representations, and abstract
reasoning in LLMs, highlighting their roles and con-
nections. Finally, we analyze spatial intelligence
across scales—from embodied to urban and global
levels—following a framework that progresses from
spatial memory and understanding to spatial rea-
soning and intelligence. Through this survey, we
aim to provide insights into interdisciplinary spatial
intelligence research and inspire future studies.
1 Introduction
Spatial intelligence is an inherently interdisciplinary research
field, encompassing diverse challenges, application scenarios,
and methodologies across multiple domains. For example, nav-
igating within a room requires spatial intelligence, designing a
15-minute community relies on spatial intelligence, predicting
the possible location of an image involves spatial intelligence,
and analyzing the spatial patterns of climate is also a form
of spatial intelligence. In other words, spatial intelligence
is ubiquitous and plays a crucial role in human society and
physical world.
Research on spatial intelligence has deep historical roots.
On the one hand, it serves as a crucial avenue for humans
to understand their own cognitive and perceptual mecha-
nisms [Ishikawa, 2021; Eichenbaum and Cohen, 2014]. Stud-
ies on human spatial cognition, ranging from mental mapping
All authors contribute equally to this work.
to wayfinding strategies, have provided foundational insights
into human intelligence. On the other hand, spatial intelligence
has long had practical significance in real-world applications,
such as embodied navigation [Lin et al., 2024], geographic
information systems (GIS) [Zhao et al., 2024], and climate
prediction [She et al., 2024]. The study of spatial intelligence
continues to evolve, bridging cognitive science, artificial intel-
ligence, and applied domains.
The rapid advancements in deep learning, particularly in
large language models (LLMs), have significantly contributed
to spatial intelligence research of recent years. LLMs have
made notable progress with world knowledge, planning and
reasoning capabilities, and powerful generalization across
tasks. These advancements have fueled research in embodied
intelligence [Gupta et al., 2021], where LLMs play a central
role in areas such as robotic navigation, multimodal perception,
and control. Recent works, such as SpatialVLM [Chen et al.,
2024] and V oxposer[Huang et al., 2023b], have demonstrated
how LLMs can improve spatial reasoning and decision-making
in embodied agents, enabling them to operate more effectively
in complex environments.
Beyond embodied intelligence, LLMs have also inspired
new research in urban and global-scale spatial intelligence.
In urban research, for example, LLMs have been integrated
with geospatial data to optimize urban planning [Zhou et al.,
2024b], traffic prediction [Li et al., 2024e] and infrastructure
management [Lai et al., 2023]. At a global scale, researchers
have explored how LLMs can enhance remote sensing analy-
sis [Kuckreja et al., 2024] and disaster prediction [Zhang et
al., 2023b], and so on, which illustrate the potential of LLMs
to process large-scale geospatial information and generate
meaningful insights for global-scale decision-making. These
interdisciplinary applications highlight the transformative im-
pact of LLMs on spatial intelligence research, paving the way
for future developments across multiple domains.
Despite the growing of research on spatial intelligence
across various fields, there is still a lack of a unified framework
for comprehensively understanding and analyzing it. Existing
studies often focus on specific aspects, such as vision-based
embodied intelligence, urban planning, or remote sensing in-
telligence, without integrating insights across disciplines and
arXiv:2504.09848v1  [cs.AI]  14 Apr 2025
===== PAGE 2 =====
Embodied Spatial Intelligence Urban Spatial Intelligence Earth Spatial Intelligence
Figure 1: Multiple scale spatial intelligence in real world: from embodied spatial intelligence to earth spatial intelligence.
scales. To bridge this gap, this survey traces the development
of spatial intelligence from the perspective of human cogni-
tion, fundamental spatial capabilities, and multi-scale system
intelligence from embodied agents, urban intelligence and
earth science. By synthesizing these perspectives, we aim to
provide a cohesive foundation for interdisciplinary research,
offering insights and inspiration for future advancements in
spatial intelligence.
Our survey makes three key contributions. First, it estab-
lishes a structured analytical framework for understanding
spatial intelligence across diverse disciplines and scales, ad-
vancing from spatial memory and perception to reasoning
and higher-level intelligence. Second, it synthesizes exist-
ing literature on spatial intelligence applications with LLMs
across multiple fields, alongside discussions on spatial mem-
ory, knowledge representation, and spatial reasoning in LLMs,
providing researchers with a timely and valuable reference.
Third, it explores key challenges and open questions in interdis-
ciplinary spatial intelligence research, uncovering connections
between embodied, urban, and global-scale intelligence while
outlining promising directions for future exploration.
2 Background and Taxonomy
2.1 Spatial Intelligence of Human
Here, we first review human spatial intelligence research from
the perspectives of neuroscience and cognitive science, eluci-
dating the potential abilities and origins of spatial intelligence
across various domains and scales. Furthermore, we explore
the relationship between spatial intelligence and other human
intelligences. These findings will enhance our understanding
of the critical capabilities of cross-domain spatial intelligence
and facilitate the development of more effective methods for
constructing and enhancing spatial intelligence.
2.1.1 Cognitive Map
Spatial cognitive map is the internal representation of envi-
ronmental knowledge, characterized by subjectivity and dis-
tortion [Ishikawa, 2021]. Tolman introduced this concept in
1948 [Tolman, 1948], later expanded by Eichenbaum et al.[Co-
hen, 1993; Eichenbaum and Cohen, 2014], emphasizing the
hippocampus’s role in spatial and non-spatial memory. At the
neural level, spatial representation relies on place cells in the
hippocampus and grid cells in the entorhinal cortex [Moser
et al., 2008; Moser et al., 2017]. Place cells activate when
an individual is in a specific location, while grid cells pro-
vide a coordinate-like system for mapping the environment.
These cells, along with head direction cells and boundary
cells, form the neural basis for constructing spatial cognitive
maps [Long et al. , 2025 ]. Recent advancements, such as
the Tolman-Eichenbaum Machine (TEM) [Whittington et al.,
2020], highlight the ability to generalize spatial and relational
memory through structural abstraction and cross-environment
representation by grid cells. Comparatively, large language
models (LLMs) leverage Transformer architectures to emu-
late spatial tasks, such as positional encoding and navigation,
drawing parallels to hippocampal functions [Whittington et
al., 2021].
2.1.2 Spatial Schema
Schemas are high-level knowledge structures that encapsulate
the common features abstracted from multiple experiences.
These structures play a critical role in the processes of perceiv-
ing, interpreting, and remembering events. They continuously
evolve with the accumulation of new experiences and memo-
ries, influencing the formation, consolidation, and retrieval of
memory [Gilboa and Marlatte, 2017]. In human spatial cog-
nition, schemas play a crucial role. Spatial schemas are high-
level spatial cognitive structures formed through the transfer
and generalization of experiences across different environ-
ments. Unlike cognitive maps, their processing is centered in
specific regions of the neocortex. Spatial schemas are highly
abstract in nature, emerging through the integration of over-
lapping neural representations in similar environments. They
serve as higher-order spatial representations that transcend
specific environments, such as the anticipated layout of a mod-
ern city [Farzanfar et al., 2023]. Spatial schemas and cognitive
maps, as distinct levels of spatial cognitive structures, interact
and influence each other, jointly contributing to human spatial
cognition.
Recent research has explored the similarities and connec-
tions between spatial intelligence based on LLMs and human
===== PAGE 3 =====
Large Language Model-Empowered Spatial Intelligence
Foundational
Capabilities
Spatial Memory
and Knowledge
Internal Encoded [Petroni et al., 2019], [Gurnee and Tegmark, 2024 ], [Roberts et al., 2020]
Externally Integrated [Mansourian and Oucheikh, 2024 ] [Yu et al., 2024b]
Abstract Spatial
Reasoning
Qualitative Reasoning [Yamada et al., 2023], [Sharma, 2023], [Lehnert et al., 2024], [Li et al., 2024a]
Geometric Reasoning: GeoEval [Zhang et al., 2024], GeomVerse [Kazemi et al., 2023]
Graph-theoretical Reasoning: GraphInstruct [Luo et al., 2024]
Spatial Intelligence
for Real World
Embodied Spatial
Intelligence
Spatial Perception and Understanding: LLMI3D [Yang et al., 2024a], 3D-MEM [Yang et al., 2024d],
EmbodiedScan [Wang et al., 2024b], Scene-LLM [Fu et al., 2024], SpatialBot [Cai et al., 2024]
Spatial Interaction and Navigation: RT-2 [Zitkovich et al., 2023], VIMA [Jiang et al., 2022],
Guide-LLM [Song et al., 2024], NavGPT [Zhou et al., 2024a], TopV-Nav [Zhong et al., 2024]
Urban Spatial
Intelligence
Spatial Understanding and Memory: GeoLLM [Manvi et al., 2023], GeoChat [Kuckreja et al., 2024],
UrbanCLIP [Yan et al., 2024], ReFound [Xiao et al., 2024], UrbanKGEnt [Ning and Liu, 2024 ]
Spatial Reasoning and Intelligence: GeoReasoner [Li et al., 2024c], LLMob [Wang et al., 2024a],
AgentMove [Feng et al., 2024b], Mobility-LLM [Gong et al., 2024], FLAME [Xu et al., 2024a],
Earth Spatial
Intelligence
Global Encoding: TorchSpatial Benchmark [Wu et al., 2024]
Climate: LLMDiff [She et al., 2024], CLLMate [Li et al., 2024b], GenCast [Ravuri et al., 2021]
Geography: GeoGPT [Zhang et al., 2023a], GeoSEE [Han et al., 2024], GeoReasoner [Yan and Lee, 2024 ]
Other Disciplines: OceanPlan [Yang et al., 2024c], Orca [Li et al., 2024d], MineAgent[Yu et al., 2024a]
Figure 2: A taxonomy of large language model-empowered spatial intelligence with representative examples.
spatial intelligence, e.g., Momennejad et al. [Momennejad
et al., 2024 ] assessed their cognitive mapping capabilities.
However, LLMs exhibit limitations, including topological
reasoning errors (e.g., fictitious paths, inefficiency) and visua
