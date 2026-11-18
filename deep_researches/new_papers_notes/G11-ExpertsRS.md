# An LLM-based multi-agent system for remote sensing analysis

**Authors:** Sun, Z., Zhou, Y., & Yang, J.  
**Year:** 2025  
**Venue:** Big Earth Data  
**DOI / arXiv:** 10.1080/20964471.2025.2600178  
**Local PDF:** An LLM-based multi-agent system for remote sensing analysis.pdf  
**Type:** methods  
**Thesis relevance:** HIGH  

## Summary
This paper presents ExpertsRS, an LLM-based multi-agent system for remote sensing analysis built on the AutoGen framework with DeepSeek-V3 as the language model. The system organizes functionality into three modules—Data, Tools, and Brain—and employs three role-specialised agents that convert vague natural-language requests from non-experts into structured remote sensing workflows (for example, assessing vegetation health). Evaluations show that ExpertsRS outperforms a baseline single LLM and a single-agent configuration, while incurring only a modest token overhead.

## Methods / Architecture
- Multi-agent architecture implemented with AutoGen.
- Backbone LLM: DeepSeek-V3.
- Three modules: Data, Tools, and Brain.
- Three role-specialised agents collaborate to parse vague natural language into structured RS workflows (e.g., vegetation-health assessment).

## Key quantitative results
- ExpertsRS outperforms the baseline LLM and the single-agent setting.
- Token overhead reported as modest (exact token counts not stated in the first-page extract).
- Exact task-level scores and ablation numbers are not provided in the first-page extract; verify against the full PDF before formal use.

## Relevance to thesis
Acts as a design template for arid crop-stress monitoring assistants aimed at non-experts: multi-agent role division can convert informal queries (e.g., "is the crop stressed?") into executable RS pipelines combining data access, tool calls, and reasoning.

## Gaps / opportunities
- Crop-stress-specific agents and EO foundation models are not the focus; the system is domain-general remote sensing.
- Exact quantitative benchmarks and token-cost trade-offs need verification in the full PDF.
- Potential extension: integrate active-learning loops and EO-FM embeddings (e.g., Prithvi, CROMA) into the Tools/Brain modules for arid environments.

## Citation (APA 7th)
Sun, Z., Zhou, Y., & Yang, J. (2025). An LLM-based multi-agent system for remote sensing analysis. *Big Earth Data*. https://doi.org/10.1080/20964471.2025.2600178

---
*Note written 2026-09-10 from first-page extract. Verify numbers in full PDF before formal proposal use.*
