# crypto_converter/coin_ticker_resolver.py

# Standard Libraries
from typing import Final, Optional

# Custom Modules
from crypto_converter.coingecko_client import search_coins


# Coin ticker resolution
BLOCKED_TICKERS: Final[frozenset[str]] = frozenset(
    {"KG", "CM"}
)
KNOWN_COINS: Final[dict[str, str]] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "SOL": "solana",
    "USDT": "tether",
}
TICKER_CACHE: dict[str, str] = {}


def resolve_coin_ticker(ticker: str) -> Optional[str]:
    """Resolve a ticker to its highest-ranked exact CoinGecko match."""
    normalized_ticker = ticker.strip().upper()

    if not normalized_ticker or normalized_ticker in BLOCKED_TICKERS:
        return None

    known_coin_id = KNOWN_COINS.get(normalized_ticker)

    if known_coin_id is not None:
        return known_coin_id

    cached_coin_id = TICKER_CACHE.get(normalized_ticker)

    if cached_coin_id is not None:
        return cached_coin_id

    for coin in search_coins(normalized_ticker):
        if coin.symbol.upper() == normalized_ticker:
            TICKER_CACHE[normalized_ticker] = coin.coin_id
            return coin.coin_id

    return None
