# crypto_converter/crypto_amount_parser.py

# Standard Libraries
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Optional

# Custom Modules
from calculator.compact_number_normalizer import (
    COMPACT_NUMBER_MULTIPLIERS,
    COMPACT_NUMBER_SUFFIX_REGEX,
    NUMBER_LITERAL_REGEX,
    normalize_number_separators,
)
from crypto_converter.coin_ticker_resolver import (
    ResolvedCoin,
    resolve_coin_reference_at,
    resolve_top_ranked_coin_reference_at,
)


# Crypto amount pattern
CRYPTO_AMOUNT_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"(?<![\w.,:-])(?P<amount>{NUMBER_LITERAL_REGEX})"
    rf"(?P<multiplier>[{COMPACT_NUMBER_SUFFIX_REGEX}])?\s+"
    r"(?P<dollar>\$)?"
    r"(?P<ticker>(?:(?<=[\s$])[A-Za-z]|[A-Za-z]{2,10}))(?!\w)",
    flags=re.IGNORECASE,
)
CRYPTO_AMOUNT_PREFIX_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"(?<![\w.,:-])(?P<amount>{NUMBER_LITERAL_REGEX})"
    rf"(?P<multiplier>[{COMPACT_NUMBER_SUFFIX_REGEX}])?\s+",
    flags=re.IGNORECASE,
)
TIMEZONE_OFFSET_PREFIX_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?:UTC|GMT)\s*[+-]\s*$",
    flags=re.IGNORECASE,
)
TIMEZONE_OFFSET_SUFFIX_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"[+-]\d",
)


@dataclass(frozen=True)
class ParsedCryptoAmount:
    """Represent a cryptocurrency amount parsed from text."""

    amount: Decimal
    ticker: str
    matched_text: str


@dataclass(frozen=True)
class ResolvedCryptoAmount:
    """Represent a parsed amount with canonical coin metadata."""

    amount: Decimal
    coin: ResolvedCoin
    matched_text: str
    start: int
    end: int


def _parse_crypto_amount_match(
    match: re.Match[str],
) -> ParsedCryptoAmount:
    normalized_amount = Decimal(
        normalize_number_separators(match.group("amount"))
    )

    multiplier = match.group("multiplier")

    if multiplier is not None:
        normalized_amount *= COMPACT_NUMBER_MULTIPLIERS[multiplier.lower()]

    return ParsedCryptoAmount(
        amount=normalized_amount,
        ticker=match.group("ticker").upper(),
        matched_text=match.group(0),
    )


def _find_crypto_amount_matches(text: str) -> list[re.Match[str]]:
    matches: list[re.Match[str]] = []

    for match in CRYPTO_AMOUNT_PATTERN.finditer(text):
        if _follows_separated_digit(text, match.start()):
            continue

        if _follows_timezone_offset_prefix(text, match.start()):
            continue

        if _is_timezone_offset_match(text, match):
            continue

        preceding_index = match.start() - 1

        while preceding_index >= 0 and text[preceding_index].isspace():
            preceding_index -= 1

        if preceding_index >= 0 and text[preceding_index] == "$":
            continue

        ticker = match.group("ticker")

        if (
            len(ticker) == 1
            and match.group("dollar") is None
            and not ticker.isupper()
        ):
            continue

        matches.append(match)

    return matches


def _is_dollar_prefixed(text: str, start: int) -> bool:
    preceding_index = start - 1

    while preceding_index >= 0 and text[preceding_index].isspace():
        preceding_index -= 1

    return preceding_index >= 0 and text[preceding_index] == "$"


def _follows_separated_digit(text: str, start: int) -> bool:
    preceding_index = start - 1

    while preceding_index >= 0 and text[preceding_index].isspace():
        preceding_index -= 1

    return preceding_index >= 0 and text[preceding_index].isdigit()


def _follows_timezone_offset_prefix(text: str, start: int) -> bool:
    return TIMEZONE_OFFSET_PREFIX_PATTERN.search(text[:start]) is not None


def _is_timezone_offset_match(text: str, match: re.Match[str]) -> bool:
    return (
        match.group("ticker").upper() in {"UTC", "GMT"}
        and TIMEZONE_OFFSET_SUFFIX_PATTERN.match(text, match.end()) is not None
    )


def _parse_amount_value(match: re.Match[str]) -> Decimal:
    amount = Decimal(normalize_number_separators(match.group("amount")))

    multiplier = match.group("multiplier")

    if multiplier is not None:
        amount *= COMPACT_NUMBER_MULTIPLIERS[multiplier.lower()]

    return amount


def _is_single_letter_reference_allowed(
    reference: str,
    is_dollar_prefixed: bool,
    top_ranked_only: bool,
) -> bool:
    normalized_reference = reference.strip()
    return (
        len(normalized_reference) != 1
        or not top_ranked_only
        or is_dollar_prefixed
        or normalized_reference.isupper()
    )


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


def resolve_crypto_amounts_from_text(
    text: str,
    top_ranked_only: bool = False,
) -> list[ResolvedCryptoAmount]:
    """Resolve crypto amounts using exact ticker or full-name references."""
    resolved_amounts: list[ResolvedCryptoAmount] = []
    previous_match_end = 0
    coin_reference_resolver = (
        resolve_top_ranked_coin_reference_at
        if top_ranked_only
        else resolve_coin_reference_at
    )

    for amount_match in CRYPTO_AMOUNT_PREFIX_PATTERN.finditer(text):
        if (
            amount_match.start() < previous_match_end
            or _is_dollar_prefixed(text, amount_match.start())
            or _follows_separated_digit(text, amount_match.start())
            or _follows_timezone_offset_prefix(text, amount_match.start())
        ):
            continue

        reference_start = amount_match.end()
        reference_is_dollar_prefixed = (
            reference_start < len(text) and text[reference_start] == "$"
        )

        if reference_is_dollar_prefixed:
            reference_start += 1

        coin_match = coin_reference_resolver(text, reference_start)

        if (
            coin_match is None
            or not _is_single_letter_reference_allowed(
                coin_match.matched_text,
                reference_is_dollar_prefixed,
                top_ranked_only,
            )
        ):
            continue

        resolved_amounts.append(
            ResolvedCryptoAmount(
                amount=_parse_amount_value(amount_match),
                coin=coin_match.coin,
                matched_text=text[amount_match.start():coin_match.end],
                start=amount_match.start(),
                end=coin_match.end,
            )
        )
        previous_match_end = coin_match.end

    return resolved_amounts


def contains_only_resolved_crypto_amounts(
    text: str,
    resolved_amounts: list[ResolvedCryptoAmount],
) -> bool:
    """Return whether text contains only resolved amounts and separators."""
    if not resolved_amounts:
        return False

    unmatched_parts: list[str] = []
    previous_match_end = 0

    for resolved_amount in resolved_amounts:
        unmatched_parts.append(text[previous_match_end:resolved_amount.start])
        previous_match_end = resolved_amount.end

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
