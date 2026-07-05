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
MAX_COIN_NAME_BUTTON_LENGTH: Final[int] = 24


def _get_chart_button_label(conversion: CryptoPriceConversion) -> str:
    coin_name = conversion.coin_name.strip()

    if not coin_name or len(coin_name) > MAX_COIN_NAME_BUTTON_LENGTH:
        coin_name = conversion.ticker

    return f"📈 {coin_name}"


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
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=_get_chart_button_label(conversion),
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
