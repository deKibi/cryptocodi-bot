# crypto_calculator/crypto_calculator.py

# Standard Libraries
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Optional

# Custom Modules
from calculator.calculator import InvalidExpressionError, calculate
from calculator.expression_parser import (
    ALTERNATIVE_OPERATORS,
    parse_expression,
)


# Crypto calculations
CRYPTO_CALCULATION_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\s*(?P<expression>[\d\s.,kKmM()+\-*/×÷−xх]+)"
    r"\s+(?P<ticker>.+?)\s*"
)
EXPLICIT_OPERATOR_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"[+\-*/×÷−xх]"
)


class ZeroCryptoAmountError(InvalidExpressionError):
    """Indicate that a crypto calculation produced a zero amount."""


@dataclass(frozen=True)
class CalculatedCryptoExpression:
    """Represent a calculated arithmetic expression with a crypto ticker."""

    display_expression: str
    calculation_expression: str
    amount: Decimal
    ticker: str
    matched_text: str


def calculate_crypto_expression(
    message_text: str,
) -> Optional[CalculatedCryptoExpression]:
    """Calculate a full-message arithmetic expression ending in a ticker."""
    match = CRYPTO_CALCULATION_PATTERN.fullmatch(message_text)

    if match is None:
        return None

    raw_expression = match.group("expression").strip()
    raw_ticker = match.group("ticker").strip()

    if (
        EXPLICIT_OPERATOR_PATTERN.search(raw_expression) is None
        or not any(character.isalpha() for character in raw_ticker)
    ):
        return None

    calculation_expression = parse_expression(raw_expression)

    if calculation_expression is None:
        return None

    calculated_value = calculate(calculation_expression)
    amount = Decimal(str(calculated_value))

    if amount == 0:
        raise ZeroCryptoAmountError(
            "Crypto calculation produced a zero amount."
        )

    if amount < 0:
        raise InvalidExpressionError(
            "Crypto calculation must produce a positive amount."
        )

    return CalculatedCryptoExpression(
        display_expression=raw_expression.translate(ALTERNATIVE_OPERATORS),
        calculation_expression=calculation_expression,
        amount=amount,
        ticker=raw_ticker.upper(),
        matched_text=message_text.strip(),
    )
