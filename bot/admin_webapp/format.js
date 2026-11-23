const EMPTY_VALUE = "—";
const THIN_SPACE = "\u2009";
const MINUTES_PER_HOUR = 60;
const SECONDS_PER_MINUTE = 60;
const MILLISECONDS_PER_SECOND = 1000;
const TASHKENT_OFFSET_HOURS = 5;
const PERCENT_SCALE = 100;
const BAR_GAP = 2;
const DATE_PART_WIDTH = 2;
const DASHBOARD_NUMBER = new Intl.NumberFormat("en-US");
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
const ISO_TIMESTAMP = /^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?$/;
const TIME_ZONE_SUFFIX = /(?:Z|[+-]\d{2}:?\d{2})$/;
const HTML_ENTITIES = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};
const REGION_LABELS = {
  tashkent_city: "Тошкент шаҳри",
  tashkent_region: "Тошкент вилояти",
  andijan: "Андижон",
  bukhara: "Бухоро",
  fergana: "Фарғона",
  jizzakh: "Жиззах",
  kashkadarya: "Қашқадарё",
  navoi: "Навоий",
  namangan: "Наманган",
  samarkand: "Самарқанд",
  surkhandarya: "Сурхондарё",
  syrdarya: "Сирдарё",
  khorezm: "Хоразм",
  karakalpakstan: "Қорақалпоғистон Республикаси",
  abroad: "Хорижда",
};
const TOPIC_LABELS = {
  family: "Оила ва муносабатлар",
  parents: "Ота-она ва ўтмиш",
  fear: "Қўрқув ва хавотир",
  money: "Пул ва даромад",
  health: "Соғлиқ ва тана",
  selfworth: "Ўз қадри ва чегаралар",
  support: "Ички таянч",
  fatigue: "Чарчоқ",
};

export function formatNumber(value) {
  if (!Number.isFinite(value)) return EMPTY_VALUE;
  return DASHBOARD_NUMBER.format(value).replaceAll(",", THIN_SPACE).replace(".", ",");
}

export function formatPercent(value) {
  return Number.isFinite(value) ? `${formatNumber(value)}%` : EMPTY_VALUE;
}

export function formatTashkent(iso, kind = "datetime") {
  if (typeof iso !== "string") return EMPTY_VALUE;

  let timestamp;
  if (ISO_DATE.test(iso)) {
    timestamp = iso;
  } else if (ISO_TIMESTAMP.test(iso)) {
    timestamp = iso.replace(" ", "T");
    if (!TIME_ZONE_SUFFIX.test(timestamp)) timestamp += "Z";
  } else {
    return EMPTY_VALUE;
  }

  const millisecondsPerHour = MINUTES_PER_HOUR * SECONDS_PER_MINUTE * MILLISECONDS_PER_SECOND;
  const date = new Date(Date.parse(timestamp) + TASHKENT_OFFSET_HOURS * millisecondsPerHour);
  if (!Number.isFinite(date.getTime())) return EMPTY_VALUE;

  const pad = (value) => String(value).padStart(DATE_PART_WIDTH, "0");
  const day = `${pad(date.getUTCDate())}.${pad(date.getUTCMonth() + 1)}`;
  const time = `${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())}`;
  if (kind === "date") return day;
  if (kind === "time") return time;
  return `${day} ${time}`;
}

export function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => HTML_ENTITIES[character]);
}

export function regionLabel(region) {
  return Object.hasOwn(REGION_LABELS, region) ? REGION_LABELS[region] : region;
}

export function topicLabel(topic) {
  return Object.hasOwn(TOPIC_LABELS, topic) ? TOPIC_LABELS[topic] : topic;
}

function normalizeQuery(query) {
  return String(query ?? "").trim().toLowerCase();
}

function includesText(value, query) {
  return String(value ?? "").toLowerCase().includes(query);
}

function matchesUsername(value, query) {
  const usernameQuery = query.replace(/^@/, "");
  return usernameQuery !== "" && includesText(String(value ?? "").replace(/^@/, ""), usernameQuery);
}

export function matchLead(row, query) {
  const text = normalizeQuery(query);
  const digits = text.replace(/\D/g, "");
  return text === ""
    || includesText(row.name, text)
    || includesText(row.region, text)
    || includesText(regionLabel(row.region), text)
    || matchesUsername(row.tg_username, text)
    || (digits !== "" && String(row.phone ?? "").replace(/\D/g, "").includes(digits));
}

export function matchUser(row, query) {
  const text = normalizeQuery(query);
  return text === ""
    || includesText(row.tg_full_name, text)
    || matchesUsername(row.tg_username, text);
}

export function sourceConversion(users, leads) {
  return users > 0 ? Math.round(leads / users * PERCENT_SCALE) : null;
}

export function dayIndexAt(x, width, count) {
  if (width <= 0 || count < 1) return null;
  const index = Math.floor(x * count / width);
  return Math.min(count - 1, Math.max(0, index));
}

export function chartGeometry(daily, width, height) {
  const slotWidth = daily.length ? width / daily.length : 0;
  const barWidth = Math.max(0, slotWidth - BAR_GAP);

  function series(key) {
    const max = daily.reduce((peak, day) => Math.max(peak, day[key]), 0);
    const bars = daily.map((day, index) => {
      const barHeight = max > 0 ? day[key] / max * height : 0;
      const slotX = index * slotWidth;
      return {
        slotX,
        x: slotX + (slotWidth - barWidth) / 2,
        y: height - barHeight,
        width: barWidth,
        height: barHeight,
      };
    });
    return { max, bars };
  }

  return { slotWidth, users: series("users"), leads: series("leads") };
}
