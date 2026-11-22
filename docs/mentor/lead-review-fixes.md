# Code-review: 5 ta jiddiy xatoni tuzatish
Holat: TUGADI
Turi: ISH · Hajm: KATTA
Spec: docs/specs/lead-review-fixes.md
Boshlangan: 2026-11-22

## Karta
Maqsad: lead yo'qolmasin; telefon to'g'ri bo'lsin (UZ aniq 12 raqam, xorij + bilan 9–15); admin vaqti created_at dan; CSV telefon "+998 90 123 45 67", ' siz.
Qilinmaydi: 5 ta nit, .playwright-mcp tozalash, push/deploy, UI matn.
Qabul mezonlari: spec'dagi 6 band; boshlang'ich holat pytest 126/126, node 40/40.

## Qadamlar
- [x] 1. Bot: drop_pending_updates olib tashlash + admin vaqti created_at (commit c65b4f1; pytest 129/129)
- [x] 2. Telefon validatsiyasi (pytest 143, node 53; Py/JS 26 qiymatda 0 farq; commit ba0dd3b)
- [x] 3. formatPhone -> validate.js, xorij raqam (commit 27e59e6; node 56, pytest 143, brauzerda tekshirildi)
- [x] 4. CSV telefon formati "998 90 123 45 67" (commit 4ccf53b; pytest 146)

## Qarorlar
- Xorij raqam ruxsat (foydalanuvchi tanlovi = tavsiya).
- CSV: dastlab "+998 90 123 45 67" tanlangan edi, lekin + bilan boshlangan katakni Excel/Sheets formula deb o'qiydi. Qayta so'raldi -> "998 90 123 45 67" (+ siz, ' siz; foydalanuvchi tanlovi = tavsiya). Xorij raqamda ' himoyasi qoladi.

## Foydalanuvchi vazifalari
- [ ] Bot deploy (Hetzner), webapp deploy (Vercel)
- [ ] Telefonda +7 raqam bilan ariza yuborib ko'rish

## Keyingi sessiya uchun eslatma
- Node testlari: `webapp/` ichida `node --test tests/*.test.mjs` (`tests/` argumenti Windows'da ishlamaydi).
- Commit qilinmagan promo fayllari foydalanuvchiniki — tegma.
