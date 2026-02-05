import json
from unittest.mock import patch, Mock

from src.ranker import filter_markets, select_top_markets


SAMPLE_MARKETS = [
    {
        "question": "Will the Fed cut interest rates in March?",
        "category": "economy",
        "outcomePrices": '["0.73", "0.27"]',
        "volume24hr": 500000.0,
        "oneDayPriceChange": 0.22,
    },
    {
        "question": "Will Elon Musk post 90-114 tweets this week?",
        "category": "culture",
        "outcomePrices": '["0.50", "0.50"]',
        "volume24hr": 300000.0,
        "oneDayPriceChange": 0.10,
    },
    {
        "question": "US strikes Iran by February 28?",
        "category": "geopolitics",
        "outcomePrices": '["0.65", "0.35"]',
        "volume24hr": 1000000.0,
        "oneDayPriceChange": 0.15,
    },
    {
        "question": "LoL: EDward Gaming vs Team WE (BO3)",
        "category": "sports",
        "outcomePrices": '["0.60", "0.40"]',
        "volume24hr": 400000.0,
        "oneDayPriceChange": 0.30,
    },
    {
        "question": "Low volume market",
        "category": "politics",
        "outcomePrices": '["0.50", "0.50"]',
        "volume24hr": 50000.0,
        "oneDayPriceChange": 0.40,
    },
]


def test_filter_markets_removes_blocklisted():
    result = filter_markets(SAMPLE_MARKETS)
    questions = [m["question"] for m in result]
    assert "Will Elon Musk post 90-114 tweets this week?" not in questions
    assert "LoL: EDward Gaming vs Team WE (BO3)" not in questions


def test_filter_markets_removes_low_volume():
    result = filter_markets(SAMPLE_MARKETS)
    questions = [m["question"] for m in result]
    assert "Low volume market" not in questions


def test_filter_markets_keeps_valid():
    result = filter_markets(SAMPLE_MARKETS)
    questions = [m["question"] for m in result]
    assert "Will the Fed cut interest rates in March?" in questions
    assert "US strikes Iran by February 28?" in questions


def test_select_top_markets_respects_weights():
    markets = [
        {"question": "Politics 1", "category": "politics", "oneDayPriceChange": 0.30},
        {"question": "Politics 2", "category": "politics", "oneDayPriceChange": 0.25},
        {"question": "Politics 3", "category": "politics", "oneDayPriceChange": 0.20},
        {"question": "Politics 4", "category": "politics", "oneDayPriceChange": 0.15},
        {"question": "Geopolitics 1", "category": "geopolitics", "oneDayPriceChange": 0.40},
        {"question": "Geopolitics 2", "category": "geopolitics", "oneDayPriceChange": 0.35},
        {"question": "Economy 1", "category": "economy", "oneDayPriceChange": 0.50},
        {"question": "Economy 2", "category": "economy", "oneDayPriceChange": 0.45},
        {"question": "Sports 1", "category": "sports", "oneDayPriceChange": 0.60},
    ]

    result = select_top_markets(markets, target_total=9)

    categories = [m["category"] for m in result]
    # Politics has highest weight, so gets most slots (including redistribution)
    assert categories.count("politics") >= 3
    assert categories.count("geopolitics") >= 2
    assert categories.count("economy") >= 2
    assert len(result) == 9


def test_select_top_markets_ranks_by_price_change():
    markets = [
        {"question": "Politics Low", "category": "politics", "oneDayPriceChange": 0.05},
        {"question": "Politics High", "category": "politics", "oneDayPriceChange": 0.50},
        {"question": "Politics Mid", "category": "politics", "oneDayPriceChange": 0.20},
    ]

    result = select_top_markets(markets, target_total=2)
    questions = [m["question"] for m in result]
    assert questions[0] == "Politics High"
    assert questions[1] == "Politics Mid"
