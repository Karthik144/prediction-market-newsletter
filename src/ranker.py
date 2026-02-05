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
    
    result.sort(key=lambda x: x.get("volume24hr", 0), reverse=True)

    return result[:5]


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
