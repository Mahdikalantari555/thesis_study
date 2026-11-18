# پلن نهایی — تشخیص آنومالی فنولوژی‌محور در مزارع نیشکر با SSL روی سری زمانی لندست

**تاریخ:** 2026-11-01 · **نسخه:** 1.0 · **مبنا:** `initial_plan_assumptions.md`

**برچسب‌ها:** «تأییدشده» = از منبع بررسی‌شده؛ «قضاوت» = استدلال روش‌شناختی من؛ «benchmark» = باید در Sprint 0 آزمایش شود.

## 0. خلاصهٔ اجرایی

هستهٔ پروژه این است که هر مشاهده نسبت به **همان مرحلهٔ رشد** در چرخه‌های نرمال دیگر سنجیده شود. برای نیشکر، «مرحله» را باید با **روز از آخرین برداشت** (و GDD) تعریف کرد، نه DOY تقویمی؛ چون چرخهٔ نیشکر به برداشت وابسته است و شکل منحنی در کاشت اول و ratoon فرق دارد. واحد تحلیل «سال» نیست، **«چرخه» (cycle)** است.

مسیر کار: اول یک baseline آماری robust (ارزان و قابل‌تفسیر)، بعد SSL فقط اگر به‌طور معنادار از آن بهتر باشد. Rust در فاز اول لازم نیست؛ فقط interface آن از ابتدا طوری طراحی می‌شود که بعداً بدون بازنویسی وصل شود.

| موضوع | تصمیم | وضعیت |
| --- | --- | --- |
| دادهٔ فاز 1 | `fields.zarr` (field × time × band) + جدول متادیتا Parquet؛ cube رستری فقط فاز 3 | قضاوت |
| Zarr | v3 با sharding؛ از GeoZarr فقط CRS + transform | تأییدشده (وضعیت استاندارد) |
| هواشناسی | store جدا (`era5.zarr`)، نه coordinate؛ GDD در لحظهٔ استفاده محاسبه می‌شود | قضاوت |
| محور هم‌راستاسازی | days-since-harvest (اصلی)؛ GDD، DOY و landmark registration برای مقایسه | قضاوت + شواهد |
| چرخهٔ نرمال | trimming تکراری robust + فیلتر ETa/yield در صورت وجود؛ بدون CWSI | قضاوت |
| فنولوژی | Whittaker/SG + قواعد برداشت؛ TIMESAT فقط برای مقایسه | قضاوت |
| مدل فاز 2 | GRU-AE و masked temporal transformer (1D)؛ CNN-Mamba برای مقایسه | قضاوت |
| 3D-CAE | فقط فاز 3 (patch-level)؛ با field-mean سازگار نیست | قضاوت |
| checkpoint | Lightning `.ckpt` برای resume؛ SafeTensors برای نسخهٔ نهایی؛ ONNX مؤخر | قضاوت |
| pipeline | Hydra + MLflow (SQLite) + DVC pipeline؛ Optuna بعد از فاز 2 | قضاوت |
| Rust | gated: بعد از profiling؛ interface از ابتدا | قضاوت |
| terrio | trial محدود و زمان‌دار، فقط برای تبدیل cube در فاز 3 | benchmark |
| benchmark | چارچوب سفارشی روی MLflow + تزریق آنومالی مصنوعی | قضاوت |

## 1. بازنگری فرضیات سند اولیه

چند فرض در سند اولیه با هم یا با هدف پروژه ناسازگارند و باید قبل از شروع اصلاح شوند:

1. **M2 و M4 ناسازگارند.** 3D-CAE به patch مکانی نیاز دارد، اما تحلیل field-mean یک سری چندمتغیرهٔ 1 بعدی تولید می‌کند. بنابراین در فاز 1 و 2 مدل‌ها 1D هستند و 3D-CAE به فاز 3 می‌رود.
2. **ریسک دایره‌ای بودن validation (M3 با A4).** اگر LST ورودی مدل باشد و CWSI برای اعتبارسنجی استفاده شود، همبستگی تا حدی ذاتی است (CWSI معمولاً از LST و هواشناسی ساخته می‌شود؛ این را در pipeline خودتان تأیید کنید). راه‌حل: ablation بدون LST، و اعتبارسنجی اصلی با ETa و yield.
3. **M5 (cadence 16 روزه) فرض ساده‌ای است.** 538 محصول قابل‌استفاده (از ۵۳۹ فایل؛ متادیتای 2022-08-07 خراب است — OQ5، حل‌شده 2026-11-14) در حدود 13.8 سال یعنی نزدیک 39 مشاهده در سال بعد از حذف ابر؛ نمونه‌برداری نامنظم است و بعد از شروع Landsat 9 (2021) متراکم‌تر می‌شود. هیچ مرحله‌ای نباید شبکهٔ منظم فرض کند: از timestamp واقعی، mask و فیلد `sensor` استفاده کنید.
4. **Farms\_subset (A2).** پیشنهاد: انتخاب مدل و hyperparameter با CV بلوکی (بر اساس منطقه) روی بقیهٔ مزارع انجام شود و Farms\_subset فقط برای گزارش نهایی بماند، وگرنه validation و tuning یکی می‌شوند. مزارع آن نباید در آموزش یا ساخت baseline باشند.
5. **A7 (GPU).** فاز 1 و بخش آماری فاز 2 روی CPU کاملاً شدنی است. GPU فقط برای Transformer/Mamba و فاز 3 لازم است.
6. **«سال نرمال» باید «چرخهٔ نرمال» شود.** چرخه‌ها بین مزارع هم‌زمان نیستند و هر چرخه ممکن است دو سال تقویمی را پوشش دهد.

## 2. فازبندی و gateها

| فاز | محتوا | خروجی | gate خروج |
| --- | --- | --- | --- |
| 0 (Sprint 0) | audit داده، `fields.zarr`، segmentation چرخه، QC روی 30 مزرعه | `fields.zarr`، جدول چرخه‌ها، گزارش QC | **G0:** تشخیص برداشت روی مزارع QC قابل‌قبول است و بیشتر مزارع حداقل چند چرخهٔ کامل دارند (آستانه را بعد از audit تعیین کنید) |
| 1 | baseline آماری phenology-aware (B0 تا B2) و ارزیابی | امتیاز آنومالی، گزارش مقایسه | **G1:** B1 (phase-aware) از B0 (تقویمی) در تزریق مصنوعی و proxyها بهتر است؛ وگرنه محور هم‌راستاسازی بازنگری می‌شود |
| 2 | مدل‌های SSL 1D روی field-level | مدل‌ها، مقایسهٔ کامل | **G2:** SSL با CI معنادار از B1 بهتر است؛ وگرنه نقش آن به embedding/retrieval محدود می‌شود |
| 3 | patch-level، 3D-CAE، XAI، cube.zarr | نقشهٔ آنومالی درون‌مزرعه | **G3 (Rust):** فقط بعد از profiling (بخش 8) |

