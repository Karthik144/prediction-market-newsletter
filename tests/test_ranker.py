from src.ranker import rank_top_movers

SAMPLE_MARKETS = [
    {
        "id": "1",
        "question": "Big mover",
        "slug": "big-mover",
        "description": "Desc 1",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.80", "0.20"],
        "volume24hr": 100000.0,
        "liquidity": "50000",
        "oneDayPriceChange": 0.30,
    },
    {
        "id": "2",
        "question": "Small mover",
        "slug": "small-mover",
        "description": "Desc 2",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.50", "0.50"],
        "volume24hr": 80000.0,
        "liquidity": "40000",
        "oneDayPriceChange": 0.02,
    },
    {
        "id": "3",
        "question": "Medium mover",
        "slug": "medium-mover",
        "description": "Desc 3",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.40", "0.60"],
        "volume24hr": 90000.0,
        "liquidity": "45000",
        "oneDayPriceChange": -0.15,
    },
    {
        "id": "4",
        "question": "Low volume mover",
        "slug": "low-volume",
        "description": "Desc 4",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.90", "0.10"],
        "volume24hr": 500.0,
        "liquidity": "100",
        "oneDayPriceChange": 0.50,
    },
]


def test_rank_top_movers_sorts_by_absolute_change():
    result = rank_top_movers(SAMPLE_MARKETS, top_n=10, min_volume_24h=0)
    assert result[0]["question"] == "Low volume mover"  # |0.50|
    assert result[1]["question"] == "Big mover"  # |0.30|
    assert result[2]["question"] == "Medium mover"  # |-0.15|


def test_rank_top_movers_filters_low_volume():
    result = rank_top_movers(SAMPLE_MARKETS, top_n=10, min_volume_24h=10000)
    questions = [m["question"] for m in result]
    assert "Low volume mover" not in questions
    assert len(result) == 3


def test_rank_top_movers_limits_results():
    result = rank_top_movers(SAMPLE_MARKETS, top_n=2, min_volume_24h=0)
    assert len(result) == 2


def test_rank_top_movers_skips_markets_without_price_change():
    markets = [
        {
            "id": "5",
            "question": "No change data",
            "slug": "no-change",
            "description": "Desc",
            "outcomes": ["Yes", "No"],
            "outcomePrices": ["0.50", "0.50"],
            "volume24hr": 50000.0,
            "liquidity": "10000",
        },
    ]
    result = rank_top_movers(markets, top_n=10, min_volume_24h=0)
    assert len(result) == 0
