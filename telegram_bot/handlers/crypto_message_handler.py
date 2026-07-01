# telegram_bot/handlers/crypto_message_handler.py

# Standard Libraries
import asyncio
import logging
from decimal import Decimal

# Third-party Libraries
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Custom Modules
from crypto_converter.crypto_amount_parser import (
    parse_crypto_amount_from_text,
)
from crypto_converter.crypto_price_converter import (
    CryptoPriceConversion,
    convert_crypto_to_fiat,
)
from telegram_bot.logging_config import (
    format_log_metadata,
    get_update_metadata,
    log_detected_crypto_message,
)


LOGGER = logging.getLogger(__name__)


def _format_decimal(value: Decimal) -> str:
    formatted_value = format(value, ".8f").rstrip("0").rstrip(".")

    return formatted_value or "0"


def format_crypto_response(conversion: CryptoPriceConversion) -> str:
    """Format a cryptocurrency conversion for a Telegram reply."""
    amount = _format_decimal(conversion.amount)
    total_usd = _format_decimal(conversion.total_usd)
    total_uah = _format_decimal(conversion.total_uah)

    return (
        "<code>"
        f"{amount} {conversion.ticker}\n"
        f"{total_usd} USD\n"
        f"{total_uah} UAH"
        "</code>"
    )


async def handle_crypto_message(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Reply when a text message contains a supported crypto amount."""
    message = update.effective_message

    if message is None:
        return

    message_text = message.text or message.caption

    if message_text is None:
        return

    parsed_crypto_amount = parse_crypto_amount_from_text(message_text)

    if parsed_crypto_amount is None:
        return

    conversion = await asyncio.to_thread(
        convert_crypto_to_fiat,
        parsed_crypto_amount.amount,
        parsed_crypto_amount.ticker,
    )

    if conversion is None:
        return

    metadata = get_update_metadata(update)
    metadata_text = format_log_metadata(metadata)
    total_usd = _format_decimal(conversion.total_usd)
    total_uah = _format_decimal(conversion.total_uah)

    LOGGER.info(
        "Crypto amount detected: %s | %s",
        parsed_crypto_amount.matched_text,
        metadata_text,
    )
    log_detected_crypto_message(
        {
            **metadata,
            "message_id": message.message_id,
            "message_text": message_text,
            "matched_text": parsed_crypto_amount.matched_text,
            "parsed_amount": str(parsed_crypto_amount.amount),
            "parsed_ticker": parsed_crypto_amount.ticker,
            "coin_id": conversion.coin_id,
            "converted_amounts": {
                "usd": str(conversion.total_usd),
                "uah": str(conversion.total_uah),
            },
        }
    )

    await message.reply_text(
        text=format_crypto_response(conversion),
        parse_mode=ParseMode.HTML,
        do_quote=True,
    )

    LOGGER.info(
        "Crypto conversion reply sent: %s USD, %s UAH | %s",
        total_usd,
        total_uah,
        metadata_text,
    )
