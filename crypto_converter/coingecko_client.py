# crypto_converter/coingecko_client.py

# Standard Libraries
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Final
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# Custom Modules
from config import COINGECKO_API_KEY


# CoinGecko Demo API
COINGECKO_SIMPLE_PRICE_URL: Final[str] = (
    "https://api.coingecko.com/api/v3/simple/price"
)
REQUEST_TIMEOUT_SECONDS: Final[int] = 10


@dataclass(frozen=True)
class CoinGeckoUnitPrice:
    """Represent the unit price of one coin in USD and UAH."""

    coin_id: str
    usd: Decimal
    uah: Decimal


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


def get_coin_unit_price(coin_id: str) -> CoinGeckoUnitPrice:
    """Fetch the unit price of a CoinGecko coin in USD and UAH."""
    normalized_coin_id = coin_id.strip().lower()

    if not normalized_coin_id:
        raise ValueError("coin_id must not be empty")

    query = urlencode(
        {
            "ids": normalized_coin_id,
            "vs_currencies": "usd,uah",
        }
    )
    request = Request(
        url=f"{COINGECKO_SIMPLE_PRICE_URL}?{query}",
        headers={
            "Accept": "application/json",
            "User-Agent": "cryptocodi-bot/1.0",
            "x-cg-demo-api-key": COINGECKO_API_KEY,
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            status_code = response.status
            response_body = response.read().decode("utf-8")
    except HTTPError as error:
        raise CoinGeckoAPIError(
            f"CoinGecko API request failed with HTTP {error.code}"
        ) from error
    except (TimeoutError, URLError) as error:
        raise CoinGeckoAPIError("CoinGecko API request failed") from error

    if status_code != 200:
        raise CoinGeckoAPIError(
            f"CoinGecko API request failed with HTTP {status_code}"
        )

    try:
        response_data = json.loads(response_body, parse_float=Decimal)
    except (json.JSONDecodeError, InvalidOperation) as error:
        raise CoinGeckoAPIError("CoinGecko returned invalid JSON") from error

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
    )
