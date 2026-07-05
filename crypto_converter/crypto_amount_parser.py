# crypto_converter/crypto_amount_parser.py

# Standard Libraries
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Optional

# Custom Modules
from calculator.compact_number_normalizer import (
    NUMBER_LITERAL_REGEX,
    normalize_number_separators,
)


# Crypto amount pattern
THOUSAND_MULTIPLIER: Final[Decimal] = Decimal("1000")
CRYPTO_AMOUNT_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"(?<![\w.,:-])(?P<amount>{NUMBER_LITERAL_REGEX})"
    r"(?:(?P<multiplier>k)\s+|\s*)"
    r"(?:\$)?"
    r"(?P<ticker>(?:(?<=[\s$])[A-Za-z]|[A-Za-z]{2,10}))(?!\w)",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedCryptoAmount:
    """Represent a cryptocurrency amount parsed from text."""

    amount: Decimal
    ticker: str
    matched_text: str


def _parse_crypto_amount_match(
    match: re.Match[str],
) -> ParsedCryptoAmount:
    normalized_amount = Decimal(
        normalize_number_separators(match.group("amount"))
    )

    if match.group("multiplier") is not None:
        normalized_amount *= THOUSAND_MULTIPLIER

    return ParsedCryptoAmount(
        amount=normalized_amount,
        ticker=match.group("ticker").upper(),
        matched_text=match.group(0),
    )


def _find_crypto_amount_matches(text: str) -> list[re.Match[str]]:
    matches: list[re.Match[str]] = []

    for match in CRYPTO_AMOUNT_PATTERN.finditer(text):
        preceding_index = match.start() - 1

        while preceding_index >= 0 and text[preceding_index].isspace():
            preceding_index -= 1

        if preceding_index >= 0 and text[preceding_index] == "$":
            continue

        matches.append(match)

    return matches


def parse_crypto_amount_from_text(
    text: str,
) -> Optional[ParsedCryptoAmount]:
    """Return the first potential cryptocurrency amount found in text."""
    matches = _find_crypto_amount_matches(text)

    if not matches:
        return None

    return _parse_crypto_amount_match(matches[0])


def parse_crypto_amounts_from_text(text: str) -> list[ParsedCryptoAmount]:
    """Return all potential cryptocurrency amounts found in text."""
    return [
        _parse_crypto_amount_match(match)
        for match in _find_crypto_amount_matches(text)
    ]


def contains_only_crypto_amounts(text: str) -> bool:
    """Return whether text consists only of crypto amounts and separators."""
    matches = _find_crypto_amount_matches(text)

    if not matches:
        return False

    unmatched_parts: list[str] = []
    previous_match_end = 0

    for match in matches:
        unmatched_parts.append(text[previous_match_end:match.start()])
        previous_match_end = match.end()

    unmatched_parts.append(text[previous_match_end:])

    return all(
        character.isspace()
        or unicodedata.category(character).startswith("P")
        for part in unmatched_parts
        for character in part
    )


if __name__ == "__main__":
    while True:
        input_text = input("Enter text (enter q to exit): ")
        parsed_crypto_amount = parse_crypto_amount_from_text(input_text)

        if input_text in ["quit", "q", "exit", "leave"]:
            print("Goodbye!")
            break

        if parsed_crypto_amount is None:
            print("Crypto amount not found.")
        else:
            print("Amount:", parsed_crypto_amount.amount)
            print("Ticker:", parsed_crypto_amount.ticker)
            print(f"Matched text: {parsed_crypto_amount.matched_text}\n")
