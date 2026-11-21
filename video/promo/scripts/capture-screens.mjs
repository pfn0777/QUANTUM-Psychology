import { createServer } from "node:http";
import { existsSync } from "node:fs";
import { readFile, readdir, mkdir } from "node:fs/promises";
import { homedir } from "node:os";
import { extname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const VIEWPORT = { width: 390, height: 844, deviceScaleFactor: 3 };
const MODULE_COUNT = 12;
const TOPIC_COUNT = 2;
const FORM_BUTTON_BOTTOM_GAP = 110;
const SECTION_TOP_GAP = 28;
const SUPPORTED_HYPERFRAMES_VERSIONS = ["0.9.72", "0.9.77"];
const STORAGE_KEY = "qp_script";
const LATIN_SCRIPT = "lat";
const CYRILLIC_SCRIPT = "cyr";
const SAMPLE_NAMES = { cyr: "Мадина Каримова", lat: "Madina Karimova" };
const scriptDir = resolve(fileURLToPath(new URL(".", import.meta.url)));
const promoDir = resolve(scriptDir, "..");
const webRoot = resolve(promoDir, "..", "..", "webapp");
const screensDir = join(promoDir, "assets", "screens");
const latinScreensDir = join(promoDir, "assets", "screens-lat");
const telegramScript = "https://telegram.org/js/telegram-web-app.js";
const mimeTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
  ".woff2": "font/woff2",
};

function parseCaptureOptions(args) {
  if (args.length === 0) return { script: CYRILLIC_SCRIPT, measureToggleLat: false };
  if (args.length === 1 && args[0] === "--measure-toggle-lat") {
    return { script: CYRILLIC_SCRIPT, measureToggleLat: true };
  }
  if (args.length === 2 && args[0] === "--script" && [CYRILLIC_SCRIPT, LATIN_SCRIPT].includes(args[1])) {
    return { script: args[1], measureToggleLat: false };
  }
  throw new Error("Usage: node capture-screens.mjs [--script cyr|lat | --measure-toggle-lat]");
}

async function loadPuppeteer() {
  try {
    return (await import("puppeteer-core")).default;
  } catch (error) {
    if (error.code !== "ERR_MODULE_NOT_FOUND") throw error;
    console.info("Project-local puppeteer-core is unavailable; checking the cached HyperFrames browser dependency.");
  }

  const npmCache = process.env.npm_config_cache ?? join(homedir(), "AppData", "Local", "npm-cache");
  const npxDir = join(npmCache, "_npx");
  if (!existsSync(npxDir)) {
    throw new Error("puppeteer-core is unavailable. Run npm install in video/promo or provide the HyperFrames CLI cache.");
  }
  for (const entry of await readdir(npxDir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const modulesDir = join(npxDir, entry.name, "node_modules");
    const hyperframesPackage = join(modulesDir, "hyperframes", "package.json");
    const puppeteerEntry = join(modulesDir, "puppeteer-core", "lib", "puppeteer", "puppeteer-core.js");
    if (!existsSync(hyperframesPackage) || !existsSync(puppeteerEntry)) continue;
    const { version } = JSON.parse(await readFile(hyperframesPackage, "utf8"));
    if (!SUPPORTED_HYPERFRAMES_VERSIONS.includes(version)) continue;
    console.info(`Using puppeteer-core bundled with cached HyperFrames ${version}.`);
    return (await import(pathToFileURL(puppeteerEntry).href)).default;
  }
  throw new Error("puppeteer-core is unavailable. Run npm install in video/promo before capturing screens.");
}

function findChrome() {
  const candidates = [
    process.env.CHROME_PATH,
    join(process.env.PROGRAMFILES ?? "C:\\Program Files", "Google", "Chrome", "Application", "chrome.exe"),
    join(process.env["PROGRAMFILES(X86)"] ?? "C:\\Program Files (x86)", "Microsoft", "Edge", "Application", "msedge.exe"),
  ].filter(Boolean);
  const executablePath = candidates.find(existsSync);
  if (!executablePath) throw new Error("No local Chrome or Edge executable found. Set CHROME_PATH.");
  return executablePath;
}

async function serveRequest(request, response) {
  if (request.method !== "GET") {
    response.writeHead(405).end();
    return;
  }
  const pathname = decodeURIComponent(new URL(request.url, "http://127.0.0.1").pathname);
  if (pathname === "/telegram-web-app.js") {
    response.writeHead(200, { "Content-Type": mimeTypes[".js"] }).end("");
    return;
  }
  if (pathname === "/favicon.ico") {
    response.writeHead(204).end();
    return;
  }
  const filePath = resolve(webRoot, `.${pathname === "/" ? "/index.html" : pathname}`);
  const pathWithinRoot = relative(webRoot, filePath);
  if (pathWithinRoot.startsWith(`..${sep}`) || pathWithinRoot === ".." || pathWithinRoot.startsWith(sep)) {
    response.writeHead(403).end();
    return;
  }
  let content;
  try {
    content = await readFile(filePath);
  } catch (error) {
    if (error.code === "ENOENT" || error.code === "EISDIR") {
      response.writeHead(404).end("Not found");
      return;
    }
    throw error;
  }
  if (filePath === join(webRoot, "index.html")) {
    const html = content.toString("utf8");
    if (!html.includes(telegramScript)) throw new Error("Telegram script URL changed in webapp/index.html.");
    content = Buffer.from(html.replace(telegramScript, "/telegram-web-app.js"));
  }
  response.writeHead(200, { "Content-Type": mimeTypes[extname(filePath)] ?? "application/octet-stream" }).end(content);
}

async function startServer() {
  const server = createServer((request, response) => {
    serveRequest(request, response).catch((error) => {
      console.error("Static server error:", error);
      if (response.headersSent) response.destroy(error);
      else response.writeHead(500).end("Internal server error");
    });
  });
  await new Promise((resolveListen, rejectListen) => {
    server.once("error", rejectListen);
    server.listen(0, "127.0.0.1", resolveListen);
  });
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("Unable to determine the local server port.");
  return { server, url: `http://127.0.0.1:${address.port}/` };
}

async function waitForPageAssets(page, script) {
  await page.waitForFunction((expectedModules) =>
    document.querySelectorAll("#modulesList .module-card").length === expectedModules &&
    document.querySelectorAll("#topicsList input[type=checkbox]").length >= 2 &&
    document.querySelectorAll("#region option[value]:not([value=''])").length > 0,
  {}, MODULE_COUNT);
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(Array.from(document.images, (image) => image.decode()));
  });
  await page.addStyleTag({ content: "html { scroll-behavior: auto !important; } *, *::before, *::after { animation: none !important; transition: none !important; }" });
  const language = await page.evaluate(() => document.documentElement.lang);
  const expectedLanguage = script === LATIN_SCRIPT ? "uz-Latn" : "uz-Cyrl";
  if (language !== expectedLanguage) throw new Error(`Expected ${expectedLanguage} mode, got ${language}.`);
  if (script === LATIN_SCRIPT) {
    const heroImage = await page.$eval(".hero__image img", (image) => image.currentSrc);
    if (!heroImage.endsWith("/assets/hero-banner.webp")) {
      throw new Error(`Expected Latin hero banner, got ${heroImage}.`);
    }
  }
}

