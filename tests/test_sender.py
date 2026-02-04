from unittest.mock import patch, MagicMock
from src.sender import send_newsletter


@patch("src.sender.resend")
def test_send_newsletter_creates_and_sends_broadcast(mock_resend):
    mock_resend.Broadcasts.create.return_value = {"id": "broadcast-123"}

    send_newsletter(
        html="<h1>Test</h1>",
        subject="Top Movers - Feb 3, 2026",
        segment_id="segment-456",
        from_email="Newsletter <news@example.com>",
        api_key="re_test_key",
    )

    mock_resend.Broadcasts.create.assert_called_once_with({
        "segment_id": "segment-456",
        "from": "Newsletter <news@example.com>",
        "subject": "Top Movers - Feb 3, 2026",
        "html": "<h1>Test</h1>",
    })
    mock_resend.Broadcasts.send.assert_called_once_with("broadcast-123")


@patch("src.sender.resend")
def test_send_newsletter_sets_api_key(mock_resend):
    mock_resend.Broadcasts.create.return_value = {"id": "broadcast-123"}

    send_newsletter(
        html="<h1>Test</h1>",
        subject="Test",
        segment_id="seg-1",
        from_email="test@example.com",
        api_key="re_my_key",
    )

    assert mock_resend.api_key == "re_my_key"
