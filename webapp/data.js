// Uzbek Cyrillic copy is preserved from Kurs modullari.txt.
const LETTERS = {
  а: "a", б: "b", в: "v", г: "g", ғ: "gʻ", д: "d", ж: "j", з: "z",
  и: "i", й: "y", к: "k", қ: "q", л: "l", м: "m", н: "n", о: "o",
  п: "p", р: "r", с: "s", т: "t", у: "u", ў: "oʻ", ф: "f", х: "x",
  ҳ: "h", ч: "ch", ш: "sh", э: "e", ё: "yo", ю: "yu", я: "ya",
  ъ: "ʼ", ь: "",
};
const VOWELS = new Set(["а", "э", "е", "и", "о", "у", "ў", "ё", "ю", "я"]);

function transliterate(value) {
  return Array.from(value, (letter, index) => {
    const lower = letter.toLowerCase();
    const previous = value[index - 1]?.toLowerCase();
    let latin;
    if (lower === "е") {
      latin = !previous || !/[а-яёғқҳў]/u.test(previous) || VOWELS.has(previous) ? "ye" : "e";
    } else if (lower === "ц") {
      latin = previous && VOWELS.has(previous) ? "ts" : "s";
    } else {
      latin = LETTERS[lower];
    }
    if (latin === undefined) return letter;
    return letter !== lower ? latin.toUpperCase() : latin;
  }).join("");
}

function pair(cyr) {
  return { cyr, lat: transliterate(cyr) };
}

export const INTRO = pair("Ушбу курс — инсоннинг ўзини англаши, ички қувватини бошқариши, онгости дастурларини ўрганиши ва ҳаёт сифатини яхшилашига қаратилган тизимли таълим дастури.");
export const TWELVE_LINE = pair("12 ой — 12 модуль — ўзгаришнинг 12 босқичи.");

export const MODULES = [
  { n: 1, title: pair("ЎЗИНИ БОШҚАРИШ"), text: pair("Ҳиссиётлар, фикрлар ва ички ҳолатни бошқариш. Қувватни тўплаш, сақлаш ва мақсад сари йўналтириш.") },
  { n: 2, title: pair("ҲАЁТ ҚОНУНИЯТЛАРИ"), text: pair("Илоҳий қонунлар, сабаб ва оқибат, мувозанат, шахсий чегаралар, тортишиш кучи ва қувват алмашинуви.") },
  { n: 3, title: pair("ОТА-ОНА ВА МУСТАҚИЛ ШАХС"), text: pair("Ота-она билан муносабатлар, болаликда шаклланган дастурлар, миннатдорлик, ҳиссий мустақиллик ва ўзига таяниш.") },
  { n: 4, title: pair("ОНГОСТИ ДАСТУРЛАРИ ВА МАҚСАДЛАР"), text: pair("Аждодлардан ўтган ҳаётий сценарийлар, ички чекловлар, қўрқувлар, ўзига ишонч ва мақсадга эришиш стратегиялари.") },
  { n: 5, title: pair("РУҲИЙ РИВОЖЛАНИШ"), text: pair("Бирлик онги, кармик сценарийлар, қалб поклиги, руҳий озуқа, илоҳий қадриятлар ва ҳаёт мазмуни.") },
  { n: 6, title: pair("ИЧКИ ДУНЁ ВА ТАШҚИ ҲАЁТ"), text: pair("Ички қисмлар, пул, бойлик, севги ва муносабатлар. Розилик, масъулият, имкониятларни кенгайтириш ва келажакни шакллантириш.") },
  { n: 7, title: pair("ОНГНИ КЕНГАЙТИРИШ"), text: pair("Интуицияни ривожлантириш, вазиятларга турли нуқтаи назардан қараш, севги, руҳий бирлик ва илоҳий масъулият.") },
  { n: 8, title: pair("ТАНА ВА ИЧКИ ҲОЛАТ"), text: pair("Тана билан муносабат, ҳиссий зўриқишлар, ички хотиржамлик, соғлом одатлар ва ўзини асраш.") },
  { n: 9, title: pair("ПУЛ ВА ФАРОВОНЛИК"), text: pair("Пулга нисбатан онгости қарашлари, етишмовчилик ҳисси, ўз қадрини англаш, молиявий масъулият ва даромадни ошириш стратегиялари.") },
  { n: 10, title: pair("СЕВГИ ВА МУНОСАБАТЛАР"), text: pair("Эркак ва аёл муносабатлари, фарзандлар билан мулоқот, оилавий сценарийлар, ҳурмат ва соғлом шахсий чегаралар.") },
  { n: 11, title: pair("ЎЗ САЛОҲИЯТИНИ РЎЁБГА ЧИҚАРИШ"), text: pair("Лойиқлик, ички таянч, шахсий салоҳият, ҳаётий мақсадлар, қарор қабул қилиш ва янги даражага ўтиш.") },
  { n: 12, title: pair("ТЎЛИҚ ТАКРОРЛАШ ВА МУСТАҲКАМЛАШ"), text: pair("Барча 11 модулни такрорлаш, билим ва кўникмаларни текшириш, коррекция қилиш, натижаларни таҳлил қилиш ва келгуси ҳаёт стратегиясини яратиш.") },
];

