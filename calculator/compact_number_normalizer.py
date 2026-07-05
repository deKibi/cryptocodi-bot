# calculator/compact_number_normalizer.py

# Standard Libraries
import re
from typing import Final


# Number normalization
NON_ZERO_GROUPED_INTEGER_REGEX: Final[str] = (
    r"(?:[1-9]\d{0,2}|0[1-9]\d?|00[1-9])"
)
GROUPED_NUMBER_REGEX: Final[str] = (
    rf"{NON_ZERO_GROUPED_INTEGER_REGEX}(?:,\d{{3}})+(?:\.\d+)?"
)
PLAIN_NUMBER_REGEX: Final[str] = r"\d+(?:[.,]\d+)?"
NUMBER_LITERAL_REGEX: Final[str] = (
    rf"(?:{GROUPED_NUMBER_REGEX}|{PLAIN_NUMBER_REGEX})"
)
GROUPED_NUMBER_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"(?<![\w.,])(?P<number>{GROUPED_NUMBER_REGEX})"
    r"(?=[kK]\b|[^\w.,]|$)"
)
DECIMAL_COMMA_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?<![\w.,])(?P<integer>\d+),(?P<fraction>\d+)"
    r"(?=[kK]\b|[^\w.,]|$)"
)
COMPACT_NUMBER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?<![\w.])(?P<number>\d+(?:\.\d+)?)[kK]\b"
)


def normalize_number_separators(expression: str) -> str:
    """Normalize grouped thousands and decimal commas in numeric literals."""
    normalized_expression = GROUPED_NUMBER_PATTERN.sub(
        lambda match: match.group("number").replace(",", ""),
        expression,
    )
    return DECIMAL_COMMA_PATTERN.sub(
        lambda match: (
            f"{match.group('integer')}.{match.group('fraction')}"
        ),
        normalized_expression,
    )


def expand_compact_numbers(expression: str) -> str:
    """Expand compact number suffixes such as 2.5k into multiplication."""
    return COMPACT_NUMBER_PATTERN.sub(
        lambda match: f"({match.group('number')}*1000)",
        expression,
    )
