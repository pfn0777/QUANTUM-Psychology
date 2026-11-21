import test from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import {
  MODULES, INTRO, TWELVE_LINE, GOAL_TITLE, GOAL, AUDIENCE_TITLE,
  AUDIENCE, CLOSING, REGIONS, TOPICS, PRIOR, CALL_TIMES, SOURCES,
  DEEP_LINK_SOURCES, LIMITS,
} from "../data.js";
import { UI, t } from "../i18n.js";

const CYRILLIC = /[А-Яа-яЁёЎўҚқҒғҲҳ]/u;
const EMOJI = /\p{Extended_Pictographic}/u;
const ERROR_KEYS = [
  "invalid_payload", "err_name", "err_age", "err_phone", "err_region",
  "err_topics", "err_prior", "err_call_time", "err_source", "err_consent",
];
const EXPECTED_CATALOG = [
  [REGIONS, [
    ["tashkent_city", "Тошкент шаҳри", "Toshkent shahri"],
    ["tashkent_region", "Тошкент вилояти", "Toshkent viloyati"],
    ["andijan", "Андижон", "Andijon"],
    ["bukhara", "Бухоро", "Buxoro"],
    ["fergana", "Фарғона", "Fargʻona"],
    ["jizzakh", "Жиззах", "Jizzax"],
    ["kashkadarya", "Қашқадарё", "Qashqadaryo"],
    ["navoi", "Навоий", "Navoiy"],
    ["namangan", "Наманган", "Namangan"],
    ["samarkand", "Самарқанд", "Samarqand"],
    ["surkhandarya", "Сурхондарё", "Surxondaryo"],
    ["syrdarya", "Сирдарё", "Sirdaryo"],
    ["khorezm", "Хоразм", "Xorazm"],
    ["karakalpakstan", "Қорақалпоғистон Республикаси", "Qoraqalpogʻiston Respublikasi"],
    ["abroad", "Хорижда", "Xorijda"],
  ]],
  [TOPICS, [
    ["family", "Оила ва муносабатлар", "Oila va munosabatlar", [3, 10]],
    ["parents", "Ота-она ва ўтмиш", "Ota-ona va oʻtmish", [3, 4]],
    ["fear", "Қўрқув ва хавотир", "Qoʻrquv va xavotir", [1, 4]],
    ["money", "Пул ва даромад", "Pul va daromad", [6, 9]],
    ["health", "Соғлиқ ва тана", "Sogʻliq va tana", [8]],
    ["selfworth", "Ўз қадри ва чегаралар", "Oʻz qadri va chegaralar", [2, 11]],
    ["support", "Ички таянч", "Ichki tayanch", [1, 11]],
    ["fatigue", "Чарчоқ", "Charchoq", [1, 8]],
  ]],
  [PRIOR, [
    ["no", "Йўқ", "Yoʻq"],
    ["finished", "Ҳа, тугатдим", "Ha, tugatdim"],
    ["stopped", "Ҳа, лекин давом эттиролмадим", "Ha, lekin davom ettirolmadim"],
  ]],
  [CALL_TIMES, [
    ["morning", "Эрталаб (9:00–12:00)", "Ertalab (9:00–12:00)"],
    ["day", "Кундузи (12:00–17:00)", "Kunduzi (12:00–17:00)"],
    ["evening", "Кечқурун (17:00–21:00)", "Kechqurun (17:00–21:00)"],
  ]],
  [SOURCES, [
    ["ig", "Instagram", "Instagram"],
    ["tg", "Telegram", "Telegram"],
    ["yt", "YouTube", "YouTube"],
    ["friend", "Танишлар орқали", "Tanishlar orqali"],
    ["other", "Бошқа", "Boshqa"],
  ]],
];
const REQUIRED_UI_KEYS = [
  "toggleCyr", "toggleLat", "heroEyebrow", "heroTitle", "heroSubtitle",
  "heroTagline", "heroTag", "heroTagText", "heroCta", "heroImageAlt", "heroImageSrc", "aboutTitle",
  "modulesTitle", "goalTitle", "audienceTitle", "founderTitle",
  "founderP1", "founderP2", "founderP3", "consultationTitle",
  "consultationStep1", "consultationStep2", "consultationStep3", "formTitle",
  "formIntro", "requiredHint", "nameLabel", "namePlaceholder", "nameHint",
  "ageLabel", "agePlaceholder", "ageHint", "phoneLabel", "phonePlaceholder",
  "phoneHint", "regionLabel", "regionPlaceholder", "topicsLabel", "topicsHint",
  "chipsHint", "priorLabel", "priorPlaceholder", "callTimeLabel",
  "callTimePlaceholder", "sourceLabel", "sourcePlaceholder", "commentLabel",
  "commentPlaceholder", "commentHint", "consentText", "submit", "sending",
  "successTitle", "successText", "openFromBot", "disclaimer", ...ERROR_KEYS,
];
const FOUNDER_KEYS = ["founderP1", "founderP2", "founderP3"];
const FOUNDER_ENDING = {
  cyr: "Баъзан ҳаётимиздаги энг катта ўзгариш ўзимизга бўлган муносабатимизни ўзгартиришдан бошланади.",
  lat: "Baʼzan hayotimizdagi eng katta oʻzgarish oʻzimizga boʻlgan munosabatimizni oʻzgartirishdan boshlanadi.",
};
const CONTACT_PHONE = /(?:\+?\d[\d\s().–-]*){7,}/u;
const SPEC_UI_CYR = {
  toggleCyr: "Кир",
  toggleLat: "Lot",
  heroEyebrow: "12 ОЙЛИК ДАСТУР",
  heroTitle: "QUANTUM Psychology",
  heroImageAlt: "QUANTUM Psychology — 12 ойлик шахсий ва руҳий ривожланиш дастури. Фикр кучини бошқариш, ички мувозанат ва хотиржамлик, ҳаёт сифатини юксалтириш. Бепул дастлабки суҳбат.",
  heroImageSrc: "assets/hero-banner-cyr.webp",
  heroSubtitle: "12 ойлик шахсий ва руҳий ривожланиш дастури",
  heroTagline: "Ички имкониятингизни очинг — янги даражага чиқинг",
  heroTag: "БЕПУЛ",
  heroTagText: "дастлабки суҳбат",
  heroCta: "Бепул суҳбатга ёзилиш",
  aboutTitle: "Дастур ҳақида",
  modulesTitle: "12 модуль",
  goalTitle: "Дастурнинг асосий мақсади",
  audienceTitle: "Курс кимлар учун?",
  founderTitle: "Менинг йўлим",
  consultationTitle: "Бепул суҳбатда нима бўлади",
  consultationStep1: "Ариза қолдирасиз.",
  consultationStep2: "Биз сизга қулай вақтда қўнғироқ қиламиз.",
  consultationStep3: "Суҳбат давомида сизни қийнаётган масалалар ва олдинга интилишингизга тўсқинлик қилаётган омилларни биргаликда тушунишга ҳаракат қиламиз.",
  formTitle: "Бепул суҳбатга ариза",
  consentText: "Маълумотларим ушбу ариза бўйича мен билан боғланиш учун ишлатилишига розиман",
  submit: "Аризани юбориш",
  successTitle: "Аризангиз қабул қилинди",
  successText: "Сизга танлаган вақтингизда боғланишга ҳаракат қиламиз.",
  openFromBot: "Аризани юбориш учун чатдаги пастки «Бепул суҳбатга ёзилиш» тугмасини босинг",
  disclaimer: "Дастур тиббий ёрдам ўрнини босмайди. Соғлиғингиз бўйича шифокорга мурожаат қилинг.",
};
const LATIN_SPOT_CHECKS = {
  heroImageAlt: "QUANTUM Psychology — 12 oylik shaxsiy va ruhiy rivojlanish dasturi. Fikr kuchini boshqarish, ichki muvozanat va xotirjamlik, hayot sifatini yuksaltirish. Bepul dastlabki suhbat.",
  heroImageSrc: "assets/hero-banner.webp",
  heroEyebrow: "12 OYLIK DASTUR",
  heroSubtitle: "12 oylik shaxsiy va ruhiy rivojlanish dasturi",
  heroTagline: "Ichki imkoniyatingizni oching — yangi darajaga chiqing",
  consultationStep2: "Biz sizga qulay vaqtda qoʻngʻiroq qilamiz.",
  consentText: "Maʼlumotlarim ushbu ariza boʻyicha men bilan bogʻlanish uchun ishlatilishiga roziman",
  openFromBot: "Arizani yuborish uchun chatdagi pastki «Bepul suhbatga yozilish» tugmasini bosing",
  disclaimer: "Dastur tibbiy yordam oʻrnini bosmaydi. Sogʻligʻingiz boʻyicha shifokorga murojaat qiling.",
};

