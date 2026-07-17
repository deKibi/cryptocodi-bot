# crypto_converter/fiat_to_crypto_parser.py

# Standard Libraries
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Optional

# Custom Modules
from common.compact_number_normalizer import (
    NUMBER_LITERAL_REGEX,
    normalize_number_separators,
)


# Fiat to crypto conversion pattern
FIAT_TO_CRYPTO_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"\s*(?:"
    rf"(?P<prefix_dollar>\$(?P<prefix_amount>{NUMBER_LITERAL_REGEX}))"
    rf"|"
    rf"(?P<suffix_amount>{NUMBER_LITERAL_REGEX})\$"
    rf")"
    r"\s+\$?(?P<ticker>[A-Za-z]{1,20})\s*",
    flags=re.IGNORECASE,
)
BLOCKED_FIAT_TO_CRYPTO_TARGETS: Final[frozenset[str]] = frozenset({"USD"})


@dataclass(frozen=True)
class ParsedFiatToCryptoConversion:
    """Represent a strict full-message USD to crypto conversion request."""

    usd_amount: Decimal
    ticker: str
    matched_text: str


def parse_fiat_to_crypto_conversion(
    message_text: str,
) -> Optional[ParsedFiatToCryptoConversion]:
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
    usd_amount = Decimal(
        normalize_number_separators(matched_amount)
    )

    if usd_amount <= 0:
        return None

    ticker = match.group("ticker").upper()

    if ticker in BLOCKED_FIAT_TO_CRYPTO_TARGETS:
        return None

    return ParsedFiatToCryptoConversion(
        usd_amount=usd_amount,
        ticker=ticker,
        matched_text=message_text.strip(),
    )