export const GOAL_TITLE = pair("Дастурнинг асосий мақсади");
export const GOAL = pair("Инсонда ўз ҳиссиётлари, фикрлари, ички қуввати, қарорлари ва ҳаётий ҳаракатларини онгли бошқариш қобилиятини шакллантириш.");
export const AUDIENCE_TITLE = pair("Курс кимлар учун?");
export const AUDIENCE = [
  pair("Ўзини чуқур англашни истаганлар;"),
  pair("Такрорланаётган муаммолардан чиқишни хоҳлаганлар;"),
  pair("Молиявий ва шахсий ўсишга интилганлар;"),
  pair("Оилавий муносабатларини яхшилашни истаганлар;"),
  pair("Ўзига ишонган, мустақил ва масъулиятли шахс бўлишни хоҳлаганлар."),
];
export const CLOSING = pair("QUANTUM Psychology — шунчаки билим эмас, балки ўзини ва ўз ҳаётини онгли бошқаришни ўргатувчи тизим.");

export const REGIONS = [
  { code: "tashkent_city", label: { cyr: "Тошкент шаҳри", lat: "Toshkent shahri" } },
  { code: "tashkent_region", label: { cyr: "Тошкент вилояти", lat: "Toshkent viloyati" } },
  { code: "andijan", label: { cyr: "Андижон", lat: "Andijon" } },
  { code: "bukhara", label: { cyr: "Бухоро", lat: "Buxoro" } },
  { code: "fergana", label: { cyr: "Фарғона", lat: "Fargʻona" } },
  { code: "jizzakh", label: { cyr: "Жиззах", lat: "Jizzax" } },
  { code: "kashkadarya", label: { cyr: "Қашқадарё", lat: "Qashqadaryo" } },
  { code: "navoi", label: { cyr: "Навоий", lat: "Navoiy" } },
  { code: "namangan", label: { cyr: "Наманган", lat: "Namangan" } },
  { code: "samarkand", label: { cyr: "Самарқанд", lat: "Samarqand" } },
  { code: "surkhandarya", label: { cyr: "Сурхондарё", lat: "Surxondaryo" } },
  { code: "syrdarya", label: { cyr: "Сирдарё", lat: "Sirdaryo" } },
  { code: "khorezm", label: { cyr: "Хоразм", lat: "Xorazm" } },
  { code: "karakalpakstan", label: { cyr: "Қорақалпоғистон Республикаси", lat: "Qoraqalpogʻiston Respublikasi" } },
  { code: "abroad", label: { cyr: "Хорижда", lat: "Xorijda" } },
];

export const TOPICS = [
  { code: "family", label: { cyr: "Оила ва муносабатлар", lat: "Oila va munosabatlar" }, modules: [3, 10] },
  { code: "parents", label: { cyr: "Ота-она ва ўтмиш", lat: "Ota-ona va oʻtmish" }, modules: [3, 4] },
  { code: "fear", label: { cyr: "Қўрқув ва хавотир", lat: "Qoʻrquv va xavotir" }, modules: [1, 4] },
  { code: "money", label: { cyr: "Пул ва даромад", lat: "Pul va daromad" }, modules: [6, 9] },
  { code: "health", label: { cyr: "Соғлиқ ва тана", lat: "Sogʻliq va tana" }, modules: [8] },
  { code: "selfworth", label: { cyr: "Ўз қадри ва чегаралар", lat: "Oʻz qadri va chegaralar" }, modules: [2, 11] },
  { code: "support", label: { cyr: "Ички таянч", lat: "Ichki tayanch" }, modules: [1, 11] },
  { code: "fatigue", label: { cyr: "Чарчоқ", lat: "Charchoq" }, modules: [1, 8] },
];

export const PRIOR = [
  { code: "no", label: { cyr: "Йўқ", lat: "Yoʻq" } },
  { code: "finished", label: { cyr: "Ҳа, тугатдим", lat: "Ha, tugatdim" } },
  { code: "stopped", label: { cyr: "Ҳа, лекин давом эттиролмадим", lat: "Ha, lekin davom ettirolmadim" } },
];

export const CALL_TIMES = [
  { code: "morning", label: { cyr: "Эрталаб (9:00–12:00)", lat: "Ertalab (9:00–12:00)" } },
  { code: "day", label: { cyr: "Кундузи (12:00–17:00)", lat: "Kunduzi (12:00–17:00)" } },
  { code: "evening", label: { cyr: "Кечқурун (17:00–21:00)", lat: "Kechqurun (17:00–21:00)" } },
];

export const SOURCES = [
  { code: "ig", label: { cyr: "Instagram", lat: "Instagram" } },
  { code: "tg", label: { cyr: "Telegram", lat: "Telegram" } },
  { code: "yt", label: { cyr: "YouTube", lat: "YouTube" } },
  { code: "friend", label: { cyr: "Танишлар орқали", lat: "Tanishlar orqali" } },
  { code: "other", label: { cyr: "Бошқа", lat: "Boshqa" } },
];

export const DEEP_LINK_SOURCES = ["ig", "tg", "yt"];
export const LIMITS = {
  nameMin: 2,
  nameMax: 80,
  ageMin: 18,
  ageMax: 99,
  phoneMinDigits: 9,
  phoneMaxDigits: 15,
  commentMax: 500,
  payloadMaxBytes: 4096,
};
