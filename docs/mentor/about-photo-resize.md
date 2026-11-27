# Resize about/02.jpg to the 1280px media limit
Holat: TUGADI
Ijrochi: codex
Turi: ISH · Hajm: KICHIK
Spec: yo'q
Boshlangan: 2026-11-27

## Karta
Maqsad: `python scripts/prepare_bot_media.py --check` to'liq o'tsin — about/02.jpg (1086x1448, 5adf46d) MAX_IMAGE_SIDE=1280 dan katta.
Qilinadi: 02.jpg → 960x1280, LANCZOS, JPEG q85, RGB, EXIF yo'q.
Qilinmaydi: boshqa rasm, kod, manifest o'zgarmaydi.
Qabul mezonlari: --check to'liq o'tadi; pytest o'tadi; poster matni o'qiladi.

## To'lqinlar
### To'lqin 1 — TUGADI
- [x] 1. about/02.jpg ni kichraytirish (960x1280, 196 KB; --check exit 0; pytest 442/442)

## Qarorlar
- Manba = hozirgi 02.jpg (asl poster bilan SHA256 teng, about-photo-swap.md).
