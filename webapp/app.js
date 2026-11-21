import {
  INTRO, TWELVE_LINE, MODULES, GOAL_TITLE, GOAL, AUDIENCE_TITLE, AUDIENCE,
  CLOSING, REGIONS, TOPICS, PRIOR, CALL_TIMES, SOURCES, DEEP_LINK_SOURCES, LIMITS,
} from "./data.js";
import { t } from "./i18n.js";
import { payloadBytes, validateLead } from "./validate.js";
import { canSendToBot } from "./telegram.js";

const STORAGE_KEY = "qp_script";
const DEFAULT_SCRIPT = "cyr";
const LATIN_SCRIPT = "lat";
const PHONE_COUNTRY_CODE = "998";
const PHONE_PREFIX = `+${PHONE_COUNTRY_CODE} `;
const PHONE_GROUPS = [2, 3, 2, 2];
const NATIONAL_PHONE_DIGITS = PHONE_GROUPS.reduce((sum, count) => sum + count, 0);
const MODULE_NUMBER_WIDTH = 2;
const SUBMIT_FALLBACK_MS = 900;
const tg = window.Telegram?.WebApp;
const inTelegram = canSendToBot(tg);
const querySource = new URLSearchParams(window.location.search).get("src");
const deepLinkSource = DEEP_LINK_SOURCES.includes(querySource) ? querySource : null;

const $ = (id) => document.getElementById(id);
const state = {
  script: readScript(),
  selectedTopics: new Set(),
  errors: {},
  messageKey: inTelegram ? null : "openFromBot",
  submitting: false,
  sent: false,
};

function readScript() {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === LATIN_SCRIPT ? LATIN_SCRIPT : DEFAULT_SCRIPT;
  } catch (error) {
    console.warn("Unable to read script preference", error);
    return DEFAULT_SCRIPT;
  }
}

function saveScript(script) {
  try {
    window.localStorage.setItem(STORAGE_KEY, script);
  } catch (error) {
    console.warn("Unable to save script preference", error);
  }
}

function element(tag, className, content) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (content !== undefined) node.textContent = content;
  return node;
}

function renderCopy() {
  document.documentElement.lang = state.script === LATIN_SCRIPT ? "uz-Latn" : "uz-Cyrl";
  document.title = t("heroTitle", state.script);
  for (const node of document.querySelectorAll("[data-i18n]")) {
    node.textContent = t(node.dataset.i18n, state.script);
  }
  for (const node of document.querySelectorAll("[data-i18n-placeholder]")) {
    node.placeholder = t(node.dataset.i18nPlaceholder, state.script);
  }
  for (const node of document.querySelectorAll("[data-i18n-aria-label]")) {
    node.setAttribute("aria-label", t(node.dataset.i18nAriaLabel, state.script));
  }
  for (const node of document.querySelectorAll("[data-i18n-src]")) {
    const value = t(node.dataset.i18nSrc, state.script);
    if (node.getAttribute("src") !== value) node.src = value;
  }
  $("introText").textContent = INTRO[state.script];
  $("twelveLine").textContent = TWELVE_LINE[state.script];
  $("goalTitle").textContent = GOAL_TITLE[state.script];
  $("goalText").textContent = GOAL[state.script];
  $("audienceTitle").textContent = AUDIENCE_TITLE[state.script];
  $("closingText").textContent = CLOSING[state.script];
  for (const button of document.querySelectorAll("[data-script]")) {
    button.setAttribute("aria-pressed", String(button.dataset.script === state.script));
  }
}

function renderModules() {
  const cards = MODULES.map((module) => {
    const card = element("article", "module-card");
    card.dataset.module = String(module.n);
    card.append(
      element("span", "module-card__number", String(module.n).padStart(MODULE_NUMBER_WIDTH, "0")),
      element("h3", "module-card__title", module.title[state.script]),
      element("p", "module-card__text", module.text[state.script]),
    );
    return card;
  });
  $("modulesList").replaceChildren(...cards);
  highlightModules();
}

function highlightModules() {
  const related = new Set(TOPICS.filter(({ code }) => state.selectedTopics.has(code)).flatMap(({ modules }) => modules));
  for (const card of $("modulesList").children) {
    card.classList.toggle("is-related", related.has(Number(card.dataset.module)));
  }
}

function renderAudience() {
  const items = AUDIENCE.map((item) => {
    const li = element("li", "audience-list__item");
    const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    icon.setAttribute("viewBox", "0 0 24 24");
    icon.setAttribute("aria-hidden", "true");
    icon.classList.add("line-icon");
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", "M4 12.5 9.5 18 20 6");
    icon.append(path);
    li.append(icon, element("span", "", item[state.script]));
    return li;
  });
  $("audienceList").replaceChildren(...items);
}

function renderSelect(id, catalog) {
  const select = $(id);
  const value = select.value;
  const placeholder = select.firstElementChild;
  const options = catalog.map(({ code, label }) => {
    const option = element("option", "", label[state.script]);
    option.value = code;
    return option;
  });
  select.replaceChildren(placeholder, ...options);
  select.value = value;
}

function renderTopics() {
  const chips = TOPICS.map(({ code, label }) => {
    const chip = element("label", "topic-chip");
    const input = element("input");
    input.type = "checkbox";
    input.name = "topics";
    input.value = code;
    input.checked = state.selectedTopics.has(code);
    chip.append(input, element("span", "", label[state.script]));
    return chip;
  });
  $("topicsList").replaceChildren(...chips);
}

