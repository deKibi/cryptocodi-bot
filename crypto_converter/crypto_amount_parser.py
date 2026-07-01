# crypto_converter/crypto_amount_parser.py

# Standard Libraries
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Optional


# Supported tickers
SUPPORTED_TICKERS: Final[tuple[str, ...]] = (
    "BTC",
    "ETH",
    "BNB",
    "SOL",
    "USDT",
)
TICKER_PATTERN: Final[str] = "|".join(
    re.escape(ticker) for ticker in SUPPORTED_TICKERS
)
CRYPTO_AMOUNT_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"(?<![\w.,-])(?P<amount>\d+(?:[.,]\d+)?)"
    rf"\s*(?P<ticker>{TICKER_PATTERN})(?!\w)",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedCryptoAmount:
    """Represent a cryptocurrency amount parsed from text."""

    amount: Decimal
    ticker: str
    matched_text: str


def parse_crypto_amount_from_text(
    text: str,
) -> Optional[ParsedCryptoAmount]:
    """Return the first supported cryptocurrency amount found in text."""
    match = CRYPTO_AMOUNT_PATTERN.search(text)

    if match is None:
        return None

    normalized_amount = match.group("amount").replace(",", ".")

    return ParsedCryptoAmount(
        amount=Decimal(normalized_amount),
        ticker=match.group("ticker").upper(),
        matched_text=match.group(0),
    )


if __name__ == "__main__":
    input_text = input("Enter text: ")
    parsed_crypto_amount = parse_crypto_amount_from_text(input_text)

    if parsed_crypto_amount is None:
        print("Crypto amount not found.")
    else:
        print("Amount:", parsed_crypto_amount.amount)
        print("Ticker:", parsed_crypto_amount.ticker)
        print("Matched text:", parsed_crypto_amount.matched_text)
