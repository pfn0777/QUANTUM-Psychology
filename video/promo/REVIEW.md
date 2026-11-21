# Frame review

## Result

| Scene / requested frame | Result |
| --- | --- |
| Hook, 1.5 s | Accepted (attempt 2). |
| Hook v2, 0–2.7 s | Snapshots at 0, 0.4, 0.8, 1.6, 2.3, 2.6 and 2.7 s reviewed: frame 0 has background and line 1 only; gold line 2 appears at 0.8 s, line 3 at 1.6 s, faint echoes at 2.3 s and a full-frame soft gold flash at 2.6–2.7 s. Accepted. |
| Hook v2, 3.0 s | Snapshot reviewed; promise scene unchanged from v1. |
| Unchanged scenes, 5 / 15 / 26 / 29.75 s | Snapshots match v1 scenes. |
| Promise, 4.5 s | Accepted (attempt 2). |
| Bot, 9 s and 11.9 s | Accepted (attempt 2). Exact caption copied from `bot/texts.py`. |
| Mini app, 15 s and 17 s | Accepted (attempt 2). |
| Form, 20 s and 23 s | New top-form source frame inspected: name, age, phone and region are present. Bottom-form source inspected: submit button present. Accepted (attempt 2). |
| CTA, 26 s and 29.5 s | Accepted (attempt 2). |

## Checks and follow-up

- Retry fixes: moved the gold check into the success screenshot's empty band; kept one lower Cormorant scene caption in bot, mini app and form; kept the form screenshot covering the phone throughout its scroll; showed the whole square welcome image with `contain`; reduced promise text sizes for two-line wrapping.
- Composition accepted on attempt 2.
- `hyperframes check`: 0 errors / 13 warnings. Final MP4 rendered.
- Sound was not heard. Source audio is the existing 30 s segment; no mix change was made.
- Weakest risk: Telegram caption may be hard to read on a phone. If the snapshot shows clipping, scroll the text within the bubble while preserving the full exact caption.

## Hook v2 verification

- `npm run check` (HyperFrames 0.9.72, final `hook.html`): 0 errors, 11 warnings, all pre-existing outside hook (promise 1; bot 4 safe-zone + 1 line_unread; miniapp 1; form 1; CTA 3). Hook: 0 warnings; `container_overflow` info for `#hook-background` is intentional push-in scale.
- Rendered `video/out/quantum-promo-30s-v2.mp4` via `npx --yes hyperframes@0.9.72 render -o ../out/quantum-promo-30s-v2.mp4`: 1080×1920, 30 fps, H.264 + AAC, 30.0 s. Integrated -14.9 LUFS; true peak -1.5 dBTP; first 0.3 s RMS -14.2 dB.
- Cormorant Garamond italic uses weight 600 because the local Cyrillic italic font files cover weights 500–600.
