import test from "node:test";
import assert from "node:assert/strict";
import { LIMITS, REGIONS, TOPICS, PRIOR, CALL_TIMES, SOURCES } from "../data.js";
import { validateLead, normalizePhone, payloadBytes } from "../validate.js";

function validForm(overrides = {}) {
  return {
    name: "Aziza Karimova",
    age: "34",
    phone: "+998 90 123 45 67",
    region: REGIONS[0].code,
    topics: [TOPICS[0].code, TOPICS[1].code],
    prior: PRIOR[0].code,
    call_time: CALL_TIMES[0].code,
    source: SOURCES[0].code,
    comment: "  Salom  ",
    consent: true,
    ...overrides,
  };
}

test("valid form becomes a normalized payload", () => {
  assert.deepEqual(validateLead(validForm({ name: "  Aziza   Karimova  " }), "lat"), {
    ok: true,
    payload: {
      v: 1,
      name: "Aziza Karimova",
      age: 34,
      phone: "+998901234567",
      region: REGIONS[0].code,
      topics: [TOPICS[0].code, TOPICS[1].code],
      prior: PRIOR[0].code,
      call_time: CALL_TIMES[0].code,
      source: SOURCES[0].code,
      comment: "Salom",
      consent: true,
      script: "lat",
    },
  });
  assert.equal(validateLead(validForm(), "unknown").payload.script, "cyr");
});

test("normalizes Python whitespace in names", () => {
  const result = validateLead(validForm({ name: "\u0085Aziza\u0085\u001c\u2029Karimova\u0085" }), "lat");
  assert.equal(result.ok, true);
  assert.equal(result.payload.name, "Aziza Karimova");
  assert.equal(validateLead(validForm({ name: "\ufeffAziza Karimova" }), "lat").errors.name, "err_name");
});

for (const name of ["", "A", "A".repeat(LIMITS.nameMax + 1), "Ali!", "A-'"]) {
  test(`rejects invalid name ${JSON.stringify(name)}`, () => {
    assert.equal(validateLead(validForm({ name }), "cyr").errors.name, "err_name");
  });
}

for (const age of [LIMITS.ageMin - 1, LIMITS.ageMax + 1, "abc", " 34 ", 25.5, true]) {
  test(`rejects invalid age ${JSON.stringify(age)}`, () => {
    assert.equal(validateLead(validForm({ age }), "cyr").errors.age, "err_age");
  });
}

const INVALID_PHONES = [
  "12345678", "1234567890123456", "+998 90 123 4", "+998 90 123 45 678",
  "90123456", "79123456789", "+1234567", "+1234567890123456",
];
for (const phone of INVALID_PHONES) {
  test(`rejects invalid phone ${phone}`, () => {
    assert.equal(normalizePhone(phone), "");
    assert.equal(validateLead(validForm({ phone }), "cyr").errors.phone, "err_phone");
  });
}

const VALID_PHONES = [
  ["+998 90 123 45 67", "+998901234567"],
  ["+998 (90) 123-45-67", "+998901234567"],
  ["+7 912 345 67 89", "+79123456789"],
  ["+90 532 123 45 67", "+905321234567"],
  ["901234567", "+998901234567"],
  ["998901234567", "+998901234567"],
  ["998 90 123 45 67", "+998901234567"],
  ["+123 456 789", "+123456789"],
];
for (const [input, expected] of VALID_PHONES) {
  test(`normalizes phone ${input}`, () => {
    assert.equal(normalizePhone(input), expected);
    assert.equal(validateLead(validForm({ phone: input }), "cyr").payload.phone, expected);
  });
}

test("phone strips U+0085 but retains U+FEFF like Python", () => {
  assert.equal(normalizePhone("\u0085+123456789\u0085"), "+123456789");
  // U+FEFF is not whitespace, so the plus is no longer leading: 9 digits become a UZ national number.
  assert.equal(normalizePhone("\ufeff+123456789\ufeff"), "+998123456789");
  assert.equal(validateLead(validForm({ phone: "\u0085+123456789\u0085" }), "lat").payload.phone, "+123456789");
  assert.equal(validateLead(validForm({ phone: "\ufeff+123456789\ufeff" }), "lat").payload.phone, "+998123456789");
});

