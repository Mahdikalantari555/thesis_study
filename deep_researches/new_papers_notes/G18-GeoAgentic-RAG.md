# GeoAgentic-RAG: A Multi-Agent framework for autonomous geospatial reasoning and visual insight generation with LLM

**Authors:** Liang, C., Cui, Y., Shi, R., et al.  
**Year:** 2026  
**Venue:** International Journal of Applied Earth Observation and Geoinformation (IJAEOG), 147, 105195  
**DOI / arXiv:** 10.1016/j.jag.2026.105195  
**Local PDF:** 1-s2.0-S1569843226001111-main.pdf  
**Type:** methods  
**Thesis relevance:** HIGH  

## Summary
GeoAgentic-RAG is a multi-agent retrieval-augmented generation framework for autonomous geospatial reasoning and visual insight generation with LLMs. The pipeline proceeds through query parsing, semantic-spatial retrieval, task decomposition, executable geospatial analysis, and visualization, backed by a unified vector and raster database. Reported performance substantially exceeds conventional RAG and code-generation baselines.

## Methods / Architecture
- Multi-agent RAG framework.
- Pipeline: query parsing → semantic-spatial retrieval → task decomposition → executable geospatial analysis → visualization.
- Unified vector + raster database for semantic-spatial retrieval.

## Key quantitative results
- Pass rate: 85.3%.
- Answer correctness: 88.3%.
- Outperforms conventional RAG and code-generation baselines.

## Relevance to thesis
Offers a transferable multi-agent geospatial reasoning template: the parse–retrieve–decompose–execute–visualize loop can be adapted to arid crop-stress workflows (e.g., NDVI anomaly retrieval, soil-moisture statistics, and map generation for non-expert users).

## Gaps / opportunities
- Evaluation is on general geospatial QA, not crop-stress phenotyping.
- No explicit active-learning or EO-foundation-model selection components.
- Opportunity: embed REMSA-style FM selection and stress-specific tools into the agent toolchain.

## Citation (APA 7th)
Liang, C., Cui, Y., Shi, R., et al. (2026). GeoAgentic-RAG: A multi-agent framework for autonomous geospatial reasoning and visual insight generation with LLM. *International Journal of Applied Earth Observation and Geoinformation*, *147*, 105195. https://doi.org/10.1016/j.jag.2026.105195

---
*Note written 2026-09-10 from first-page extract. Verify numbers in full PDF before formal proposal use.*
