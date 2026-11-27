# Telegram bot showcase: results, reviews, Coaching 12 video, about, call-back

Status: approved 2026-11-27. Plan: 4 waves (0 = media collection, 1–3 = code).

## Goal
A client who opens the bot from Instagram should, without leaving the bot, see:
real reviews and results, the Coaching 12 video, who the coach is, and one-tap ways
to call or be called. Every section ends with a call to action.

## Client flow
1. `/start` → existing welcome photo + caption (unchanged) → `start_greeting` with the
   new reply keyboard → Coaching 12 video with caption and inline buttons.
2. Persistent reply keyboard (`resize_keyboard=True`, `is_persistent=True`):
   ```
   R1: [open_button]                         web_app (existing, unchanged)
   R2: [results_button] [coaching_button]
   R3: [about_button]   [contact_button]
   R4: [callback_button]                     request_contact=True
   ```
3. Inline navigation (`callback_data` prefix `show:`; must not collide with admin `adm:`):
   - `show:rev:<n>` — reviews page n (1-based). Invalid/out of range → page 1.
   - `show:video` — Coaching 12 video.
   - `show:about` — about the coach.
   - `show:contact` — admin contact card.
   Inline buttons cannot open the Mini App with `sendData`, so CTAs to the form point to
   the reply-keyboard button in text.

## Sections
### Results and reviews (`results_button`, `show:rev:<n>`)
- Page 1 only: send `results_intro` text first.
- Then a media group (album) of up to `ALBUM_MAX = 10` photos from `bot/assets/reviews/`,
  sorted by file name.
- Then `results_footer` text with inline keyboard:
  - row 1: `results_more_button` (`show:rev:<n+1>`) — only if a next page exists;
  - row 2: `nav_coaching` (`show:video`), `admin_phone_button` (`show:contact`).
- No photos at all → `results_empty`, no crash, warning logged.
- Callback query must always be answered (`callback.answer()`).

### Coaching 12 (`coaching_button`, `show:video`, after `/start`)
- `send_video` of `bot/assets/coaching12.mp4` with `coaching_caption`,
  `width=720, height=1280, duration=137, supports_streaming=True`.
- Inline: `nav_results` (`show:rev:1`), `admin_phone_button` (`show:contact`).
- File missing → `media_unavailable`, logged.

### About the coach (`about_button`, `show:about`)
- Album of photos from `bot/assets/about/` (sorted, max 10; skip album if empty),
  then `about_text` with inline: `nav_results` (`show:rev:1`), `nav_coaching` (`show:video`).

### Contact (`contact_button`, `show:contact`)
- `send_contact(phone_number=ADMIN_PHONE, first_name=ADMIN_CONTACT_NAME)`.
- Then `contact_text` with inline URL button `write_admin_button` → `https://t.me/aziza8111`.

### Call me back (`callback_button`, reply keyboard `request_contact=True`)
Handler on `F.contact`:
1. `contact.user_id != message.from_user.id` (or `None`) → `callback_not_own`, nothing saved.
2. Normalize phone with the existing rule in `bot/leads.py` (`_valid_phone`; Telegram sends
   numbers with or without `+`). Invalid → `callback_not_own`.
3. Per-user cooldown `COOLDOWN_SECONDS` (30) in memory → `callback_cooldown`, nothing saved.
4. `storage.save_callback(...)` → id. Storage error → `server_error`, logged.
5. Notify `admin_chat_id` with `render_callback_admin(row, now_utc)` (HTML parse mode),
   then `mark_callback_delivered(id)`. Delivery error → logged (exception type name only),
   row stays `delivered = 0`; the client still gets `callback_thanks`.
6. `_record_user(...)` as for leads, then reply `callback_thanks` with the main keyboard.
7. `retry_undelivered_once` also retries undelivered call-back requests.

Admin message (Cyrillic, all user values HTML-escaped and stripped of control chars,
same approach as `leads.render_admin`):
```
<b>Қўнғироқ сўрови</b>
Сўров ID: {id}
Вақт: {dd.mm.yyyy HH:MM Tashkent}
Телефон: {phone}
Telegram: <a href="tg://user?id={tg_user_id}">{full_name}</a> (@{username})
```

## File-id cache
- In-memory `dict[str, str]` path → Telegram `file_id`, owned by one `Showcase` instance.
- First send uses `FSInputFile`; after success store `file_id`
  (photo: `message.photo[-1].file_id`, video: `message.video.file_id`).
