# Statistika ko'ruvchi roli + Admin Mini App (vizual statistika)

## Maqsad
Faruh (admin emas) va boshqa ishonchli odamlar statistikani ko'ra olsin. Bot ichidagi `/admin`, `/stats`, `/export` va CSV ularga ham ochiladi. Bundan tashqari, alohida **Admin Mini App** qilinadi. Unda vizual statistika bo'ladi: jami foydalanuvchilar, yangilar, kunlik grafik, manbalar, "kim ariza yubordi" ro'yxati, foydalanuvchilar ro'yxati va CSV tugmalari. Ariza xabarlari avvalgidek faqat admin chatga boradi.

## Kontekst
- aiogram 3.13, long polling (`bot/bot.py:397`). aiohttp 3.10 aiogram bilan birga keladi, shuning uchun yangi paket kerak emas.
- Ruxsat 4 joyda tekshiriladi: `message.chat.id != settings.admin_chat_id` (`bot.py:264, 271, 289, 326`). Umumiy helper yo'q.
- `Settings` (`bot.py:56`): token, admin_chat_id, webapp_url, db_path. `load_settings` (`bot.py:90`).
- Storage (`bot/storage.py`): `count_users`, `count_lead_users`, `count_undelivered`, `user_rows_since`, `rows_since`, `export_csv`, `export_users_csv`.
- `bot/admin_panel.py`: `TASHKENT_TZ`, `LOOKBACK_DAYS`, `panel_keyboard()`, `build_overview/users/daily` (matn). `catalog.label` manba nomlari uchun.
- Mijoz Mini App'i (`webapp/`) Vercel'da turadi, unga tegilmaydi. Brend tokenlari `webapp/styles.css:1-17`, shriftlar `webapp/fonts/*.woff2`.
- Server: `/opt/quantum-bot`, systemd `quantum-bot`. `ufw` faqat SSH'ga ochiq, 80/443 bo'sh, Caddy va nginx yo'q (tekshirildi).
- Testlar: `python -m pytest` (~115 test), `node --test "webapp/tests/*.test.mjs"`.

## Arxitektura (qisqa)
- Bot jarayoni ichida aiohttp server `127.0.0.1:8090` da ishlaydi (`PANEL_URL` bo'sh bo'lsa ishga tushmaydi).
- Caddy `https://2-31-25-204.sslip.io` → `127.0.0.1:8090`, sertifikat avtomatik olinadi.
- `/admin/` — statik Mini App (`bot/admin_webapp/`). `/admin/api/dashboard` (GET) va `/admin/api/export` (POST) API'lari.
- Kirish Telegram `initData` orqali tekshiriladi. HMAC-SHA256: kalit = HMAC("WebAppData", BOT_TOKEN), solishtirish constant-time, `auth_date` 24 soatdan eski bo'lmasin. Keyin `user.id ∈ ruxsat ro'yxati` tekshiriladi. Parol yo'q.
- Ruxsat ro'yxati: `STATS_VIEWER_IDS` va `ADMIN_CHAT_ID` (u musbat, ya'ni shaxsiy chat bo'lsa).
- CSV fayl brauzerga yuklanmaydi. Bot uni so'ragan odamning shaxsiy chatiga hujjat qilib yuboradi.

## API kontrakti (frontend va backend shunga tayanadi)
- So'rov sarlavhasi: `Authorization: tma <initData>`.
- `GET /admin/api/dashboard` → `200 {generated_at, totals:{users, users_today, users_7d, users_30d, active_7d, lead_users, conversion_pct|null, leads_today, leads_7d, leads_30d, undelivered}, daily:[{date, users, leads}]x30, sources:[{key, label, users, leads}], leads:[{created_at, name, phone, tg_username, source_label, region, age, topics}] (oxirgi 200), users:[{first_seen_at, last_seen_at, tg_full_name, tg_username, source_label, has_lead}] (oxirgi 200)}`.
- `POST /admin/api/export` body `{"kind":"leads"|"users"}` → `200 {"ok":true}`. Bot faylni `send_document(user_id)` bilan yuboradi.
- Xatolar `{"error": "<code>"}` ko'rinishida: 401 `unauthorized` / `expired`, 403 `forbidden`, 400 `bad_request`, 429 `too_many` (bir odamga 10 soniyada bitta eksport), 502 `send_failed`, 500 `internal`.
- Har javobda: `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, CSP `default-src 'self'; script-src 'self' https://telegram.org; frame-ancestors https://web.telegram.org`.

