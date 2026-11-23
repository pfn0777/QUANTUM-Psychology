import {
  chartGeometry, dayIndexAt, formatNumber, formatPercent, formatTashkent, matchLead, matchUser,
  regionLabel, sourceConversion, topicLabel,
} from "./format.js";

const TAB_KEY = "admin-tab";
const RECENT_LIMIT = 200;
const DASHBOARD_DAYS = 30;
const SEARCH_DELAY_MS = 150;
const EXPORT_STATUS_MS = 4000;
const CHART = { width: 300, height: 96, radius: 2 };
const PRIMARY_POINTER_BUTTON = 0;
const SOURCE_BAR = { height: 6, radius: 3, scale: 100 };
const BACKGROUND = "#160536";
const SVG_NAMESPACE = "http://www.w3.org/2000/svg";
const USERNAME = /^[A-Za-z0-9_]{5,32}$/;
const DIRECT_SOURCE = "Тўғридан-тўғри";
const SEARCH_PLACEHOLDER = "Исм, телефон ёки username";
const CLEAR_SEARCH = "Тозалаш";
const HTTP = { ok: 200, unauthorized: 401, forbidden: 403, rateLimited: 429, badGateway: 502 };
const KPI = [
  ["Жами фойдаланувчилар", "users", formatNumber],
  ["Ариза қолдирганлар", "lead_users", formatNumber],
  ["Конверсия", "conversion_pct", formatPercent],
  ["Фаол, 7 кун", "active_7d", formatNumber],
];
const PERIODS = [
  ["Бугун", "today"],
  ["7 кун", "7d"],
  ["30 кун", "30d"],
];
const LISTS = {
  leads: {
    match: matchLead,
    empty: "Ҳали ариза йўқ. Мижозлар Mini App орқали ариза юборганда шу ерда кўринади.",
    exportLabel: "Аризалар CSV — чатга юбориш",
  },
  users: {
    match: matchUser,
    empty: "Ҳали ҳеч ким ботга кирмаган. /start босганлар шу ерда кўринади.",
    exportLabel: "Фойдаланувчилар CSV — чатга юбориш",
  },
};
const STATES = {
  outside: {
    title: "Панел фақат Telegram ичида очилади",
    detail: "Ботдаги /admin тугмаси орқали очинг.",
    icon: "M21 4 3 11l7 2 2 7 9-16ZM10 13 21 4",
  },
  expired: {
    title: "Сессия муддати тугади",
    detail: "Панелни ёпиб, қайта очинг.",
    icon: "M12 7v5l3 2m6-2a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
    action: "Ёпиш",
    run: () => telegram?.close?.(),
  },
  forbidden: {
    title: "Рухсат йўқ",
    detail: "Бу панел фақат статистика кўрувчилар учун. Админга мурожаат қилинг.",
    icon: "M6 10h12v10H6zm2 0V7a4 4 0 0 1 8 0v3m-4 4v2",
  },
  error: {
    title: "Маълумотни юклаб бўлмади",
    detail: "Интернетни текширинг ва қайта уриниб кўринг.",
    icon: "M12 8v5m0 3h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
    action: "Қайта уриниш",
    run: () => fetchDashboard(),
  },
};

let elements;
let telegram;
let activeTab = "overview";
let dashboardData;
let dashboardRequest;
let exporting = false;
let resetChart;
const lists = {};

function element(tag, className = "", content) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (content != null) node.textContent = content;
  return node;
}

function button(className, content) {
  const node = element("button", className, content);
  node.type = "button";
  return node;
}

function svgElement(tag, attributes) {
  const node = document.createElementNS(SVG_NAMESPACE, tag);
  for (const [name, value] of Object.entries(attributes)) {
    node.setAttribute(name, value);
  }
  return node;
}

function icon(path, className) {
  const svg = svgElement("svg", { viewBox: "0 0 24 24", "aria-hidden": "true", class: className });
  svg.append(svgElement("path", { d: path }));
  return svg;
}

function selectTab(name, { focus = false, remember = false } = {}) {
  const changed = activeTab !== name;
  activeTab = name;
  for (const tab of elements.tabs) {
    const selected = tab.dataset.tab === name;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    const panel = document.getElementById(tab.dataset.tab);
    panel.hidden = !selected;
    panel.classList.toggle("panel-enter", selected && changed);
    if (selected && focus) tab.focus();
  }
  if (!changed) return;

  resetChart?.();
  window.scrollTo(0, 0);
  if (remember) {
    try {
      sessionStorage.setItem(TAB_KEY, name);
    } catch {
      console.warn("Could not save the active admin tab.");
    }
  }
}

