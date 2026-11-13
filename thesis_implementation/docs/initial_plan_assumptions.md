# پلن اولیه و فرضیات — SSL Anomaly Detection (Phenology-Aware)

**تهیه:** 2026-11-01  
**وضعیت:** پلن اولیه (Draft) — برای تحقیق عمیق توسط Claude Agent  
**پروژه:** تشخیص تنش/آنومالی در مزارع نیشکر با SSL روی سری زمانی لندست  
**مکمل:** `SSL_Proposal/method_design_ssl.md`, `SSL_Proposal/scalable_config_and_extensions.md`, `data/DATA_SUMMARY.md`

---

## ۱. هدف این سند

این سند **پلن اولیه** است، نه پلن نهایی. هدف آن:

1. ثبت **فرضیات** و **محدودیت‌ها** پیش از تحقیق.
2. تعریف **سؤالات تحقیق** برای Claude Agent.
3. ارائه **پیشنهادات اولیه** (data format، model format، pipeline) که Claude Agent باید **بهبود دهد** و **best practices** را پیشنهاد کند.
4. شرح مفهوم **Phenology-Aware Anomaly** که هسته اصلی پروژه است.

Claude Agent باید این سند را بخواند، تحقیق عمیق انجام دهد، و **پلن نهایی** (با بهترین practices) را تولید کند.

---

## ۲. فرضیات (Assumptions)

### ۲.۱ داده
- **A1**: داده لندست ۸/۹ L2، ۲۰۱۳–۲۰۲۶، ۵۳۹ محصول، ۳۰m، ۴۹۰ مزرعه.
- **A2**: `Farms_subset` (۳۲ مزرعه R11) به‌عنوان validation set.
- **A3**: هواشناسی ERA5 روزانه (۵۰۰۲ روز، no gaps) موجود است.
- **A4**: محصولات METRIC (ETaDaily, CWSI, LST, NDVI, …) موجود هستند.
- **A5**: داده به‌صورت GeoTIFF (30m، EPSG:32639) ذخیره شده است.
- **A6**: Rust toolchain (۱.۹۰+) روی سیستم محلی نصب است.
- **A7**: GPU محلی (~۲۴GB) یا Colab (T4/A100) موجود است.

### ۲.۲ محدودیت‌های محاسباتی
- **C1**: پردازش اولیه روی **لپ‌تاپ شخصی** (نه سرور).
- **C2**: هر اسکریپت باید **progress bar** (tqdm/rich) داشته باشد.
- **C3**: هر اسکریپت باید **checkpoint/resume** داشته باشد (crash-safe).
- **C4**: **Resource throttling**: استفاده از کل CPU/RAM ممنوع (داغ شدن). پیش‌فرض: ۲ worker، ۲ thread BLAS.
- **C5**: داده باید **محلی** باشد (نه cloud-only)، اما **قابل انتقال** به Colab باشد.
- **C6**: زمان اجرای هر مرحله باید **قابل تخمین** باشد (ETA).

### ۲.۳ مفهومی
- **M1**: هدف = **label-free anomaly detection** (تشخیص انحراف از الگوی نرمال).
- **M2**: معماری اولیه = 3D-CAE (سبک) + Tiny CNN-Mamba (مقایسه).
- **M3**: ورودی اولیه = raw bands + LST (شاخص‌ها ablation).
- **M4**: سطح تحلیل اولیه = field-mean (zonal mean).
- **M5**: Cadence = Landsat 16-روزه.

---

## ۳. Phenology-Aware Anomaly (هسته اصلی)

### ۳.۱ تعریف

**Phenology-Aware Anomaly** یعنی:

> هر تاریخ (observation) نسبت به **فاز فنولوژیک خودش** (نه تاریخ تقویمی) و نسبت به **همان فاز در سال‌های دیگر** مقایسه می‌شود.

به‌عبارت دیگر:

