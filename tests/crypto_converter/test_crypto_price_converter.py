# tests/crypto_converter/test_crypto_price_converter.py

# Standard Libraries
from decimal import Decimal

# Third-party Libraries
import pytest

# Custom Modules
from crypto_converter.coingecko_client import CoinGeckoUnitPrice
from crypto_converter.coin_ticker_resolver import ResolvedCoin
from crypto_converter.crypto_price_converter import (
    convert_fiat_to_resolved_crypto,
    convert_resolved_coin_to_fiat,
)


def test_convert_resolved_coin_to_fiat_uses_unit_prices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get_coin_unit_price(coin_id: str) -> CoinGeckoUnitPrice:
        assert coin_id == "bitcoin"
        return CoinGeckoUnitPrice(
            coin_id="bitcoin",
            usd=Decimal("100"),
            uah=Decimal("4000"),
            eur=Decimal("90"),
            cad=Decimal("140"),
            pln=Decimal("390"),
            rub=Decimal("9000"),
            usd_24h_change=Decimal("1.5"),
        )

    monkeypatch.setattr(
        "crypto_converter.crypto_price_converter.get_coin_unit_price",
        fake_get_coin_unit_price,
    )

    conversion = convert_resolved_coin_to_fiat(
        amount=Decimal("2"),
        resolved_coin=ResolvedCoin("bitcoin", "BTC", "Bitcoin"),
    )

    assert conversion.amount == Decimal("2")
    assert conversion.ticker == "BTC"
    assert conversion.coin_id == "bitcoin"
    assert conversion.coin_name == "Bitcoin"
    assert conversion.unit_price_usd == Decimal("100")
    assert conversion.unit_price_uah == Decimal("4000")
    assert conversion.total_usd == Decimal("200")
    assert conversion.total_uah == Decimal("8000")
    assert conversion.usd_24h_change == Decimal("1.5")


def test_convert_resolved_coin_rejects_non_positive_amount() -> None:
    with pytest.raises(ValueError):
        convert_resolved_coin_to_fiat(
            amount=Decimal("0"),
            resolved_coin=ResolvedCoin("bitcoin", "BTC", "Bitcoin"),
        )


def test_convert_fiat_to_resolved_crypto_uses_unit_price(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get_coin_unit_price(coin_id: str) -> CoinGeckoUnitPrice:
        assert coin_id == "binancecoin"
        return CoinGeckoUnitPrice(
            coin_id="binancecoin",
            usd=Decimal("500"),
            uah=Decimal("20000"),
            eur=Decimal("450"),
            cad=Decimal("700"),
            pln=Decimal("1950"),
            rub=Decimal("45000"),
        )

    monkeypatch.setattr(
        "crypto_converter.crypto_price_converter.get_coin_unit_price",
        fake_get_coin_unit_price,
    )

    conversion = convert_fiat_to_resolved_crypto(
        usd_amount=Decimal("10"),
        resolved_coin=ResolvedCoin("binancecoin", "BNB", "BNB"),
    )

    assert conversion is not None
    assert conversion.usd_amount == Decimal("10")
    assert conversion.crypto_conversion.amount == Decimal("0.02")
    assert conversion.crypto_conversion.ticker == "BNB"
    assert conversion.crypto_conversion.total_usd == Decimal("10")
    assert conversion.crypto_conversion.total_uah == Decimal("400.00")


def test_convert_fiat_to_resolved_crypto_ignores_fiat_target() -> None:
    conversion = convert_fiat_to_resolved_crypto(
        usd_amount=Decimal("10"),
        resolved_coin=ResolvedCoin("tether", "UAH", "Hryvnia"),
    )

    assert conversion is None


def test_convert_fiat_to_resolved_crypto_rejects_non_positive_amount() -> None:
    with pytest.raises(ValueError):
        convert_fiat_to_resolved_crypto(
            usd_amount=Decimal("0"),
            resolved_coin=ResolvedCoin("binancecoin", "BNB", "BNB"),
        )
