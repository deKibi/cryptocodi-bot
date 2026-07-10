# tests/crypto_converter/test_crypto_conversion_flow.py

# Standard Libraries
from decimal import Decimal

# Custom Modules
from crypto_converter.crypto_amount_parser import parse_crypto_amounts_from_text


def test_parse_duplicate_crypto_amounts_before_handler_deduplication() -> None:
    parsed_amounts = parse_crypto_amounts_from_text("1 BTC, 1 BTC")

    assert [parsed_amount.amount for parsed_amount in parsed_amounts] == [
        Decimal("1"),
        Decimal("1"),
    ]
    assert [parsed_amount.ticker for parsed_amount in parsed_amounts] == [
        "BTC",
        "BTC",
    ]
    assert [parsed_amount.matched_text for parsed_amount in parsed_amounts] == [
        "1 BTC",
        "1 BTC",
    ]
