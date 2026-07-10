# tests/calculator/test_formatter.py

# Third-party Libraries
import pytest

# Custom Modules
from calculator.calculator import calculate
from calculator.expression_parser import parse_expression
from telegram_bot.handlers.calculator_message_handler import (
    _format_calculation_result,
    format_calculation_response,
)


@pytest.mark.parametrize(
    ("result", "expected_result"),
    [
        (1.0, "1"),
        (0.3333333333333333, "0.33333"),
        (0.5, "0.5"),
        (-0.5, "-0.5"),
        (-0.0, "0"),
        (-0.000001, "0"),
        (1.99999, "1.99999"),
        (1.999999, "1.99999"),
    ],
)
def test_format_calculation_result(
    result: int | float,
    expected_result: str,
) -> None:
    assert _format_calculation_result(result) == expected_result


@pytest.mark.parametrize(
    ("expression", "result", "expected_result"),
    [
        ("1 / 1", 1.0, "1"),
        ("4 / 2", 2.0, "2"),
        ("5 / 2", 2.5, "2.5"),
        ("1 / 3", 0.3333333333333333, "0.33333"),
        ("2 / 3", 0.6666666666666666, "0.66666"),
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


@pytest.mark.parametrize(
    ("text", "expected_result"),
    [
        ("1/1", "1"),
        ("1/2", "0.5"),
        ("1/3", "0.33333"),
        ("2/3", "0.66666"),
        ("10/4", "2.5"),
        ("199999 / 100000", "1.99999"),
    ],
)
def test_calculator_returns_formatted_result(
    text: str,
    expected_result: str,
) -> None:
    expression = parse_expression(text)

    assert expression is not None

    result = calculate(expression)
    response = format_calculation_response(text, result)

    assert f"<code>{expected_result}</code>" in response
