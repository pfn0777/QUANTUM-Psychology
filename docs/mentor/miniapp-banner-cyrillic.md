# Mini App: kirill banner + yozuvga qarab almashish
Holat: TUGADI
Ijrochi: codex
Turi: ISH · Hajm: KICHIK
Spec: docs/specs/miniapp-banner-cyrillic.md
Boshlangan: 2026-11-21

## Karta
Maqsad: kirillda kirill banner, lotinda hozirgi lotin banner; "QUANTUM Psychology" ikkalasida lotincha.
Qilinmaydi: lotin bannerni qayta yasash, CTA zonani siljitish, forma/bot/deploy/push.
Qabul mezonlari: spec "Acceptance"; `node --test "webapp/tests/*.test.mjs"`; 390x844 ikkala yozuvda.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. RASM: webapp/assets/hero-banner-cyr.webp (commit bb928fa; 2-urinish; 1314x1197, 187 KB; foydalanuvchi ffmpeg bilan o'girdi)
### To'lqin 2 — TUGADI
- [x] 2. Swap: index.html + app.js + i18n.js (heroImageSrc kaliti) + data.test.mjs (commit b83ce42, 1-urinishda; 40/40 node test; 390x844: cyr → hero-banner-cyr.webp, lat → hero-banner.webp, CTA zona 68–84%, 196x51px)

## Qarorlar
- Foydalanuvchi tanlovi: rasmli banner (matn rasm ichida). Mentor tavsiyasi: HTML hero (kirill harflari buzilishi xavfi).

## Kichik topilmalar (keyinroq)
- Codex PNG ni 1313x1198 o'lchamda chiqaradi — konvertatsiyada scale=1314:1197 bilan to'g'rilanadi.

## Foydalanuvchi vazifalari
- [ ] Push + Vercel deploy
- [ ] Telefonda tekshirish

## Keyingi sessiya uchun eslatma
- Codex'da Python yo'q; ffmpeg oldin sandbox'da bloklangan.
