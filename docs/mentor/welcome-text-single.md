# /start welcome: single text
Holat: TUGADI
Ijrochi: codex
Turi: ISH · Hajm: KICHIK
Spec: yo'q
Boshlangan: 2026-11-21

## Karta
Maqsad: /start da bitta matn: rasm + yangi caption + inline «Қўшимча маълумотлар»; keyin «👇» + reply keyboard (web app).
Qilinmaydi: rasm, tugma nomlari, URL, ariza oqimi o'zgarmaydi; deploy/push yo'q.
Qabul mezonlari: /start 2 xabar yuboradi; eski 3 matn kodda yo'q; `pytest bot/tests -q` yashil.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. texts.py + bot.py + testlar (commit d008083, 126/126 passed)

## Foydalanuvchi vazifalari
- [ ] Hetznerga deploy va Telegram'da /start ni tekshirish

## Qarorlar
- Foydalanuvchi tanlovi: inline tugma rasmga ulanadi, reply keyboard «👇» xabari bilan o'rnatiladi (Telegram bitta xabarga ikki xil markup ulamaydi).
- Lotin matni — cyr matnning tarjimasi (taxmin, kartada tasdiqlangan).
