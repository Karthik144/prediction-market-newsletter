from src.blocklist import is_blocklisted, passes_thresholds


def test_blocks_tweet_counts():
    assert is_blocklisted("Will Elon Musk post 90-114 tweets from Feb 2 to Feb 4?")
    assert is_blocklisted("Will Elon post 100 tweets tomorrow?")
    assert is_blocklisted("Elon Musk # tweets January 30 - February 6, 2026?")


def test_blocks_daily_crypto_prices():
    assert is_blocklisted("Will the price of Bitcoin be above $80,000 on February 4?")
    assert is_blocklisted("Bitcoin above $100k on Jan 15?")
    assert is_blocklisted("What price will Bitcoin hit in February?")
    assert is_blocklisted("What price will Solana hit in February?")


def test_blocks_esports():
    assert is_blocklisted("LoL: EDward Gaming vs Team WE (BO3)")
    assert is_blocklisted("Valorant Champions 2026 - Team A vs Team B")
    assert is_blocklisted("LCS Spring Split - Match 5")
    assert is_blocklisted("LPL Group Stage Match")
    assert is_blocklisted("LoL: Weibo Gaming vs Anyone's Legend (BO3) - LPL")


def test_allows_legitimate_markets():
    assert not is_blocklisted("Will Trump win the 2028 election?")
    assert not is_blocklisted("Will the Fed cut rates in March?")
    assert not is_blocklisted("US strikes Iran by February 28?")
    assert not is_blocklisted("Who will win Super Bowl LX?")
    assert not is_blocklisted("Thunder vs. Spurs")  # NBA game is allowed


def test_passes_thresholds_filters_resolved():
    assert not passes_thresholds(probability=0.96, volume_24h=500000)
    assert not passes_thresholds(probability=0.04, volume_24h=500000)
    assert passes_thresholds(probability=0.50, volume_24h=500000)


def test_passes_thresholds_filters_low_volume():
    assert not passes_thresholds(probability=0.50, volume_24h=100000)
    assert passes_thresholds(probability=0.50, volume_24h=250000)
    assert passes_thresholds(probability=0.50, volume_24h=500000)
