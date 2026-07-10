# tests/calculator/test_expression_parser.py

# Third-party Libraries
import pytest

# Custom Modules
from calculator.expression_parser import parse_expression


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2+2", "2+2"),
        ("10 - 3", "10 - 3"),
        ("2х5", "2*5"),
        ("2×5", "2*5"),
    ],
)
def test_parse_valid_expressions(text: str, expected: str) -> None:
    assert parse_expression(text) == expected


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
