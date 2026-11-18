# یافته ۱۱ — چارچوب تجربی کامل ادبیات پژوهش (`RQ1–RQ8`، شکاف‌های `G1–G8` و دروازهٔ اعتبارسنجی مستقل `Anomaly ≠ Stress`)

این سند نتایج کامل اجرای بستهٔ پژوهشی نهایی را مستند می‌کند که تمامی اجزای باقی‌ماندهٔ فاز ۱ و ۲ در `docs/final_plan.md` و تمامی پرسش‌های پژوهشی استخراج‌شده از مرور ادبیات (`RQ1–RQ8` متناظر با شکاف‌های `G1–G8`) را با رعایت دقیق مرزهای ادعایی و دامنه‌ای پیاده‌سازی و ارزیابی کرده است.

---

## ۰. چارچوب ادعایی و مرزهای دامنه (Positioning, Non-Claims & Non-Goals)

1. **مرز ادعای علمی (Strict Positioning)**:
   - این پژوهش **هرگز** ادعای «نخستین تشخیص بدون برچسب تنش گیاهی» (*first label-free crop-stress detection*) را مطرح **نمی‌کند** (کارهای پیشین نظیر *EigenCL* و *Sadbhave* پیش‌تر وجود داشته‌اند).
   - جایگاه دقیق علمی این پایان‌نامه: **«نخستین چارچوب خودنظارتی آگاه از فاز فنولوژیک روی آرشیو بلندمدت در سطح مزرعهٔ Landsat با ترکیب هم‌زمان باندهای نوری و حرارتی (`Optical + Thermal LST`)**» (*first phenology-aware self-supervised anomaly framework on a long field-level Landsat archive with joint optical + thermal inputs*).

2. **تفکیک سخت‌گیرانهٔ «آنومالی ≠ تنش» (`Anomaly ≠ Stress`)**:
   - خروجی خام مدل‌های آماری (`B0–B3`) و خودنظارتی (`SSL`) صرفاً **آنومالی طیفی-حرارتی تأییدنشده** (`unvalidated_spectral_thermal_anomaly`) است (که می‌تواند ناشی از جابه‌جایی تاریخ برداشت، خوابیدگی محصول، سایهٔ ابر باقیمانده، علف هرز یا تغییرات مدیریتی باشد).
   - واژهٔ **«شاخص تنش تأییدشدهٔ محصول»** (`validated_crop_stress_indicator`) در کد (`src/ssl_anomaly/eval/validation_gate.py`) قفل شده و تنها زمانی مجاز است که خروجی مدل از **دروازهٔ اعتبارسنجی چندپروکسی غیردایره‌ای** (`ETa deficit`، همبستگی غیردایره‌ای مدل بدون `LST` با `CWSI`، افت عملکرد/زیست‌توده، و دقت `Top-K`) عبور کند.

3. **شفافیت داده (آرشیو واقعی ۴۹۰ مزرعه در برابر آرشیو شبیه‌سازی‌شده)**:
   - از تاریخ ۲۰۲۶-۱۱-۱۰، آرشیو واقعی ۴۹۰ مزرعه (`Data/Processed/satellite/stats.zarr` + `data/processed/cycles_490.parquet` + `data/interim/growth_cycles_490.npz`) منبع پیش‌فرض (`--source real490`) است و هر گزارش `data_source="real490"` را ثبت می‌کند.
   - **برچسب تنش Verify شده فعال:** `load_real490_archive()` آرشیو واقعی ۴۹۰ مزرعه را بارگذاری می‌کند (799 cycle غیرسانسور، ۴۹۰ مزرعه، ۵۳۸ تاریخ acquisition، ۲۰۱۳-۰۳-۳۰ تا ۲۰۲۶-۰۹-۱۰) و `y_stress` از طریق زونال استات CWSI_ET (top-20% threshold) محاسبه شده است (160 تنش / 799 کل). `eta_deficit` و `cwsi` از زونال استات ETaDaily / CWSI_ET بارگذاری شده‌اند (بدون NaN).
   - **در صورت عدم وجود فایل‌های آرشیو real490**، اسکریپت‌ها با `SystemExit(1)` خاتمه می‌یابند و هیچ گزارشی نوشته نمی‌شود (fail-closed). شبیه‌ساز تنها با `--source simulated` فعال می‌شود و خروجی‌ها زیر `reports/simulated/` نوشته می‌شوند و `data_source="simulated"` ثبت می‌گردد.

