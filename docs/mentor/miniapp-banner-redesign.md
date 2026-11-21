# Mini App: banner PNG hero + yorqin redizayn
Holat: TUGADI
Ijrochi: codex
Turi: ISH · Hajm: KATTA
Spec: docs/specs/miniapp-banner-redesign.md
Boshlangan: 2026-11-21

## Karta
Maqsad: hero o'rniga banner rasm, ustidagi CTA formaga olib boradi; butun sahifa yorqin binafsha+oltin, matn kontrasti yuqori.
Qilinmaydi: sendData/validate/telegram.js, bot/, deploy, push.
Qabul mezonlari: spec "Qabul mezonlari"; `node --test "webapp/tests/*.test.mjs"`; impeccable detect; 390x844 skrinshot.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. Banner asset (commit 9e003c9; ffmpeg Codex sandbox'da bloklangan — foydalanuvchi o'zi yuritdi; webp 1314x1197, 195 KB)
- [x] 2. Butun sahifa redizayni (commit b8e86ed, 2-urinishda; 39/39 node test; detect: faqat spec talab qilgan dark-glow)
### To'lqin 2 — TUGADI
- [x] 3. Hero almashtirish (commit e5d9ee0, 1-urinishda; 39/39 node test; 390x844: CTA zona 196x51px, gorizontal skroll yo'q, bosilganda #leadForm)

## Kichik topilmalar (keyinroq)
- Forma placeholder rangi kiritilgan matnga juda o'xshash (telefon "+998 90 123 45 67" to'ldirilgandek ko'rinadi) — placeholder'ni #b9a6e8 atrofiga tushirish (≥4.5:1 saqlab).
- impeccable detect: dark-glow (oltin tugma soyasi) — spec talabi, qoldirildi.
- .playwright-mcp/ untracked — .gitignore'ga qo'shish taklifi.

## Qarorlar
- Foydalanuvchi tanlovi: PNG banner hero o'rniga. Mentor tavsiyasi: HTML hero, sabab: kirill, tiniqlik, og'irlik.
- CTA: formaga skroll, sendData mantig'i o'zgarmaydi.
- Doira: butun mini app.

## Foydalanuvchi vazifalari
- [ ] Push + Vercel deploy
- [ ] Telefonda tekshirish

## Keyingi sessiya uchun eslatma
- Codex'da Python yo'q; JS test: `node --test "webapp/tests/*.test.mjs"`.