اصل کار: هر فاز با ماژول + تست + CLI نازک پیش می‌رود و notebook فقط برای EDA است. هیچ فازی بدون عبور از gate قبلی شروع نمی‌شود.

## 3. لایهٔ داده

### 3.1 ساختار

```
data/
  raw/landsat/             # GeoTIFFهای اصلی (read-only، با DVC)
  geo/fields.gpkg          # هندسهٔ مزارع
  geo/fields.parquet       # farm_id, block, variety, region (مثل R11), سن/ratoon, ...
  interim/field_mask.tif   # raster با field_id روی شبکهٔ 30m (یک بار ساخته می‌شود)
  interim/zonal/*.parquet  # خروجی هر صحنه (واحد checkpoint)
  processed/fields.zarr    # فاز 1: (field, time, band)
  processed/era5.zarr      # (time, var) روزانه
  processed/cube.zarr      # فاز 3، اختیاری
  manifests/*.sqlite       # وضعیت پردازش هر صحنه
```

**چرا `fields.zarr` اول؟** 490 مزرعه × 539 زمان × چند band فقط چند ده مگابایت است. پس در فاز 1 chunking مسئله نیست (یک chunk کافی است) و نیازی به تبدیل کل رسترها نیست. سؤال chunking فقط برای `cube.zarr` در فاز 3 مطرح می‌شود.

### 3.2 تصمیم‌ها دربارهٔ Zarr

- **v2 یا v3:** v3 با sharding. مشخصات GeoZarr هنوز در حال تثبیت است: سه convention پایه (multiscales، projection، spatial) در اکتبر 2025 منتشر شد و فاز دوم درایور GDAL هنوز در حال انجام بود. پس **فقط** CRS و affine transform را کامل ذخیره کنید؛ overview/pyramid برای تحلیل field-mean لازم نیست. (تأییدشده؛ منبع: EOPF/Development Seed)
- **consolidated metadata:** در v3 جزو مشخصات نیست و برای store محلی لازم نیست.
- **dtype و compression:** برای cube: `int16` با `scale_factor`/`add_offset` در attrs (ضرایب را از متادیتای محصول بخوانید، نه از حافظه)، `fill_value` برای nodata، codec: zstd سطح 3 با shuffle. برای `fields.zarr`: float32.
- **chunk در `cube.zarr` (فقط فاز 3، benchmark):** سه پیکربندی را روی سه الگوی دسترسی بسنجید: (الف) خواندن همهٔ زمان‌های یک مزرعه، (ب) خواندن یک صحنه، (ج) توان نوشتن در ingest. کاندیداها: `C1` ingest با (time=1, y=x=512)؛ `C2` train با inner chunk (time=همه، 64×64) و shard (512×512)؛ `C3` حد وسط (time=16، 128×128). روش: ingest با C1 (resume‌پذیر)، سپس یک بار rechunk به C2.
- **هواشناسی:** store جدا و متغیرهای خام روزانه (Tmean، بارش، تابش، ...). GDD با Tbase قابل تنظیم در لحظهٔ استفاده محاسبه شود و در Zarr ثابت نشود، چون Tbase یک hyperparameter است.
- **متادیتا:** فقط در `fields.parquet` (farm\_id، block، variety، region، سن/ratoon، ...). attrs در Zarr فقط نسخه، CRS، hash منشأ و ترتیب band را نگه دارد.

### 3.3 pipeline ingest (فاز 0)

به‌جای per-polygon zonal stats، یک بار `field_mask.tif` ساخته می‌شود و برای هر صحنه با `bincount` آمار گرفته می‌شود؛ این کار معمولاً بسیار سریع‌تر از rasterstats است و در فاز 1 نیاز به Rust را عملاً حذف می‌کند (benchmark کنید).

مراحل: (1) `build_field_mask` ← (2) برای هر صحنه: خواندن band‌ها، ساخت mask کیفیت (cloud/shadow/cirrus/snow از QA\_PIXEL در صورت وجود؛ بیت‌ها را از مستندات محصول خودتان تأیید کنید)، zonal stats، نوشتن اتمیک `zonal/{scene}.parquet` ← (3) تجمیع در `fields.zarr`.

```python
# src/ssl_anomaly/utils/throttle.py
import os

def limit_threads(n: int = 2) -> None:
    """قبل از import کردن numpy/torch صدا زده شود (اول CLI)."""
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS", "GDAL_NUM_THREADS"):
        os.environ[key] = str(n)
    os.environ.setdefault("GDAL_CACHEMAX", "512")  # MB

def lower_priority() -> None:
    import psutil
    p = psutil.Process()
    p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 10)

def wait_for_headroom(min_free_gb: float = 2.0, poll_s: float = 5.0) -> None:
    import time, psutil
    while psutil.virtual_memory().available < min_free_gb * 2**30:
        time.sleep(poll_s)
```

```python
# src/ssl_anomaly/utils/manifest.py  — checkpoint/resume در سطح هر آیتم
import sqlite3

class Manifest:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute("""CREATE TABLE IF NOT EXISTS items(
            key TEXT PRIMARY KEY, status TEXT, seconds REAL, error TEXT)""")

    def pending(self, keys):
        done = {r[0] for r in self.db.execute(
            "SELECT key FROM items WHERE status='done'")}
        return [k for k in keys if k not in done]

    def mark(self, key, status, seconds=0.0, error=None):
        self.db.execute("INSERT OR REPLACE INTO items VALUES (?,?,?,?)",
                        (key, status, seconds, error))
        self.db.commit()
```

```python
# src/ssl_anomaly/io/zonal.py
import numpy as np, pandas as pd

def zonal_scene(bands: dict[str, np.ndarray], valid: np.ndarray,
                labels: np.ndarray, n_fields: int) -> pd.DataFrame:
    """labels: int32، 0 = بیرون از مزارع؛ valid: bool (بدون ابر/سایه/...)"""
    inside = labels > 0
    lab, ok = labels[inside], valid[inside]
    n_all = np.bincount(lab, minlength=n_fields + 1)
    n_ok = np.bincount(lab[ok], minlength=n_fields + 1)
    out = {"field": np.arange(n_fields + 1),
           "valid_frac": n_ok / np.maximum(n_all, 1)}
    for name, arr in bands.items():
        v = arr[inside][ok].astype("float64")
        l = lab[ok]
        good = np.isfinite(v)
        v, l = v[good], l[good]
        cnt = np.bincount(l, minlength=n_fields + 1)
        out[f"{name}_mean"] = np.bincount(l, weights=v, minlength=n_fields + 1) / np.maximum(cnt, 1)
        out[f"{name}_median"] = (pd.Series(v).groupby(l).median()
                                 .reindex(range(n_fields + 1)).to_numpy())
    return pd.DataFrame(out).iloc[1:]  # حذف label=0
```

