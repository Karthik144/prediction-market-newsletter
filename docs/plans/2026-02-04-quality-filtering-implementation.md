# Quality Filtering Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace simple price-change ranking with multi-stage quality filtering that surfaces important world events across categories.

**Architecture:** Fetch events by category using Polymarket's tag_id parameter → apply blocklist → filter by volume threshold → send candidates to Groq LLM for judgment + summary → select top markets per category based on weights.

**Tech Stack:** Python, Groq SDK (Llama 3.1 8B), Polymarket Events API, existing Resend integration

---

### Task 1: Add Groq Dependency

**Files:**
- Modify: `requirements.txt`
- Modify: `.env.example`

**Step 1: Add groq to requirements.txt**

Edit `requirements.txt` to add:
```
groq==0.15.0
```

**Step 2: Add GROQ_API_KEY to .env.example**

Edit `.env.example` to add:
```
GROQ_API_KEY=gsk_xxxxxxxxxxxx
```

**Step 3: Commit**

```bash
git add requirements.txt .env.example
git commit -m "chore: add groq dependency for LLM filtering"
```

---

### Task 2: Update Polymarket Module to Fetch by Category

**Files:**
- Modify: `src/polymarket.py`
- Modify: `tests/test_polymarket.py`

**Step 1: Write the failing test**

Add to `tests/test_polymarket.py`:
```python
from unittest.mock import patch, Mock

from src.polymarket import fetch_events_by_category, CATEGORY_TAGS


def test_fetch_events_by_category_uses_tag_id():
    mock_response = Mock()
    mock_response.json.return_value = [
        {"id": "1", "title": "Test Event", "markets": [{"question": "Test?"}]}
    ]
    mock_response.raise_for_status = Mock()

    with patch("src.polymarket.requests.get", return_value=mock_response) as mock_get:
        result = fetch_events_by_category("politics", limit=10)

        # Verify tag_id was passed
        call_args = mock_get.call_args
        assert call_args[1]["params"]["tag_id"] == CATEGORY_TAGS["politics"]
        assert call_args[1]["params"]["limit"] == "10"


def test_fetch_events_by_category_returns_markets():
    mock_response = Mock()
    mock_response.json.return_value = [
        {
            "id": "1",
            "title": "Fed Decision",
            "volume24hr": 500000,
            "markets": [
                {"question": "Will Fed cut rates?", "outcomePrices": '["0.7", "0.3"]'}
            ]
        }
    ]
    mock_response.raise_for_status = Mock()

    with patch("src.polymarket.requests.get", return_value=mock_response):
        result = fetch_events_by_category("economy", limit=10)

        assert len(result) == 1
        assert result[0]["question"] == "Will Fed cut rates?"
        assert result[0]["category"] == "economy"
        assert result[0]["event_title"] == "Fed Decision"


def test_category_tags_exist():
    assert CATEGORY_TAGS["politics"] == 2
    assert CATEGORY_TAGS["geopolitics"] == 100265
    assert CATEGORY_TAGS["economy"] == 100328
    assert CATEGORY_TAGS["sports"] == 1
    assert CATEGORY_TAGS["science_tech"] == 1401
    assert CATEGORY_TAGS["culture"] == 596
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_polymarket.py::test_fetch_events_by_category_uses_tag_id -v`
Expected: FAIL with "cannot import name 'fetch_events_by_category'"

**Step 3: Write implementation**

Add to `src/polymarket.py`:
```python
CATEGORY_TAGS = {
    "politics": 2,
    "geopolitics": 100265,
    "economy": 100328,
    "science_tech": 1401,
    "sports": 1,
    "culture": 596,
}

CATEGORY_WEIGHTS = {
    "politics": 3,
    "geopolitics": 2,
    "economy": 2,
    "science_tech": 1,
    "sports": 1,
    "culture": 1,
}


def fetch_events_by_category(category: str, limit: int = 20) -> list[dict]:
    """Fetch markets from a category using Polymarket's Events API with tag_id."""
    tag_id = CATEGORY_TAGS.get(category)
    if tag_id is None:
        return []

    url = f"{GAMMA_API_BASE}/events"
    params = {
        "tag_id": tag_id,
        "active": "true",
        "closed": "false",
        "limit": str(limit),
        "order": "volume24hr",
        "ascending": "false",
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    events = response.json()

    # Flatten: extract markets from events, add category and event context
    markets = []
    for event in events:
        event_title = event.get("title", "")
        event_volume = event.get("volume24hr", 0)
        for market in event.get("markets", []):
            market["category"] = category
            market["event_title"] = event_title
            # Use event volume if market volume not available
            if not market.get("volume24hr"):
                market["volume24hr"] = event_volume
            markets.append(market)

    return markets
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_polymarket.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/polymarket.py tests/test_polymarket.py
git commit -m "feat: add fetch_events_by_category using tag_id filtering"
```

