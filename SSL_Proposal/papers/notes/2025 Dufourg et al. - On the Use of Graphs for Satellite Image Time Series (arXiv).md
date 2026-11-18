# On the Use of Graphs for Satellite Image Time Series

## Full citation
Dufourg, C., Pelletier, C., May, S., & Lefevre, S. (2025). "On the use of Graphs for Satellite Image Time Series." IEEE Geoscience and Remote Sensing Magazine, DOI: 10.1109/MGRS.2025.3622200; arXiv:2505.16685v2 (Universite Bretagne Sud/IRISA, CNES, UiT). Code: github.com/corentin-dfg/graph4sits.

## Problem & setting
- Survey + methodology + two case studies on representing satellite image time series (SITS) as **spatio-temporal graphs** (extension of Object-Based Image Analysis): nodes = spatio-temporal objects (fields/regions), spatial edges (adjacency) + spatio-temporal edges (object states linked across dates). Positions graphs vs pixel-grid methods (CNN/ViT) and against DTDG/CTDG dynamic-graph formalisms.
- Case study 1: land-cover mapping on DynamicEarthNet (75 areas worldwide, Planet Fusion 3 m daily Jan 2018-Dec 2019, 24 monthly labeled dates, 7 classes). Case study 2: NDWI forecasting on SEN2DWATER (3,682 filtered Sentinel-2 64x64 sequences, 17 basins in Italy/Spain, ~2-month revisit, 6 input acquisitions -> predict next).

## Method
- **Graph construction pipeline**: (i) collect SITS considering resolution trade-offs; (ii) entity definition — objects from segmentation (SLIC, Felzenszwalb), land registers, or clustering of similar disconnected pixels; endurantist (object persists, properties evolve) vs perdurantist (3D spatio-temporal objects) paradigms; features = per-region spectral statistics (mean/std/min/max per band); (iii) edges: region adjacency (spatial) + footprint overlap between consecutive dates (spatio-temporal); optionally attributed/weighted edges.
- **Case 1**: Felzenszwalb segmentation per date; GNN encoders (4 layers, hidden 64; 2 spatial + 2 temporal aggregation layers) with GCN/GraphSAGE/GIN/GATv2/ResGatedGCN vs MLP (edge-free OBIA) vs pixel-based U-Net; CE loss, Adam 1e-4, 100 epochs.
- **Case 2**: GraphCast-style encoder-processor-decoder on a coarse SLIC superpixel mesh (256 superpixels); pixel time series + spatio-temporal positional embedding (sin lat, sin/cos lon, sin DOY) via MLPs into node features; residual prediction (predicts change from last state); Huber loss, Adam 1e-4; baselines LSTM, ConvLSTM, TDCNN-ConvLSTM, persistence, input-average.

## Data & labels
- Supervised (monthly pixel labels in case 1; next-image NDWI in case 2); authors note semi-supervised extension with the unlabeled daily acquisitions is possible. Basin-disjoint train/test split enforced in case 2 (85:15).

## Results
- **Case 1 (DynamicEarthNet)**: U-Net best (val mIoU 33.69, test OA 69.85); GraphSAGE best graph model (val mIoU 31.48, test OA 68.21) with 35x fewer params (27,782 vs 983,654) and 5x faster training (2.32 h vs 10.63 h); MLP 29.42 mIoU — spatio-temporal context adds ~2 pp mIoU over context-free OBIA; anisotropic aggregators (GATv2, ResGatedGCN) and sum-aggregation (GIN) underperform mean-aggregation (GraphSAGE). U-Net/SITS control (same batch regime) collapses to 9.25 mIoU, showing spatio-temporal modeling helps when data variety per batch is limited. Segmentation ceiling ~91-92% OA; object-based error is not the bottleneck. Preprocessing (graph building) = 98% of test time (34 s/SITS, CPU segmentation).
- **Case 2 (NDWI forecasting)**: graph-based model best RMSE 0.1097 and PSNR 26.42 vs TDCNN-ConvLSTM 0.1111/25.68, LSTM 0.1162, persistence 0.1332; graph model generalizes better to under-represented NDWI values and water/impervious targets; TDCNN-ConvLSTM better on vegetation; both fail on abrupt changes (harvest, drought) due to low temporal frequency. Superpixel count (1-4096) barely affects RMSE — regional analysis suffices. Input length ablation: 1-2 acquisitions worse than persistence; 6 (full year) best (RMSE 0.1097 vs 0.1200 at 5).

## What transfers to our thesis
- **Field-as-node graph representation for sugarcane**: parcel/field objects with per-date spectral statistics and adjacency + cross-date edges is a natural, lightweight alternative to pixel grids for 16-day Landsat series — reduces working units (memory/compute), supports farmer-facing field-level outputs, and lets an SSL encoder operate at field granularity.
- Case-study design lessons for our cross-year models: basin/field-disjoint splits (avoid leakage), full-year input windows (1-2 dates worse than persistence — a caution for short-window stress detection), and the residual-prediction trick (predict change from last state, as GraphCast) which maps to forecasting NDVI/ETa anomalies rather than absolute values.
- Honest negative results to cite: GNNs on SITS still trail pixel CNNs (U-Net) on segmentation; aggregator choice matters (mean > attention/gated); preprocessing (object extraction) dominates inference cost — supports the argument that pixel/time-series models remain the pragmatic choice for our Landsat pipeline unless field objects are pre-existing (as in our sugarcane case).
- Multi-year annual cycle argument: models need >=6 acquisitions (~1 year) to learn seasonality — justifies our multi-year Landsat input windows for normal-behavior learning.

## Limitations / caveats
- Graph case study 1 clearly loses to U-Net (mIoU 31.5 vs 33.7 val); graph construction is slow and hand-crafted; no SSL or label-free pipeline anywhere in the paper.
- Case 2 forecasting limited by ~2-month revisit and cloud filtering (3,682/5,264 sequences kept); abrupt changes unpredicted — analogous to our stress-onset problem.
- No thermal/ETa products; optical only; NDWI-specific conclusions may not transfer to vegetation indices.
- Survey sections are comprehensive but the empirical evidence rests on two small case studies.

## Key numbers to quote in lit review
- Spatio-temporal GNN (GraphSAGE) matches U-Net on land-cover mapping from daily Planet SITS with 35x fewer parameters and 5x faster training (OA 68.2% vs 69.9%), but U-Net still leads mIoU (33.7 vs 31.5).
- Spatio-temporal context improves over context-free object features by ~2 pp mIoU (GraphSAGE 31.48 vs MLP 29.42).
- GraphCast-style superpixel-mesh model achieves best NDWI forecasting (RMSE 0.1097, PSNR 26.42) beating ConvLSTM variants; needs >=6 acquisitions (~1 year) to beat even persistence.
- 98% of graph-model inference time is graph construction (object segmentation) — a practical scalability caveat for field-level graph pipelines.
