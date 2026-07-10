# tests/crypto_converter/test_crypto_amount_parser.py

# Standard Libraries
from decimal import Decimal

# Third-party Libraries
import pytest

# Custom Modules
from crypto_converter.crypto_amount_parser import parse_crypto_amount_from_text


@pytest.mark.parametrize(
    ("text", "expected_amount", "expected_ticker", "expected_match"),
    [
        ("1 BTC", Decimal("1"), "BTC", "1 BTC"),
        ("0.5 BNB", Decimal("0.5"), "BNB", "0.5 BNB"),
        ("1k BTC", Decimal("1000"), "BTC", "1k BTC"),
        ("1m BNB", Decimal("1000000"), "BNB", "1m BNB"),
        ("100 000 BNB", Decimal("100000"), "BNB", "100 000 BNB"),
    ],
)
def test_parse_crypto_amounts(
    text: str,
    expected_amount: Decimal,
    expected_ticker: str,
    expected_match: str,
) -> None:
    parsed_amount = parse_crypto_amount_from_text(text)

    assert parsed_amount is not None
    assert parsed_amount.amount == expected_amount
    assert parsed_amount.ticker == expected_ticker
    assert parsed_amount.matched_text == expected_match


@pytest.mark.parametrize(
    "text",
    [
        "20cad",
        "2*20cad",
        "$100 ETH",
        "10:00 GMT+3",
        "10 GMT+3",
        "10 UTC+3",
    ],
)
def test_ignore_non_crypto_amounts(text: str) -> None:
    assert parse_crypto_amount_from_text(text) is None