```python
# scripts/run_zonal.py  (CLI نازک؛ منطق در ماژول‌ها)
def run(scene_ids, cfg):
    limit_threads(cfg.workers); lower_priority()
    mf = Manifest(cfg.paths.manifest)
    todo = mf.pending(scene_ids)
    for sid in tqdm(todo, desc="zonal", smoothing=0.05):   # ETA از tqdm
        wait_for_headroom(cfg.min_free_gb)
        t0 = time.time()
        try:
            df = process_scene(sid, cfg)                    # read → mask → zonal_scene
            tmp = cfg.paths.zonal / f"{sid}.parquet.tmp"
            df.to_parquet(tmp)
            tmp.replace(cfg.paths.zonal / f"{sid}.parquet")  # نوشتن اتمیک
            mf.mark(sid, "done", time.time() - t0)
        except Exception as e:                               # crash یک صحنه کل اجرا را نمی‌کُشد
            mf.mark(sid, "failed", time.time() - t0, repr(e))
```

```python
# تجمیع نهایی در fields.zarr (v3)
ds = xr.Dataset(
    {"median": (("field", "time", "band"), med),
     "valid_frac": (("field", "time"), vf)},
    coords={"field": field_ids, "time": times, "band": band_names,
            "sensor": ("time", sensors)},
)
ds.to_zarr("data/processed/fields.zarr", mode="w", zarr_format=3)
```

**ایندکس‌های spectral** (NDVI و غیره) از band‌های خام در مرحلهٔ بعد ساخته می‌شوند، نه در ingest؛ تا ablation ورودی‌ها بدون ingest مجدد ممکن باشد.

### 3.4 آزمایش terrio (timebox، فقط برای فاز 3)

terrio (pure-Rust، بدون وابستگی به GDAL) هنوز pre-1.0 است (نسخهٔ 0.4.x) و می‌تواند Zarr v3 با convention مکانی بنویسد؛ همچنین API آن شبیه rioxarray است. (تأییدشده؛ منبع: PyPI) پیشنهاد: 10 صحنه را هم با terrio و هم با rasterio+xarray به Zarr تبدیل کنید و مقایسه کنید: برابری مقادیر (`np.allclose`)، زمان، اوج حافظه، و قابل‌خواندن بودن خروجی با xarray. قاعدهٔ تصمیم (پیشنهادی): terrio فقط وقتی انتخاب شود که خروجی یکسان باشد، 10 از 10 صحنه بدون خطا تبدیل شوند و مزیت واضحی در زمان یا حافظه داشته باشد؛ در غیر این صورت rasterio+xarray باقی می‌ماند. چون این تبدیل فقط برای `cube.zarr` لازم است، اولویت آن پایین‌تر از بقیهٔ Sprint 0 است.

## 4. هستهٔ روش: Phenology-Aware Anomaly

### 4.1 چرا DOY کافی نیست (شواهد)

در مطالعات نیشکر، مراحل رشد در کاشت اول و ratoon فرق دارد و روش‌های مبتنی بر شکل منحنی معمولاً به تاریخ کاشت و برداشت نیاز دارند تا فصل‌ها از سری بلند جدا شوند. کار Joshi و همکاران (2024) نشان می‌دهد با یک مدل ذوزنقه‌ای می‌شود مراحل رشد را از سری NDVI لندست/سنتینل-2 بدون دانستن این تاریخ‌ها استخراج کرد. (تأییدشده؛ منبع: Remote Sensing 16(22), 4244). نتیجه برای این پروژه: برداشت‌ها را خودمان از سری زمانی پیدا می‌کنیم و چرخه را از آن‌ها می‌سازیم.

### 4.2 مراحل pipeline

1. **QC و سری هر مزرعه.** برای هر (field, time): median پیکسل‌های معتبر؛ مشاهده‌ای با `valid_frac` کمتر از آستانه (پیشنهاد اولیه 0.5، بعد از audit تنظیم شود) حذف یا با وزن کم وارد می‌شود. outlierهای نقطه‌ای (افت یک‌مشاهده‌ای که برنمی‌گردد) با Hampel حذف شوند تا با برداشت اشتباه گرفته نشوند.
2. **هموارسازی.** برای نمونه‌برداری نامنظم، Whittaker-Eilers با وزن مشاهده روی شبکهٔ روزانه (به‌جای Savitzky-Golay که شبکهٔ منظم می‌خواهد). پارامتر `lam` با cross-validation (حذف تصادفی مشاهدات) روی نمونه‌ای از مزارع تنظیم شود. SG روی شبکهٔ 8 روزهٔ درون‌یابی‌شده به‌عنوان مقایسه در Sprint 0 اجرا شود. (قضاوت)
3. **segmentation چرخه.** برداشت = کف NDVI با prominence کافی که قبلش پلاتوی بالا و بعدش صعود دارد. چرخه = فاصلهٔ دو برداشت متوالی؛ چرخهٔ اول و آخر `censored` برچسب می‌خورند و در baseline وارد نمی‌شوند (ولی می‌توانند امتیاز بگیرند). کاشت مجدد (replant) از وقفهٔ طولانی با NDVI پایین یا از متادیتا تشخیص داده شود و شمارندهٔ ratoon صفر شود.
4. **محور مرحله و شبکهٔ فاز.** محور اصلی `dsh` (روز از برداشت). شبکهٔ ریز با bin حدود 15 روز (حدود 28 bin برای یک چرخهٔ حدود یک‌ساله؛ طول واقعی را از داده بگیرید) برای baseline، و سه مرحلهٔ درشت برای تفسیر: استقرار/پنجه‌زنی، رشد اصلی تا شروع پلاتو، رسیدن تا برداشت (از برازش ذوزنقه‌ای). تعداد 10 فاز سند اولیه جای خود را به همین ترکیب می‌دهد، چون اندازهٔ bin باید با تراکم مشاهدات (حدود هر 9 تا 16 روز) سازگار باشد.
5. **strata و baseline.** هر چرخه به یک stratum تعلق دارد: (نوع چرخه: plant/ratoon-n) × (گروه رقم، اگر موجود است). baseline هر (stratum, bin, band) = median و MAD روی چرخه‌های نرمال همهٔ مزارع آن stratum، با leave-one-out برای چرخه‌ای که امتیاز می‌گیرد. اثر مزرعه با offset انقباضی وارد می‌شود: `δ_f = n_f/(n_f+κ) · median(x − m)` با κ حدود 2 تا 3 (تنظیمی). اگر یک bin کمتر از `min_n` چرخه داشت، به stratum درشت‌تر برگردید: (رقم, ratoon) ← (ratoon) ← همه.
6. **انتخاب چرخهٔ نرمال (trimming).** سه دور تکرار: baseline از چرخه‌های فعال، امتیاز همهٔ چرخه‌ها، حذف q درصد بالای «بار آنومالی» هر stratum (q حدود 10 تا 20 درصد؛ حساسیت‌سنجی شود). اگر داده‌ای از عملکرد یا ETa هست، به‌عنوان فیلتر مستقل اضافه شود. CWSI برای انتخاب نرمال استفاده نشود (بخش 1، مورد 2).
7. **امتیاز.** `z = (x − m)/max(1.4826·MAD, floor)` برای هر band؛ تجمیع در هر bin با `S = sqrt(mean_k z_k²)` و حفظ علامت هر band برای تفسیر (مثلاً NDVI منفی و LST مثبت = الگوی تنش). `floor` را از صدک پایین MADهای کل داده بگیرید تا تقسیم بر مقدار نزدیک صفر ممکن نشود. آستانهٔ رایج modified z-score برابر 3.5 است (نقطهٔ شروع).
8. **آنومالی پیوسته (run).** پرچم وقتی `S > 3.5` برای حداقل 2 مشاهدهٔ متوالی (فقط bin‌های مشاهده‌شده شمرده می‌شوند). برای تغییرات کند، CUSUM/EWMA روی z به‌عنوان آشکارساز دوم.
9. **داده‌ی گمشده.** بین bin‌ها درون‌یابی نکنید مگر ±1 bin؛ bin بدون مشاهده NaN می‌ماند و امتیاز ندارد. فاصلهٔ طولانی بدون مشاهده خودش یک feature کیفیت است (`max_gap_days` هر چرخه) و در گزارش می‌آید.

