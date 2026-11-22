# QUANTUM Psychology — 30 soniyalik promo video (bot + mini app)

## Maqsad
Instagram Reels/Stories va Telegram kanal uchun 30 s vertikal motion-grafika video: bot va mini app nima qilishini ko'rsatadi va odamni `@quantum_PsyBot` ga bepul suhbatga yozilishga chaqiradi. Uslub — mini app'ning o'zi (to'q binafsha + oltin, Cormorant Garamond + Montserrat), musiqa — `video uchun music/momotmusic-technology-ambient-201091.mp3`.

## Kontekst
- Mini app: `webapp/` (statik). Ranglar `webapp/styles.css:3-14`: `#160536` fon, `#24095a`/`#33107a` sirt, `#7b2cf0`/`#9b5cff` binafsha, `#ffcf5a`/`#ffe39a`/`#f5b52e` oltin, matn `#fff`/`#e4d8ff`. Shriftlar `webapp/fonts/*.woff2`, logo `webapp/assets/logo-mark.svg`, banner `webapp/assets/hero-banner-cyr.webp`.
- Matnlar (kirill): `webapp/i18n.js` (`heroTagline`, `heroSubtitle`, `consultationStep1-3`, `heroCta`...), `bot/texts.py` (`welcome_caption`, `open_button`, `thanks`). Bot rasmi `bot/assets/welcome.png`.
- Vosita: HyperFrames (`npx hyperframes`, HTML → MP4, skill `C:/Users/user/.claude/skills/hyperframes/SKILL.md` + `references/types/vertical.md`, `references/types/launch.md`), ffmpeg/ffprobe bor. Codex `ready: true`.
- Musiqa 115.2 s, 256 kbps — 30 s bo'lagi kesiladi.

## Chegaralar
- Qilinadi: yangi papka `video/promo/` (HyperFrames loyihasi), mini app ekran suratlari, musiqa bo'lagi, render qilingan MP4.
- Qilinmaydi: bot/mini app kodi o'zgarmaydi; ovoz (voiceover) va subtitr yo'q; AI rasm generatsiya yo'q; lotin versiya va 16:9 yo'q; push/deploy yo'q.
- Tegilmaydi: `bot/`, `webapp/` (faqat o'qiladi), `video uchun music/` (asl fayl o'zgarmaydi).

## Qabul mezonlari
- [ ] `video/out/quantum-promo-30s.mp4`: 1080×1920, 30 fps, H.264 + AAC, davomiyligi 30.0 ±0.1 s — tekshiruv: `ffprobe`
- [ ] Musiqa 30 s, boshida ~0.5 s fade-in, oxirida ~2 s fade-out, ovoz balandligi ≈ −14 LUFS — tekshiruv: `ffmpeg -af ebur128`
- [ ] Ranglar va shriftlar faqat mini app palitrasidan; barcha matn kirillda, imlo `i18n.js`/`texts.py` dagidek
- [ ] Mini app ekranlari — haqiqiy (Playwright bilan `webapp/` dan olingan), telefon ramkasida
- [ ] Oxirgi kadrda: logo, «Дастлабки суҳбат — БЕПУЛ», `@quantum_PsyBot`, oltin tugma «Бепул суҳбатга ёзилиш»
- [ ] `npx hyperframes check --json` — 0 error; matn 80% title-safe zonada
- [ ] Men har sahnadan kadrni ko'rib chiqaman (snapshot) — buzuq/kesilgan matn yo'q

## Storyboard (30 s, 9:16)
| Vaqt | Sahna | Mazmun |
|---|---|---|
| 0–3 s | Hook | Qora-binafsha fon, oltin zarrachalar, atom-logo chiziladi, «QUANTUM *Psychology*» oltin gradientda |
| 3–7 s | Va'da | Kinetik matn: «Ички имкониятингизни очинг —» / «янги даражага чиқинг» |
| 7–12 s | Bot | Telefonda Telegram chat mockup: `welcome.png` + haqiqiy `welcome_caption`, «Бепул суҳбатга ёзилиш» tugmasi pulslaydi → bosiladi |
| 12–18 s | Mini app | Mini app ochiladi: banner → «12 ойлик дастур · 12 модуль» kartochkalari scroll bo'ladi |
| 18–24 s | Ariza | Forma to'ldiriladi (namuna: «Мадина», +998 90 123 45 67, mavzular) → oltin tugma → «Аризангизни олдик» |
| 24–30 s | CTA | Logo, «Дастлабки суҳбат — БЕПУЛ», `@quantum_PsyBot`, oltin tugma; musiqa so'nadi |
Sahna almashuvlari musiqa urg'ulariga (beat) moslanadi, agar ritm aniqlansa.

