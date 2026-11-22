# Promo video 30s — Latin variant

Approved plan copy: C:\Users\user\.claude\plans\foamy-growing-shore-of-7f96999e-123b-416a-b76d-f41f4b7527c0.md

## Decision
Bot scene (3) stays Cyrillic (bot /start is always Cyrillic, bot/bot.py:157). Everything else Latin. Mini app scene shows a tap on the «Lotin» toggle, then Latin screens.

## Latin texts (source: webapp/i18n.js lat, bot/texts.py lat)
- Promise: «Ichki imkoniyatingizni oching — yangi darajaga chiqing»
- Mini app caption: «12 oylik dastur · 12 modul»
- Form caption: «Ariza — 1 daqiqada»; success: «Arizangiz qabul qilindi»
- CTA: «Dastlabki suhbat — BEPUL», @quantum_PsyBot, button «Bepul suhbatga yozilish»
- Use ʻ (U+02BB) for oʻ/gʻ exactly as i18n.js.

## Acceptance
- video/out/quantum-promo-30s-lat.mp4: 1080x1920, 30 fps, H.264+AAC, 30.0 ±0.1 s
- video/promo/assets/screens-lat/*.png: real Latin mini app screens, 1170x2532
- Cyrillic compositions and screens unchanged
- hyperframes check: 0 errors for the Latin root
- Contact sheet: Cyrillic only in bot scene, no tofu, no cropped text
- .gitignore covers video/promo/.hyperframes/

## Waves
1a. capture-screens.mjs `--script lat` → assets/screens-lat/ (default cyr behaviour unchanged)
1b. .gitignore + REVIEW.md:5
2. index-lat.html + compositions/lat/{promise,miniapp,form,cta}.html, reuse hook.html and bot.html; render MP4
