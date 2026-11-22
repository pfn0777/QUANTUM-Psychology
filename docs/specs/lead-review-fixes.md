# Code-review: 5 ta jiddiy xatoni tuzatish (lead oqimi)

## Maqsad
Mijoz arizalari (lead) yo'qolmasin, telefon raqam to'g'ri va ishlatsa bo'ladigan holda saqlansin. Admin esa to'g'ri vaqtni va toza CSV'ni olsin.
Foyda oladiganlar: mijoz (ariza yetib boradi, chet el raqami ham ishlaydi) va admin (to'g'ri raqam, vaqt va eksport).

## Kontekst
- Bot: aiogram, `bot/bot.py` (handlers, `main`), `bot/leads.py` (`_valid_phone`, `render_admin`), `bot/storage.py` (SQLite aiosqlite, `export_csv`), `bot/catalog.py` (`PHONE_MIN_DIGITS=9`, `PHONE_MAX_DIGITS=15`).
- Webapp: `webapp/app.js` (`formatPhone`, 200-qator), `webapp/validate.js` (`normalizePhone`, `validateLead`).
- Testlar: `python -m pytest` (126 ta o'tyapti), `node --test tests/*.test.mjs` (`webapp/` ichida, 40 ta o'tyapti).
- DB: sxema o'zgarmaydi.
- Commit qilinmagan fayllar (`docs/mentor/promo-*`, `docs/specs/promo-*`, `video uchun music/`, `video/...`) foydalanuvchiniki. Ularga tegilmaydi, commitga qo'shilmaydi.

## Foydalanuvchi qarorlari
- Chet el raqami ruxsat etiladi: mijoz `+998` ni o'chirib, boshqa kod bilan yozsa, raqam o'zgarmaydi (15 raqamgacha). O'zbekiston raqami aniq 12 raqam bo'lishi shart.
- CSV'da telefon `998 90 123 45 67` ko'rinishida chiqadi: `+` ham, `'` ham yo'q. Sabab: Excel/Sheets `+` bilan boshlangan katakni formula deb o'qiydi (qayta so'ralgan qaror).

## Telefon qoidasi (bot va webapp'da bir xil)
- `+998...` → aniq 12 raqam → `+998XXXXXXXXX`, aks holda rad etiladi.
- `+<boshqa kod>...` → 9–15 raqam → `+<raqamlar>`.
- `+` siz 9 raqam → O'zbekiston milliy raqami → `+998` + raqamlar.
- `+` siz, `998` bilan boshlanadigan 12 raqam → `+998...`.
- `+` siz boshqa har qanday holat → rad etiladi.

## Chegaralar
- Qilinadi: code-review'dagi 5 ta jiddiy topilma va har biriga regressiya testi.
- Qilinmaydi: 5 ta mayda topilma (thanks tartibi, lock'lar tozalanishi, src saqlash, retry limit, success panel matni), `.playwright-mcp/` tozalash, push yoki deploy, UI matnini o'zgartirish.
- Tegilmaydi: `deploy/`, `.env*`, `video/`, `docs/` (holat va spec fayllaridan tashqari), DB sxemasi.

## Qabul mezonlari
- [ ] Bot `drop_pending_updates` siz ishga tushadi: navbatda kutib qolgan `web_app_data` qayta ishlanadi. Tekshiruv: test `main`/polling chaqiruvida `drop_pending_updates` yo'qligini tasdiqlaydi.
- [ ] Admin xabaridagi "Вақт" `created_at` dan olinadi, retry yo'lida ham. Tekshiruv: 10:00 da yaratilgan, 15:00 da yuborilgan lead'da 10:00 (Toshkent vaqti) chiqishini ko'rsatadigan test.
- [ ] `+998 90 123 4` botda ham, `validateLead` da ham rad etiladi. `+998901234567` va `+79123456789` qabul qilinadi. Tekshiruv: pytest + node test.
- [ ] `formatPhone("+7 912 345 67 89")` → `+79123456789`, o'zgarmaydi. `formatPhone("998887766")` → `+998 99 888 77 66`. `+998` ni yozish odatdagidek formatlanadi. Tekshiruv: node test (`formatPhone` test qilish uchun `validate.js` ga ko'chiriladi).
- [ ] CSV'da O'zbekiston raqami `998 90 123 45 67` ko'rinishida, `+` va `'` siz. Ism yoki izoh `=` bilan boshlansa, `'` himoyasi saqlanadi. Tekshiruv: pytest.
- [ ] Barcha eski testlar o'tadi: pytest kamida 126 ta, node kamida 40 ta va yangi testlar.

## Chekka holatlar
- Bo'sh maydon yoki faqat `+` → avvalgidek ishlaydi.
- `+9` yoki `+99` deb yozish (998 ning boshlanishi) → avvalgidek qisman `+99` ko'rinadi.
- `+90...` (Turkiya) → chet el raqami sifatida qoladi.
- Bazadagi eski raqamlar ham CSV'da yangi formatda chiqadi, chunki formatlash eksport paytida qilinadi.
- Chet el raqami CSV'da `+` bilan boshlanadi. Uning formula himoyasi (`'`) saqlanadi, bu kamdan-kam holat.
- Restartdan keyin eski `/start` xabarlariga ham javob boriladi, bu zararsiz.

## Qadamlar
1. Bot: pending update'larni saqlash va admin vaqtini `created_at` dan olish. Fayllar: `bot/bot.py`, `bot/tests/test_bot.py`. Retry yo'lida `created_at` ISO matn bo'lib keladi, `datetime.fromisoformat` bilan o'qiladi. Tekshiruv: `python -m pytest`.
2. Telefon validatsiyasi (bot va webapp, bitta qoida). Fayllar: `bot/leads.py`, `webapp/validate.js`, `bot/tests/test_leads.py` + `webapp/tests/validate.test.mjs`. Tekshiruv: pytest + node.
3. Webapp telefon maydoni. `formatPhone` `validate.js` ga export qilib ko'chiriladi, `app.js` uni import qiladi. Fayllar: `webapp/app.js`, `webapp/validate.js`, `webapp/tests/validate.test.mjs`. Tekshiruv: node test va brauzerda qo'lda (Playwright): `+7...` va `998887766` kiritib ko'rish.
4. CSV telefon formati. Fayllar: `bot/storage.py`, `bot/tests/test_storage.py`. Tekshiruv: pytest.

Har qadam: ishchi → tekshiruvchi → QABUL bo'lsa alohida commit (`fix:`). Push qilinmaydi.

## DB / migratsiya: yo'q

## Foydalanuvchi bajaradigan ishlar
- Tugagach: botni Hetzner'ga deploy qilish ("Hetznerga deploy qil" deb aytasiz) va webapp'ni Vercel'ga chiqarish. Tartib muhim emas, eski va yangi versiyalar bir-biriga mos.
- Telefonda tekshirish: formada `+7` raqam kiritish va ariza yuborish.

## Xavflar
- Telefon qoidasi qattiqroq bo'ladi: avval o'tgan chala O'zbekiston raqamlari endi rad etiladi. Bu maqsadning o'zi.
- `drop_pending_updates` olib tashlansa, uzoq to'xtashdan keyin to'plangan xabarlar birdan keladi. Cooldown va lock buni ko'taradi.

## Taxminlar
- "Вақт" faqat ariza yaratilgan vaqtni ko'rsatadi, "kechikdi" degan qo'shimcha belgi qo'shilmaydi.
- Chet el raqami formada guruhlanmaydi (`+79123456789`), chunki mamlakat kodining uzunligi har xil.
