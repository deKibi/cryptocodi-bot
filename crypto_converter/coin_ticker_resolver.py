# crypto_converter/coin_ticker_resolver.py

# Standard Libraries
from dataclasses import dataclass
from threading import Lock
from typing import Final, Optional

# Custom Modules
from config import CRYPTO_MAX_MARKET_CAP_RANK
from crypto_converter.coingecko_client import (
    CoinGeckoSearchCoin,
    get_top_market_cap_coins,
    search_coins,
)


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


@dataclass(frozen=True)
class ResolvedCoinMatch:
    """Represent a resolved coin reference inside text."""

    coin: ResolvedCoin
    matched_text: str
    end: int


KNOWN_COINS: Final[dict[str, ResolvedCoin]] = {
    "BTC": ResolvedCoin("bitcoin", "BTC", "Bitcoin"),
    "ETH": ResolvedCoin("ethereum", "ETH", "Ethereum"),
    "BNB": ResolvedCoin("binancecoin", "BNB", "BNB"),
    "SOL": ResolvedCoin("solana", "SOL", "Solana"),
    "USD": ResolvedCoin("tether", "USDT", "Tether"),
    "USDT": ResolvedCoin("tether", "USDT", "Tether"),
    "UAH": ResolvedCoin("tether", "UAH", "Hryvnia"),
}
TICKER_CACHE: dict[str, ResolvedCoin] = {}
_COIN_REFERENCE_INDEX: Optional[dict[str, list[ResolvedCoin]]] = None
_MAX_COIN_REFERENCE_LENGTH = 0
_CATALOG_LOCK = Lock()


def _to_resolved_coin(coin: CoinGeckoSearchCoin) -> ResolvedCoin:
    return ResolvedCoin(
        coin_id=coin.coin_id,
        ticker=coin.symbol.upper(),
        name=coin.name,
    )


def _get_coin_reference_index() -> dict[str, list[ResolvedCoin]]:
    global _COIN_REFERENCE_INDEX
    global _MAX_COIN_REFERENCE_LENGTH

    if _COIN_REFERENCE_INDEX is not None:
        return _COIN_REFERENCE_INDEX

    with _CATALOG_LOCK:
        if _COIN_REFERENCE_INDEX is not None:
            return _COIN_REFERENCE_INDEX

        reference_index: dict[str, list[ResolvedCoin]] = {}
        catalog_coins = get_top_market_cap_coins(
            CRYPTO_MAX_MARKET_CAP_RANK
        )
        eligible_coin_ids = {
            catalog_coin.coin_id for catalog_coin in catalog_coins
        }

        for catalog_coin in catalog_coins:
            resolved_coin = _to_resolved_coin(catalog_coin)

            for reference in (catalog_coin.symbol, catalog_coin.name):
                normalized_reference = reference.strip().casefold()

                if not normalized_reference:
                    continue

                reference_coins = reference_index.setdefault(
                    normalized_reference,
                    [],
                )

                if all(
                    coin.coin_id != resolved_coin.coin_id
                    for coin in reference_coins
                ):
                    reference_coins.append(resolved_coin)

        for reference, known_coin in KNOWN_COINS.items():
            if (
                known_coin.ticker != "UAH"
                and known_coin.coin_id not in eligible_coin_ids
            ):
                continue

            reference_coins = reference_index.setdefault(
                reference.casefold(),
                [],
            )

            if all(
                coin.coin_id != known_coin.coin_id
                or coin.ticker != known_coin.ticker
                for coin in reference_coins
            ):
                reference_coins.append(known_coin)

        reference_index["hryvnia"] = [KNOWN_COINS["UAH"]]
        _MAX_COIN_REFERENCE_LENGTH = max(
            (len(reference) for reference in reference_index),
            default=0,
        )
        _COIN_REFERENCE_INDEX = reference_index
        return reference_index


def _select_ambiguous_coin(
    reference: str,
    candidates: list[ResolvedCoin],
) -> Optional[ResolvedCoin]:
    candidate_ids = {candidate.coin_id for candidate in candidates}

    matching_coins = [
        search_coin
        for search_coin in search_coins(reference)
        if search_coin.coin_id in candidate_ids
    ]

    if matching_coins:
        selected_coin = min(
            matching_coins,
            key=lambda coin: (
                coin.market_cap_rank is None,
                coin.market_cap_rank or 0,
            ),
        )
        return _to_resolved_coin(selected_coin)

    return None


def resolve_coin(ticker: str) -> Optional[ResolvedCoin]:
    """Resolve an exact ticker or coin name to canonical metadata."""
    normalized_reference = ticker.strip().casefold()
    normalized_ticker = ticker.strip().upper()

    if not normalized_ticker or normalized_ticker in BLOCKED_TICKERS:
        return None

    cached_coin = TICKER_CACHE.get(normalized_reference)

    if cached_coin is not None:
        return cached_coin

    reference_index = _get_coin_reference_index()
    candidates = reference_index.get(normalized_reference, [])

    if len(candidates) == 1:
        resolved_coin = candidates[0]
        TICKER_CACHE[normalized_reference] = resolved_coin
        return resolved_coin

    if len(candidates) > 1:
        resolved_coin = _select_ambiguous_coin(ticker, candidates)

        if resolved_coin is not None:
            TICKER_CACHE[normalized_reference] = resolved_coin

        return resolved_coin

    return None


def resolve_coin_reference_at(
    text: str,
    start: int,
) -> Optional[ResolvedCoinMatch]:
    """Resolve the longest exact coin reference beginning at an offset."""
    reference_index = _get_coin_reference_index()
    maximum_end = min(len(text), start + _MAX_COIN_REFERENCE_LENGTH)

    for end in range(maximum_end, start, -1):
        if end < len(text) and (text[end].isalnum() or text[end] == "_"):
            continue

        reference = text[start:end]
        normalized_reference = reference.casefold()

        if normalized_reference not in reference_index:
            continue

        resolved_coin = resolve_coin(reference)

        if resolved_coin is None:
            return None

        return ResolvedCoinMatch(
            coin=resolved_coin,
            matched_text=reference,
            end=end,
        )

    return None


def resolve_coin_ticker(ticker: str) -> Optional[str]:
    """Resolve a ticker to its highest-ranked exact CoinGecko match."""
    resolved_coin = resolve_coin(ticker)

    if resolved_coin is None:
        return None

    return resolved_coin.coin_id


if __name__ == "__main__":
    from crypto_converter.crypto_amount_parser import parse_crypto_amount_from_text
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
