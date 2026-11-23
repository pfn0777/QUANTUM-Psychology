import test from "node:test";
import assert from "node:assert/strict";
import {
  chartGeometry, dayIndexAt, escapeHtml, formatNumber, formatPercent, formatTashkent,
  matchLead, matchUser, regionLabel, sourceConversion, topicLabel,
} from "../format.js";

test("formatNumber groups counts with U+2009 and uses a decimal comma", () => {
  assert.equal(formatNumber(1234567), "1\u2009234\u2009567");
  assert.equal(formatNumber(1234.5), "1\u2009234,5");
  assert.equal(formatNumber(0), "0");
  assert.equal(formatNumber(undefined), "—");
});

test("formatPercent formats a percentage without dropping zero", () => {
  assert.equal(formatPercent(12.5), "12,5%");
  assert.equal(formatPercent(12), "12%");
  assert.equal(formatPercent(0), "0%");
  assert.equal(formatPercent(null), "—");
});

test("formatTashkent applies UTC+5 across midnight and across years", () => {
  assert.equal(formatTashkent("2026-12-31T19:05:42Z"), "01.01 00:05");
  assert.equal(formatTashkent("2026-11-22T09:05:00.123456+00:00", "time"), "14:05");
  assert.equal(formatTashkent("2026-11-21T19:00:00+00:00", "date"), "22.11");
  assert.equal(formatTashkent("2026-11-22", "date"), "22.11");
  assert.equal(formatTashkent("2026-11-22T09:05:00"), "22.11 14:05");
  assert.equal(formatTashkent("invalid"), "—");
});

test("escapeHtml handles script-like names, quotes and ampersands", () => {
  assert.equal(escapeHtml('<script>alert("test & \'test\'")</script>'),
    "&lt;script&gt;alert(&quot;test &amp; &#39;test&#39;&quot;)&lt;/script&gt;");
  assert.equal(escapeHtml("=cmd"), "=cmd");
});

test("matchLead finds mixed-script names, digits, usernames and regions", () => {
  const row = {
    name: "Тест Mijoz",
    phone: "+998 90 123 00 01",
    tg_username: "Test_Mijoz",
    region: "Тошкент",
  };
  assert.equal(matchLead(row, "  ТЕСТ mIjOz "), true);
  assert.equal(matchLead(row, "90 123"), true);
  assert.equal(matchLead(row, "@tEsT_mIjOz"), true);
  assert.equal(matchLead(row, "тошк"), true);
  assert.equal(matchLead({ ...row, region: "tashkent_city" }, "тошк"), true);
  assert.equal(matchLead(row, "номаълум"), false);
  assert.equal(matchLead(row, "@"), false);
  assert.equal(matchLead(row, " "), true);
});

test("catalog labels display Cyrillic and preserve unknown or already formatted values", () => {
  assert.equal(regionLabel("tashkent_city"), "Тошкент шаҳри");
  assert.equal(regionLabel("Тест ҳудуди"), "Тест ҳудуди");
  assert.equal(regionLabel(null), null);
  assert.equal(topicLabel("family"), "Оила ва муносабатлар");
  assert.equal(topicLabel("Чарчоқ"), "Чарчоқ");
  assert.equal(topicLabel("__proto__"), "__proto__");
});

test("matchUser tolerates absent usernames and searches full names and handles", () => {
  const row = { tg_full_name: "Тест User", tg_username: null };
  assert.equal(matchUser(row, "тест u"), true);
  assert.equal(matchUser(row, "@no_user"), false);
  assert.equal(matchUser(row, ""), true);
  assert.equal(matchUser({ ...row, tg_username: "Preview_User" }, "@preview"), true);
});

test("sourceConversion rounds to an integer and handles zero users", () => {
  assert.equal(sourceConversion(3, 2), 67);
  assert.equal(sourceConversion(8, 1), 13);
  assert.equal(sourceConversion(6, 0), 0);
  assert.equal(sourceConversion(0, 2), null);
});

test("chartGeometry shares day slots and scales each series to its own maximum", () => {
  const daily = [{ users: 7, leads: 1 }, { users: 0, leads: 0 }, { users: 14, leads: 4 }];
  const geometry = chartGeometry(daily, 30, 96);
  assert.equal(geometry.slotWidth, 10);
  assert.equal(geometry.users.max, 14);
  assert.equal(geometry.leads.max, 4);
  assert.deepEqual(geometry.users.bars, [
    { slotX: 0, x: 1, y: 48, width: 8, height: 48 },
    { slotX: 10, x: 11, y: 96, width: 8, height: 0 },
    { slotX: 20, x: 21, y: 0, width: 8, height: 96 },
  ]);
  assert.deepEqual(geometry.leads.bars.map((bar) => bar.height), [24, 0, 96]);
});

test("chartGeometry has finite values with empty days or all-zero counts", () => {
  assert.deepEqual(chartGeometry([], 300, 96), {
    slotWidth: 0,
    users: { max: 0, bars: [] },
    leads: { max: 0, bars: [] },
  });
  const geometry = chartGeometry(Array.from({ length: 30 }, () => ({ users: 0, leads: 0 })), 300, 96);
  assert.equal(geometry.slotWidth, 10);
  for (const series of [geometry.users, geometry.leads]) {
    assert.equal(series.max, 0);
    assert.equal(series.bars.length, 30);
    assert.ok(series.bars.every((bar) => bar.height === 0 && bar.y === 96));
  }
});

test("dayIndexAt maps positions to the nearest day and clamps both edges", () => {
  const width = 264;
  const days = 30;
  assert.equal(dayIndexAt(-10, width, days), 0);
  assert.equal(dayIndexAt(0, width, days), 0);
  assert.equal(dayIndexAt(8.79, width, days), 0);
  assert.equal(dayIndexAt(8.8, width, days), 1);
  assert.equal(dayIndexAt(132, width, days), 15);
  assert.equal(dayIndexAt(width, width, days), 29);
  assert.equal(dayIndexAt(width + 10, width, days), 29);
});

test("dayIndexAt handles an empty chart, one day and a zero-width chart", () => {
  assert.equal(dayIndexAt(30, 264, 0), null);
  assert.equal(dayIndexAt(-10, 264, 1), 0);
  assert.equal(dayIndexAt(300, 264, 1), 0);
  assert.equal(dayIndexAt(0, 0, 30), null);
});
