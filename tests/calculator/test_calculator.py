# tests/calculator/test_calculator.py

# Third-party Libraries
import pytest

# Custom Modules
from calculator.calculator import calculate


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("2+2", 4),
        ("10 - 3", 7),
        ("5*4", 20),
        ("20 / 4", 5),
        ("2*(3+4)", 14),
    ],
)
def test_calculate_valid_expressions(
    expression: str,
    expected: int | float,
) -> None:
    assert calculate(expression) == expected
