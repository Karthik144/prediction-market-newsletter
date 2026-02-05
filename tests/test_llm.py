from unittest.mock import Mock, patch

from src.llm import judge_market, LLMResult


def test_judge_market_parses_worthy_response():
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content='{"worthy": true, "summary": "This is important because..."}'))
    ]

    with patch("src.llm.Groq") as mock_groq:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client

        result = judge_market(
            question="Will the Fed cut rates?",
            category="economy",
            probability=0.73,
            change=0.22,
            api_key="test_key",
        )

        assert result.worthy is True
        assert result.summary == "This is important because..."


def test_judge_market_parses_unworthy_response():
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content='{"worthy": false, "summary": null}'))
    ]

    with patch("src.llm.Groq") as mock_groq:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client

        result = judge_market(
            question="Will Elon tweet 100 times?",
            category="culture",
            probability=0.50,
            change=0.05,
            api_key="test_key",
        )

        assert result.worthy is False
        assert result.summary is None


def test_judge_market_handles_malformed_json():
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content="This is not JSON"))
    ]

    with patch("src.llm.Groq") as mock_groq:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client

        result = judge_market(
            question="Test question",
            category="politics",
            probability=0.50,
            change=0.10,
            api_key="test_key",
        )

        assert result.worthy is False
        assert result.summary is None
