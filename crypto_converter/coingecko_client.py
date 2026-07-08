# crypto_converter/coingecko_client.py

# Standard Libraries
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Final, Optional

# Third-party Libraries
import httpx

# Custom Modules
from config import COINGECKO_API_KEY
from crypto_converter.usage_limiter import crypto_usage_limiter


# CoinGecko Demo API
COINGECKO_SIMPLE_PRICE_URL: Final[str] = (
    "https://api.coingecko.com/api/v3/simple/price"
)
COINGECKO_SEARCH_URL: Final[str] = (
    "https://api.coingecko.com/api/v3/search"
)
COINGECKO_MARKETS_URL: Final[str] = (
    "https://api.coingecko.com/api/v3/coins/markets"
)
COINGECKO_COINS_LIST_URL: Final[str] = (
    "https://api.coingecko.com/api/v3/coins/list"
)
REQUEST_TIMEOUT_SECONDS: Final[int] = 10
COINGECKO_MARKETS_MAX_PAGE_SIZE: Final[int] = 250


@dataclass(frozen=True)
class CoinGeckoUnitPrice:
    """Represent one coin's prices in supported fiat currencies."""

    coin_id: str
    usd: Decimal
    uah: Decimal
    eur: Decimal
    cad: Decimal
    pln: Decimal
    usd_24h_change: Optional[Decimal] = None
    uah_24h_change: Optional[Decimal] = None
    eur_24h_change: Optional[Decimal] = None
    cad_24h_change: Optional[Decimal] = None
    pln_24h_change: Optional[Decimal] = None


@dataclass(frozen=True)
class CoinGeckoSearchCoin:
    """Represent a coin returned by CoinGecko search."""

    coin_id: str
    symbol: str
    name: str
    market_cap_rank: Optional[int] = None


class CoinGeckoAPIError(RuntimeError):
    """Indicate that CoinGecko prices could not be retrieved or parsed."""


def _parse_price(coin_data: dict[str, object], currency: str) -> Decimal:
    value = coin_data.get(currency)

    if value is None or isinstance(value, bool):
        raise CoinGeckoAPIError(
            f"CoinGecko response does not contain a valid {currency} price"
        )

    try:
        price = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise CoinGeckoAPIError(
            f"CoinGecko returned an invalid {currency} price"
        ) from error

    if not price.is_finite() or price < 0:
        raise CoinGeckoAPIError(
            f"CoinGecko returned an invalid {currency} price"
        )

    return price


def _parse_optional_percentage(
    coin_data: dict[str, object],
    field_name: str,
) -> Optional[Decimal]:
    value = coin_data.get(field_name)

    if value is None:
        return None

    if isinstance(value, bool):
        raise CoinGeckoAPIError(
            f"CoinGecko returned an invalid {field_name} value"
        )

    try:
        percentage = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise CoinGeckoAPIError(
            f"CoinGecko returned an invalid {field_name} value"
        ) from error

    if not percentage.is_finite():
        raise CoinGeckoAPIError(
            f"CoinGecko returned an invalid {field_name} value"
        )

    return percentage


