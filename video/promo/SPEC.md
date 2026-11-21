# QUANTUM Psychology — 30 s vertical promo

## Format and timing

- Canvas: 1080 × 1920, 30 fps, 900 frames.
- Music: 86 BPM, beat = 60/86 = 0.697674 s. Boundaries are rounded beat times.
- Audio: `assets/audio/music-30s-v2.m4a`, 0–30 s, with hook impact and whoosh; no voiceover or subtitles.
- Action-safe: x 54–1026, y 96–1824. Title-safe: x 108–972, y 192–1728.
- Phone: x 110–970, y 315–1595.

| Scene | Beats | Seconds | Proof or action |
| --- | ---: | ---: | --- |
| Hook | 0–4 | 0–2.791 | Full-frame purple image and «Нега ҳаётингизда» at frame 0; gold «бир хил муаммо» punches in at 0.698 s; «такрорланади?» rises at 1.395 s; faint echoes at 2.093 s; warm gold flash cuts to promise at 2.791 s. |
| Promise | 4–10 | 2.791–6.977 | Two lines appear word by word at 0.6977 s spacing. |
| Bot | 10–18 | 6.977–12.558 | Telegram mockup with actual welcome image and exact bot caption; reply key pulses and is tapped near 11.8 s. |
| Mini app | 18–26 | 12.558–18.140 | Real hero screenshot rises, real long module screenshot scrolls past multiple cards. |
| Form | 26–34 | 18.140–23.721 | Real filled top form scrolls to bottom and submit; real success state follows. |
| CTA | 34–43 | 23.721–30.000 | Brand mark, free consultation claim, bot handle, gold booking button; still after 28 s. |

## Color and type

- Background: #160536; surface gradient center: #24095a; purple glow: #7b2cf0 and #9b5cff.
- Gold gradient: #f5b52e → #ffe39a → #ffcf5a.
- Text: #ffffff, secondary #e4d8ff.
- Headings: local Cormorant Garamond 500–700 including italic; UI: local Montserrat 400–800. Cyrillic, Cyrillic-ext and Latin subsets use the same unicode ranges as `webapp/fonts.css`.
- Hook grain uses fixed SVG noise seed 47291; animation has no random source.

## Deliberate choices

- The bot chat is a labelled mockup because the repository supplies the real text and image but no Telegram screenshot.
- The application and form use genuine mini app captures. The form uses sample values: Мадина Каримова, 29, +998 90 123 45 67.
- Host boundaries land on beats. Each scene animates its own entrance and exit over roughly 0.25–0.75 s.