- **DOY (Day of Year) تقویمی** کافی نیست (چون فصل رشد در سال‌های مختلف متفاوت است).
- **فاز فنولوژیک** (onset / peak / senescence) باید از منحنی NDVI هر مزرعه/سال استخراج شود.
- **Baseline نرمال چند-ساله**: برای هر مزرعه و هر فاز فنولوژیک، median + MAD روی سال‌های نرمال.
- **Anomaly score**: انحراف از baseline چند-ساله (z-score)، نه فقط از میانگین فصل.

### ۳.۲ چالش‌ها (برای تحقیق)

1. **استخراج فاز فنولوژیک**: چگونه onset/peak/senescence را از NDVI time series استخراج کنیم؟ (Savitzky-Golay smoothing? TIMESAT? DL-based?)
2. **هم‌راستاسازی بین‌ساله**: DOY ± window vs فاز فنولوژیک vs GDD (Growing Degree Days)?
3. **سال‌های نرمال**: کدام سال‌ها "نرمال" هستند؟ (عملکرد بالا? CWSI پایین? expert-selected?)
4. **Intra-field**: آیا فاز فنولوژیک درون یک مزرعه یکنواخت است؟ (پچ‌های مختلف ممکن است فاز متفاوتی داشته باشند.)
5. **Cross-crop**: آیا روش فاز-محور به محصولات دیگر تعمیم می‌یابد؟
6. **Missing data**: اگر یک فاز در یک سال داده نداشته باشد، چه؟

### ۳.۳ پیشنهادات اولیه (برای بهبود توسط Claude)

- **Phenology extraction**: TIMESAT یا Python (scipy.signal.find_peaks + Savitzky-Golay) روی NDVI.
- **Alignment**: ترکیب DOY ± 15d و فاز فنولوژیک، انتخاب پایدارترین.
- **Baseline**: median + MAD روی سال‌های نرمال (مثلاً ۲۰۱۵–۲۰۱۷ یا سال‌های با عملکرد بالا).
- **Anomaly score**: z-score per (field, phenophase, year).
- **Retrieval**: kNN در embedding space برای "سال‌های مشابه".

---

## ۴. Data Format — پیشنهاد اولیه (Claude باید بهبود دهد)

### ۴.۱ پیشنهاد: Zarr v3

- **فرمت**: Zarr (v2 یا v3) با xarray.
- **دلیل**: chunked، cloud-native، consolidated metadata، empty chunks skip، fsspec.
- **Chunking**: قابل تنظیم (time-series vs spatial slice).
- **Compression**: Blosc/zstd (level 3) یا lz4.
- **GeoZarr**: CRS، dimensions، coordinates، overviews.

### ۴.۲ سؤالات برای Claude (Best Practices)

1. **Zarr v2 vs v3**: کدام برای این use case بهتر است؟ (v3 sharding، consolidated metadata differences)
2. **Chunk shape optimal**: برای phenology-aware anomaly (field-mean + time-series) چه chunk shape؟
3. **GeoZarr compliance**: آیا باید GeoZarr standard را کامل پیاده کنیم؟ (overviews، CRS encoding)
4. **Conversion pipeline**: GeoTIFF → Zarr بهینه‌ترین روش؟ (rasterio + xarray vs GDAL vs terrio)
5. **Storage layout**: یک Zarr store برای همه bands یا جداگانه؟ (band-major vs time-major)
6. **Weather integration**: هواشناسی را به‌عنوان coordinate یا data variable ذخیره کنیم؟
7. **Metadata**: چه metadata باید ذخیره شود؟ (farm_id، block، variety، age، …)

### ۴.۳ پیشنهاد اولیه Conversion Pipeline

```
GeoTIFF (per scene, per band)
    ↓
rasterio.open() → read window
    ↓
xarray.DataArray (with dims: time, y, x)
    ↓
stack bands → Dataset
    ↓
chunk & compress
    ↓
to_zarr() (consolidated=True)
```

**Progress**: tqdm per scene.  
**Checkpoint**: manifest of processed scenes (JSON).  
**Throttle**: 2 workers، memory check.

---

## ۵. Model Format — پیشنهاد اولیه (Claude باید بهبود دهد)

