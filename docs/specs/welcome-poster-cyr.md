# Welcome rasmi + poster: brend kitobi uslubida, kirill yozuvlar

## Maqsad
Bot /start da yuboriladigan `bot/assets/welcome.png` hali eski binafsha-neon uslubda va lotincha. Uni brend kitobi uslubiga (fil suyagi, oltin, shokolad) o'tkazib, yozuvlarni kirillga almashtirish. Xuddi shu dizayndagi tugmasiz posterni ham (`Downloads\2DDD\Quantum Psychology_ Unlock Your Potential.png`) shu uslubda, kirill yozuvlar bilan tayyorlash. Foydalanuvchi: bot mijozlari (standart til — kirill, `bot/texts.py:99`).

## Kontekst
- Bot: `bot/bot.py:55` — `WELCOME_PHOTO = BOT_DIR / "assets" / "welcome.png"`, 1254x1254. Kod o'zgarmaydi, faqat fayl almashadi.
- Brend tokenlari: `docs/specs/miniapp-brand-redesign.md` (ivory `#FBF6EC`, gold `#C9A050`, chocolate `#3B2112`, bronze `#8C6420`, gradientlar, Cormorant Garamond + Montserrat, emoji yo'q, binafsha yo'q).
- Qayta ishlatiladi: `webapp/fonts.css` + `webapp/fonts/` (kirill subsetlari bor), `webapp/assets/logo-mark.svg` (atom belgisi), `webapp/i18n.js:8-17` kirill matnlari.
- Mini App hero'si allaqachon shu yondashuvda qilingan: matnsiz AI fon + HTML matn.

## Chegaralar
- Qilinadi: matnsiz fon rasm (Codex imagegen), HTML/CSS shablonlar, headless Chrome bilan PNG'ga render, `bot/assets/welcome.png` ni almashtirish, poster PNG.
- Qilinmaydi: bot kodi, matnlar (`texts.py`, `i18n.js`), lotincha variant rasmi, alohida avatar-logo, deploy, push.
- Tegilmaydi: `bot/*.py`, `webapp/` (faqat o'qiladi), `brand/` dagi brend kitobi.

## Rasm matnlari (brend nomi lotincha, qolgani kirill)
- Eyebrow pill: «12 ОЙЛИК ДАСТУР»
- Sarlavha: «QUANTUM» (oltin gradient, Cormorant 700) + «Psychology» (bronza, italic)
- Subtitle: «12 ойлик шахсий ва руҳий ривожланиш дастури»
- 3 foyda (oltin chiziqli ikonka: miya, lotus, o'sish): «Фикр кучини бошқариш» · «Ички мувозанат ва хотиржамлик» · «Ҳаёт сифатини юксалтириш»
- Shior: «Ички имкониятингизни очинг — янги даражага чиқинг»
- Faqat welcome'da: oltin strelka (emoji o'rniga) + shokolad CTA pill «БЕПУЛ СУҲБАТГА ЁЗИЛИШ ТУГМАСИНИ БОСИНГ»

## Qabul mezonlari
- [ ] `bot/assets/welcome.png` — 1254x1254 PNG, < 5 MB — `ffprobe`
- [ ] Poster — 1313x1198 PNG: `brand/posters/quantum-poster-cyr.png` + nusxa `Downloads\2DDD\Quantum Psychology_ Unlock Your Potential (kirill).png` (asl fayl o'zgarmaydi)
- [ ] Barcha yozuvlar kirill (brend nomidan tashqari), harflar buzilmagan (Ҳ, Қ, Ў, Ғ to'g'ri) — qo'lda ko'rish
- [ ] Binafsha rang, neon, emoji yo'q; ranglar faqat brend tokenlaridan — `node --test` shablon testi
- [ ] Fon rasmida hech qanday matn/harf/logo yo'q — Codex tekshiruvchisi FOCUS: RASM + men ko'raman
- [ ] Bot testlari buzilmagan — `pytest -q`

## Chekka holatlar
- Shrift yuklanmasa render lotin fallback bilan chiqadi → render skripti shriftlar yuklanishini kutadi (`--virtual-time-budget`), testda tekshiriladi.
- Chrome topilmasa → Edge yo'li, ikkalasi ham bo'lmasa aniq xato bilan to'xtaydi.
- Telegram foto limiti 10 MB → hajm tekshiriladi.

## To'lqinlar
### To'lqin 1 (parallel) — umumiy tekshiruv: `node --test scripts/posters/tests/*.mjs`
1. **RASM** — `scripts/posters/assets/bg.webp` (kvadrat, kamida 1254x1254 ga crop/resize). Mazmun: krem marmar fon, burchaklarda oltin ipak to'lqinlar, pastda oltin chiziqli yorug' miya (line-art) va konsentrik oltin halqalar, yuqorida yumshoq oltin bokeh. Markaz bo'sh va yorug' (matn uchun). Uslub manbai: `webapp/assets/hero-bg.webp`. Avoid: har qanday matn/harf/logo, binafsha/ko'k, neon, inson. — tekshiruv: `ffprobe` + tekshiruvchi FOCUS: RASM
2. **BAJARISH** — `scripts/posters/render.mjs` + `scripts/posters/tests/render.test.mjs`: HTML → PNG (headless Chrome/Edge, `--screenshot --window-size=W,H --hide-scrollbars --virtual-time-budget`), argumentlar: html, out, width, height; xatoda log + exit 1 (silent catch yo'q). Test: argument validatsiyasi, brauzer yo'lini topish. — tekshiruv: `node --test scripts/posters/tests/render.test.mjs`

### To'lqin 2 (1-ga bog'liq) — umumiy tekshiruv: `node --test scripts/posters/tests/*.mjs; pytest -q`
3. **BAJARISH** [3+ fayl → tekshiruvchi FOCUS: RASM] — `scripts/posters/posters.css`, `welcome.html`, `poster.html`, `tests/templates.test.mjs`; render qilish → `bot/assets/welcome.png` (1254x1254), `brand/posters/quantum-poster-cyr.png` (1313x1198) + Downloads nusxasi. Fontlar `../../webapp/fonts.css` orqali, atom — `logo-mark.svg` dan inline. Test: kirill matnlar bor, eski lotin matnlar yo'q, emoji yo'q, binafsha hex yo'q. — tekshiruv: `node --test scripts/posters/tests/templates.test.mjs` + `ffprobe`

## DB / migratsiya: yo'q

## Foydalanuvchi bajaradigan ishlar
- Push, keyin Hetzner'da botni yangilash (yangi welcome.png serverga tushishi uchun).
- Posterni kerakli joyga (kanal/post) o'zi joylaydi.

## Xavflar
- AI rasmda kirill harflar buziladi — shuning uchun matn rasmga AI bilan emas, HTML render bilan yoziladi.
- Lotin tilini tanlagan foydalanuvchi ham kirill welcome rasmini ko'radi (bot bitta rasm yuboradi). Hozircha qabul qilinadi.

## Mentor fikri
- Rasmni to'liq AI bilan matnli generatsiya qilish (eski rasm shunday qilingan) kirillda xato harflar beradi. Tavsiya: matnsiz fon + HTML/CSS matn → aniq harflar, brend shriftlari, keyin matnni o'zgartirish 1 buyruq.

## Taxminlar
- Poster tugmasiz, asl o'lcham 1313x1198 saqlanadi.
- Shablon va render skripti `scripts/posters/` da commit qilinadi; `brand/` gitignore'da — poster commitga tushmaydi.

Reja tasdiqlansa: har qabul qilingan qadam alohida commit, push yo'q.
