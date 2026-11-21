# /start welcome photo + inline Mini App button
Holat: TUGADI (deploy foydalanuvchida)
Ijrochi: codex
Turi: ISH · Hajm: KATTA
Spec: docs/specs/start-welcome-photo.md
Boshlangan: 2026-11-21

## Karta
Maqsad: /start → hero rasm + xush kelibsiz caption + inline web_app tugma; pastki reply tugma qoladi.
Qilinmaydi: server endpoint, deploy, push.
Qabul mezonlari: spec'dagi ro'yxat.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. bot/assets/welcome.png (hero screenshot) (commit 714600c)
- [x] 2. webapp canSendToBot (initData) + openFromBot matni (commit 7de89c1)
### To'lqin 2 — TUGADI
- [x] 3. (commit f668d80, 2-urinishda: yuborish tartibi testi qo'shildi)
Yakuniy: pytest 124/124, node --test 39/39.
- [ ] 3 (asl matn): bot /start: answer_photo + inline tugma + reply keyboard

## Qarorlar
- Foydalanuvchi tanlovi: gibrid (inline + pastki tugma). Sabab: sendData faqat keyboard launch'da ishlaydi; to'liq inline uchun server kerak.

## Kichik topilmalar (keyinroq)
- `node --test webapp/tests/` (papka) Node 26 da 0 test bilan yiqiladi; `node --test webapp/tests/*.mjs` ishlatilsin.
- Codex shablonlari (ishchi.md, rasm.md) Secret guard'ga tushardi — foydalanuvchi tuzatdi.

## Foydalanuvchi vazifalari
- [ ] Push → Vercel, keyin botni Hetzner'da yangilash (avval Vercel).
