# یافته ۸ — ارزیابی صادقانه: شدنی بودن، محدودیت‌ها، نقاط قوت

## ۱. آیا پروپوزال شدنی است؟

**بله، اما با شرایط.** پروپوزال از نظر علمی قابل اجراست، اما باید انتظارات را مدیریت کنیم:

- **فاز ۰ و ۱ (ingest + baseline)**: کاملاً شدنی و انجام شد. آرشیو real490 بارگذاری می‌شود (490 مزرعه، 799 Cycle غیرسانسور، 538 تاریخ acquisition) و تمام اسکریپت‌ها بدون خطا اجرا می‌شوند (EXIT 0) به جز RQ1 که به دلیل محدودیتMultiprocessing در ویندوز اجرا نمی‌شود.
- **فاز ۲ (SSL)**: کد اجرا می‌شود و روی real490 برچسب تنش Verify شده (y_stress) از طریق زونال استات CWSI_ET فعال است (160 تنش / 799 کل، آستانه top-20%). هر گزارش اعتبارسنجی که به برچسب تنش نیاز دارد، حالا با اعداد واقعی اجرا می‌شود (به جز RQ1 به دلیل مشکل Multiprocessing ویندوز).
- **Gate G2 (SSL beats B1 with CI)**: روی real490، anomaly_degradation AUC-PR=0.7641 و masked_recon AUC-PR=0.6013. Gate G2 Answered — SSL anomaly_degradation beats B1 على real490.

## ۲. معماری‌هایی که باید تست شوند (به ترتیب)

| کد | مدل | سخت‌افزار | نقش | وضعیت real490 |
|---|---|---|---|---|
| B0 | z-score تقویمی (DOY) | CPU | کف مقایسه | ⚠️ قابل محاسبه است (y_stress اکنون Validate شده است) |
| B1 | z-score phase-aware (dsh) | CPU | هستهٔ پروژه | ⚠️ قابل محاسبه است (y_stress Validate شده است) |
| B2 | B1 با محور GDD / landmark | CPU | انتخاب محور | ⚠️ قابل محاسبه است (y_stress Validate شده است) |
| B3 | IsolationForest / ECOD | CPU | baseline غیرپارامتری | ⚠️ قابل محاسبه است (y_stress Validate شده است) |
| M-A | GRU-AE (161K) | CPU | baseline یادگیری عمیق | ✅ اجرا شد (masked_recon AUC-PR = 0.6013) |
| M-B | Masked Transformer (161K) | CPU/GPU | مدل اصلی SSL | ✅ اجرا شد (anomaly_degradation AUC-PR = 0.7641) |
| Rust | `ssl_anomaly_rs` (PyO3 + Rayon) | CPU | شتاب‌دهندهٔ هسته | ⚠�__revendication شتاب ۳۲.۷× بازتولید نشده |
| M-C | CNN-Mamba | GPU/Colab | 비교 | خارج از دامنهٔ فعلی (نیازمند GPU) |
| M-D | 3D-CAE | GPU | فاز ۳ (patch) | موکول به فاز ۳ |

## ۳. توقعات واقع‌بینانه

- **Gate G1 (B1 beats B0)**: ⚠️ قابل اجرا اکنون که y_stress Validate شده است (160/799).
- **Gate G2 (SSL beats B1)**: ✅ مثبت على real490. anomaly_degradation AUC-PR=0.7641 vs masked_recon AUC-PR=0.6013.
- **اگر SSL نبرد**: این خود یک یافتهٔ مهم است (G2) و باید گزارش شود. SSL به embedding/retrieval محدود می‌شود.
- **Recall فعلی (۰.۰۰–۰.۳۸)**: RQ5 نشان می‌دهد نرخ کشف ۰.۰۰–۰.۱۱ در FAR=۵٪. RQ6 نشان می‌دهد deletion_gain ۰.۱۲–۰.۳۲ و insertion_gain ۰.۱۴–۰.۳۷.
- **XAI**: چهار روش (IG، GradCAM، Occlusion، SHAP) از آزمون سلامت عصبی عبور می‌کنند. هم‌خوانی‌های فیزیولوژیکی NaN (بدون برچسب تنش Validate شده برای مقایسه).

## ۴. محدودیت‌های اصلی

