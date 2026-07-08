# calculator/compact_number_normalizer.py

# Standard Libraries
import re
from typing import Final


# Number normalization
COMPACT_NUMBER_MULTIPLIERS: Final[dict[str, int]] = {
    "k": 1_000,
    "m": 1_000_000,
}
COMPACT_NUMBER_SUFFIX_REGEX: Final[str] = r"kKmM"
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
    rf"(?=[{COMPACT_NUMBER_SUFFIX_REGEX}]\b|[^\w.,]|$)"
)
DECIMAL_COMMA_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?<![\w.,])(?P<integer>\d+),(?P<fraction>\d+)"
    rf"(?=[{COMPACT_NUMBER_SUFFIX_REGEX}]\b|[^\w.,]|$)"
)
COMPACT_NUMBER_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"(?<![\w.])(?P<number>\d+(?:\.\d+)?)"
    rf"(?P<suffix>[{COMPACT_NUMBER_SUFFIX_REGEX}])\b"
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
    """Expand compact thousand and million suffixes into multiplication."""
    return COMPACT_NUMBER_PATTERN.sub(
        lambda match: (
            f"({match.group('number')}*"
            f"{COMPACT_NUMBER_MULTIPLIERS[match.group('suffix').lower()]})"
        ),
        expression,
    )
