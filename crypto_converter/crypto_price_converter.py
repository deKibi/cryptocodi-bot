# crypto_converter/crypto_price_converter.py

# Standard Libraries
from dataclasses import dataclass
from decimal import Decimal
from typing import Final

# Custom Modules
from crypto_converter.coingecko_client import get_coin_unit_price


# Supported coins
SUPPORTED_COINS: Final[dict[str, str]] = {
    "BNB": "binancecoin",
}


@dataclass(frozen=True)
class CryptoPriceConversion:
    """Represent a cryptocurrency amount converted to USD and UAH."""

    amount: Decimal
    ticker: str
    coin_id: str
    unit_price_usd: Decimal
    unit_price_uah: Decimal
    total_usd: Decimal
    total_uah: Decimal


def convert_crypto_to_fiat(
    amount: Decimal,
    ticker: str,
) -> CryptoPriceConversion:
    """Convert a supported cryptocurrency amount to USD and UAH."""
    if amount <= 0:
        raise ValueError("amount must be greater than zero")

    normalized_ticker = ticker.strip().upper()
    coin_id = SUPPORTED_COINS.get(normalized_ticker)

    if coin_id is None:
        raise ValueError(f"Unsupported cryptocurrency ticker: {ticker}")

    unit_price = get_coin_unit_price(coin_id)

    return CryptoPriceConversion(
        amount=amount,
        ticker=normalized_ticker,
        coin_id=coin_id,
        unit_price_usd=unit_price.usd,
        unit_price_uah=unit_price.uah,
        total_usd=amount * unit_price.usd,
        total_uah=amount * unit_price.uah,
    )


if __name__ == "__main__":
    conversion = convert_crypto_to_fiat(
        amount=Decimal("1"),
        ticker="bnb",
    )

    print("Input:", conversion.amount, conversion.ticker)
    print("CoinGecko ID:", conversion.coin_id)
    print("Unit price USD:", conversion.unit_price_usd)
    print("Unit price UAH:", conversion.unit_price_uah)
    print("Total USD:", conversion.total_usd)
    print("Total UAH:", conversion.total_uah)
