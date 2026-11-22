# Promo hook v2 (kirill, viral boshlanish)
Holat: TUGADI
Ijrochi: codex
Turi: ISH · Hajm: KATTA
Spec: docs/specs/promo-hook-v2.md
Boshlangan: 2026-11-21

## Karta
Maqsad: 0–2.791 s hook'ni og'riq-savol + AI fon + impact SFX bilan qayta qurish; v2 MP4.
Qilinmaydi: 2.791 s dan keyingi sahnalar, lotin versiya, bot/webapp, push/deploy, v1 MP4 o'chirish.
Qabul mezonlari: check 0 error; 0-kadr qora emas + matn; v2 MP4 1080x1920 30fps 30.0s H.264+AAC; audio boshida impact, ≈ −14 LUFS.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. RASM: hook-bg-a.png tanlandi (commit 6ef2dd0); hook-bg-b.png ishlatilmaydi, commit qilinmagan
- [x] 2. Audio v2 (commit e1207bb, 2-urinishda; music −14.9 LUFS, TP −2.6, boshi RMS −21.7 dB; impact −3 dB, whoosh −6 dB)
### To'lqin 2 — TUGADI
- [x] 3. hook.html + index.html + SPEC/REVIEW (commit 95a8b91, 3-urinishda; check 0 error / 11 warning — hammasi eski sahnalarda; MP4 h264 1080x1920 30fps 30.000s, −14.9 LUFS, TP −1.5 dBTP, boshi RMS −14.2 dB)

## Qarorlar
- Hook: og'riq-savol «Нега ҳаётингизда бир хил муаммо такрорланади?» (foydalanuvchi tanlovi = tavsiya).
- AI fon yuzsiz siluet; SFX + fade-in'siz musiqa; yangi fayl v2.

## Kichik topilmalar (keyinroq)
- Promise sahnasi (v1 dan): 3.0 s da «янги даражага чиқинг» oltin qatori «имкониятингизни» dan oldin ko'rinadi (.gold background-clip:text span opacity'ni hisobga olmaydi).
- 2.3 s dagi echo nusxalari juda xira.
- docs/mentor/promo-video-30s*.md va specs fayllari commit qilinmagan (foydalanuvchiniki, tegilmaydi).

## Foydalanuvchi vazifalari
- [ ] v2 ni telefonda ovozli/ovozsiz ko'rish
- [ ] Instagram'da v1/v2 A/B, 3 s retention
