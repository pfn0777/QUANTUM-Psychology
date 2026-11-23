# QUANTUM Psychology Telegram bot va Mini App

Bu loyiha 12 modulli dastur haqida ma'lumot beradigan Telegram Mini App va bepul dastlabki suhbat uchun arizalarni qabul qiladigan botdan iborat. Arizalar SQLite bazasiga yoziladi va administrator chatiga yuboriladi. Bot doimiy ishlaydigan serverda, statik Mini App esa Vercel'da ishlaydi.

## Tuzilma

| Yo'l | Vazifasi |
| --- | --- |
| `bot/` | Aiogram bot, arizalar bazasi va Python testlari |
| `bot/data/` | SQLite ma'lumotlari; Git'ga kiritilmaydi |
| `webapp/` | Statik HTML, CSS, JavaScript, shriftlar va testlar |
| `deploy/quantum-bot.service` | Linux systemd xizmat fayli |
| `webapp/vercel.json` | Vercel sozlamasi (Root Directory = webapp) |

## Lokal ishga tushirish

Python 3.11 va Node.js kerak. Loyiha ildizida quyidagilarni bajaring:

```powershell
py -3.11 -m pip install -r bot/requirements.txt
py -3.11 -m pytest -q
node --test "webapp/tests/*.test.mjs"
Copy-Item bot/.env.example bot/.env
```

`bot/.env` qiymatlarini quyidagi ko'rsatmalarga ko'ra to'ldiring. Botni ishga tushirish:

```powershell
Set-Location bot
py -3.11 bot.py
```

`bot/.env` Git tomonidan e'tiborsiz qoldiriladi. Uni repozitoriyga qo'shmang.

## BotFather va administrator ID

Telegram'da `@BotFather` bilan `/newbot` orqali bot yarating. U bergan tokenni `bot/.env` ichidagi `BOT_TOKEN` ga kiriting; tokenni hech kimga yubormang.

Xabar oladigan shaxs o'z Telegram akkauntidan `@userinfobot` ga `/start` yuborib, qaytgan raqamli ID'ni `ADMIN_CHAT_ID` sifatida yozishi mumkin. Administrator botga ham kamida bir marta `/start` yuborsin, aks holda bot unga birinchi bo'lib xabar yubora olmaydi. Guruhga yuborilsa, guruhning raqamli chat ID'si kerak; u manfiy bo'lishi mumkin va bot shu guruhga qo'shilgan bo'lishi kerak.

`bot/.env` dagi qiymatlar:

| Kalit | Qiymat |
| --- | --- |
| `BOT_TOKEN` | BotFather bergan token |
| `ADMIN_CHAT_ID` | Butun son; guruh ID'si manfiy bo'lishi mumkin |
| `WEBAPP_URL` | Mini App'ning `https://` bilan boshlanadigan Vercel manzili |
| `DB_PATH` | Ixtiyoriy SQLite yo'li; odatiy qiymat `data/leads.db`, `bot/` papkasiga nisbatan |

## Mini App'ni Vercel'da chiqarish

Vercel'da ushbu repozitoriyni yangi loyiha sifatida import qiling. Root Directory = `webapp`, Framework Preset = Other qilib belgilang; build/install buyruqlarini kiritmang. Sozlamalar `webapp/vercel.json` faylida. Deploy tugagach, berilgan `https://...vercel.app` manzilini `bot/.env` dagi `WEBAPP_URL` ga yozing. Botni yangi manzil bilan qayta ishga tushiring.

Botning uzoq so'rovli (`long polling`) jarayoni Vercel'da emas, doimiy ishlaydigan serverda turadi.

## Botni Linux serverda ishga tushirish

Serverda Python 3.11, `venv` va Git bo'lsin. Repozitoriyni `/opt/quantum-bot` manziliga joylang. Quyidagi buyruqlar server terminalida bajariladi; `<repo-url>` o'rniga o'z repozitoriy manzilingizni kiriting:

```bash
sudo useradd --system --home-dir /opt/quantum-bot --no-create-home --shell /usr/sbin/nologin quantum-bot
sudo git clone <repo-url> /opt/quantum-bot
cd /opt/quantum-bot
sudo python3.11 -m venv .venv
sudo .venv/bin/python -m pip install -r bot/requirements.txt
sudo install -d -o quantum-bot -g quantum-bot -m 750 bot/data
sudo install -o root -g quantum-bot -m 640 bot/.env.example bot/.env
sudoedit bot/.env
```

