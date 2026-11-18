# SST-LTP: Self-Supervised Transformers for Long-Term Prediction of Landsat NDVI Time Series

## Full citation
Faran, I., Netanyahu, N.S., Roitberg, E., & Shoshany, M. (2025). "Self-Supervised Transformers for Long-Term Prediction of Landsat NDVI Time Series." ICPRAM 2025 (SCITEPRESS), pages 542-552. DOI: 10.5220/0013381700003905 (Bar-Ilan University / Technion). Code: github.com/FaranIdo/SST-LTP.

## Problem & setting
- Multi-decade NDVI forecasting on Landsat (1984-2024, missions 5/7/8/9) in a heterogeneous Mediterranean-to-arid desert-fringe landscape in Israel (rainfall 450 -> 250 mm/yr); challenges: strong seasonality, long-term trends, droughts, fires, abrupt changes, cloud gaps.
- Study area: 53.94 x 37.35 km, 30 m/px, 1,798x1,245 pixels, 2,238,510 pixel time series; two annual seasonal composites (Winter Oct-Apr, Summer May-Sep) averaged from scenes with <20% cloud -> 2 values/pixel/year.

## Method
- **Self-supervised pretext = direct future-value prediction**: input sequence O = {(NDVI_i, year_i, season_i)} for one pixel; model predicts NDVI at a *specified* future time N+delta in a single forward pass (not autoregressive — avoids error accumulation and repeated inference of AR models). Trained on MSE loss against observed NDVI; no labels needed.
- **Architecture**: BERT-style Transformer — 3 encoder blocks, 8 heads, embedding dim 256, dropout 0.2; observation embedding = NDVI linear embedding + sinusoidal continuous temporal encoding of normalized time t' = (2(t-t_start)+s) / (2(t_end-t_start+1)) (year+season as continuous cyclic signal, sin/cos harmonics) + positional encoding; decoder = MaxPool over temporal dimension + dense -> scalar NDVI. 200 epochs, Adam 1e-4 with 10-epoch warmup + exponential decay.
- Evaluation across input lengths (2.5-20 years) and horizons (1-5 years); baselines SVM (RBF), 3-layer FCN, CNN-1D, 3-layer LSTM trained on the same 10-sample (5-year) sequences.

## Data & labels
- Fully label-free (self-supervised on the NDVI series itself); 80/10/10 pixel split; windowing extracts (N past + 1 target) sequences.

## Results
- Best configuration: 10-year input sequences give the largest gains; 15-20 years marginally lower L1; performance declines with horizon (best next-year).
- **Next-year prediction with 10-year inputs: SST-LTP MAE 0.0338, MSE 0.0027, R2 0.8337** vs LSTM 0.0363/0.0031/0.8088, FCN 0.0383/0.7953, CNN-1D 0.0391/0.7810, SVM 0.0456/0.7459.
- Key architectural advantage: target year/season given as input -> direct multi-year prediction in one inference call (baselines need iterative calls).
- Failure mode: struggles with unexpected outliers/abrupt events (sudden disturbances) — model captures trends and seasonality, not anomalies.
- Qualitatively tracks high-variability samples better than LSTM (which oversmooths) and CNN/FCN.

## What transfers to our thesis
- **The Landsat time-series SSL pretext that most closely matches our stress-detection pipeline**: a transformer trained to predict future NDVI on unlabeled multi-decadal Landsat data; deviations of observed from predicted NDVI (the model's own residuals, which the authors flag as "outliers it cannot predict") are exactly the anomaly/stress signal our thesis exploits — the paper's stated weakness is our design's mechanism.
- **Temporal embedding design transfers directly**: normalized continuous year+season encoding (t' with sin/cos harmonics) handles multi-year Landsat composites; for 16-day sugarcane series, replace season in {0,1} with DOY phase — the formula is given and reusable.
- Two-composites-per-year (winter/summer) cloud-filtering strategy (<20% cloud scenes averaged) is a simple Landsat compositing baseline we can improve on with 16-day composites.
- Supports the thesis's "normal-behavior model + anomaly score" framing with quantitative evidence that prediction-based SSL outperforms LSTM/CNN/SVM on long Landsat series.
- Non-autoregressive direct multi-horizon prediction avoids error accumulation — relevant for forecasting ETa/CWSI trajectories to anticipate stress.

## Limitations / caveats
- Single variable (NDVI only), single scene/region, pixel-wise (no spatial context — authors list spatial correlation as future work); seasonal (2/year) not 16-day resolution.
- Not evaluated on cross-region transfer; no downstream stress/anomaly task quantified (anomaly detection is future work); pixel split may leak spatial autocorrelation between train/test pixels.
- Transformer is small but no parameter/FLOP reporting; no comparison to modern forecasting SSL (Presto, PatchTST, iTransformer empirically — only cited).
- Mediterranean natural vegetation; sugarcane is managed perennial with different phenology and irrigation dynamics.

## Key numbers to quote in lit review
- Self-supervised Transformer on 40 years of Landsat NDVI (1984-2024): next-year prediction MAE 0.0338, R2 0.834 — beating LSTM (0.0363/0.809), CNN-1D, FCN and SVM.
- 10 years of history is the practical optimum for multi-decadal prediction; gains saturate beyond 10-15 years.
- Direct (non-autoregressive) prediction with year/season conditioning outperforms iterative multi-step inference and avoids error accumulation.
- The model cannot predict abrupt outliers — the documented failure mode that anomaly-based stress detection can invert into a detection signal.
