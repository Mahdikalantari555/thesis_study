# یافته‌های اجرایی — تشخیص آنومالی فنولوژی‌محور در مزارع نیشکر

پوشه `docs/findings` ثبت یافته‌های حاصل از اجرای واقعی pipeline روی داده‌های متریک خوزستان است.
هر فایل یک یافتهٔ مستقل را با شواهد عددی مستند می‌کند تا برای ارائه به استاد راهنما و دفاع قابل استناد باشد.

## فهرست

1. `01_data_and_ingest.md` — داده و ingest
2. `02_phenology_cycles.md` — فنولوژی و چرخه‌ها
3. `03_baseline_indices_vs_raw.md` — مقایسهٔ baseline روی شاخص‌ها در برابر باندهای خام
4. `04_evaluation.md` — ارزیابی و تزریق مصنوعی
5. `05_ssl_training.md` — آموزش SSL و پایداری
6. `06_advisor_presentation_plan.md` — چه چیزی بعد از ارائهٔ پاورپوینت به استاد نشان دهیم
7. `07_validation_and_map.md` — validation split و نقشهٔ مکانی پویا (per-day anomaly)
8. `08_honest_assessment.md` — ارزیابی صادقانه: شدنی بودن، معماری‌ها، محدودیت‌ها، نقاط قوت
9. `09_anomaly_layer_explained.md` — لایهٔ آنومالی: معنا، منشأ، فرمول‌ها، علم پشتش
10. `10_remaining_code_results.md` — نتایج تکمیلی: بک‌اند Rust (`32.7×`)، تحلیل حساسیت Ablation، آزمون درون‌مزرعه‌ای `E-INTRA`، مقایسهٔ `B0–B3` و `GRU-AE` در برابر `Masked Transformer`
11. `11_rq1_to_rq8_empirical_framework.md` — چارچوب تجربی کامل ادبیات پژوهش (`RQ1–RQ8`، شکاف‌های `G1–G8`، دروازهٔ اعتبارسنجی مستقل `Anomaly ≠ Stress`، مقاومت ابری `date/Δt`، پیش‌دستی `+34` روزه و `Temporal XAI`)
12. `12_data_scarcity_diagnostics.md` — تشخیص کمبود داده و کیفیت بازنمایی (`DS1–DS5`: learning curve، train/val gap، collapse/alignment/uniformity + t-SNE، few-shot، واریانس seed/LOYO) + پروتکل_eval مدل‌های آینده در `docs/eval_protocol_future_models.md`
13. `13_literature_phenology_and_perturbations.md` — مرور منابع: استخراج خودکار فنولوژی/چرخه، محور زمان برای SSL، اختلال‌های نیشکر و SSL روی سری نامنظم (۳۹ منبع، ۲۲ موجود + ۱۷ تازه؛ پیشنهادهای R1–R8 برای سند تصمیم)
14. `14_stage_conditioned_thresholds.md` — تشخیص آنومالی با آستانه‌های conditional (npphen confidence envelope) روی ۷۹۹ چرخه و ۳۷۰ مزرعه: ۱۸,۵۰۵ مشاهده، ۱,۷۷۴ شانه (۹.۵۹%)
