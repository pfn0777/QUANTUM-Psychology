# Mini App: yangi brend kitobi bo'yicha redizayn + oltin HTML hero
Holat: JARAYONDA
Ijrochi: codex
Turi: ISH · Hajm: KATTA
Spec: docs/specs/miniapp-brand-redesign.md
Boshlangan: 2026-11-28

## Karta
Maqsad: butun mini app yangi brendda (fil suyagi + oltin + shokolad); hero — Codex fon rasmi + HTML oltin "QUANTUM Psychology" + shokolad CTA → #leadForm.
Qilinmaydi: ko'p ekranli ilova, matn mazmuni, sendData/validate/telegram.js/data.js, bot/, deploy, push.
Qabul mezonlari: spec "Acceptance"; `node --test "webapp/tests/*.test.mjs"`; 390x844 cyr/lat + 360x740 skrinshot.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. RASM: webapp/assets/hero-bg.webp (commit c912b9b, 1-urinishda; 1024x1536, 36 KB; ffmpeg'ni boshqaruvchi yuritdi; PNG o'chirildi)
- [x] 2. Brend tokenlari va butun sahifa (commit 66d61e3, 1-urinishda; 56/56 node test; binafsha qoldiq yo'q)
### To'lqin 2 — KOD TUGADI, VIZUAL TEKSHIRUV KUTILMOQDA
- [x] 3. Hero qayta qurish (commit 77dbc1c, 2-urinishda: gradient yuqori stopi 2.88:1 → #AD7F32 3.33:1; 56/56 node test; eski bannerlar o'chirildi)
- [ ] Vizual: 390x844 cyr/lat, 360x740 — lokal server ishga tushirish auto-mode'da rad etildi, foydalanuvchi ruxsati yoki telefonda tekshiruv kerak

## Qarorlar
- Foydalanuvchi tanlovi: matnsiz rasm + HTML matn (mentor tavsiyasi bilan bir xil).
- Doira: hozirgi sahifani yangi brendga o'tkazish, struktura o'zgarmaydi.

## Kichik topilmalar (keyinroq)
- .hero__title-main da background-clip:text bilan text-shadow — Chrome'da gradient ustini biroz xiralashtirishi mumkin (juda zaif .08); vizualda ko'rinsa olib tashlash.
- app.js'dagi data-i18n-src sikli endi ishlatilmaydi (zararsiz).
- logo-mark.svg boshida BOM bor (brauzerga zarar yo'q, lekin keraksiz).
- 1-to'lqinda 360px skroll va tap-target brauzerda tekshirilmagan — 2-to'lqin skrinshotida tekshiriladi.

## Foydalanuvchi vazifalari
- [ ] Push + Vercel deploy
- [ ] Telefonda tekshirish

## Keyingi sessiya uchun eslatma
- Codex'da Python yo'q; ffmpeg oldin sandbox'da bloklangan; PNG o'lchami biroz siljiydi (scale bilan to'g'rilash).
