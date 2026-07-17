# tests/crypto_calculator/test_crypto_calculator.py

# Standard Libraries
from decimal import Decimal

# Third-party Libraries
import pytest

# Custom Modules
from calculator.calculator import InvalidExpressionError
from crypto_calculator.crypto_calculator import (
    ZeroCryptoAmountError,
    calculate_crypto_expression,
)


@pytest.mark.parametrize(
    ("text", "expected_amount", "expected_ticker"),
    [
        ("2 * 2 BNB", Decimal("4"), "BNB"),
        ("2 * 2k BNB", Decimal("4000"), "BNB"),
        ("2 * 2kk BNB", Decimal("4000000"), "BNB"),
        ("2х2k BNB", Decimal("4000"), "BNB"),
    ],
)
def test_calculate_crypto_expression(
    text: str,
    expected_amount: Decimal,
    expected_ticker: str,
) -> None:
    calculated_expression = calculate_crypto_expression(text)

    assert calculated_expression is not None
    assert calculated_expression.amount == expected_amount
    assert calculated_expression.ticker == expected_ticker
    assert calculated_expression.matched_text == text


@pytest.mark.parametrize(
    "text",
    [
        "2 BNB",
        "сьогодні витратив 2*2 BNB",
        "2*20cad",
    ],
)
def test_ignore_non_crypto_calculator_messages(text: str) -> None:
    assert calculate_crypto_expression(text) is None


def test_zero_crypto_calculation_raises_error() -> None:
    with pytest.raises(ZeroCryptoAmountError):
        calculate_crypto_expression("1 - 1 BNB")


def test_negative_crypto_calculation_raises_error() -> None:
    with pytest.raises(InvalidExpressionError):
        calculate_crypto_expression("1 - 2 BNB")