function assertPair(value) {
  assert.deepEqual(Object.keys(value).sort(), ["cyr", "lat"]);
  for (const script of ["cyr", "lat"]) {
    assert.equal(typeof value[script], "string");
    assert.ok(value[script].trim(), `${script} copy must be non-empty`);
  }
  assert.equal(CYRILLIC.test(value.lat), false, `Latin copy contains Cyrillic: ${value.lat}`);
}

function stringsIn(value) {
  if (typeof value === "string") return [value];
  if (Array.isArray(value)) return value.flatMap(stringsIn);
  if (value && typeof value === "object") return Object.values(value).flatMap(stringsIn);
  return [];
}

test("12 modules are ordered and all script pairs are filled", () => {
  assert.equal(MODULES.length, 12);
  assert.deepEqual(MODULES.map(({ n }) => n), Array.from({ length: 12 }, (_, index) => index + 1));
  for (const module of MODULES) {
    assert.deepEqual(Object.keys(module).sort(), ["n", "text", "title"]);
    assertPair(module.title);
    assertPair(module.text);
  }
  assert.equal(MODULES[0].title.cyr, "ЎЗИНИ БОШҚАРИШ");
  assert.ok(MODULES[11].text.cyr.startsWith("Барча 11 модулни"));
});

test("course copy matches the read-only source verbatim", () => {
  const lines = readFileSync(new URL("../../Kurs modullari.txt", import.meta.url), "utf8")
    .split(/\r?\n/u).filter(Boolean);
  const after = (prefix) => lines[lines.findIndex((line) => line.startsWith(prefix)) + 1];
  assert.equal(INTRO.cyr, lines.find((line) => line.startsWith("Ушбу курс")));
  assert.equal(TWELVE_LINE.cyr, lines.find((line) => line.startsWith("12 ой —")));
  for (const module of MODULES) {
    const line = lines.find((item) => item.startsWith(`${module.n}-МОДУЛЬ. `));
    assert.equal(module.title.cyr, line.slice(`${module.n}-МОДУЛЬ. `.length));
    assert.equal(module.text.cyr, after(`${module.n}-МОДУЛЬ. `));
  }
  assert.equal(GOAL_TITLE.cyr, lines.find((line) => line === "Дастурнинг асосий мақсади"));
  assert.equal(GOAL.cyr, after("Дастурнинг асосий мақсади"));
  assert.equal(AUDIENCE_TITLE.cyr, lines.find((line) => line === "Курс кимлар учун?"));
  assert.equal(AUDIENCE.length, 5);
  assert.deepEqual(AUDIENCE.map((item) => item.cyr),
    lines.filter((line) => line.startsWith("• ")).map((line) => line.slice(2)));
  assert.equal(CLOSING.cyr, lines.find((line) => line.startsWith("QUANTUM Psychology —")));
  for (const value of [INTRO, TWELVE_LINE, GOAL_TITLE, GOAL, AUDIENCE_TITLE, ...AUDIENCE, CLOSING]) {
    assertPair(value);
  }
});

