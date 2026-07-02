# calculator/calculator.py

# Standard Libraries
import ast
import math
import operator
from collections.abc import Callable
from typing import Final


# Calculation limits
MAX_EXPRESSION_LENGTH: Final[int] = 200
MAX_AST_NODES: Final[int] = 50
MAX_AST_DEPTH: Final[int] = 15
MAX_ABSOLUTE_VALUE: Final[int] = 10 ** 100
MAX_ABSOLUTE_EXPONENT: Final[int] = 100

BinaryOperator = Callable[[int | float, int | float], int | float]
UnaryOperator = Callable[[int | float], int | float]

ALLOWED_BINARY_OPERATORS: Final[dict[type[ast.operator], BinaryOperator]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}
ALLOWED_UNARY_OPERATORS: Final[dict[type[ast.unaryop], UnaryOperator]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class CalculatorError(ValueError):
    """Base exception for calculator errors."""


class InvalidExpressionError(CalculatorError):
    """Raised when an expression is empty or syntactically invalid."""


class UnsupportedOperationError(CalculatorError):
    """Raised when an expression contains unsupported syntax."""


class CalculationLimitError(CalculatorError):
    """Raised when an expression exceeds a calculator safety limit."""


class DivisionByZeroError(CalculatorError):
    """Raised when an expression attempts to divide by zero."""


def _ensure_value_is_safe(value: int | float) -> int | float:
    if isinstance(value, float) and not math.isfinite(value):
        raise CalculationLimitError("Calculation produced a non-finite number.")

    if abs(value) > MAX_ABSOLUTE_VALUE:
        raise CalculationLimitError(
            "Calculation result exceeds the allowed value limit."
        )

    return value


def _validate_power(base: int | float, exponent: int | float) -> None:
    if not isinstance(exponent, int):
        raise UnsupportedOperationError(
            "Only integer exponents are supported."
        )

    if abs(exponent) > MAX_ABSOLUTE_EXPONENT:
        raise CalculationLimitError(
            "Exponent exceeds the allowed limit."
        )

    if exponent <= 0 or abs(base) <= 1:
        return

    if exponent * math.log(abs(base)) > math.log(MAX_ABSOLUTE_VALUE):
        raise CalculationLimitError(
            "Calculation result exceeds the allowed value limit."
        )


def _evaluate_node(node: ast.AST, depth: int = 0) -> int | float:
    if depth > MAX_AST_DEPTH:
        raise CalculationLimitError("Expression is nested too deeply.")

    if isinstance(node, ast.Constant):
        if type(node.value) not in (int, float):
            raise UnsupportedOperationError(
                "Only integer and decimal numbers are supported."
            )

        return _ensure_value_is_safe(node.value)

    if isinstance(node, ast.UnaryOp):
        unary_operator = ALLOWED_UNARY_OPERATORS.get(type(node.op))

        if unary_operator is None:
            raise UnsupportedOperationError("Unary operator is not supported.")

        operand = _evaluate_node(node.operand, depth + 1)
        return _ensure_value_is_safe(unary_operator(operand))

    if isinstance(node, ast.BinOp):
        binary_operator = ALLOWED_BINARY_OPERATORS.get(type(node.op))

        if binary_operator is None:
            raise UnsupportedOperationError("Binary operator is not supported.")

        left = _evaluate_node(node.left, depth + 1)
        right = _evaluate_node(node.right, depth + 1)

        if isinstance(node.op, ast.Pow):
            _validate_power(left, right)

        try:
            result = binary_operator(left, right)
        except ZeroDivisionError as error:
            raise DivisionByZeroError("Division by zero is not allowed.") from error
        except OverflowError as error:
            raise CalculationLimitError(
                "Calculation exceeds the allowed numeric range."
            ) from error

        if type(result) not in (int, float):
            raise UnsupportedOperationError(
                "Calculation must produce a real number."
            )

        return _ensure_value_is_safe(result)

    raise UnsupportedOperationError(
        f"Unsupported expression element: {type(node).__name__}."
    )


def calculate(expression: str) -> int | float:
    """Safely calculate a prepared arithmetic expression."""
    if not isinstance(expression, str):
        raise InvalidExpressionError("Expression must be a string.")

    normalized_expression = expression.strip()

    if not normalized_expression:
        raise InvalidExpressionError("Expression must not be empty.")

    if len(normalized_expression) > MAX_EXPRESSION_LENGTH:
        raise CalculationLimitError("Expression is too long.")

    try:
        expression_tree = ast.parse(normalized_expression, mode="eval")
    except (SyntaxError, ValueError) as error:
        raise InvalidExpressionError(
            "Expression has invalid mathematical syntax."
        ) from error

    if sum(1 for _ in ast.walk(expression_tree)) > MAX_AST_NODES:
        raise CalculationLimitError("Expression contains too many operations.")

    return _evaluate_node(expression_tree.body)


if __name__ == "__main__":
    successful_cases = (
        ("3*2", 6),
        ("0.5 * 3", 1.5),
        ("10 + 5", 15),
        ("12 / 4", 3.0),
        ("2 ** 8", 256),
        ("(5 + 3) * 2", 16),
        ("(10 + 5) / 3", 5.0),
        ("-3 + 5", 2),
    )
    error_cases = (
        ("10 / 0", DivisionByZeroError),
        ("2 ** 101", CalculationLimitError),
        ("99999999999999999999 ** 10", CalculationLimitError),
        ("1 + " * 30 + "1", CalculationLimitError),
        ("__import__('os').system('echo unsafe')", UnsupportedOperationError),
        ("sin(30)", UnsupportedOperationError),
        ("sqrt(16)", UnsupportedOperationError),
        ("10 USD + 0.1 BTC", InvalidExpressionError),
        ("", InvalidExpressionError),
    )

    for test_expression, expected_result in successful_cases:
        actual_result = calculate(test_expression)
        status = "PASS" if actual_result == expected_result else "FAIL"
        print(
            f"{status}: {test_expression!r} -> {actual_result!r} "
            f"(expected {expected_result!r})"
        )

    for test_expression, expected_error in error_cases:
        try:
            calculate(test_expression)
        except expected_error as error:
            print(f"PASS: {test_expression!r} -> {type(error).__name__}: {error}")
        except CalculatorError as error:
            print(
                f"FAIL: {test_expression!r} -> {type(error).__name__}: {error} "
                f"(expected {expected_error.__name__})"
            )
        else:
            print(
                f"FAIL: {test_expression!r} did not raise "
                f"{expected_error.__name__}"
            )