async function scrollToElement(page, selector, gap = SECTION_TOP_GAP) {
  await page.$eval(selector, (element, offset) => {
    const top = window.scrollY + element.getBoundingClientRect().top - offset;
    window.scrollTo(0, Math.max(0, top));
  }, gap);
}

async function captureViewport(page, name, outputDir) {
  await page.screenshot({ path: join(outputDir, name), captureBeyondViewport: false });
  console.info(`Captured ${name}`);
}

async function captureModulesLong(page, outputDir) {
  const clip = await page.$eval("#modulesList", (list, viewportWidth) => {
    const section = list.closest("section");
    if (!section) throw new Error("Modules section is missing.");
    const rect = section.getBoundingClientRect();
    return { x: 0, y: rect.top + window.scrollY, width: viewportWidth, height: rect.height };
  }, VIEWPORT.width);
  await page.screenshot({ path: join(outputDir, "02-modules-long.png"), clip, captureBeyondViewport: true });
  console.info("Captured 02-modules-long.png");
}

async function selectFirstRealOption(page, selector) {
  const value = await page.$eval(selector, (select) => Array.from(select.options).find((option) => option.value)?.value);
  if (!value) throw new Error(`No real option available for ${selector}.`);
  await page.select(selector, value);
  return value;
}

async function fillForm(page, script, outputDir) {
  const sampleName = SAMPLE_NAMES[script];
  await page.type("#name", sampleName);
  await page.type("#age", "29");
  await page.$eval("#phone", (input) => {
    input.value = "+998 90 123 45 67";
    input.dispatchEvent(new Event("input", { bubbles: true }));
  });
  const region = await selectFirstRealOption(page, "#region");
  await selectFirstRealOption(page, "#prior");
  await selectFirstRealOption(page, "#call_time");
  await selectFirstRealOption(page, "#source");
  if (script === LATIN_SCRIPT) {
    const selectedLabels = await page.$$eval("#region, #prior, #call_time, #source", (selects) =>
      selects.map((select) => select.selectedOptions[0]?.textContent ?? ""));
    if (selectedLabels.some((label) => /[\u0400-\u04FF]/u.test(label))) {
      throw new Error(`Expected Latin form options, got ${JSON.stringify(selectedLabels)}.`);
    }
  }
  await page.$$eval("#topicsList input[type=checkbox]", (inputs, count) => {
    if (inputs.length < count) throw new Error("Insufficient topic options.");
    inputs.slice(0, count).forEach((input) => input.click());
  }, TOPIC_COUNT);
  await page.click("#consent");
  const state = await page.evaluate(() => ({
    name: document.querySelector("#name").value,
    age: document.querySelector("#age").value,
    phone: document.querySelector("#phone").value,
    region: document.querySelector("#region").value,
    topics: document.querySelectorAll("#topicsList input:checked").length,
    prior: document.querySelector("#prior").value,
    callTime: document.querySelector("#call_time").value,
    source: document.querySelector("#source").value,
    consent: document.querySelector("#consent").checked,
    submitEnabled: !document.querySelector("#submitButton").disabled,
  }));
  if (state.name !== sampleName || state.age !== "29" ||
      state.phone !== "+998 90 123 45 67" || state.region !== region ||
      state.topics !== TOPIC_COUNT || !state.prior || !state.callTime || !state.source ||
      !state.consent || !state.submitEnabled) {
    throw new Error(`Form state is incomplete: ${JSON.stringify(state)}`);
  }
  await scrollToElement(page, ".section--form");
  await captureViewport(page, "03a-form-top.png", outputDir);
  await page.$eval("#submitButton", (button, bottomGap) => {
    const top = window.scrollY + button.getBoundingClientRect().bottom - window.innerHeight + bottomGap;
    window.scrollTo(0, Math.max(0, top));
  }, FORM_BUTTON_BOTTOM_GAP);
}

