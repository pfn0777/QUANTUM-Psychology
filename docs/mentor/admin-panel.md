# Admin panel (Telegram)
Holat: TUGADI (2026-11-22, pytest 219 passed)
Ijrochi: codex
Turi: ISH · Hajm: XAVFLI (DB sxema, ruxsat)
Spec: docs/specs/admin-panel.md
Boshlangan: 2026-11-22

## Karta
Maqsad: admin chatda /admin -> panel: foydalanuvchilar soni (/start bosganlar), yangi (bugun/7/30), faol, konversiya, arizalar, 14 kunlik dinamika, manbalar, arizalar CSV + foydalanuvchilar CSV.
Qilinmaydi: broadcast, bloklaganlarni aniqlash, web admin, ko'p admin, deploy, push.
Qabul mezonlari: spec'dagi 8 band; to'liq `python -m pytest` yashil (bazaviy 146 passed).

## To'lqinlar
### To'lqin 1 — TUGADI (pytest 185 passed)
- [x] 1. Users storage — bot/storage.py, bot/tests/test_storage_users.py [XAVFLI] (commit 3a6d4ed, 3-urinishda)
- [x] 2. Panel matn/klaviatura — bot/admin_panel.py, bot/tests/test_admin_panel.py (commit 71b6f11)
### To'lqin 2 — TUGADI (pytest 219 passed)
- [x] 3. Botga ulash — bot/bot.py, bot/texts.py, bot/tests/test_bot.py, bot/tests/test_catalog.py [XAVFLI] (commit 575e578, 3-urinishda; oxirgi xavfsizlik tuzatishini mentor diff orqali tekshirdi)
- [x] 4. README (commit 5d546a1, 2-urinishda)

## Qarorlar
- "Ro'yxatdan o'tgan" = /start bosgan har kim (foydalanuvchi tanlovi).
- Eski foydalanuvchilar arizalardan tiklanadi (foydalanuvchi tanlovi).
- Ko'rinish: menyuda /admin + inline tugmali panel (foydalanuvchi tanlovi).
- Foydalanuvchilar CSV — faqat admin chatda (foydalanuvchi tanlovi).
- Vaqt zonasi: Toshkent UTC+5 fixed offset (tzdata'siz).
- web_app_data: upsert_user ariza saqlangandan keyin, Telegramga yetkazishdan oldin (tekshiruvchi talabi).
- Admin handlerlarda Telegram/ClientDecodeError faqat xato turi bilan log qilinadi (token oqmasligi uchun).

## Kichik topilmalar (keyinroq)
- Broadcast — alohida vazifa.
- storage.init() da commit paytida cancel bo'lsa backfill saqlanib qolishi mumkin (tekshiruvchi O'RTA). Qabul qilindi: faqat startda, backfill idempotent. init'dagi cancel-cleanup kodi ortiqcha murakkab — keyin soddalashtirish mumkin.
- test_admin_panel: 2/3 -> 67% yaxlitlash holati testi yo'q (round vs int).

## Foydalanuvchi vazifalari
- [ ] Deploydan oldin serverdagi leads.db nusxasi.
- [ ] Deploy (so'raganda).
- [ ] Telegram'da /admin ni tekshirish.

## Keyingi sessiya uchun eslatma
- To'lqin 2 Codex limiti tufayli to'xtadi (1-urinish). Qadam 3: kod yozilmagan, fayllar toza. Qadam 4: README.md da ~23 qatorli chala, tekshirilmagan o'zgarish bor (commit qilinmagan) — davomda ishchi shu diffni ko'rib, tugatadi.
- Davom: 2-to'lqin topshirig'ini aynan shu spec bo'yicha qayta berish (qadam 3 + qadam 4).
- Bash hook ~8 KB dan katta heredoc'ni rad etadi — boshqaruvchi promptni qisqa qilsin.
- Codex setup birinchi tekshiruvda shared runtime pipe ulanmadi, login bor.
