# crypto_converter/coin_ticker_resolver.py

# Standard Libraries
from typing import Final, Optional

# Custom Modules
from crypto_converter.coingecko_client import search_coins
from crypto_converter.crypto_amount_parser import parse_crypto_amount_from_text


# Coin ticker resolution
BLOCKED_TICKERS: Final[frozenset[str]] = frozenset(
    {"KG", "CM"}
)
KNOWN_COINS: Final[dict[str, str]] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "SOL": "solana",
    "USD": "tether",
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


if __name__ == "__main__":
    from crypto_converter.crypto_price_converter import convert_crypto_to_fiat

    while True:
        input_text = input("Enter text (enter q to exit): ")

        if input_text.lower() in ("quit", "q", "exit", "leave"):
            print("Goodbye!")
            break

        parsed_crypto_amount = parse_crypto_amount_from_text(input_text)

        if parsed_crypto_amount is None:
            print("Crypto amount not found.\n")
            continue

        conversion = convert_crypto_to_fiat(
            amount=parsed_crypto_amount.amount,
            ticker=parsed_crypto_amount.ticker,
        )

        if conversion is None:
            print(f"Coin not found: {parsed_crypto_amount.ticker}\n")
            continue

        print("Amount:", conversion.amount)
        print("Ticker:", conversion.ticker)
        print("Matched text:", parsed_crypto_amount.matched_text)
        print("CoinGecko ID:", conversion.coin_id)
        print("Total USD:", conversion.total_usd)
        print(f"Total UAH: {conversion.total_uah}\n")