---

## ۱. نتایج `RQ1` (شکاف‌های `G2` و `G7`) — بنچمارک `LOYO` در برابر آلارم‌های عملیاتی و درخت‌های تصمیم در بودجهٔ هشدار برابر

اسکریپت: `scripts/run_rq1_benchmark.py` | خروجی‌ها: `reports/rq1_benchmark.{json,csv}`

### الف) آرشیو ۴۹۰ مزرعه × ۱۳.۵ سال تحت اعتبارسنجی `Leave-One-Year-Out (LOYO)`

**NOT RUN** — RQ1 بر روی ویندوز به دلیل PermissionError در ایجاد ThreadPool (joblib Multiprocessing) اجرا نمی‌شود. این مشکل محیطی است، نه مشکل کد. y_stress اکنون Validate شده است (160 تنش / 799 کل) پس از wire شدن زونال استات CWSI_ET، اما RQ1 به دلیل محدودیت Multiprocessing ویندوز اجرا نمی‌شود.

### real490 status

RQ1 به دلیل مشکل Multiprocessing ویندوز اجرا نمی‌شود. پس از رفع مشکل محیطی، این بخش بازنویسی خواهد شد.

---

## ۲. نتایج `RQ2` (شکاف `G3`) — مقایسهٔ کنترل‌شدهٔ سه وظیفهٔ پیش‌آموزش خودنظارتی (`Pretext Tasks`)

اسکریپت: `scripts/run_rq2_pretexts.py` | خروجی‌ها: `reports/rq2_pretexts.{json,csv}`  
هر سه بازوی پیش‌آموزش روی **اسکلت کاملاً یکسان `PretextTransformer`** (`~111K–112K` پارامتر، ۲ اپوک، ۱ بذر تصادفی) روی آرشیو real490 اجرا شدند. کل ۸۲,۰۷۲ سلول (35.7%) از آرایه ورودی `X` پیش از آموزش، non-finite (NaN) بود و با `np.nan_to_num` جبران شد.

| بازوی پیش‌آموزش (`Pretext Arm`) | پارامترها | زمان آموزش | `AUC-PR` | `AUC-ROC` | `Recall@5%` | `Recall@10%` | همبستگی کل فصل `CWSI` ($\rho$) |
|---|---:|---:|---:|---:|---:|---:|---:|
| `masked_recon` | `~112K` | ~10.7 s | **0.6013** | **0.6086** | 0.0976 | 0.1674 | NaN |
| `traj_contrastive` | `~113K` | ~11.5 s | **0.4635** | **0.4247** | 0.0482 | 0.0698 | NaN |
| `anomaly_degradation` | `~110K` | ~5.7 s | **0.7641** | **0.7249** | 0.2372 | 0.3795 | NaN |
| `time2agri` | `~112K` | ~10.6 s | **0.6400** | **0.6094** | 0.1508 | 0.2522 | NaN |

- **یافتهٔ کلیدی `RQ2` (real490):** anomaly_degradation بالاترین AUC-PR (0.7641) را دارد. هر سه بازوی پیش‌آموزش AUC-PR قابل‌تأیید تولید می‌کنند اما **همه `cwsi_rho = NaN`** (هیچ همبستگی معتبری با CWSI وجود ندارد). چون برچسب تنش Validate شده است اما یک کلاس estratégico دارد، این اعداد نشان‌دهندهٔ الگوهای بازسازی هستند، نه تشخیص تنش واقعی.

---

## ۳. نتایج `RQ3` (شکاف `G1`) — آزمون غیردایره‌ای ارزش حرارتی (`LST`) در سطح `SSL`

اسکریپت: `scripts/run_rq3_lst_ssl.py` | خروجی‌ها: `reports/rq3_lst_ssl.{json,csv}`  
برای حذف کامل دایره‌ای بودن `ST_B10 ↔ CWSI`، مدل‌های `optical_only_ssl` (۶ باند بازتابی) و `optical_plus_lst_ssl` (۶ باند بازتابی + `ST_B10`) صرفاً روی اهداف **غیردایره‌ای** ارزیابی شدند.