---

### Task 3: Create Blocklist Module with Tests

**Files:**
- Create: `src/blocklist.py`
- Create: `tests/test_blocklist.py`

**Step 1: Write the failing test**

Create `tests/test_blocklist.py`:
```python
from src.blocklist import is_blocklisted, passes_thresholds


def test_blocks_tweet_counts():
    assert is_blocklisted("Will Elon Musk post 90-114 tweets from Feb 2 to Feb 4?")
    assert is_blocklisted("Will Elon post 100 tweets tomorrow?")
    assert is_blocklisted("Elon Musk # tweets January 30 - February 6, 2026?")


def test_blocks_daily_crypto_prices():
    assert is_blocklisted("Will the price of Bitcoin be above $80,000 on February 4?")
    assert is_blocklisted("Bitcoin above $100k on Jan 15?")
    assert is_blocklisted("What price will Bitcoin hit in February?")
    assert is_blocklisted("What price will Solana hit in February?")


def test_blocks_esports():
    assert is_blocklisted("LoL: EDward Gaming vs Team WE (BO3)")
    assert is_blocklisted("Valorant Champions 2026 - Team A vs Team B")
    assert is_blocklisted("LCS Spring Split - Match 5")
    assert is_blocklisted("LPL Group Stage Match")
    assert is_blocklisted("LoL: Weibo Gaming vs Anyone's Legend (BO3) - LPL")


def test_allows_legitimate_markets():
    assert not is_blocklisted("Will Trump win the 2028 election?")
    assert not is_blocklisted("Will the Fed cut rates in March?")
    assert not is_blocklisted("US strikes Iran by February 28?")
    assert not is_blocklisted("Who will win Super Bowl LX?")
    assert not is_blocklisted("Thunder vs. Spurs")  # NBA game is allowed


def test_passes_thresholds_filters_resolved():
    assert not passes_thresholds(probability=0.96, volume_24h=500000)
    assert not passes_thresholds(probability=0.04, volume_24h=500000)
    assert passes_thresholds(probability=0.50, volume_24h=500000)


def test_passes_thresholds_filters_low_volume():
    assert not passes_thresholds(probability=0.50, volume_24h=100000)
    assert passes_thresholds(probability=0.50, volume_24h=250000)
    assert passes_thresholds(probability=0.50, volume_24h=500000)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_blocklist.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.blocklist'"

**Step 3: Write implementation**

Create `src/blocklist.py`:
```python
import re

BLOCKLIST_PATTERNS = [
    r"tweet|#\s*tweets",  # Tweet counts
    r"(bitcoin|solana|ethereum).*\$.*on\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",  # Daily crypto
    r"what price will.*(bitcoin|solana|ethereum).*hit",  # Monthly crypto price
    r"\bbo[35]\b|\blpl\b|\blcs\b|\blec\b|\bvalorant\b|\blol:",  # Esports
]

MIN_VOLUME_24H = 250000
RESOLVED_UPPER = 0.95
RESOLVED_LOWER = 0.05


def is_blocklisted(question: str) -> bool:
    """Check if a market question matches any blocklist pattern."""
    question_lower = question.lower()
    for pattern in BLOCKLIST_PATTERNS:
        if re.search(pattern, question_lower):
            return True
    return False


