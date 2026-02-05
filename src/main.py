import json
import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from src.polymarket import fetch_events_by_category, CATEGORY_TAGS
from src.ranker import filter_markets, select_top_markets
from src.llm import judge_market
from src.email_template import render_newsletter
from src.sender import send_newsletter


def _get_probability(market: dict) -> float:
    """Extract probability from market's outcomePrices."""
    prices = market.get("outcomePrices", '["0.5", "0.5"]')
    if isinstance(prices, str):
        prices = json.loads(prices)
    return float(prices[0])


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
            probability=_get_probability(market),
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
