# پیشنهادهای گسترش — پیکربندی مقیاس‌پذیر و قابلیت‌های اضافی

**پروژه:** کشف تنش/آنومالی گیاهی با SSL روی سری زمانی لندست  
**تاریخ:** 2026-10-24  
**مکمل:** `method_design_ssl.md`, `00_SSL_questionnaire.md`, `lit_review/08_executive_synthesis.md`

---

## ۰. اصل کلیدی: پیکربندی واحد، مقیاس متغیر

کد باید **یک فایل کانفیگ واحد** (مثلاً `config.yaml`) داشته باشد که بر اساس **توان محاسباتی سیستم** (پهپاد → لپ‌تاپ → سرور) تنظیم شود. با تغییر کانفیگ، **فقط دقت** تغییر کند، نه منطق کد. سه پروفایل پیشنهادی:

| پروفایل | سخت‌افزار | اندازه مدل | سطح فضایی | ورودی | دقت مورد انتظار |
|---------|-----------|------------|-----------|-------|------------------|
| `edge` (پهپاد/Edge) | CPU، <2GB RAM | <100K params، 1D-CNN کم‌عمق | field-level (1 بردار به ازای هر مزرعه) | شاخص‌های خلاصه (NDVI, CWSI) | پایه |
| `laptop` | CPU/GPU کوچک، 8–16GB | <1M params | field + patch (8×8) | raw bands + LST | متوسط |
| `server` | GPU ≥24GB | >5M params (CNN-Mamba کامل) | pixel/patch (32×32) | raw bands + LST + ETa + CWSI | بالا |

**پارامترهای کانفیگ‌پذیر (حداقل):**

```yaml
system:
  device: auto          # cpu | cuda | mps
  precision: fp32       # fp32 | fp16 | int8
  num_workers: 2
model:
  profile: laptop       # edge | laptop | server
  encoder_width: 64     # 16/64/256
  encoder_depth: 2      # 1/2/4
  patch_size: 8         # 1/8/32  (1 = pixel-level)
  temporal_window: 32   # timesteps per sample
spatial:
  level: field          # field | patch | pixel
  aggregation: zonal     # zonal | mean | none
input:
  raw_bands: true
  lst: true
  indices: [NDVI, NDRE]   # optional
  etadaily: false       # toggle
  cwsi: false           # toggle
anomaly:
  score: reconstruction_error   # reconstruction_error | latent_distance
  threshold: median_plus_mad    # median_plus_mad | percentile
  consecutive_dates: 2
baseline:
  normal_years: [2015, 2016, 2017]   # سال‌های نرمال برای مقایسه چند-ساله
```

**قانون طراحی:** هیچ `if profile == "server"` در کد آموزش. همهٔ تفاوت‌ها از کانفیگ خوانده می‌شوند. تغییر پروفایل ⇒ تغییر دقت، نه تغییر منطق.

---

## ۱. اولویت ۲ — سطح داخل‌مزرعه (Sub-field / Pixel-level)  ⭐

**هدف:** کشف آنومالی نه فقط به ازای هر مزرعه، بلکه برای بخش‌های داخل مزرعه (پیکسل/پچ).

- **داده:** Landsat 30m ⇒ یک مزرعه ۲۵ ha ≈ ۲۷۸ پیکسل. پس pixel/patch-level شدنی است.
- **معماری:** MAE با patch size قابل کانفیگ (1/8/32). در `edge` patch=1 (field vector)؛ در `server` patch=4/8 با نقشه بازسازی.
- **خروجی:** نقشه آنومالی مکانی per date + aggregation به field score (max/mean/percentile).
- **اعتبارسنجی:** تطابق با نقشه ECe (کریجینگ ۱۲۸ چاه) و CWSI spatial.
- **هزینه:** حجم داده ×۲۷۸؛ نیاز به patch-based data loader و chunked inference.
- **پیش‌نیاز:** تعریف mask پلیگون مزرعه (rasterize polygons → pixel membership).

## ۲. اولویت ۵ — مقایسه صریح سال‌ها و فصل رشد (Cross-year / Season alignment)  ⭐

