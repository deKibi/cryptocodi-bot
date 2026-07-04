# telegram_bot/keyboards/crypto_conversion_keyboard.py

# Standard Libraries
from typing import Final
from urllib.parse import quote

# Third-party Libraries
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Custom Modules
from crypto_converter.crypto_price_converter import CryptoPriceConversion


# Coin chart links
COINGECKO_COIN_URL_TEMPLATE: Final[str] = (
    "https://www.coingecko.com/en/coins/{coin_id}"
)


def build_crypto_conversion_keyboard(
    conversions: list[CryptoPriceConversion],
) -> InlineKeyboardMarkup:
    """Build unique CoinGecko chart buttons in conversion order."""
    keyboard: list[list[InlineKeyboardButton]] = []
    added_tickers: set[str] = set()

    for conversion in conversions:
        if conversion.ticker in added_tickers:
            continue

        added_tickers.add(conversion.ticker)
        coin_id = quote(conversion.coin_id.strip(), safe="")
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"📈 Графік {conversion.ticker}",
                    url=COINGECKO_COIN_URL_TEMPLATE.format(coin_id=coin_id),
                )
            ]
        )

    return InlineKeyboardMarkup(keyboard)
