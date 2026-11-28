# Mini App: welcome uslubidagi premium oltin hero + oltin sarlavhalar

## Maqsad
Mini app'ni ochgan mijoz birinchi ekranda /start welcome rasmidagidek (`scripts/posters/assets/welcome-gold.png`) dabdabali, 3D metall oltin brendni ko'rsin. Bo'lim sarlavhalari ham shu oltin uslubda bo'lsin.

## Kontekst
- Sahifa: `webapp/index.html` (hero: qator 28–45), `webapp/styles.css` (451 qator; hero: 113–198, tugmalar: 212–239, `.section h2`: 242–247, `.section--feature h2`: 305, media: 429–451).
- Tokenlar `styles.css:3-29` (`--gold #C9A050`, `--gold-light #F1D79A`, `--chocolate #3B2112`, `--bronze #8C6420`, `--cocoa #5A3620`, `--dark #2A170B`, `--ivory`, `--marble`, `--champagne`, `--border-gold #D9B66E`).
- Fon: `webapp/assets/hero-bg.webp` (1024x1536, marmar + oltin lentalar + nur + lotus) — o'zgarmaydi. Hozir uni `.hero::before` dagi oq radial qatlam (`.93 → .75 → .32`) yuvib yuboryapti.
- Hozirgi sarlavha: `.hero__title-main` — yassi `#AD7F32 → #7A5518` gradient, `background-clip: text`. `.hero__title-sub` — oddiy bronza rang.
- Ikonkalar: `.hero__icon` — fil suyagi doira, SVG `stroke="#8C6420"` (HTML atributi; CSS `stroke` xossasi uni bosib o'tadi).
- Shriftlar: `webapp/fonts.css` — Cormorant Garamond 500–700 + italic, Montserrat 400–800 (kirill bor).
- Testlar: `node --test "webapp/tests/*.test.mjs"` (56/56). `data.test.mjs:210-226` hero tuzilishini tekshiradi: `img.hero__bg src="assets/hero-bg.webp" alt=""`, `<h1 id="heroTitle">…QUANTUM…Psychology…</h1>`, `<a class="button button--primary hero__cta" href="#leadForm">`, `data-i18n="heroBenefit1..3"`.
- Namuna: welcome rasmi — bo'rtiq 3D oltin harflar (och sariq yaltiroq → oltin → to'q bronza qirra), yorqin nur, oltin ramka, shokolad medalyonli oltin ikonkalar, yaltiroq shokolad CTA oltin qirrali.

## Chegaralar
- Qilinadi:
  - "QUANTUM" — 3D metall oltin: ko'p stopli gradient (och krem-sariq yaltiroq → oltin → to'q bronza → yaltiroq → bronza), orqada to'q jigarrang "ekstruziya" qatlami (pseudo-element yoki `data-text`), tashqi iliq nur (`drop-shadow`), bir martalik yaltiroq yugurishi (shimmer).
  - "Psychology" — shu oltin uslubning italic, yengilroq varianti (to'q qirra bilan).
  - `.hero::before` oq qatlami yengillashadi — lentalar va nur ko'rinadi, lekin matn markazi o'qiladigan bo'lib qoladi.
  - Hero oltin ramka (gradient chegara + ichki nozik chiziq), welcome'dagi oltin ramkaga o'xshash.
  - `.hero__icon` — shokolad medalyon (radial gradient), oltin gradient halqa, oltin glif (CSS `stroke`).
  - `.hero__cta` — yaltiroq shokolad, oltin gradient qirra, yengil oltin nur; matn `--gold-light`.
  - `.hero__eyebrow` yorlig'i va `.hero__divider` — oltin gradient bilan boyitiladi.
  - `.section h2` — metall oltin gradient matn (to'q bronzaga yaqin, o'qiladigan); `.section--feature h2` — to'q fonda yorqin oltin variant.
  - `prefers-reduced-motion: reduce` — shimmer va kirish animatsiyasi o'chadi.
- Qilinmaydi: matn mazmuni, forma va maydonlar, `app.js`, `i18n.js`, `data.js`, `validate.js`, `telegram.js`, yangi rasm/AI generatsiya, bot, push, deploy.
- Tegilmaydi: `webapp/assets/*`, `webapp/tests/*` (testlar o'zgarishsiz o'tishi kerak), `bot/`, `scripts/`.

## Qabul mezonlari
- [ ] `node --test "webapp/tests/*.test.mjs"` — 56/56 (yoki hozirgi jami) o'tadi.
- [ ] O'zgargan fayllar faqat `webapp/styles.css` va (kerak bo'lsa) `webapp/index.html` — `git diff --stat`.
- [ ] Skrinshot 390x844 (cyr) va 360x740 (lat yoki cyr): "QUANTUM" 3D oltin, to'q qirrali, fonda aniq o'qiladi; lentalar/nur ko'rinadi; ramka, medalyon ikonkalar, CTA welcome uslubida.
- [ ] Gorizontal skroll yo'q; "QUANTUM" 360px kenglikda kesilmaydi va qatorga bo'linmaydi.
- [ ] `prefers-reduced-motion: reduce` blokida yangi animatsiyalar o'chirilgan.
- [ ] Yangi magic ranglar — iloji boricha `:root` tokenlari orqali (yangi tokenlar qo'shish mumkin, masalan `--gold-shine`, `--gold-deep`).
- [ ] Oddiy matn kontrasti (subtitle, benefits, offer) hozirgidan pasaymaydi.

## Chekka holatlar
- Shrift kech yuklansa — fallback serif'da ham bo'rtiq effekt buzilmaydi (ekstruziya qatlami matn bilan bir xil shriftda).
- Kichik ekran (360px) — sarlavha o'lchami `clamp` bilan kichrayadi, `letter-spacing` kesilishga olib kelmaydi.
- Telegram WebView (Android Chrome, iOS WebKit) — `-webkit-background-clip: text` va `-webkit-text-fill-color` saqlanadi.

## Tekshiruv
- `node --test "webapp/tests/*.test.mjs"`
- Skrinshot: headless Chrome (`scripts/posters/render.mjs webapp/index.html <out.png> 390 844` yoki lokal `npx http-server webapp` + headless Chrome). Skrinshotlar faqat scratch papkaga, commit qilinmaydi.
