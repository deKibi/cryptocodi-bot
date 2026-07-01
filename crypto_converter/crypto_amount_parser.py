# crypto_converter/crypto_amount_parser.py

# Standard Libraries
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Optional


# Crypto amount pattern
THOUSAND_MULTIPLIER: Final[Decimal] = Decimal("1000")
CRYPTO_AMOUNT_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?<![\w.,:-])(?P<amount>\d+(?:[.,]\d+)?)"
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
        match.group("amount").replace(",", ".")
    )

    if match.group("multiplier") is not None:
        normalized_amount *= THOUSAND_MULTIPLIER

    return ParsedCryptoAmount(
        amount=normalized_amount,
        ticker=match.group("ticker").upper(),
        matched_text=match.group(0),
    )


def parse_crypto_amount_from_text(
    text: str,
) -> Optional[ParsedCryptoAmount]:
    """Return the first potential cryptocurrency amount found in text."""
    match = CRYPTO_AMOUNT_PATTERN.search(text)

    if match is None:
        return None

    return _parse_crypto_amount_match(match)


def parse_crypto_amounts_from_text(text: str) -> list[ParsedCryptoAmount]:
    """Return all potential cryptocurrency amounts found in text."""
    return [
        _parse_crypto_amount_match(match)
        for match in CRYPTO_AMOUNT_PATTERN.finditer(text)
    ]


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