function renderFormOptions() {
  renderSelect("region", REGIONS);
  renderSelect("prior", PRIOR);
  renderSelect("call_time", CALL_TIMES);
  renderSelect("source", SOURCES);
  if (deepLinkSource) $("source").value = deepLinkSource;
  $("sourceField").hidden = Boolean(deepLinkSource);
  renderTopics();
}

function renderErrors() {
  for (const node of document.querySelectorAll("[data-error-for]")) {
    const key = state.errors[node.dataset.errorFor];
    node.hidden = !key;
    node.textContent = key ? t(key, state.script) : "";
    const field = node.closest("[data-field]");
    field?.classList.toggle("has-error", Boolean(key));
    const input = field?.querySelector("input, select, textarea");
    if (input) input.setAttribute("aria-invalid", String(Boolean(key)));
  }
  const payloadError = state.errors.payload;
  if (payloadError) state.messageKey = payloadError;
  renderMessage();
}

function renderMessage() {
  const message = $("formMessage");
  message.hidden = !state.messageKey;
  message.textContent = state.messageKey ? t(state.messageKey, state.script) : "";
}

function updateSubmitButton() {
  const button = $("submitButton");
  button.disabled = !$("consent").checked || state.submitting || state.sent;
  button.textContent = t(state.submitting ? "sending" : "submit", state.script);
}

function updateCommentCounter() {
  $("commentCounter").textContent = `${Array.from($("comment").value).length} / ${LIMITS.commentMax}`;
}

function render() {
  renderCopy();
  renderModules();
  renderAudience();
  renderFormOptions();
  renderErrors();
  updateCommentCounter();
  updateSubmitButton();
}

function formatPhone(value) {
  const entered = value.replace(/\D/gu, "");
  if (!entered) return value.startsWith("+") ? "+" : "";
  if (value.startsWith("+") && entered && PHONE_COUNTRY_CODE.startsWith(entered) &&
      entered.length < PHONE_COUNTRY_CODE.length) return `+${entered}`;
  const digits = (entered.startsWith(PHONE_COUNTRY_CODE)
    ? entered.slice(PHONE_COUNTRY_CODE.length)
    : entered).slice(0, NATIONAL_PHONE_DIGITS);
  let index = 0;
  const parts = [];
  for (const length of PHONE_GROUPS) {
    const part = digits.slice(index, index + length);
    if (part) parts.push(part);
    index += length;
  }
  return `${PHONE_PREFIX}${parts.join(" ")}`.trimEnd();
}

function collectForm() {
  return {
    name: $("name").value,
    age: $("age").value,
    phone: $("phone").value,
    region: $("region").value,
    topics: TOPICS.filter(({ code }) => state.selectedTopics.has(code)).map(({ code }) => code),
    prior: $("prior").value,
    call_time: $("call_time").value,
    source: $("source").value,
    ...(deepLinkSource ? { src: deepLinkSource } : {}),
    comment: $("comment").value,
    consent: $("consent").checked,
  };
}

function showFirstError() {
  document.querySelector(".field__error:not([hidden])")?.closest("[data-field]")?.scrollIntoView({
    behavior: "smooth", block: "center",
  });
}

function finish() {
  if (!state.sent) return;
  $("successPanel").hidden = false;
  $("leadForm").hidden = true;
  $("successPanel").scrollIntoView({ behavior: "smooth", block: "center" });
}

function submit(event) {
  event.preventDefault();
  if (state.submitting || state.sent) return;

  if (!inTelegram) {
    state.messageKey = "openFromBot";
    renderMessage();
    $("formMessage").scrollIntoView({ behavior: "smooth", block: "center" });
    return;
  }

  const result = validateLead(collectForm(), state.script);
  state.errors = result.ok ? {} : result.errors;
  state.messageKey = null;
  renderErrors();
  if (!result.ok) {
    showFirstError();
    return;
  }
  if (payloadBytes(result.payload) > LIMITS.payloadMaxBytes) {
    state.messageKey = "invalid_payload";
    renderMessage();
    return;
  }

  state.submitting = true;
  updateSubmitButton();
  try {
    tg.sendData(JSON.stringify(result.payload));
    state.sent = true;
    window.setTimeout(finish, SUBMIT_FALLBACK_MS);
  } catch (error) {
    console.warn("Unable to send lead through Telegram", error);
    state.submitting = false;
    state.messageKey = "sendFailed";
    renderMessage();
    updateSubmitButton();
  }
}

for (const button of document.querySelectorAll("[data-script]")) {
  button.addEventListener("click", () => {
    if (state.script === button.dataset.script) return;
    state.script = button.dataset.script;
    saveScript(state.script);
    render();
  });
}

$("topicsList").addEventListener("change", (event) => {
  if (!(event.target instanceof HTMLInputElement)) return;
  if (event.target.checked) state.selectedTopics.add(event.target.value);
  else state.selectedTopics.delete(event.target.value);
  highlightModules();
  if (state.selectedTopics.size) {
    delete state.errors.topics;
    renderErrors();
  }
});

$("phone").addEventListener("input", (event) => {
  event.target.value = formatPhone(event.target.value);
});
$("comment").addEventListener("input", updateCommentCounter);
$("consent").addEventListener("change", updateSubmitButton);
$("leadForm").addEventListener("submit", submit);

$("name").maxLength = LIMITS.nameMax;
$("age").min = String(LIMITS.ageMin);
$("age").max = String(LIMITS.ageMax);
$("comment").maxLength = LIMITS.commentMax;
render();

if (tg) {
  try {
    tg.ready();
    tg.expand();
  } catch (error) {
    console.warn("Unable to initialize Telegram WebApp", error);
  }
}
