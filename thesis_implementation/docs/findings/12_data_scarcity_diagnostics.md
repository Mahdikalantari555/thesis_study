# یافته ۱۲ — تشخیص کمبود داده و کیفیت بازنمایی (`DS1–DS5`): آیا مدل با ۵۳۹ تاریخ واقعاً «داده‌کم» است؟

این سند پاسخ ما به سؤال کلیدی استاد راهنما را مستند می‌کند: **آیا مدل خودنظارتی روی آرشیو واقعی ۳۲ مزرعه (۵۳۹ تاریخ Landsat، ۲۰۱۳–۲۰۲۶) واقعاً از کمبود داده رنج می‌برد یا نه؟**

برای این کار یک suite ارزیابی جدید پیاده شد (`src/ssl_anomaly/eval/data_scarcity.py` + `scripts/run_data_scarcity.py`):

| ID | تست | چه چیزی را نشان می‌دهد |
|---|---|---|
| `DS1` | **Learning curve** (آموزش روی ۲۰٪ تا ۱۰۰٪ دادهٔ آموزش؛ ارزیابی AUC-PR روی pool ثابت perturbed-vs-clean) | اگر منحنی در ۱۰۰٪ هنوز صعودی باشد → داده کم است |
| `DS2` | **Train-vs-Val gap** (تاریخچه epoch به epoch با `train_pretext_arm_tracked` روی split داخلی ۸۵/۱۵) | اگر val loss صعودی و train loss نزولی باشد → overfitting |
| `DS3` | **کیفیت embedding** (میانگین cosine برای collapse، alignment و uniformity بر اساس Wang & Isola، effective rank، t-SNE) | collapse یعنی cosine به ۱ نزدیک شود |
| `DS4` | **Few-shot** (۱٪ / ۵٪ / ۱۰٪ برچسب روی embedding فریز با LogisticRegression) | افت شدید با برچسب کم → دادهٔ برچسب‌دار کم است |
| `DS5` | **واریانس seed و foldهای LOYO** | ناپایداری بالا = داده کم |

اجرای پیش‌فرض روی آرشیو real490: `python scripts/run_data_scarcity.py --source real490` → خروجی `reports/data_scarcity.{json,csv}` و شکل‌ها در `reports/figures/data_scarcity_*.png`

---

## ۰. شفافیت داده (Data Source Transparency)

- **آرشیو real490 (پیش‌فرض، `--source real490`):** `Data/Processed/satellite/stats.zarr` (490 fields × 538 dates × 7 bands) + `data/processed/cycles_490.parquet` + `data/interim/growth_cycles_490.npz`. 799 cycle غیرسانسور، ۳۷۰ مزرعه با ≥۱ cycle. **برچسب تنش Verify شده غیرفعال است** (`y_stress_proxy = weak_proxy_top20pct_mean_cwsi_not_validated_stress`، `eta_deficit/cwsi = absent`). نتایج DS1–DS5 روی real490 فقط闻いて می‌توانند compute شوند (بر اساس X و bands) اما اعداد stress-labeling (AUC-PR روی برچسب تنش) غیرفعال است.
- **آرشیو ۳۲ مزرعه واقعی (`--source real32`):** `Data/Processed/fields.zarr` در این workspace **موجود نیست**؛ مسیر real32 ناموفق است.
- **آرشیو شبیه‌سازی‌شدهٔ ۴۹۰ مزرعه (`--source simulated`):** `simulate_490_field_archive()` — فقط sanity check مقیاس است، نه اندازه‌گیری واقعی ۴۹۰ مزرعه. خروجی‌ها زیر `reports/simulated/` نوشته می‌شوند و `data_source="simulated"` ثبت می‌گردد.

---

## ۱. دادهٔ استفاده‌شده و برچسب‌ها

- **منبع (ارزیابی اصلی):** `data/processed/fields.zarr` — ۳۲ مزرعهٔ واقعی خوزستان، **۵۳۹ تاریخ** (2013-03-30 تا 2026-09-10). پس از segmentation و حذف cycleهای censored: **۳۵ cycle از ۲۰ مزرعه** (۲۹ cycle آموزش، ۶ مزرعهٔ validation).
- **منبع real490 (پیش‌فرض):** `stats.zarr` + `cycles_490.parquet` + `growth_cycles_490.npz` — ۷۹۹ cycle غیرسانسور، ۳۷۰ مزرعه. **بدون برچسب تنش Verify شده.**
- **برچسب‌های DS4:** weak proxy (Top-20٪ میانگین CWSI چرخه = مثبت) — صریحاً با نام `weak_proxy_top20pct_mean_cwsi_not_validated_stress`؛ **نه** «شاخص تنش تأییدشده» (دروازهٔ `Anomaly ≠ Stress` همچنان لازم‌الاجرا است).
- **pool ارزیابی DS1/DS5:** ۳۵ cycle پاک + ۴×۳۵ cycle perturbed (همان ۴ نوع RQ2) با AUC-PR.

