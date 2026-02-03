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