test("catalog codes, order, labels, module links and limits match the spec", () => {
  for (const [table, expected] of EXPECTED_CATALOG) {
    assert.equal(table.length, expected.length);
    assert.deepEqual(table.map(({ code }) => code), expected.map(([code]) => code));
    assert.equal(new Set(table.map(({ code }) => code)).size, expected.length);
    for (const [index, item] of table.entries()) {
      const [code, cyr, lat, modules] = expected[index];
      assert.equal(item.code, code);
      assertPair(item.label);
      assert.deepEqual(item.label, { cyr, lat }, code);
      if (modules) assert.deepEqual(item.modules, modules, code);
    }
  }
  for (const { modules } of TOPICS) {
    assert.ok(modules.length > 0);
    for (const n of modules) assert.ok(Number.isInteger(n) && n >= 1 && n <= 12);
  }
  assert.deepEqual(DEEP_LINK_SOURCES, ["ig", "tg", "yt"]);
  assert.deepEqual(LIMITS, {
    nameMin: 2, nameMax: 80, ageMin: 18, ageMax: 99,
    phoneMinDigits: 9, phoneMaxDigits: 15, commentMax: 500, payloadMaxBytes: 4096,
  });
});

test("fixed UI copy matches section 9 verbatim in Cyrillic and Latin spot checks", () => {
  for (const [key, expected] of Object.entries(SPEC_UI_CYR)) {
    assert.equal(UI.cyr[key], expected, `cyr.${key}`);
  }
  for (const [key, expected] of Object.entries(LATIN_SPOT_CHECKS)) {
    assert.equal(UI.lat[key], expected, `lat.${key}`);
  }
});

