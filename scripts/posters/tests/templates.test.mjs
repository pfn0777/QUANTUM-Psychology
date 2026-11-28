import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const WELCOME_SIZE = 1254;
const path = (relative) => fileURLToPath(new URL(relative, import.meta.url));
const read = (relative) => readFileSync(path(relative), "utf8");
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

test("welcome gold template", () => {
  assert.match(files.welcome, /<html lang="uz-Cyrl">/);
  assert.match(files.welcome, /href="\.\.\/\.\.\/webapp\/fonts\.css"/);
  assert.match(files.welcome, /href="posters\.css"/);
  assert.match(files.welcome, /src="assets\/welcome-gold\.png"/);
  assert.ok(files.welcome.includes(shared.at(-1)));
  assert.doesNotMatch(files.welcome, /имкониятигеизни/);
});

test("welcome gold source is 1254px PNG", () => {
  const png = readFileSync(path("../assets/welcome-gold.png"));
  assert.equal(png.subarray(0, 8).toString("hex"), "89504e470d0a1a0a");
  assert.equal(png.toString("ascii", 12, 16), "IHDR");
  assert.equal(png.readUInt32BE(16), WELCOME_SIZE);
  assert.equal(png.readUInt32BE(20), WELCOME_SIZE);
});

test("poster copy and page-specific CTA", () => {
  for (const phrase of shared) assert.ok(files.poster.includes(phrase), `poster: missing ${phrase}`);
  assert.match(files.poster, /<html lang="uz-Cyrl">/);
  assert.match(files.poster, /href="\.\.\/\.\.\/webapp\/fonts\.css"/);
  assert.match(files.poster, /href="posters\.css"/);
  assert.ok(!files.poster.includes(cta));
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
