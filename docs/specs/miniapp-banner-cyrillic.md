# Mini App: Cyrillic hero banner + script-based swap

## Goal
Cyrillic users see a Cyrillic banner, Latin users see the existing Latin banner. "QUANTUM Psychology" stays in Latin, unchanged, on both.

## Context
- Current banner: `webapp/assets/hero-banner.webp` (1314x1197, Latin text only).
- Hero markup: `webapp/index.html:28-33`; CTA hotspot `.hero__cta` at left 22%, top 68%, w 56%, h 16% (`webapp/styles.css:120-130`).
- Script switch: `renderCopy()` in `webapp/app.js:57-78`, `DEFAULT_SCRIPT = "cyr"`.
- Tests: `node --test "webapp/tests/*.test.mjs"`.

## Scope
- Do: generate `webapp/assets/hero-banner-cyr.webp` (edit of existing banner, same layout); swap `<img src>` by script.
- Don't: regenerate Latin banner, move CTA hotspot, touch form/bot/deploy, push.

## Cyrillic texts (from webapp/i18n.js)
- Badge: «12 ОЙЛИК ДАСТУР»
- Title: «QUANTUM Psychology» (Latin, unchanged)
- Subtitle: «12 ойлик шахсий ва руҳий ривожланиш дастури»
- Features: «Фикр кучини бошқариш» · «Ички мувозанат ва хотиржамлик» · «Ҳаёт сифатини юксалтириш»
- Tagline: «Ички имкониятингизни очинг — янги даражага чиқинг»
- Tag: «БЕПУЛ» + «дастлабки суҳбат»
- Button: «БЕПУЛ СУҲБАТГА ЁЗИЛИШ»

## Acceptance
- [ ] Cyrillic image: every letter correct (қ, ҳ, ў, ғ, ё), title Latin; 1314x1197 WebP ≤400 KB — ffprobe + mentor visual check.
- [ ] Button in Cyrillic image in same place as Latin one (CTA hotspot fits) — 390x844 screenshot.
- [ ] Script toggle swaps image src; default (cyr) HTML src is Cyrillic image (no flash) — node test.
- [ ] `node --test "webapp/tests/*.test.mjs"` all pass.

## Waves
1. RASM — `webapp/assets/hero-banner-cyr.webp`.
2. BAJARISH — `webapp/index.html`, `webapp/app.js`, `webapp/tests/data.test.mjs`.

## Risks
- AI garbles Uzbek Cyrillic letters → up to 3 attempts, mentor checks each letter.
- ffmpeg blocked in Codex sandbox before → user may need to convert PNG→WebP.
