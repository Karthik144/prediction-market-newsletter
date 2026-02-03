# Prediction Market Newsletter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a daily email newsletter that surfaces the top-moving prediction markets from Polymarket, sent automatically via GitHub Actions and Resend.

**Architecture:** A single Python script triggered by a GitHub Actions cron job at 7am ET. It fetches active markets from Polymarket's Gamma API, ranks them by 24-hour price change, renders an HTML email, and broadcasts it to subscribers via Resend's Broadcast API.

**Tech Stack:** Python 3.12, requests, resend (Python SDK), GitHub Actions, Resend (email delivery)

---

### Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `src/__init__.py`
- Create: `.gitignore`

**Step 1: Create requirements.txt**

```
requests==2.32.3
resend==2.5.0
python-dotenv==1.0.1
```

**Step 2: Create .env.example**

```
RESEND_API_KEY=re_xxxxxxxxxxxx
RESEND_AUDIENCE_ID=your-audience-id-here
FROM_EMAIL=Newsletter <newsletter@yourdomain.com>
```

**Step 3: Create .gitignore**

```
__pycache__/
*.pyc
.env
.venv/
venv/
```

**Step 4: Create src/__init__.py**

Empty file.

**Step 5: Install dependencies**

Run: `pip install -r requirements.txt`

**Step 6: Commit**

```bash
git add requirements.txt .env.example .gitignore src/__init__.py
git commit -m "feat: project setup with dependencies"
```

---

### Task 2: Polymarket API Client

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_polymarket.py`
- Create: `src/polymarket.py`

**Step 1: Write the failing test**

```python
# tests/test_polymarket.py
import json
from unittest.mock import patch, MagicMock
from src.polymarket import fetch_active_markets

SAMPLE_MARKETS_RESPONSE = [
    {
        "id": "123",
        "question": "Will X happen?",
        "slug": "will-x-happen",
        "description": "This market resolves to Yes if X happens by Dec 31.",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.65", "0.35"],
        "volume": "500000",
        "volume24hr": 50000.0,
        "liquidity": "100000",
        "clobTokenIds": ["token1", "token2"],
        "lastTradePrice": 0.65,
        "oneDayPriceChange": 0.15,
    },
    {
        "id": "456",
        "question": "Will Y happen?",
        "slug": "will-y-happen",
        "description": "This market resolves to Yes if Y happens.",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.30", "0.70"],
        "volume": "1000",
        "volume24hr": 50.0,
        "liquidity": "200",
        "clobTokenIds": ["token3", "token4"],
        "lastTradePrice": 0.30,
        "oneDayPriceChange": -0.25,
    },
]


