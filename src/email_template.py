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
                <a href="{{{{{{RESEND_UNSUBSCRIBE_URL}}}}}}" style="color: #6b7280;">Unsubscribe</a>
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
