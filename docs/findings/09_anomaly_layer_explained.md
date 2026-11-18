# یافته ۹ — لایهٔ آنومالی: معنا، منشأ، فرمول‌ها، علم پشتش

## ۱. لایهٔ آنومالی چیست؟

**لایهٔ آنومالی** یک مقدار عددی (score) است که برای هر مزرعه در هر تاریخ محاسبه می‌شود و نشان می‌دهد **چقدر رفتار آن مزرعه در آن زمان از «الگوی نرمال» چرخه‌های قبلی آن stratum انحراف دارد.**

- **score = 0**: مزرعه دقیقاً مثل چرخه‌های نرمال رفتار می‌کند.
- **score بالا**: مزرعه در آن تاریخ غیرعادی است (احتمال تنش).
- **آستانه**: score > 3.5 برای حداقل ۲ bin متوالی → پرچم anomaly (run).

## ۲. منشأ: از کجا آمده؟

این روش از **z-score robust (modified z-score)** گرفته شده است:

1. **Baseline (B1)**: برای هر stratum (plant/ratoon-n × block) و هر bin فاز (۱۵ روزه)، **median** و **MAD** (Median Absolute Deviation) چرخه‌های نرمال محاسبه می‌شود.
2. **Trimming**: چرخه‌هایی که بیشترین «بار آنومالی» را دارند (top 15%) حذف می‌شوند تا baseline آلوده نشود.
3. **Scoring**: هر مشاهده با baseline مقایسه می‌شود.

این روش از مقالات **Eilers (2003)** (Whittaker smoother) و **Joshi et al. (2024)** (sugarcane phenology) الهام گرفته شده و با **robust statistics** (median/MAD به جای mean/std) پایدار شده است.

## ۳. فرمول‌ها

### ۳.۱ MAD (Median Absolute Deviation)
$$\text{MAD} = \text{median}(|x_i - \text{median}(x)|)$$

### ۳.۲ Scale (با ضریب ۱.۴۸۲۶)
$$\text{scale} = 1.4826 \times \text{MAD}$$

ضریب ۱.۴۸۲۶ MAD را به انحراف معیار معادل تبدیل می‌کند (برای توزیع نرمال).

### ۳.۳ z-score (modified)
$$z_k = \frac{x_k - m_k}{\max(\text{scale}_k, \text{floor})}$$

که $m_k$ = median baseline برای band $k$، و `floor` = صدک ۵ MADهای کل داده (برای جلوگیری از تقسیم بر صفر).

### ۳.۴ S (امتیاز تجمیعی per bin)
$$S = \sqrt{\frac{1}{K} \sum_{k=1}^{K} z_k^2}$$

$K$ = تعداد باندها. این RMS band aggregation است.

### ۳.۵ Flag (پرچم anomaly)
$$\text{flag} = (|S| > 3.5) \text{ for } \geq 2 \text{ consecutive observed bins}$$

آستانهٔ ۳.۵ از modified z-score (Iglewicz & Hoaglin, 1993) گرفته شده است.

### ۳.۶ Stratum fallback
اگر یک bin کمتر از `min_n=5` چرخه داشت:
$$(\text{variety}, \text{ratoon}) \leftarrow (\text{ratoon}) \leftarrow \text{all}$$

### ۳.۷ Field offset (shrinkage)
$$\delta_f = \frac{n_f}{n_f + \kappa} \times \text{median}(x - m), \quad \kappa \approx 2.5$$

اثر مزرعه با انقباض (shrinkage) وارد می‌شود.

### ۳.۸ Trimmed normal cycles (3 iterations)
$$\text{active} = \text{burden} \leq Q_{1-q}(\text{burden})$$

$q = 0.15$ (top 15% حذف می‌شوند).

## ۴. علم پشتش

| مفهوم | توضیح | منبع |
|---|---|---|
| Robust statistics | median/MAD به جای mean/std — مقاوم در برابر outliers | Huber (1981) |
| Modified z-score | آستانهٔ ۳.5 برای تشخیص outlier | Iglewicz & Hoaglin (1993) |
| Whittaker-Eilers | smoother برای دادهٔ نامنظم | Eilers (2003) |
| Phenology alignment | days-since-harvest به جای DOY | Joshi et al. (2024) |
| Trimmed loss | حذف ۱۰٪ بالاترین loss در هر batch | robust M-estimation |
| Leave-one-out | baseline بدون خود چرخه | cross-validation |

