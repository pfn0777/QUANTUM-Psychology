# Spec: Mini App brand redesign + gold HTML hero

Date: 2026-11-28 · Executor: Codex · Plan: approved by user

## Goal
Move the Telegram Mini App (`webapp/`) from the old dark purple theme to the new brand book (light ivory + gold + chocolate). Rebuild the hero as HTML text over a Codex-generated text-free background image: gold "QUANTUM Psychology", subtitle, 3 benefits, tagline, БЕПУЛ tag and a chocolate CTA that scrolls to `#leadForm`.

## Out of scope
Multi-screen app (bottom nav, courses, gift); copy changes (except 3 hero benefit lines); lead submission logic (`tg.sendData`); bot; deploy; push.

## Do not touch
`webapp/validate.js`, `webapp/telegram.js`, `webapp/data.js`, `webapp/fonts.css`, `webapp/fonts/`, `bot/`, `brand/`.

## Brand tokens (source: brand book)
| Token | Value | Use |
|---|---|---|
| ivory | `#FBF6EC` | main background |
| marble | `#F2E8D8` | second background, soft cards |
| gold | `#C9A050` | decor, icons, borders, pill borders (never body text) |
| chocolate | `#3B2112` | primary button, headings, dark block |
| bronze | `#8C6420` | gold-coloured text/links on light backgrounds, section labels |
| gold-light | `#F1D79A` | text on chocolate |
| champagne | `#E9D6B0` | borders, input border, dividers |
| cocoa | `#5A3620` | gradient top of chocolate |
| text-soft | `#6B5340` | secondary text |
| text | `#2B1A0E` | body text |
| dark | `#2A170B` | gradient bottom of chocolate |
| border-gold | `#D9B66E` | secondary button border |
| error | dark warm red with ≥4.5:1 on ivory (e.g. `#A3322A`) |

Ratio per screen: 60% ivory/marble, 20% champagne, 12% chocolate, 8% gold.

Gradients:
- Gold light ("Oltin nur", gold button / БЕПУЛ tag / premium marks): `linear-gradient(180deg,#FBE9B4 0%,#E0B65E 50%,#A9792B 100%)` — tag variant `#F1D79A→#C9A050` with text `#2B1A0E`.
- Keyword text on light bg: `linear-gradient(180deg,#D9AE55 0%,#A9792B 55%,#7A5518 100%)` + `background-clip:text`. If the lightest stop fails 3:1 on ivory at display size, darken the top stop (e.g. `#B98A3A`) — contrast wins.
- Chocolate pill: `linear-gradient(180deg,#5A3620 0%,#3B2112 60%,#2A170B 100%)` + `2px solid #C9A050`.
- Cream pill: `linear-gradient(180deg,#FFFDF7,#F4EAD7)` + `1.5px solid #D9B66E`, shadow `0 6px 16px rgba(140,100,32,.15)`.
- Page background: `radial-gradient(circle at 12% 6%, rgba(255,236,190,.9) 0%, rgba(255,236,190,0) 22%), linear-gradient(180deg,#FBF6EC 0%,#F4EAD9 100%)`.

Typography:
- Headings: Cormorant Garamond 600/700/italic. Display 700 caps. Section h2 700, colour chocolate (keyword words may use gold gradient).
- UI/body: Montserrat 400–700. Body 400 16/26. Buttons/tags 700, 13–15px, CAPS, letter-spacing .08em (tags .1–.12em).
- Section labels: 12px 700, letter-spacing .14em, `#8C6420`.

Components:
- Primary button: height ≥54, radius 999, chocolate gradient, 2px `#C9A050` border, shadow `0 8px 20px rgba(59,33,18,.25)`, text `#F1D79A` 700 15px ls .08em CAPS. Only one primary per screen. Disabled: visibly muted, still readable.
- Secondary button: cream pill. Tertiary: transparent, `#8C6420`, height 48.
- Tags: БЕПУЛ gold gradient; ЖОНЛИ `#3B2112` bg + `#F1D79A`; outline 1.5px `#C9A050`; СОВҒА `#F2E8D8` + `#8C6420`.
- Input/select: height 50, radius 999 (textarea radius 22), 1.5px `#E9D6B0`, bg `#FBF6EC`, text `#2B1A0E`, placeholder `#6B5340`-ish but clearly lighter than typed text while ≥4.5:1 is NOT required for placeholder (keep ≥3:1). Focus border `#C9A050` + soft gold ring.
- Cards: white, 1px `#E9D6B0`, radius 26 (card) / 22 (block), shadow `0 10px 28px rgba(140,100,32,.14)`. Quote/feature block may be chocolate gradient with 1.5px gold border and `#F1D79A`/ivory text.
- Icons: line, stroke 1.6, `#8C6420`, inside 50–52px circle with 1.5px `#C9A050` border and white/ivory fill.
- Divider: gold line fade → 7px rotated diamond → small atom → diamond → line fade.
- Spacing base 4 (4·8·12·16·24·32·48).

