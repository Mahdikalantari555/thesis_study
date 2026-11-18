# AgroGraphNet — Intelligent Crop Disease Prediction Using Spatio-Temporal Graph Neural Networks

## Full citation
Bose, S. R., Jeba, J. A., Evangeline, N. C., Regin, R., Sameer Ali, M. M., Aravintha, S. J. V. (2025). Intelligent Crop Disease Prediction Using Spatio-Temporal Graph Neural Networks. *FMDB Transactions on Sustainable Intelligent Networks*, 2(4), 176–189. DOI: 10.69888/FTSIN.2025.000549. (Low-tier venue; treat cautiously.)

## Problem & setting
- Task: supervised crop disease prediction per farm (Healthy / Blight / Rust / Mosaic / Bacterial) by modeling farms as graph nodes; edges from spatial proximity (<5 km configurable) + environmental similarity.
- Data: farm-level CSVs — Sentinel-2 10 m vegetation indices (NDVI, NDRE, GNDVI, EVI, SAVI, NDWI), daily weather (temp, rain, humidity, wind) aggregated to 7-day/30-day windows, lab soil properties (pH, nutrients, texture), management records, agronomist disease labels. Multi-season; 72.2% healthy, Rust 9.4%, Blight 8.2%, Mosaic 6.2%, Bacterial 3.8%.

## Method
- Fully supervised (NOT SSL). Three GNNs compared: GCN (Kipf-Welling spectral conv), GraphSAGE (inductive neighbor sampling/aggregation), GAT (attention-weighted neighbor aggregation); GNN branch F→128→64 conv layers, ReLU, dropout (0.5 in diagram / 0.2 in training config); 3 hidden layers of 64 dims, Adam lr=0.001, batch 32, early stopping patience 10, converges in 40–60 epochs.
- Ensemble: 3 GNNs + Random Forest + SVM + Logistic Regression → majority voting + confidence averaging; CLI package for preprocessing/training/visualization.
- Evaluation protocols: random 60/20/20 split; spatial CV via k-means clusters on coordinates assigned wholly to train/val/test; temporal validation holding out the most recent season.

## Data & labels
- ~5,000 fields for full-graph training (synthetic graphs >50,000 nodes for scaling tests); labels from expert visual inspection + lab testing. Satellite features 10 m S2; Landsat mentioned only as complementary source.

## Results
- Accuracy: GAT 91.6% > GraphSAGE 89.7% > GCN 88.3%; GNNs beat CNN/MLP baselines that treat fields as isolated samples. GraphSAGE most robust across spatial/temporal evaluation conditions.
- Full-graph training on ~5,000 fields: 2–3 h on an RTX 3050 (16 GB RAM); mini-batch on >50k-node synthetic graphs 4–6 h; inference <10 s.
- Feature correlation matrix: NDVI–EVI correlation only 0.12, weather correlations −0.09 to 0.04 — used to justify multi-source integration.
- No per-class F1 table or confidence intervals reported; example output shows uniform 0.800 ensemble confidence for all Healthy predictions — weak evidentiary depth.

## What transfers to our thesis
- Limited direct transfer (supervised, no SSL, no time-series encoder), but the **field-as-node graph with edges from distance + environmental similarity** is a relevant relational prior for our sugarcane scheme: spatially adjacent fields share water/salinity stress drivers, and a graph over field embeddings from our SSL encoder could propagate stress evidence to label-scarce fields.
- The spatial k-means cluster CV and hold-out-last-season validation are exactly the cross-year generalization protocols we should adopt and report.
- Supports the argument that ignoring spatial context underperforms — a baseline motivation for including inter-field context in a lightweight multi-product model.

## Limitations / caveats
- Weak venue (FMDB Transactions), no public data ("available on request"), no code link, no ablation of edge construction, no precision/recall/F1 numbers despite claiming them; sample output table is degenerate (all identical predictions/confidence 0.800).
- Supervised only; requires agronomist labels; disease classes generic (not sugarcane, not water/salinity stress).
- Small real dataset (~5k fields), scaling numbers from synthetic graphs.

## Key numbers to quote in lit review
- GAT 91.6% / GraphSAGE 89.7% / GCN 88.3% accuracy for farm-level disease classification vs isolated-sample CNN/MLP baselines.
- Edge threshold 5 km spatial proximity + environmental similarity; node degree typically 2–3.
- Full-graph training of ~5,000 fields feasible on consumer GPU (RTX 3050) in 2–3 h; inference <10 s.
- Class imbalance: 72.2% healthy vs 3.8–9.4% per disease class.
