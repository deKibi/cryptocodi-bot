# tests/crypto_converter/test_crypto_amount_parser.py

# Standard Libraries
from decimal import Decimal

# Third-party Libraries
import pytest

# Custom Modules
from crypto_converter import crypto_amount_parser
from crypto_converter.coin_ticker_resolver import (
    ResolvedCoin,
    ResolvedCoinMatch,
)
from crypto_converter.crypto_amount_parser import (
    parse_crypto_amount_from_text,
    resolve_crypto_amounts_from_text,
)


@pytest.mark.parametrize(
    ("text", "expected_amount", "expected_ticker", "expected_match"),
    [
        ("1 BTC", Decimal("1"), "BTC", "1 BTC"),
        ("0.5 BNB", Decimal("0.5"), "BNB", "0.5 BNB"),
        ("1k BTC", Decimal("1000"), "BTC", "1k BTC"),
        ("1kk BTC", Decimal("1000000"), "BTC", "1kk BTC"),
        ("2.5kk BNB", Decimal("2500000.0"), "BNB", "2.5kk BNB"),
        ("1m BNB", Decimal("1000000"), "BNB", "1m BNB"),
        ("1kk K", Decimal("1000000"), "K", "1kk K"),
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
        "1kkBTC",
    ],
)
def test_ignore_non_crypto_amounts(text: str) -> None:
    assert parse_crypto_amount_from_text(text) is None


@pytest.mark.parametrize(
    ("text", "expected_amount"),
    [
        ("1k k", Decimal("1000")),
        ("1kk k", Decimal("1000000")),
    ],
)
def test_resolve_single_letter_ticker_after_compact_multiplier(
    monkeypatch: pytest.MonkeyPatch,
    text: str,
    expected_amount: Decimal,
) -> None:
    coin = ResolvedCoin("sidekick", "K", "Sidekick")

    def resolve_k_reference(
        message_text: str,
        start: int,
    ) -> ResolvedCoinMatch | None:
        if not message_text[start:].casefold().startswith("k"):
            return None

        return ResolvedCoinMatch(
            coin=coin,
            matched_text=message_text[start:start + 1],
            end=start + 1,
        )

    monkeypatch.setattr(
        crypto_amount_parser,
        "resolve_coin_reference_at",
        resolve_k_reference,
    )

    resolved_amounts = resolve_crypto_amounts_from_text(text)

    assert len(resolved_amounts) == 1
    assert resolved_amounts[0].amount == expected_amount
    assert resolved_amounts[0].coin.ticker == "K"
