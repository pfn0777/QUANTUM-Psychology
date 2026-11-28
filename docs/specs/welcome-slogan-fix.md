# Welcome rasmi: slogan imlosini tuzatish + welcome.html'ni oltin rasmga moslash

## Maqsad
/start bosgan har bir yangi mijoz ko'radigan oltin welcome rasmidagi xato ("имкониятигеизни") yo'qolsin: to'g'risi «Ички имкониятингизни очинг — янги даражага чиқинг». `scripts/posters/welcome.html` esa botdagi rasmning manbai bo'lsin: rasm shu shablondan render qilinadi.

## Kontekst
- Bot: `bot/bot.py:55` → `WELCOME_PHOTO = BOT_DIR / "assets" / "welcome.png"` (kod o'zgarmaydi).
- Joriy rasm: `bot/assets/welcome.png` — foydalanuvchining AI rasmi, PNG 1254x1254, commit 55537f9 (sha256 4bdd3334...). Slogan qatori ~y 685–730.
- Render: `scripts/posters/render.mjs` (headless Chrome, `node scripts/posters/render.mjs <html> <out.png> <w> <h>`).
- Shrift: `webapp/fonts.css` → Cormorant Garamond italic 500–600, kirill bor (rasmdagi slogan shriftiga yaqin).
- `posters.css:4-7`: `.canvas`, `.canvas__bg`, `.canvas::before` (oq radial qatlam — oltin variantda o'chirilishi kerak, aks holda rasm xiralashadi).
- Testlar: `scripts/posters/tests/templates.test.mjs` (welcome va poster matnlari, ruxsat etilgan hex ranglar), `render.test.mjs`.

## Chegaralar
- Qilinadi: oltin rasm manba sifatida `scripts/posters/assets/welcome-gold.png` ga nusxalanadi (bayt-bayt bir xil → git yangi blob yaratmaydi); `welcome.html` = shu rasm fon + slogan qatorini yopuvchi yumshoq qirrali "patch" + to'g'ri slogan HTML matni; `bot/assets/welcome.png` shu shablondan qayta render qilinadi (1254x1254).
- Qilinmaydi: bot kodi, caption, tugmalar; `poster.html` va uning ko'rinishi; rasmning boshqa qismlari; AI bilan qayta generatsiya; push, deploy.
- Tegilmaydi: `docs/mentor/miniapp-brand-redesign.md` (foydalanuvchiniki), `bot/` ichidagi `.py` fayllar.

## Qabul mezonlari
- [ ] `bot/assets/welcome.png` — png 1254x1254 — `ffprobe`
- [ ] Rasmda slogan aynan «Ички имкониятингизни очинг — янги даражага чиқинг», italic serif, rang va o'lcham asl qatorga yaqin; patch chegarasi 100% masshtabda ko'rinmaydi — qo'lda (mentor `Read` bilan ko'radi) + Codex tekshiruvchisi FOCUS: RASM
- [ ] Slogan bandidan tashqarida piksellar asl rasm bilan deyarli bir xil (kanal farqi ≤ 3) — vaqtinchalik diff skripti (scratch, commit qilinmaydi)
- [ ] `templates.test.mjs` yangilangan: welcome → `assets/welcome-gold.png` ga ishora, to'g'ri slogan bor, "имкониятигеизни" yo'q; poster uchun eski tekshiruvlar o'zgarmagan; ruxsat etilgan ranglar ro'yxatidan hech narsa olib tashlanmagan — `node --test scripts/posters/tests`
- [ ] `poster.html` diff'da yo'q; `posters.css` da faqat yangi `.canvas--gold*` qoidalar qo'shilgan
- [ ] `rtk proxy python -m pytest bot/tests` — hammasi o'tadi (oldin 442/442)

## Chekka holatlar
- Shrift yuklanmasa → render.mjs `FONT_WAIT_MS` kutadi; tekshiruvda slogan Cormorant'da ekanini ko'rish.
- Chrome rasmni rang profili bilan o'zgartirsa → diff tekshiruvi buni ushlaydi.
- Marmar teksturada patch dog' bo'lib qolsa → patch fonini o'sha rasmning yaqin toza bandidan olish (`background: url(welcome-gold.png)` + siljitish) va mask bilan qirralarni yumshatish.

## To'lqinlar
### To'lqin 1 — umumiy tekshiruv: `node --test scripts/posters/tests` + `rtk proxy python -m pytest bot/tests`
1. Oltin shablon + tuzatilgan rasm — fayllar: `scripts/posters/assets/welcome-gold.png` (yangi), `scripts/posters/welcome.html`, `scripts/posters/posters.css`, `scripts/posters/tests/templates.test.mjs`, `bot/assets/welcome.png` — tekshiruv: yuqoridagi mezonlar. (5 fayl → Codex tekshiruvchisi ishlaydi.)

Bitta to'lqin, bitta qadam: hamma fayllar zanjir (render shablonga bog'liq), parallellik foyda bermaydi.

## DB / migratsiya: yo'q

## Foydalanuvchi bajaradigan ishlar
- Push, keyin Hetzner'da botni yangilash (rasm fayli almashadi, restart kerak bo'lishi mumkin).
- Telegram'da /start bosib, slogan to'g'riligini ko'rish.

## Xavflar
- Patch ko'zga tashlansa — mentor ko'rib qabul qilmaydi, qayta beriladi.
- Rasm hajmi ~2.3 MB qoladi (oldin ham shunday edi, foydalanuvchi tanlovi PNG).

## Taxminlar
- Slogan rangi/o'lchami asl qatordan ko'z bilan olinadi; ruxsat etilgan palitradagi eng yaqin rang ishlatiladi.
- Eski ivory welcome dizayni git tarixida qoladi (commit 2ffd880), alohida fayl sifatida saqlanmaydi — foydalanuvchi tanlovi.