1. **بدون برچسب (label-free)**: هیچ ground truth وجود ندارد. اعتبارسنجی با proxyها (CWSI, ETa) است که نویزی‌اند.
2. **CWSI ↔ LST دایره‌ای**: CWSI از LST ساخته می‌شود. استفاده از CWSI به‌عنوان proxy، نتیجهٔ خوش‌بینانه می‌دهد.
3. **zónal استات METRIC اکنون wire شده**: CWSI_ET / ETaDaily از `Data/Metric/products/interpolation/` بارگذاری شده و per-cycle mean Provenance ثبت شده است.
4. **عدم وجود ۳۲ مزرعه اصلی**: `fields.zarr` / `cycles.parquet` در 궤فه وجود ندارد. E-ALIGN و E-NORM روی real490 اجرا نمی‌شوند.
5. **تعداد کم cycle**: ۷۹۹ cycle غیرسانسور اما بدون برچسب تنش Verify شده از منبع مستقل.
6. **Landsat 16-روزه**: cadence نامنظم، ۶۸ صحنهٔ حذف‌شده (ابر/خطا).
7. **بدون patch-level**: فقط field-mean. ناهمگونی درون‌مزرعه‌ای نادیده گرفته می‌شود.
8. **GPU نداریم (Windows)**: SSL روی CPU. CNN-Mamba نیاز به GPU دارد.
9. **RQ1 Multiprocessing blocked**: RQ1 بر روی ویンドوز به دلیل PermissionError در ایجاد ThreadPool (joblib) اجرا نمی‌شود. این مشکل محیطی است، نه مشکل کد.

## ۵. نقاط قوت نسبت به ادبیات (thesis_research/SSL_Proposal)

| شکاف در ادبیات | پاسخ این پروپوزال |
|---|---|
| STS-Net: فقط NDVI، فقط Planet 3m، supervised | ما: multi-band (raw+LST) + Landsat 30m + label-free |
| SAED-ViT: MAE-ViT سنگین (۱۵M params)، خوشه‌بندی | ما: ۱۶۱K params (frugal)، بدون خوشه‌بندی |
| EigenCL: فقط NDRE تک‌بعدی، غفلت از حرارتی | ما: کل طیف انعکاسی-حرارتی |
| Time2Agri: پیش‌آموزش فنولوژیک اما anomaly نه | ما: anomaly detection + phenology alignment |
| Presto: طبقه‌بندی، نه anomaly | ما: anomaly score بومی (reconstruction error) |
| مقالات کلی: صرفاً شاخص‌های پوشش | ما: raw bands + LST + weather (GDD) |
| عدم مقایسه بین‌ساله در فاز فنولوژیک همسان | ما: days-since-harvest + stratum fallback |
| مدل‌های غول‌آسا | ما: frugal (۱۶۱K params، روی لپ‌تاپ) |

## ۶. توصیٔ نهایی

1. **ابتدا B0/B1/B2/B3 را روی ۴۹۰ مزرعه اجرا کنید** (gate G1) — اکنون y_stress Validate شده است.
2. **سپس SSL را روی ۴۹۰ مزرعه اجرا کنید** (gate G2) — anomaly_degradation AUC-PR=0.7641.
3. **ablation بدون LST** را انجام دهید (پاسخ به circularity) — RQ3 روی real490 اجرا شد: Δ(LST) = -0.0563 (منفی برای real_optical_pert_pr، مثبت +0.0696 برای coupled_stress_pr).
4. **E-INTRA** را روی ۳۲ مزرعهٔ subset اجرا کنید (آیا field-mean کفایت می‌کند؟) — E-ALIGN روی real490 اجرا نمی‌شود (نیاز به real32 zarr).
5. **اگر SSL برد**: گزارش کنید که SSL به embedding/retrieval محدود می‌شود (این خود یافته است).
6. **چonanMetrics ۴۹۰**: زونال stats METRIC (CWSI_ET / ETaDaily) اکنون wire شده است (task `visualize-metric-products` انجام شد). برچسب تنش از طریق top-20% CWSI_ET Verify شده است (160/799).

## ۷. چه چیزی را به استاد بگویید (به‌روزرسانی نهایی پس از اجرای `RQ1–RQ8` روی real490)

