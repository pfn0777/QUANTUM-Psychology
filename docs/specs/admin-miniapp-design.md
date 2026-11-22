# Admin Mini App — dizayn brifi

Spec: `docs/specs/admin-miniapp.md` (API kontrakti, holatlar, chegaralar). Bu fayl faqat ko'rinish va xatti-harakatni belgilaydi.
5-qadam (frontend) shu brif bo'yicha yoziladi. Brif matnini kod izohiga, HTML'ga yoki tashqariga beriladigan faylga ko'chirmang.

## Rejim va taxminlar
- Rejim: **Operate** (vazifa bajariladigan ekran). Bezak emas — tez o'qiladigan sonlar, ishonchli ro'yxat.
- PRODUCT.md yo'q. Quyidagilar taxmin (foydalanuvchi tasdiqlamagan):
  - Foydalanuvchi: loyiha egasi va 1–2 ishonchli ko'ruvchi. Telefonda, Telegram ichida, kuniga bir necha marta ochadi.
  - Asosiy ishlar: (1) "bugun nechta odam keldi, nechtasi ariza qoldirdi?" (2) "kim ariza yubordi — qo'ng'iroq qilay" (3) "qaysi manba ishlayapti?" (4) CSV'ni chatga olish.
- Vizual dunyo **mavjud** — mijoz Mini App'i (`webapp/styles.css`). Yangi dunyo ixtiro qilinmaydi, o'sha brend Operate registrida ishlatiladi.

