import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { buildBrowserArgs, findBrowser, FONT_WAIT_MS, parseArgs } from "../render.mjs";

const HTML = import.meta.filename;

test("parseArgs accepts an existing HTML file and positive integer dimensions", () => {
  assert.deepEqual(parseArgs([HTML, "poster.png", "400", "300"]), {
    html: HTML, out: "poster.png", width: 400, height: 300,
  });
});

test("parseArgs rejects missing arguments and missing HTML", () => {
  assert.throws(() => parseArgs([HTML, "poster.png", "400"]), /Usage:/);
  assert.throws(() => parseArgs([path.join(os.tmpdir(), "missing-poster-template.html"), "poster.png", "400", "300"]), /HTML file does not exist/);
});

for (const [width, height] of [["-1", "300"], ["400", "0"], ["1.5", "300"], ["400", "2.5"]]) {
  test(`parseArgs rejects invalid dimensions ${width}x${height}`, () => {
    assert.throws(() => parseArgs([HTML, "poster.png", width, height]), /positive integers/);
  });
}

test("findBrowser returns the first existing candidate", () => {
  assert.equal(findBrowser(["first", "second", "third"], (candidate) => candidate !== "first"), "second");
});

test("findBrowser reports when no browser exists", () => {
  assert.throws(() => findBrowser(["first"], () => false), /Chrome or Edge not found/);
});

test("buildBrowserArgs sets the screenshot size, absolute path, and HTML URL", () => {
  const args = buildBrowserArgs({ html: HTML, out: "poster.png", width: 400, height: 300 });
  assert.ok(args.includes("--headless=new"));
  assert.ok(args.includes("--disable-gpu"));
  assert.ok(args.includes("--hide-scrollbars"));
  assert.ok(args.includes("--force-device-scale-factor=1"));
  assert.ok(args.includes(`--virtual-time-budget=${FONT_WAIT_MS}`));
  assert.ok(args.includes("--window-size=400,300"));
  assert.ok(args.includes(`--screenshot=${path.resolve("poster.png")}`));
  assert.ok(args.includes("--allow-file-access-from-files"));
  assert.ok(!args.includes("--default-background-color=00000000"));
  assert.equal(args.at(-1), pathToFileURL(HTML).href);
});