### ۵.۱ پیشنهاد: PyTorch + SafeTensors + ONNX (optional)

- **Training**: PyTorch (Lightning) — native، انعطاف‌پذیر.
- **Checkpoint**: SafeTensors (سریع، امن، zero-copy) یا PyTorch `.pt`.
- **Inference (production)**: ONNX (cross-platform، Rust/C++ inference) یا TorchScript.
- **Export**: `torch.onnx.export()` یا `safetensors.torch.save_file()`.

### ۵.۲ سؤالات برای Claude (Best Practices)

1. **SafeTensors vs .pt**: کدام برای checkpointing بهتر است؟ (SafeTensors: no pickle، fast loading)
2. **ONNX vs TorchScript**: کدام برای inference روی edge (پهپاد) بهتر است؟
3. **Model versioning**: چگونه model versions را track کنیم؟ (MLflow model registry vs DVC vs W&B)
4. **Quantization**: آیا INT8/FP16 quantization برای edge لازم است؟ (torch.quantization / ONNX Runtime)
5. **Serialization**: آیا model architecture را هم serialize کنیم یا فقط weights؟ (پیشنهاد: architecture در کد، weights در SafeTensors)
6. **Reproducibility**: چگونه ensure کنیم model training reproducible است؟ (seed، deterministic ops، environment pinning)

### ۵.۳ پیشنهاد اولیه Model I/O

```python
# Save (training)
from safetensors.torch import save_file
save_file(model.state_dict(), "model.safetensors")

# Load (inference)
from safetensors.torch import load_file
state_dict = load_file("model.safetensors")
model.load_state_dict(state_dict)

# Export (production)
import torch.onnx
torch.onnx.export(model, dummy_input, "model.onnx", opset_version=17)
```

---

## ۶. Pipeline Architecture — پیشنهاد اولیه (Claude باید بهبود دهد)

### ۶.۱ پیشنهاد: Hydra + MLflow + DVC + Optuna

```
configs/          # Hydra composition
    base.yaml     # system, paths, device
    model/        # 3dcae.yaml, cnn_mamba.yaml
    data/         # field_mean.yaml, full_raster.yaml
    input/        # bands, weather, indices toggles
    experiment/   # ablation configs
    profile/      # edge/laptop/server

data/
    ingest/       # GeoTIFF → Zarr (Rust-accelerated)
    weather/      # ERA5 fusion
    datasets/     # PyTorch Dataset classes

models/           # architectures
training/         # Lightning modules
experiments/      # runner + sweep
xai/              # Captum/tint attribution
benchmark/        # metrics, comparison tables
tracking/         # MLflow + DVC integration
```

### ۶.۲ سؤالات برای Claude (Best Practices)

1. **Config management**: Hydra vs OmegaConf-only vs Pydantic-settings؟
2. **Experiment tracking**: MLflow vs W&B vs Neptune؟ (پیشنهاد: MLflow local + W&B optional)
3. **Data versioning**: DVC vs LakeFS vs Delta Lake؟ (پیشنهاد: DVC برای data، MLflow برای models)
4. **HP tuning**: Optuna vs Ray Tune vs Hydra multirun؟ (پیشنهاد: Optuna + MLflow nested runs)
5. **Pipeline orchestration**: DVC pipeline vs Prefect vs Airflow vs Makefile؟ (پیشنهاد: DVC pipeline برای reproducibility)
6. **Testing**: pytest vs unittest؟ (پیشنهاد: pytest + pytest-cov)
7. **Logging**: logging vs loguru vs structlog؟ (پیشنهاد: loguru برای سادگی)
8. **Type checking**: mypy vs pyright؟ (پیشنهاد: pyright برای سرعت)

---

## ۷. Phenology-Aware Anomaly — Pipeline پیشنهادی

### ۷.۱ مراحل

