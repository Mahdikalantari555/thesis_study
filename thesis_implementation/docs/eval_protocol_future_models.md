# پروتکل ارزیابی اجباری برای مدل‌های آینده

این سند **الزامی** است: هر مدل جدیدی که بعداً آموزش می‌دهیم (معماری جدید، pretext جدید، تغییر tokenizer یا داده) **باید** این پروتکل را بگذراند تا هر claimای دربارهٔ «کافی بودن داده» یا «عملکرد واقعی مدل» قابل استناد باشد. این همان چک‌لیست «تشخیص کمبود داده» است که در `docs/findings/12_data_scarcity_diagnostics.md` پیاده و اجرا شده است.

## ۰. داده و پیش‌نیازها

- دادهٔ محلی: `data/processed/fields.zarr` (۳۲ مزرعه، ۵۳۹ تاریخ) و `data/processed/cycles.parquet` (اگر موجود نیست، `scripts/run_data_scarcity.py` خودش با segmentation می‌سازد).
- آرشیو کامل ۴۹۰ مزرعه روی مسیر خارجی؛ اگر mount نبود، fallback شبیه‌ساز کالیبره‌شده (`--source simulate490`) فقط برای sanity check مقیاس است و **هرگز** به‌عنوان نتیجهٔ واقعی گزارش نمی‌شود.
- محیط: `uv sync` یا `conda env create -f environment.yaml` (بسته به `pyproject.toml`؛ شکل‌ها با matplotlib).

## ۱. گام‌های اجباری برای هر مدل جدید

| گام | دستور | خروجی | gate |
|---|---|---|---|
| ۱. Data-scarcity diagnostics | `OMP_NUM_THREADS=1 python scripts/run_data_scarcity.py --arms <arm> --seeds 42,43,44 --epochs 30` | `reports/data_scarcity.json` + figures | thresholdهای §۲ |
| ۲. LOYO + baseline ladder | `python scripts/run_rq1_benchmark.py` | `reports/rq1_benchmark.json` | مدل باید از RF/GBT/NDVI/CWSI در بودجهٔ هشدار برابر بهتر باشد |
| ۳. Linear probing | `python scripts/run_rq7_rq8.py` | `reports/rq7_probing.csv` | پروب فریز باید از random-init بهتر باشد |
| ۴. Validation gate | خودکار در RQ1/RQ7 | `reports/expert_stress_review_packet.csv` | «آنومالی = تنش» فقط با عبور از دروازهٔ چندپروکسی |
| ۵. XAI (اگر claim علی می‌شود) | `python scripts/run_rq6_xai.py` | `reports/rq6_xai.json` | deletion/insertion و sanity check باید PASS کنند |

## ۲. Thresholdهای «داده‌کم» (verdict)

یک run به‌عنوان **data-scarce** علامت می‌خورد اگر هر یک از این‌ها true شود (`reports/data_scarcity.json` → `arms[*].verdict.flags`):

1. `learning_curve_still_rising`: slope بازهٔ آخر (۸۰٪→۱۰۰٪) بزرگتر از ۰.۰۱ → منحنی هنوز تخت نشده → دادهٔ آموزش کم است.
2. `train_val_overfitting_suspected`: val loss در ربع آخر epochها صعودی و train loss هنوز نزولی → overfitting.
3. `representation_collapse_suspected`: میانگین cosine جفتی روی embeddingهای فریز > ۰.۹۵ → collapse.
4. `few_shot_drop_flag`: افت AUC-ROC بین ۱۰٪ و ۱٪ برچسب > ۰.۲ → دادهٔ برچسب‌دار کم است.
5. ناپایداری: `loyo_auc_pr_std` یا `seed_std_learning_curve` > ۰.۰۵ → نتایج unstable هستند.

اگر هیچ‌کدام true نشد، claim «با دادهٔ موجود، مدل داده‌کم نیست» مجاز است (همان نتیجهٔ Finding 12 برای downstream).

## ۳. چک‌لیست قبل از هر claim

- [ ] `run_data_scarcity.py` با arm جدید اجرا شده و `verdict.data_scarcity_suspected=false` باشد (یا rationale برای هر flag true).
- [ ] Learning curve رسم شده باشد (`reports/figures/data_scarcity_learning_curve_<arm>.png`) و در finding مستند شده باشد.
- [ ] t-SNE embeddingها (`data_scarcity_tsne_<arm>.png`) خوشهٔ تک‌نقطه‌ای obvious (collapse) نداشته باشد.
- [ ] LOYO + baselines (RQ1) اجرا شده باشد؛ مدل از RF/GBT/NDVI/CWSI در Recall@10% بهتر باشد.
- [ ] Linear probe (RQ7) از random-init بهتر باشد.
- [ ] اگر claim «تنش» می‌شود: دروازهٔ `Anomaly ≠ Stress` گذرانده شده باشد.
- [ ] نتایج در `docs/findings/` با شمارهٔ بعدی و با اعداد JSON مستند شده باشد.

## ۴. چه چیزهایی را هرگز claim نکنید

- «اولین تشخیص بدون برچسب تنش» (کارهای پیشین مثل EigenCL وجود دارند).
- «۴۹۰ مزرعهٔ واقعی تست شد» وقتی فقط شبیه‌ساز اجرا شده است.
- «داده کافی است» بدون learning curve.
- «بازنمایی خوب است» وقتی cosine collapse بالای ۰.۹۵ است.

## الحاقیه: اعتبارسنجی آینده‌نگر رشد

برای آزمایش جدید، پیش از استفاده از اعداد LOYO یا ادعای تعمیم به آینده، پروتکل [اعتبارسنجی انحراف رشد](growth_validation.md) و OpenSpec مرتبط را بخوانید. LOYO با آموزش روی سال‌های بعدی پیش‌بینی آینده نیست؛ هم‌چنین عبور یک «validation gate» بر اساس proxy به‌تنهایی اثبات تشخیص تنش فیزیولوژیک نیست. اسکریپت جدید baselineهای NDVI و GRU/Transformer آموزش‌دیده مجدد را در حساسیت مصنوعی retrospective ارزیابی می‌کند، نه همه مدل‌ها و نه تنش واقعی.
