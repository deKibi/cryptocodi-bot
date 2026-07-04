# calculator/compact_number_normalizer.py

# Standard Libraries
import re
from typing import Final


# Compact numbers
COMPACT_NUMBER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?<![\w.])(?P<number>\d+(?:\.\d+)?)[kK]\b"
)


def expand_compact_numbers(expression: str) -> str:
    """Expand compact number suffixes such as 2.5k into multiplication."""
    return COMPACT_NUMBER_PATTERN.sub(
        lambda match: f"({match.group('number')}*1000)",
        expression,
    )