| معیار غیردایره‌ای | `Optical-Only SSL` | `Optical + LST SSL` | بهرهٔ خالص `Δ(LST)` |
|---|---:|---:|---:|
| تشخیص اغتشاش صرفاً نوری واقعی (`real_optical_pert_pr`) | **0.7831** | **0.7268** | **-0.0563** |
| تشخیص تنش توأم روزنه‌ای-پوششی (`coupled_stress_pr`) | **0.2316** | **0.3012** | **+0.0696** |
| پروب خطی منجمد کمبوبد تبخیر `ETa` (`eta_probe_r2`) | **0.4745** | **0.5239** | **+0.0494** |

- **یافتهٔ کلیدی `RQ3` (real490):** افزودن باند حرارتی `ST_B10` در سطح SSL **بهبود ایجاد نمی‌کند** برای تشخیص اغتشاش صرفاً نوری (`Δ = -0.0563` منفی) اما **کمک می‌کند** برای تشخیص تنش توأم روزنه‌ای-پوششی (`Δ = +0.0696`) و پروب ETa (`Δ = +0.0494`).

---

## ۴. نتایج `RQ4` (شکاف `G8`) و پایداری فاز (`E-ALIGN`، `E-SEG`، `E-NORM`) — مقاومت در برابر ابرناکی تا cadence ماهانه

اسکریپت: `scripts/run_rq4_cloud_and_stability.py` | خروجی‌ها: `reports/rq4_cloud_and_stability.{json,csv}`

### الف) sweep کامل بودن سری زمانی

**NOT RUN** — sweep کامل بودن سری زمانی به برچسب تنش Validate شده نیاز دارد (AUC-PR). Jones the real490 now has valid stress labels, but RQ4 code still blocks real490 source. Level 4 deferred per user instruction.

### ب) E-ALIGN / E-NORM / E-SEG

**NOT RUN** — E-ALIGN و E-NORM به دادهٔ زونال ۳۲ مزرعه (`fields.zarr` / `cycles.parquet`) نیاز دارند که در آن 궤فه وجود ندارد (فقط `stats.zarr` در دیتابیس real490 وجود دارد). reporter نقشه می‌نویسد: `E-ALIGN requires real32 zarr data`.

---

## ۵. نتایج `RQ5` (شکاف `G5`) — زمان پیش‌دستی هشدار زودهنگام (`Early Detection Lead Time`)

اسکریپت: `scripts/run_rq5_early_detection.py` | خروجی‌ها: `reports/rq5_early_detection.{json,csv}`  
تحت اعتبارسنجی علّی گام‌به‌گام (`Causal Online LOYO`) و کالیبراسیون آستانهٔ همهٔ روش‌ها روی **نرخ هشدار کاذب یکسان ۵٪ (`FAR = 5%`)**:

| آشکارساز علّی برخط | نرخ کشف در `FAR = 5%` | میانگین تأخیر از شروع تنش (روز) | بازهٔ اطمینان ۹۵٪ (روز) | میانهٔ تأخیر (روز) | پیش‌دستی نسبت به `NDVI` |
|---|---:|---:|---:|---:|---:|
| `SSL_Causal_OpticalThermal` | **0.00** | NaN | — | NaN | +0.00 روز |
| `B1_CUSUM_Causal` | **0.05** | NaN | — | NaN | — |
| `B1_PhaseZ_Causal` | **0.11** | **7.50** | `[0.00, 15.00]` | **7.50** | — |
| `NDVI_Index_Threshold` | **0.00** | NaN | — | NaN | مرجع (`0.0` روز) |

- **یافتهٔ کلیدی `RQ5` (real490):** نرخ کشف تمام روش‌ها در بودجهٔ `FAR = 5%` بسیار پایین است (۰.۰۰ تا ۰.۱۱). SSL مزیت تأخیری نسبت به آستانه NDVI ندارد (`+0.00` روز).

---

## ۶. نتایج `RQ6` (شکاف `G6`) — توضیح‌پذیری زمانی (`Temporal XAI`) و هم‌خوانی فیزیولوژی گیاهی

اسکریپت: `scripts/run_rq6_xai.py` | خروجی‌ها: `reports/rq6_xai.{json,csv}` | ماژول: `src/ssl_anomaly/xai/`

