# crypto_converter/coin_ticker_resolver.py

# Standard Libraries
from dataclasses import dataclass
from typing import Final, Optional

# Custom Modules
from crypto_converter.coingecko_client import (
    get_coins_by_symbol,
    search_coins,
)
from crypto_converter.crypto_amount_parser import parse_crypto_amount_from_text


# Coin ticker resolution
BLOCKED_TICKERS: Final[frozenset[str]] = frozenset(
    {"KG", "CM", "UTC"}
)


@dataclass(frozen=True)
class ResolvedCoin:
    """Represent canonical CoinGecko metadata for a ticker."""

    coin_id: str
    ticker: str
    name: str


KNOWN_COINS: Final[dict[str, ResolvedCoin]] = {
    "BTC": ResolvedCoin("bitcoin", "BTC", "Bitcoin"),
    "ETH": ResolvedCoin("ethereum", "ETH", "Ethereum"),
    "BNB": ResolvedCoin("binancecoin", "BNB", "BNB"),
    "SOL": ResolvedCoin("solana", "SOL", "Solana"),
    "USD": ResolvedCoin("tether", "USDT", "Tether"),
    "USDT": ResolvedCoin("tether", "USDT", "Tether"),
}
TICKER_CACHE: dict[str, ResolvedCoin] = {}


def resolve_coin(ticker: str) -> Optional[ResolvedCoin]:
    """Resolve a ticker to canonical CoinGecko coin metadata."""
    normalized_ticker = ticker.strip().upper()

    if not normalized_ticker or normalized_ticker in BLOCKED_TICKERS:
        return None

    known_coin = KNOWN_COINS.get(normalized_ticker)

    if known_coin is not None:
        return known_coin

    cached_coin = TICKER_CACHE.get(normalized_ticker)

    if cached_coin is not None:
        return cached_coin

    for coin in get_coins_by_symbol(normalized_ticker):
        if coin.symbol.upper() == normalized_ticker:
            resolved_coin = ResolvedCoin(
                coin_id=coin.coin_id,
                ticker=coin.symbol.upper(),
                name=coin.name,
            )
            TICKER_CACHE[normalized_ticker] = resolved_coin
            return resolved_coin

    for coin in search_coins(normalized_ticker):
        if coin.symbol.upper() == normalized_ticker:
            resolved_coin = ResolvedCoin(
                coin_id=coin.coin_id,
                ticker=coin.symbol.upper(),
                name=coin.name,
            )
            TICKER_CACHE[normalized_ticker] = resolved_coin
            return resolved_coin

    return None


def resolve_coin_ticker(ticker: str) -> Optional[str]:
    """Resolve a ticker to its highest-ranked exact CoinGecko match."""
    resolved_coin = resolve_coin(ticker)

    if resolved_coin is None:
        return None

    return resolved_coin.coin_id


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
