# calculator/expression_parser.py

# Standard Libraries
import ast
import re
from typing import Final, Optional

# Custom Modules
from calculator.compact_number_normalizer import (
    COMPACT_NUMBER_PATTERN,
    expand_compact_numbers,
    normalize_number_separators,
)


# Expression parsing
ALTERNATIVE_OPERATORS: Final[dict[int, str]] = str.maketrans({
    "×": "*",
    "x": "*",
    "х": "*",
    "÷": "/",
    "−": "-",
})
EXPRESSION_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"[\d\s.kKmM()+\-*/]+"
)
SUPPORTED_AST_NODES: Final[tuple[type[ast.AST], ...]] = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.UAdd,
    ast.USub,
)


def _has_supported_syntax(
    expression: str,
    require_binary_operation: bool = False,
) -> bool:
    try:
        expression_tree = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError):
        return False

    has_binary_operation = False

    for node in ast.walk(expression_tree):
        if not isinstance(node, SUPPORTED_AST_NODES):
            return False

        if isinstance(node, ast.Constant) and type(node.value) not in (int, float):
            return False

        if isinstance(node, ast.BinOp):
            has_binary_operation = True

    return has_binary_operation or not require_binary_operation


def _remove_compact_number_suffixes(expression: str) -> str:
    return COMPACT_NUMBER_PATTERN.sub(
        lambda match: match.group("number"),
        expression,
    )


def parse_expression(message_text: str) -> Optional[str]:
    """Return a normalized arithmetic expression or None for other text."""
    if not isinstance(message_text, str):
        return None

    prepared_expression = normalize_number_separators(
        message_text.strip().translate(ALTERNATIVE_OPERATORS)
    )
    validation_expression = _remove_compact_number_suffixes(
        prepared_expression
    )

    if not _has_supported_syntax(
        validation_expression,
        require_binary_operation=True,
    ):
        return None

    normalized_expression = expand_compact_numbers(prepared_expression)

    if not normalized_expression:
        return None

    if EXPRESSION_PATTERN.fullmatch(normalized_expression) is None:
        return None

    if not _has_supported_syntax(normalized_expression):
        return None

    return normalized_expression


if __name__ == "__main__":
    if __package__:
        from calculator.calculator import CalculatorError, calculate
    else:
        from calculator import CalculatorError, calculate

    # test_cases = (
    #     ("3*2", "3*2"),
    #     (" 3 * 2 ", "3 * 2"),
    #     ("(10 + 5) / 3", "(10 + 5) / 3"),
    #     ("3 × 2", "3 * 2"),
    #     ("3x2", "3*2"),
    #     ("3х2", "3*2"),
    #     ("12 ÷ 4", "12 / 4"),
    #     ("5 − 3", "5 - 3"),
    #     ("порахуй 3*2", None),
    #     ("3*2 будь ласка", None),
    #     ("результат 10 + 5", None),
    #     ("hello", None),
    #     ("", None),
    #     ("3 +", None),
    #     ("10 // 2", None),
    # )

    # for test_text, expected_expression in test_cases:
    #     parsed_expression = parse_expression(test_text)
    #     status = "PASS" if parsed_expression == expected_expression else "FAIL"
    #     print(
    #         f"{status}: {test_text!r} -> {parsed_expression!r} "
    #         f"(expected {expected_expression!r})"
    #     )

    while True:
        input_text = input("Enter expression (enter q to exit): ")

        if input_text.strip().lower() in ("q", "quit", "exit", "leave"):
            print("Goodbye!")
            break

        parsed_expression = parse_expression(input_text)

        if parsed_expression is None:
            print("Expression not found.\n")
            continue

        try:
            result = calculate(parsed_expression)
        except CalculatorError as error:
            print(f"Calculation error: {error}\n")
            continue

        print(f"Result: {result}\n")