## Direction contract
- THESIS: Bitta qarashda "bugun nima bo'ldi" — sonlar birinchi, bezak oxirgi. Odatiy "admin shablon" (oq fon, ko'k sidebar, 12 ta bir xil kartochka) rad etiladi; o'rniga brendning to'q binafsha muhiti, oltin rang faqat ariza va asosiy harakat uchun.
- OWN-WORLD: To'q binafsha yer (`#160536`), bo'limlar `--surface`, plitkalar `--surface-raised`. Ikki ma'lumot rangi: lavanda = foydalanuvchilar, oltin = arizalar. Montserrat tabular raqamlar. Kontentsiz ham taniladi: binafsha ustida oltin ustunlar va oltin "Ариза бор" belgisi.
- STORY: Ochadi → 4 ta katta son va bugungi qator → grafikda trend → "Аризалар" tabida yangi arizani topib, telefonga bosadi → kerak bo'lsa CSV'ni chatga oladi.
- FIRST VIEWPORT (360×640): tepada 56px header (wordmark + "Янгиланди 14:05" + yangilash tugmasi), ostida 44px segment tablar, keyin 2×2 KPI plitkalar, keyin "Бугун / 7 кун / 30 кун" jadvali — hammasi birinchi ekranda. Grafik birinchi ekran pastidan boshlanadi.
- FORM: Bitta sahifa, 3 ta tab (Умумий / Аризалар / Фойдаланувчилар). seed: none (pinned) — "admin panelga mini app qil statistika vizual ko'rish uchun va mijozlarni statistikasni bilish uchun".
- FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Tokenlar
`webapp/styles.css:1-17` dagi tokenlar **aynan** ko'chiriladi (`bot/admin_webapp/styles.css` ichida, import emas — ular alohida serverda turadi). Qo'shimcha tokenlar:

| Token | Qiymat | Vazifa |
|---|---|---|
| `--series-users` | `var(--lavender)` | foydalanuvchi ustunlari, manba chizig'i |
| `--series-leads` | `var(--gold)` | ariza ustunlari, "Ариза бор" |
| `--grid` | `rgba(228,216,255,.12)` | grafik tayanch chizig'i, ro'yxat ajratgichi |
| `--focus` | `var(--gold-light)` | focus-visible halqa |
| `--skeleton` | `rgba(155,92,255,.18)` | skeleton bloklar |

- Fon: `body` uchun tekis `--background` (mijoz app'idagi gradient emas — uzun ro'yxatda tekis fon tinchroq).
- Lavanda kichik matn uchun ishlatilmaydi (kontrast yetmaydi). Matn faqat `--text`, `--muted`, `--gold`, `--gold-light`, `--error`.
- Ranglar strategiyasi: Restrained. Oltin faqat: ariza qiymatlari, asosiy tugma, tanlangan tab indikatori, focus. Boshqa joyda oltin yo'q.

## Tipografiya
- Hamma UI va raqamlar: **Montserrat** (`webapp/fonts/montserrat-400-800-*.woff2`, server `/admin/fonts/` da beradi; CSS'da nisbiy yo'l `fonts/...`). `font-display: swap`.
- Cormorant Garamond — faqat wordmark'dagi "QUANTUM" so'zi (latin fayl). Sarlavha, label, tugmada Cormorant yo'q.
- O'lchamlar (rem, fluid emas): 12 / 14 / 16 / 20 / 28px.
  - 12px 500 `--muted` — label, meta, o'q yozuvlari.
  - 14px 400/600 — ro'yxat matni, tugmalar, jadval.
  - 16px 600 — bo'lim sarlavhalari.
  - 20px 700 — jadval raqamlari.
  - 28px 700 — KPI raqamlari.
- Hamma raqamlarda `font-variant-numeric: tabular-nums`.
- Raqam formati: minglik ajratgich — ingichka bo'sh joy (`1 234`), o'nlik — vergul (`12,5%`). Konversiya `null` → `—`.

## Layout
- Kenglik: `width: min(100%, 720px)`, markazda. Yon bo'shliq 16px. `padding` da `env(safe-area-inset-*)`.
- Oraliq ritmi: 4px asos; bo'lim ichida 16px, bo'limlar orasida 24px. Sarlavha ustida pastidan ko'proq joy.
- Radiuslar: plitka va input — 14px (`--field-radius`), bo'lim — 20px (`--block-radius`). Ichma-ich kartochka yo'q: ro'yxat qatorlari bo'lim ichida ajratgich bilan, alohida kartochka emas.
- Telegram: `Telegram.WebApp.ready()`, `expand()`, `setHeaderColor('#160536')`, `setBackgroundColor('#160536')`. Telegram mavzusi (light) e'tiborsiz — panel har doim to'q.

### Header (56px)
- Chapda: kichik wordmark — "QUANTUM" (Cormorant 600, `--gold-light`, harf oralig'i .18em) va pastida "Статистика" (12px `--muted`).
- O'ngda: "Янгиланди 14:05" (12px `--muted`, `generated_at` Toshkent vaqtida) va yangilash ikon-tugmasi (44×44, `aria-label="Янгилаш"`, inline SVG aylana-strelka).
- Yangilashda eski ma'lumot ko'rinib turadi, faqat ikon aylanadi va tugma `disabled`. Skeleton qayta chiqmaydi.

### Tablar (44px, sticky top)
- Segment control: "Умумий", "Аризалар", "Фойдаланувчилар". `role="tablist"`, strelka tugmalari bilan o'tish.
- Aktiv tab: `--surface-raised` fon + pastda 2px oltin chiziq. Noaktiv: `--muted` matn, fonsiz.
- Sticky, fon `--background`, scroll paytida kontent ustida qoladi.
- Oxirgi tab `sessionStorage` da eslab qolinadi (faqat tab nomi; try/catch, xatoda `console.warn`).

### "Умумий" tab
1. **KPI 2×2** (≥600px da 4 ustun). Har plitka: label (12px muted) tepada, raqam (28px 700) pastda, balandligi bir xil.
   - "Жами фойдаланувчилар" → `totals.users`
   - "Ариза қолдирганлар" → `totals.lead_users` (raqam oltin)
   - "Конверсия" → `totals.conversion_pct` + `%` yoki `—`
   - "Фаол, 7 кун" → `totals.active_7d`
2. **Davr jadvali** (bitta bo'lim, 3 qator × 2 ustun):
   - Sarlavha: "Давр" | "Янги фойдаланувчи" | "Ариза".
   - Qatorlar: "Бугун" (users_today, leads_today), "7 кун", "30 кун". Ariza ustuni raqamlari oltin, "Бугун" qatori 20px, qolganlari 16px.
3. **Yetkazilmagan ogohlantirish** — faqat `undelivered > 0`: bo'lim ustida 1 qatorli banner, chapda 3px `--error` chiziq, matn "{n} та ариза админ чатга етказилмаган". 0 bo'lsa umuman chiqmaydi.
4. **Grafik "30 кунлик динамика"** (pastda batafsil).
5. **Manbalar "Манбалар (30 кун)"** (pastda batafsil).

### "Аризалар" tab
- Tab ostida sticky qidiruv qatori: input (44px, placeholder "Исм, телефон ёки username", ichida qidiruv ikoni, tozalash ×) va o'ngda soni "{n} та".
- Ro'yxat (eng yangisi tepada). Har qator:
  - 1-qator: ism (14px 600, `--text`) chapda; sana "22.11 14:05" (12px muted) o'ngda.
  - 2-qator: telefon — `tel:` havola, oltin, tabular; username — `@name`, `Telegram.WebApp.openTelegramLink('https://t.me/name')` bilan ochiladi. Username yo'q bo'lsa — hech narsa yozilmaydi.
  - 3-qator (12px muted): manba chipi ("Instagram" va h.k., 1px `--border`, radius 999px) · hudud · yosh.
  - 4-qator: mavzular (`topics`), 12px, 2 qatordan keyin `line-clamp`; qatorga bosilsa to'liq ochiladi (`aria-expanded`).
  - Qator balandligi kamida 64px, ajratgich 1px `--grid`.
- Ro'yxat ostida: `length === 200` bo'lsa "Охирги 200 таси кўрсатилмоқда. Тўлиқ рўйхат — CSV файлда."
- Eng pastda asosiy tugma: "Аризалар CSV — чатга юбориш" (pastda "Eksport").

### "Фойдаланувчилар" tab
- Xuddi shu qidiruv qatori.
- Qator: to'liq ism (14px 600) · o'ngda `has_lead` bo'lsa oltin belgi "Ариза бор" (oltin chegarali chip, oltin matn).
  - 2-qator: `@username` (yoki hech narsa) · manba chipi.
  - 3-qator (12px muted): "Биринчи: 20.11 09:12 · Охирги: 22.11 14:05".
- Limit izohi va "Фойдаланувчилар CSV — чатга юбориш" tugmasi.

## Grafik (inline SVG, kutubxonasiz)
- Ikki **alohida** ustunli grafik ustma-ust, x o'qi umumiy: tepada "Фойдаланувчилар" (lavanda), pastda "Аризалар" (oltin). Ikki o'qli bitta grafik qilinmaydi — miqyoslar har xil.
- Har biri: `viewBox="0 0 300 96"`, `width: 100%`, balandligi 96px. 30 ustun, ustun kengligi 300/30 minus 2px oraliq, uchi 2px radius.
- Har grafikning y-maksimumi o'zining eng katta qiymati. Chapda tepada kichik yozuv "макс {n}" (12px muted). Grid chiziqlari yo'q, faqat 0 tayanch chizig'i (`--grid`).
- X yozuvlari (faqat pastki grafik ostida): birinchi kun, o'rta kun, "Бугун". Format "dd.mm".
- O'qish qatori (grafiklar ustida, 14px): standart holatda "30 кунда: {u} фойдаланувчи · {l} ариза". Ustunga bosilganda (yoki strelka bilan) o'sha kun ikkala grafikda ajratiladi (boshqa ustunlar 40% shaffof), qator "{dd.mm}: {u} фойдаланувчи · {l} ариза" bo'ladi. Qayta bosish yoki tashqariga bosish — standart holatga qaytadi.
- 0 qiymatli kun: ustun chizilmaydi, faqat tayanch chiziq.
- Hamma qiymat 0 bo'lsa: grafiklar o'rniga bitta yozuv "30 кунда ҳали маълумот йўқ".
- Legend alohida chiqmaydi — har grafikning sarlavhasi uning legend'i (rangli 8px kvadrat + nom).
- A11y: `role="img"` va `aria-label` = standart o'qish qatori matni. Bosish uchun shaffof `<rect>` ustunlar, butun ustun balandligi bo'yicha (nishon kamida 10px keng — 360px ekranda 30 ustun sig'adi).

## Manbalar
- Bo'lim ichida har manba bitta qator, `users` bo'yicha kamayish tartibida:
  - Chapda nom (14px 600), o'ngda "{users} · {leads} · {conv}%" (12px, ariza oltin).
  - Ostida ikki ingichka chiziq (6px, radius 3px): lavanda — users, oltin — leads. Ikkalasi bir miqyosda (hamma manbalardagi eng katta qiymat).
- Konversiya manba uchun frontendda hisoblanadi: `users > 0` bo'lsa `round(leads/users*100)`, aks holda `—`.
- Manba yo'q bo'lsa: "Ҳали манба маълумоти йўқ".

## Eksport
- Tugma: to'liq kenglik, 48px, oltin fon (`--gold`), to'q matn `#24074f`, 600. Holatlar: hover/active — `--gold-deep`; focus — 2px `--focus` halqa + 2px offset; disabled — 50% shaffof.
- Bosilganda: tugma `disabled`, matn "Юборилмоқда…". Natija tugma ostidagi status qatorida (`aria-live="polite"`), 4 soniyadan keyin yo'qoladi:
  - 200 → "Файл чатга юборилди" (`--gold-light`) + `Telegram.WebApp.HapticFeedback.notificationOccurred('success')`.
  - 429 → "Бир оз кутинг ва қайта босинг".
  - 502 → "Юбориб бўлмади. Аввал ботга /start ёзинг".
  - boshqa → "Хатолик юз берди. Қайта уриниб кўринг".
  - Xato matnlari `--error`.
- Modal yo'q, toast ham yo'q — status tugma yonida.

## Holatlar (to'liq ekran holatlari tablar o'rnida chiqadi)
| Holat | Qachon | Sarlavha | Matn | Harakat |
|---|---|---|---|---|
| Yuklanmoqda | birinchi so'rov | — | skeleton: 4 plitka, jadval, grafik bloki; `aria-busy="true"`, sr-only "Юкланмоқда" | — |
| Telegram'dan tashqari | `initData` bo'sh yoki 401 `unauthorized` | "Панел фақат Telegram ичида очилади" | "Ботдаги /admin тугмаси орқали очинг." | — |
| Muddati o'tgan | 401 `expired` | "Сессия муддати тугади" | "Панелни ёпиб, қайта очинг." | "Ёпиш" → `Telegram.WebApp.close()` |
| Ruxsat yo'q | 403 | "Рухсат йўқ" | "Бу панел фақат статистика кўрувчилар учун. Админга мурожаат қилинг." | — |
| Xato | tarmoq, 500, buzuq JSON | "Маълумотни юклаб бўлмади" | "Интернетни текширинг ва қайта уриниб кўринг." | "Қайта уриниш" |
| Bo'sh baza | `users == 0` | KPI'lar 0, konversiya "—", grafik bo'sh yozuvi | Ro'yxatlarda: | |
| | Аризалар bo'sh | — | "Ҳали ариза йўқ. Мижозлар Mini App орқали ариза юборганда шу ерда кўринади." | — |
| | Фойдаланувчилар bo'sh | — | "Ҳали ҳеч ким ботга кирмаган. /start босганлар шу ерда кўринади." | — |
| Qidiruv natijasiz | filter bo'sh | — | "Ҳеч нарса топилмади" | "Тозалаш" |

- To'liq ekran holati: markazda, max 320px, 48px ikon (inline SVG, chiziqli, `--lavender`), sarlavha 16px 600, matn 14px muted, tugma — ikkinchi darajali (1px `--border`, shaffof fon, 44px).
- Yangilash paytidagi xato: eski ma'lumot qoladi, header ostida 1 qatorli `--error` yozuv "Янгилаб бўлмади" (keyingi muvaffaqiyatli yangilashda yo'qoladi). 401/403 esa har doim to'liq ekran holatiga o'tadi.

## Qidiruv mantig'i (`format.js`, test qilinadi)
- Katta-kichik harf farqsiz; kirill va lotin aralash ism bo'lishi mumkin — oddiy `toLowerCase()` yetadi.
- Telefon: so'rov va telefondagi raqam bo'lmagan belgilar olib tashlanib solishtiriladi ("90 123" → "90123" topadi).
- Username: boshidagi `@` e'tiborsiz.
- Ism, telefon, username (arizada yana hudud) bo'yicha. Debounce 150ms.

## Format qoidalari (`format.js`)
- Vaqt: backend UTC ISO beradi → Toshkent vaqti **qat'iy +5 soat** (backend bilan bir xil; `Intl` timezone'iga tayanmaslik). Ro'yxatda "dd.mm HH:MM", grafikda "dd.mm", header'da "HH:MM".
- Raqam: `1 234` (U+2009), foiz: `12,5%` yoki butun bo'lsa `12%`.
- Xavfsizlik: hamma ma'lumot `textContent` / `createElement` bilan qo'yiladi. Ma'lumot bilan `innerHTML` yo'q. `escapeHtml` funksiyasi baribir bo'ladi va test qilinadi (preview va kerak bo'lgan joylar uchun).
- Username havolasi faqat `^[A-Za-z0-9_]{5,32}$` ga mos bo'lsa yaratiladi, aks holda oddiy matn.
- Telefon `tel:` havolasi faqat raqam va `+` dan tuzilgan qiymat bilan.
- Shaxsiy ma'lumot `localStorage`/`sessionStorage` ga yozilmaydi.

## Harakat (motion)
- Faqat holat o'zgarishi: tab almashinuvi 150ms opacity, tugma bosilishi 100ms, ustun tanlanishi 150ms opacity, yangilash ikoni aylanishi.
- Sahifa yuklanishida xoreografiya yo'q.
- Skeleton yengil pulse (1.2s). `prefers-reduced-motion: reduce` da hamma animatsiya o'chadi.

## A11y va interaksiya
- Hamma bosiladigan nishon ≥44×44px.
- `:focus-visible` — 2px `--focus` halqa, 2px offset. Hover faqat `@media (hover: hover)` ichida.
- Kontrast: matn ≥4.5:1 (`--muted` `--surface` ustida — tekshirilgan juft), grafik ustunlari ≥3:1.
- `lang="uz-Cyrl"`. Sahifa sarlavhasi `<title>Статистика</title>`.
- 320px kenglikda gorizontal scroll yo'q; uzun ism `overflow-wrap: anywhere`.

## Fayllar va tuzilma (5-qadam uchun)
- `index.html` — skelet: header, tablist, 3 ta tabpanel, holat konteyneri. `<script src="https://telegram.org/js/telegram-web-app.js">` (CSP ruxsat bergan yagona tashqi skript), keyin `format.js`, `app.js` (`type="module"`).
- `format.js` — sof funksiyalar (eksport qilinadi): `formatNumber`, `formatPercent`, `formatTashkent(iso, kind)`, `escapeHtml`, `matchLead(row, q)`, `matchUser(row, q)`, `sourceConversion(users, leads)`, `chartGeometry(daily, width, height)`.
- `app.js` — `fetch` (`Authorization: tma <initData>`), holat mashinasi, `render(data)` (alohida eksport — preview fixture bilan chaqiradi).
- `styles.css` — tokenlar + komponentlar.
- `tests/format.test.mjs` — format, qidiruv, escape, grafik geometriyasi (bo'sh kunlar, hammasi 0, maksimum).
- `tests/preview.html` — **sintetik** fixture bilan `render()` chaqiradi. `?state=loading|outside|expired|forbidden|error|empty|full` parametri bilan har holatni ko'rsatadi. Fixture: 30 kun (orasida 0 kunlar), 200 ta ariza va 180 ta user, `<script>alert(1)</script>` ismli qator, `=cmd` ismli qator, username'siz qator, 40 belgili uzun ism, 4 ta manba (biri `null` → "Тўғридан-тўғри"), `undelivered: 2`. Fixture'dagi ism/telefonlar ochiq-oydin soxta bo'lsin ("Тест Мижоз 1", `+998 90 000 00 01`).

## Vizual ko'rik (4-to'lqin) mezonlari
- 360×640 va 1024×768 skrinshotlar: `?state=full` uchala tab, `empty`, `expired`, `error`.
- Tekshiriladi: birinchi ekranda KPI + davr jadvali ko'rinadi; grafik 360px da ustunlar ajralib turadi; ro'yxatda kesilish yoki ustma-ust tushish yo'q; oltin faqat ruxsat etilgan joylarda; `<script>` ismi matn bo'lib ko'rinadi.
