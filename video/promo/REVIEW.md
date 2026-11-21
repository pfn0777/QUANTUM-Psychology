# Frame review

## Result

| Scene / requested frame | Result |
| --- | --- |
| Hook, 1.5 s | Accepted (attempt 2). |
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