### 4.3 skeleton کد

```python
# src/ssl_anomaly/phenology/smoothing.py
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

def whittaker(y, w, lam, d=2):
    """Whittaker-Eilers؛ w=0 یعنی مشاهده‌ای وجود ندارد."""
    n = len(y)
    D = sparse.eye(n, format="csr")
    for _ in range(d):
        D = D[1:] - D[:-1]
    A = (sparse.diags(w) + lam * (D.T @ D)).tocsc()
    return spsolve(A, w * np.nan_to_num(y))

def to_daily(t_days, y, quality, lam):
    t0 = int(t_days.min())
    grid = np.arange(t0, int(t_days.max()) + 1)
    yy, ww = np.zeros(len(grid)), np.zeros(len(grid))
    idx = (t_days - t0).astype(int)
    yy[idx], ww[idx] = y, quality       # quality = valid_frac × وزن‌کاهندهٔ نزدیکی به ابر
    return grid, whittaker(yy, ww, lam)
```

```python
# src/ssl_anomaly/phenology/cycles.py
from dataclasses import dataclass
import numpy as np
from scipy.signal import find_peaks

@dataclass(frozen=True)
class Cycle:
    field: int
    cycle_id: int
    t_start: int          # روز (شمارهٔ روز از epoch ثابت)
    t_end: int
    censored: bool        # چرخهٔ اول/آخر سری
    kind: str             # "plant" | "ratoon"
    ratoon_no: int

def detect_harvests(grid, ys, min_prominence, min_gap_days):
    idx, _ = find_peaks(-ys, prominence=min_prominence, distance=min_gap_days)
    return idx            # کاندیدها؛ بعد با قاعدهٔ «پلاتوی بالا قبل، صعود بعد» پالایش شوند

def segment_cycles(field, grid, ys, cfg) -> list[Cycle]:
    ...                    # کاندیدها → پالایش → بازه‌ها → برچسب plant/ratoon
```

```python
# src/ssl_anomaly/baseline/robust.py
import numpy as np
MAD_K = 1.4826

def robust_stats(X, min_n=5):
    """X: (cycles, bins, bands)، NaN = بدون مشاهده → (median, scale): (bins, bands)"""
    n = np.sum(~np.isnan(X), axis=0)
    med = np.nanmedian(X, axis=0)
    scale = np.nanmedian(np.abs(X - med), axis=0) * MAD_K
    bad = n < min_n
    med[bad] = np.nan; scale[bad] = np.nan
    return med, scale

def score_loo(X, active, floor):
    """z هر چرخه نسبت به baseline چرخه‌های فعال، بدون خودش."""
    Z = np.full_like(X, np.nan)
    for i in range(X.shape[0]):
        keep = active.copy(); keep[i] = False
        med, scale = robust_stats(X[keep])
        Z[i] = (X[i] - med) / np.maximum(scale, floor)
    return Z

def trimmed_active(X, groups, floor, q=0.15, iters=3, thr=3.5):
    active = np.ones(X.shape[0], bool)
    for _ in range(iters):
        burden = np.zeros(X.shape[0])
        for g in np.unique(groups):
            idx = np.where(groups == g)[0]
            Z = score_loo(X[idx], active[idx], floor)
            burden[idx] = np.nanmean(np.abs(Z) > thr, axis=(1, 2))
        for g in np.unique(groups):
            idx = np.where(groups == g)[0]
            active[idx] = burden[idx] <= np.nanquantile(burden[idx], 1 - q)
    return active

def flag_runs(s, thr=3.5, min_run=2):
    """s: (bins,) امتیاز تجمیعی؛ NaN شمرده نمی‌شود."""
    obs = np.where(~np.isnan(s))[0]
    hit = np.abs(s[obs]) > thr
    flags, start = np.zeros(len(obs), bool), None
    for j, h in enumerate(np.append(hit, False)):
        if h and start is None:
            start = j
        elif not h and start is not None:
            if j - start >= min_run:
                flags[start:j] = True
            start = None
    out = np.zeros(len(s), bool); out[obs] = flags
    return out
```

### 4.4 آزمایش‌های کلیدی برای سؤال‌های باز

