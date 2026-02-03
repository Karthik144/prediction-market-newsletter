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
