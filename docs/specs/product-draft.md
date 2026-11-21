# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary users are subscribers of the QUANTUM Psychology Telegram channel. They are Uzbek adults, and reshared posts suggest most are women. They care about their inner state, consciousness and energy, family and relationships, and money. They open the Mini App from the bot, usually after watching channel content (56.9% of channel posts are video), and their job is to understand the 12-module program and request a free initial consultation.

Segment shares (gender, age, region, income) are unknown. Do not state them as facts.

## Product Purpose

QUANTUM Psychology is a Telegram bot plus a Mini App:
- The visitor browses the 12-month, 12-module program and submits a request for a free initial consultation.
- The request is saved to SQLite and sent to the admin chat, and the admin calls the client back.

Success means a qualified lead with a phone number, topics of interest, a preferred call time, and a lead source. The admin can see sources and demographics through `/stats`.

## Positioning

The system grew out of the founder's own life. The founder lived with a disability for eighteen years, now walks freely, and built QUANTUM Psychology from years of study, research and personal experience. The program is a structured 12-month path of 12 modules aimed at self-understanding and working through inner blocks. A neighbouring course cannot truthfully claim this founder story.

## Operating Context

The flow:
1. The user opens the Mini App from the bot's keyboard button inside Telegram, mostly on a phone.
2. They submit the lead form through `Telegram.WebApp.sendData`.

Constraints and supporting pieces:
- `sendData` works only for keyboard-button launches. In other contexts the page asks the visitor to open it from the bot.
- Deep links carry the lead source in `?src=`.
- Static site on Vercel (`webapp/`). aiogram bot with long polling (`bot/`).
- Source material for copy and analysis, all read-only:
  - `Kurs modullari.txt`
  - `telegram post.txt`
  - `telegram-audience-report.md`
  - `instagram-audience-report.md`

## Capabilities and Constraints

- Uzbek only. Cyrillic is the default, with a Latin toggle stored per device. Russian is out of scope.
- Lead form fields:
  - name, age, phone (+998 mask), region
  - topics: these highlight the related modules
  - prior experience, call time, source
  - comment
  - consent checkbox (required)
- Out of scope:
  - payments and prices
  - user cabinet and web admin
  - AI-generated imagery presented as real

## Brand Commitments

- Name: QUANTUM Psychology.
- Brand book: `brand/QUANTUM Psychology — Brend kitobi.html` (read-only).
- The hero banner `webapp/assets/hero-banner.webp` is the user's own asset, chosen to replace the HTML hero. Its text is in Latin script only.
- Voice: warm, first-person founder voice ("Mening yo'lim"), calm and hopeful. No clinical or hype tone.

## Evidence on Hand

- The founder's personal story, already in `webapp/i18n.js` (`founderP1`–`founderP3`).
- The 12-module course description in `Kurs modullari.txt`.
- The following are absent:
  - testimonials and participant results
  - numbers and media mentions
  - prices

  Never fabricate them. Positive reshared messages in the channel are not consented testimonials.

## Product Principles

1. The founder's real story is the proof. Never add claims, results or social proof that do not exist.
2. One action matters: requesting the free consultation. Everything else supports understanding the program.
3. Respect personal data. Collect only what the admin uses, always with explicit consent.
4. Cyrillic and Latin readers get equal quality of copy.
5. Promise self-understanding and support, not guaranteed outcomes.

## Accessibility & Inclusion

The founder's story is about disability. Keep the experience usable for people with motor or vision limitations:
- large tap targets (at least 44px)
- high text contrast (at least 4.5:1)
- visible focus states
- respect for reduced motion
