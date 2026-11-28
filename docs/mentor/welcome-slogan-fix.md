# Welcome rasmi: slogan imlosini tuzatish + welcome.html = oltin manba
Holat: TUGADI
Ijrochi: codex
Turi: ISH · Hajm: KATTA
Spec: docs/specs/welcome-slogan-fix.md
Boshlangan: 2026-11-28

## Karta
Maqsad: oltin welcome rasmida «Ички имкониятингизни очинг — янги даражага чиқинг» to'g'ri chiqsin; welcome.html bot rasmining manbai bo'lsin.
Qilinmaydi: bot kodi, poster.html, rasmning boshqa qismlari, AI qayta generatsiya, push, deploy.
Qabul mezonlari: spec'dagi ro'yxat.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. welcome-gold.png manba + welcome.html patch + posters.css + test + bot/assets/welcome.png render (commit 8089d3a, 1-urinishda; node 14/14, pytest 442/442; slogan bandidan tashqarida piksel farqi 0, diff bbox (144,677)-(1110,732); tekshiruvchi QABUL)

## Qarorlar
- Faqat slogan qatori tuzatiladi (HTML patch, Cormorant Garamond italic) — foydalanuvchi tanlovi (Tavsiya).
- welcome.html = oltin rasm; ivory variant faqat git tarixida — foydalanuvchi tanlovi (Tavsiya).

## Kichik topilmalar (keyinroq)
- `node --test scripts/posters/tests` (papka) bu Node'da yiqiladi; to'g'ri buyruq: `node --test scripts/posters/tests/*.test.mjs`.
- render.mjs ishchi muhitida Chrome GPU xatosi berdi; rasm qo'shimcha Chrome bayroqlari bilan render qilindi. Keyingi renderda takrorlansa — render.mjs'ga bayroq qo'shishni ko'rib chiqish.
- welcome-gold.png git blob'i oldingi welcome.png bilan bir xil (5719c69) — repo hajmi oshmadi.

## Foydalanuvchi vazifalari
- [ ] Push + Hetzner'da botni yangilash.
- [ ] Telegram'da /start → slogan to'g'riligini ko'rish.

## Keyingi sessiya uchun eslatma
- docs/mentor/miniapp-brand-redesign.md foydalanuvchiniki — tegilmaydi.
- pytest natijasi uchun `rtk proxy python -m pytest bot/tests`.
