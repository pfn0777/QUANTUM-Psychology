# Admin panel (Telegram) — foydalanuvchilar va statistika

## Maqsad
Admin (ADMIN_CHAT_ID) Telegram menyusidagi `/admin` orqali panel ochadi: botga nechta odam kirgani
(/start bosganlar), ulardan nechtasi ariza qoldirgani, kunlik dinamika, manbalar va CSV yuklab olish.
Hozir bot /start bosganlarni umuman saqlamaydi — faqat `leads` jadvali bor. Shuning uchun yangi `users` jadvali kerak.

## Kontekst
- aiogram 3 bot, long polling: `bot/bot.py` (BotHandlers, build_dispatcher, admin_commands, setup_commands).
- Saqlash: `bot/storage.py` (aiosqlite, `_write_lock`, `_utc_iso`, `_fetch_rows`, CSV formula guard `CSV_FORMULA_PREFIXES`).
- Mavjud arizalar statistikasi: `bot/stats.py::build_stats` (7/30 kun, kirillcha HTML) — qayta ishlatiladi.
- Matnlar: `bot/texts.py` (cyr/lat kalitlari bir xil bo'lishi `tests/test_catalog.py::EXPECTED_TEXT_KEYS` bilan tekshiriladi; emoji taqiqlangan).
- Deep link manbalari: `catalog.DEEP_LINK_SOURCES = ("ig","tg","yt")`, nomlari `catalog.SOURCES` + `catalog.label`.
- Testlar: `pytest` (pytest.ini, asyncio_mode=auto), bazaviy holat: 146 passed.
- Admin chat guruh bo'lishi mumkin — ruxsat mavjud pattern bo'yicha: `message.chat.id == settings.admin_chat_id`.

## Chegaralar
- Qilinadi: `users` jadvali + eski arizalardan tiklash; /start va Mini App arizasida foydalanuvchini yozish;
  `/admin` menyu buyrug'i + inline tugmali panel; foydalanuvchilar CSV; README bo'limi.
- Qilinmaydi: hammaga xabar yuborish (broadcast), botni bloklaganlarni aniqlash, web admin, ko'p admin, deploy, push.
- Tegilmaydi: `webapp/`, `leads.py` validatsiyasi, `stats.py` mantig'i, mavjud `/stats` va `/export` xatti-harakati.

## Panel tarkibi (kirillcha, mavjud admin matnlari kabi)
- Umumiy (asosiy xabar): jami foydalanuvchilar; yangi — bugun / 7 kun / 30 kun; faol (oxirgi 7 kunda kirgan);
  ariza qoldirganlar soni va konversiya % (0 foydalanuvchida «—»); arizalar — bugun / 7 / 30 kun; yetkazilmagan arizalar soni.
- Tugmalar: «Фойдаланувчилар» (manba bo'yicha 30 kun: ig/tg/yt/тўғридан-тўғри), «Аризалар» (`stats.build_stats`),
  «14 кунлик динамика» (kun: yangi user · ariza), «Аризалар CSV», «Фойдаланувчилар CSV», «Янгилаш».
- «Bugun» va kunlik dinamika Toshkent vaqtida: `timezone(timedelta(hours=5))` (tzdata'siz).

## Qabul mezonlari
- [ ] /start foydalanuvchini `users` ga yozadi; qayta /start dublikat yaratmaydi, `last_seen_at`, username, ism yangilanadi; birinchi manba saqlanib qoladi — `pytest bot/tests/test_storage_users.py`
- [ ] Bot startida (init) eski arizalardagi har bir `tg_user_id` bir marta `users` ga qo'shiladi (first_seen = eng birinchi ariza vaqti); init 2 marta chaqirilsa ham dublikat yo'q — `pytest bot/tests/test_storage_users.py`
- [ ] Foydalanuvchini yozishdagi DB xatosi /start javobini to'xtatmaydi (log qilinadi) — `pytest bot/tests/test_bot.py`
- [ ] Panel matnlari to'g'ri sanaydi: oraliq chegaralari, Toshkent yarim tuni, 0 holat, konversiya %, HTML escape — `pytest bot/tests/test_admin_panel.py`
- [ ] `/admin` va har bir tugma faqat admin chatda ishlaydi; boshqa chatdan kelgan callback hech narsa ko'rsatmaydi, lekin `callback.answer()` chaqiriladi — `pytest bot/tests/test_bot.py`
- [ ] Admin menyusi: /admin, /start, /stats, /export; oddiy user menyusi o'zgarmaydi — `pytest bot/tests/test_bot.py`
- [ ] Foydalanuvchilar CSV: BOM, sarlavha, formula guard (`=`, `+`, ... bilan boshlangan ism) — `pytest bot/tests/test_storage_users.py`
- [ ] To'liq suite yashil: `python -m pytest`

## Chekka holatlar
- Bo'sh baza (0 user, 0 ariza) — nolga bo'linish yo'q.
- `from_user` yo'q xabar — yozilmaydi, xato yo'q.
- Username yo'q / ismda `<b>` yoki `=cmd` — HTML escape va CSV guard.
- «Янгилаш» ikki marta bosilsa, matn o'zgarmagan — Telegram «message is not modified» xatosi log qilinadi, bot yiqilmaydi.
- Callback eski xabarda (`callback.message` None yoki inaccessible) — faqat `answer()`.
- Noma'lum `src` (deep link) — manba NULL ("тўғридан-тўғри").

## To'lqinlar
### To'lqin 1 (2 qadam parallel) — umumiy tekshiruv: `python -m pytest`
1. **Users storage** [XAVFLI — DB sxema] — fayllar: `bot/storage.py`, `bot/tests/test_storage_users.py` (yangi)
   - `users(tg_user_id INTEGER PRIMARY KEY, tg_username TEXT, tg_full_name TEXT NOT NULL, source TEXT, first_seen_at TEXT NOT NULL, last_seen_at TEXT NOT NULL)` + `idx_users_first_seen_at`.
   - init: `CREATE TABLE IF NOT EXISTS` + backfill `INSERT OR IGNORE ... SELECT ... FROM leads GROUP BY tg_user_id` (MIN/MAX created_at).
   - `upsert_user(tg_user_id, tg_username, tg_full_name, source, seen_at)` — `ON CONFLICT DO UPDATE`, `source = COALESCE(users.source, excluded.source)`.
   - O'qish: `user_counts`-ga kerakli xom ma'lumot (`users_since(since)` → first_seen_at, last_seen_at, source), `count_users()`, `count_lead_users()`, `count_undelivered()`, `export_users_csv()`. `_write_lock` va mavjud rollback patterni.
   - tekshiruv: `python -m pytest bot/tests/test_storage_users.py bot/tests/test_storage.py`
2. **Panel matn va klaviatura (pure)** — fayllar: `bot/admin_panel.py` (yangi), `bot/tests/test_admin_panel.py` (yangi)
   - Callback data konstantalari (`adm:overview`, `adm:users`, `adm:leads`, `adm:daily`, `adm:csv_leads`, `adm:csv_users`), `panel_keyboard()`.
   - `build_overview(...)`, `build_users(...)`, `build_daily(user_rows, lead_rows, now_utc, days=14)` — oddiy dict/int qabul qiladi, storage'ga tegmaydi (stats.py kabi).
   - tekshiruv: `python -m pytest bot/tests/test_admin_panel.py`

### To'lqin 2 (1-to'lqinga bog'liq, 2 qadam parallel) — umumiy tekshiruv: `python -m pytest`
3. **Botga ulash** [XAVFLI — ruxsat] — fayllar: `bot/bot.py`, `bot/texts.py`, `bot/tests/test_bot.py`, `bot/tests/test_catalog.py`
   - `start` va `web_app_data`da `upsert_user` (xato → log, javob davom etadi). `cmd_admin` matni; `admin_commands()` boshiga `/admin`.
   - `admin_panel` (Command("admin")) va `admin_callback` (`F.data.startswith("adm:")`), ruxsat tekshiruvi, edit_text yoki CSV document.
   - tekshiruv: `python -m pytest bot/tests/test_bot.py bot/tests/test_catalog.py`
4. **README** — fayl: `README.md` — admin panel bo'limi, `/admin`, yangi jadval va deploydan oldin DB backup eslatmasi.
   - tekshiruv: qo'lda (tekshiruvchi o'qiydi).

## DB / migratsiya
Bor: yangi `users` jadvali, `CREATE TABLE IF NOT EXISTS` bilan bot startida avtomatik yaratiladi + backfill.
Mavjud `leads` jadvaliga tegilmaydi. Qaytarish: eski kodni qaytarish yetarli (eski kod `users` jadvalini e'tiborsiz qoldiradi);
kerak bo'lsa `DROP TABLE users`. Prod'da deploydan oldin `leads.db` nusxasi olinadi (foydalanuvchi).

## Foydalanuvchi bajaradigan ishlar
- Deploy (o'zingiz so'raganda) — oldin serverdagi `leads.db` nusxasini olish.
- Deploydan keyin Telegram'da admin chatda menyuni ochib `/admin` ni tekshirish.

## Xavflar
- Shaxsiy ma'lumot (users CSV) — faqat admin chat; formula guard.
- Ariza qoldirmay ketgan eski foydalanuvchilarni tiklab bo'lmaydi — ular keyingi /start'da qo'shiladi.

## Mentor fikri
- "Ro'yxatdan o'tganlar" sonini hozirgi kod bilan bilib bo'lmaydi: `bot/bot.py:151` `start` hech narsa saqlamaydi. Yangi jadval — yagona to'g'ri yo'l.
- Broadcast (hammaga xabar) foydali, lekin spam va Telegram limitlari xavfi bor — alohida vazifa sifatida.

## Taxminlar
- Panel matnlari kirillcha (mavjud /stats kabi).
- Admin o'zi /start bossa, u ham foydalanuvchi sifatida sanaladi (1–2 ta farq).
- "Faol" = oxirgi 7 kunda /start bosgan yoki ariza qoldirgan.
- Kunlik dinamika 14 kun.