@patch("src.polymarket.requests.get")
def test_fetch_active_markets_returns_parsed_markets(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_MARKETS_RESPONSE
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    markets = fetch_active_markets()

    assert len(markets) == 2
    assert markets[0]["question"] == "Will X happen?"
    assert markets[0]["oneDayPriceChange"] == 0.15
    mock_get.assert_called_once()


@patch("src.polymarket.requests.get")
def test_fetch_active_markets_calls_gamma_api(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    fetch_active_markets()

    call_args = mock_get.call_args
    assert "gamma-api.polymarket.com" in call_args[0][0]
    assert call_args[1]["params"]["active"] == "true"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_polymarket.py -v`
Expected: FAIL with `ModuleNotFoundError` or `ImportError`

**Step 3: Write minimal implementation**

```python
# src/polymarket.py
import requests

GAMMA_API_BASE = "https://gamma-api.polymarket.com"


def fetch_active_markets(limit: int = 100) -> list[dict]:
    """Fetch active markets from Polymarket's Gamma API, sorted by 24h volume."""
    url = f"{GAMMA_API_BASE}/markets"
    params = {
        "active": "true",
        "closed": "false",
        "limit": str(limit),
        "order": "volume24hr",
        "ascending": "false",
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_polymarket.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add src/polymarket.py tests/__init__.py tests/test_polymarket.py
git commit -m "feat: polymarket API client to fetch active markets"
```

---

### Task 3: Market Ranker

**Files:**
- Create: `tests/test_ranker.py`
- Create: `src/ranker.py`

**Step 1: Write the failing tests**

```python
# tests/test_ranker.py
from src.ranker import rank_top_movers

SAMPLE_MARKETS = [
    {
        "id": "1",
        "question": "Big mover",
        "slug": "big-mover",
        "description": "Desc 1",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.80", "0.20"],
        "volume24hr": 100000.0,
        "liquidity": "50000",
        "oneDayPriceChange": 0.30,
    },
    {
        "id": "2",
        "question": "Small mover",
        "slug": "small-mover",
        "description": "Desc 2",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.50", "0.50"],
        "volume24hr": 80000.0,
        "liquidity": "40000",
        "oneDayPriceChange": 0.02,
    },
    {
        "id": "3",
        "question": "Medium mover",
        "slug": "medium-mover",
        "description": "Desc 3",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.40", "0.60"],
        "volume24hr": 90000.0,
        "liquidity": "45000",
        "oneDayPriceChange": -0.15,
    },
    {
        "id": "4",
        "question": "Low volume mover",
        "slug": "low-volume",
        "description": "Desc 4",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.90", "0.10"],
        "volume24hr": 500.0,
        "liquidity": "100",
        "oneDayPriceChange": 0.50,
    },
]


def test_rank_top_movers_sorts_by_absolute_change():
    result = rank_top_movers(SAMPLE_MARKETS, top_n=10, min_volume_24h=0)
    assert result[0]["question"] == "Low volume mover"  # |0.50|
    assert result[1]["question"] == "Big mover"  # |0.30|
    assert result[2]["question"] == "Medium mover"  # |-0.15|


def test_rank_top_movers_filters_low_volume():
    result = rank_top_movers(SAMPLE_MARKETS, top_n=10, min_volume_24h=10000)
    questions = [m["question"] for m in result]
    assert "Low volume mover" not in questions
    assert len(result) == 3


def test_rank_top_movers_limits_results():
    result = rank_top_movers(SAMPLE_MARKETS, top_n=2, min_volume_24h=0)
    assert len(result) == 2


def test_rank_top_movers_skips_markets_without_price_change():
    markets = [
        {
            "id": "5",
            "question": "No change data",
            "slug": "no-change",
            "description": "Desc",
            "outcomes": ["Yes", "No"],
            "outcomePrices": ["0.50", "0.50"],
            "volume24hr": 50000.0,
            "liquidity": "10000",
        },
    ]
    result = rank_top_movers(markets, top_n=10, min_volume_24h=0)
    assert len(result) == 0
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ranker.py -v`
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

```python
# src/ranker.py


def rank_top_movers(
    markets: list[dict],
    top_n: int = 10,
    min_volume_24h: float = 10000,
) -> list[dict]:
    """Filter and rank markets by absolute 24h price change."""
    filtered = []
    for market in markets:
        price_change = market.get("oneDayPriceChange")
        if price_change is None:
            continue
        volume_24h = market.get("volume24hr", 0)
        if volume_24h < min_volume_24h:
            continue
        filtered.append(market)

    filtered.sort(key=lambda m: abs(m["oneDayPriceChange"]), reverse=True)
    return filtered[:top_n]
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_ranker.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add src/ranker.py tests/test_ranker.py
git commit -m "feat: market ranker filters and sorts by top movers"
```

---

### Task 4: HTML Email Template

**Files:**
- Create: `tests/test_email_template.py`
- Create: `src/email_template.py`

**Step 1: Write the failing tests**

```python
# tests/test_email_template.py
from src.email_template import render_newsletter

SAMPLE_MOVERS = [
    {
        "question": "Will X happen?",
        "slug": "will-x-happen",
        "description": "This market resolves to Yes if X happens by Dec 31, 2026.",
        "outcomePrices": ["0.80", "0.20"],
        "oneDayPriceChange": 0.15,
        "volume24hr": 120000.0,
    },
    {
        "question": "Will Y happen?",
        "slug": "will-y-happen",
        "description": "This market resolves to Yes if Y happens.",
        "outcomePrices": ["0.35", "0.65"],
        "oneDayPriceChange": -0.10,
        "volume24hr": 85000.0,
    },
]


def test_render_newsletter_contains_market_questions():
    html = render_newsletter(SAMPLE_MOVERS, date_str="Feb 3, 2026")
    assert "Will X happen?" in html
    assert "Will Y happen?" in html


def test_render_newsletter_contains_probabilities():
    html = render_newsletter(SAMPLE_MOVERS, date_str="Feb 3, 2026")
    assert "80%" in html


def test_render_newsletter_contains_price_change_arrows():
    html = render_newsletter(SAMPLE_MOVERS, date_str="Feb 3, 2026")
    # Positive change should have up arrow
    assert "&#9650;" in html or "▲" in html
    # Negative change should have down arrow
    assert "&#9660;" in html or "▼" in html


def test_render_newsletter_contains_polymarket_links():
    html = render_newsletter(SAMPLE_MOVERS, date_str="Feb 3, 2026")
    assert "https://polymarket.com/event/will-x-happen" in html
    assert "https://polymarket.com/event/will-y-happen" in html


def test_render_newsletter_contains_descriptions():
    html = render_newsletter(SAMPLE_MOVERS, date_str="Feb 3, 2026")
    assert "This market resolves to Yes if X happens" in html


def test_render_newsletter_contains_date():
    html = render_newsletter(SAMPLE_MOVERS, date_str="Feb 3, 2026")
    assert "Feb 3, 2026" in html


def test_render_newsletter_contains_unsubscribe_placeholder():
    html = render_newsletter(SAMPLE_MOVERS, date_str="Feb 3, 2026")
    assert "{{{RESEND_UNSUBSCRIBE_URL}}}" in html
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_email_template.py -v`
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

```python
# src/email_template.py


def _format_probability(outcome_prices: list[str]) -> str:
    """Format the Yes outcome price as a percentage."""
    price = float(outcome_prices[0])
    return f"{price * 100:.0f}%"


def _format_change(change: float) -> tuple[str, str, str]:
    """Return (arrow, formatted change, color) for a price change."""
    pct = abs(change) * 100
    if change >= 0:
        return "&#9650;", f"+{pct:.1f}%", "#16a34a"
    return "&#9660;", f"-{pct:.1f}%", "#dc2626"


def _format_volume(volume: float) -> str:
    """Format volume as human-readable string."""
    if volume >= 1_000_000:
        return f"${volume / 1_000_000:.1f}M"
    if volume >= 1_000:
        return f"${volume / 1_000:.0f}K"
    return f"${volume:.0f}"


def _truncate(text: str, max_length: int = 120) -> str:
    """Truncate text to max_length, adding ellipsis if needed."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rsplit(" ", 1)[0] + "..."


def _render_market_row(market: dict) -> str:
    """Render a single market as an HTML table row."""
    question = market["question"]
    slug = market["slug"]
    description = _truncate(market.get("description", ""))
    probability = _format_probability(market["outcomePrices"])
    arrow, change_str, color = _format_change(market["oneDayPriceChange"])
    volume = _format_volume(market.get("volume24hr", 0))
    link = f"https://polymarket.com/event/{slug}"

    return f"""
    <tr>
      <td style="padding: 16px 0; border-bottom: 1px solid #e5e7eb;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td style="font-family: Arial, sans-serif;">
              <div style="font-size: 16px; font-weight: bold; color: #111827; margin-bottom: 6px;">
                {question}
              </div>
              <div style="font-size: 13px; color: #6b7280; margin-bottom: 8px;">
                {description}
              </div>
              <table cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="font-size: 22px; font-weight: bold; color: #111827; padding-right: 16px;">
                    {probability}
                  </td>
                  <td style="font-size: 15px; font-weight: bold; color: {color}; padding-right: 16px;">
                    {arrow} {change_str}
                  </td>
                  <td style="font-size: 13px; color: #6b7280;">
                    Vol: {volume}
                  </td>
                </tr>
              </table>
              <div style="margin-top: 8px;">
                <a href="{link}" style="font-size: 13px; color: #2563eb; text-decoration: none;">
                  View on Polymarket &rarr;
                </a>
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>"""


def render_newsletter(markets: list[dict], date_str: str) -> str:
    """Render the full newsletter HTML email."""
    market_rows = "\n".join(_render_market_row(m) for m in markets)

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Top Movers - {date_str}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f3f4f6;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f3f4f6;">
    <tr>
      <td align="center" style="padding: 24px 16px;">
        <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden;">
          <!-- Header -->
          <tr>
            <td style="background-color: #1e1b4b; padding: 24px 32px;">
              <div style="font-family: Arial, sans-serif; font-size: 22px; font-weight: bold; color: #ffffff;">
                Top Movers
              </div>
              <div style="font-family: Arial, sans-serif; font-size: 14px; color: #c7d2fe; margin-top: 4px;">
                {date_str} &middot; Powered by Polymarket
              </div>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding: 8px 32px 24px 32px;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                {market_rows}
              </table>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding: 16px 32px 24px 32px; border-top: 1px solid #e5e7eb;">
              <div style="font-family: Arial, sans-serif; font-size: 12px; color: #9ca3af; text-align: center;">
                Data from <a href="https://polymarket.com" style="color: #6b7280;">Polymarket</a>.
                Prices reflect market-implied probabilities, not guarantees.
              </div>
              <div style="font-family: Arial, sans-serif; font-size: 12px; color: #9ca3af; text-align: center; margin-top: 8px;">
                <a href="{{{{RESEND_UNSUBSCRIBE_URL}}}}" style="color: #6b7280;">Unsubscribe</a>
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
```

**Important note on the unsubscribe placeholder:** The template uses `{{{RESEND_UNSUBSCRIBE_URL}}}` (triple braces) which is Resend's template syntax. Since we're using Python f-strings, we need to escape the braces. In the implementation, use quadruple braces `{{{{RESEND_UNSUBSCRIBE_URL}}}}` in the f-string so it renders as `{{{RESEND_UNSUBSCRIBE_URL}}}` in the output.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_email_template.py -v`
Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add src/email_template.py tests/test_email_template.py
git commit -m "feat: HTML email template for newsletter"
```

---

### Task 5: Resend Email Sender

**Files:**
- Create: `tests/test_sender.py`
- Create: `src/sender.py`

**Step 1: Write the failing tests**

```python
# tests/test_sender.py
from unittest.mock import patch, MagicMock
from src.sender import send_newsletter


@patch("src.sender.resend")
def test_send_newsletter_creates_and_sends_broadcast(mock_resend):
    mock_resend.Broadcasts.create.return_value = {"id": "broadcast-123"}

    send_newsletter(
        html="<h1>Test</h1>",
        subject="Top Movers - Feb 3, 2026",
        audience_id="audience-456",
        from_email="Newsletter <news@example.com>",
        api_key="re_test_key",
    )

    mock_resend.Broadcasts.create.assert_called_once_with({
        "audience_id": "audience-456",
        "from": "Newsletter <news@example.com>",
        "subject": "Top Movers - Feb 3, 2026",
        "html": "<h1>Test</h1>",
    })
    mock_resend.Broadcasts.send.assert_called_once_with("broadcast-123")


@patch("src.sender.resend")
def test_send_newsletter_sets_api_key(mock_resend):
    mock_resend.Broadcasts.create.return_value = {"id": "broadcast-123"}

    send_newsletter(
        html="<h1>Test</h1>",
        subject="Test",
        audience_id="aud-1",
        from_email="test@example.com",
        api_key="re_my_key",
    )

    assert mock_resend.api_key == "re_my_key"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sender.py -v`
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

```python
# src/sender.py
import resend


def send_newsletter(
    html: str,
    subject: str,
    audience_id: str,
    from_email: str,
    api_key: str,
) -> str:
    """Create and send a broadcast email to the audience via Resend."""
    resend.api_key = api_key

    broadcast = resend.Broadcasts.create({
        "audience_id": audience_id,
        "from": from_email,
        "subject": subject,
        "html": html,
    })

    broadcast_id = broadcast["id"]
    resend.Broadcasts.send(broadcast_id)
    return broadcast_id
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_sender.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add src/sender.py tests/test_sender.py
git commit -m "feat: resend email sender with broadcast API"
```

---

### Task 6: Main Orchestrator

**Files:**
- Create: `tests/test_main.py`
- Create: `src/main.py`

**Step 1: Write the failing tests**

```python
# tests/test_main.py
from unittest.mock import patch, MagicMock
from src.main import run


@patch("src.main.send_newsletter")
@patch("src.main.render_newsletter")
@patch("src.main.rank_top_movers")
@patch("src.main.fetch_active_markets")
def test_run_orchestrates_pipeline(mock_fetch, mock_rank, mock_render, mock_send):
    mock_fetch.return_value = [{"id": "1"}]
    mock_rank.return_value = [{"id": "1", "question": "Test?"}]
    mock_render.return_value = "<html>newsletter</html>"
    mock_send.return_value = "broadcast-123"

    run(
        resend_api_key="re_key",
        audience_id="aud-1",
        from_email="test@example.com",
    )

    mock_fetch.assert_called_once()
    mock_rank.assert_called_once_with(mock_fetch.return_value, top_n=10, min_volume_24h=10000)
    mock_render.assert_called_once()
    mock_send.assert_called_once()


@patch("src.main.send_newsletter")
@patch("src.main.render_newsletter")
@patch("src.main.rank_top_movers")
@patch("src.main.fetch_active_markets")
def test_run_skips_send_when_no_movers(mock_fetch, mock_rank, mock_render, mock_send):
    mock_fetch.return_value = [{"id": "1"}]
    mock_rank.return_value = []

    run(
        resend_api_key="re_key",
        audience_id="aud-1",
        from_email="test@example.com",
    )

    mock_render.assert_not_called()
    mock_send.assert_not_called()
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_main.py -v`
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

```python
# src/main.py
import os
from datetime import datetime, timezone

from src.polymarket import fetch_active_markets
from src.ranker import rank_top_movers
from src.email_template import render_newsletter
from src.sender import send_newsletter


def run(resend_api_key: str, audience_id: str, from_email: str) -> None:
    """Orchestrate the newsletter pipeline: fetch -> rank -> render -> send."""
    markets = fetch_active_markets()
    top_movers = rank_top_movers(markets, top_n=10, min_volume_24h=10000)

    if not top_movers:
        print("No top movers found. Skipping send.")
        return

    date_str = datetime.now(timezone.utc).strftime("%b %-d, %Y")
    subject = f"Top Movers \u2014 {date_str}"
    html = render_newsletter(top_movers, date_str=date_str)

    broadcast_id = send_newsletter(
        html=html,
        subject=subject,
        audience_id=audience_id,
        from_email=from_email,
        api_key=resend_api_key,
    )
    print(f"Newsletter sent. Broadcast ID: {broadcast_id}")


if __name__ == "__main__":
    run(
        resend_api_key=os.environ["RESEND_API_KEY"],
        audience_id=os.environ["RESEND_AUDIENCE_ID"],
        from_email=os.environ.get("FROM_EMAIL", "Newsletter <newsletter@yourdomain.com>"),
    )
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_main.py -v`
Expected: PASS (2 tests)

**Step 5: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS (15 tests total)

**Step 6: Commit**

```bash
git add src/main.py tests/test_main.py
git commit -m "feat: main orchestrator wiring up the pipeline"
```

---

### Task 7: GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/newsletter.yml`

**Step 1: Create the workflow file**

```yaml
name: Daily Newsletter

on:
  schedule:
    # 7:00 AM ET = 12:00 PM UTC (EST) or 11:00 AM UTC (EDT)
    - cron: '0 12 * * *'
  workflow_dispatch: # Allow manual trigger

jobs:
  send-newsletter:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: python -m pytest tests/ -v

      - name: Send newsletter
        env:
          RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
          RESEND_AUDIENCE_ID: ${{ secrets.RESEND_AUDIENCE_ID }}
          FROM_EMAIL: ${{ secrets.FROM_EMAIL }}
        run: python -m src.main
```

**Step 2: Verify YAML is valid**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/newsletter.yml'))"`

If `yaml` isn't installed, just visually verify the indentation is correct.

**Step 3: Commit**

```bash
git add .github/workflows/newsletter.yml
git commit -m "feat: github actions workflow for daily newsletter"
```

---

### Task 8: Final Integration Test & Cleanup

**Step 1: Run all tests one final time**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS

**Step 2: Verify the script runs (dry run, will fail on API call but validates imports)**

Run: `python -c "from src.main import run; print('All imports OK')"`
Expected: prints "All imports OK"

**Step 3: Final commit with any remaining cleanup**

```bash
git status
# If any unstaged changes, add and commit
```

---

## Post-Implementation Setup (Manual Steps)

These are done by the user in the browser, not automated:

1. **Create Resend account** at https://resend.com
2. **Add and verify a sending domain** in Resend dashboard
3. **Create an audience** in Resend dashboard, copy the audience ID
4. **Generate an API key** in Resend dashboard
5. **Add GitHub secrets** in repo settings:
   - `RESEND_API_KEY` = your Resend API key
   - `RESEND_AUDIENCE_ID` = your audience ID
   - `FROM_EMAIL` = `Newsletter <newsletter@yourdomain.com>`
6. **Test with manual trigger** — Go to Actions tab, select "Daily Newsletter", click "Run workflow"
