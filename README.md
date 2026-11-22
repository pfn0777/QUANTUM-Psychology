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

`/export` administratorga arizalarni CSV ko'rinishida beradi. `/stats` oxirgi 7 va 30 kun statistikalarini chiqaradi. Bu buyruqlar faqat `ADMIN_CHAT_ID` bilan mos chatda ishlaydi.

## Admin panel

Panel botga ulangach, `/admin` faqat `ADMIN_CHAT_ID` bilan mos chatda ishlaydi va shu chatning buyruqlar menyusida ko'rinadi.

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

## Shaxsiy ma'lumotlar

Arizalarda ism, telefon va boshqa shaxsiy ma'lumotlar bor. Ularni himoyalang, kirishni cheklang va saqlash muddatini belgilang. O'zbekiston fuqarolarining shaxsiy ma'lumotlarini O'zbekiston hududidagi serverda saqlash talabi qo'llanishini tekshiring; server joylashuvi va huquqiy muvofiqlik haqidagi yakuniy qarorni loyiha egasi qabul qiladi.

Foydalanuvchilar CSV faylida ham shaxsiy ma'lumotlar bor. Panel ulangach, fayl faqat administrator chatida yuklab olinadi.