test("hero banner sources exist and initial HTML uses the Cyrillic source", () => {
  for (const script of ["cyr", "lat"]) {
    assert.ok(existsSync(new URL(`../${UI[script].heroImageSrc}`, import.meta.url)), `${script} hero banner is missing`);
  }
  const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");
  const heroImage = html.match(/<div class="hero__image"[^>]*><img\b([^>]*)>/u)?.[1];
  assert.ok(heroImage, "hero image is missing");
  assert.equal(heroImage.match(/\bsrc="([^"]+)"/u)?.[1], UI.cyr.heroImageSrc);
  assert.match(heroImage, /\bdata-i18n-src="heroImageSrc"/u);
});

test("UI has equal scripts, required errors, fallback and no emoji", () => {
  assert.deepEqual(Object.keys(UI.cyr).sort(), Object.keys(UI.lat).sort());
  for (const script of ["cyr", "lat"]) {
    for (const key of REQUIRED_UI_KEYS) {
      assert.equal(typeof UI[script][key], "string", `${script}.${key}`);
      assert.ok(UI[script][key].trim(), `${script}.${key}`);
    }
    for (const [key, value] of Object.entries(UI[script])) {
      assert.equal(typeof value, "string", key);
      assert.ok(value.trim(), key);
    }
    for (const key of ERROR_KEYS) assert.ok(UI[script][key], `${script}.${key}`);
    const founderKeys = Object.keys(UI[script]).filter((key) => /^founderP\d+$/u.test(key));
    assert.deepEqual(founderKeys, FOUNDER_KEYS);
    const paragraphs = founderKeys.map((key) => UI[script][key]);
    assert.ok(paragraphs.length >= 2 && paragraphs.length <= 3);
    for (const paragraph of paragraphs) {
      assert.equal(paragraph.includes("\n"), false, `${script} founder paragraph has extra line breaks`);
      assert.equal(paragraph.includes("@"), false, `${script} founder story has a handle`);
      assert.equal(CONTACT_PHONE.test(paragraph), false, `${script} founder story has a phone number`);
      assert.equal(/\d/u.test(paragraph), false, `${script} founder story has a digit`);
    }
    assert.ok(paragraphs.at(-1).endsWith(FOUNDER_ENDING[script]));
  }
  assert.match(UI.cyr.founderP1, /Ўн саккиз йил ногиронлик билан яшадим/u);
  assert.match(UI.cyr.founderP1, /эркин юриш мен учун катта орзу эди/u);
  assert.match(UI.cyr.founderP2, /эркин ҳаракатланаман/u);
  assert.match(UI.cyr.founderP2, /билимларим, изланишларим ва шахсий тажрибам асосида QUANTUM Psychology тизимини яратдим/u);
  assert.match(UI.cyr.founderP3, /инсонларга ўзини яхшироқ англаш/u);
  assert.match(UI.lat.founderP1, /Oʻn sakkiz yil nogironlik bilan yashadim/u);
  assert.match(UI.lat.founderP2, /QUANTUM Psychology tizimini yaratdim/u);
  assert.match(UI.lat.founderP3, /insonlarga oʻzini yaxshiroq anglash/u);
  assert.match(UI.cyr.founderP1, /яшадим/u);
  assert.match(UI.cyr.founderP2, /яратдим/u);
  assert.match(UI.cyr.founderP3, /мақсад қилдим/u);
  assert.match(UI.lat.founderP1, /yashadim/u);
  assert.match(UI.lat.founderP2, /yaratdim/u);
  assert.match(UI.lat.founderP3, /maqsad qildim/u);
  assert.equal(t("heroCta", "lat"), UI.lat.heroCta);
  assert.equal(t("heroCta", "unknown"), UI.cyr.heroCta);
  assert.equal(t("missing_key", "lat"), "missing_key");
  assert.equal(t("toString", "lat"), "toString");
  assert.equal(UI.cyr.openFromBot, "Аризани юбориш учун чатдаги пастки «Бепул суҳбатга ёзилиш» тугмасини босинг");
  for (const value of stringsIn({ MODULES, INTRO, TWELVE_LINE, GOAL_TITLE, GOAL, AUDIENCE_TITLE,
    AUDIENCE, CLOSING, REGIONS, TOPICS, PRIOR, CALL_TIMES, SOURCES, UI })) {
    assert.equal(EMOJI.test(value), false, `Emoji found in ${value}`);
  }
});
