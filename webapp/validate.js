import { REGIONS, TOPICS, PRIOR, CALL_TIMES, SOURCES, DEEP_LINK_SOURCES, LIMITS } from "./data.js";

const CYRILLIC_LETTER = /^[\u0400-\u052f]$/u;
const LATIN_LETTER = /^[A-Za-z]$/u;
const ALPHABETIC = /^\p{L}$/u;
const NAME_PUNCTUATION = new Set(["\u02bb", "\u02bc", "\u2018", "\u2019", "'", "-", " "]);
// Python str.split()/strip() whitespace, matching bot/leads.py.
const PYTHON_WHITESPACE = /[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+/gu;
const LONE_SURROGATE = /^[\ud800-\udfff]$/u;
const DIGIT = /\d/g;
const CODES = {
  region: new Set(REGIONS.map(({ code }) => code)),
  topics: new Set(TOPICS.map(({ code }) => code)),
  prior: new Set(PRIOR.map(({ code }) => code)),
  call_time: new Set(CALL_TIMES.map(({ code }) => code)),
  source: new Set(SOURCES.map(({ code }) => code)),
};
const DEEP_LINK_CODES = new Set(DEEP_LINK_SOURCES);
const PAYLOAD_VERSION = 1;
const UZBEKISTAN_PHONE_PREFIX = "998";
const UZ_NATIONAL_DIGITS = LIMITS.phoneMinDigits;
const UZ_PHONE_GROUPS = [2, 3, 2, 2];
const UZ_PHONE_DISPLAY_PREFIX = `+${UZBEKISTAN_PHONE_PREFIX} `;
const UZ_FULL_DIGITS =UZBEKISTAN_PHONE_PREFIX.length + UZ_NATIONAL_DIGITS;

function isNameLetter(character) {
  return LATIN_LETTER.test(character) ||
    (CYRILLIC_LETTER.test(character) && ALPHABETIC.test(character));
}

function stripPythonWhitespace(value) {
  return value.replace(PYTHON_WHITESPACE, (run, offset) =>
    offset === 0 || offset + run.length === value.length ? "" : run);
}

export function normalizePhone(value) {
  if (typeof value !== "string") return "";
  const input = stripPythonWhitespace(value);
  const digits = (input.match(DIGIT) ?? []).join("");
  const isUz = digits.startsWith(UZBEKISTAN_PHONE_PREFIX);
  if (input.startsWith("+")) {
    if (isUz) return digits.length === UZ_FULL_DIGITS ? `+${digits}` : "";
    return digits.length >= LIMITS.phoneMinDigits && digits.length <= LIMITS.phoneMaxDigits ? `+${digits}` : "";
  }
  if (digits.length === UZ_NATIONAL_DIGITS) return `+${UZBEKISTAN_PHONE_PREFIX}${digits}`;
  if (digits.length === UZ_FULL_DIGITS && isUz) return `+${digits}`;
  return "";
}

export function formatPhone(value) {
  const entered = value.replace(/\D/gu, "");
  const plus = value.startsWith("+");
  if (!entered) return plus ? "+" : "";
  if (plus && UZBEKISTAN_PHONE_PREFIX.startsWith(entered) &&
      entered.length < UZBEKISTAN_PHONE_PREFIX.length) return `+${entered}`;
  if (plus && !entered.startsWith(UZBEKISTAN_PHONE_PREFIX)) {
    return `+${entered.slice(0, LIMITS.phoneMaxDigits)}`;
  }
  const stripCode = entered.startsWith(UZBEKISTAN_PHONE_PREFIX) &&
    (plus || entered.length > UZ_NATIONAL_DIGITS);
  const digits = (stripCode ? entered.slice(UZBEKISTAN_PHONE_PREFIX.length) : entered)
    .slice(0, UZ_NATIONAL_DIGITS);
  let index = 0;
  const parts = [];
  for (const length of UZ_PHONE_GROUPS) {
    const part = digits.slice(index, index + length);
    if (part) parts.push(part);
    index += length;
  }
  return `${UZ_PHONE_DISPLAY_PREFIX}${parts.join(" ")}`.trimEnd();
}

export function payloadBytes(payload) {
  return new TextEncoder().encode(JSON.stringify(payload)).length;
}

export function validateLead(form, script) {
  const fields = form && typeof form === "object" ? form : {};
  const errors = {};

  const name = typeof fields.name === "string"
    ? fields.name.replace(PYTHON_WHITESPACE, " ").replace(/^ +| +$/gu, "")
    : "";
  const nameCharacters = Array.from(name);
  const nameLength = nameCharacters.length;
  if (
    nameLength < LIMITS.nameMin || nameLength > LIMITS.nameMax ||
    nameCharacters.some((character) => !isNameLetter(character) && !NAME_PUNCTUATION.has(character)) ||
    nameCharacters.filter(isNameLetter).length < LIMITS.nameMin
  ) errors.name = "err_name";

  const ageInput = fields.age;
  const age = typeof ageInput === "number" ? ageInput :
    typeof ageInput === "string" && /^\d+$/u.test(ageInput) ? Number(ageInput) : NaN;
  if (!Number.isInteger(age) || age < LIMITS.ageMin || age > LIMITS.ageMax) errors.age = "err_age";

  const phone = normalizePhone(fields.phone);
  if (!phone) errors.phone = "err_phone";

  for (const field of ["region", "prior", "call_time"]) {
    if (!CODES[field].has(fields[field])) errors[field] = `err_${field}`;
  }

  const topics = Array.isArray(fields.topics) ? [...new Set(fields.topics)] : [];
  if (!topics.length || topics.length > CODES.topics.size || topics.some((code) => !CODES.topics.has(code))) {
    errors.topics = "err_topics";
  }

  const source = DEEP_LINK_CODES.has(fields.src) ? fields.src : fields.source;
  if (!CODES.source.has(source)) errors.source = "err_source";
  // Python rejects any lone surrogate when encoding the original comment as UTF-8.
  if (fields.comment !== undefined &&
      (typeof fields.comment !== "string" || Array.from(fields.comment).some((character) => LONE_SURROGATE.test(character)))) {
    errors.comment = "invalid_payload";
  }
  if (fields.consent !== true) errors.consent = "err_consent";

  if (Object.keys(errors).length) return { ok: false, errors };

  const comment = typeof fields.comment === "string"
    ? Array.from(stripPythonWhitespace(fields.comment)).slice(0, LIMITS.commentMax).join("")
    : "";
  const payload = {
    v: PAYLOAD_VERSION,
    name,
    age,
    phone,
    region: fields.region,
    topics,
    prior: fields.prior,
    call_time: fields.call_time,
    source,
    comment,
    consent: true,
    script: script === "lat" ? "lat" : "cyr",
  };
  if (payloadBytes(payload) > LIMITS.payloadMaxBytes) {
    return { ok: false, errors: { payload: "invalid_payload" } };
  }
  return { ok: true, payload };
}