function mount() {
  if (elements) return;
  const byId = (id) => document.getElementById(id);
  elements = {
    updated: byId("updated-at"),
    refresh: byId("refresh"),
    refreshError: byId("refresh-error"),
    state: byId("state"),
    dashboard: byId("dashboard"),
    overview: byId("overview"),
    tabs: [...document.querySelectorAll("[data-tab]")],
  };

  try {
    const saved = sessionStorage.getItem(TAB_KEY);
    if (elements.tabs.some((tab) => tab.dataset.tab === saved)) activeTab = saved;
  } catch {
    console.warn("Could not restore the active admin tab.");
  }
  selectTab(activeTab);

  elements.tabs.forEach((tab, index, tabs) => {
    tab.addEventListener("click", () => selectTab(tab.dataset.tab, { remember: true }));
    tab.addEventListener("keydown", (event) => {
      const destinations = {
        ArrowLeft: (index + tabs.length - 1) % tabs.length,
        ArrowRight: (index + 1) % tabs.length,
        Home: 0,
        End: tabs.length - 1,
      };
      if (!Object.hasOwn(destinations, event.key)) return;
      event.preventDefault();
      selectTab(tabs[destinations[event.key]].dataset.tab, { focus: true, remember: true });
    });
  });

  elements.refresh.addEventListener("click", fetchDashboard);
  document.addEventListener("click", (event) => {
    if (!event.target.closest(".chart-section")) resetChart?.();
  });
}

function skeleton() {
  const block = element("div", "loading-blocks");
  const tiles = element("div", "kpi-grid");
  for (const _ of KPI) tiles.append(element("div", "skeleton skeleton-tile"));
  block.setAttribute("aria-hidden", "true");
  block.append(tiles, element("div", "skeleton skeleton-table"), element("div", "skeleton skeleton-chart"));
  return block;
}

export function renderState(state) {
  mount();
  dashboardRequest?.abort();
  dashboardData = undefined;
  resetChart = undefined;
  elements.dashboard.hidden = true;
  elements.overview.replaceChildren();
  for (const view of Object.values(lists)) {
    clearTimeout(view.searchTimer);
    clearTimeout(view.statusTimer);
    view.input.value = "";
    view.results.replaceChildren();
    view.status.textContent = "";
  }
  elements.updated.textContent = "";
  elements.updated.removeAttribute("datetime");
  elements.updated.hidden = true;
  elements.refresh.hidden = true;
  elements.refreshError.textContent = "";
  elements.state.hidden = false;
  elements.state.setAttribute("aria-busy", String(state === "loading"));

  if (state === "loading") {
    elements.state.replaceChildren(element("p", "sr-only", "Юкланмоқда"), skeleton());
    return;
  }

  const { title, detail, icon: path, action, run } = STATES[state];
  const card = element("div", "state-card");
  card.append(icon(path, "state-icon"), element("h2", "", title), element("p", "", detail));
  if (action) {
    const control = button("secondary-button", action);
    control.addEventListener("click", run);
    card.append(control);
  }
  elements.state.replaceChildren(card);
}

function buildKpis(totals) {
  const grid = element("dl", "kpi-grid");
  for (const [label, key, format] of KPI) {
    const tile = element("div", "kpi-tile");
    tile.append(element("dt", "meta", label));
    tile.append(element("dd", key === "lead_users" ? "lead-value" : "", format(totals[key])));
    grid.append(tile);
  }
  return grid;
}

function buildPeriodTable(totals) {
  const table = element("table", "period-table");
  const head = table.createTHead().insertRow();
  for (const label of ["Давр", "Янги фойдаланувчи", "Ариза"]) {
    const cell = element("th", "", label);
    cell.scope = "col";
    head.append(cell);
  }
  const body = table.createTBody();
  for (const [label, key] of PERIODS) {
    const row = body.insertRow();
    const period = element("th", "", label);
    period.scope = "row";
    row.append(period, element("td", "", formatNumber(totals[`users_${key}`])),
      element("td", "lead-value", formatNumber(totals[`leads_${key}`])));
  }
  const section = element("div", "surface period-section");
  section.append(table);
  return section;
}

