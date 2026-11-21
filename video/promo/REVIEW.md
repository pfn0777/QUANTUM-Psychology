# Frame review

## Result

| Scene / requested frame | Result |
| --- | --- |
| Hook, 1.5 s | Pending visual snapshot: browser/GPU startup failed in sandbox. |
| Promise, 4.5 s | Pending visual snapshot: browser/GPU startup failed in sandbox. |
| Bot, 9 s and 11.9 s | Pending visual snapshot: browser/GPU startup failed in sandbox. Exact caption copied from `bot/texts.py`. |
| Mini app, 15 s and 17 s | Pending visual snapshot: browser/GPU startup failed in sandbox. |
| Form, 20 s and 23 s | New top-form source frame inspected: name, age, phone and region are present. Bottom-form source inspected: submit button present. Pending composed snapshots. |
| CTA, 26 s and 29.5 s | Pending visual snapshot: browser/GPU startup failed in sandbox. |

## Checks and follow-up

- Retry fixes: moved the gold check into the success screenshot's empty band; kept one lower Cormorant scene caption in bot, mini app and form; kept the form screenshot covering the phone throughout its scroll; showed the whole square welcome image with `contain`; reduced promise text sizes for two-line wrapping.
- Retry lint: `npx hyperframes lint --json` could not start because PowerShell blocks `npx.ps1`; `npx.cmd` reached npm, but the restricted network returned `EACCES` while fetching HyperFrames. Offline mode returned `ENOTCACHED`. No new lint result is available.
- Lead visual review still needed at 22.8 and 23.3 s for the check placement, plus the form scroll, bot image and caption, and promise wrapping. No retry snapshot, check or render was run here.
- `hyperframes check --json` static lint: 0 errors, 0 warnings across 7 HTML files.
- Runtime check: Chrome GPU process crashed during startup; full layout, contrast and craft checks did not run. Audio check could not find ffprobe through the CLI even though the CapCut binary exists.
- No composed frame was visually inspected. Do not describe the finished video as approved until the lead runs the required snapshots and views each frame.
- Sound was not heard. Source audio is the existing 30 s segment; no mix change was made.
- Weakest risk: Telegram caption may be hard to read on a phone. If the snapshot shows clipping, scroll the text within the bubble while preserving the full exact caption.
- Run the full check, requested ten snapshots, review contact sheets and render in a browser-capable environment. Inspect the rendered MP4 with ffprobe.
