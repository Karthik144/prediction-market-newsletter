from unittest.mock import patch, MagicMock
from src.sender import send_newsletter


@patch("src.sender.resend")
def test_send_newsletter_sends_to_all_contacts(mock_resend):
    mock_resend.Contacts.list.return_value = {
        "data": [
            {"email": "user1@example.com", "unsubscribed": False},
            {"email": "user2@example.com", "unsubscribed": False},
        ]
    }
    mock_resend.Emails.send.return_value = {"id": "email-123"}

    result = send_newsletter(
        html="<h1>Test</h1>",
        subject="Top Movers - Feb 3, 2026",
        audience_id="audience-456",
        from_email="Newsletter <news@example.com>",
        api_key="re_test_key",
    )

    assert len(result) == 2
    assert mock_resend.Emails.send.call_count == 2
    mock_resend.Contacts.list.assert_called_once_with(audience_id="audience-456")


@patch("src.sender.resend")
def test_send_newsletter_skips_unsubscribed(mock_resend):
    mock_resend.Contacts.list.return_value = {
        "data": [
            {"email": "user1@example.com", "unsubscribed": False},
            {"email": "user2@example.com", "unsubscribed": True},
        ]
    }
    mock_resend.Emails.send.return_value = {"id": "email-123"}

    result = send_newsletter(
        html="<h1>Test</h1>",
        subject="Test",
        audience_id="aud-1",
        from_email="test@example.com",
        api_key="re_my_key",
    )

    assert len(result) == 1
    assert mock_resend.Emails.send.call_count == 1


@patch("src.sender.resend")
def test_send_newsletter_sets_api_key(mock_resend):
    mock_resend.Contacts.list.return_value = {"data": []}

    send_newsletter(
        html="<h1>Test</h1>",
        subject="Test",
        audience_id="aud-1",
        from_email="test@example.com",
        api_key="re_my_key",
    )

    assert mock_resend.api_key == "re_my_key"
