# Restore commands menu button
Holat: TUGADI
Ijrochi: codex
Turi: ISH · Hajm: KICHIK
Spec: yo'q
Boshlangan: 2026-11-27

## Karta
Maqsad: admin/viewer chatlarida pastki chap tugma yana "Menyu" (komandalar) bo'lsin; vizual statistika faqat /admin inline tugmasi orqali.
Qilinmaydi: /admin inline tugma, Mini App, oddiy userlar menyusi o'zgarmaydi.
Qabul mezonlari: setup_commands admin (agar >0) + viewerlarga MenuButtonCommands o'rnatadi, panel_url bo'sh bo'lsa ham; xato bo'lsa log va davom; testlar o'tadi.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. bot/bot.py setup_commands: MenuButtonWebApp -> MenuButtonCommands + testlar (commit 2d6f425; 442 passed)

## Qarorlar
- Telegram per-chat menu button'ni eslab qoladi, shuning uchun aktiv MenuButtonCommands o'rnatiladi (shunchaki kodni o'chirish yetmaydi).

## Foydalanuvchi vazifalari
- [ ] Botni serverda qayta deploy qilish
