# Promo hook v2 — viral boshlanish (kirill, 30 s)

## Maqsad
Instagram Reels'da tomoshabin birinchi 2–3 soniyada skip qilmasin. Hozirgi hook (`video/promo/compositions/hook.html`) 0-kadrda qora ekran, keyin logo + brend nomi — bu skip'ga olib keladi. Yangi hook: og'riq-savol, 0-kadrdayoq matn va premium AI fon, ovozli zarba. Qolgan 27 s o'zgarmaydi.

## Kontekst
- HyperFrames 0.9.72 loyihasi: `video/promo/` (`index.html`, `compositions/*.html`, `npm run check|render`).
- Hook oralig'i 0–2.791 s (beat'ga bog'langan; beat'lar 0 / 0.698 / 1.395 / 2.093 / 2.791 — `video/audio/README.md`).
- Matn manbai: `webapp/data.js:55` «Такрорланаётган муаммолардан чиқишни хоҳлаганлар».
- Palitra: `#160536`, `#24095a`, `#7b2cf0`/`#9b5cff`, oltin `#f5b52e`/`#ffcf5a`/`#ffe39a`; shriftlar `video/promo/assets/fonts/` (Cormorant Garamond, Montserrat, kirill subset).
- Musiqa: `video uchun music/momotmusic-technology-ambient-201091.mp3`, start 77.880 s, skript `video/audio/analyze-music.mjs`. ffmpeg — CapCut ffmpeg (`$env:LOCALAPPDATA\CapCut\Apps\9.8.0.4213\ffmpeg.exe`).
- `.gitignore`: `video/out/`, `video/audio/`, `video/promo/assets/audio/` — audio va MP4 commit qilinmaydi.

## Chegaralar
- Qilinadi: yangi hook kompozitsiyasi, AI fon rasmi, fade-in'siz musiqa v2, impact/whoosh SFX, `video/out/quantum-promo-30s-v2.mp4`.
- Qilinmaydi: 2.791 s dan keyingi sahnalar (promise, bot, miniapp, form, cta) o'zgarmaydi; lotin versiya (`video/promo-lat/`) tegilmaydi; bot/webapp kodi tegilmaydi; push/deploy yo'q; v1 MP4 o'chirilmaydi.
- Tegilmaydi: `bot/`, `webapp/`, `video/promo-lat/`, `video uchun music/`, `compositions/{promise,bot,miniapp,form,cta}.html`.

