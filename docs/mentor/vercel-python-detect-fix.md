# Vercel deploy: Python detection fix
Holat: TUGADI
Ijrochi: codex
Turi: XATO · Hajm: KICHIK
Spec: yo'q
Boshlangan: 2026-11-21

## Karta
Maqsad: Vercel `webapp/` ni statik sayt sifatida deploy qilsin (PYTHON_ENTRYPOINT_NOT_FOUND yo'qolsin).
Sabab: vercel.json da framework yo'q → Vercel repodagi bot/*.py, requirements.txt, pytest.ini ni ko'rib Python preset tanlagan.
Qilinmaydi: bot/webapp kodi, Hetzner deploy, Vercel dashboard sozlamalari.
Qabul mezonlari: vercel.json valid JSON, framework/buildCommand/installCommand = null; .vercelignore bot/, scripts/, deploy/, docs/, pytest.ini ni chiqaradi; `node --test webapp/tests` o'tadi.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. vercel.json + .vercelignore (commit a4448c0, 1-urinishda; webapp testlari 35/35)

## Kichik topilmalar (keyinroq)
- `node --test webapp/tests` (papka) Node 26 da MODULE_NOT_FOUND beradi; `node --test webapp/tests/*.test.mjs` ishlaydi. README/hujjatlarda shu buyruq bo'lsa yangilash kerak.

## Qarorlar
- Vercel MCP loyihani ko'rmadi; dashboard preset tekshirilmadi. vercel.json framework override ishlatiladi.

## Foydalanuvchi vazifalari
- [ ] git push → Vercel build logini tekshirish
- [ ] Baribir yiqilsa: Settings → Build and Deployment → Framework Preset → Other
