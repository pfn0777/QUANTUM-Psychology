# Vercel deploy: Python detection fix
Holat: TUGADI
Ijrochi: codex
Turi: XATO · Hajm: KICHIK
Spec: yo'q
Boshlangan: 2026-11-21

## Karta
Maqsad: Vercel `webapp/` ni statik sayt sifatida deploy qilsin (PYTHON_ENTRYPOINT_NOT_FOUND yo'qolsin).
Sabab: vercel.json da framework yo'q → Vercel repodagi bot/*.py, requirements.txt, pytest.ini ni ko'rib Python preset tanlagan.
Qilinmaydi: bot/webapp kodi, Hetzner deploy, Vercel dashboard sozlamalari.
Qabul mezonlari: vercel.json valid JSON, framework/buildCommand/installCommand = null; .vercelignore bot/, scripts/, deploy/, docs/, pytest.ini ni chiqaradi; `node --test webapp/tests` o'tadi.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. vercel.json + .vercelignore (commit a4448c0, 1-urinishda; webapp testlari 35/35)

## Kichik topilmalar (keyinroq)
- `node --test webapp/tests` (papka) Node 26 da MODULE_NOT_FOUND beradi; `node --test webapp/tests/*.test.mjs` ishlaydi. README/hujjatlarda shu buyruq bo'lsa yangilash kerak.

## Qarorlar
- Vercel MCP loyihani ko'rmadi; dashboard preset tekshirilmadi. vercel.json framework override ishlatiladi.

## Tahlil 2 (2026-11-21, push'dan keyin)
- 7c5a0d9 deploy: Ready, lekin sayt 404. Build log: "Build output contains no functions/static/services". Output: faqat middleware.
- Sabab: dashboard'da Framework Preset = Python. vercel.json dagi `"framework": null` Vercel CLI 66 da "o'rnatilmagan" deb o'qiladi va dashboard preset'i (Python) ishlaydi; Python preset outputDirectory'ni e'tiborsiz qoldiradi. Bot fayllari .vercelignore bilan chiqarilgani uchun endi yiqilmaydi, lekin bo'sh chiqadi.
- Yechim: dashboard → Framework Preset = Other (foydalanuvchi qiladi). Kod o'zgarishi kerak emas.

## Foydalanuvchi vazifalari
- [x] Framework Preset: Python → Other (mentor Chrome orqali, foydalanuvchi ruxsati bilan, saqlandi)
- [ ] Oxirgi deploy'ni (7c5a0d9) Redeploy qilish va saytni tekshirish
- [ ] git push → Vercel build logini tekshirish
- [ ] Baribir yiqilsa: Settings → Build and Deployment → Framework Preset → Other
