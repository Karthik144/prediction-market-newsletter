# Quality Filtering Pipeline — Design

## Overview

Replace the current "rank by 24h price change" approach with a multi-stage quality filtering pipeline. The goal: surface important world events across categories (politics, geopolitics, economy, etc.) rather than noise (tweet counts, daily crypto bets, esports).

## Pipeline

```
Stage 1: Fetch by Category
    → Query Polymarket Events API with tag_id for each category
    → Polymarket already categorizes events with tags

Stage 2: Blocklist Filtering
    → Remove: tweet counts, daily crypto bets, esports, resolved (>95%/<5%)

Stage 3: Volume Filter
    → Minimum 24h volume: $250,000
    → Rank by volume within each category

Stage 4: LLM Quality Filter + Summary (Groq)
    → Send top N by volume per category
    → Returns: worthy (bool) + 2-3 sentence summary

Stage 5: Weighted Selection
    → Politics: 3, Geopolitics: 2, Economy: 2
    → Science/Tech: 1, Sports: 1, Culture: 1
    → Target: ~10 markets total

Stage 6: Render & Send
    → HTML email with market + LLM summary
    → Send via Resend
```

## Category Configuration

### Tag IDs (from Polymarket API)

Use Polymarket's existing event tags via the Events API `tag_id` parameter:

```python
CATEGORY_TAGS = {
    "politics": 2,
    "geopolitics": 100265,
    "economy": 100328,
    "science_tech": 1401,
    "sports": 1,
    "culture": 596,
}
```

### Category Weights

```python
CATEGORY_WEIGHTS = {
    "politics": 3,
    "geopolitics": 2,
    "economy": 2,
    "science_tech": 1,
    "sports": 1,
    "culture": 1,
}
TARGET_TOTAL = 10
```

## Blocklist Filtering

### Pattern Blocklist

```python
BLOCKLIST_PATTERNS = [
    r"tweet|post.*\d+.*tweets",           # Tweet counts
    r"bitcoin.*\$.*on (jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",  # Daily crypto prices
    r"bo3|bo5|lpl|lcs|lec|valorant",      # Esports
]
```

### Threshold Blocklist

```python
BLOCKLIST_THRESHOLDS = {
    "resolved_upper": 0.95,   # Markets > 95% (already decided)
    "resolved_lower": 0.05,   # Markets < 5% (already decided)
    "min_volume_24h": 250000, # Minimum $250k volume
}
```

## LLM Integration (Groq)

### Provider

- **Groq** with Llama 3.1 8B
- Free tier: 14k+ requests/day
- Fast inference (~500 tokens/sec)

### Prompt Design

**System prompt (~100 tokens):**
```
You evaluate prediction markets for a news digest. Respond in JSON only.
A market is newsworthy if: (1) it concerns events affecting many people, and (2) the current odds reveal something the mainstream news isn't stating clearly.
Reject: celebrity gossip, sports scores, social media metrics, crypto price bets, trivial predictions.
```

**User prompt (~50 tokens + market data):**
```
Market: {question}
Category: {category}
Current: {probability}% | 24h change: {change}

{"worthy": true/false, "summary": "2-3 sentences if worthy, else null"}
```

**Example response:**
```json
{"worthy": true, "summary": "Traders give 73% odds to a Fed rate cut in March, up from 51% yesterday. This shift follows weaker-than-expected jobs data and suggests markets expect the Fed to pivot sooner than officials have signaled."}
```

### Token Budget

- ~200 tokens per market
- ~50 markets sent to LLM per day
- ~10k tokens/day — well within free tier

## Email Format

```
Market: Will the Fed cut rates in March?
Current: 73% | 24h change: +22%

Traders give 73% odds to a Fed rate cut in March, up from 51%
yesterday. This shift follows weaker-than-expected jobs data and
suggests markets expect the Fed to pivot sooner than officials
have signaled.

Volume: $1.2M | [View on Polymarket]
```

## Code Changes

### Files to Modify

| File | Changes |
|------|---------|
| `src/polymarket.py` | Add `fetch_events_by_category()` using Events API with tag_id |
| `src/ranker.py` | Replace with blocklist filtering + volume threshold + weighted selection |
| `src/main.py` | Update orchestration for new pipeline |
| `src/email_template.py` | Display LLM summaries |

### New Files

| File | Purpose |
|------|---------|
| `src/llm.py` | Groq client for quality filtering + summary |

### Dependencies

Add to `requirements.txt`:
```
groq
```

### Environment Variables

Add:
- `GROQ_API_KEY` — Groq API key (GitHub Actions secret)

## Weighted Selection Algorithm

1. Fetch events from each category using tag_id
2. Apply blocklist and volume threshold
3. Send candidates to LLM for judgment
4. Group LLM-approved markets by category
5. Within each category, rank by 24h price change (biggest movers first)
6. Allocate slots based on weights (politics: 3, geopolitics: 2, etc.)
7. If a category has fewer markets than allocation, redistribute to others
8. Cap at TARGET_TOTAL (10)
