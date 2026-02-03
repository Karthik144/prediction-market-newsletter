import json
from unittest.mock import patch, MagicMock
from src.polymarket import fetch_active_markets

SAMPLE_MARKETS_RESPONSE = [
    {
        "id": "123",
        "question": "Will X happen?",
        "slug": "will-x-happen",
        "description": "This market resolves to Yes if X happens by Dec 31.",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.65", "0.35"],
        "volume": "500000",
        "volume24hr": 50000.0,
        "liquidity": "100000",
        "clobTokenIds": ["token1", "token2"],
        "lastTradePrice": 0.65,
        "oneDayPriceChange": 0.15,
    },
    {
        "id": "456",
        "question": "Will Y happen?",
        "slug": "will-y-happen",
        "description": "This market resolves to Yes if Y happens.",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.30", "0.70"],
        "volume": "1000",
        "volume24hr": 50.0,
        "liquidity": "200",
        "clobTokenIds": ["token3", "token4"],
        "lastTradePrice": 0.30,
        "oneDayPriceChange": -0.25,
    },
]


@patch("src.polymarket.requests.get")
def test_fetch_active_markets_returns_parsed_markets(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_MARKETS_RESPONSE
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    markets = fetch_active_markets()

    assert len(markets) == 2
    assert markets[0]["question"] == "Will X happen?"
    assert markets[0]["oneDayPriceChange"] == 0.15
    mock_get.assert_called_once()


@patch("src.polymarket.requests.get")
def test_fetch_active_markets_calls_gamma_api(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    fetch_active_markets()

    call_args = mock_get.call_args
    assert "gamma-api.polymarket.com" in call_args[0][0]
    assert call_args[1]["params"]["active"] == "true"
