# calculator/expression_parser.py

# Standard Libraries
import ast
import re
from typing import Final, Optional


# Expression parsing
ALTERNATIVE_OPERATORS: Final[dict[int, str]] = str.maketrans({
    "×": "*",
    "÷": "/",
    "−": "-",
})
EXPRESSION_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"[\d\s.()+\-*/]+"
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


def _has_supported_syntax(expression: str) -> bool:
    try:
        expression_tree = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError):
        return False

    for node in ast.walk(expression_tree):
        if not isinstance(node, SUPPORTED_AST_NODES):
            return False

        if isinstance(node, ast.Constant) and type(node.value) not in (int, float):
            return False

    return True


def parse_expression(message_text: str) -> Optional[str]:
    """Return a normalized arithmetic expression or None for other text."""
    if not isinstance(message_text, str):
        return None

    normalized_expression = message_text.strip().translate(
        ALTERNATIVE_OPERATORS
    )

    if not normalized_expression:
        return None

    if EXPRESSION_PATTERN.fullmatch(normalized_expression) is None:
        return None

    if not _has_supported_syntax(normalized_expression):
        return None

    return normalized_expression


if __name__ == "__main__":
    test_cases = (
        ("3*2", "3*2"),
        (" 3 * 2 ", "3 * 2"),
        ("(10 + 5) / 3", "(10 + 5) / 3"),
        ("3 × 2", "3 * 2"),
        ("12 ÷ 4", "12 / 4"),
        ("5 − 3", "5 - 3"),
        ("порахуй 3*2", None),
        ("3*2 будь ласка", None),
        ("результат 10 + 5", None),
        ("hello", None),
        ("", None),
        ("3 +", None),
        ("10 // 2", None),
    )

    for test_text, expected_expression in test_cases:
        parsed_expression = parse_expression(test_text)
        status = "PASS" if parsed_expression == expected_expression else "FAIL"
        print(
            f"{status}: {test_text!r} -> {parsed_expression!r} "
            f"(expected {expected_expression!r})"
        )