## ۴.۵ رابطه با SSL (مکمل یا جایگزین)

**لایهٔ آنومالی فعلی (B1)** یک **baseline آماری** است: z-score robust روی چرخه‌های نرمال.
**SSL (M-B)** یک **baseline یادگیری‌عمیق** است: خطای بازسازی (reconstruction error) مدل Transformer.

### تفاوت‌ها

| | B1 (آماری) | SSL (Transformer) |
|---|---|---|
| **ورودی** | باندهای خام (mean per field) | token sequence (bands + weather + dsh + ...) |
| **مدل** | median/MAD per (stratum, bin) | masked autoencoder |
| **امتیاز** | RMS z-score | reconstruction error (Huber) |
| **تفسیرپذیری** | بالا (هر band/bin) | متوسط (Captum/XAI لازم) |
| **پایداری** | بالا | نامشخص (gate G2) |
| **هزینه** | CPU، چند دقیقه | CPU/GPU، چند ساعت |

### چگونه ترکیب می‌شوند؟

1. **B1 اول**: baseline آماری به‌عنوان کف مقایسه.
2. **SSL دوم**: اگر SSL با CI معنادار از B1 بهتر باشد (gate G2)، امتیاز SSL به‌عنوان anomaly score اصلی استفاده می‌شود.
3. **ترکیب**: اگر هر دو جداگانه از B1 بهتر باشند، با **rank-average** ترکیب می‌شوند.
4. **بدون برچسب**: وزن‌های یادگرفته‌شده روی دادهٔ مصنوعی fit نمی‌شوند (خطر overfit).

### فرمول SSL anomaly score
$$\text{score}_{\text{SSL}} = \frac{1}{K} \sum_{k=1}^{K} \text{Huber}(x_k, \hat{x}_k)$$

که $\hat{x}_k$ = بازسازی مدل برای band $k$ (token پوشانده‌شده). سپس robust scaling (median/MAD) به z تبدیل می‌شود تا با B1 هم‌واحد باشد.

### وضعیت فعلی
- SSL روی ۳۲ مزرعه (۴۳ cycle) آموزش دیده است.
- Gate G2 (SSL beats B1 with CI) **هنوز تست نشده**.
- باید روی ۴۹۰ مزرعه اجرا و مقایسه شود.

## ۵. daily anomaly (نسخهٔ جدید)

برای هر مزرعه در هر تاریخ:
1. تعیین چرخهٔ متعلق (از cycles.parquet).
2. محاسبهٔ dsh (days-since-harvest).
3. تعیین bin (dsh // 15).
4. دریافت median/scale از baseline برای آن stratum/bin.
5. محاسبهٔ z برای هر باند.
6. $S = \sqrt{\text{mean}(z^2)}$.

این مقدار در `data/processed/daily_anomaly.parquet` ذخیره می‌شود و در نقشهٔ timeslider استفاده می‌شود.

## ۶. تفسیر

- **S < 5**: نرمال (سبز)
- **5 ≤ S < 10**: متوسط (زرد)
- **S ≥ 10**: آنومالی (قرمز)
- **run**: ≥ ۲ bin متوالی با S > 3.5 → پرچم anomaly

## ۷. محدودیت‌های این لایه

1. **بدون برچسب**: هیچ ground truth وجود ندارد. S فقط «انحراف از نرمال» است، نه «تنش».
2. **CWSI circularity**: اگر CWSI به‌عنوان proxy استفاده شود، نتیجهٔ خوش‌بینانه است.
3. **scale floor**: اگر MAD بسیار کوچک باشد، floor جلوگیری از explosion می‌کند اما ممکن است sensitivity را کاهش دهد.
4. **stratum fallback**: اگر cycle کم باشد، baseline درشت‌تر (all) استفاده می‌شود → کمتر دقیق.