async function captureScreens(options) {
  const outputDir = options.script === LATIN_SCRIPT ? latinScreensDir : screensDir;
  if (!options.measureToggleLat) await mkdir(outputDir, { recursive: true });
  const puppeteer = await loadPuppeteer();
  const { server, url } = await startServer();
  let browser;
  try {
    console.info("Launching headless browser.");
    browser = await puppeteer.launch({
      executablePath: findChrome(),
      headless: true,
      pipe: true,
      userDataDir: join(promoDir, "renders", `capture-browser-profile-${process.pid}`),
      args: ["--disable-gpu", "--disable-gpu-compositing", "--disable-background-networking", "--disable-sync", "--no-first-run", "--no-sandbox"],
    });
    console.info("Browser launched.");
    const page = await browser.newPage();
    await page.setViewport(VIEWPORT);
    await page.emulateMediaFeatures([{ name: "prefers-reduced-motion", value: "reduce" }]);
    if (options.script === LATIN_SCRIPT) {
      await page.evaluateOnNewDocument((key, value) => window.localStorage.setItem(key, value), STORAGE_KEY, LATIN_SCRIPT);
    }
    const pageErrors = [];
    page.on("pageerror", (error) => { pageErrors.push(error); console.error("Page error:", error); });
    page.on("requestfailed", (request) => console.error(`Request failed: ${request.url()} (${request.failure()?.errorText})`));
    console.info(`Loading ${url}`);
    const response = await page.goto(url, { waitUntil: "networkidle0" });
    if (response?.status() !== 200) throw new Error(`Mini app returned HTTP ${response?.status()}.`);
    console.info("Page loaded; waiting for dynamic content and assets.");
    await waitForPageAssets(page, options.script);
    if (pageErrors.length) throw new AggregateError(pageErrors, "Mini app failed to initialize.");

    if (options.measureToggleLat) {
      const css = await page.$eval("#toggleLat", (button) => {
        const { x, y, width, height } = button.getBoundingClientRect();
        return { x, y, width, height };
      });
      const screenshot = Object.fromEntries(Object.entries(css).map(([key, value]) => [key, value * VIEWPORT.deviceScaleFactor]));
      console.info(`Lotin button bounding box: ${JSON.stringify({ css, screenshot })}`);
      return;
    }

    await page.evaluate(() => window.scrollTo(0, 0));
    await captureViewport(page, "01-hero.png", outputDir);
    await scrollToElement(page, ".section--about");
    await captureViewport(page, "05-about.png", outputDir);
    await scrollToElement(page, "#modulesList", SECTION_TOP_GAP + 90);
    await captureViewport(page, "02-modules.png", outputDir);
    await captureModulesLong(page, outputDir);
    await fillForm(page, options.script, outputDir);
    await captureViewport(page, "03-form.png", outputDir);
    await page.evaluate(() => {
      document.querySelector("#leadForm").hidden = true;
      document.querySelector("#successPanel").hidden = false;
    });
    await scrollToElement(page, ".section--form");
    await captureViewport(page, "04-success.png", outputDir);
    if (pageErrors.length) throw new AggregateError(pageErrors, "Mini app failed during capture.");
  } finally {
    try {
      if (browser) await browser.close();
    } finally {
      await new Promise((resolveClose, rejectClose) => server.close((error) => error ? rejectClose(error) : resolveClose()));
    }
  }
}

Promise.resolve().then(() => captureScreens(parseCaptureOptions(process.argv.slice(2)))).catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