function chartSeries(series, kind, label, summary) {
  const block = element("div", `chart-series series-${kind}`);
  const heading = element("div", "series-header");
  heading.append(element("h3", "series-title", label),
    element("span", "meta", `макс ${formatNumber(series.max)}`));
  const svg = svgElement("svg", {
    viewBox: `0 0 ${CHART.width} ${CHART.height}`,
    preserveAspectRatio: "none",
    role: "img",
    "aria-label": summary,
  });
  svg.append(svgElement("line", {
    class: "chart-baseline", x1: 0, x2: CHART.width, y1: CHART.height, y2: CHART.height,
  }));
  const bars = series.bars.map(({ x, y, width, height }) => {
    if (height === 0) return null;
    const bar = svgElement("rect", { class: "chart-bar", x, y, width, height, rx: CHART.radius });
    svg.append(bar);
    return bar;
  });
  block.append(heading, svg);
  return { block, bars };
}

function chartSummary(label, users, leads) {
  return `${label}: ${formatNumber(users)} фойдаланувчи · ${formatNumber(leads)} ариза`;
}

function buildChart(daily, totals) {
  const section = element("section", "surface chart-section");
  const heading = element("h2", "", "30 кунлик динамика");
  heading.id = "chart-title";
  section.append(heading);
  const geometry = chartGeometry(daily, CHART.width, CHART.height);
  resetChart = undefined;
  if (!geometry.users.max && !geometry.leads.max) {
    section.append(element("p", "muted", "30 кунда ҳали маълумот йўқ"));
    return section;
  }

  const summary = chartSummary("30 кунда", totals.users_30d, totals.leads_30d);
  const reading = element("p", "chart-reading", summary);
  reading.id = "chart-reading";
  reading.setAttribute("aria-live", "polite");
  const users = chartSeries(geometry.users, "users", "Фойдаланувчилар", summary);
  const leads = chartSeries(geometry.leads, "leads", "Аризалар", summary);
  const dateAt = (index) => formatTashkent(daily[index].date, "date");
  const axis = element("div", "chart-axis meta");
  const midpoint = Math.floor(daily.length / 2);
  for (const label of [dateAt(0), dateAt(midpoint), "Бугун"]) axis.append(element("span", "", label));

  const plots = element("div", "chart-plots");
  plots.tabIndex = 0;
  plots.setAttribute("role", "group");
  plots.setAttribute("aria-labelledby", heading.id);
  plots.setAttribute("aria-describedby", reading.id);
  plots.setAttribute("aria-keyshortcuts", "ArrowLeft ArrowRight Home End Escape");
  plots.append(users.block, leads.block, axis);

  let selected = null;
  function select(index) {
    if (index === selected) return;
    selected = index;
    reading.textContent = index === null ? summary : chartSummary(dateAt(index), daily[index].users, daily[index].leads);
    for (const series of [users, leads]) {
      series.bars.forEach((bar, day) => bar?.classList.toggle("dimmed", index !== null && day !== index));
    }
  }

  function dayAtPointer(event) {
    const { left, width } = plots.getBoundingClientRect();
    return dayIndexAt(event.clientX - left, width, daily.length);
  }

  let pointerDay = null;
  resetChart = () => select(null);
  plots.addEventListener("pointerdown", (event) => {
    if (!event.isPrimary || event.button !== PRIMARY_POINTER_BUTTON) return;
    const index = dayAtPointer(event);
    if (index === null) return;
    pointerDay = index;
    plots.setPointerCapture(event.pointerId);
    select(index === selected ? null : index);
  });
  plots.addEventListener("pointermove", (event) => {
    if (!plots.hasPointerCapture(event.pointerId)) return;
    const index = dayAtPointer(event);
    if (index === null || index === pointerDay) return;
    pointerDay = index;
    select(index);
  });
  plots.addEventListener("keydown", (event) => {
    const last = daily.length - 1;
    const destinations = {
      ArrowLeft: selected === null ? last : Math.max(0, selected - 1),
      ArrowRight: selected === null ? 0 : Math.min(last, selected + 1),
      Home: 0,
      End: last,
      Escape: null,
    };
    if (!Object.hasOwn(destinations, event.key)) return;
    event.preventDefault();
    select(destinations[event.key]);
  });
  section.append(plots, reading);
  return section;
}

