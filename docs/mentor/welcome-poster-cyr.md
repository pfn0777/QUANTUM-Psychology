# Welcome rasmi + poster: brend uslubi, kirill yozuvlar
Holat: TUGADI
Ijrochi: codex
Turi: ISH · Hajm: KATTA
Spec: docs/specs/welcome-poster-cyr.md
Boshlangan: 2026-11-28

## Karta
Maqsad: bot/assets/welcome.png va "Unlock Your Potential" posterini brend kitobi uslubida (ivory/gold/chocolate), kirill yozuvlar bilan qayta qilish.
Qilinmaydi: bot kodi, matnlar, lotin variant, avatar-logo, deploy, push.
Qabul mezonlari: spec'dagi ro'yxat.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. RASM: scripts/posters/assets/bg.webp 1280x1280, 61 KB (commit bb90542)
- [x] 2. scripts/posters/render.mjs + tests/render.test.mjs — 9/9 (commit 7788f0f)
### To'lqin 2 — TUGADI
- [x] 3. posters.css, welcome.html, poster.html, tests/templates.test.mjs (commit 2ffd880) + welcome.png (commit 1b012d5), 2-urinishda: CTA qator bo'linishi, poster vertikal muvozanati, ikonka o'lchami.
  Poster: brand/posters/quantum-poster-cyr.png (gitignore) + Downloads\2DDD\...(kirill).png nusxasi.
Yakuniy: node 12/12, pytest 442/442.

## Qarorlar
- Brend nomi lotincha (QUANTUM Psychology), qolgan yozuvlar kirill — foydalanuvchi tanlovi.
- "Logo" = tugmasiz poster, brand/posters/ ga + Downloads nusxasi — foydalanuvchi tanlovi.
- CTA: «БЕПУЛ СУҲБАТГА ЁЗИЛИШ ТУГМАСИНИ БОСИНГ», emoji o'rniga oltin strelka.
- Matn AI bilan emas, HTML render bilan (kirill harflar buzilmasligi uchun).

## Kichik topilmalar (keyinroq)

## Foydalanuvchi vazifalari
- [ ] Push, keyin Hetzner'da botni yangilash.

## Keyingi sessiya uchun eslatma
- docs/mentor/miniapp-brand-redesign.md dagi commit qilinmagan o'zgarish foydalanuvchiniki — tegilmaydi.
