import requests

GAMMA_API_BASE = "https://gamma-api.polymarket.com"

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