Logo mark (`webapp/assets/logo-mark.svg`): viewBox `0 0 100 100`; three ellipses rx44 ry15 rotated 0/60/120 around (50,50); circle r12 (stroke); filled dot r≈6; stroke `#C9A050`, no other colours. App icon (`webapp/assets/app-icon.svg`): rounded square, gradient `#5A3620→#2A170B`, 2px gold border, mark in `#E0B65E`.

Rules: no emoji; no cold blue/neon/purple; no light-gold text on white/ivory; ≤3 pills per screen; always light theme (`color-scheme: light`, `theme-color #FBF6EC`), also in Telegram dark mode.

## Hero (wave 2)
Order inside `<section class="hero">`:
1. Background `<img class="hero__bg" src="assets/hero-bg.webp" alt="" ...>` (decorative), `object-fit: cover`, plus a soft ivory scrim/radial behind the text column. Fallback: brand page gradient if image fails.
2. Brand atom (inline SVG or `logo-mark.svg`), gold.
3. Cream eyebrow pill — `heroEyebrow`.
4. `<h1 id="heroTitle">`: `<span class="hero__title-main">QUANTUM</span><span class="hero__title-sub">Psychology</span>` — main: Cormorant 700, large `clamp()`, gold keyword gradient (≥3:1 vs ivory at every stop); sub: Cormorant 600 italic, bronze. Text comes from i18n (`heroTitle` stays for `document.title`).
5. Divider.
6. Subtitle — `heroSubtitle`, Montserrat 600, chocolate.
7. Benefits list — 3 items with gold line icons (brain, lotus, growth/arrow-up) + `heroBenefit1..3`.
8. Tagline — `heroTagline`, Cormorant italic, chocolate/soft.
9. БЕПУЛ tag (`heroTag`) + `heroTagText`.
10. CTA `<a class="button button--primary hero__cta" href="#leadForm" data-i18n="heroCta">` + decorative chevron, ≥54px.

Pills in hero: exactly 3 (eyebrow, tag, CTA). One soft enter animation; disabled under `prefers-reduced-motion`.

New i18n keys:
- cyr: `heroBenefit1` "Фикр кучини бошқариш", `heroBenefit2` "Ички мувозанат ва хотиржамлик", `heroBenefit3` "Ҳаёт сифатини юксалтириш".
- lat: `heroBenefit1` "Fikr kuchini boshqarish", `heroBenefit2` "Ichki muvozanat va xotirjamlik", `heroBenefit3` "Hayot sifatini yuksaltirish".
Removed: `heroImageSrc`, `heroImageAlt`. Deleted files: `webapp/assets/hero-banner.webp`, `webapp/assets/hero-banner-cyr.webp`.

## Acceptance
- No purple residue: `Select-String -Path webapp/styles.css,webapp/index.html -Pattern '#160536|#7b2cf0|#9b5cff|#24074f|violet|lavender'` → empty.
- `node --test "webapp/tests/*.test.mjs"` all pass.
- Hero `h1` contains HTML text "QUANTUM" and "Psychology"; CTA is `<a href="#leadForm">`, height ≥48px.
- 390×844: CTA fully visible in first viewport in both scripts. 360×740: no horizontal scroll.
- Background image: WebP, ≤300 KB, no text/letters/logo/people.
- Contrast: body text ≥4.5:1, large display ≥3:1.
- Script toggle switches all hero copy including benefits.
- Telegram: `setHeaderColor("#FBF6EC")` and `setBackgroundColor("#FBF6EC")` only when `tg.isVersionAtLeast?.("6.1")`, inside existing try/catch with `console.warn`.