```
1. Extract phenology per field per year
   - NDVI time series → Savitzky-Golay smoothing
   - find_peaks → onset, peak, senescence
   - Output: phenology calendar (field, year, phase, doy)

2. Align observations to phenophase
   - Map each observation to nearest phenophase
   - Interpolate to standard phenophase grid (e.g., 10 phases per season)

3. Build multi-year normal baseline
   - For each (field, phenophase): median + MAD over normal years
   - Normal years: expert-selected or top-quartile yield

4. Compute anomaly score
   - z-score: (obs - baseline_median) / baseline_MAD
   - Per field, per phenophase, per year

5. Detect anomalous runs
   - Threshold: median + k·MAD (robust)
   - Flag: score > threshold for ≥ N consecutive phenophases

6. Validate
   - Agreement with CWSI, ETaDaily, yield records
   - Expert review
```

### ۷.۲ سؤالات برای Claude (Research Questions)

1. **Phenology extraction method**: TIMESAT vs scipy vs DL-based? (کدام برای Landsat 16-روزه بهتر است؟)
2. **Phenophase granularity**: چند فاز؟ (3: onset/peak/senescence vs 10: fine-grained)
3. **Alignment method**: DOY ± window vs phenophase vs GDD? (کدام پایدارتر است؟)
4. **Normal years selection**: expert-selected vs data-driven (top-quartile yield/CWSI)?
5. **Intra-field phenology**: آیا فاز درون مزرعه یکنواخت است؟ (اگر نه، چگونه handle کنیم؟)
6. **Missing phenophase**: اگر یک فاز در یک سال داده نداشته باشد، چه؟ (interpolation vs skip)
7. **Cross-crop generalization**: آیا روش فاز-محور به محصولات دیگر تعمیم می‌یابد؟
8. **Validation**: چگونه phenology-aware anomaly را validate کنیم؟ (CWSI correlation? expert review?)

---

## ۸. Rust Acceleration — پیشنهاد اولیه

### ۸.۱ کتابخونه‌های آماده (استفاده فوری)

| کتابخونه | کاربرد | وضعیت |
|---------|--------|-------|
| **oxidized-rasterstats** | zonal stats (drop-in rasterstats) | آماده، ۷–۱۷× سریع‌تر |
| **eo-processor** | spectral indices، temporal stats، zonal_stats، RF | آماده |
| **terrio** | GeoTIFF→Zarr conversion، reproject، warp | early dev، برای I/O |
| **rasterqc** | raster statistics | آماده |

### ۸.۲ سؤالات برای Claude

1. **terrio vs rasterio+GDAL**: کدام برای GeoTIFF→Zarr بهتر است؟ (terrio: pure Rust، no C deps; rasterio: mature، GDAL-backed)
2. **PyO3 custom**: آیا نیاز به Rust custom (PyO3) برای heavy loops هست؟ (پیشنهاد: اول آماده‌ها، بعد custom)
3. **Parallelism**: rayon vs multiprocessing vs Dask? (پیشنهاد: rayon برای Rust، Dask برای Python)
4. **Memory management**: چگونه large rasters را بدون OOM پردازش کنیم؟ (chunked reading، streaming)

---

## ۹. Explainability (XAI) — پیشنهاد اولیه

### ۹.۱ کتابخونه‌ها

| کتابخونه | کاربرد |
|---------|--------|
| **Captum** | IG، GradCAM، DeepLIFT، GradientSHAP |
| **time_interpret (tint)** | TemporalIntegratedGradients، TemporalOcclusion، DynaMask |
| **tsCaptum** | segmentation-based SHAP (equal-length segmentation بهترین) |
| **SHAP** | TreeExplainer (RF/XGB)، KernelSHAP |
| **meteors** | XAI برای hyperspectral/multispectral |

### ۹.۲ Phenology-Aware XAI

- **Temporal attribution**: کدام phenophase بیشترین تأثیر را دارد؟
- **Channel attribution**: کدام band/weather variable بیشترین تأثیر؟
- **Field attribution**: کدام مزرعه بیشترین anomaly؟
- **Faithfulness**: deletion/insertion AUC برای phenophase-level attribution.

### ۹.۳ سؤالات برای Claude

