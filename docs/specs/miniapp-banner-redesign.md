# Mini App: banner PNG hero + yorqin binafsha/oltin redizayn

## Maqsad
Mijoz mini app'ni ochganda birinchi bo'lib tayyor "Quantum Psychology" bannerini ko'radi. Banner ustidagi "BEPUL SUHBATGA YOZILISH" tugmasi bosiladi va ariza formasiga olib boradi. Qolgan sahifa shu bannerdagi kabi yorqin binafsha + oltin uslubda, matnlar tiniq va kontrastli.

## Kontekst
- Loyiha: `webapp/` — statik Telegram Mini App (Vercel). Fayllar: `index.html` (151), `styles.css` (394), `app.js` (323), `i18n.js` (147).
- Hozirgi hero: [index.html:30-39](webapp/index.html#L30-L39) — matn rasmdagi bilan bir xil. CTA `href="#leadForm"`.
- Ariza: `tg.sendData` ([app.js:243-281](webapp/app.js#L243-L281)) — o'zgarmaydi.
- Manba rasm: `C:\Users\user\Downloads\2DDD\Quantum Psychology_ Inner Potential.png` — 1314×1197, 1.9 MB, matn faqat lotinda.
- Rasmdagi tugma koordinatalari: x 322–985, y 873–958 (px) → left 24.5%, top 72.9%, width 50.5%, height 7.1%.
- Testlar: `node --test "webapp/tests/*.test.mjs"` (hero i18n kalitlari testda qotirilgan — `data.test.mjs:64-113`).
- Impeccable: PRODUCT.md/DESIGN.md yo'q. Brief aniq (rasm palitrani pin qiladi) → yo'nalish shu spec'da.

## Chegaralar
- Qilinadi: hero o'rniga banner rasm + bosiladigan zona; butun sahifa ranglari, tipografika va kontrasti redizayn.
- Qilinmaydi: ariza yuborish mantig'i (`sendData`, `validate.js`, `telegram.js`), bot kodi, matn mazmuni, deploy, push.
- Tegilmaydi: `bot/`, `webapp/validate.js`, `webapp/telegram.js`, `webapp/data.js`, shriftlar.

## Dizayn yo'nalishi (impeccable, Persuade rejimi)
- Palitra (rasmdan): fon `#160536`→`#2a0a6b` chuqur binafsha; yorqin binafsha nur `#7b2cf0`/`#9b5cff`; oltin `#ffcf5a`/`#f5b52e`; matn `#ffffff`, ikkilamchi matn `#e4d8ff` (kulrang emas, binafsha tusli).
- Kontrast: oddiy matn ≥7:1, ikkilamchi ≥4.5:1, placeholder ≥4.5:1.
- Tugma: rasmdagidek oltin gradient fon + to'q binafsha `#24074f` qalin matn, yumshoq oltin soya (offset + blur).
- Sarlavhalar: Cormorant Garamond, qattiq oltin rang (gradient-text YO'Q — tiniqlik uchun), Montserrat matn uchun (mavjud woff2).
- Olib tashlanadi (impeccable ban): bo'lim raqamlari 01–07 (`.section__index`), eyebrow.
- Brauzer yuzalari: `::selection`, caret, focus-ring, scrollbar — palitradan.
- Harakat: bitta muallif lahza — banner yuklanganda yumshoq paydo bo'lish (reduced-motion hurmat qilinadi).

## Qabul mezonlari
- [ ] Sahifa tepasida banner rasm to'liq kenglikda, buzilmagan nisbatda — qo'lda 390×844.
- [ ] Banner tugmasi ustidagi zona bosilganda forma (`#leadForm`) ga skroll — qo'lda.
- [ ] Bosiladigan zona balandligi 390px kenglikda ≥44px (zona tugma + "BEPUL dastlabki suhbat" qatorini qamraydi).
- [ ] Zona `<a>` element, `aria-label` = `heroCta` (kirill/lotin), klaviatura focus ko'rinadi.
- [ ] Rasmda `alt` matni (kirill/lotin), sahifada ko'rinmas `h1`.
- [ ] Barcha matn kontrasti ≥4.5:1; bo'lim raqamlari yo'q; impeccable detect toza — `impeccable detect --json webapp/index.html webapp/styles.css`.
- [ ] Ariza menyudan/klaviaturadan yuborish xulqi o'zgarmagan — `node --test "webapp/tests/*.test.mjs"` hammasi o'tadi.
- [ ] Rasm og'irligi ≤400 KB — `ffprobe` + fayl hajmi.

## Chekka holatlar
- Rasm yuklanmasa: `alt` matn + oltin fallback CTA ko'rinadi (zona baribir ishlaydi).
- Kirill rejimida rasm lotinda qoladi (foydalanuvchi tanlovi).
- Takror bosish: oddiy anchor, xavf yo'q.

## To'lqinlar
### To'lqin 1 — umumiy tekshiruv: `node --test "webapp/tests/*.test.mjs"` (parallel)
1. **Banner asset** — fayllar: `webapp/assets/hero-banner.webp` (yangi) — mezon: 1314×1197, WebP q≈90, ≤400 KB, matn tiniq — tekshiruv: `ffprobe` + hajm.
2. **Butun sahifa redizayni (hero'siz)** — fayllar: `webapp/styles.css`, `webapp/index.html` (faqat bo'lim raqamlarini olib tashlash) — mezon: yangi tokenlar, kontrast, tugma, maydonlar, kartalar, brauzer yuzalari — tekshiruv: node test + detect.

### To'lqin 2 (1-to'lqinga bog'liq)
3. **Hero almashtirish** — fayllar: `webapp/index.html`, `webapp/styles.css` (hero qismi), `webapp/i18n.js` (+`heroImageAlt` cyr/lat), `webapp/tests/data.test.mjs` (yangi kalit) — mezon: yuqoridagi hero mezonlari — tekshiruv: node test + Playwright 390×844 skrinshot (mentor ko'radi).

## DB / migratsiya: yo'q

## Foydalanuvchi bajaradigan ishlar
- Vercel'ga deploy (push) — o'zingiz.
- Telefonda tekshirish: botdagi klaviatura tugmasi → mini app → banner tugmasini bosish → forma → yuborish.

## Xavflar
- Banner tugmasi kichik (≈23px balandlik 390px ekranda) — zona kattalashtirilmasa bosish qiyin.
- Kirill foydalanuvchi bannerda lotin matnni ko'radi.

## Mentor fikri
- PNG o'rniga HTML hero tavsiya qilingan edi (kirill, tiniqlik, og'irlik). Foydalanuvchi tanlovi: PNG — qabul qilindi.

## Taxminlar
- PNG → WebP (q≈90) ga o'giriladi, chunki 1.9 MB Telegram ichida sekin yuklanadi; ko'rinish bir xil.
- Eski hero i18n kalitlari o'chirilmaydi (testlar va `document.title` ishlatadi).
- PRODUCT.md (`/impeccable init`) keyinroq taklif qilinadi.

Reja tasdiqlansa: har qabul qilingan qadam alohida commit. Push qilinmaydi.
