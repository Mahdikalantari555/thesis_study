# Bidirectional Semantic Complementary Tool Retrieval for Remote Sensing Agents

**Authors:** Wang, Z., Hou, D., et al.  
**Year:** 2026  
**Venue:** arXiv  
**DOI / arXiv:** arXiv:2606.07538v1  
**Local PDF:** 2606.07538v1.pdf  
**Type:** methods  
**Thesis relevance:** Medium  

## Summary
BSCTR addresses semantic asymmetry in tool retrieval for remote sensing agents via bidirectional semantic complementarity. Query enhancement uses planning decomposition; tool enrichment uses a dynamic dependency graph with continual learning. The method builds on RS-Agent and Earth-Agent and is evaluated on GeoPlan-bench and API-Bank.

## Methods / Architecture
- Problem framing: semantic asymmetry in RS tool retrieval
- Query enhancement via planning decomposition
- Tool enrichment via dynamic dependency graph + continual learning
- Benchmarks: GeoPlan-bench + API-Bank
- Builds on RS-Agent and Earth-Agent
- Code: github.com/geox-lab/BSCTR

## Key quantitative results
- Exact table numbers not available in first-page extract
- Outperforms baselines on GeoPlan-bench and API-Bank (qualitative claim in extract)

## Relevance to thesis
Tool-chain retrieval mechanisms are relevant for assembling indices, preprocessing, and foundation-model adapters in crop-stress pipelines where multi-step tool composition is required.

## Gaps / opportunities
- Agricultural domain tools not explicitly covered in benchmarks
- Continual-learning claims need verification of long-tail tool updates
- Opportunity to specialize tool dependency graphs for NDVI/EVI/stress-index chains

## Citation (APA 7th)
Wang, Z., Hou, D., et al. (2026). *Bidirectional Semantic Complementary Tool Retrieval for Remote Sensing Agents*. arXiv:2606.07538v1.

---
*Note written 2026-09-10 from first-page extract. Verify numbers in full PDF before formal proposal use.*
