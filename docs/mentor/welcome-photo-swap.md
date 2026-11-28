# /start welcome image: swap to Downloads\welcom.png
Holat: TUGADI
Ijrochi: codex
Turi: ISH · Hajm: KICHIK
Spec: yo'q
Boshlangan: 2026-11-28

## Karta (foydalanuvchi tasdiqlagan: "ha")
Maqsad: /start bosilganda C:\Users\user\Downloads\welcom.png dagi rasm chiqsin.
Qilinadi: bot/assets/welcome.png shu fayl bilan almashtiriladi (PNG, 1254x1254, 2.3 MB). Kod o'zgarmaydi — bot/bot.py:55 WELCOME_PHOTO shu yo'lni ishlatadi.
Qilinmaydi: bot kodi, caption, tugmalar, scripts/posters shablonlari, push, deploy.
Qabul mezonlari: ffprobe → png 1254x1254 · `python -m pytest bot/tests` o'tadi.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. Downloads\welcom.png → bot/assets/welcome.png; sha256 bir xil (4bdd3334...), png 1254x1254 (commit 55537f9; pytest 442/442)

## Qarorlar
- Mentor topilmasi: rasmda imlo xatosi "имкониятигеизни" (to'g'risi "имкониятингизни"). Mentor tavsiyasi: avval tuzatish. Foydalanuvchi kartani "ha" bilan tasdiqladi — rasm shu holicha qo'yildi.
- scripts/posters/welcome.html shabloni endi bot rasmiga mos emas — xabardor qilindi.

## Kichik topilmalar (keyinroq)
- rtk filtri pytest'ning yakuniy "N passed" qatorini yutadi; to'g'ri natija `rtk proxy python -m pytest ...` bilan olinadi.

## Foydalanuvchi vazifalari
- [x] Codex runtime tiklandi.
- [ ] Push + Hetzner'da botni yangilash.

## Keyingi sessiya uchun eslatma
- docs/mentor/miniapp-brand-redesign.md dagi commit qilinmagan o'zgarish foydalanuvchiniki — tegilmaydi.
