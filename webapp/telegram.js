// telegram-web-app.js reports platform "unknown" when the page is opened outside Telegram.
const OUTSIDE_TELEGRAM_PLATFORM = "unknown";

// initData is intentionally not checked: Telegram leaves it empty for Mini Apps
// launched from a reply-keyboard button, which is the only launch mode where sendData works.
export function canSendToBot(webApp) {
  return Boolean(
    webApp &&
      typeof webApp.sendData === "function" &&
      webApp.platform &&
      webApp.platform !== OUTSIDE_TELEGRAM_PLATFORM,
  );
}
