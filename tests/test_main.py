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
