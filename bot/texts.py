"""Client-facing bot messages in Cyrillic and Latin Uzbek."""

TEXTS: dict[str, dict[str, str]] = {
    "cyr": {
        "cmd_admin": "Админ панел",
        "cmd_start": "Ботни бошлаш",
        "cmd_stats": "Статистика",
        "cmd_export": "Аризаларни юклаб олиш (CSV)",
        "welcome_caption": "Ассалому алайкум! QUANTUM Psychology’га хуш келибсиз. Бизда шахсий ва руҳий ривожланиш учун 12 ойлик дастур бор. Дастур ҳақида танишишни истасангиз, пастдаги «Бепул суҳбатга ёзилиш» тугмани босинг. Дастлабки суҳбат бепул.",
        "start_greeting": "👇",
        "more_info_button": "Қўшимча маълумотлар",
        "open_button": "Бепул суҳбатга ёзилиш",
        "thanks": "Аризангизни олдик. Сиз танлаган вақтда қўнғироқ қиламиз.",
        "cooldown": "Аризангиз яқинда қабул қилинди. Илтимос, бироздан кейин қайта уриниб кўринг.",
        "server_error": "Ҳозир аризани сақлай олмадик. Илтимос, кейинроқ қайта уриниб кўринг.",
        "admin_read_error": "Маълумотни ўқий олмадик. Кейинроқ қайта уриниб кўринг.",
        "fallback_hint": "Ариза қолдириш учун қуйидаги тугмани босинг.",
        "invalid_payload": "Ариза маълумотларини ўқий олмадик. Илтимос, шаклни қайта тўлдиринг.",
        "err_name": "Илтимос, исмингизни тўғри киритинг.",
        "err_age": "Илтимос, ёшингизни 18–99 оралиғида киритинг.",
        "err_phone": "Илтимос, телефон рақамингизни +998 XX XXX XX XX шаклида киритинг.",
        "err_region": "Илтимос, ҳудудингизни танланг.",
        "err_topics": "Илтимос, камида битта мавзуни танланг.",
        "err_prior": "Илтимос, олдинги тажрибангиз ҳақидаги жавобни танланг.",
        "err_call_time": "Илтимос, қўнғироқ учун қулай вақтни танланг.",
        "err_source": "Илтимос, биз ҳақимизда қаердан билганингизни танланг.",
        "err_consent": "Илтимос, маълумотларингизни ушбу ариза учун ишлатишга розилигингизни белгиланг.",
    },
    "lat": {
        "cmd_admin": "Admin panel",
        "cmd_start": "Botni boshlash",
        "cmd_stats": "Statistika",
        "cmd_export": "Arizalarni yuklab olish (CSV)",
        "welcome_caption": "Assalomu alaykum! QUANTUM Psychology’ga xush kelibsiz. Bizda shaxsiy va ruhiy rivojlanish uchun 12 oylik dastur bor. Dastur haqida tanishishni istasangiz, pastdagi «Bepul suhbatga yozilish» tugmani bosing. Dastlabki suhbat bepul.",
        "start_greeting": "👇",
        "more_info_button": "Qoʻshimcha maʼlumotlar",
        "open_button": "Bepul suhbatga yozilish",
        "thanks": "Arizangizni oldik. Siz tanlagan vaqtda qoʻngʻiroq qilamiz.",
        "cooldown": "Arizangiz yaqinda qabul qilindi. Iltimos, birozdan keyin qayta urinib koʻring.",
        "server_error": "Hozir arizani saqlay olmadik. Iltimos, keyinroq qayta urinib koʻring.",
        "admin_read_error": "Maʼlumotni oʻqiy olmadik. Keyinroq qayta urinib koʻring.",
        "fallback_hint": "Ariza qoldirish uchun quyidagi tugmani bosing.",
        "invalid_payload": "Ariza maʼlumotlarini oʻqiy olmadik. Iltimos, shaklni qayta toʻldiring.",
        "err_name": "Iltimos, ismingizni toʻgʻri kiriting.",
        "err_age": "Iltimos, yoshingizni 18–99 oraligʻida kiriting.",
        "err_phone": "Iltimos, telefon raqamingizni +998 XX XXX XX XX shaklida kiriting.",
        "err_region": "Iltimos, hududingizni tanlang.",
        "err_topics": "Iltimos, kamida bitta mavzuni tanlang.",
        "err_prior": "Iltimos, oldingi tajribangiz haqidagi javobni tanlang.",
        "err_call_time": "Iltimos, qoʻngʻiroq uchun qulay vaqtni tanlang.",
        "err_source": "Iltimos, biz haqimizda qayerdan bilganingizni tanlang.",
        "err_consent": "Iltimos, maʼlumotlaringizni ushbu ariza uchun ishlatishga roziligingizni belgilang.",
    },
}


def t(key: str, script: str = "cyr", **fmt: object) -> str:
    """Return a localized message; missing keys raise KeyError."""
    messages = TEXTS[script if script in TEXTS else "cyr"]
    return messages[key].format(**fmt)
