import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

export const FONT_WAIT_MS = 5000;
const BROWSER_TIMEOUT_MS = 30000;

export const DEFAULT_CANDIDATES = [
  ...(process.env.CHROME_PATH ? [process.env.CHROME_PATH] : []),
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
];

export function parseArgs(argv) {
  if (argv.length !== 4) {
    throw new Error("Usage: node scripts/posters/render.mjs <html> <out.png> <width> <height>");
  }

  const [html, out, widthText, heightText] = argv;
  if (!fs.existsSync(html) || !fs.statSync(html).isFile()) {
    throw new Error(`HTML file does not exist: ${html}`);
  }
  if (!out) {
    throw new Error("Output PNG path is required");
  }

  const width = Number(widthText);
  const height = Number(heightText);
  if (!Number.isSafeInteger(width) || width <= 0 || !Number.isSafeInteger(height) || height <= 0) {
    throw new Error("Width and height must be positive integers");
  }

  return { html, out, width, height };
}

export function findBrowser(candidates = DEFAULT_CANDIDATES, exists = fs.existsSync) {
  const browser = candidates.find((candidate) => exists(candidate));
  if (!browser) {
    throw new Error("Chrome or Edge not found");
  }
  return browser;
}

export function buildBrowserArgs({ html, out, width, height }) {
  return [
    "--headless=new",
    "--disable-gpu",
    "--hide-scrollbars",
    "--force-device-scale-factor=1",
    `--virtual-time-budget=${FONT_WAIT_MS}`,
    `--window-size=${width},${height}`,
    `--screenshot=${path.resolve(out)}`,
    "--allow-file-access-from-files",
    pathToFileURL(path.resolve(html)).href,
  ];
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  const browser = findBrowser();
  fs.mkdirSync(path.dirname(path.resolve(options.out)), { recursive: true });

  const result = spawnSync(browser, buildBrowserArgs(options), {
    encoding: "utf8",
    timeout: BROWSER_TIMEOUT_MS,
  });
  if (result.error) {
    throw new Error(`Browser failed: ${result.error.message}`);
  }
  if (result.status !== 0) {
    throw new Error(`Browser exited with status ${result.status}: ${result.stderr || result.stdout}`);
  }
  if (!fs.existsSync(options.out)) {
    throw new Error(`Browser did not create output PNG: ${options.out}`);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    main();
  } catch (error) {
    console.error(error);
    process.exitCode = 1;
  }
}