- **E-ALIGN (محور هم‌راستاسازی).** چهار حالت را با هم مقایسه کنید: A) DOY±15، B) `dsh`، C) GDD از برداشت (با Tbase تنظیمی)، D) landmark registration (انتقال خطی تکه‌ای برای هم‌ترازکردن «برداشت، شروع پلاتو، اوج، برداشت بعدی»). معیار: (1) پراکندگی درون‌bin چرخه‌های نرمال (MAD کمتر بهتر)، (2) خطای پیش‌بینی median به‌جای چرخهٔ کنارگذاشته (CV)، (3) پایداری در برابر حذف تصادفی 20 تا 50 درصد مشاهدات. انتخاب محور باید بر پایهٔ همین سه معیار و نه شهود باشد.
- **E-SEG (حساسیت به segmentation).** تاریخ برداشت را ±16 و ±32 روز جابه‌جا کنید و تغییر امتیازها را بسنجید. اگر امتیازها بی‌ثبات‌اند، مشکل از segmentation است نه مدل.
- **E-INTRA (یکنواختی درون‌مزرعه).** روی 32 مزرعهٔ Farms\_subset همین الگوریتم برداشت را در سطح پیکسل/زیرمزرعه اجرا کنید و پراکندگی تاریخ برداشت درون هر مزرعه را گزارش کنید. اگر برای بخش قابل‌توجهی از مزارع از حدود دو فاصلهٔ مشاهده (حدود 30 روز) بیشتر باشد، field-mean به‌تنهایی کافی نیست و باید فاز 3 با zoning درون‌مزرعه جلو بیفتد (آستانه پیشنهادی است).
- **E-NORM (حساسیت به q).** q را روی 0، 10، 20 و 30 درصد اجرا کنید و پایداری رتبه‌بندی آنومالی‌ها را (همبستگی Spearman بین اجراها) گزارش کنید.

### 4.5 تعمیم به محصولات دیگر

در این پروژه ادعای تعمیم نمی‌شود. فقط interface طوری طراحی می‌شود که `CycleSegmenter` و `phase_axis` قابل جایگزینی باشند. پیاده‌سازی نیشکر تنها پیاده‌سازی موجود است و چرخه‌بندی بر پایهٔ برداشت فقط برای محصولاتی با برداشت واضح معنا دارد.

## 5. مدل SSL

SSL فقط وقتی وارد می‌شود که B1 (baseline آماری phase-aware) ساخته و ارزیابی شده باشد؛ هدف مدل این است که چیزی بگیرد که z-score نمی‌گیرد: وابستگی بین band‌ها، وابستگی زمانی بین مشاهدات و اثر هواشناسی.

### 5.1 نمایش ورودی

هر چرخه یک دنبالهٔ token است (یک token به‌ازای هر مشاهدهٔ واقعی، بدون impute): ویژگی‌ها = band‌ها (استانداردسازی robust)، `valid_frac`، `Δt` از مشاهدهٔ قبلی؛ conditioning = `dsh` و GDD (نرمال‌شده)، sin/cos(DOY) (برای اثر تقویمی باقی‌مانده)، `ratoon_no`، رقم (در صورت وجود)، پرچم سنجنده (L8/L9)، و هواشناسی تجمیعی بین دو مشاهده (مجموع بارش، میانگین دما و ...). ورودی ابتدا `bands + LST` است و شاخص‌ها در ablation.

### 5.2 وظیفهٔ pretext

مدل‌سازی مشاهدات پوشانده‌شده (masked observation modeling): 15 تا 30 درصد token‌ها تصادفی، به‌علاوهٔ بلوک‌های متوالی 1 تا 3 مشاهده‌ای که شکاف ابر را تقلید می‌کنند. loss: Huber روی token‌های پوشانده‌شده، و برای مقاومت در برابر آلودگی داده (آنومالی در دادهٔ آموزش) در هر batch حدود 10 درصد بیشترین loss کنار گذاشته می‌شود (trimmed loss). آموزش فقط روی چرخه‌های `active` از trimming.

### 5.3 معماری‌ها (به ترتیب اجرا)

| کد | مدل | سخت‌افزار | نقش |
| --- | --- | --- | --- |
| M-A | GRU autoencoder کوچک | CPU | اولین baseline یادگیری عمیق |
| M-B | Transformer encoder 1D (3 تا 4 لایه، d=64، کمتر از 1M پارامتر) با masked modeling | CPU/GPU کوچک | مدل اصلی فاز 2 |
| M-C | CNN-Mamba کوچک | معمولاً GPU/Colab | مقایسه (اجرای selective-scan معمولاً به kernel‌های CUDA وابسته است؛ در Sprint 0 تأیید شود) |
| M-D | 3D-CAE | GPU | فقط فاز 3 روی patch |

### 5.4 امتیاز آنومالی

1. **باقی‌مانده بازسازی:** token‌ها با K گذر masking طوری پوشانده می‌شوند که هر token حداقل یک‌بار پیش‌بینی شود؛ باقی‌مانده با مقیاس robust هر فاز (از چرخه‌های نرمال) به z تبدیل می‌شود تا با بخش 4 هم‌واحد باشد.
2. **فاصلهٔ embedding:** فاصلهٔ kNN (cosine) چرخه تا چرخه‌های نرمال همان stratum؛ کاربرد دوم آن retrieval «چرخه‌های مشابه» برای تفسیر است.
3. **ترکیب:** فقط اگر هر کدام جداگانه از B1 بهتر باشد، با rank-average ترکیب شوند. بدون برچسب واقعی، وزن‌های یادگرفته‌شده نباید روی دادهٔ مصنوعی fit شوند (خطر overfit به نوع آنومالی تزریقی).

### 5.5 پروتکل آموزش و جلوگیری از leakage

- Farms\_subset (32 مزرعهٔ R11) از آموزش، baseline، انتخاب مدل و tuning کنار می‌ماند (بخش 1، مورد 4).
- CV: K=5 تایی بلوکی بر اساس منطقه روی بقیهٔ مزارع. در هر fold، baseline و آمارهٔ نرمال‌سازی فقط از مزارع train همان fold ساخته می‌شود.
- early stopping روی loss بازسازی در validation (نه روی معیار آنومالی). 5 seed برای هر پیکربندی و گزارش میانگین به‌همراه بازهٔ اطمینان.
- ablation اثر هواشناسی: `weather=on/off` تفاوت بین «غیرعادی نسبت به چرخه‌های نرمال» و «غیرعادی با وجود هواشناسی همان دوره» را نشان می‌دهد.

## 6. ارزیابی و benchmark

بدون برچسب واقعی، هیچ‌کدام از شواهد زیر به‌تنهایی «دقت» را اثبات نمی‌کنند؛ مجموعه‌شان «سازگاری چندمنبعی» را نشان می‌دهد و باید همین‌طور گزارش شود.

### 6.1 چهار نوع شواهد