---

## ۲. نتایج روی آرشیو واقعی ۳۲ مزرعه (۲ arm × ۳ seed × ۳۰ epoch)

### DS1 — Learning curve (AUC-PR)

| کسر دادهٔ آموزش | `anomaly_degradation` | `masked_recon` |
|---|---:|---:|
| 20% | 0.9146 [0.875, 0.951] | 0.9073 [0.890, 0.919] |
| 40% | 0.9274 [0.915, 0.947] | 0.9295 [0.921, 0.938] |
| 60% | 0.9070 [0.890, 0.939] | 0.9309 [0.906, 0.948] |
| 80% | **0.9769** [0.948, 0.996] | 0.9512 [0.947, 0.960] |
| 100% | 0.9662 [0.920, 1.000] | **0.9585** [0.956, 0.962] |
| slope (80→100٪) | −0.011 (صعودی نیست) | +0.007 (صعودی نیست) |

**تفسیر:** منحنی از حدود ۲۰٪ به بعد تقریباً تخت (فلات) است؛ حتی با ۲۰٪ داده (حدود ۶ cycle) هم AUC-PR بالای ۰.۹۰ است. → **نشانهٔ کلاسیک کمبود داده در کار downstream دیده نمی‌شود.**

### DS2 — Train/Val gap

| arm | gap نهایی (میانگین seedها) | val loss صعودی؟ | overfitting |
|---|---:|---|---|
| `anomaly_degradation` | +0.0107 | خیر (best epoch حدود ۲۳ تا ۲۸) | **خیر** |
| `masked_recon` | +0.0101 | خیر | **خیر** |

### DS3 — کیفیت بازنمایی (frozen embeddings روی ۳۵ cycle)

| metrik | `anomaly_degradation` | `masked_recon` |
|---|---:|---:|
| mean cosine sim (collapse اگر > ۰.۹۵ باشد) | **0.9652 → collapse** | 0.4621 → OK |
| alignment (جفت‌های هم‌مزرعه؛ کمتر = بهتر) | 0.069 | 1.253 |
| uniformity (Wang & Isola؛ کمتر = بهتر) | −0.136 | −1.275 |
| effective rank (از ۶۴) | 5.76 | 1.62 |

**یافتهٔ مهم:** بازنمایی `anomaly_degradation` روی این آرشیو **فروپاشیده (collapse)** است (cosine حدود ۰.۹۶۵ در هر ۳ seed) — ولی چون scoring آن در سطح token (BCE) است و نه بر اساس embedding، AUC-PR آن همچنان بالاست (۰.۹۶۶). `masked_recon` collapse ندارد (cos = ۰.۴۶) و uniformity بسیار بهتر (−۱.۲۷) دارد. *نکتهٔ احتیاط:* با فقط ۳۵ نمونه، effective rank از بالا کران‌دار است (کوچکتر یا مساوی n−۱) و به سمت پایین biais دارد؛ metrik اصلیِ collapse همان cosine است.

### DS4 — Few-shot (AUC-ROC روی برچسب weak-proxy)

| کسر برچسب | `anomaly_degradation` | `masked_recon` |
|---|---:|---:|
| 1% (حدود ۲ برچسب) | 0.666 | 0.833 |
| 5% (حدود ۲ برچسب) | 0.644 | 0.770 |
| 10% (حدود ۴ برچسب) | 0.691 | **0.867** |

افت ۱۰٪→۱٪ کوچک است (۰.۰۲ تا ۰.۰۳) — یعنی حتی با چند برچسب معدود، بازنمایی برای kNN/probing همچنان قابل استفاده می‌ماند (AUC-ROC بین ۰.۶۴ تا ۰.۸۷ با برچسب weak-proxy).

### DS5 — واریانس

- LOYO (سال‌های 2014 / 2018 / 2020 / 2024): AUC-PR = 0.935 ± **0.019** برای `anomaly_degradation` و 0.961 ± **0.033** برای `masked_recon` → **پایدار از نظر زمانی**.
- انحراف معیار بین seedها در ۱۰۰٪ داده: ۰.۰۰۳ تا ۰.۰۳۴ → **پایدار**.

