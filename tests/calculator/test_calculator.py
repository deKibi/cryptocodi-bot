# tests/calculator/test_calculator.py

# Third-party Libraries
import pytest

# Custom Modules
from calculator.calculator import DivisionByZeroError, calculate


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


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("1/2", 0.5),
        ("10/4", 2.5),
    ],
)
def test_calculate_division_with_remainder(
    expression: str,
    expected: float,
) -> None:
    assert calculate(expression) == expected


def test_calculate_repeating_division_result() -> None:
    assert calculate("1/3") == pytest.approx(1 / 3)


def test_calculate_division_by_zero_raises_error() -> None:
    with pytest.raises(DivisionByZeroError):
        calculate("1/0")
