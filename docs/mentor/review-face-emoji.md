# Review album: one Odinaxon card + flower emoji on faces
Holat: TUGADI
Ijrochi: codex
Turi: ISH · Hajm: KICHIK (fayl o'chirish bor — kartada tasdiqlangan)
Spec: yo'q
Boshlangan: 2026-11-27

## Karta
Maqsad: "Natijalar" albomida Ahmedova Odinaxonning 4 ta kartasidan faqat eng kuchlisi (17.jpg, "Коучинггача / Ҳозир") qolsin; belgilangan rasmlarda yuz 🌸 bilan yopilsin.
Qilinadi:
- bot/assets/reviews/16.jpg, 18.jpg, 19.jpg o'chiriladi (tasdiqlangan).
- 🌸 (rangli, Segoe UI Emoji) yuzga: 15.jpg, 17.jpg, 20.jpg, 21.jpg.
- Qayta raqamlash 01..24 (17→16, 20→17, 21→18, 22..27→19..24).
- Manifest: otziv/01, 03, 04 → skipped; post-edit eslatma. EXPECTED_COUNTS reviews 27→24.
Qilinmaydi: prepare_bot_media.py to'liq yurgizilmaydi (about/02.jpg qo'lda almashtirilgan — 5adf46d); video, about, bot kodi o'zgarmaydi.
Qabul mezonlari: reviews 01..24.jpg; 4 rasmda rangli 🌸 yuzni to'liq yopadi, matnga tegmaydi; `python scripts/prepare_bot_media.py --check` va `pytest` o'tadi.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. Emodzi qo'yish + o'chirish + qayta raqamlash + manifest/count (1-urinishda; tekshiruvchining 15.jpg "iyak" topilmasi mentor tomonidan rad etildi — ko'ringan joy bo'yin)

## Qarorlar
- Qoladigan karta: 17.jpg "Коучинггача / Ҳозир" (foydalanuvchi tanlovi = mentor tavsiyasi).
- Emodzi: 🌸 (foydalanuvchi tanlovi; mentor tavsiyasi 😊 edi — did masalasi).
- Pipeline qayta yurgizilmaydi: bot/assets — haqiqat manbai.

## Kichik topilmalar (keyinroq)
- prepare_bot_media.py to'liq qayta yurgizilsa about/02 almashuvi va 🌸 yo'qoladi.
- `prepare_bot_media.py --check` about/02.jpg da yiqiladi (1086x1448 > MAX_IMAGE_SIDE 1280) — 5adf46d dan beri, oldindan mavjud. Tuzatish: rasmni ≤1280 ga kichraytirish.

## Foydalanuvchi vazifalari
- [ ] Serverga deploy (bot qayta ishga tushsa file_id keshi yangilanadi).

## Keyingi sessiya uchun eslatma
- Faqat bitta to'lqin.
