# Promo video 30s (bot + mini app)
Holat: TUGADI
Ijrochi: codex
Turi: ISH · Hajm: KATTA
Spec: docs/specs/promo-video-30s.md
Boshlangan: 2026-11-21

## Karta
Maqsad: 30 s vertikal (1080x1920) motion video, mini app uslubida, musiqa bilan, CTA @quantum_PsyBot.
Qilinmaydi: bot/webapp kodi o'zgarmaydi; voiceover, subtitr, AI rasm, lotin/16:9 yo'q; push/deploy yo'q.
Qabul mezonlari: video/out/quantum-promo-30s.mp4 1080x1920 30fps 30.0s H.264+AAC; hyperframes check 0 error; kadrlar ko'rib chiqilgan.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. HyperFrames loyiha + mini app ekranlari (commit e002932)
- [x] 2. Musiqa 30 s bo'lagi (video/audio/, gitignore'da — commit yo'q; start 77.88 s, 86 BPM, -14.4 LUFS, -1.9 dBTP, 3-urinishda)
### To'lqin 2 — TUGADI
- [x] 3. (commit 59ca325, 2-urinishda; check ok 0 error / 13 warning; MP4 h264 1080x1920 30fps 30.000s, 8.3 MB)
- Eslatma: REVIEW.md:5 eskirgan; video/promo/.hyperframes/{artifacts,cache,video-state.json} .gitignore'ga qo'shilishi kerak.
- Sahna Kompozitsiya + render (sahna chegaralari beat'ga: 0 / 2.791 / 6.977 / 12.558 / 18.140 / 23.721 / 30)

## Kichik topilmalar (keyinroq)
- Codex sandbox'da WinGet ffmpeg EPERM — CapCut ffmpeg ($env:LOCALAPPDATA\CapCut\Apps\9.8.0.4213) ishlatiladi.
- HyperFrames init keshdagi 0.9.72 bilan qilingan.

## Qarorlar
- Format 9:16, kirill, haqiqiy ekranlar + motion, username @quantum_PsyBot (foydalanuvchi tanlovi).

## Foydalanuvchi vazifalari
- [ ] MP4 ni telefonda ko'rish
- [ ] Musiqa litsenziyasini tasdiqlash
