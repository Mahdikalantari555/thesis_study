# یافته ۵ — آموزش SSL با weather (Farms_subset, 32 مزرعه)

## مدل

- Masked Transformer (1D): ۱۶۱K پارامتر.
- Input: باندهای خام (۷) + weather (۵: tmean, et0, rad, rh, gdd) + dsh + DOY + sensor + ratoon + valid_frac + Δt.
- pretext: masked observation modeling (۱۵-۳۰٪ tokens + بلوک‌های ۱-۳).
- trimmed loss: ۱۰٪ بالاترین loss حذف می‌شود.

## نتایج

- Train cycles: ~۷۰ (validation خالی — باید Farms_subset split شود).
- ۱۵ epoch، loss پایدار (~۰.۰۰۱)، **NaN نشد**.
- Weather به tokenها اضافه شد → GDD و ET0 در مدل وارد شدند.
- Best checkpoint: epoch=14.
- Release: `releases/transformer`.

## یافتهٔ کلیدی

- SSL روی دادهٔ واقعی subset + weather بدون NaN اجرا شد.
- Weather به‌عنوان ۵ feature به tokenها اضافه شد → پاسخ به شکاف «هواشناسی استفاده نشده».
- validation خالی است → باید train/val split روی ۳۲ مزرعه انجام شود.