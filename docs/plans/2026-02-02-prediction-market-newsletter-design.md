# Prediction Market Newsletter — Design

## Overview

A daily email newsletter that surfaces the top-moving prediction markets from Polymarket. Runs as an automated Python script on GitHub Actions, sends via Resend.

## Architecture

```
GitHub Actions (cron, 7am ET)
  -> Python script
    -> Polymarket API (fetch markets)
    -> Filter & rank top movers
    -> Render HTML email
    -> Resend API (send to subscriber list)
```

No database. No backend. No web framework. Subscribers managed entirely through Resend's audience/contacts feature.

## Data Pipeline

1. **Fetch active markets** from Polymarket's CLOB API — markets with current token prices (price = probability)
2. **Compare prices** — Current price vs. price 24 hours ago to find biggest swings
3. **Filter noise** — Ignore low-volume/low-liquidity markets where small trades cause wild swings
4. **Rank by absolute change** — Sort by largest absolute probability movement (e.g., 30% -> 55% = 25 point swing)
5. **Select top 5-10** movers for the newsletter

If Polymarket's API doesn't provide historical prices directly, store yesterday's snapshot as a JSON artifact in GitHub Actions or committed to the repo.

## Email Content

**Subject line:** "Top Movers — {date}"

Each market entry includes:
- Market question
- Current probability (bold)
- 24h change with direction arrow
- Trading volume
- Brief market description (truncated to 1-2 lines)
- Direct link to the market on Polymarket

**Layout:** Clean, simple HTML email using tables and inline styles for email client compatibility. Resend handles unsubscribe links, bounce management, and CAN-SPAM compliance.

## Subscriber Acquisition

MVP: Resend's hosted signup form, or a simple static landing page (GitHub Pages) with an email input that calls Resend's API to add contacts to an audience.

## Project Structure

```
prediction-market-newsletter/
├── src/
│   ├── main.py              # Entry point — orchestrates fetch -> rank -> send
│   ├── polymarket.py         # Polymarket API client
│   ├── ranker.py             # Filtering & ranking logic
│   ├── email_template.py     # HTML email rendering
│   └── sender.py             # Resend API integration
├── .github/
│   └── workflows/
│       └── newsletter.yml    # Cron workflow (daily at 7am ET)
├── requirements.txt          # requests, resend
├── .env.example              # Template for API keys
└── README.md
```

## Dependencies

- `requests` — HTTP client for Polymarket API
- `resend` — Resend Python SDK for email delivery

## Environment Variables

- `RESEND_API_KEY` — Resend API key (stored as GitHub Actions secret)
- `RESEND_AUDIENCE_ID` — Resend audience ID for subscriber list

## Tech Decisions

- **Python over TypeScript** — Simpler for a data pipeline script, fewer build steps, both Polymarket and Resend have good Python support
- **GitHub Actions over VPS** — Zero cost, no infrastructure, already have the repo on GitHub
- **Resend over SendGrid** — SendGrid killed its free plan in 2025. Resend free tier: 3,000 emails/month (100/day), 1,000 contacts
- **No database** — Resend manages subscribers. Market data is fetched fresh each run.
