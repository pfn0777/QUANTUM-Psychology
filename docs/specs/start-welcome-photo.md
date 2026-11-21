# /start: welcome photo + inline Mini App button (hybrid)

## Maqsad
Mijoz /start bosganda: Mini App hero rasmi + qisqa "xush kelibsiz" matni + rasm tagida inline "Бепул суҳбатга ёзилиш" tugmasi (Mini App ochiladi). Arizalar yo'qolmasligi uchun pastki (reply keyboard) tugma ham qoladi.

## Kontekst
- Bot: aiogram 3, `bot/bot.py` (`BotHandlers.start`, `keyboard()` — `src` deep-link qo'shadi), matnlar `bot/texts.py` (cyr/lat), testlar `bot/tests/test_bot.py::test_start_source_and_unknown`, `bot/tests/test_catalog.py`.
- Mini App: `webapp/telegram.js::canSendToBot`, `webapp/app.js` (`!inTelegram` bo'lsa `openFromBot` xabari), `webapp/i18n.js`, testlar `webapp/tests/*.mjs` (`node --test`).
- Telegram cheklovi: `sendData` faqat keyboard-button launch'da ishlaydi. Keyboard launch'da `initData` bo'sh, inline/menu launch'da to'la.

## Chegaralar
- Qilinadi: /start → 2 xabar (1: rasm+caption+inline web_app tugma; 2: `start_greeting` + reply keyboard). Mini App inline'dan ochilsa "Yuborish" → pastki tugmaga yo'naltiruvchi xabar.
- Qilinmaydi: server endpoint, HTTP orqali ariza yuborish, deploy, push.
- Tegilmaydi: `leads.py`, `storage.py`, `stats.py`, `catalog.py`, `webapp/validate.js`, `data.js`.

## Qabul mezonlari
- [ ] /start → `answer_photo` (welcome.png, caption = `welcome_caption`, InlineKeyboardMarkup, web_app URL `src` bilan)
- [ ] /start → 2-xabar `start_greeting` + reply keyboard
- [ ] Rasm yuborishda xato → log, 2-xabar baribir yuboriladi
- [ ] `canSendToBot` initData to'la bo'lsa `false`
- [ ] `openFromBot`: «Аризани юбориш учун чатдаги пастки «Бепул суҳбатга ёзилиш» тугмасини босинг» (lat mos)
- [ ] `bot/assets/welcome.png` mavjud, hero aniq, < 1 MB

## Caption
cyr: «Ассалому алайкум! QUANTUM Psychology'га хуш келибсиз. 12 ойлик шахсий ва руҳий ривожланиш дастури. Бепул дастлабки суҳбатга ёзилиш учун қуйидаги тугмани босинг.»
lat: «Assalomu alaykum! QUANTUM Psychology'ga xush kelibsiz. 12 oylik shaxsiy va ruhiy rivojlanish dasturi. Bepul dastlabki suhbatga yozilish uchun quyidagi tugmani bosing.»

## Xavf
Avval Vercel (webapp), keyin bot deploy — aks holda inline tugma eski Mini App'ni ochadi va ariza yo'qoladi.
