# Spec: QUANTUM Psychology — Telegram bot + Mini App (lead capture)

Status: approved 2026-11-20. Executor: Codex workers (via boshqaruvchi).

## 1. Goal
A client opens the Mini App from the bot, browses the 12 course modules (brand style), and leaves a request for a **free initial consultation** («бепул дастлабки суҳбат»). The request is saved to SQLite and sent to the admin chat. The admin calls the client back.
Secondary goal: collect lead source (deep link) and demographics; admin sees them via `/stats`.

## 2. Out of scope
Payments/price, Russian language, user cabinet/lessons/bottom nav, «Совға»/«3 кун» screens, web admin, AI-generated images, deploy.

## 3. Do not touch (read-only, never commit)
`brand/`, `Kurs modullari.txt`, `telegram post.txt`, `instagram-audience-report.md`, `telegram-audience-report.md`, `Screenshot_*.png`.

## 4. Environment
- Windows 11, PowerShell. Python: **`py -3.11`** (aiogram 3.13.1, aiosqlite 0.20.0, python-dotenv 1.0.1 already installed; pytest must be installed via requirements). Node v26 (`node --test`).
- All test commands run from repo root: `py -3.11 -m pytest -q`, `node --test webapp/tests/`.
- Reference pattern (read-only): `C:\Users\user\.claude\skills\hotel-miniapp\templates\` (`bot/bot.py`, `bot/test_rooms_sync.py`, `webapp/app.js`, `deploy/*`).

## 5. Layout
```
.gitignore
pytest.ini                       # testpaths = bot/tests, asyncio_mode = auto, pythonpath = bot
bot/requirements.txt             # aiogram>=3.13,<4  aiosqlite  python-dotenv  pytest  pytest-asyncio
bot/catalog.py                   # codes + labels (cyr/lat) + limits
bot/texts.py                     # client-facing bot messages (cyr/lat)
bot/storage.py                   # aiosqlite storage
bot/leads.py                     # payload validation + admin message render
bot/stats.py                     # /stats text builder
bot/bot.py                       # aiogram handlers, main()
bot/.env.example
bot/data/                        # leads.db lives here (gitignored)
bot/tests/conftest.py, test_*.py
scripts/extract_brand_assets.py
webapp/package.json              # {"type":"module","private":true} — lets node --test import webapp/*.js as ESM
webapp/index.html, styles.css, app.js
webapp/data.js, i18n.js, validate.js   # ES modules
webapp/fonts.css, webapp/fonts/*.woff2, webapp/assets/*.svg
webapp/tests/*.test.mjs
deploy/quantum-bot.service
vercel.json, README.md
```

## 6. Catalog (single source of truth; bot `catalog.py` and webapp `data.js` MUST match codes, order and labels)
Scripts: `cyr`, `lat`. Latin = official Uzbek Latin alphabet (oʻ, gʻ with U+02BB `ʻ`, tutuq belgisi U+02BC `ʼ`), e.g. «Ҳаёт қонуниятлари» → «Hayot qonuniyatlari».

**REGIONS** (order as listed):
| code | cyr | lat |
|---|---|---|
| tashkent_city | Тошкент шаҳри | Toshkent shahri |
| tashkent_region | Тошкент вилояти | Toshkent viloyati |
| andijan | Андижон | Andijon |
| bukhara | Бухоро | Buxoro |
| fergana | Фарғона | Fargʻona |
| jizzakh | Жиззах | Jizzax |
| kashkadarya | Қашқадарё | Qashqadaryo |
| navoi | Навоий | Navoiy |
| namangan | Наманган | Namangan |
| samarkand | Самарқанд | Samarqand |
| surkhandarya | Сурхондарё | Surxondaryo |
| syrdarya | Сирдарё | Sirdaryo |
| khorezm | Хоразм | Xorazm |
| karakalpakstan | Қорақалпоғистон Республикаси | Qoraqalpogʻiston Respublikasi |
| abroad | Хорижда | Xorijda |

**TOPICS** (code → label → related modules):
| code | cyr | lat | modules |
|---|---|---|---|
| family | Оила ва муносабатлар | Oila va munosabatlar | 3, 10 |
| parents | Ота-она ва ўтмиш | Ota-ona va oʻtmish | 3, 4 |
| fear | Қўрқув ва хавотир | Qoʻrquv va xavotir | 1, 4 |
| money | Пул ва даромад | Pul va daromad | 6, 9 |
| health | Соғлиқ ва тана | Sogʻliq va tana | 8 |
| selfworth | Ўз қадри ва чегаралар | Oʻz qadri va chegaralar | 2, 11 |
| support | Ички таянч | Ichki tayanch | 1, 11 |
| fatigue | Чарчоқ | Charchoq | 1, 8 |

**PRIOR**: `no` Йўқ / Yoʻq · `finished` Ҳа, тугатдим / Ha, tugatdim · `stopped` Ҳа, лекин давом эттиролмадим / Ha, lekin davom ettirolmadim
**CALL_TIMES**: `morning` Эрталаб (9:00–12:00) / Ertalab (9:00–12:00) · `day` Кундузи (12:00–17:00) / Kunduzi (12:00–17:00) · `evening` Кечқурун (17:00–21:00) / Kechqurun (17:00–21:00)
**SOURCES**: `ig` Instagram · `tg` Telegram · `yt` YouTube · `friend` Танишлар орқали / Tanishlar orqali · `other` Бошқа / Boshqa
Deep-link sources (accepted in `/start <param>` and `?src=`): `ig`, `tg`, `yt` only.

**LIMITS**: NAME_MIN=2, NAME_MAX=80, AGE_MIN=18, AGE_MAX=99, PHONE_MIN_DIGITS=9, PHONE_MAX_DIGITS=15, COMMENT_MAX=500, PAYLOAD_MAX_BYTES=4096, COOLDOWN_SECONDS=30, RETRY_INTERVAL_SECONDS=300.

## 7. Payload (Mini App → bot via `Telegram.WebApp.sendData`)
JSON object, UTF-8, ≤ 4096 bytes:
```json
{"v":1,"name":"Азиза Каримова","age":34,"phone":"+998901234567","region":"tashkent_city",
 "topics":["family","fear"],"prior":"no","call_time":"evening","source":"ig",
 "comment":"…","consent":true,"script":"cyr"}
```
Rules (bot is authoritative, webapp mirrors):
- `name`: string, trimmed, internal whitespace collapsed, length NAME_MIN..NAME_MAX, allowed chars = Cyrillic letters (incl. ўқғҳ), Latin letters, `ʻ ‘ ’ ' ʼ`, `-`, space. At least 2 letters.
- `age`: int (or digit-only string) in AGE_MIN..AGE_MAX; bool rejected.
- `phone`: keep digits (and leading `+`); digits count PHONE_MIN_DIGITS..PHONE_MAX_DIGITS. Normalised as `+<digits>` if 12 digits starting `998`, else as entered digits with `+` if originally present.
- `region`, `prior`, `call_time`, `source`: must be catalog codes.
- `topics`: non-empty list of unique catalog codes (duplicates removed, order kept), max = number of topics.
- `comment`: optional string, trimmed, truncated to COMMENT_MAX (not rejected).
- `consent`: must be exactly `true`.
- `script`: `cyr` | `lat`; anything else → `cyr`.
- Unknown extra keys are ignored. Non-JSON / non-object → reject with `invalid_payload`.
Error keys (used in `texts.py` and `i18n.js`): `invalid_payload, err_name, err_age, err_phone, err_region, err_topics, err_prior, err_call_time, err_source, err_consent`.

## 8. Module contracts (Python)
- `catalog.py`: ordered dicts `REGIONS, TOPICS, PRIOR, CALL_TIMES, SOURCES: dict[str, dict[str, str]]` (code → {"cyr","lat"}); `TOPIC_MODULES: dict[str, tuple[int, ...]]`; `DEEP_LINK_SOURCES = ("ig","tg","yt")`; `SCRIPTS = ("cyr","lat")`; limit constants from §6; `label(table, code, script="cyr") -> str` (KeyError-safe: returns code if unknown).
- `texts.py`: `TEXTS: dict[str, dict[str, str]]` with keys `"cyr"`, `"lat"` holding identical key sets; `t(key: str, script: str = "cyr", **fmt) -> str` (falls back to cyr). Keys at least: `start_greeting, open_button, thanks, cooldown, server_error` + all error keys from §7. Tone: «Сиз», warm, no emoji, no guarantees, no CAPS.
- `storage.py`: `class Storage(path: str | Path)`: `async init()` (creates parent dir + `CREATE TABLE IF NOT EXISTS leads`), `async save(lead: dict) -> int`, `async mark_delivered(lead_id: int)`, `async undelivered(limit: int = 50) -> list[dict]`, `async rows_since(since: datetime) -> list[dict]`, `async all_rows() -> list[dict]`, `async export_csv(labels: Mapping[str, Mapping[str, str]] | None = None) -> bytes`, `async close()`. Columns: `id, created_at (ISO-8601 UTC), tg_user_id, tg_username, tg_full_name, name, age, phone, region, topics (JSON list), prior, call_time, source, comment, script, delivered (0/1)`. Returned dicts have `topics` as list. CSV: UTF-8 with BOM, `;`-free standard comma CSV via `csv` module, topics joined with `, `; `labels` maps column → {code → label} to show human labels; CSV-injection guard: cell starting with `= + - @ \t \r` gets `'` prefix. aiosqlite only, no sync IO. Parameterised SQL only.
- `leads.py`: `@dataclass(frozen=True) Lead` (fields of §7 after normalisation, without `v`/`consent`); `@dataclass(frozen=True) Rejected(error_key: str, script: str)`; `parse_payload(raw: str) -> Lead | Rejected`; `lead_to_row(lead, user) -> dict` (user = object with `id, username, full_name`); `render_admin(row: dict, now_utc: datetime) -> str` — Cyrillic HTML (aiogram ParseMode.HTML), every user value `html.escape`d, includes: header «Янги ариза — бепул суҳбат», name, age, phone, region label, topic labels, prior label, call-time label, source label, comment (if any), Telegram link `<a href="tg://user?id=ID">…</a>` (+ `@username` if any), time in Tashkent (UTC+5) `dd.mm.yyyy HH:MM`, lead id.
- `stats.py`: `age_bucket(age) -> str` (`18–24, 25–34, 35–44, 45–54, 55+`); `build_stats(rows: list[dict], now_utc: datetime) -> str` — Cyrillic HTML text with two periods (7 and 30 days): total count, then counts by source, topic (a lead counts once per topic), region, age bucket, prior; sorted by count desc, zero rows omitted; empty period → «Ариза йўқ».
- `bot.py`: Settings from env (`BOT_TOKEN`, `ADMIN_CHAT_ID` int, `WEBAPP_URL` must start with `https://`, `DB_PATH` default `data/leads.db` relative to bot dir) → `ConfigError` with readable message; `main()` prints it and exits 1 without traceback. Handlers: `/start [param]` → reply keyboard (`is_persistent=True`, `resize_keyboard=True`) with one `KeyboardButton(web_app=WebAppInfo(url=WEBAPP_URL[?src=param]))`, param only if in DEEP_LINK_SOURCES; `web_app_data` → parse → Rejected: reply `t(error_key, script)`; cooldown check (30s per user, applied after successful validation) → save to DB (on exception: log + `server_error`) → send admin message → on success `mark_delivered`, on `TelegramAPIError` log and leave undelivered → reply `thanks` (in lead script). Background task every RETRY_INTERVAL_SECONDS resends undelivered. `/export` and `/stats` only when `message.chat.id == ADMIN_CHAT_ID`, otherwise ignored silently; `/export` sends CSV document `leads_YYYYMMDD.csv` (or «Ариза йўқ»). Fallback handler registered last → short hint to press the button. `start_polling(drop_pending_updates=True, allowed_updates=dp.resolve_used_update_types())`. Logging never prints token or phone numbers.

## 9. Mini App content
Copy source: `Kurs modullari.txt` (module titles/texts verbatim in cyr) and `telegram post.txt`. No contact phone/@handle in the app.
Sections (top → bottom):
1. Header: logo mark + wordmark, `Кир | Lot` segmented toggle (remembers choice in `localStorage` key `qp_script`, all access in try/catch; default `cyr`).
2. Hero: eyebrow «12 ОЙЛИК ДАСТУР»; title «QUANTUM Psychology»; subtitle «12 ойлик шахсий ва руҳий ривожланиш дастури»; tagline «Ички имкониятингизни очинг — янги даражага чиқинг»; tag «БЕПУЛ» + text «дастлабки суҳбат»; primary gold CTA «Бепул суҳбатга ёзилиш» (scrolls to form).
3. About: intro paragraph (verbatim) + «12 ой — 12 модуль — ўзгаришнинг 12 босқичи».
4. 12 modules: cards (number «01»…«12», title, description); topic-related modules get a highlighted state.
5. Goal («Дастурнинг асосий мақсади», verbatim).
6. «Курс кимлар учун?» — 5 bullets verbatim (line icons, no emoji).
7. Founder: short version of the post story (2–3 short paragraphs, first person, no name/photo), ends with «Баъзан ҳаётимиздаги энг катта ўзгариш ўзимизга бўлган муносабатимизни ўзгартиришдан бошланади.»
8. «Бепул суҳбатда нима бўлади»: 1) Ариза қолдирасиз. 2) Биз сизга қулай вақтда қўнғироқ қиламиз. 3) Суҳбат давомида сизни қийнаётган масалалар ва олдинга интилишингизга тўсқинлик қилаётган омилларни биргаликда тушунишга ҳаракат қиламиз.
9. Form (fields per §7; topics = multi-select chips; selecting topics highlights related module cards; source question hidden when valid `?src=` present) + consent checkbox «Маълумотларим ушбу ариза бўйича мен билан боғланиш учун ишлатилишига розиман» + submit (disabled until consent; disabled after click to prevent double submit).
10. Disclaimer: «Дастур тиббий ёрдам ўрнини босмайди. Соғлиғингиз бўйича шифокорга мурожаат қилинг.»
11. Closing line verbatim: «QUANTUM Psychology — шунчаки билим эмас, балки ўзини ва ўз ҳаётини онгли бошқаришни ўргатувчи тизим.»
Outside Telegram (`!window.Telegram?.WebApp?.initData` / no `sendData`): content visible, submit shows «Аризани юбориш учун ботдаги тугма орқали очинг».
Submit: build payload → `tg.sendData(JSON.stringify(payload))` → Telegram closes the app; fallback `setTimeout(finish, 900)` as in hotel template `webapp/app.js:305-333`.

`data.js` exports: `MODULES` (12 × `{n, title:{cyr,lat}, text:{cyr,lat}}`), `INTRO, TWELVE_LINE, GOAL_TITLE, GOAL, AUDIENCE_TITLE, AUDIENCE (5), CLOSING` (each `{cyr,lat}`), `REGIONS, TOPICS (with modules), PRIOR, CALL_TIMES, SOURCES` (arrays `{code, label:{cyr,lat}}`), `DEEP_LINK_SOURCES`, `LIMITS`.
`i18n.js` exports `UI = {cyr:{…}, lat:{…}}` (identical key sets) and `t(key, script)`.
`validate.js` exports `validateLead(form, script) -> {ok:true, payload} | {ok:false, errors:{field: errorKey}}`, `normalizePhone(str)`, `payloadBytes(obj)`.

## 10. Brand (from `brand/QUANTUM Psychology — Brend kitobi.html`)
- File structure: pages are gzip+base64 bundles in a manifest JSON (line ~220). Logo SVGs use non-standard attr `sc-camel-view-box` → rename to `viewBox`. Fonts (Cormorant Garamond 500/600/700 + Italic, Montserrat 400–800) embedded as woff2.
- Colors: bg `#140B2E`, `#2A1458`, `#4B2A8C`, gold `#D4AF6A` (CTA/emphasis only), lavender `#B79CE8`, light gold `#F1D9A0`, body text `#EDE6FA`, pearl `#FBF7F0`, ink `#1E1433`, card `#1C1040`, muted `#CFC2EA`, border `rgba(183,156,232,.22)`. Ratio 60/22/12/6.
- Gradients: hero `radial-gradient(ellipse at 50% 35%, #6A3FC2, #2A1458 50%, #140B2E)`; gold CTA `linear-gradient(135deg,#F1D9A0,#D4AF6A 50%,#A8823E)`.
- Type: headings Cormorant Garamond; body Montserrat 16/26; buttons 13–15px caps +0.08em; eyebrow 12–13px 700, letter-spacing .14–.2em; H2 Montserrat 700 22/30.
- Components: buttons ≥48px tall, radius 999, one gold primary per screen; input 50px, radius 14, border 1.5px `#4B2A8C`, gold on focus; block radius 20; card radius 24; spacing 4px grid; line icons 1.6px stroke in 52px circle with gold border.
- Logo: atom mark (3 ellipses rx44 ry15 rotated 0/60/120 + dot); wordmark live text «QUANTUM» Cormorant 600 .18em `#F1D9A0` + «Psychology» Cormorant Italic `#EDE6FA`. Min 24px mark. No stretch/recolor/glow.
- Forbidden: emoji, cold blue/neon, text glow, >3 accents, >5 sparkles.
- Layout: mobile-first, 390px wide target, no horizontal scroll, respects Telegram safe areas.

## 11. Acceptance
See plan acceptance list; final gates: `py -3.11 -m pytest -q` all green, `node --test webapp/tests/` all green, `py -3.11 scripts/extract_brand_assets.py --check` passes, manual check at 390×844 in both scripts.