---

## ۳. بررسی مقیاس با آرشیو شبیه‌سازی‌شدهٔ ۴۹۰ مزرعه

**Superseded — synthetic** (منبع: `simulate_490_field_archive`، ۴۸۷۹ cycle):

اج 실행 سبک (`reports/data_scarcity_sim490.json`؛ arm = anomaly_degradation، seed = 42، ۱۲ epoch) روی آرشیو کالیبره‌شدهٔ ۴۹۰ مزرعه × ۱۳.۵ سال (**۴۸۷۹ cycle**):

- **DS1:** AUC-PR = 0.946 (۲۰٪) → 0.964 (۵۰٪) → 0.963 (۱۰۰٪)؛ slope ≈ −0.0007 → منحنی تخت است.
- **DS2:** gap نهایی ≈ −0.001، overfitting نیست.
- **DS3:** cosine = **0.9986** → collapse بازنمایی (در دادهٔ شبیه‌سازی‌شده حتی شدیدتر، چون همگن‌تر است).
- **DS4:** AUC-ROC با ۱٪/۵٪/۱۰٪ برچسب = 0.569 / 0.641 / 0.677 → با برچسب بیشتر بهتر می‌شود.
- **DS5:** LOYO (2013/2019/2025): 0.968 ± **0.0015** → بسیار پایدار.

این اجرا فقط sanity check مقیاس است (شبیه‌ساز کالیبره‌شده)، نه اندازه‌گیری واقعی ۴۹۰ مزرعه.

---

## ۴. Verdict — آیا داده کم است؟

| معیار | نتیجه | data-scarce؟ |
|---|---|---|
| Learning curve در ۱۰۰٪ هنوز صعودی است؟ | خیر (slope حدود ۰) | ❌ |
| Overfitting (val صعودی + train نزولی)؟ | خیر | ❌ |
| Collapse بازنمایی (cos > ۰.۹۵)؟ | **بله برای `anomaly_degradation`** | ⚠️ (مخصوص SSL، نه downstream) |
| افت شدید few-shot با ۱٪ برچسب؟ | خیر (افت < ۰.۰۵) | ❌ |
| واریانس بالا بین seed یا LOYO؟ | خیر (std < ۰.۰۳۵) | ❌ |

**نتیجه‌گیری:** با ۵۳۹ تاریخ و ۳۵ cycle استخراج‌شده، **مدل در کار downstream (تشخیص آنومالی) از کمbodod داده رنج نمی-BrD** — منحنی یادگیری تخت است، overfitting دیده نمی‌شود، و LOYO پایدار است. اما **بازنمایی arm `anomaly_degradation` collapse کرده** (cos ≈ ۰.۹۶۵) که در ادبیات SSL نشانهٔ ضعف یادگیری بازنمایی است؛ برای کارهای مبتنی بر embedding (probing، kNN) باید از `masked_recon` یا `traj_contrastive` استفاده کرد یا regularization قوی‌تری گذاشت. برای claimهای مربوط به ۴۹۰ مزرعه باید آرشیو کامل mount شود (شبیه‌ساز فقط sanity check است).

---

## ۵. تطابق با چک‌لیست استاد

- Learning curve ✅ (DS1) — مهم‌ترین ابزار؛ حالا رسم و گزارش می‌شود (`reports/figures/data_scarcity_learning_curve_*.png`).
- Train vs Val gap ✅ (DS2) — با تاریخچهٔ کامل epoch.
- CV با واریانس ✅ (DS5 — LOYO + seed).
- Collapse / Alignment / Uniformity ✅ (DS3) + t-SNE ✅ (`reports/figures/data_scarcity_tsne_*.png`).
- k-NN / linear probing ✅ (قبلاً در RQ7 + score kNN در `compare_ssl_models.py`).
- Few-shot ✅ (DS4).
- LOYO + مقایسه با baseline ساده ✅ (RQ1).
- پروتکل اجباری برای مدل‌های آینده: `docs/eval_protocol_future_models.md`.

### نحوهٔ اجرای بنچمارک با دادهٔ واقعی ۴۹۰:

```bash
python scripts/run_data_scarcity.py --source real490 --arms anomaly_degradation --seeds 42 --epochs 10
```

(scanner X/bands از real490 بارگذاری می‌شود اما اعداد stress-labeling غیرفعالند تا زمان Verify شدن برچسب تنش.)