- If a send that used cached ids raises `TelegramBadRequest`, drop those ids and retry once
  with `FSInputFile`. Second failure → log + `media_unavailable`.

## DB: new table (additive)
```sql
CREATE TABLE IF NOT EXISTS callback_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,          -- UTC ISO, same as leads
    tg_user_id INTEGER NOT NULL,
    tg_username TEXT,
    tg_full_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    delivered INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_callback_requests_created_at ON callback_requests (created_at);
```
Storage methods: `save_callback(row: dict) -> int`, `mark_callback_delivered(id) -> None`,
`undelivered_callbacks(limit=DEFAULT_UNDELIVERED_LIMIT) -> list[dict]`.
`leads` and `users` are not changed. Rollback: ignore the table or `DROP TABLE` (user only).

## Content constants (`bot/content.py`)
```
ASSETS_DIR = BOT_DIR / "assets"
REVIEWS_DIR = ASSETS_DIR / "reviews"
ABOUT_DIR = ASSETS_DIR / "about"
COACHING_VIDEO = ASSETS_DIR / "coaching12.mp4"
COACHING_VIDEO_WIDTH = 720; COACHING_VIDEO_HEIGHT = 1280; COACHING_VIDEO_DURATION = 137
ALBUM_MAX = 10
ADMIN_PHONE = "+998916628111"
ADMIN_CONTACT_NAME = "QUANTUM Psychology"
ADMIN_TELEGRAM_USERNAME = "aziza8111"
ADMIN_TELEGRAM_URL = "https://t.me/aziza8111"
SHOW_PREFIX = "show:"
review_photos(dir=REVIEWS_DIR) -> list[Path]   # sorted *.jpg
about_photos(dir=ABOUT_DIR) -> list[Path]
pages(items, size=ALBUM_MAX) -> list[list[Path]]
clamp_page(raw: str | int | None, total: int) -> int   # invalid → 1
```

## Media assets
- Raw captures (done in wave 0, not committed): `Otzivlar/instagram/<slug>/NN.png`,
  slugs `natijalar` (15), `otziv` (6), `asoschi` (2). Each is a 327x583 PNG screen capture
  of a paused story (stories are video cards; CDN URLs cannot be downloaded). No download
  script is needed.
- Manifest: `docs/specs/instagram-media-manifest.json` — for every file a `crop`
  box `[left, top, right, bottom]` in capture pixels (removes Instagram UI and stickers),
  plus `bot_order` and skipped stories.
- `scripts/prepare_bot_media.py` (stdlib + Pillow, run with `py -3.11`):
  - reads the manifest; paths in it are relative to the repo root;
  - for Instagram files: crop by `crop`, then upscale 2x with `Image.LANCZOS`;
  - Telegram screenshots: no crop, no upscale;
  - writes JPEG q85, RGB, no EXIF, longest side ≤ 1280 px, each ≤ 1 MB;
  - deletes nothing outside `bot/assets/reviews/` and `bot/assets/about/`; before writing,
    it removes only old `*.jpg` in those two folders so the numbering stays exact;
  - compresses the video with ffmpeg (found via `shutil.which("ffmpeg")`; clear error if
    missing);
  - `--check` mode: verifies outputs (count, size limits, ffprobe codecs) and exits non-zero
    on any problem; does not write.
- Bot copies (committed):
  - `bot/assets/reviews/NN.jpg` (01..27) — `natijalar` 01..15, `otziv` 01..06, then the
    6 Telegram screenshots `Otzivlar/Screenshot_1..6.png` (names kept, user decision).
  - `bot/assets/about/NN.jpg` (01..02) — `asoschi`.
  - JPEG quality 85, longest side ≤ 1280 px, each ≤ 1 MB, RGB, EXIF stripped.
  - `bot/assets/coaching12.mp4` — from `Kouching 12 haqida video/c197f912.mp4`, h264 + aac,
    720x1280, `-movflags +faststart`, ≤ 12 MB.

## Texts (keys added to both `cyr` and `lat` in `bot/texts.py`)
`start_greeting` changes; all others are new.