## Chekka holatlar
- Mini app Telegram'siz ochilsa (`telegram-web-app.js`) — oddiy brauzerda render bo'lishi kerak; muvaffaqiyat paneli `hidden` ni olib tashlash bilan suratga olinadi.
- Kirill shriftlari: `@font-face` faqat `assets/fonts/` dagi woff2 lar orqali (cyrillic + cyrillic-ext subsetlari).
- `init` bo'sh bo'lmagan papkaga yozmasligi mumkin — shuning uchun musiqa 1-to'lqinda alohida papkaga chiqadi.

## To'lqinlar
### To'lqin 1 (2 qadam parallel) — umumiy tekshiruv: `ffprobe` ikki natija bo'yicha
1. **Loyiha + ekranlar** — fayllar: `video/promo/**` (init, `assets/fonts`, `assets/logo-mark.svg`, `assets/welcome.png`, `assets/screens/*.png`, `scripts/capture-screens.mjs`), `.gitignore` (`video/out/`, `video/audio/`, `video/promo/assets/audio/`) — mezon: 4–5 ta ekran (banner, modullar, to'ldirilgan forma, muvaffaqiyat paneli), 390×844 CSS px @3x — tekshiruv: `ffprobe` o'lcham + men `Read` bilan ko'raman.
2. **Musiqa bo'lagi** — fayllar: `video/audio/music-30s.m4a`, `video/audio/README.md` (buyruq va tanlangan oraliq) — mezon: eng jonli 30 s oraliq (RMS/onset tahlili), fade, −14 LUFS, BPM hisobotda — tekshiruv: `ffprobe` + `ebur128`.

### To'lqin 2 (1-to'lqinga bog'liq) — umumiy tekshiruv: `npx hyperframes check --json` + `ffprobe video/out/quantum-promo-30s.mp4`
3. **Kompozitsiya + render** — fayllar: `video/promo/index.html`, `video/promo/compositions/*.html`, `video/promo/SPEC.md`, `video/promo/assets/audio/` (musiqa nusxasi), `video/out/quantum-promo-30s.mp4` — mezon: yuqoridagi storyboard va qabul mezonlari — tekshiruv: check 0 error, `snapshot --review` kadrlarini men ko'raman, keyin render.

Har qabul qilingan qadam alohida lokal commit (MP4 va audio commit qilinmaydi). Push yo'q.

## DB / migratsiya: yo'q

## Foydalanuvchi bajaradigan ishlar
- Tayyor MP4 ni telefonda ko'rib chiqish va fikr berish.
- Musiqa litsenziyasi: Pixabay'dan olingan bo'lsa tijoriy foydalanish mumkin — manbani o'zingiz tasdiqlang.

## Xavflar
- Forma namunasi soxta ma'lumot — ochiq "namuna" sifatida (+998 90 123 45 67 — mini app placeholderi), haqiqiy odam ma'lumoti emas.
- Bot chati — haqiqiy matn va rasm bilan qurilgan mockup (Telegram skrinshoti yo'q); ko'rinishi Telegram'ga yaqin, lekin 1:1 emas.

## Mentor fikri
- Bot ekranining haqiqiy skrinshoti repo'da yo'q. Telefoningizdan `/start` skrinshotini yuborsangiz, mockup o'rniga u qo'yiladi — ishonchliroq. Hozircha mockup bilan ketamiz.

## Taxminlar
- Musiqaning eng energetik 30 s qismi avtomatik tanlanadi.
- Forma namunasi ismi «Мадина».
- Video 30 fps, H.264, ~8–12 Mbit/s.
