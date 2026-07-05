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
DELETE_CRYPTO_RESPONSE_CALLBACK: Final[str] = "delete_response"


def build_crypto_conversion_keyboard(
    conversions: list[CryptoPriceConversion],
) -> InlineKeyboardMarkup:
    """Build unique CoinGecko chart buttons in conversion order."""
    keyboard: list[list[InlineKeyboardButton]] = []
    added_coin_ids: set[str] = set()

    for conversion in conversions:
        if (
            conversion.ticker == "UAH"
            or conversion.coin_id in added_coin_ids
        ):
            continue

        added_coin_ids.add(conversion.coin_id)
        coin_id = quote(conversion.coin_id.strip(), safe="")
        coin_name = conversion.coin_name.strip() or conversion.ticker
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"📈 Графік {coin_name}",
                    url=COINGECKO_COIN_URL_TEMPLATE.format(coin_id=coin_id),
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="Delete",
                callback_data=DELETE_CRYPTO_RESPONSE_CALLBACK,
            )
        ]
    )

    return InlineKeyboardMarkup(keyboard)