def passes_thresholds(probability: float, volume_24h: float) -> bool:
    """Check if market passes volume and resolution thresholds."""
    if volume_24h < MIN_VOLUME_24H:
        return False
    if probability > RESOLVED_UPPER or probability < RESOLVED_LOWER:
        return False
    return True
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_blocklist.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/blocklist.py tests/test_blocklist.py
git commit -m "feat: add blocklist filtering module"
```

---

### Task 4: Create LLM Module with Tests

**Files:**
- Create: `src/llm.py`
- Create: `tests/test_llm.py`

**Step 1: Write the failing test**

Create `tests/test_llm.py`:
```python
from unittest.mock import Mock, patch

from src.llm import judge_market, LLMResult


def test_judge_market_parses_worthy_response():
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content='{"worthy": true, "summary": "This is important because..."}'))
    ]

    with patch("src.llm.Groq") as mock_groq:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client

        result = judge_market(
            question="Will the Fed cut rates?",
            category="economy",
            probability=0.73,
            change=0.22,
            api_key="test_key",
        )

        assert result.worthy is True
        assert result.summary == "This is important because..."


def test_judge_market_parses_unworthy_response():
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content='{"worthy": false, "summary": null}'))
    ]

    with patch("src.llm.Groq") as mock_groq:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client

        result = judge_market(
            question="Will Elon tweet 100 times?",
            category="culture",
            probability=0.50,
            change=0.05,
            api_key="test_key",
        )

        assert result.worthy is False
        assert result.summary is None


def test_judge_market_handles_malformed_json():
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content="This is not JSON"))
    ]

    with patch("src.llm.Groq") as mock_groq:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client

        result = judge_market(
            question="Test question",
            category="politics",
            probability=0.50,
            change=0.10,
            api_key="test_key",
        )

        assert result.worthy is False
        assert result.summary is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.llm'"

**Step 3: Write implementation**

Create `src/llm.py`:
```python
import json
from dataclasses import dataclass

from groq import Groq


SYSTEM_PROMPT = """You evaluate prediction markets for a news digest. Respond in JSON only.
A market is newsworthy if: (1) it concerns events affecting many people, and (2) the current odds reveal something the mainstream news isn't stating clearly.
Reject: celebrity gossip, social media metrics, crypto price bets, trivial predictions."""


@dataclass
class LLMResult:
    worthy: bool
    summary: str | None


def judge_market(
    question: str,
    category: str,
    probability: float,
    change: float,
    api_key: str,
) -> LLMResult:
    """Use Groq LLM to judge if a market is newsworthy and generate a summary."""
    client = Groq(api_key=api_key)

    change_str = f"+{change*100:.0f}%" if change >= 0 else f"{change*100:.0f}%"
    user_prompt = f"""Market: {question}
Category: {category}
Current: {probability*100:.0f}% | 24h change: {change_str}

{{"worthy": true/false, "summary": "2-3 sentences if worthy, else null"}}"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=200,
    )

    content = response.choices[0].message.content
    try:
        data = json.loads(content)
        return LLMResult(
            worthy=data.get("worthy", False),
            summary=data.get("summary"),
        )
    except (json.JSONDecodeError, KeyError):
        return LLMResult(worthy=False, summary=None)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/llm.py tests/test_llm.py
git commit -m "feat: add Groq LLM integration for market judgment"
```

---

### Task 5: Update Ranker Module

**Files:**
- Modify: `src/ranker.py`
- Modify: `tests/test_ranker.py`

**Step 1: Write failing tests for new pipeline**