1. **Temporal XAI method**: TemporalIntegratedGradients vs SHAP segmentation vs occlusion؟
2. **Phenophase-level attribution**: چگونه attribution را به phenophase map کنیم؟
3. **Channel dropping**: چگونه channel dropping experiments را systematic انجام دهیم؟ (ablation study)
4. **Faithfulness metrics**: deletion/insertion AUC vs comprehensiveness/sufficiency؟

---

## ۱۰. Benchmarking — پیشنهاد اولیه

### ۱۰.۱ کتابخونه‌ها

| کتابخونه | کاربرد |
|---------|--------|
| **chronobench** | registry-driven benchmarking، sweep، CSV output |
| **torchgeo-bench** | frozen-backbone evaluation، KNN/linear probe |
| **GEO-Bench-2** | standardized EO benchmark، ۱۹ dataset |
| **MLflow** | experiment tracking، model registry |

### ۱۰.۲ Benchmarking Strategy

- **Baseline models**: RF/XGBoost (indices)، 3D-CAE، CNN-Mamba (supervised)، Presto features.
- **Metrics**: F1، AUC-ROC، Cohen's Kappa، cross-year stability، XAI faithfulness.
- **Ablation**: drop bands/weather → measure impact.
- **Comparison**: field-mean (zonal) vs full-raster (patch-level).

### ۱۰.۳ سؤالات برای Claude

1. **Benchmark framework**: chronobench vs custom MLflow-based؟
2. **Metrics**: کدام metrics برای anomaly detection مناسب‌ترند؟ (AUC-PR vs AUC-ROC vs F1)
3. **Cross-validation**: leave-one-year-out vs leave-one-field-out vs temporal split؟
4. **Statistical significance**: چگونه نتایج را statistically compare کنیم؟ (paired t-test، Wilcoxon، bootstrap CI)

---

## ۱۱. Deliverable مورد انتظار از Claude Agent

Claude Agent باید:

1. **تحقیق عمیق** درباره هر بخش بالا انجام دهد.
2. **Best practices** را پیشنهاد دهد (data format، model format، pipeline، etc.).
3. **پلن نهایی** را بنویسد (با بهترین practices).
4. **سؤالات باز** را پاسخ دهد یا پیشنهاد دهد.
5. **کد نمونه** (skeleton) برای هر مرحله بنویسد.
6. **Memory log** به‌روزرسانی کند.

---

## ۱۲. سؤالات باز برای کاربر (پس از تحقیق Claude)

1. **Phenology method**: TIMESAT vs scipy vs DL? (Claude باید پیشنهاد دهد)
2. **Normal years**: expert-selected vs data-driven? (Claude باید پیشنهاد دهد)
3. **Zarr chunking**: time-series vs spatial? (Claude باید benchmark کند)
4. **Model format**: SafeTensors vs ONNX? (Claude باید پیشنهاد دهد)
5. **Pipeline orchestrator**: DVC vs Prefect? (Claude باید پیشنهاد دهد)
6. **terrio trial**: آیا اسکریپت آزمایشی terrio→Zarr بنویسیم؟ (Claude باید تصمیم بگیرد)

---

## ۱۳. خلاصه

| بخش | پیشنهاد اولیه | Claude باید |
|------|---------------|-----------|
| Data format | Zarr v3 (xarray) | Best practices + chunking optimization |
| Model format | PyTorch + SafeTensors + ONNX | Best practices + quantization |
| Pipeline | Hydra + MLflow + DVC + Optuna | Best practices + orchestration |
| Phenology | TIMESAT/scipy + median baseline | Best method + validation |
| Rust | oxidized-rasterstats + eo-processor + terrio | Best I/O method |
| XAI | Captum + tint + tsCaptum | Best temporal XAI |
| Benchmark | chronobench + MLflow | Best metrics + significance |

---

*این سند پلن اولیه است. Claude Agent باید تحقیق عمیق انجام دهد و پلن نهایی را تولید کند.*
*آخرین به‌روزرسانی: 2026-11-01*
