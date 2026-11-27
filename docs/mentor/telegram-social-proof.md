# Bot vitrinasi: natijalar, otzivlar, Коучинг 12, ustoz, qo'ng'iroq
Holat: TUGADI
Ijrochi: codex
Turi: ISH · Hajm: XAVFLI (shaxsiy ma'lumot: telefon)
Spec: docs/specs/telegram-social-proof.md
Boshlangan: 2026-11-27

## Karta
Maqsad: botga kirgan mijoz otzivlar, Коучинг 12 video, ustoz haqida ma'lumotni ko'rib, ariza qoldirsin yoki qo'ng'iroq so'rasin.
Qilinmaydi: AI rasm, drip eslatmalar, admin panel statistikasi, Mini App o'zgarishi, deploy, push.
Qabul mezonlari: spec "Tests" bo'limi; `py -3.11 -m pytest -q` va `node --test "webapp/tests/*.test.mjs"` yashil.

## To'lqinlar
### To'lqin 0 — mentor: Instagram media manifesti — TUGADI
- [x] 0. 23 ta story skrinshoti `Otzivlar/instagram/{natijalar,otziv,asoschi}/` ga; manifest `docs/specs/instagram-media-manifest.json` (crop qutilari bilan)
### To'lqin 1 (parallel) — TUGADI
- [x] 1. Media pipeline (2-to'lqinda kesim tuzatilib qayta yasaldi, commit c8ba62a)
- [x] 2. `bot/storage.py` + `bot/tests/test_storage_callbacks.py` [XAVFLI] (commit 6fe06a4)
- [x] 3. `bot/texts.py`, `bot/content.py`, `bot/tests/test_catalog.py`, `bot/tests/test_content.py` (commit 7ea4317)
### To'lqin 2 (parallel) — TUGADI
- [x] A. Media: target cheklovi + qayta yasash; 27+2 JPEG, video 9.5 MB (commit c8ba62a)
- [x] 4. `bot/showcase.py` + `bot/tests/test_showcase.py` (commit fe59ffa)
- [x] 5. `bot/callbacks.py` + `bot/tests/test_callbacks.py` [XAVFLI] (commit d753469, tekshiruvchi QABUL)
### To'lqin 3 — TUGADI
- [x] 6. (commit 3d604a8, 2-urinishda; 442 test yashil)
  Fayllar: `bot/bot.py` + `bot/tests/test_bot.py` — ulash [XAVFLI]

## Qarorlar
- Foydalanuvchi tanlovi: otzivlardagi ismlar boricha. Mentor tavsiyasi: ism qatorini kesish, sabab: odamlar botda ishlatilishiga rozilik bermagan bo'lishi mumkin.
- Qo'ng'iroq yo'li: ikkalasi — "Менга қўнғироқ қилинг" (request_contact) + kontakt kartasi.
- Kontakt: +998 91 662 81 11, @aziza8111.
- Natijalar bo'limida izoh: "натижалар — шахсий тажриба, ҳар кимда турлича".
- AI rasm ishlatilmaydi (haqiqiy otziv va foto bor).
- Instagram story'lar video karta (360x640), CDN URL'larini yuklab bo'lmaydi → to'xtatilgan story ekrandan olindi (327x583), skript 2x kattalashtiradi.
- Tibbiy da'voli kartalar (allergiya, migren, "kasalliklar to'xtagan") botga olinmadi — mentor qarori: Telegram reklama qoidalari va ishonch xavfi. Foydalanuvchi xohlasa qo'shiladi.
- НАТИЖА - ОТЗЫВ highlight'i hozircha olinmadi: 27 ta otziv (3 sahifa) yetarli.
- Rejadan aniqlashtirish: admin xabari render va kontakt tekshiruvi alohida `bot/callbacks.py` ga (2-to'lqinda parallel), `bot.py` yengilroq bo'lishi uchun. Yetkazilmagan qo'ng'iroq so'rovlari ham retry qilinadi.

## Kichik topilmalar (keyinroq)
- `bot/tests/test_bot.py` 1046 qator (>800) — mavzu bo'yicha bo'lish (start/showcase/callback/admin).
- `bot/showcase.py` xatoda `logger.exception` (traceback) ishlatadi; shaxsiy ma'lumot yo'q, lekin loyiha uslubiga moslab "faqat tur nomi" qilish mumkin.
- Admin xabari ketib, `mark_callback_delivered` yiqilsa — retry qayta yuboradi (at-least-once). Qabul qilindi: takroriy xabar yo'qolgan qo'ng'iroqdan yaxshiroq; leads yo'li ham shunday.
- НАТИЖА - ОТЗЫВ highlight'i va qolgan ~25 ОТЗЫВ story'si hali olinmagan.

## Foydalanuvchi vazifalari
- [ ] Deploydan oldin `leads.db` zaxira nusxasi
- [ ] `git push` + deploy
- [ ] Telegramda qo'lda tekshiruv

## Keyingi sessiya uchun eslatma
- `Otzivlar/` commit qilinmaydi.
