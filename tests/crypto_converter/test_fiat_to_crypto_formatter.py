# tests/crypto_converter/test_fiat_to_crypto_formatter.py

# Standard Libraries
from decimal import Decimal

# Third-party Libraries
import pytest

# Custom Modules
from crypto_converter.crypto_price_converter import (
    CryptoPriceConversion,
    FiatToCryptoConversion,
)
from telegram_bot.handlers.crypto_message_handler import (
    format_fiat_to_crypto_response,
)
from telegram_bot.localization.messages import get_message


def _build_fiat_to_crypto_conversion(
    usd_amount: Decimal,
    crypto_amount: Decimal,
    ticker: str,
    unit_price_usd: Decimal,
) -> FiatToCryptoConversion:
    return FiatToCryptoConversion(
        usd_amount=usd_amount,
        crypto_conversion=CryptoPriceConversion(
            amount=crypto_amount,
            ticker=ticker,
            coin_id=ticker.lower(),
            unit_price_usd=unit_price_usd,
            unit_price_uah=unit_price_usd * Decimal("40"),
            total_usd=usd_amount,
            total_uah=usd_amount * Decimal("40"),
            coin_name=ticker,
        ),
    )


@pytest.mark.parametrize(
    ("unit_price_usd", "crypto_amount", "expected_amount"),
    [
        (Decimal("500"), Decimal("0.02"), "0.02"),
        (Decimal("3000"), Decimal("0.0033333333"), "0.00333"),
        (Decimal("0.05"), Decimal("200"), "200"),
        (Decimal("0.05"), Decimal("2"), "2"),
    ],
)
def test_format_fiat_to_crypto_response_uses_readable_precision(
    unit_price_usd: Decimal,
    crypto_amount: Decimal,
    expected_amount: str,
) -> None:
    conversion = _build_fiat_to_crypto_conversion(
        usd_amount=Decimal("10"),
        crypto_amount=crypto_amount,
        ticker="BNB",
        unit_price_usd=unit_price_usd,
    )

    response_text = format_fiat_to_crypto_response(conversion, language="en")
    approximation_note = get_message(
        "fiat_to_crypto_approximation_note",
        language="en",
    )

    assert "<code>10$ BNB:</code>" in response_text
    assert f"<code>≈{expected_amount} BNB</code>" in response_text
    assert f"<i>{approximation_note}</i>" in response_text
    assert f"<code>{approximation_note}</code>" not in response_text


def test_format_fiat_to_crypto_response_preserves_nonzero_amount() -> None:
    conversion = _build_fiat_to_crypto_conversion(
        usd_amount=Decimal("0.1"),
        crypto_amount=Decimal("0.000000001"),
        ticker="BTC",
        unit_price_usd=Decimal("100000000"),
    )

    response_text = format_fiat_to_crypto_response(conversion, language="en")

    assert "<code>0.1$ BTC:</code>" in response_text
    assert "<code>≈0.000000001 BTC</code>" in response_text
    assert "<code>≈0 BTC</code>" not in response_text