| نوع | روش | چه چیزی را نشان می‌دهد | محدودیت |
| --- | --- | --- | --- |
| V1 تزریق مصنوعی | روی چرخه‌های نرمال کنار گذاشته: افت NDVI با عمق (5، 10، 20، 30 درصد) و طول (1، 2، 3، 5 مشاهده) در فازهای اولیه/میانی/پایانی؛ تأخیر فنولوژی ±15 تا 45 روز؛ افزایش LST | حساسیت (recall در نرخ هشدار ثابت) و تأخیر تشخیص | فقط انواعی که تزریق شده‌اند |
| V2 proxyهای ضعیف | ETa/ETref پایین، CWSI بالا (با و بدون LST)، yield هر چرخه در صورت وجود | همبستگی Spearman بار آنومالی با نقصان عملکرد و AUC-PR روی برچسب‌های proxy | proxy نویزی است؛ CWSI تا حدی به LST وابسته است |
| V3 رویدادها و خبره | فهرست رویدادهای شناخته‌شده (سیل، یخ‌زدگی، شوری، قطع آبیاری) و بازبینی کور خبره روی top-K | precision@K | نیاز به وقت خبره |
| V4 پایداری | حذف تصادفی مشاهدات، جابه‌جایی تاریخ برداشت، تغییر q، تغییر seed | استحکام روش | پایداری ≠ درستی |

### 6.2 نردبان baseline

| کد | روش | هدف |
| --- | --- | --- |
| B0 | z-score تقویمی (DOY، median/MAD) | کف مقایسه |
| B1 | z-score phase-aware با محور `dsh` | **هستهٔ پروژه** |
| B2 | B1 با محور GDD یا landmark | انتخاب محور |
| B3 | Isolation Forest/ECOD روی ویژگی‌های هر چرخه | baseline غیرپارامتری |
| B4 | GRU-AE | یادگیری عمیق ساده |
| B5 | Transformer با masked modeling | مدل اصلی SSL |
| B6 | CNN-Mamba | مقایسه |

قاعده: اگر B5/B6 از B1 بهتر نباشند، این خودش یافتهٔ مهمی است و گزارش می‌شود (G2).

### 6.3 معیارها و آمار

- **معیار اصلی:** AUC-PR (عدم توازن زیاد)، به‌علاوهٔ recall در نرخ هشدار ثابت (مثلاً 5 درصد چرخه‌ها)، تأخیر تشخیص (تعداد مشاهده از آغاز تزریق تا اولین هشدار) و Spearman با proxyها. AUC-ROC و F1 فرعی. Kappa اولویت ندارد.
- **واحد نمونه‌برداری:** مزرعه (چرخه‌های یک مزرعه وابسته‌اند). cluster bootstrap روی مزرعه یا بلوک منطقه‌ای برای بازهٔ اطمینان 95 درصد.
- **مقایسهٔ جفتی:** روی foldهای یکسان؛ Wilcoxon signed-rank روی تفاوت معیار هر مزرعه، با گزارش اندازهٔ اثر و CI. چون چند مقایسه هم‌زمان انجام می‌شود، تصحیح Holm. آزمون t جفتی استفاده نشود (فرض نرمال بودن برقرار نیست).
- **cross-validation:** اصلی = بلوکی بر اساس منطقه؛ leave-one-year-out فقط برای سنجش پایداری زمانی (چون چرخه‌ها به یک سال تقویمی محدود نیستند، «سال» را با «چرخهٔ شروع‌شده در آن سال» تعریف کنید)؛ split تقویمی (آخرین چرخهٔ کامل 2025–2026 به‌عنوان test زمانی) برای کنترل drift.
- **فریم‌ورک:** چارچوب سفارشی روی MLflow با رجیستری ساده از مدل‌ها و معیارها. chronobench و ابزارهای مشابه اختیاری‌اند و فقط اگر نصب و بررسی‌شان کمتر از اجرای چارچوب سفارشی وقت بگیرد (تأییدنشده در این سند).

## 7. مهندسی نرم‌افزار و بازتولیدپذیری

### 7.1 ساختار repo

```
ssl_anomaly/
  pyproject.toml, uv.lock, dvc.yaml
  conf/                    # Hydra
    base.yaml
    profile/ laptop.yaml colab.yaml
    data/ model/ input/ experiment/
  src/ssl_anomaly/
    io/            # landsat.py, zonal.py, zarr_store.py, era5.py
    phenology/     # smoothing.py, cycles.py, align.py, backends.py
    baseline/      # robust.py, trimming.py, score.py
    models/        # gru_ae.py, masked_tf.py, cnn_mamba.py
    train/         # lit_module.py, data.py
    eval/          # synthetic.py, proxies.py, stats.py
    xai/
    utils/         # throttle.py, manifest.py
  tests/           # unit/, regression/ (golden), parity/
  scripts/         # CLI نازک؛ بدون منطق
  notebooks/       # فقط EDA
  rust/            # بعد از gate G3
```

### 7.2 تصمیم‌ها

| موضوع | تصمیم | دلیل |
| --- | --- | --- |
| config | Hydra + structured configs (dataclass)؛ `profile=laptop\|colab` | ترکیب‌پذیری و جابه‌جایی بین لپ‌تاپ و Colab |
| tracking | MLflow محلی (backend SQLite)؛ W&B فعلاً نه | یک ابزار کافی است؛ همه‌چیز محلی می‌ماند |
| نسخه‌بندی داده | DVC برای داده و stageها | بازتولیدپذیری در سطح stage |
| orchestration | `dvc.yaml`؛ Prefect/Airflow لازم نیست | یک نفر، یک ماشین |
| HP tuning | Hydra multirun در فاز 1؛ Optuna بعد از G2 با nested runs در MLflow | فضای جست‌وجو اول کوچک است |
| تست | pytest + pytest-cov؛ golden regression؛ تست parity | هر refactor با regression محافظت شود |
| logging | `logging` استاندارد + `rich` | وابستگی کمتر |
| type/lint | pyright + ruff | سرعت |
| env | uv با lockfile | نسخه‌های pin‌شده |

### 7.3 ریتم تست

- **unit:** هر تابع در `phenology/` و `baseline/` با سری مصنوعی با پاسخ مشخص (مثلاً سری ذوزنقه‌ای با برداشت‌های معلوم؛ خطای قابل‌قبول حداکثر یک فاصلهٔ مشاهده).
- **golden regression:** 3 مزرعهٔ انتخابی؛ خروجی (تاریخ برداشت، median هر bin، z-score) در `.npz` کوچک ذخیره می‌شود و هر تغییر کد باید آن را حفظ کند یا تغییر را آگاهانه تأیید کنید.
- **parity:** وقتی Rust اضافه شد، همان ورودی‌ها روی هر دو backend (بخش 8).
- پیاده‌سازی مرحله‌به‌مرحله: هر بخش از بخش 4 ابتدا با تست نوشته و روی داده تأیید شود، بعد بخش بعدی.

