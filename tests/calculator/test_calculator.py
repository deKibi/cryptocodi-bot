# tests/calculator/test_calculator.py

# Third-party Libraries
import pytest

# Custom Modules
from calculator.calculator import calculate
from calculator.expression_parser import parse_expression


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2+2", 4),
        ("10 - 3", 7),
        ("5*4", 20),
        ("20 / 4", 5),
        ("2*(3+4)", 14),
        ("2х5", 10),
        ("2×5", 10),
    ],
)
def test_calculate_real_user_expressions(
    text: str,
    expected: int | float,
) -> None:
    expression = parse_expression(text)

    assert expression is not None
    assert calculate(expression) == expected


@pytest.mark.parametrize(
    "text",
    [
        "28",
        "+28",
        "+100",
        "-50",
        "сьогодні заробив +28",
        "профіт +100",
        "ціна 20-30 доларів",
        "2*20cat",
        "привіт 2+2",
    ],
)
def test_ignore_non_calculator_messages(text: str) -> None:
    assert parse_expression(text) is None