**هدف:** مدل بتواند یک مزرعه را در «همان فصل رشد» اما «سال‌های مختلف» مقایسه کند (حتی بخش‌های داخل مزرعه).

- **تعریف baseline نرمال چند-ساله:** برای هر مزرعه و هر DOY (day-of-year) پنجرهٔ ۱۶-روزه، محاسبهٔ median و MAD روی سال‌های نرمال (مثلاً ۲۰۱۵–۲۰۱۷ یا سال‌های با عملکرد بالا).
- **آنومالی:** انحراف از baseline چند-ساله، نه فقط از średnia فصل. z-score per (field, DOY-window, year).
- **هم‌راستاسازی فصل رشد:** نرمال‌سازی بر اساس «روز پس از کاشت/برداشت» (crop calendar) به‌جای DOY تقویمی، برای مقایسهٔ سال‌های با شروع رشد متفاوت.
- **خروجی:** anomaly score per field per date + «سال‌های مشابه» retrieval (kNN در embedding space).
- **پیش‌نیاز:** crop calendar per field (کاشت/برداشت) — از DATA_SUMMARY/مزرعه‌بندی.

---

## ۳. سایر موارد (برای گسترش پروژه)

| # | مورد | اقدام پیشنهادی | فاز |
|---|------|----------------|-----|
| ۳ | چندمحصولی (multi-crop) | نرمال‌سازی per-crop/per-season؛ baseline جدا per crop؛ اعتبارسنجی روی ≥2 محصول | گسترش |
| ۴ | ETaDaily & CWSI به‌عنوان ورودی | toggle در کانفیگ؛ توجه: خودشان خروجی مدل فیزیکی‌اند ⇒ خطر circularity؛ فقط به‌عنوان کانال کمکی + ablation | گسترش |
| ۶ | فاز دانش (Knowledge integration) | RAG: vector store از مقالات/کتاب‌ها/Q&A؛ retrieval بر اساس anomaly type؛ grounding + citation | فاز بعدی (جدا) |
| ۷ | پیاده‌سازی کد | pipeline آموزش، data loader، baseline‌ها (RF/XGBoost, CWSI-threshold alarm, STS-NET, Presto) | فوری |
| ۸ | کیفیت داده | QC پس از CFMASK؛ شمارش تاریخ‌های معتبر؛ ECe/CWSI فقط ۲۰۲۳ ⇒ نیاز به برچسب بیشتر | فوری |
| ۹ | آلودگی «نرمال» (G4) | synthetic-anomaly degradation arm (AnomalyBERT-style) | روش |
| ۱۰ | لپ‌تاپ/سبک | هدف صریح params ≤1M، استنتاج CPU <1s per field | طراحی |
| ۱۱ | XAI | SHAP/Grad-CAM زمانی + اعتبارسنجی فیزیولوژیک (Angon) + faithfulness (deletion/insertion) | روش |
| ۱۲ | Adversarial/contamination | robust loss (trimmed) + one-class SVM روی SSL features | روش |

---

## ۴. ترتیب پیشنهادی اجرا (Roadmap)

1. **فوری:** کانفیگ مقیاس‌پذیر + data loader + QC داده.
2. **کوتاه‌مدت:** baseline چند-ساله (مورد ۵) + field-level anomaly score + اعتبارسنجی CWSI/ETa.
3. **میان‌مدت:** sub-field (مورد ۲) + multi-crop (مورد ۳) + ETa/CWSI input (مورد ۴).
4. **بلندمدت:** فاز دانش/RAG (مورد ۶).

---

## ۵. تصمیمات باز برای استاد/کاربر

- [ ] پروفایل پیش‌فرض `laptop` تأیید شود.
- [ ] سطح فضایی پیش‌فرض: field یا patch؟
- [ ] سال‌های نرمال برای baseline چند-ساله: کدام سال‌ها؟
- [ ] ETa/CWSI به‌عنوان ورودی یا فقط validation؟
- [ ] Crop calendar per field موجود است؟
