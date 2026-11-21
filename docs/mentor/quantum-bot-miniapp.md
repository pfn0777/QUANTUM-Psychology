# QUANTUM Psychology — Telegram bot + Mini App
Holat: TUGADI
Ijrochi: codex
Turi: ISH · Hajm: XAVFLI (shaxsiy ma'lumot)
Spec: docs/specs/quantum-bot-miniapp.md
Reja: C:\Users\user\.claude\plans\shiny-toasting-sphinx.md
Boshlangan: 2026-11-20

## Karta
Maqsad: mijoz mini app'da 12 modulni ko'radi va bepul suhbatga ariza qoldiradi; ariza SQLite + admin chatga; admin qo'ng'iroq qiladi. Manba (deep link) va demografiya `/stats` da.
Qilinmaydi: to'lov/narx, rus tili, kabinet, web admin, AI rasm, deploy.
Qabul mezonlari: spec §11 + reja ro'yxati. Python: `py -3.11 -m pytest -q`; JS: `node --test webapp/tests/`.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. Infra (commit 5be7b3a; pip install mentor tomonidan, pytest 1/1)
- [x] 2. Brend assetlari (commit bc31653, 3-urinishda; 3 SVG, 9 variable woff2 subset)
### To'lqin 2 — TUGADI
- [x] 3. catalog.py + texts.py (commit 51f90a1, 13 test)
- [x] 4. data.js + i18n.js (commit 409dd9d, 3-urinishda; lotin namunasi ko'rildi — to'g'ri)
- [x] 5. storage.py [XAVFLI] (commit 18938e8, 2-urinishda, 7 test)
### To'lqin 3 — TUGADI (pytest 105, node 35)
- [x] 6. leads.py [XAVFLI] (commit d028dc2, 3-urinishda, 67 test; NaN/takroriy kalit/bidi/yangi qator himoyasi)
- [x] 7. stats.py + storage tuzatish (commit 33184ca, 1-urinishda, 23 test)
- [x] 8. validate.js + catalog sync test (commit 6a8f97d, 3-urinishda, 30 JS + 1 sync)
### To'lqin 4 — TUGADI (pytest 122, node 35; env: BOT_TOKEN, ADMIN_CHAT_ID, WEBAPP_URL, DB_PATH)
- [x] 9. bot.py [XAVFLI] (commit af7e0ce, 3-urinishda, 17 test; retry dublikat poygasi tuzatildi)
- [x] 10. Mini app UI (commit 10e95b1, 3-urinishda; telefon maskasi tuzatildi; qo'lda 390×844: skroll yo'q, lotin to'liq, src=ig yashirildi, mavzu→modul ajratish ishlaydi)
- [x] 11. Deploy + README (commit 6b8bfea, 2-urinishda)

## Qarorlar
- Foydalanuvchi tanlovi: kirill + lotin tugmasi. Mentor tavsiyasi: faqat kirill, sabab: ikki baravar matn va tarjima xatosi xavfi. Qaror foydalanuvchiniki (did/biznes).
- Narx ko'rsatilmaydi; taklif — bepul dastlabki suhbat.
- Saqlash: admin chat + SQLite + `/export` CSV.
- Payload'da ro'yxatlar kod ko'rinishida.
- Python `py -3.11` bilan ishlatiladi (default `python` boshqa versiya bo'lishi mumkin).
- Foydalanuvchi fayllari `.gitignore` ga qo'shiladi (tasodifan commit bo'lmasligi uchun).

## Kichik topilmalar (keyinroq)
- Codex sandbox'da `py -3.11` yo'q ("No installed Python found!"). Python tekshiruvlarini boshqaruvchi o'zi yuritadi, ishchi emas.
- pytest-asyncio: `asyncio_default_fixture_loop_scope` ogohlantirishi — pytest.ini'ga `= function` qo'shish (2-to'lqinda).
- pip: mcp 1.23.3 pydantic>=2.11 talab qiladi, o'rnatilgani 2.9.2 (aiogram 3.13 cheklovi, oldindan bor edi).
- Git: LF→CRLF ogohlantirishi; `.gitattributes` qo'shish mumkin.
- Node v26: `node --test webapp/tests/` ishlamaydi → `node --test "webapp/tests/*.test.mjs"` ishlatiladi.
- validate.js izohdagi yakka surrogatda `errors.comment = "invalid_payload"` qaytaradi — app.js (qadam 10) bu kalitni i18n orqali ko'rsatishi kerak.
- Eski Codex job task-mwoyrxau-oxt7i3 (read-only tekshiruvchi) hali "running" ko'rinadi — zararsiz.
- bot.py fallback F.text admin guruhida ham javob beradi (privacy mode yoqilgan bo'lsa muammo emas).
- `.gitattributes` (`*.service text eol=lf`) — serverga CRLF bilan ketmasligi uchun.
- `.playwright-mcp/` (qo'lda tekshiruv skrinshotlari) untracked — .gitignore'ga qo'shish yoki o'chirish foydalanuvchi qarori.
- test_catalog.py:152 emoji tekshiruvi ba'zi BMP emoji'ni qamramaydi (KICHIK).

## Foydalanuvchi vazifalari
- [ ] BotFather token → `bot/.env` (o'zi)
- [ ] ADMIN_CHAT_ID
- [ ] Vercel deploy, WEBAPP_URL
- [ ] Server deploy
- [ ] Deep link havolalarini bio/kanal/YouTube'ga qo'yish
- [ ] Rozilik matni, lotin tarjima, mavzu→modul jadvalini tasdiqlash
- [ ] Shaxsiy ma'lumot joylashuvi (O'zbekiston serveri) bo'yicha qaror

## Keyingi sessiya uchun eslatma
- To'lqin 1–3 tugadi (oxirgi commit 6a8f97d). Navbat: To'lqin 4 (qadam 9 bot.py [XAVFLI], 10 UI, 11 deploy+README), uchalasi parallel, fayllar kesishmaydi.
- Boshqaruvchi topshirig'iga yana yoz: Codex'da Python yo'q (pytest'ni boshqaruvchi yuritadi); JS: `node --test "webapp/tests/*.test.mjs"`; `cx.mjs` Bash'dan.
- 10-qadam: 390×844 da qo'lda tekshiruv; kontakt telefon/@handle app'ga qo'yilmaydi.