### 7.4 DVC pipeline

```yaml
stages:
  field_mask:
    cmd: python scripts/build_field_mask.py
    deps: [data/geo/fields.gpkg]
    outs: [data/interim/field_mask.tif]
  zonal:
    cmd: python scripts/run_zonal.py
    deps: [data/raw/landsat, data/interim/field_mask.tif, src/ssl_anomaly/io/zonal.py]
    outs: [data/interim/zonal]
  fields_zarr:
    cmd: python scripts/build_fields_zarr.py
    deps: [data/interim/zonal]
    outs: [data/processed/fields.zarr]
  cycles:
    cmd: python scripts/segment_cycles.py
    deps: [data/processed/fields.zarr, conf/phenology]
    outs: [data/processed/cycles.parquet]
  baseline:
    cmd: python scripts/build_baseline.py
    deps: [data/processed/cycles.parquet, data/processed/fields.zarr]
    outs: [data/processed/baseline.npz, data/processed/scores.parquet]
  evaluate:
    cmd: python scripts/evaluate.py
    deps: [data/processed/scores.parquet]
    metrics: [reports/metrics.json]
```

stage-level resume را DVC می‌دهد و item-level resume را `Manifest` (بخش 3.3).

### 7.5 checkpoint، export و بازتولیدپذیری

برای resume آموزش از `.ckpt` خود Lightning استفاده کنید (optimizer و scheduler را هم نگه می‌دارد). SafeTensors برای نسخهٔ نهایی مدل است (بدون pickle و سریع‌بارگذاری). وزن‌ها را همراه با config و آمارهٔ نرمال‌سازی ذخیره کنید؛ بدون `norm_stats.json` مدل قابل استفاده نیست.

```python
from safetensors.torch import save_file, load_file
import json

def export_release(model, cfg: dict, norm_stats: dict, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    save_file({k: v.detach().cpu().contiguous() for k, v in model.state_dict().items()},
              out_dir / "model.safetensors")
    (out_dir / "model_config.json").write_text(json.dumps(cfg, indent=2))
    (out_dir / "norm_stats.json").write_text(json.dumps(norm_stats, indent=2))  # ترتیب band + آمار

def load_release(build_model, out_dir):
    cfg = json.loads((out_dir / "model_config.json").read_text())
    model = build_model(cfg)
    model.load_state_dict(load_file(out_dir / "model.safetensors"))
    return model.eval()
```

```python
# شروع هر آزمایش
import lightning as L, torch
L.seed_everything(cfg.seed, workers=True)
torch.use_deterministic_algorithms(True, warn_only=True)
# در MLflow ثبت شود: git SHA، hash نسخهٔ داده (DVC)، uv.lock، splits.json، seed
```

- **ONNX:** فعلاً نه. فقط وقتی نیاز واقعی به inference روی edge ایجاد شد و فقط برای مدل‌های GRU/Transformer؛ export مدل‌های Mamba معمولاً مشکل‌ساز است (قضاوت؛ در همان زمان بررسی شود). quantization (FP16/INT8) فقط بعد از پذیرش مدل FP32 و با معیار «افت مجاز در V1 و V2».
- **versioning مدل:** MLflow model registry محلی؛ `splits.json` و نسخهٔ داده کنار مدل ثبت شوند.

### 7.6 profile لپ‌تاپ

```yaml
# conf/profile/laptop.yaml
workers: 2
blas_threads: 2
min_free_gb: 2.0
low_priority: true
device: cpu
batch_size: 64
```

هر CLI در ابتدا `limit_threads(cfg.blas_threads)` را قبل از import کتابخانه‌های عددی صدا می‌زند، اولویت پردازش را پایین می‌آورد، و progress و ETA را با `rich`/`tqdm` نشان می‌دهد.

## 8. شتاب‌دهی با Rust (gated؛ نه در فاز 1)

### 8.1 اصل

اول پیاده‌سازی مرجع Python/NumPy با تست؛ Rust فقط جایگزین تابعی می‌شود که profiling نشان داده گلوگاه است و خروجی‌اش با مرجع یکی است. در فاز 1 Rust لازم نیست: ساخت `field_mask` یک‌بار و `bincount` در هر صحنه، و داده‌ای در حد چند ده مگابایت، گلوگاه نمی‌سازد (با اندازه‌گیری تأیید شود).

### 8.2 gate G3 (پیشنهادی)

وارد Rust شوید فقط اگر یکی از این‌ها برقرار باشد: (الف) profiling (cProfile/py-spy/scalene) نشان دهد یک stage بیش از حدود 30 درصد زمان کل را می‌گیرد و اجرای کامل بیش از حدود 30 دقیقه است؛ (ب) پردازش سطح پیکسل در فاز 3 با NumPy عملی نیست (زمان یا حافظه). آستانه‌ها را بعد از اولین profile واقعی دوباره تنظیم کنید.

### 8.3 ترتیب هدف‌ها

| اولویت | هدف | توضیح |
| --- | --- | --- |
| 1 | راه‌حل بدون Rust | `field_mask` + `bincount`؛ بسیاری از موارد را حل می‌کند |
| 2 | کتابخانه‌های آماده | `oxidized-rasterstats` (zonal) و `eo-processor` (شاخص‌ها و آمار زمانی): ادعای سرعت 7 تا 17 برابر و «آماده بودن» از سند اولیه است و در این بررسی تأیید نشده؛ در gate با benchmark و تست parity روی یک صحنهٔ واقعی بسنجید |
| 3 | terrio برای I/O | تأییدشده: pure-Rust، pre-1.0؛ برای تبدیل cube (بخش 3.4) |
| 4 | PyO3 + maturin سفارشی | Whittaker دسته‌ای، `detect_harvests`/segmentation، baseline robust (median/MAD) روی 10^6 تا 10^7 سری پیکسلی، و binning فاز؛ موازی‌سازی با rayon و تعداد thread برابر `cfg.workers` |

### 8.4 طراحی interface از همین حالا

```python
# src/ssl_anomaly/phenology/backends.py
from typing import Protocol
import numpy as np

class PhenologyBackend(Protocol):
    def whittaker_batch(self, y: np.ndarray, w: np.ndarray, lam: float) -> np.ndarray: ...
    def robust_baseline(self, X: np.ndarray, min_n: int) -> tuple[np.ndarray, np.ndarray]: ...

def get_backend(name: str) -> PhenologyBackend:
    if name == "numpy":
        from .backend_numpy import NumpyBackend; return NumpyBackend()
    if name == "rust":                      # فقط بعد از G3
        from ssl_anomaly_rs import RustBackend; return RustBackend()
    raise ValueError(name)
```