Replace `tests/test_ranker.py`:
```python
import json
from unittest.mock import patch, Mock

from src.ranker import filter_markets, select_top_markets


SAMPLE_MARKETS = [
    {
        "question": "Will the Fed cut interest rates in March?",
        "category": "economy",
        "outcomePrices": '["0.73", "0.27"]',
        "volume24hr": 500000.0,
        "oneDayPriceChange": 0.22,
    },
    {
        "question": "Will Elon Musk post 90-114 tweets this week?",
        "category": "culture",
        "outcomePrices": '["0.50", "0.50"]',
        "volume24hr": 300000.0,
        "oneDayPriceChange": 0.10,
    },
    {
        "question": "US strikes Iran by February 28?",
        "category": "geopolitics",
        "outcomePrices": '["0.65", "0.35"]',
        "volume24hr": 1000000.0,
        "oneDayPriceChange": 0.15,
    },
    {
        "question": "LoL: EDward Gaming vs Team WE (BO3)",
        "category": "sports",
        "outcomePrices": '["0.60", "0.40"]',
        "volume24hr": 400000.0,
        "oneDayPriceChange": 0.30,
    },
    {
        "question": "Low volume market",
        "category": "politics",
        "outcomePrices": '["0.50", "0.50"]',
        "volume24hr": 50000.0,
        "oneDayPriceChange": 0.40,
    },
]


def test_filter_markets_removes_blocklisted():
    result = filter_markets(SAMPLE_MARKETS)
    questions = [m["question"] for m in result]
    assert "Will Elon Musk post 90-114 tweets this week?" not in questions
    assert "LoL: EDward Gaming vs Team WE (BO3)" not in questions


def test_filter_markets_removes_low_volume():
    result = filter_markets(SAMPLE_MARKETS)
    questions = [m["question"] for m in result]
    assert "Low volume market" not in questions


def test_filter_markets_keeps_valid():
    result = filter_markets(SAMPLE_MARKETS)
    questions = [m["question"] for m in result]
    assert "Will the Fed cut interest rates in March?" in questions
    assert "US strikes Iran by February 28?" in questions


def test_select_top_markets_respects_weights():
    markets = [
        {"question": "Politics 1", "category": "politics", "oneDayPriceChange": 0.30},
        {"question": "Politics 2", "category": "politics", "oneDayPriceChange": 0.25},
        {"question": "Politics 3", "category": "politics", "oneDayPriceChange": 0.20},
        {"question": "Politics 4", "category": "politics", "oneDayPriceChange": 0.15},
        {"question": "Geopolitics 1", "category": "geopolitics", "oneDayPriceChange": 0.40},
        {"question": "Geopolitics 2", "category": "geopolitics", "oneDayPriceChange": 0.35},
        {"question": "Economy 1", "category": "economy", "oneDayPriceChange": 0.50},
        {"question": "Economy 2", "category": "economy", "oneDayPriceChange": 0.45},
        {"question": "Sports 1", "category": "sports", "oneDayPriceChange": 0.60},
    ]

    result = select_top_markets(markets, target_total=9)

    categories = [m["category"] for m in result]
    assert categories.count("politics") == 3
    assert categories.count("geopolitics") == 2
    assert categories.count("economy") == 2


def test_select_top_markets_ranks_by_price_change():
    markets = [
        {"question": "Politics Low", "category": "politics", "oneDayPriceChange": 0.05},
        {"question": "Politics High", "category": "politics", "oneDayPriceChange": 0.50},
        {"question": "Politics Mid", "category": "politics", "oneDayPriceChange": 0.20},
    ]

    result = select_top_markets(markets, target_total=2)
    questions = [m["question"] for m in result]
    assert questions[0] == "Politics High"
    assert questions[1] == "Politics Mid"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_ranker.py -v`
Expected: FAIL with "cannot import name 'filter_markets'"

**Step 3: Replace implementation**

