import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

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
    )
