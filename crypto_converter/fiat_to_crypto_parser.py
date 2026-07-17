# crypto_converter/fiat_to_crypto_parser.py

# Standard Libraries
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Optional

# Custom Modules
from common.compact_number_normalizer import (
    COMPACT_NUMBER_MULTIPLIERS,
    COMPACT_NUMBER_SUFFIX_REGEX,
    NUMBER_LITERAL_REGEX,
    normalize_number_separators,
)


# Fiat to crypto conversion pattern
FIAT_TO_CRYPTO_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"\s*(?:"
    rf"(?P<prefix_dollar>\$(?P<prefix_amount>{NUMBER_LITERAL_REGEX})"
    rf"(?P<prefix_multiplier>{COMPACT_NUMBER_SUFFIX_REGEX})?)"
    rf"|"
    rf"(?P<suffix_amount>{NUMBER_LITERAL_REGEX})"
    rf"(?P<suffix_multiplier>{COMPACT_NUMBER_SUFFIX_REGEX})?\$"
    rf")"
    r"\s+\$?(?P<ticker>[A-Za-z]{1,20})\s*",
    flags=re.IGNORECASE,
)
BLOCKED_FIAT_TO_CRYPTO_TARGETS: Final[frozenset[str]] = frozenset({"USD"})
MIN_FIAT_TO_CRYPTO_USD_AMOUNT: Final[Decimal] = Decimal("0.1")


@dataclass(frozen=True)
class ParsedFiatToCryptoConversion:
    """Represent a strict full-message USD to crypto conversion request."""

    usd_amount: Decimal
    ticker: str
    matched_text: str


@dataclass(frozen=True)
class ParsedLowFiatToCryptoAmount:
    """Represent a strict USD to crypto request below the minimum amount."""

    usd_amount: Decimal
    ticker: str
    matched_text: str


def parse_fiat_to_crypto_conversion(
    message_text: str,
) -> Optional[ParsedFiatToCryptoConversion | ParsedLowFiatToCryptoAmount]:
    """Return a USD to crypto conversion request from a full message."""
    if not isinstance(message_text, str):
        return None

    match = FIAT_TO_CRYPTO_PATTERN.fullmatch(message_text)

    if match is None:
        return None

    matched_amount = (
        match.group("prefix_amount")
        or match.group("suffix_amount")
    )
    matched_multiplier = (
        match.group("prefix_multiplier")
        or match.group("suffix_multiplier")
    )
    usd_amount = Decimal(
        normalize_number_separators(matched_amount)
    )

    if matched_multiplier is not None:
        usd_amount *= COMPACT_NUMBER_MULTIPLIERS[
            matched_multiplier.lower()
        ]

    ticker = match.group("ticker").upper()

    if ticker in BLOCKED_FIAT_TO_CRYPTO_TARGETS:
        return None

    if usd_amount < MIN_FIAT_TO_CRYPTO_USD_AMOUNT:
        return ParsedLowFiatToCryptoAmount(
            usd_amount=usd_amount,
            ticker=ticker,
            matched_text=message_text.strip(),
        )

    return ParsedFiatToCryptoConversion(
        usd_amount=usd_amount,
        ticker=ticker,
        matched_text=message_text.strip(),
    )