Replace `src/ranker.py`:
```python
import json

from src.blocklist import is_blocklisted, passes_thresholds
from src.polymarket import CATEGORY_WEIGHTS


def _get_probability(market: dict) -> float:
    """Extract probability from market's outcomePrices."""
    prices = market.get("outcomePrices", '["0.5", "0.5"]')
    if isinstance(prices, str):
        prices = json.loads(prices)
    return float(prices[0])


def filter_markets(markets: list[dict]) -> list[dict]:
    """Filter markets through blocklist and threshold checks."""
    result = []
    for market in markets:
        question = market.get("question", "")

        if is_blocklisted(question):
            continue

        probability = _get_probability(market)
        volume_24h = market.get("volume24hr", 0)
        if not passes_thresholds(probability, volume_24h):
            continue

        result.append(market)

    return result


def select_top_markets(markets: list[dict], target_total: int = 10) -> list[dict]:
    """Select top markets from each category based on weights."""
    # Group by category
    by_category: dict[str, list[dict]] = {}
    for market in markets:
        cat = market.get("category")
        if cat:
            by_category.setdefault(cat, []).append(market)

    # Sort each category by absolute price change
    for cat in by_category:
        by_category[cat].sort(
            key=lambda m: abs(m.get("oneDayPriceChange", 0)),
            reverse=True,
        )

    # Calculate total weight for categories we have
    total_weight = sum(CATEGORY_WEIGHTS.get(cat, 0) for cat in by_category)
    if total_weight == 0:
        return []

    # First pass: allocate based on weights
    selected: list[dict] = []
    remaining_slots = target_total

    for cat, weight in sorted(CATEGORY_WEIGHTS.items(), key=lambda x: -x[1]):
        if cat not in by_category or remaining_slots <= 0:
            continue

        allocation = max(1, round((weight / total_weight) * target_total))
        available = by_category[cat]
        take = min(allocation, len(available), remaining_slots)

        selected.extend(available[:take])
        remaining_slots -= take

    # Second pass: fill remaining slots
    if remaining_slots > 0:
        for cat, weight in sorted(CATEGORY_WEIGHTS.items(), key=lambda x: -x[1]):
            if cat not in by_category or remaining_slots <= 0:
                continue

            already_taken = sum(1 for m in selected if m.get("category") == cat)
            available = by_category[cat][already_taken:]

            for market in available:
                if remaining_slots <= 0:
                    break
                selected.append(market)
                remaining_slots -= 1

    return selected[:target_total]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_ranker.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ranker.py tests/test_ranker.py
git commit -m "feat: update ranker with blocklist filtering and weighted selection"
```

---

### Task 6: Update Email Template for Summaries

**Files:**
- Modify: `src/email_template.py`
- Modify: `tests/test_email_template.py`

**Step 1: Write failing test for summary display**

Add to `tests/test_email_template.py`:
```python
def test_render_market_row_displays_summary():
    market = {
        "question": "Will the Fed cut rates?",
        "slug": "fed-rate-cut",
        "description": "Original description",
        "summary": "Traders give 73% odds to a Fed rate cut. This follows weak jobs data.",
        "outcomePrices": '["0.73", "0.27"]',
        "oneDayPriceChange": 0.22,
        "volume24hr": 500000.0,
    }
    html = render_newsletter([market], date_str="Feb 4, 2026")

    assert "Traders give 73% odds to a Fed rate cut" in html
    assert "This follows weak jobs data" in html
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_email_template.py::test_render_market_row_displays_summary -v`
Expected: FAIL (summary not in output)

**Step 3: Update implementation**

In `src/email_template.py`, change line 41 from:
```python
    description = _truncate(market.get("description", ""))
```
to:
```python
    summary = market.get("summary")
    description = summary if summary else _truncate(market.get("description", ""))
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_email_template.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/email_template.py tests/test_email_template.py
git commit -m "feat: display LLM summary in email template"
```

---

### Task 7: Update Main Orchestrator

**Files:**
- Modify: `src/main.py`
- Modify: `tests/test_main.py`

**Step 1: Write failing test**

Replace `tests/test_main.py`:
```python
from unittest.mock import patch, Mock

from src.main import run


def test_run_fetches_all_categories():
    mock_markets = [
        {
            "question": "Test market",
            "slug": "test",
            "category": "politics",
            "outcomePrices": '["0.70", "0.30"]',
            "oneDayPriceChange": 0.20,
            "volume24hr": 500000.0,
            "summary": "Test summary",
        }
    ]

    with patch("src.main.fetch_events_by_category", return_value=mock_markets) as mock_fetch:
        with patch("src.main.filter_markets", return_value=mock_markets):
            with patch("src.main.judge_market") as mock_judge:
                mock_judge.return_value = Mock(worthy=True, summary="Test summary")
                with patch("src.main.select_top_markets", return_value=mock_markets):
                    with patch("src.main.render_newsletter", return_value="<html>"):
                        with patch("src.main.send_newsletter", return_value=["id1"]):
                            run(
                                resend_api_key="test",
                                audience_id="test",
                                from_email="test@test.com",
                                groq_api_key="test_groq",
                            )

    # Should fetch from all categories
    assert mock_fetch.call_count == 6  # 6 categories


def test_run_skips_send_when_no_markets():
    with patch("src.main.fetch_events_by_category", return_value=[]):
        with patch("src.main.filter_markets", return_value=[]):
            with patch("src.main.select_top_markets", return_value=[]):
                with patch("src.main.send_newsletter") as mock_send:
                    run(
                        resend_api_key="test",
                        audience_id="test",
                        from_email="test@test.com",
                        groq_api_key="test_groq",
                    )

    mock_send.assert_not_called()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py -v`
