# Promo video 30s — Latin variant
Holat: TUGADI
Ijrochi: codex
Turi: ISH · Hajm: KATTA
Spec: docs/specs/promo-video-30s-lat.md
Boshlangan: 2026-11-21

## Karta
Maqsad: kirill promo videoning lotin varianti (yosh auditoriya uchun).
Qilinmaydi: bot/webapp kodi, kirill kompozitsiyalari, musiqa/timing o'zgarmaydi; push yo'q.
Qabul mezonlari: lat MP4 1080x1920 30fps 30.0s; real lat ekranlar; kirill o'zgarmagan; check 0 error; kadrlar ko'rilgan.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. Lotin ekranlari (commit d27a6fc; 7 png, modules-long 1170x9162; toggle #toggleLat bbox @3x x954 y57 w144 h144)
- [x] 2. Chore .gitignore + REVIEW.md (commit 23e74e3)
### To'lqin 2 — TUGADI
- [x] 3. Lotin kompozitsiya + render (commit 0e7187d; sibling project video/promo-lat/ — hyperframes 0.9.72 check/snapshot faqat index.html ni oladi; check passed 0 error; MP4 h264 1080x1920 30fps 30.000s 8.5 MB)

## Kichik topilmalar (keyinroq)
- .gitignore'ga video/promo-lat/{assets/audio,.hyperframes,snapshots,renders}/ qo'shilmagan (hozircha untracked, commitga kirmagan).
- promo-lat/assets — video/promo/assets nusxasi (~10 MB takror).

## Qarorlar
- Foydalanuvchi tanlovi: bot sahnasi kirillcha qoladi (bot /start doim kirillcha); mini app sahnasida «Lotin» tugmasi bosilishi ko'rsatiladi.

## Foydalanuvchi vazifalari
- [ ] Lotin MP4 ni telefonda ko'rish
