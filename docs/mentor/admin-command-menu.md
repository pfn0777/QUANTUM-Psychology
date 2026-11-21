# Admin-only command menu
Holat: TUGADI
Ijrochi: codex
Turi: ISH · Hajm: KICHIK
Spec: yo'q
Boshlangan: 2026-11-21

## Karta
Maqsad: bot startida set_my_commands: default scope → /start; BotCommandScopeChat(ADMIN_CHAT_ID) → /start, /stats, /export.
Qilinmaydi: handler mantig'i, ruxsat tekshiruvi, deploy, push.
Qabul mezonlari: test 2 scope va buyruqlar ro'yxatini tekshiradi; set_my_commands xatosi botni yiqitmaydi (log); to'liq pytest o'tadi.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. bot.py + texts.py + tests/test_bot.py + tests/test_catalog.py (commit c1ffd52)
Tekshiruv: pytest 126/126 passed.

## Qarorlar
- Oddiy user menyusida faqat /start (foydalanuvchi tanlovi).
- Admin menyusiga /export ham qo'shildi (foydalanuvchi tanlovi).
- Tavsiflar kirillcha: «Ботни бошлаш», «Статистика», «Аризаларни юклаб олиш (CSV)».

## Foydalanuvchi vazifalari
- [ ] Serverga deploy (o'zingiz so'raganda).
