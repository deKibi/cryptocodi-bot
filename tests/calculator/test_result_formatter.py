# tests/calculator/test_result_formatter.py

# Third-party Libraries
import pytest

# Custom Modules
from telegram_bot.handlers.calculator_message_handler import (
    format_calculation_response,
)


@pytest.mark.parametrize(
    ("expression", "result", "expected_result"),
    [
        ("1 / 1", 1.0, "1"),
        ("4 / 2", 2.0, "2"),
        ("5 / 2", 2.5, "2.5"),
        ("1 / 3", 0.3333333333333333, "0.3333"),
        ("2 / 3", 0.6666666666666666, "0.6667"),
        ("2.0 + 1.0", 3.0, "3"),
    ],
)
def test_format_calculation_response_result(
    expression: str,
    result: int | float,
    expected_result: str,
) -> None:
    response = format_calculation_response(expression, result)

    assert f"<code>{expected_result}</code>" in response
