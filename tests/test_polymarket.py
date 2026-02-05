import json
from unittest.mock import patch, MagicMock, Mock
from src.polymarket import fetch_active_markets, fetch_events_by_category, CATEGORY_TAGS

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


def test_fetch_events_by_category_uses_tag_id():
    mock_response = Mock()
    mock_response.json.return_value = [
        {"id": "1", "title": "Test Event", "markets": [{"question": "Test?"}]}
    ]
    mock_response.raise_for_status = Mock()

    with patch("src.polymarket.requests.get", return_value=mock_response) as mock_get:
        result = fetch_events_by_category("politics", limit=10)

        # Verify tag_id was passed
        call_args = mock_get.call_args
        assert call_args[1]["params"]["tag_id"] == CATEGORY_TAGS["politics"]
        assert call_args[1]["params"]["limit"] == "10"


def test_fetch_events_by_category_returns_markets():
    mock_response = Mock()
    mock_response.json.return_value = [
        {
            "id": "1",
            "title": "Fed Decision",
            "volume24hr": 500000,
            "markets": [
                {"question": "Will Fed cut rates?", "outcomePrices": '["0.7", "0.3"]'}
            ]
        }
    ]
    mock_response.raise_for_status = Mock()

    with patch("src.polymarket.requests.get", return_value=mock_response):
        result = fetch_events_by_category("economy", limit=10)

        assert len(result) == 1
        assert result[0]["question"] == "Will Fed cut rates?"
        assert result[0]["category"] == "economy"
        assert result[0]["event_title"] == "Fed Decision"


def test_category_tags_exist():
    assert CATEGORY_TAGS["politics"] == 2
    assert CATEGORY_TAGS["geopolitics"] == 100265
    assert CATEGORY_TAGS["economy"] == 100328
    assert CATEGORY_TAGS["sports"] == 1
    assert CATEGORY_TAGS["science_tech"] == 1401
    assert CATEGORY_TAGS["culture"] == 596
