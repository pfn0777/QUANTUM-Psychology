// telegram-web-app.js reports platform "unknown" when the page is opened outside Telegram.
const OUTSIDE_TELEGRAM_PLATFORM = "unknown";

// Keyboard-button launches have empty initData. Inline/menu launches have full initData,
// where sendData does not work.
export function canSendToBot(webApp) {
  return Boolean(
    webApp &&
      typeof webApp.sendData === "function" &&
      !webApp.initData &&
      webApp.platform &&
      webApp.platform !== OUTSIDE_TELEGRAM_PLATFORM,
  );
}
