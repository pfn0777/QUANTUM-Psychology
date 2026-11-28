# Mini App: welcome uslubidagi premium oltin hero + sarlavhalar
Holat: TUGADI
Ijrochi: codex
Turi: ISH · Hajm: KICHIK
Spec: docs/specs/miniapp-gold-premium.md
Boshlangan: 2026-11-28

## Karta
Maqsad: mini app birinchi ekrani welcome rasmidagidek 3D metall oltin, premium; h2 sarlavhalar oltin.
Qilinmaydi: matn, forma, JS fayllar, yangi rasm, bot, push, deploy.
Qabul mezonlari: spec; `node --test "webapp/tests/*.test.mjs"`; 390x844 + 360x740 skrinshot.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. Premium oltin hero + h2 (commit 746be19, 2-urinishda; faqat styles.css +86/-21, 516 qator; node 56/56; skrinshot 390 cyr/lat, 360 cyr — QUANTUM yorqin oltin + to'q ekstruziya, ~285/350px, kesilmagan)
  - 1-urinish: 56/56 test, diff toza (faqat styles.css). Mentor QAYTARDI: QUANTUM to'q jigarrang (gold-deep stoplari + stroke + ikki ekstruziya), kichik (~70% kenglik), Psychology xira. 2-urinish (high) berildi.

## Qarorlar
- Foydalanuvchi tanlovi: CSS 3D oltin (Tavsiya) — rasm kesish emas.
- Foydalanuvchi tanlovi: doira — hero + sarlavhalar (Tavsiya).
- hero-bg.webp qayta ishlatiladi; yangi AI rasm yo'q (fon welcome'ga allaqachon o'xshash, uni oq qatlam yuvgan).

## Kichik topilmalar (keyinroq)
- .section--feature h2 (to'q fondagi yorqin oltin) skrinshotda ko'rilmadi — file:// iframe'da skroll ishlamadi; telefonda tekshirish.
- render.mjs 390px'da Chrome headless min. oyna kengligi tufayli kesadi — mobil skrinshot uchun iframe wrapper kerak.

## Foydalanuvchi vazifalari
- [ ] Push + Vercel deploy
- [ ] Telegram'da mini app'ni ochib tekshirish
