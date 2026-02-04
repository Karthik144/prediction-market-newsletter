from unittest.mock import patch, MagicMock
from src.main import run


@patch("src.main.send_newsletter")
@patch("src.main.render_newsletter")
@patch("src.main.rank_top_movers")
@patch("src.main.fetch_active_markets")
def test_run_orchestrates_pipeline(mock_fetch, mock_rank, mock_render, mock_send):
    mock_fetch.return_value = [{"id": "1"}]
    mock_rank.return_value = [{"id": "1", "question": "Test?"}]
    mock_render.return_value = "<html>newsletter</html>"
    mock_send.return_value = "broadcast-123"

    run(
        resend_api_key="re_key",
        segment_id="seg-1",
        from_email="test@example.com",
    )

    mock_fetch.assert_called_once()
    mock_rank.assert_called_once_with(mock_fetch.return_value, top_n=10, min_volume_24h=10000)
    mock_render.assert_called_once()
    mock_send.assert_called_once()


@patch("src.main.send_newsletter")
@patch("src.main.render_newsletter")
@patch("src.main.rank_top_movers")
@patch("src.main.fetch_active_markets")
def test_run_skips_send_when_no_movers(mock_fetch, mock_rank, mock_render, mock_send):
    mock_fetch.return_value = [{"id": "1"}]
    mock_rank.return_value = []

    run(
        resend_api_key="re_key",
        segment_id="seg-1",
        from_email="test@example.com",
    )

    mock_render.assert_not_called()
    mock_send.assert_not_called()