## Hook storyboard (0–2.791 s)
| Vaqt | Nima |
|---|---|
| 0.000 | AI fon to'liq ko'rinadi (qorong'u binafsha, siluet), 1-qator «Нега ҳаётингизда» **allaqachon ekranda** (oq, Montserrat 800). Impact SFX. Fon sekin push-in 1.00→1.08. |
| 0.698 | «бир хил муаммо» — oltin, Cormorant 700 italic, eng katta; scale punch 1.15→1 + oltin glow |
| 1.395 | «такрорланади?» — oq, slide-up |
| 2.093 | "Takror" motivi: «бир хил муаммо» qatorining 2–3 ta xira echo nusxasi siljiydi (loop hissi) |
| 2.5–2.791 | Oltin nur chaqnashi (flash) + whoosh → 2.791 da promise sahnasiga keskin kesim (beat ustida) |
- Matn bloki y 520–1300, x 90–990 (Instagram UI xavfsiz zonasi); vinyetka + yengil film grain; deterministik (Math.random yo'q).

## Qabul mezonlari
- [ ] `npx hyperframes@0.9.72 check` — 0 error
- [ ] Snapshot 0.0 s: qora emas, fon + 1-qator matn ko'rinadi; 0.8 / 1.6 / 2.3 / 2.7 / 3.0 s kadrlar — matn kesilmagan, xavfsiz zonada, imlo to'g'ri
- [ ] AI rasm: matn/logo/watermark/yuz yo'q, 1080×1920, palitraga mos — `ffprobe` + men `Read` bilan ko'raman
- [ ] `video/out/quantum-promo-30s-v2.mp4`: 1080×1920, 30 fps, H.264+AAC, 30.0 ±0.1 s — `ffprobe`
- [ ] Audio: birinchi 0.3 s jim emas (impact eshitiladi), umumiy ≈ −14 LUFS, true peak ≤ −1 dBTP — `ffmpeg ebur128` + `astats`
- [ ] 2.791 s dan keyingi kadrlar v1 bilan bir xil (5 s, 15 s, 26 s snapshot'lar v1 bilan solishtiriladi)

## To'lqinlar
### To'lqin 1 (2 qadam parallel) — umumiy tekshiruv: `ffprobe` rasm va audio fayllari
1. **RASM: hook foni** — fayllar: `video/promo/assets/hook/hook-bg-a.png`, `hook-bg-b.png` (2 variant, men birini tanlayman) — imagegen (Codex), keyin ffmpeg bilan cover-crop 1080×1920.
   - Subject: orqadan ko'ringan yolg'iz siluet odam, qorong'u binafsha bo'shliqda, atrofida o'zini takrorlovchi halqa/eshiklar koridori (loop — "bir xil muammo"), oldinda tor oltin nur yorig'i.
   - Style: kinematografik, yuqori kontrast, chuqur binafsha #160536–#24095a, oltin #ffcf5a aksent, film grain, premium.
   - Composition: vertikal 9:16, siluet pastki uchdan birda, yuqori-o'rta qism bo'sh (matn uchun qorong'u negative space).
   - Avoid: yuz, matn, harf, logo, watermark, ortiqcha qo'l-oyoq, yorqin to'yingan ranglar.
2. **Audio v2** — fayllar: `video/promo/scripts/make-hook-audio.mjs` (commit), chiqish `video/promo/assets/audio/music-30s-v2.m4a`, `hook-impact.wav`, `hook-whoosh.wav` (gitignore) — musiqa: o'sha start 77.880 s, fade-in yo'q, 2 s fade-out, loudnorm −14 LUFS; SFX ffmpeg'da sintez (impact: 45–60 Hz sinus + noise transient, eksponensial so'nish ~0.8 s; whoosh: 0.3 s filtrlangan shovqin sweep) — tekshiruv: `ffprobe` + `ebur128`.

### To'lqin 2 (1-ga bog'liq) — umumiy tekshiruv: `npm run check` + `ffprobe video/out/quantum-promo-30s-v2.mp4`
3. **Hook kompozitsiya + render** — fayllar: `video/promo/compositions/hook.html`, `video/promo/index.html` (audio src → v2, SFX `<audio>` elementlari 0 s va 2.49 s da), `video/promo/SPEC.md`, `video/promo/REVIEW.md`, `video/out/quantum-promo-30s-v2.mp4` — mezon: storyboard + qabul mezonlari — tekshiruv: check 0 error, snapshot'larni men ko'raman, keyin render.

Har qabul qilingan qadam alohida lokal commit (MP4/audio commit qilinmaydi). Push yo'q.

## DB / migratsiya: yo'q

## Foydalanuvchi bajaradigan ishlar
- v2 MP4 ni telefonda ovoz bilan va ovozsiz ko'rish.
- Instagram'da A/B: v1 va v2 ni (yoki Trial Reels) solishtirib, 3 s retention'ni Insights'da ko'rish.

## Xavflar
- AI rasm siluetida artefakt chiqishi mumkin — 2 variant, buzuq bo'lsa qayta generatsiya.
- 2.8 s ichida 3 qator o'qilishi tig'iz — so'zlar beat bo'yicha chiqadi, oxirgi qator 1.4 s da tugaydi (1.4 s o'qish vaqti).

## Mentor fikri
- Brend nomi hook'dan olib tashlanadi — u promise/bot/CTA sahnalarida bor. Bu ataylab: viral hook brend emas, tomoshabin og'rig'i bilan boshlanadi.

## Taxminlar
- Hook matni: «Нега ҳаётингизда / бир хил муаммо / такрорланади?»
- Hook davomiyligi 2.791 s saqlanadi (keyingi sahnalar siljimaydi).