| key | cyr | lat |
|---|---|---|
| start_greeting | Пастдаги менюдан танланг:\n⭐ Натижалар ва отзивлар — иштирокчилар нима дейди\n🎥 Коучинг 12 ҳақида — устоз 2 дақиқада тушунтиради\n👩‍🏫 Устоз ҳақида — Зулхумор ким\n📞 Боғланиш — админ рақами\n📲 Менга қўнғироқ қилинг — рақамингизни юборинг, ўзимиз қўнғироқ қиламиз | Pastdagi menyudan tanlang:\n⭐ Natijalar va otzivlar — ishtirokchilar nima deydi\n🎥 Kouching 12 haqida — ustoz 2 daqiqada tushuntiradi\n👩‍🏫 Ustoz haqida — Zulhumor kim\n📞 Bogʻlanish — admin raqami\n📲 Menga qoʻngʻiroq qiling — raqamingizni yuboring, oʻzimiz qoʻngʻiroq qilamiz |
| results_button | ⭐ Натижалар ва отзивлар | ⭐ Natijalar va otzivlar |
| coaching_button | 🎥 Коучинг 12 ҳақида | 🎥 Kouching 12 haqida |
| about_button | 👩‍🏫 Устоз ҳақида | 👩‍🏫 Ustoz haqida |
| contact_button | 📞 Боғланиш | 📞 Bogʻlanish |
| callback_button | 📲 Менга қўнғироқ қилинг | 📲 Menga qoʻngʻiroq qiling |
| results_intro | ⭐ Иштирокчиларнинг ўз сўзлари\n\nБу ерда Коучинг 12 иштирокчиларининг натижалари ва отзивлари.\n\nИзоҳ: натижалар — иштирокчиларнинг шахсий тажрибаси, ҳар кимда турлича бўлади. | ⭐ Ishtirokchilarning oʻz soʻzlari\n\nBu yerda Kouching 12 ishtirokchilarining natijalari va otzivlari.\n\nIzoh: natijalar — ishtirokchilarning shaxsiy tajribasi, har kimda turlicha boʻladi. |
| results_footer | Отзивлар {page}/{total}.\nСиз ҳам ўз йўлингизни бошламоқчимисиз? Пастдаги «Бепул суҳбатга ёзилиш» тугмасини босинг 👇 | Otzivlar {page}/{total}.\nSiz ham oʻz yoʻlingizni boshlamoqchimisiz? Pastdagi «Bepul suhbatga yozilish» tugmasini bosing 👇 |
| results_more_button | Яна отзивлар ({page}/{total}) | Yana otzivlar ({page}/{total}) |
| results_empty | Отзивлар тез орада қўшилади. | Otzivlar tez orada qoʻshiladi. |
| coaching_caption | 🎥 Коучинг 12 — QUANTUM Psychology’нинг 12 ойлик дастури.\n\nЗулхумор устоз 2 дақиқада айтиб беради:\n• фикрлаш йўналишини ўзгартириш;\n• ҳаётингиз учун масъулиятни ўз қўлингизга олиш;\n• ўзингизга ишонч ва ички таянч;\n• индивидуал ёки мини-гуруҳда ишлаш.\n\nСизга қайси формат мос — бепул дастлабки суҳбатда аниқлаймиз. Пастдаги «Бепул суҳбатга ёзилиш» тугмасини босинг 👇 | 🎥 Kouching 12 — QUANTUM Psychology’ning 12 oylik dasturi.\n\nZulhumor ustoz 2 daqiqada aytib beradi:\n• fikrlash yoʻnalishini oʻzgartirish;\n• hayotingiz uchun masʼuliyatni oʻz qoʻlingizga olish;\n• oʻzingizga ishonch va ichki tayanch;\n• individual yoki mini-guruhda ishlash.\n\nSizga qaysi format mos — bepul dastlabki suhbatda aniqlaymiz. Pastdagi «Bepul suhbatga yozilish» tugmasini bosing 👇 |
| about_text | 👩‍🏫 Зулхумор Қодирова — энергокоуч, таълим дастурлари муаллифи ва QUANTUM Psychology академияси асосчиси.\n\n«18 йил ногиронлик билан яшадим. Оддий ҳаракат қилиш, эркин юриш мен учун катта орзу эди. Лекин қалбимда доим бир ишонч яшарди: менинг ҳаётим ҳали ўзгариши мумкин.\n\nБугун ҳаётим бутунлай бошқача: эркин ҳаракатланаман, орзулар қиламан.\n\nЙиллар давомидаги билим, изланиш ва шахсий тажрибам асосида QUANTUM Psychology тизимини яратдим. Мақсадим — инсонларга ўз ички дунёсини англаш, ўзини қадрлаш, оила ва муносабатлар, молиявий қарашлар ва ички тўсиқлар устида ишлашда ёрдам бериш.\n\nБаъзан ҳаётдаги энг катта ўзгариш ўзимизга бўлган муносабатни ўзгартиришдан бошланади.»\n\n🎁 Дастлабки суҳбат бепул. Пастдаги «Бепул суҳбатга ёзилиш» тугмасини босинг ёки «📲 Менга қўнғироқ қилинг» орқали рақамингизни қолдиринг. | 👩‍🏫 Zulhumor Qodirova — energokouch, taʼlim dasturlari muallifi va QUANTUM Psychology akademiyasi asoschisi.\n\n«18 yil nogironlik bilan yashadim. Oddiy harakat qilish, erkin yurish men uchun katta orzu edi. Lekin qalbimda doim bir ishonch yashardi: mening hayotim hali oʻzgarishi mumkin.\n\nBugun hayotim butunlay boshqacha: erkin harakatlanaman, orzular qilaman.\n\nYillar davomidagi bilim, izlanish va shaxsiy tajribam asosida QUANTUM Psychology tizimini yaratdim. Maqsadim — insonlarga oʻz ichki dunyosini anglash, oʻzini qadrlash, oila va munosabatlar, moliyaviy qarashlar va ichki toʻsiqlar ustida ishlashda yordam berish.\n\nBaʼzan hayotdagi eng katta oʻzgarish oʻzimizga boʻlgan munosabatni oʻzgartirishdan boshlanadi.»\n\n🎁 Dastlabki suhbat bepul. Pastdagi «Bepul suhbatga yozilish» tugmasini bosing yoki «📲 Menga qoʻngʻiroq qiling» orqali raqamingizni qoldiring. |
| contact_text | 📞 Админ билан боғланиш\n\nТелефон: +998 91 662 81 11\nTelegram: @aziza8111\n\nҚўнғироқ қилинг ёки Telegram’да ёзинг — саволларингизга жавоб берамиз. Ёки «📲 Менга қўнғироқ қилинг» тугмасини босинг, ўзимиз қўнғироқ қиламиз. | 📞 Admin bilan bogʻlanish\n\nTelefon: +998 91 662 81 11\nTelegram: @aziza8111\n\nQoʻngʻiroq qiling yoki Telegram’da yozing — savollaringizga javob beramiz. Yoki «📲 Menga qoʻngʻiroq qiling» tugmasini bosing, oʻzimiz qoʻngʻiroq qilamiz. |
| callback_thanks | Раҳмат! Рақамингизни олдик. Админ тез орада сизга қўнғироқ қилади. | Rahmat! Raqamingizni oldik. Admin tez orada sizga qoʻngʻiroq qiladi. |
| callback_not_own | Илтимос, ўз рақамингизни «📲 Менга қўнғироқ қилинг» тугмаси орқали юборинг. | Iltimos, oʻz raqamingizni «📲 Menga qoʻngʻiroq qiling» tugmasi orqali yuboring. |
| callback_cooldown | Сўровингиз яқинда қабул қилинди. Админ сизга қўнғироқ қилади. | Soʻrovingiz yaqinda qabul qilindi. Admin sizga qoʻngʻiroq qiladi. |
| media_unavailable | Ҳозир материални юклай олмадик. Илтимос, кейинроқ қайта уриниб кўринг. | Hozir materialni yuklay olmadik. Iltimos, keyinroq qayta urinib koʻring. |
| nav_results | ⭐ Отзивлар | ⭐ Otzivlar |
| nav_coaching | 🎥 Коучинг 12 | 🎥 Kouching 12 |
| nav_about | 👩‍🏫 Устоз ҳақида | 👩‍🏫 Ustoz haqida |
| admin_phone_button | 📞 Админ рақами | 📞 Admin raqami |
| write_admin_button | ✍️ Telegram’да ёзиш | ✍️ Telegram’da yozish |

`\n` in the table means a real line break in the Python string.
The bot sends Cyrillic (current default); Latin keys exist for parity (`test_catalog.py`).

## Out of scope
AI images, drip/reminder messages, admin panel or Mini App stats for call-backs, Mini App
form changes, price/start date, deploy, push.

## Tests
- `py -3.11 -m pytest -q` (baseline 219 passed) and `node --test "webapp/tests/*.test.mjs"`.
- Call-back: own contact saved + admin notified; foreign contact rejected; invalid phone
  rejected; cooldown; storage error; delivery error keeps `delivered=0`; HTML escaping.
- Showcase: paging (sizes, invalid page → 1, last page has no "more"), cache reuse,
  `TelegramBadRequest` → re-upload, missing files → `media_unavailable`.
- Dispatcher: new text buttons, `F.contact`, `show:` callbacks registered before fallback.
