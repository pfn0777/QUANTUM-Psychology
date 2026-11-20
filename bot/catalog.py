"""Shared bot catalog codes, labels, and validation limits."""

REGIONS: dict[str, dict[str, str]] = {
    "tashkent_city": {"cyr": "Тошкент шаҳри", "lat": "Toshkent shahri"},
    "tashkent_region": {"cyr": "Тошкент вилояти", "lat": "Toshkent viloyati"},
    "andijan": {"cyr": "Андижон", "lat": "Andijon"},
    "bukhara": {"cyr": "Бухоро", "lat": "Buxoro"},
    "fergana": {"cyr": "Фарғона", "lat": "Fargʻona"},
    "jizzakh": {"cyr": "Жиззах", "lat": "Jizzax"},
    "kashkadarya": {"cyr": "Қашқадарё", "lat": "Qashqadaryo"},
    "navoi": {"cyr": "Навоий", "lat": "Navoiy"},
    "namangan": {"cyr": "Наманган", "lat": "Namangan"},
    "samarkand": {"cyr": "Самарқанд", "lat": "Samarqand"},
    "surkhandarya": {"cyr": "Сурхондарё", "lat": "Surxondaryo"},
    "syrdarya": {"cyr": "Сирдарё", "lat": "Sirdaryo"},
    "khorezm": {"cyr": "Хоразм", "lat": "Xorazm"},
    "karakalpakstan": {
        "cyr": "Қорақалпоғистон Республикаси",
        "lat": "Qoraqalpogʻiston Respublikasi",
    },
    "abroad": {"cyr": "Хорижда", "lat": "Xorijda"},
}

TOPICS: dict[str, dict[str, str]] = {
    "family": {"cyr": "Оила ва муносабатлар", "lat": "Oila va munosabatlar"},
    "parents": {"cyr": "Ота-она ва ўтмиш", "lat": "Ota-ona va oʻtmish"},
    "fear": {"cyr": "Қўрқув ва хавотир", "lat": "Qoʻrquv va xavotir"},
    "money": {"cyr": "Пул ва даромад", "lat": "Pul va daromad"},
    "health": {"cyr": "Соғлиқ ва тана", "lat": "Sogʻliq va tana"},
    "selfworth": {"cyr": "Ўз қадри ва чегаралар", "lat": "Oʻz qadri va chegaralar"},
    "support": {"cyr": "Ички таянч", "lat": "Ichki tayanch"},
    "fatigue": {"cyr": "Чарчоқ", "lat": "Charchoq"},
}

TOPIC_MODULES: dict[str, tuple[int, ...]] = {
    "family": (3, 10),
    "parents": (3, 4),
    "fear": (1, 4),
    "money": (6, 9),
    "health": (8,),
    "selfworth": (2, 11),
    "support": (1, 11),
    "fatigue": (1, 8),
}

PRIOR: dict[str, dict[str, str]] = {
    "no": {"cyr": "Йўқ", "lat": "Yoʻq"},
    "finished": {"cyr": "Ҳа, тугатдим", "lat": "Ha, tugatdim"},
    "stopped": {
        "cyr": "Ҳа, лекин давом эттиролмадим",
        "lat": "Ha, lekin davom ettirolmadim",
    },
}

CALL_TIMES: dict[str, dict[str, str]] = {
    "morning": {"cyr": "Эрталаб (9:00–12:00)", "lat": "Ertalab (9:00–12:00)"},
    "day": {"cyr": "Кундузи (12:00–17:00)", "lat": "Kunduzi (12:00–17:00)"},
    "evening": {"cyr": "Кечқурун (17:00–21:00)", "lat": "Kechqurun (17:00–21:00)"},
}

SOURCES: dict[str, dict[str, str]] = {
    "ig": {"cyr": "Instagram", "lat": "Instagram"},
    "tg": {"cyr": "Telegram", "lat": "Telegram"},
    "yt": {"cyr": "YouTube", "lat": "YouTube"},
    "friend": {"cyr": "Танишлар орқали", "lat": "Tanishlar orqali"},
    "other": {"cyr": "Бошқа", "lat": "Boshqa"},
}

DEEP_LINK_SOURCES = ("ig", "tg", "yt")
SCRIPTS = ("cyr", "lat")

NAME_MIN = 2
NAME_MAX = 80
AGE_MIN = 18
AGE_MAX = 99
PHONE_MIN_DIGITS = 9
PHONE_MAX_DIGITS = 15
COMMENT_MAX = 500
PAYLOAD_MAX_BYTES = 4096
COOLDOWN_SECONDS = 30
RETRY_INTERVAL_SECONDS = 300


def label(table: dict[str, dict[str, str]], code: str, script: str = "cyr") -> str:
    """Return a localized label, or the code if it is absent."""
    entry = table.get(code)
    if entry is None:
        return code
    return entry[script if script in SCRIPTS else "cyr"]