function buildSources(sources) {
  const section = element("section", "surface sources-section");
  section.append(element("h2", "", "Манбалар (30 кун)"));
  if (sources.length === 0) {
    section.append(element("p", "muted", "Ҳали манба маълумоти йўқ"));
    return section;
  }

  const max = sources.reduce((peak, { users, leads }) => Math.max(peak, users, leads), 0);
  const list = element("ul", "source-list");
  list.setAttribute("role", "list");
  const ranked = [...sources].sort((first, second) => second.users - first.users);
  for (const { label, users, leads } of ranked) {
    const row = element("li", "source-row");
    const heading = element("div", "source-heading");
    const values = element("p", "meta source-values");
    values.append(`${formatNumber(users)} · `, element("span", "lead-value", formatNumber(leads)),
      ` · ${formatPercent(sourceConversion(users, leads))}`);
    heading.append(element("h3", "", label ?? DIRECT_SOURCE), values);
    row.append(heading);

    const bars = element("div", "source-bars");
    bars.setAttribute("aria-hidden", "true");
    for (const [kind, count] of [["users", users], ["leads", leads]]) {
      const width = max > 0 ? count / max * SOURCE_BAR.scale : 0;
      const svg = svgElement("svg", {
        class: `series-${kind}`, width: `${width}%`, height: SOURCE_BAR.height,
      });
      svg.append(svgElement("rect", { width: "100%", height: SOURCE_BAR.height, rx: SOURCE_BAR.radius }));
      bars.append(svg);
    }
    row.append(bars);
    list.append(row);
  }
  section.append(list);
  return section;
}

function timeNode(iso) {
  const time = element("time", "meta", formatTashkent(iso));
  if (typeof iso === "string") time.dateTime = iso;
  return time;
}

function usernameNode(value) {
  if (!value) return null;
  if (!USERNAME.test(value)) return element("span", "muted", `@${value}`);
  const url = `https://t.me/${value}`;
  const link = element("a", "contact-link", `@${value}`);
  link.href = url;
  link.addEventListener("click", (event) => {
    if (telegram?.openTelegramLink) {
      event.preventDefault();
      telegram.openTelegramLink(url);
    }
  });
  return link;
}

function phoneNode(value) {
  if (!value) return null;
  const phone = value.replace(/[^\d+]/g, "");
  if (!/^\+?\d+$/.test(phone)) return element("span", "lead-value", value);
  const link = element("a", "contact-link lead-value", value);
  link.href = `tel:${phone}`;
  return link;
}

function buildLead(row, index) {
  const item = element("li", "record");
  const heading = element("div", "record-heading");
  heading.append(element("strong", "", row.name), timeNode(row.created_at));
  item.append(heading);

  const contacts = element("div", "record-contacts");
  for (const contact of [phoneNode(row.phone), usernameNode(row.tg_username)]) {
    if (contact) contacts.append(contact);
  }
  if (contacts.childNodes.length) item.append(contacts);

  const meta = element("div", "record-meta meta");
  meta.append(element("span", "chip", row.source_label ?? DIRECT_SOURCE));
  for (const value of [regionLabel(row.region), row.age]) {
    if (value != null && value !== "") meta.append(element("span", "", "·"), element("span", "", value));
  }
  item.append(meta);

  if (row.topics.length) {
    const toggle = button("topic-toggle");
    const topics = element("span", "topics", row.topics.map(topicLabel).join(" · "));
    toggle.setAttribute("aria-expanded", "false");
    toggle.append(topics, icon("m6 9 6 6 6-6", "topic-chevron"));
    const expand = () => toggle.setAttribute("aria-expanded", String(toggle.getAttribute("aria-expanded") === "false"));
    toggle.addEventListener("click", expand);
    item.addEventListener("click", (event) => {
      if (!event.target.closest("a, button")) expand();
    });
    topics.id = `topics-${index}`;
    toggle.setAttribute("aria-controls", topics.id);
    item.append(toggle);
  }
  return item;
}

function buildUser(row) {
  const item = element("li", "record");
  const heading = element("div", "record-heading");
  heading.append(element("strong", "", row.tg_full_name));
  if (row.has_lead) heading.append(element("span", "chip lead-value lead-chip", "Ариза бор"));
  const contacts = element("div", "record-contacts meta");
  const username = usernameNode(row.tg_username);
  if (username) contacts.append(username, element("span", "", "·"));
  contacts.append(element("span", "chip", row.source_label ?? DIRECT_SOURCE));
  const dates = element("p", "meta user-dates");
  const first = element("span");
  const last = element("span");
  first.append("Биринчи: ", timeNode(row.first_seen_at));
  last.append("Охирги: ", timeNode(row.last_seen_at));
  dates.append(first, element("span", "", "·"), last);
  item.append(heading, contacts, dates);
  return item;
}

