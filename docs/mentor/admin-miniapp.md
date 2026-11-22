# Statistika ko'ruvchi roli + Admin Mini App
Holat: JARAYONDA
Ijrochi: codex
Turi: ISH · Hajm: XAVFLI (auth, shaxsiy ma'lumot, yangi HTTP server)
Spec: docs/specs/admin-miniapp.md
Boshlangan: 2026-11-22

## Karta
Maqsad: STATS_VIEWER_IDS dagi odamlar /admin, /stats, /export, CSV va vizual Admin Mini App'ni ko'radi; ariza xabarlari faqat admin chatga.
Qilinmaydi: login/parol, broadcast, tahrirlash/o'chirish, ko'ruvchiga ariza xabari, webapp/ o'zgarishi, deploy, push.
Qabul mezonlari: spec'dagi 10 band; `python -m pytest` + node testlar yashil.

## To'lqinlar
### To'lqin 1 — TUGADI (pytest 281 passed)
- [x] 1. Ko'ruvchi roli va sozlamalar [XAVFLI] (commit ef57a22, 3-urinishda; qolgan 2 PANEL_URL chekka holati mentor qarori bilan keyinga — "Kichik topilmalar"; ruxsat diffini mentor o'qidi)
- [x] 2. initData tekshiruvi [XAVFLI] (commit 9b3c707)
- [x] 3. Dashboard ma'lumoti (commit 5c7d368)
### Dizayn brifi (mentor, /impeccable) — docs/specs/admin-miniapp-design.md
- [x] brif (yozildi; PRODUCT.md yo'q — taxminlar brifda belgilangan; 3 tab: Умумий/Аризалар/Фойдаланувчилар)
### To'lqin 2 ← HOZIR SHU
- [ ] 4. Panel HTTP serveri [XAVFLI]
- [ ] 5. Admin Mini App frontend
- [ ] 6. Paneldagi Mini App tugmasi (tugma matnlari admin_panel.py da hardcoded — texts.py/test_catalog kerak emas)
### To'lqin 3
- [ ] 7. Botga ulash [XAVFLI]
- [ ] 8. README + deploy/Caddyfile
### To'lqin 4
- [ ] 9. Vizual ko'rik (/impeccable)

## Qarorlar
- Manzil: https://2-31-25-204.sslip.io/admin/ (foydalanuvchi tanlovi), Caddy reverse proxy -> 127.0.0.1:8090.
- Mini App'da mijoz ma'lumoti to'liq (ism, telefon, username) — foydalanuvchi tanlovi.
- Ko'ruvchi ariza xabarlarini olmaydi — foydalanuvchi tanlovi.
- Kirish: STATS_VIEWER_IDS + ADMIN_CHAT_ID (musbat bo'lsa) — foydalanuvchi tanlovi.
- Auth: Telegram initData HMAC (parol yo'q) — mentor tavsiyasi, foydalanuvchi parolli panel so'ragan edi, tasdiqlandi.
- CSV chatga send_document bilan yuboriladi.

## Kichik topilmalar (keyinroq)
- PANEL_URL: oxirida nuqtali host (`panel.example.org.`) rad etiladi; `https://[2001:db8::1]junk` qabul qilinadi (bot.py ~109/151). Operator config, xavf past.
- webapp_auth: tz-siz `now` TypeError; bo'sh/str bo'lmagan token aniq xato bermaydi; noto'g'ri UTF-8 replacement bilan dekodlanadi.
- dashboard: zonasiz now_utc mahalliy vaqt deb olinadi (ValueError tavsiya).
- bot/tests/test_bot.py 800 qatorga yetdi — bo'lish taklif qilinadi.
- Muhit: `python -m pytest` RTK orqali "No tests collected" ko'rsatishi mumkin — `rtk proxy python -m pytest` ishlatilsin.

## Foydalanuvchi vazifalari
- [ ] bot/.env: ADMIN_CHAT_ID da bitta ID qoldirish; STATS_VIEWER_IDS=...; PANEL_URL=https://2-31-25-204.sslip.io/admin/
- [ ] Deploy so'rash ("Hetznerga deploy qil"): leads.db backup, Caddy, ufw 80/443, serverdagi .env ni o'zi yangilaydi.
- [ ] Telegram'da tekshirish.

## Keyingi sessiya uchun eslatma
- Ish daraxti boshlanishda toza edi (HEAD f36a601).