```python
# tests/parity/test_backends.py
@pytest.mark.parametrize("seed", range(20))
def test_rust_matches_numpy(seed):
    X = random_cycles(seed)                 # شامل NaN و bin‌های کم‌نمونه
    m0, s0 = get_backend("numpy").robust_baseline(X, 5)
    m1, s1 = get_backend("rust").robust_baseline(X, 5)
    np.testing.assert_allclose(m0, m1, rtol=1e-6, equal_nan=True)
    np.testing.assert_allclose(s0, s1, rtol=1e-6, equal_nan=True)
```

قرارداد: `backend: numpy|rust` در config، تست parity اجباری قبل از ادغام، و ثبت speedup واقعی در MLflow. کد Rust قبل از G3 نوشته نمی‌شود.

## 9. تفسیرپذیری (XAI)

- **فاز 1 (بدون DL):** baseline آماری ذاتاً قابل‌تفسیر است: سهم هر band و هر bin در امتیاز، و خلاصهٔ آن در سه مرحلهٔ درشت رشد.
- **فاز 2 تا 3 (مدل‌های DL):** اول Captum (Integrated Gradients) و occlusion پنجره‌ای زمانی؛ نتیجه به bin‌ها و مراحل درشت تجمیع شود. ابزارهای تخصصی سری زمانی (tint، tsCaptum) و meteors اختیاری‌اند و در این سند بررسی نشده‌اند.
- **faithfulness:** deletion/insertion AUC در سطح bin فاز؛ به‌علاوهٔ sanity check (تصادفی‌سازی وزن مدل باید attribution را از بین ببرد).
- **channel dropping:** با Hydra multirun روی `input.drop` (هر band، LST، هواشناسی) و 5 seed؛ تغییر معیار با CI گزارش شود (همان ablation بخش 6).

## 10. ریسک‌ها

| ریسک | اثر | کاهش |
| --- | --- | --- |
| تشخیص نادرست برداشت | baseline مخدوش | QC بصری روی 30 مزرعه، E-SEG، مقایسه با سوابق برداشت |
| تعداد کم چرخهٔ نرمال | baseline ناپایدار | pooling سلسله‌مراتبی، انقباض offset، `min_n` |
| آلودگی چرخه‌های نرمال | آنومالی‌ها «عادی» می‌شوند | trimming تکراری و trimmed loss |
| validation دایره‌ای (LST ↔ CWSI) | نتیجهٔ خوش‌بینانه | ablation بدون LST؛ تکیه بر ETa/yield |
| تغییر توزیع (L8 → L9، رقم، مدیریت، اقلیم) | drift | flag سنجنده، test زمانی، گزارش پایداری |
| ارزیابی بدون برچسب | ادعای بیش‌ازحد | ترکیب V1 تا V4 و گزارش صریح محدودیت |
| داغ شدن لپ‌تاپ | توقف کار | throttle، اولویت پایین، resume |
| ابزارهای نابالغ (terrio، GeoZarr) | شکست یا تغییر API | fallback به rasterio+xarray، pin کردن نسخه |
| scope creep | کار بی‌پایان | gateهای G0 تا G3 |

## 11. ادامهٔ کار

### 11.1 ورودی‌هایی که از شما لازم است

این‌ها کیفیت بخش 4 و 6 را مستقیماً تعیین می‌کنند و در صورت وجود باید قبل از Sprint 0 مشخص شوند:

1. هر نوع سابقهٔ تاریخ کاشت و برداشت (حتی جزئی یا برای زیرمجموعه‌ای از مزارع).
2. متادیتای رقم، سن مزرعه و ratoon.
3. عملکرد (yield) هر مزرعه در هر چرخه.
4. فهرست رویدادهای شناخته‌شده (سیل، یخ‌زدگی، شوری، قطع آبیاری) و یک خبرهٔ دردسترس برای بازبینی top-K.

### 11.2 Sprint 0

1. **audit داده:** تاریخ‌ها، `valid_frac` هر مزرعه، تعداد چرخه‌های ممکن، و تأیید اینکه CWSI از LST ساخته شده یا نه.
2. **ingest:** `field_mask` + zonal با resume + `fields.zarr`.
3. **segmentation:** اجرا و QC بصری روی 30 مزرعه؛ مقایسه با سوابق برداشت؛ خروجی = G0.
4. **B0 و B1:** baseline تقویمی و phase-aware + تزریق مصنوعی + E-ALIGN؛ خروجی = G1.
5. **اولویت پایین:** benchmark chunking و trial terrio برای فاز 3.

### 11.3 پاسخ شش سؤال باز سند اولیه

| سؤال | پاسخ |
| --- | --- |
| روش فنولوژی | Whittaker + قواعد برداشت (scipy)؛ TIMESAT فقط مقایسه؛ DL فعلاً نه |
| سال/چرخهٔ نرمال | data-driven با trimming تکراری و فیلتر ETa/yield؛ نظر خبره برای validation؛ بدون CWSI |
| chunking Zarr | فاز 1: یک chunk کافی است؛ cube فاز 3: benchmark سه پیکربندی (C1 تا C3) |
| قالب مدل | `.ckpt` برای resume، SafeTensors برای نسخهٔ نهایی؛ ONNX مؤخر |
| orchestrator | DVC pipeline + Manifest (item-level)؛ Prefect/Airflow نه |
| trial terrio | بله، timebox و فقط برای تبدیل cube در فاز 3؛ rasterio+xarray fallback |

### 11.4 منابع

- Joshi N., Simms D.M., Burgess P.J. (2024). Automating the derivation of sugarcane growth stages from Earth observation time series. Remote Sensing 16(22), 4244. https://dspace.lib.cranfield.ac.uk/handle/1826/23202
- EOPF Explorer: GeoZarr standards (وضعیت conventionها و درایور GDAL). https://explorer.eopf.copernicus.eu/datamodel/technical-deep-dive
- Pangeo showcase: GeoZarr sharding در GDAL (2026-03-04). https://discourse.pangeo.io/t/pangeo-showcase-no-shard-feelings-geozarr-rendering-in-qgis-powered-by-gdal-march-4-2026-at-12-pm-et/5526
- terrio (PyPI). https://pypi.org/project/terrio/
- Eilers P.H.C. (2003). A perfect smoother. Analytical Chemistry 75(14), 3631–3636.
