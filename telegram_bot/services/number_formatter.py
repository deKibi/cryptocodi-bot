# telegram_bot/services/number_formatter.py

# Standard Libraries
from decimal import Decimal, InvalidOperation
from typing import Final


# Number formatting
LARGE_NUMBER_GROUPING_THRESHOLD: Final[Decimal] = Decimal("10000")


def format_large_number(value: str) -> str:
    """Group the integer part of a large numeric string with spaces."""
    try:
        numeric_value = Decimal(value)
    except InvalidOperation:
        return value

    if (
        not numeric_value.is_finite()
        or abs(numeric_value) < LARGE_NUMBER_GROUPING_THRESHOLD
    ):
        return value

    plain_value = (
        format(numeric_value, "f")
        if "e" in value.lower()
        else value
    )
    sign = ""

    if plain_value.startswith(("+", "-")):
        sign = plain_value[0]
        plain_value = plain_value[1:]

    integer_part, separator, fractional_part = plain_value.partition(".")
    grouped_integer = format(int(integer_part), ",").replace(",", " ")

    if not separator:
        return f"{sign}{grouped_integer}"

    return f"{sign}{grouped_integer}.{fractional_part}"
