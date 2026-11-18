# RS-Agent: Automating Remote Sensing Tasks through Intelligent Agent

**Authors:** Xu, W., Yu, Z., Mu, B., Wang, J., Wei, Z., & Peng, M.  
**Year:** 2024  
**Venue:** Sci China Inf Sci / arXiv  
**DOI / arXiv:** arXiv:2406.07089v4  
**Local PDF:** RS-Agent Automating Remote Sensing Tasks through Intelligent Agent.pdf  
**Type:** methods  
**Thesis relevance:** High  

## Summary
RS-Agent is a domain-adapted intelligent agent for automating remote sensing (RS) tasks. It introduces Task-Aware Retrieval in Solution Space and DualRAG (keyword + semantic retrieval), coordinated by a Central Controller with a Toolkit, Solution Space, and Knowledge Space. The framework is LLM-agnostic (ChatGPT, LLaMA, Qwen, DeepSeek) and provides a canonical template for agentic crop-stress GeoAI systems.

## Methods / Architecture
- Central Controller + Toolkit + Solution Space + Knowledge Space
- Task-Aware Retrieval in Solution Space
- DualRAG: keyword + semantic dual retrieval
- LLM-agnostic design supporting ChatGPT, LLaMA, Qwen, DeepSeek
- Public code: github.com/IntelliSensing/RS-Agent

## Key quantitative results
- >95% task planning accuracy
- Evaluated on 9 datasets covering 18 RS tasks
- Outperforms RS-ChatGPT baseline
- Supports both optical and SAR imagery

## Relevance to thesis
Canonical agentic RS baseline and architectural template for a crop-stress GeoAI agent; provides concrete retrieval + planning patterns that can be adapted to multi-temporal agricultural stress analysis.

## Gaps / opportunities
- Unclear how solution-space retrieval generalizes to novel crop-stress phenology tasks
- Limited analysis of temporal/multi-sensor stress trajectories beyond optical+SAR coverage
- No explicit failure-aware memory loop (contrast with later RSMeM-style agents)

## Citation (APA 7th)
Xu, W., Yu, Z., Mu, B., Wang, J., Wei, Z., & Peng, M. (2024). *RS-Agent: Automating Remote Sensing Tasks through Intelligent Agent*. arXiv:2406.07089v4.

---
*Note written 2026-09-10 from first-page extract. Verify numbers in full PDF before formal proposal use.*
