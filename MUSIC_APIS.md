# APIهای رایگان موزیک برای ریلز

برای موزیک پس‌زمینه ریلز می‌توانی از این منابع **رایگان** و **APIدار** استفاده کنی:

---

## ۱. Jamendo (موزیک زیاد، API رایگان)

- **سایت:** https://www.jamendo.com  
- **دریافت API:** https://developer.jamendo.com  
  - ثبت‌نام کن و یک **Client ID** رایگان بگیر.  
  - در پروژه داخل `.env` قرار بده:  
    `JAMENDO_CLIENT_ID=کلید_تو`

- **مزایا:** موزیک زیاد، جستجو با کلمه (مثلاً emotional, sad, epic)، لایسنس مشخص برای استفاده.

---

## ۲. Pixabay Music (همان کلید ویدیو)

- **سایت موزیک:** https://pixabay.com/music  
- **API:** همان کلید Pixabay از https://pixabay.com/api/docs/  
- در کد از endpoint موزیک Pixabay استفاده می‌شود؛ اگر سرویس موزیک API را فعال کند، همان کلید کار می‌کند. در غیر این صورت موزیک از Jamendo یا fallback (SoundHelix) گرفته می‌شود.

---

## ۳. FreePD (دامنه عمومی، بدون API)

- **سایت:** https://freepd.com  
- موزیک‌ها Public Domain هستند؛ لینک دانلود مستقیم روی سایت هست.  
- برای اتوماسیون باید خودت لیست لینک‌های MP3 را در کد یا config بگذاری (الان پروژه از SoundHelix به‌صورت fallback استفاده می‌کند).

---

## ۴. SoundHelix (بدون API، لینک مستقیم)

- **سایت:** https://www.soundhelix.com  
- موزیک‌های نمونه رایگان با لینک مستقیم MP3.  
- در این پروژه به‌عنوان **fallback** وقتی Jamendo نباشد استفاده می‌شود.

---

## ۵. YouTube Audio Library (بدون API رسمی)

- موزیک رایگان برای ویدیو؛ فقط از طریق سایت یوتیوب و به‌صورت دستی.  
- برای دانلود خودکار API رسمی ندارد.

---

## خلاصه برای این پروژه

| منبع    | کلید/کار | استفاده در پروژه        |
|--------|-----------|---------------------------|
| Jamendo | ثبت‌نام → Client ID در `.env` | موزیک با جستجو (emotional, sad, epic و…) |
| Pixabay Music | همان کلید ویدیو از pixabay.com/api/docs | موزیک با جستجو (همان key)، هر بار متفاوت |
| SoundHelix | بدون کلید | Fallback موزیک (لینک ثابت) |

**توصیه:** برای **موزیک ترند و باکیفیت** حتماً **Jamendo** را در https://developer.jamendo.com ثبت کن و `JAMENDO_CLIENT_ID` را در `.env` بگذار. در `config/config.yaml` گزینهٔ `download.music_order: popularity_week_desc` باعث می‌شود موزیک‌های محبوب همین هفته (ترند) انتخاب شوند.
