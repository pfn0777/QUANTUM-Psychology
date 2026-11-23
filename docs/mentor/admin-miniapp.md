# Statistika ko'ruvchi roli + Admin Mini App
Holat: TUGADI (2026-11-23)
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
### To'lqin 2 — TUGADI (pytest 343 passed, node 68 pass)
- [x] 4. Panel HTTP serveri [XAVFLI] (commit 8b2d020, 3/3 urinish; panel_server.py ni mentor to'liq o'qidi: auth, allowlist, log, statik yo'l, 127.0.0.1 — maqbul. Qolgan 3 ta [O'RTA] → 4b)
- [x] 5. Admin Mini App frontend (commit d6f46cc, 3/3 urinish; qolgan 1 ta [O'RTA] → 5b; 320px brauzer ko'rigi → 9)
- [x] 6. Paneldagi Mini App tugmasi (commit c3068f0, 1-urinishda, 13 passed)
### To'lqin 3 — TUGADI (pytest 372 passed, node 68 pass)
- [x] 7. Botga ulash [XAVFLI] (commit 0493e5e, 1-urinishda, 100 passed; mentor diffni o'qidi)
- [x] 4b. Panel server qoldiqlari [XAVFLI] (commit ae1b72f, 3/3 urinish, 77 passed; (a)(b)(c) yopildi; qolgan 3 ta [O'RTA] faqat auth'dan o'tgan ko'ruvchi yo'lida → "Kichik topilmalar")
- [x] 5b. Manbalar qatori (commit b482c49, 1-urinishda, node 12 pass)
### To'lqin 4 — TUGADI (pytest 376 passed, node 68 pass)
- [x] 8. README + deploy/Caddyfile (1-urinishda; mentor diffni o'qidi: DB yo'li kodga mos, Caddy faqat /admin, sir yo'q; caddy lokal yo'q — validate serverda)
- [x] 7b. Yopilish tartibi (1-urinishda, 104 passed; `_shutdown` helper, close_bot_session=False)
- [x] 9. Vizual ko'rik (mentor, 2026-11-23): 360×640 va 1024×768 (full), 320×640 mobil emulyatsiya; holatlar full/empty/expired/error va 3 tab. 320px da gorizontal siljish yo'q (scrollWidth=320), tablar 44px balandlik, `<script>` ismi matn sifatida, noto'g'ri username havolasiz. Bloklovchi kamchilik yo'q → tuzatish qadami kerak emas. Mayda: 320px da "Янгиланди 14:05" ikki qatorga bo'linadi.

### To'lqin 5 — deploy tuzatishi (2026-11-23)
- [x] 10. aiohttp 3.12+ moslik: 100-continue `send_headers()`; log nomi testi (1-urinishda; lokal 376 passed, serverda aiohttp 3.14.5 bilan 375 passed + 1 skipped (Node yo'q)) (commit 785d227)
### Deploy (2026-11-23)
- Caddy v2.11.9 o'rnatildi, sertifikat olindi, ufw 80/443 ochildi; kod /opt/quantum-bot ga, leads.db.bak-20261123-0625; quantum-bot active, NRestarts=0; boshqa 11 servis active.
- Foydalanuvchi serverdagi .env ga PANEL_URL va STATS_VIEWER_IDS qo'shdi; restartdan keyin panel 127.0.0.1:8090 da, /admin/ 200 + CSP, API kirishsiz 401, /admin/tests/ 404.
- Telegram'da foydalanuvchi tekshirdi (2026-11-23): ko'ruvchi /admin, Mini App, CSV, admin guruh — hammasi ishladi.

## Qarorlar
- (2026-11-23) Qadam 4 va 5 3/3 urinishda tugadi: testlar yashil, qolgan topilmalar tor va aniq → joriy holat commit qilindi, qoldiqlar 4b/5b qadamlariga bo'lindi (skill qoidasi: bir marta bo'lish).
- (2026-11-23) Qadam 7: web_app tugmasi faqat `chat.type == "private"` da (Telegram guruhda web_app inline tugmani rad etadi). Panel server porti band bo'lsa (OSError) — log, polling davom etadi.
- (2026-11-23) Qadam 4, 3-urinish uchun mentor qarorlari: sarlavhalar `on_response_prepare` orqali; har qanday 5xx → {"error":"internal"} + faqat tur nomi logda; ClientError/ClientDecodeError → 502; statik fayl faqat static_dir ildizidagi .html/.js/.css; start_panel faqat 127.0.0.1.
- (2026-11-23) Qadam 5: grafikdagi har kun uchun alohida nishon o'rniga butun grafik bitta interaktiv zona (pointer x → eng yaqin kun, ←/→ klaviatura, tanlangan kun izohda). Sabab: 320px da 30 kun = <10px, nishon minimumi bajarilmaydi.
- Manzil: https://2-31-25-204.sslip.io/admin/ (foydalanuvchi tanlovi), Caddy reverse proxy -> 127.0.0.1:8090.
- Mini App'da mijoz ma'lumoti to'liq (ism, telefon, username) — foydalanuvchi tanlovi.
- Ko'ruvchi ariza xabarlarini olmaydi — foydalanuvchi tanlovi.
- Kirish: STATS_VIEWER_IDS + ADMIN_CHAT_ID (musbat bo'lsa) — foydalanuvchi tanlovi.
- Auth: Telegram initData HMAC (parol yo'q) — mentor tavsiyasi, foydalanuvchi parolli panel so'ragan edi, tasdiqlandi.
- CSV chatga send_document bilan yuboriladi.

## Kichik topilmalar (keyinroq)
- panel_server (4b qoldig'i, mentor qarori bilan qabul — hammasi faqat initData+allowlist'dan o'tgan ko'ruvchi uchun): chunked eksportga 100-continue hajm tekshiruvisiz; mijoz tanani yarim yopsa yakuniy 400 kelmaydi; `request.read()` da timeout yo'q. Yechim kerak bo'lsa: chunked → 411, `asyncio.timeout`, EOF → 400.
- test_panel_server.py:381 — test aiohttp ichki parseriga bog'langan.
- Mini App: 320px da "Янгиланди 14:05" ikki qatorga bo'linadi (`white-space: nowrap` yetadi).
- Manba konversiyasi leads/users — bir odam bir nechta ariza qoldirsa 100% dan oshishi mumkin (brif shunday).
- `.codex/config.toml` (untracked) — /codex skill yaratgan Codex sozlamasi; commit qilinmaydi, foydalanuvchi qaror qiladi.
- PANEL_URL: oxirida nuqtali host (`panel.example.org.`) rad etiladi; `https://[2001:db8::1]junk` qabul qilinadi (bot.py ~109/151). Operator config, xavf past.
- webapp_auth: tz-siz `now` TypeError; bo'sh/str bo'lmagan token aniq xato bermaydi; noto'g'ri UTF-8 replacement bilan dekodlanadi.
- dashboard: zonasiz now_utc mahalliy vaqt deb olinadi (ValueError tavsiya).
- bot/tests/test_bot.py 800 qatorga yetdi — bo'lish taklif qilinadi.
- Muhit: `python -m pytest` RTK orqali "No tests collected" ko'rsatishi mumkin — `rtk proxy python -m pytest` ishlatilsin.

## Foydalanuvchi vazifalari
- [x] bot/.env: ADMIN_CHAT_ID da bitta ID qoldirish; STATS_VIEWER_IDS=...; PANEL_URL=https://2-31-25-204.sslip.io/admin/
- [x] Deploy so'rash ("Hetznerga deploy qil"): leads.db backup, Caddy, ufw 80/443, serverdagi .env ni o'zi yangiladi.
- [x] Telegram'da tekshirish.

## Keyingi sessiya uchun eslatma
- OCHIQ: `C:\Users\user\.claude\skills\hetzner-deploy\SKILL.md` ga yozish (mentor-rejim hook blokladi):
  1) "`ufw` is on and allows **only OpenSSH**." → "`ufw` is on and allows OpenSSH + 80/tcp + 443/tcp (80/443 opened 2026-11-23 for Caddy)."
  2) "Shared infra" paragrafiga: Caddy (2026-11-23, apt cloudsmith caddy-stable, unit `caddy`) 80/443 ni egallaydi, auto HTTPS; `/etc/caddy/Caddyfile` = quantum-bot `deploy/Caddyfile` (`2-31-25-204.sslip.io`, `/admin*` → 127.0.0.1:8090, qolgani 404); yangi web loyiha — faqat sayt bloki QO'SHILADI, ustidan yozilmaydi; `caddy validate` → `systemctl reload caddy`; asl fayl `Caddyfile.default-bak`. quantum-bot deploy: `git ls-files bot deploy pytest.ini webapp/fonts` → stage, `/opt/quantum-bot/.venv` bilan pytest, stop, `bot/data/leads.db` backup, nusxa, `root:quantum-bot` 640/750 (`bot/data` dan tashqari), start.
- Ish daraxti boshlanishda toza edi (HEAD f36a601).
- To'lqin 2: sessiya uzildi; diskda uchala qadam fayllari bor (commit qilinmagan). Boshqaruvchi qayta ulandi — tekshirib, chalasini tugatadi.
- Foydalanuvchi bot/.env ga STATS_VIEWER_IDS qo'shdi (1 ta, load_settings OK); PANEL_URL hali bo'sh.