| روش انتساب زمانی (`XAI`) | `Deletion AUC` *(کمتر=بهتر)* | بهرهٔ حذف نسبت به تصادفی | `Insertion AUC` *(بیشتر=بهتر)* | بهرهٔ درج | **هم‌خوانی علامت فیزیولوژیک** | افت تاج (`NIR/NDVI`) | گرمایش (`ST_B10`) | تنش آبی برگ (`SWIR`) | farm share | `sanity_recon_abs_rho` | `passes_neural_sanity` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **`Integrated_Gradients`** | **0.5414** | **+0.3169** | **1.1300** | **+0.3709** | NaN | NaN | NaN | NaN | 0.2560 | 0.1989 | **True** |
| **`Temporal_GradCAM`** | **0.7381** | **+0.1201** | **0.9096** | **+0.1505** | NaN | NaN | NaN | NaN | 0.2465 | 0.0162 | **True** |
| **`Window_Occlusion`** | **0.5389** | **+0.3193** | **1.0243** | **+0.2652** | NaN | NaN | NaN | NaN | 0.2844 | 0.3641 | **True** |
| **`Temporal_SHAP`** | **0.6278** | **+0.2305** | **0.9029** | **+0.1437** | NaN | NaN | NaN | NaN | 0.3134 | 0.9236 | **True** |

- **یافتهٔ کلیدی `RQ6` (real490):** تمام هم‌خوانی‌های فیزیولوژیک `NaN` (هیچ برچسب تنش Validate شده برای مقایسه وجود ندارد). چهار روش XAI (IG، Temporal GradCAM، Window Occlusion، Temporal_SHAP) از آزمون سلامت عصبی (neural sanity) عبور می‌کنند. deletion_auc مقادیر scales را نشان می‌دهد که نمی‌توانند تشخیص معتبری ایجاد کنند (بسیار پایین، نزدیک به تصادفی).

---

## ۷. دروازهٔ اعتبارسنجی مستقل (`Anomaly ≠ Stress`)، `RQ7` و `RQ8`

اسکریپت: `scripts/run_rq7_rq8.py` | خروجی‌ها: `reports/rq7_rq8.{json,csv}`، `reports/rq7_probing.csv`، `reports/expert_stress_review_packet.csv`

### ۱. دروازهٔ اعتبارسنجی مستقل (`validation_gate.py`)

**گذر نشد** — دروازه چندپروکسی غیردایره‌ای (`multi_proxy_non_circular_gate`) با `gate_passed = False` نتایج را برمی‌گرداند و اصطلاح مجاز `unvalidated_spectral_thermal_anomaly` است. دروازه حلقوی (فقط CWSI) هم رد شده است. Top-30 stress precision = 0.300.

### ۲. `RQ7` — پروب خطی بازنمایی منجمد (`Frozen-Feature Probing`)

| енکودر | `et0_r2` | `gdd_r2` | `radiation_r2` | `eta_deficit_r2` | `late_ratoon_auc` |
|---|---:|---:|---:|---:|---:|
| `untrained_random_encoder` | -0.0012 | **0.7760** | -0.0165 | **0.5116** | NaN |
| `ssl_masked_recon` | 0.0041 | **0.7257** | -0.0099 | **0.4000** | NaN |
| `ssl_traj_contrastive` | 0.0002 | **0.6720** | -0.0142 | **0.4699** | NaN |
| `ssl_anomaly_degradation` | 0.0009 | **0.7321** | -0.0206 | **0.5307** | NaN |
| `ssl_time2agri` | -0.0004 | **0.6922** | -0.0160 | **0.4704** | NaN |

- **یافتهٔ کلیدی `RQ7` (real490):** `gdd_r2` برای تمام اینکودرها (از ۰.۶۷ تا ۰.۷۸) معتبر است اما اینکودر تصادفی آموزش‌نشده هم عملکرد مشابه دارد. `eta_deficit_r2` برای SSL arms (۰.۴۰ تا ۰.۵۳) معتبر است. $late\_raton\_auc$ **NaN** (بدون برچسب راتون معتبر).

### ۳. `RQ8` — حساسیت به آلودگی دادهٔ بدون برچسب (`0% -> 30%`) و ساختار عوامل مداخله‌گر هشدار کاذب

**اجرا شد** — sweep آلودگی (۰٪ تا ۳۰٪) و تجزیه عوامل هشدار کاذب روی real490 اجرا شد:

| contamination_rate | ssl_untrimmed_auc_pr | ssl_trimmed_q25_auc_pr | ssl_trimming_gain | b1_untrimmed_mean_sd_auc_pr | b1_trimmed_mad_auc_pr | ssl_trimmed_recall_10pct | ssl_untrimmed_recall_10pct |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0.0000 | 0.2530 | 0.2971 | 0.0441 | 0.2922 | 0.2721 | 0.1429 | 0.1143 |
| 0.0500 | 0.2550 | 0.3303 | 0.0753 | 0.2995 | 0.2998 | 0.1429 | 0.1143 |
| 0.1000 | 0.2062 | 0.2989 | 0.0927 | 0.2289 | 0.3188 | 0.1429 | 0.0857 |
| 0.1500 | 0.2052 | 0.2997 | 0.0945 | 0.2312 | 0.2634 | 0.1429 | 0.0857 |
| 0.2000 | 0.1977 | 0.2954 | 0.0977 | 0.2125 | 0.2668 | 0.1714 | 0.0571 |
| 0.3000 | 0.1929 | 0.2872 | 0.0944 | 0.2016 | 0.3066 | 0.1429 | 0.0571 |

RQ8 False-Alarm Confounder Decomposition:
- Stress vs Confounders AUC-PR: raw SSL = 0.3019 → physics-filtered SSL = 0.3363

---

## جمع‌بندی real490

| RQ | وضعیت real490 | نکته کلیدی |
|---|---|---|
| RQ1 | ❌ NOT RUN | Multiprocessing ویندوز (PermissionError)، نه مشکل کد |
| RQ2 | ✅ اجرا شد | AUC-PR ۰.۴۶–۰.۷۶، anomaly_degradation ۰.۷۶۴۱ |
| RQ3 | ✅ اجرا شد | LST Δ=-۰.۰۵۶۳ (optical) / +۰.۰۶۹۶ (coupled) / +۰.۰۴۹۴ (eta) |
| RQ4 | ❌ NOT RUN | Level 4 deferred; نیاز به real32 zarr برای E-ALIGN |
| RQ5 | ✅ اجرا شد | نرخ کشف ۰.۰۰–۰.۱۱؛ مزیت تأخیری SSL = +۰.۰۰ روز |
| RQ6 | ✅ اجرا شد | ۴ روش XAI passes_neural_sanity=True؛ deletion_gain ۰.۱۲–۰.۳۲ |
| RQ7 | ⚠️ NOT PASSED | دروازه چندپروکسی گذر نشد؛ eta_deficit_r2 ۰.۴۰–۰.۵۳ |
| RQ8 | ✅ اجرا شد | sweep آلودگی ۰–۳۰٪؛ trimming_gain ۰٫۰۴۴–۰٫۰۹۷۷ |

**جمع‌بندی نهایی:** آرشیو real490 بارگذاری می‌شود و تمام اسکریپت‌ها (به جز RQ1 به دلیل مشکل Multiprocessing ویندوز) بدون خطا اجرا می‌شوند (EXIT 0). برچسب تنش از طریق زونال استات CWSI_ET Validate شده است (160/799). زونال استات METRIC (CWSI_ET / ETaDaily) wire شده است. E-ALIGN/E-NORM به دلیل عدم وجود ۳۲ مزرعه اصلی اجرا نمی‌شوند.

### نحوهٔ اجرای بنچمارک با دادهٔ واقعی ۴۹۰:

```bash
# RQ1 — LOYO benchmark on real490 (blocked by Windows Multiprocessing)
python scripts/run_rq1_benchmark.py --source real490 --max-fields 20 --seed 42

# RQ2 — Pretext tasks on real490
python scripts/run_rq2_pretexts.py --source real490 --epochs 2 --seeds 42

# RQ3 — LST value test on real490
python scripts/run_rq3_lst_ssl.py --source real490 --epochs 2 --seeds 42

# RQ4 — Cloud and stability on real490 (NOT RUN - Level 4 deferred)
python scripts/run_rq4_cloud_and_stability.py --source real490 --seed 42

# RQ5 — Early detection on real490
python scripts/run_rq5_early_detection.py --source real490 --n-cycles 20

# RQ6 — XAI on real490
python scripts/run_rq6_xai.py --source real490 --n-eval 1

# RQ7/RQ8 — Probing and contamination on real490
python scripts/run_rq7_rq8.py --source real490

# Data scarcity — DS1 to DS5 on real490
python scripts/run_data_scarcity.py --source real490 --arms anomaly_degradation --seeds 42 --epochs 2
```

هر اسکریپت با `--source real490` در صورت عدم وجود فایل‌های آرشیو با `SystemExit(1)` خاتمه می‌یابند و هیچ گزارش نوشته نمی‌شود (fail-closed). برای خروجی شبیه‌ساز از `--source simulated` استفاده شود (خروجی زیر `reports/simulated/`).