for (const field of ["region", "prior", "call_time", "source"]) {
  test(`rejects unknown ${field}`, () => {
    assert.equal(validateLead(validForm({ [field]: "unknown" }), "cyr").errors[field], `err_${field}`);
  });
}

test("rejects missing and unknown topics", () => {
  for (const topics of [[], ["unknown"], "family"]) {
    assert.equal(validateLead(validForm({ topics }), "cyr").errors.topics, "err_topics");
  }
});

test("removes duplicate topics while retaining order", () => {
  const topics = [TOPICS[1].code, TOPICS[0].code, TOPICS[1].code];
  assert.deepEqual(validateLead(validForm({ topics }), "cyr").payload.topics, topics.slice(0, 2));
});

test("requires exact consent", () => {
  for (const consent of [false, "true", 1]) {
    assert.equal(validateLead(validForm({ consent }), "cyr").errors.consent, "err_consent");
  }
});

test("valid deep-link src supplies source when the question is hidden", () => {
  const { source: _source, ...form } = validForm({ src: "tg" });
  assert.equal(validateLead(form, "cyr").payload.source, "tg");
  assert.equal(validateLead({ ...form, src: "unknown" }, "cyr").errors.source, "err_source");
  assert.equal(validateLead(validForm({ source: "unknown", src: "yt" }), "cyr").payload.source, "yt");
});

test("trims and truncates overlong comments", () => {
  const comment = `  ${"x".repeat(LIMITS.commentMax + 1)}  `;
  assert.equal(validateLead(validForm({ comment }), "cyr").payload.comment, "x".repeat(LIMITS.commentMax));
});

test("comment strips U+0085 but retains U+FEFF like Python", () => {
  assert.equal(validateLead(validForm({ comment: "\u0085Salom\u0085" }), "cyr").payload.comment, "Salom");
  assert.equal(validateLead(validForm({ comment: "\ufeffSalom\ufeff" }), "cyr").payload.comment, "\ufeffSalom\ufeff");
});

test("rejects a non-string comment before sending", () => {
  assert.equal(validateLead(validForm({ comment: 42 }), "cyr").errors.comment, "invalid_payload");
});

test("rejects lone surrogates in comments before truncation and byte checks", () => {
  for (const comment of ["before\ud800after", `x`.repeat(LIMITS.commentMax) + "\udc00"]) {
    const result = validateLead(validForm({ comment }), "cyr");
    assert.equal(result.ok, false);
    assert.equal(result.errors.comment, "invalid_payload");
  }
  const escapedPayload = { comment: "\ud800" };
  assert.equal(payloadBytes(escapedPayload), Buffer.byteLength(JSON.stringify(escapedPayload), "utf8"));
  assert.ok(payloadBytes(escapedPayload) < LIMITS.payloadMaxBytes);
});

test("maximum-length valid payload fits Telegram's UTF-8 limit", () => {
  const result = validateLead(validForm({
    name: "Ў".repeat(LIMITS.nameMax),
    age: LIMITS.ageMax,
    phone: "+" + "9".repeat(LIMITS.phoneMaxDigits - 1) + "1",
    region: REGIONS.at(-1).code,
    topics: TOPICS.map(({ code }) => code),
    prior: PRIOR.at(-1).code,
    call_time: CALL_TIMES.at(-1).code,
    source: SOURCES.at(-1).code,
    comment: "😀".repeat(LIMITS.commentMax),
  }), "cyr");
  assert.equal(result.ok, true);
  assert.ok(payloadBytes(result.payload) <= LIMITS.payloadMaxBytes);
  assert.equal(payloadBytes({ comment: "😀" }), new TextEncoder().encode(JSON.stringify({ comment: "😀" })).length);
});
