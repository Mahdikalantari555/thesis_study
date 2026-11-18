# RSMeM: Knowledge-Enhanced Memory Evolution for Remote Sensing Agents with Systematic Evaluation

**Authors:** Wu, B., Zhang, Y., et al.  
**Year:** 2026  
**Venue:** arXiv  
**DOI / arXiv:** arXiv:2607.24772v2  
**Local PDF:** 2607.24772v2.pdf  
**Type:** methods  
**Thesis relevance:** High  

## Summary
RSMeM introduces knowledge-enhanced memory evolution for remote sensing agents. It combines Hierarchical Knowledge Grounding (3 domains → 12 subdomains → 64 task formulations) with Failure-Aware Experience Refinement in a ReAct-style, tool-augmented agent. Backbones include DeepSeek-V3.2, Kimi-K2, and Qwen3-32B/8B, evaluated on Earth-Bench.

## Methods / Architecture
- Hierarchical Knowledge Grounding: 3 domains → 12 subdomains → 64 task formulations
- Failure-Aware Experience Refinement
- ReAct-style agent with tools
- Backbones: DeepSeek-V3.2, Kimi-K2, Qwen3-32B/8B
- Benchmark: Earth-Bench

## Key quantitative results
- +6.07% accuracy on DeepSeek-V3.2 with <1% extra experience tokens
- Consistent gains across multiple backbones

## Relevance to thesis
Failure-aware memory evolution mirrors active-learning-style iterative improvement for crop-stress analysis agents, enabling accumulation of expert correction patterns across seasons/regions.

## Gaps / opportunities
- Hierarchical knowledge taxonomy is RS-general; crop-stress subdomain depth untested
- Experience token efficiency could be stress-task-specific
- Opportunity to couple failure-aware refinement with AgriWorld verifiable protocols

## Citation (APA 7th)
Wu, B., Zhang, Y., et al. (2026). *RSMeM: Knowledge-Enhanced Memory Evolution for Remote Sensing Agents with Systematic Evaluation*. arXiv:2607.24772v2.

---
*Note written 2026-09-10 from first-page extract. Verify numbers in full PDF before formal proposal use.*
