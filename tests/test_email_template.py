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