function renderList(kind) {
  const view = lists[kind];
  const query = view.input.value.trim();
  const rows = dashboardData[kind];
  const matches = query ? rows.filter((row) => LISTS[kind].match(row, query)) : rows;
  view.count.textContent = `${formatNumber(matches.length)} та`;
  view.limit.hidden = rows.length !== RECENT_LIMIT;
  view.clear.hidden = view.input.value === "";
  if (!matches.length) {
    const message = element("div", "list-message");
    message.append(element("p", "muted", query ? "Ҳеч нарса топилмади" : LISTS[kind].empty));
    if (query) {
      const clear = button("secondary-button", CLEAR_SEARCH);
      clear.addEventListener("click", view.clearSearch);
      message.append(clear);
    }
    view.results.replaceChildren(message);
    return;
  }

  const list = element("ul", "record-list");
  list.setAttribute("role", "list");
  const buildRow = kind === "leads" ? buildLead : buildUser;
  list.append(...matches.map(buildRow));
  view.results.replaceChildren(list);
}

function mountList(kind) {
  const panel = document.getElementById(kind);
  const search = element("div", "search-row");
  const field = element("div", "search-field");
  const input = element("input");
  input.type = "search";
  input.placeholder = SEARCH_PLACEHOLDER;
  input.setAttribute("aria-label", SEARCH_PLACEHOLDER);
  input.autocomplete = "off";
  const clear = button("icon-button search-clear", "×");
  clear.setAttribute("aria-label", CLEAR_SEARCH);
  field.append(icon("M16 16l4 4m-2-9a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z", "search-icon"), input, clear);
  const count = element("span", "meta search-count");
  count.setAttribute("aria-live", "polite");
  search.append(field, count);

  const results = element("div", "surface record-results");
  const limit = element("p", "meta list-limit",
    `Охирги ${RECENT_LIMIT} таси кўрсатилмоқда. Тўлиқ рўйхат — CSV файлда.`);
  const exportButton = button("export-button", LISTS[kind].exportLabel);
  const status = element("p", "export-status");
  status.setAttribute("aria-live", "polite");
  exportButton.addEventListener("click", () => exportCsv(kind));
  panel.append(search, results, limit, exportButton, status);

  const view = { input, clear, count, results, limit, exportButton, status };
  view.clearSearch = () => {
    clearTimeout(view.searchTimer);
    input.value = "";
    renderList(kind);
    input.focus();
  };
  clear.addEventListener("click", view.clearSearch);
  input.addEventListener("input", () => {
    clear.hidden = input.value === "";
    clearTimeout(view.searchTimer);
    view.searchTimer = setTimeout(() => renderList(kind), SEARCH_DELAY_MS);
  });
  return view;
}

export function render(data) {
  mount();
  dashboardData = data;
  const { totals, daily, sources, generated_at: generatedAt } = data;
  elements.state.hidden = true;
  elements.state.replaceChildren();
  elements.state.setAttribute("aria-busy", "false");
  elements.dashboard.hidden = false;
  elements.refresh.hidden = false;
  elements.updated.hidden = false;
  elements.updated.dateTime = generatedAt;
  elements.updated.textContent = `Янгиланди ${formatTashkent(generatedAt, "time")}`;
  elements.refreshError.textContent = "";

  const overview = [buildKpis(totals), buildPeriodTable(totals)];
  if (totals.undelivered > 0) {
    overview.push(element("p", "undelivered", `${formatNumber(totals.undelivered)} та ариза админ чатга етказилмаган`));
  }
  overview.push(buildChart(daily, totals), buildSources(sources));
  elements.overview.replaceChildren(...overview);
  for (const kind of Object.keys(LISTS)) {
    lists[kind] ??= mountList(kind);
    clearTimeout(lists[kind].searchTimer);
    renderList(kind);
  }
}