## Chegaralar
- Qilinadi: ko'ruvchi roli (`STATS_VIEWER_IDS`); ko'ruvchi menyusida admin buyruqlari; Admin Mini App (`/admin` paneldagi tugma + ko'ruvchi chatidagi menyu tugmasi); API; Caddyfile namunasi; README.
- Qilinmaydi: login/parol, broadcast, ma'lumotni tahrirlash yoki o'chirish, ko'ruvchiga ariza xabarlari, mijoz Mini App'ini o'zgartirish, deploy va push (ularni siz qilasiz), ko'p admin chat.
- Tegilmaydi: `webapp/` (faqat shriftlarni o'qish), `leads.py`, `stats.py` mantig'i, ariza yetkazish (`_deliver`), `deploy/quantum-bot.service`.

## Qabul mezonlari
- [ ] `STATS_VIEWER_IDS` ("1, 2", bo'sh yoki yo'q) to'g'ri o'qiladi, noto'g'ri qiymatda `ConfigError` chiqadi — `pytest bot/tests/test_bot.py`
- [ ] Ko'ruvchi shaxsiy chatida `/admin`, `/stats`, `/export` va panel tugmalari ishlaydi. Ko'ruvchi ID'si guruhda yoki begona chatda hech narsa olmaydi — `pytest bot/tests/test_bot.py`
- [ ] Har ko'ruvchi chatida admin buyruqlar menyusi o'rnatiladi, birida xato bo'lsa boshqalari baribir o'rnatiladi — `pytest bot/tests/test_bot.py`
- [ ] initData: to'g'ri imzo qabul qilinadi. O'zgartirilgan maydon, `hash` yo'qligi, boshqa token, eski yoki kelajakdagi `auth_date`, buzuq `user` JSON rad etiladi — `pytest bot/tests/test_webapp_auth.py`
- [ ] Dashboard sonlari to'g'ri: Toshkent yarim tuni, 30 kunlik qator (bo'sh kunlar 0), 0 foydalanuvchida konversiya null, ro'yxat limiti 200 — `pytest bot/tests/test_dashboard.py`
- [ ] API 401, 403, 400 va 429 holatlarida ma'lumot bermaydi. To'g'ri foydalanuvchiga 200 qaytaradi. Eksport `send_document` ni so'ragan user_id bilan chaqiradi. Xavfsizlik sarlavhalari bor. `tests/` papkasi tashqariga berilmaydi — `pytest bot/tests/test_panel_server.py`
- [ ] Mini App holatlari: yuklanmoqda, ruxsat yo'q, muddati o'tgan ("qayta oching"), bo'sh ma'lumot, xato. Qidiruv ism, telefon va username bo'yicha ishlaydi. Shaxsiy ma'lumot `localStorage` ga yozilmaydi. HTML escape qilinadi — `node --test "bot/admin_webapp/tests/*.test.mjs"` + skrinshot ko'rigi
- [ ] Mini App tugmasi faqat shaxsiy chatda va `PANEL_URL` berilgan bo'lsa chiqadi. Guruh admin chatida inline panel avvalgidek ishlaydi — `pytest bot/tests/test_admin_panel.py bot/tests/test_bot.py`
- [ ] `PANEL_URL` bo'sh bo'lsa bot avvalgidek ishlaydi va server ishga tushmaydi — `pytest bot/tests/test_bot.py`
- [ ] To'liq suite yashil: `python -m pytest` va `node --test "webapp/tests/*.test.mjs" "bot/admin_webapp/tests/*.test.mjs"`

## Chekka holatlar
- Bo'sh baza, ya'ni 0 user va 0 ariza.
- `initData` bo'sh: Mini App Telegram'dan tashqarida ochilgan.
- 24 soatdan ortiq ochiq turgan oyna: `expired` → "qayta oching".
- CSV tugmasi ketma-ket bosilsa: 429.
- Ko'ruvchi botni hali `/start` qilmagan: `send_document` xato beradi → 502, foydalanuvchiga "avval botga /start yozing" chiqadi.
- Ismda `<script>` yoki `=cmd` bo'lsa: frontendda escape, CSV'da mavjud formula guard.
- Port 8090 band bo'lsa: log yoziladi, bot polling'i davom etadi.
- Telegram Web klienti (iframe) uchun: `frame-ancestors` ruxsat beradi.

## To'lqinlar

### To'lqin 1 (3 qadam parallel) — umumiy tekshiruv: `python -m pytest`
1. **Ko'ruvchi roli va sozlamalar** [XAVFLI — ruxsat] — `bot/bot.py`, `bot/tests/test_bot.py`, `bot/.env.example`
   - `Settings` ga `viewer_ids: frozenset[int] = frozenset()`, `panel_url: str = ""`, `panel_port: int = 8090` qo'shiladi (default qiymatlar bilan, shunda mavjud `Settings(...)` chaqiruvlari buzilmaydi). `PANEL_URL` faqat https, `PANEL_PORT` 1–65535.
   - `_can_view(chat)`: `chat.id == admin_chat_id` yoki (`chat.type == "private"` va `chat.id in viewer_ids`). 4 joyda shu helper ishlatiladi.
   - `setup_commands`: har bir viewer uchun `BotCommandScopeChat`, har biri alohida try va log bilan.
   - tekshiruv: `python -m pytest bot/tests/test_bot.py`
2. **initData tekshiruvi** [XAVFLI — auth] — `bot/webapp_auth.py`, `bot/tests/test_webapp_auth.py`
   - `validate_init_data(init_data, bot_token, now, max_age) -> dict` (user). Xatoda `InitDataError(code)` (`unauthorized`/`expired`). `hmac.compare_digest`. Magic number o'rniga konstanta.
   - tekshiruv: `python -m pytest bot/tests/test_webapp_auth.py`
3. **Dashboard ma'lumoti** — `bot/storage.py`, `bot/dashboard.py`, `bot/tests/test_dashboard.py`
   - Storage'ga `recent_leads(limit)` va `recent_users(limit)` qo'shiladi (`LIMIT` bilan, mavjud `_fetch_rows` pattern).
   - `build_dashboard(...) -> dict` API kontraktiga mos, JSON-safe. `admin_panel.TASHKENT_TZ`, `catalog.label` va storage'dagi telefon formatlash qayta ishlatiladi.
   - tekshiruv: `python -m pytest bot/tests/test_dashboard.py bot/tests/test_storage.py bot/tests/test_storage_users.py`

### Dizayn brifi (men, `/impeccable` skill bilan) — `docs/specs/admin-miniapp-design.md`
Brend tokenlari asosida layout, KPI plitkalari, grafik uslubi, ro'yxat, holatlar va mobil o'lchamlar belgilanadi. Kod yozilmaydi, faqat brif. 5-qadam shu brif bo'yicha bajariladi.

### To'lqin 2 (1-to'lqinga bog'liq, 3 qadam parallel) — umumiy tekshiruv: `python -m pytest` + `node --test "bot/admin_webapp/tests/*.test.mjs"`
4. **Panel HTTP serveri** [XAVFLI — auth, shaxsiy ma'lumot] — `bot/panel_server.py`, `bot/tests/test_panel_server.py`
   - `create_app(settings, storage, bot, clock)` va `start_panel(...) -> AppRunner` (`127.0.0.1`). Statik fayllar: `/admin/` ← `bot/admin_webapp/` (`tests/` dan tashqari), `/admin/fonts/` ← `webapp/fonts/`.
   - Kontrakt bo'yicha API, eksport cooldown, sarlavhalar. Logda shaxsiy ma'lumot yo'q.
   - Testlar `aiohttp.test_utils.TestServer/TestClient` bilan, yangi paket qo'shilmaydi.
   - tekshiruv: `python -m pytest bot/tests/test_panel_server.py`
5. **Admin Mini App frontend** — `bot/admin_webapp/index.html`, `app.js`, `format.js`, `styles.css`, `tests/format.test.mjs`, `tests/preview.html` (fixture bilan, faqat lokal ko'rish uchun)
   - Kirillcha UI, CDN'siz, grafik inline SVG. `render(data)` alohida qilinadi, shunda preview fixture bilan chizish mumkin.
   - tekshiruv: `node --test "bot/admin_webapp/tests/*.test.mjs"`
6. **Paneldagi Mini App tugmasi** — `bot/admin_panel.py`, `bot/texts.py`, `bot/tests/test_admin_panel.py`, `bot/tests/test_catalog.py`
   - `panel_keyboard(panel_url: str | None = None)`: url bo'lsa web_app tugmasi qo'shiladi. Matn kaliti cyr va lat'da.
   - tekshiruv: `python -m pytest bot/tests/test_admin_panel.py bot/tests/test_catalog.py`

### To'lqin 3 (2 qadam parallel) — umumiy tekshiruv: to'liq suite (ikkala buyruq)
7. **Botga ulash** [XAVFLI] — `bot/bot.py`, `bot/tests/test_bot.py`
   - `main()`: `panel_url` bo'lsa `start_panel`, `finally` da `runner.cleanup()`, port xatosi log qilinadi.
   - `/admin` da tugma faqat shaxsiy chatda chiqadi. Viewer chatlariga `set_chat_menu_button(MenuButtonWebApp)`.
   - tekshiruv: `python -m pytest bot/tests/test_bot.py`
8. **Deploy hujjatlari** — `README.md`, `deploy/Caddyfile`
   - Ko'ruvchi qo'shish, yangi `.env` kalitlari, Caddy o'rnatish, `ufw allow 80,443/tcp`, DB backup.
   - tekshiruv: qo'lda (Codex tekshiruvchi o'qiydi)

### To'lqin 4 — Vizual ko'rik
9. `tests/preview.html` ni brauzerda ochaman, telefon va desktop o'lchamida skrinshot olaman va `/impeccable` bilan tanqidiy ko'rib chiqaman. Kamchilik topilsa, 5-qadam fayllari bo'yicha bitta tuzatish qadami qilinadi.

## DB / migratsiya
Yo'q: faqat o'qish so'rovlari qo'shiladi. Sxema o'zgarmaydi.

## Foydalanuvchi bajaradigan ishlar
1. O'z Telegram ID'ingizni `@userinfobot` dan oling. Uni va ikkinchi odam ID'sini `bot/.env` ga `STATS_VIEWER_IDS=111,222` qilib yozing.
2. `ADMIN_CHAT_ID` da yana bitta ID qolishi kerak. Agar ikkita yozgan bo'lsangiz, bot ishga tushmaydi.
3. `.env` ga `PANEL_URL=https://2-31-25-204.sslip.io/admin/` qo'shing.
4. Deploy: "Hetznerga deploy qil" desangiz, men `hetzner-deploy` bo'yicha qilaman. U leads.db backup, Caddy o'rnatish, `ufw allow 80,443/tcp` va kodni nusxalashni o'z ichiga oladi. Serverdagi `.env` ni esa o'zingiz yangilaysiz.
5. Telegram'da ko'ruvchi bilan botga `/start` yozing, keyin menyudagi panel tugmasini oching.

## Xavflar
- Shaxsiy ma'lumot (ism, telefon) HTTPS orqali chiqadi. Himoya initData imzosi va ruxsat ro'yxati bilan; ikkalasi ham test bilan qoplanadi.
- Serverda yangi umumiy infratuzilma paydo bo'ladi: Caddy 80/443 portni egallaydi. Hozir bu portlarni boshqa servis ishlatmaydi. Keyin boshqa loyihalar ham shu Caddy orqali chiqishi kerak bo'ladi.
- sslip.io uchinchi tomon DNS xizmati. U ishlamay qolsa, panel ochilmaydi, bot esa ishlashda davom etadi. Keyinroq o'z domeningizga o'tish uchun faqat Caddyfile va `PANEL_URL` almashtiriladi.

## Mentor fikri
- Login va parolli web panel o'rniga Telegram initData ishlatiladi. Parolni o'g'irlash yoki taxmin qilish xavfi yo'q, sessiya va parol saqlash ham kerak emas.
- CSV brauzerga emas, chatga yuboriladi. Telegram Mini App ichida fayl yuklab olish klientlarda bir xil ishlamaydi, chatga yuborish esa ishonchli va izi qoladi.

## Taxminlar
- Mini App UI kirillchada bo'ladi (mavjud admin matnlari kabi).
- Ro'yxatlarda oxirgi 200 ta ariza va 200 ta foydalanuvchi ko'rsatiladi. Grafik 30 kunlik.
- initData 24 soat amal qiladi. Eksport cooldown 10 soniya. Port 8090.

## Ish tartibi
Har qabul qilingan qadam alohida commit qilinadi. Push qilinmaydi.