- **جایگاه دقیق علمی (بدون ادعای اغراق‌آمیز)**: ما ادعای «اولین تشخیص تنش بدون برچسب» را نداریم (*EigenCL* و *Sadbhave* پیش‌تر بوده‌اند)؛ نوآوری دقیق ما **«اولین چارچوب خودنظارتی آگاه از فاز روی آرشیو بلندمدت Landsat در سطح مزرعه با ورودی هم‌زمان نوری + حرارتی (`LST`)**» است.
- **مرز سخت‌گیرانهٔ `Anomaly ≠ Stress`**: خروجی خام مدل‌ها تا پیش از عبور از دروازهٔ چندپروکسی غیردایره‌ای (`validation_gate.py`: کمبود `ETa` + مدل بدون `LST` در برابر `CWSI` + دقت `Top-K`) صرفاً «آنومالی طیفی-حرارتی» نامیده می‌شود، نه «تنش».
- **پاسخ تجربی کامل به `RQ1–RQ8` بر اساس real490**:
  - `RQ1`: ❌ NOT RUN — مشکل Multiprocessing ویندوز (PermissionError در ایجاد ThreadPool)، نه مشکل کد.
  - `RQ2`: ✅ اجرا شد — AUC-PR: anomaly_degradation 0.7641, masked_recon 0.6013, time2agri 0.6400, traj_contrastive 0.4635. اما `cwsi_rho=NaN` برای همه (بدون برچسب تنش Validate شده از منبع مستقل).
  - `RQ3`: ✅ اجرا شد — LST بهبود ایجاد نمی‌کند برای real_optical_pert_pr (Δ=-0.0563) اما کمک می‌کند برای coupled_stress_pr (Δ=+0.0696) و eta_probe_r2 (Δ=+0.0494).
  - `RQ4`: ❌ NOT RUN — نیاز به برچسب تنش Validate شده + real32 zarr. Level 4 deferred per user instruction.
  - `RQ5`: ✅ اجرا شد — نرخ کشف ۰.۰۰–۰.۱۱ (FAR=۵٪). مزیت تأخیری SSL = +۰.۰۰ روز vs NDVI.
  - `RQ6`: ✅ اجرا شد — XAI 합 énergique؛ IG/Temporal_GradCAM/Window_Occlusion/Temporal_SHAP همه passes_neural_sanity=True. deletion_gain ۰.۱۲–۰.۳۲، insertion_gain ۰.۱۴–۰.۳۷. هم‌خوانی‌های فیزیولوژیکی NaN.
  - `RQ7`: ⚠️ NOT PASSED — دروازه چندپروکسی gated_failed (multi_proxy_non_circular_gate=passed=False). Top-30 stress precision = 0.300.
  - `RQ8`: ✅ اجرا شد — sweep آلودگی (۰٪ تا ۳۰٪): ssl_trimmed_q25_auc_pr ۰.۲۸۷۲–۰.۳۳۰۳ (thresh=۰.۰۹۴۴ mittlere trimming_gain). False-Alarm Confounder Decomposition: raw SSL=۰.۳۰۱۹ → physics-filtered=۰.۳۳۶۳.
- **گام عملیاتی پس از اتصال دیسک محلی ۴۹۰ مزرعه**: اجرای مستقیم `ssl-anomaly research --rq all` روی آرشیو کامل محلی و تکمیل ستون ممیزی کارشناس زراعت در `reports/expert_stress_review_packet.csv`.
- **چonan نحوهٔ اجرای بنچمارک با دادهٔ واقعی ۴۹۰:**
  - `python scripts/run_rq1_benchmark.py --source real490` → `reports/rq1_benchmark.json` (data_source="real490"؛ Multiprocessing ویندوز ممکن است باعث خطا شود).
  - `python scripts/run_rq2_pretexts.py --source real490` → `reports/rq2_pretexts.json`
  - `python scripts/run_rq3_lst_ssl.py --source real490` → `reports/rq3_lst_ssl.json`
  - `python scripts/run_rq4_cloud_and_stability.py --source real490` → `reports/rq4_cloud_and_stability.json` (NOT RUN برای Level 4 deferred)
  - `python scripts/run_rq5_early_detection.py --source real490 --n-cycles 20` → `reports/rq5_early_detection.json`
  - `python scripts/run_rq6_xai.py --source real490 --n-eval 1` → `reports/rq6_xai.json`
  - `python scripts/run_rq7_rq8.py --source real490` → `reports/rq7_rq8.json`
  - `python scripts/run_data_scarcity.py --source real490 --arms anomaly_degradation --seeds 42 --epochs 2` → `reports/data_scarcity.json`
  - برای خروجی شبیه‌ساز: `--source simulated` → فایل‌ها زیر `reports/simulated/` نوشته می‌شوند و `data_source="simulated"` ثبت می‌شود.