function validateDashboard(data) {
  const count = (value) => Number.isInteger(value) && value >= 0;
  const date = (value) => formatTashkent(value) !== "—";
  const optionalText = (value) => value == null || typeof value === "string";
  const rows = (items, valid) => Array.isArray(items) && items.every((row) => row && valid(row));
  const totals = data?.totals;
  const countKeys = ["users", "active_7d", "lead_users", "undelivered",
    ...PERIODS.flatMap(([, key]) => [`users_${key}`, `leads_${key}`])];
  if (!totals || !date(data.generated_at) || !countKeys.every((key) => count(totals[key]))
    || !(totals.conversion_pct === null || Number.isFinite(totals.conversion_pct))
    || !rows(data.daily, (row) => date(row.date) && count(row.users) && count(row.leads))
    || data.daily.length !== DASHBOARD_DAYS
    || !rows(data.sources, (row) => optionalText(row.label) && count(row.users) && count(row.leads))
    || !rows(data.leads, (row) => date(row.created_at) && typeof row.name === "string"
      && optionalText(row.phone) && optionalText(row.tg_username) && optionalText(row.source_label)
      && optionalText(row.region) && (row.age == null || count(row.age))
      && Array.isArray(row.topics) && row.topics.every((topic) => typeof topic === "string"))
    || !rows(data.users, (row) => date(row.first_seen_at) && date(row.last_seen_at)
      && typeof row.tg_full_name === "string" && optionalText(row.tg_username)
      && optionalText(row.source_label) && typeof row.has_lead === "boolean")) {
    throw new Error("Invalid dashboard response");
  }
  return data;
}

function adminRequest(path, { headers, ...options } = {}) {
  return fetch(path, {
    ...options,
    cache: "no-store",
    headers: { ...headers, Authorization: `tma ${telegram.initData}` },
  });
}

async function showAccessError(response, signal) {
  if (signal?.aborted) return true;
  if (response.status === HTTP.forbidden) {
    renderState("forbidden");
    return true;
  }
  if (response.status === HTTP.unauthorized) {
    let payload;
    try {
      payload = await response.json();
    } catch {
      console.warn("Could not read the admin authorization response.");
    }
    if (!signal?.aborted) renderState(payload?.error === "expired" ? "expired" : "outside");
    return true;
  }
  return false;
}

async function fetchDashboard() {
  if (!telegram?.initData || dashboardRequest) return;
  if (!dashboardData) renderState("loading");
  dashboardRequest = new AbortController();
  const { signal } = dashboardRequest;
  elements.refresh.disabled = true;
  elements.refresh.classList.add("refreshing");
  try {
    const response = await adminRequest("api/dashboard", { signal });
    if (await showAccessError(response, signal) || signal.aborted) return;
    if (response.status !== HTTP.ok) throw new Error("Dashboard request failed");
    const data = validateDashboard(await response.json());
    if (!signal.aborted) render(data);
  } catch {
    if (signal.aborted) return;
    console.warn("Could not load the admin dashboard.");
    if (dashboardData) elements.refreshError.textContent = "Янгилаб бўлмади";
    else renderState("error");
  } finally {
    dashboardRequest = undefined;
    elements.refresh.disabled = false;
    elements.refresh.classList.remove("refreshing");
  }
}

function setExportStatus(view, message, success) {
  view.status.classList.toggle("success", success);
  view.status.textContent = message;
  view.statusTimer = setTimeout(() => { view.status.textContent = ""; }, EXPORT_STATUS_MS);
}

async function exportCsv(kind) {
  if (!telegram?.initData || exporting) return;
  const view = lists[kind];
  exporting = true;
  clearTimeout(view.statusTimer);
  view.status.textContent = "";
  view.exportButton.textContent = "Юборилмоқда…";
  for (const entry of Object.values(lists)) entry.exportButton.disabled = true;
  let status;
  try {
    const response = await adminRequest("api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kind }),
    });
    if (await showAccessError(response)) return;
    status = response.status;
  } catch {
    console.warn("Could not request an admin CSV export.");
  } finally {
    exporting = false;
    view.exportButton.textContent = LISTS[kind].exportLabel;
    for (const entry of Object.values(lists)) entry.exportButton.disabled = false;
  }

  if (!dashboardData) return;
  const messages = {
    [HTTP.ok]: "Файл чатга юборилди",
    [HTTP.rateLimited]: "Бир оз кутинг ва қайта босинг",
    [HTTP.badGateway]: "Юбориб бўлмади. Аввал ботга /start ёзинг",
  };
  const success = status === HTTP.ok;
  setExportStatus(view, messages[status] ?? "Хатолик юз берди. Қайта уриниб кўринг", success);
  if (success) telegram.HapticFeedback?.notificationOccurred?.("success");
}

if (document.querySelector("[data-admin-entry]")) {
  mount();
  telegram = window.Telegram?.WebApp;
  try {
    telegram?.ready?.();
    telegram?.expand?.();
    telegram?.setBackgroundColor?.(BACKGROUND);
    telegram?.setHeaderColor?.(BACKGROUND);
  } catch {
    console.warn("Could not configure the Telegram Mini App.");
  }
  if (telegram?.initData) fetchDashboard();
  else renderState("outside");
}
