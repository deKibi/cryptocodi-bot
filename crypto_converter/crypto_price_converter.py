# crypto_converter/crypto_price_converter.py

# Standard Libraries
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Optional

# Custom Modules
from crypto_converter.coin_ticker_resolver import (
    FIAT_TICKERS,
    ResolvedCoin,
    resolve_coin,
)
from crypto_converter.coingecko_client import (
    CoinGeckoAPIError,
    get_coin_unit_price,
)


# Fiat conversion
PERCENT_BASE: Final[Decimal] = Decimal("100")


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
    usd_24h_change: Optional[Decimal] = None
    coin_name: str = ""


def _calculate_cross_rate_24h_change(
    usd_24h_change: Optional[Decimal],
    source_24h_change: Optional[Decimal],
) -> Optional[Decimal]:
    if usd_24h_change is None or source_24h_change is None:
        return None

    source_change_multiplier = (
        Decimal("1") + source_24h_change / PERCENT_BASE
    )
    usd_change_multiplier = Decimal("1") + usd_24h_change / PERCENT_BASE

    if source_change_multiplier <= 0 or usd_change_multiplier <= 0:
        return None

    return (
        usd_change_multiplier / source_change_multiplier - Decimal("1")
    ) * PERCENT_BASE


def _convert_fiat_currency(
    amount: Decimal,
    resolved_coin: ResolvedCoin,
) -> CryptoPriceConversion:
    tether_unit_price = get_coin_unit_price("tether")
    source_prices = {
        "UAH": tether_unit_price.uah,
        "EUR": tether_unit_price.eur,
        "CAD": tether_unit_price.cad,
        "PLN": tether_unit_price.pln,
        "RUB": tether_unit_price.rub,
    }
    source_24h_changes = {
        "UAH": tether_unit_price.uah_24h_change,
        "EUR": tether_unit_price.eur_24h_change,
        "CAD": tether_unit_price.cad_24h_change,
        "PLN": tether_unit_price.pln_24h_change,
        "RUB": tether_unit_price.rub_24h_change,
    }
    source_price = source_prices[resolved_coin.ticker]

    if source_price == 0:
        raise CoinGeckoAPIError(
            f"CoinGecko returned a zero {resolved_coin.ticker} price"
        )

    unit_price_usd = tether_unit_price.usd / source_price
    unit_price_uah = tether_unit_price.uah / source_price

    return CryptoPriceConversion(
        amount=amount,
        ticker=resolved_coin.ticker,
        coin_id="tether",
        unit_price_usd=unit_price_usd,
        unit_price_uah=unit_price_uah,
        total_usd=amount * unit_price_usd,
        total_uah=amount * unit_price_uah,
        usd_24h_change=_calculate_cross_rate_24h_change(
            tether_unit_price.usd_24h_change,
            source_24h_changes[resolved_coin.ticker],
        ),
        coin_name=resolved_coin.name,
    )


def convert_crypto_to_fiat(
    amount: Decimal,
    ticker: str,
) -> Optional[CryptoPriceConversion]:
    """Convert a resolved cryptocurrency amount to USD and UAH."""
    if amount <= 0:
        raise ValueError("amount must be greater than zero")

    resolved_coin = resolve_coin(ticker)

    if resolved_coin is None:
        return None

    return convert_resolved_coin_to_fiat(amount, resolved_coin)


def convert_resolved_coin_to_fiat(
    amount: Decimal,
    resolved_coin: ResolvedCoin,
) -> CryptoPriceConversion:
    """Convert an amount using already resolved canonical coin metadata."""
    if amount <= 0:
        raise ValueError("amount must be greater than zero")

    if resolved_coin.ticker in FIAT_TICKERS:
        return _convert_fiat_currency(amount, resolved_coin)

    unit_price = get_coin_unit_price(resolved_coin.coin_id)

    return CryptoPriceConversion(
        amount=amount,
        ticker=resolved_coin.ticker,
        coin_id=resolved_coin.coin_id,
        unit_price_usd=unit_price.usd,
        unit_price_uah=unit_price.uah,
        total_usd=amount * unit_price.usd,
        total_uah=amount * unit_price.uah,
        usd_24h_change=unit_price.usd_24h_change,
        coin_name=resolved_coin.name,
    )


if __name__ == "__main__":
    conversion = convert_crypto_to_fiat(
        amount=Decimal("1"),
        ticker="bnb",
    )

    if conversion is None:
        print("Coin not found.")
    else:
        print("Input:", conversion.amount, conversion.ticker)
        print("CoinGecko ID:", conversion.coin_id)
        print("Unit price USD:", conversion.unit_price_usd)
        print("Unit price UAH:", conversion.unit_price_uah)
        print("Total USD:", conversion.total_usd)
        print("Total UAH:", conversion.total_uah)
