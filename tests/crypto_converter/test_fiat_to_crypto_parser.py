# tests/crypto_converter/test_fiat_to_crypto_parser.py

# Standard Libraries
from decimal import Decimal

# Third-party Libraries
import pytest

# Custom Modules
from crypto_converter.fiat_to_crypto_parser import (
    parse_fiat_to_crypto_conversion,
)


@pytest.mark.parametrize(
    ("text", "expected_amount", "expected_ticker"),
    [
        ("10$ BNB", Decimal("10"), "BNB"),
        ("$10 BNB", Decimal("10"), "BNB"),
        ("10.5$ bnb", Decimal("10.5"), "BNB"),
        ("$10.5 $BNB", Decimal("10.5"), "BNB"),
        ("10,5$ BNB", Decimal("10.5"), "BNB"),
        ("1k$ BNB", Decimal("1000"), "BNB"),
        ("$1k BNB", Decimal("1000"), "BNB"),
        ("0.1k$ BNB", Decimal("100.0"), "BNB"),
        ("$0.1k BNB", Decimal("100.0"), "BNB"),
        ("1m$ ETH", Decimal("1000000"), "ETH"),
        ("$1m ETH", Decimal("1000000"), "ETH"),
        ("1kk$ BTC", Decimal("1000000"), "BTC"),
        ("$1kk BTC", Decimal("1000000"), "BTC"),
        ("10$ $BNB", Decimal("10"), "BNB"),
        ("10$ bNb", Decimal("10"), "BNB"),
        ("10$ USDT", Decimal("10"), "USDT"),
    ],
)
def test_parse_fiat_to_crypto_conversion(
    text: str,
    expected_amount: Decimal,
    expected_ticker: str,
) -> None:
    parsed_conversion = parse_fiat_to_crypto_conversion(text)

    assert parsed_conversion is not None
    assert parsed_conversion.usd_amount == expected_amount
    assert parsed_conversion.ticker == expected_ticker
    assert parsed_conversion.matched_text == text


@pytest.mark.parametrize(
    "text",
    [
        "10$ в BNB",
        "1k$ в BNB",
        "порахуй 10$ BNB",
        "10$ BNB будь ласка",
        "10 $ BNB",
        "$ 10 BNB",
        "1 k$ BNB",
        "$1 k BNB",
        "10$BNB",
        "$10BNB",
        "1k$BNB",
        "$1kBNB",
        "10 usd BNB",
        "10$ USD",
        "0$ в BNB",
        "0$ BNB",
        "-10$ BNB",
        "10$",
    ],
)
def test_ignore_invalid_fiat_to_crypto_conversion(text: str) -> None:
    assert parse_fiat_to_crypto_conversion(text) is None
