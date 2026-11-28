import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const read = (path) => readFileSync(fileURLToPath(new URL(path, import.meta.url)), "utf8");
const files = {
  welcome: read("../welcome.html"),
  poster: read("../poster.html"),
  css: read("../posters.css"),
};
const shared = [
  "12 ОЙЛИК ДАСТУР",
  "QUANTUM",
  "Psychology",
  "12 ойлик шахсий ва руҳий ривожланиш дастури",
  "Фикр кучини бошқариш",
  "Ички мувозанат ва хотиржамлик",
  "Ҳаёт сифатини юксалтириш",
  "Ички имкониятингизни очинг — янги даражага чиқинг",
];
const cta = "БЕПУЛ СУҲБАТГА ЁЗИЛИШ ТУГМАСИНИ БОСИНГ";
const allowed = new Set((
  "#FBF6EC #F2E8D8 #C9A050 #3B2112 #8C6420 #F1D79A #E9D6B0 " +
  "#5A3620 #6B5340 #2B1A0E #2A170B #D9B66E #FFFDF7 #F4EAD7 " +
  "#FBE9B4 #E0B65E #A9792B #D9AE55 #7A5518 #B98A3A"
).toUpperCase().split(" "));

test("exact copy and page-specific CTA", () => {
  for (const [name, html] of [["welcome", files.welcome], ["poster", files.poster]]) {
    for (const phrase of shared) assert.ok(html.includes(phrase), `${name}: missing ${phrase}`);
    assert.match(html, /<html lang="uz-Cyrl">/);
    assert.match(html, /href="\.\.\/\.\.\/webapp\/fonts\.css"/);
    assert.match(html, /href="posters\.css"/);
  }
  const welcomeCta = files.welcome.match(/<div class="cta">([\s\S]*?)<\/div>/)?.[1];
  assert.ok(welcomeCta, "welcome: missing CTA");
  assert.equal(welcomeCta.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim(), cta);
  assert.ok(!files.poster.includes(cta));
  assert.match(files.welcome, /class="chevron"/);
  assert.doesNotMatch(files.poster, /class="chevron"|class="cta"/);
});

test("no old Latin copy, emoji, or purple styling", () => {
  const oldCopy = /OYLIK|Fikr kuchini|Ichki|Hayot|BEPUL SUHBATGA/;
  const purple = /#(?:160536|7b2cf0|9b5cff|24074f)\b|\b(?:violet|purple|lavender|neon)\b/i;
  for (const [name, content] of Object.entries(files)) {
    assert.doesNotMatch(content, oldCopy, name);
    assert.doesNotMatch(content, /\p{Extended_Pictographic}/u, name);
    assert.doesNotMatch(content, purple, name);
  }
});

test("only approved hex colors", () => {
  for (const [name, content] of Object.entries(files)) {
    for (const [hex] of content.matchAll(/#[0-9a-fA-F]{3,8}\b/g)) {
      assert.ok(allowed.has(hex.toUpperCase()), `${name}: unexpected color ${hex}`);
    }
  }
});
