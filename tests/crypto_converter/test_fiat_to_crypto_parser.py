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
        ("10$ в BNB", Decimal("10"), "BNB"),
        ("10.5$ в bnb", Decimal("10.5"), "BNB"),
        ("10,5$ в BNB", Decimal("10.5"), "BNB"),
        ("10$ в $BNB", Decimal("10"), "BNB"),
        ("10$ В bNb", Decimal("10"), "BNB"),
        ("10$ в USDT", Decimal("10"), "USDT"),
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
        "порахуй 10$ в BNB",
        "10$ в BNB будь ласка",
        "10 $ в BNB",
        "10$ BNB",
        "10 usd в BNB",
        "10$ в USD",
        "0$ в BNB",
        "-10$ в BNB",
        "10$ в",
    ],
)
def test_ignore_invalid_fiat_to_crypto_conversion(text: str) -> None:
    assert parse_fiat_to_crypto_conversion(text) is None