`bot/.env` ga haqiqiy `BOT_TOKEN`, `ADMIN_CHAT_ID` va `WEBAPP_URL` qiymatlarini kiriting. `DB_PATH` odatiy `data/leads.db` bo'lsa, baza `bot/data/` ichida yaratiladi. Agar `DB_PATH` ni o'zgartirsangiz, xizmatning yozish huquqi va `ReadWritePaths` ham shu joyga mos bo'lishi kerak.

```bash
sudo cp deploy/quantum-bot.service /etc/systemd/system/quantum-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now quantum-bot.service
sudo systemctl status quantum-bot.service
```

Bot `bot/.env` faylini o'zi o'qiydi. systemd unit ichida `EnvironmentFile` ishlatilmaydi. Xizmat `quantum-bot` nomli oddiy foydalanuvchi bilan yuradi va faqat `bot/data/` papkasiga yozadi. Xatoni ko'rish uchun `sudo journalctl -u quantum-bot.service -n 100` buyrug'idan foydalaning; loglarni ulashishdan oldin shaxsiy ma'lumot yo'qligini tekshiring.

## Havolalar va foydalanish

`<bot_username>` o'rniga BotFather'da tanlangan username'ni yozing:

| Havola | Joylashuvi |
| --- | --- |
| `https://t.me/<bot_username>?start=ig` | Instagram bio |
| `https://t.me/<bot_username>?start=tg` | Telegram kanal |
| `https://t.me/<bot_username>?start=yt` | YouTube video tavsifi |

Botga `/start` yuborilganda Mini App'ni uning javob klaviaturasidagi tugma orqali oching. `Telegram.WebApp.sendData` faqat shu reply-keyboard tugmasidan ochilganda botga ma'lumot qaytaradi. Forma yuborilgach, ariza bazaga yozilishi va administrator chatiga kelishi kerak.

`/export` ruxsat berilgan odamga arizalarni CSV ko'rinishida beradi. `/stats` oxirgi 7 va 30 kun statistikalarini chiqaradi. Ruxsat shartlari quyidagi bo'limda keltirilgan.

## Admin panel

Panel botga ulangach, `/admin` administrator chatida va ruxsat berilgan ko'ruvchilarning shaxsiy chatlarida ishlaydi. Buyruq shu chatlarning menyusida ko'rinadi.

Panelda jami foydalanuvchilar, bugun hamda oxirgi 7 va 30 kunda qo'shilganlar, oxirgi 7 kunda faol bo'lganlar, ariza qoldirgan foydalanuvchilar soni va ularning jami foydalanuvchilardagi ulushi (konversiya) ko'rsatiladi. Arizalar soni bugun hamda oxirgi 7 va 30 kun uchun beriladi. Yetkazilmagan arizalar soni ham ko'rsatiladi. Bugungi hisob va kunlik dinamika Toshkent vaqti (UTC+5) bo'yicha yuritiladi.

- **Фойдаланувчилар** — oxirgi 30 kunda qo'shilgan foydalanuvchilar soni manbalar bo'yicha
- **Аризалар** — arizalar statistikasi
- **14 кунлик динамика** — oxirgi 14 kunning har biri uchun yangi foydalanuvchilar va arizalar soni
- **Аризалар CSV** — arizalarni yuklab olish
- **Фойдаланувчилар CSV** — foydalanuvchilarni yuklab olish
- **Янгилаш** — panelni yangilash

Botda `/start` bosgan yoki Mini App orqali arizani muvaffaqiyatli yuborgan foydalanuvchi ro'yxatga qo'shiladi. Bot ishga tushganda `users` jadvali avtomatik yaratiladi va avvalgi arizalardan foydalanuvchilar tiklanadi. Avval ariza qoldirmaganlar panel ulangach, keyingi `/start` bosishida ro'yxatga qo'shiladi.

Yangilangan botni serverga chiqarishdan oldin `leads.db` bazasining zaxira nusxasini oling. Bot to'xtatilgan paytda baza joylashgan papkada quyidagi buyruqni bajaring. `YYYYMMDD` o'rniga nusxa olingan sanani yozing. `DB_PATH` da boshqa fayl nomi berilgan bo'lsa, buyruqni moslang.