Expected: FAIL

**Step 3: Update implementation**

Replace `src/main.py`:
```python
import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from src.polymarket import fetch_events_by_category, CATEGORY_TAGS
from src.ranker import filter_markets, select_top_markets
from src.llm import judge_market
from src.email_template import render_newsletter
from src.sender import send_newsletter


def run(
    resend_api_key: str,
    audience_id: str,
    from_email: str,
    groq_api_key: str,
) -> None:
    """Orchestrate the newsletter pipeline: fetch -> filter -> judge -> select -> send."""
    # Stage 1: Fetch from all categories
    all_markets = []
    for category in CATEGORY_TAGS.keys():
        markets = fetch_events_by_category(category, limit=20)
        all_markets.extend(markets)

    # Stage 2 & 3: Blocklist + volume filtering
    filtered = filter_markets(all_markets)

    if not filtered:
        print("No markets passed filtering. Skipping send.")
        return

    # Stage 4: LLM judgment (limit API calls)
    worthy_markets = []
    for market in filtered[:50]:  # Cap at 50 LLM calls
        result = judge_market(
            question=market["question"],
            category=market.get("category", "unknown"),
            probability=float(market.get("outcomePrices", '["0.5"]')[0] if isinstance(market.get("outcomePrices"), list) else 0.5),
            change=market.get("oneDayPriceChange", 0),
            api_key=groq_api_key,
        )
        if result.worthy:
            market["summary"] = result.summary
            worthy_markets.append(market)

    # Stage 5: Weighted selection
    top_movers = select_top_markets(worthy_markets, target_total=10)

    if not top_movers:
        print("No worthy markets found. Skipping send.")
        return

    # Stage 6: Render and send
    date_str = datetime.now(timezone.utc).strftime("%b %-d, %Y")
    subject = f"Top Movers — {date_str}"
    html = render_newsletter(top_movers, date_str=date_str)

    email_ids = send_newsletter(
        html=html,
        subject=subject,
        audience_id=audience_id,
        from_email=from_email,
        api_key=resend_api_key,
    )
    print(f"Newsletter sent to {len(email_ids)} recipients.")


if __name__ == "__main__":
    run(
        resend_api_key=os.environ["RESEND_API_KEY"],
        audience_id=os.environ["RESEND_AUDIENCE_ID"],
        from_email=os.environ.get("FROM_EMAIL", "Newsletter <newsletter@yourdomain.com>"),
        groq_api_key=os.environ["GROQ_API_KEY"],
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/main.py tests/test_main.py
git commit -m "feat: update main orchestrator for quality filtering pipeline"
```

---

### Task 8: Update GitHub Actions Workflow

**Files:**
- Modify: `.github/workflows/newsletter.yml`

**Step 1: Check workflow file**

Run: `cat .github/workflows/newsletter.yml`

**Step 2: Add GROQ_API_KEY to workflow env**

Add to the env section:
```yaml
env:
  RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
  RESEND_AUDIENCE_ID: ${{ secrets.RESEND_AUDIENCE_ID }}
  GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
```

**Step 3: Commit**

```bash
git add .github/workflows/newsletter.yml
git commit -m "chore: add GROQ_API_KEY to GitHub Actions workflow"
```

---

### Task 9: Run Full Test Suite

**Step 1: Install new dependency**

Run: `pip install groq`

**Step 2: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 3: Commit any fixes**

```bash
git add -A
git commit -m "fix: address test failures"
```

---

### Task 10: Manual Integration Test (Optional)

**Step 1: Add GROQ_API_KEY to .env**

Get a free API key from https://console.groq.com and add to `.env`:
```
GROQ_API_KEY=gsk_your_actual_key
```

**Step 2: Run locally**

Run: `python -m src.main`

**Step 3: Verify output**

Check that:
- Markets are fetched from multiple categories
- Blocklisted content (tweets, esports, crypto prices) is filtered
- Each market has an LLM-generated summary
- Categories are balanced according to weights