def _get_response_data(
    url: str,
    params: dict[str, str],
) -> object:
    crypto_usage_limiter.acquire_coingecko_request()

    try:
        response = httpx.get(
            url=url,
            params=params,
            headers={
                "Accept": "application/json",
                "User-Agent": "cryptocodi-bot/1.0",
                "x-cg-demo-api-key": COINGECKO_API_KEY,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 401:
            raise CoinGeckoAPIError(
                "CoinGecko API authentication failed"
            ) from error

        raise CoinGeckoAPIError(
            "CoinGecko API request failed with HTTP "
            f"{error.response.status_code}"
        ) from error
    except httpx.RequestError as error:
        raise CoinGeckoAPIError("CoinGecko API request failed") from error

    try:
        return json.loads(response.text, parse_float=Decimal)
    except (json.JSONDecodeError, InvalidOperation) as error:
        raise CoinGeckoAPIError("CoinGecko returned invalid JSON") from error


def _parse_coins(coins_data: list[object]) -> list[CoinGeckoSearchCoin]:
    coins: list[CoinGeckoSearchCoin] = []

    for coin_data in coins_data:
        if not isinstance(coin_data, dict):
            continue

        coin_id = coin_data.get("id")
        symbol = coin_data.get("symbol")
        name = coin_data.get("name")
        market_cap_rank = coin_data.get("market_cap_rank")

        if not all(isinstance(value, str) for value in (coin_id, symbol, name)):
            continue

        if isinstance(market_cap_rank, bool) or not isinstance(
            market_cap_rank,
            (int, type(None)),
        ):
            market_cap_rank = None

        coins.append(
            CoinGeckoSearchCoin(
                coin_id=coin_id,
                symbol=symbol,
                name=name,
                market_cap_rank=market_cap_rank,
            )
        )

    return coins


def get_coin_catalog() -> list[CoinGeckoSearchCoin]:
    """Return all CoinGecko coin IDs, symbols, and names."""
    response_data = _get_response_data(
        url=COINGECKO_COINS_LIST_URL,
        params={"include_platform": "false"},
    )

    if not isinstance(response_data, list):
        raise CoinGeckoAPIError("CoinGecko returned an unexpected response")

    return _parse_coins(response_data)


def get_top_market_cap_coins(
    max_market_cap_rank: int,
) -> list[CoinGeckoSearchCoin]:
    """Return CoinGecko coins up to a maximum market cap rank."""
    if max_market_cap_rank <= 0:
        raise ValueError("max_market_cap_rank must be greater than zero")

    page_size = min(
        max_market_cap_rank,
        COINGECKO_MARKETS_MAX_PAGE_SIZE,
    )
    page_count = (max_market_cap_rank + page_size - 1) // page_size
    ranked_coins: list[CoinGeckoSearchCoin] = []

    for page in range(1, page_count + 1):
        response_data = _get_response_data(
            url=COINGECKO_MARKETS_URL,
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": str(page_size),
                "page": str(page),
                "sparkline": "false",
            },
        )

        if not isinstance(response_data, list):
            raise CoinGeckoAPIError(
                "CoinGecko returned an unexpected response"
            )

        ranked_coins.extend(
            coin
            for coin in _parse_coins(response_data)
            if coin.market_cap_rank is not None
            and coin.market_cap_rank <= max_market_cap_rank
        )

        if len(response_data) < page_size:
            break

    return ranked_coins


def get_coins_by_symbol(symbol: str) -> list[CoinGeckoSearchCoin]:
    """Return exact-symbol coins ordered by market capitalization."""
    normalized_symbol = symbol.strip().lower()

    if not normalized_symbol:
        raise ValueError("symbol must not be empty")

    response_data = _get_response_data(
        url=COINGECKO_MARKETS_URL,
        params={
            "vs_currency": "usd",
            "symbols": normalized_symbol,
            "include_tokens": "all",
            "order": "market_cap_desc",
            "per_page": "50",
            "page": "1",
            "sparkline": "false",
        },
    )

    if not isinstance(response_data, list):
        raise CoinGeckoAPIError("CoinGecko returned an unexpected response")

    return _parse_coins(response_data)


def search_coins(query: str) -> list[CoinGeckoSearchCoin]:
    """Search CoinGecko coins ordered by market capitalization."""
    normalized_query = query.strip()

    if not normalized_query:
        raise ValueError("query must not be empty")

    response_data = _get_response_data(
        url=COINGECKO_SEARCH_URL,
        params={"query": normalized_query},
    )

    if not isinstance(response_data, dict):
        raise CoinGeckoAPIError("CoinGecko returned an unexpected response")

    coins_data = response_data.get("coins")

    if not isinstance(coins_data, list):
        raise CoinGeckoAPIError(
            "CoinGecko response does not contain a valid coins list"
        )

    return _parse_coins(coins_data)


def get_coin_unit_price(coin_id: str) -> CoinGeckoUnitPrice:
    """Fetch a CoinGecko coin's prices in supported fiat currencies."""
    normalized_coin_id = coin_id.strip().lower()

    if not normalized_coin_id:
        raise ValueError("coin_id must not be empty")

    response_data = _get_response_data(
        url=COINGECKO_SIMPLE_PRICE_URL,
        params={
            "ids": normalized_coin_id,
            "vs_currencies": "usd,uah,eur,cad,pln",
            "include_24hr_change": "true",
        },
    )

    if not isinstance(response_data, dict):
        raise CoinGeckoAPIError("CoinGecko returned an unexpected response")

    coin_data = response_data.get(normalized_coin_id)

    if not isinstance(coin_data, dict):
        raise CoinGeckoAPIError(
            f"CoinGecko response does not contain {normalized_coin_id} prices"
        )

    return CoinGeckoUnitPrice(
        coin_id=normalized_coin_id,
        usd=_parse_price(coin_data, "usd"),
        uah=_parse_price(coin_data, "uah"),
        eur=_parse_price(coin_data, "eur"),
        cad=_parse_price(coin_data, "cad"),
        pln=_parse_price(coin_data, "pln"),
        usd_24h_change=_parse_optional_percentage(
            coin_data,
            "usd_24h_change",
        ),
        uah_24h_change=_parse_optional_percentage(
            coin_data,
            "uah_24h_change",
        ),
        eur_24h_change=_parse_optional_percentage(
            coin_data,
            "eur_24h_change",
        ),
        cad_24h_change=_parse_optional_percentage(
            coin_data,
            "cad_24h_change",
        ),
        pln_24h_change=_parse_optional_percentage(
            coin_data,
            "pln_24h_change",
        ),
    )