```bash
cp leads.db leads.db.bak-YYYYMMDD
```

## Statistika ko'ruvchi va Admin Mini App

Sozlamalar namunasi `bot/.env.example` da. `bot/.env` ga kerakli qiymatlarni kiriting:

| Kalit | Qiymat |
| --- | --- |
| `STATS_VIEWER_IDS` | Ixtiyoriy, vergul bilan ajratilgan Telegram foydalanuvchi ID'lari, masalan `111111111,222222222` |
| `PANEL_URL` | Admin Mini App'ning `https://` manzili, masalan `https://2-31-25-204.sslip.io/admin/`; bo'sh bo'lsa panel HTTP serveri ishga tushmaydi |
| `PANEL_PORT` | Ixtiyoriy lokal port; odatiy qiymat `8090` |

O'z ID'ingizni `@userinfobot` orqali oling. `STATS_VIEWER_IDS` dagi odamlar va `ADMIN_CHAT_ID` musbat bo'lsa, shu ID egasi statistikaga kira oladi. Ko'ruvchi `/admin`, `/stats` va `/export` buyruqlaridan faqat bot bilan shaxsiy chatda foydalanadi; unga ariza xabarlari yuborilmaydi. CSV kelishi uchun ko'ruvchi avval botga `/start` yuborishi shart.

Shaxsiy chatda `/admin` ichidagi **Визуал статистика** tugmasi yoki chat menyusi tugmasi Admin Mini App'ni ochadi. CSV so'ralganda fayl bot bilan chatga hujjat sifatida keladi. Kirish Telegram `initData` imzosi bilan tekshiriladi; uning amal qilish muddati 24 soat. Muddati o'tsa, Mini App'ni qayta oching.

Serverni birinchi marta sozlash (Ubuntu/Debian): loyiha `/opt/quantum-bot` da, xizmat `quantum-bot` nomida deb olinadi. Avval botni to'xtatib, bazadan sana qo'shimchali zaxira nusxa oling; `DB_PATH` boshqacha bo'lsa, yo'lni moslang. So'ng [Caddy rasmiy APT yo'riqnomasi](https://caddyserver.com/docs/install) bo'yicha Caddy'ni o'rnating:

```bash
sudo systemctl stop quantum-bot.service
cd /opt/quantum-bot
sudo cp bot/data/leads.db "bot/data/leads.db.bak-$(date +%Y%m%d)"
sudo apt install --yes debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg
sudo chmod o+r /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

`bot/.env` dagi `PANEL_URL`, `PANEL_PORT` va ko'ruvchilar ID'larini sozlang. `/etc/caddy/Caddyfile` ichida boshqa saytlar bo'lsa, faqat `deploy/Caddyfile` dagi blokni qo'shing, mavjud faylni ustidan yozmang. Faqat ushbu sayt bo'lsa:

```bash
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
sudo systemctl reload caddy
sudo ufw allow 80,443/tcp
sudo systemctl restart quantum-bot.service
curl -I https://2-31-25-204.sslip.io/admin/
```

Oxirgi buyruqda `200` holati va `Content-Security-Policy` sarlavhasi kutiladi. Mini App ko'rinishini lokal tekshirish uchun `bot/admin_webapp/tests/preview.html?state=loading` faylini oching; `state` qiymati `loading`, `outside`, `expired`, `forbidden`, `error`, `empty` yoki `full` bo'lishi mumkin.

## Shaxsiy ma'lumotlar

Arizalarda ism, telefon va boshqa shaxsiy ma'lumotlar bor. Ularni himoyalang, kirishni cheklang va saqlash muddatini belgilang. O'zbekiston fuqarolarining shaxsiy ma'lumotlarini O'zbekiston hududidagi serverda saqlash talabi qo'llanishini tekshiring; server joylashuvi va huquqiy muvofiqlik haqidagi yakuniy qarorni loyiha egasi qabul qiladi.

Foydalanuvchilar CSV faylida ham shaxsiy ma'lumotlar bor. Panel ulangach, fayl faqat administrator chatida yuklab olinadi.
