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
from config import MAX_CRYPTO_PAIRS_PER_MESSAGE
from crypto_converter.crypto_amount_parser import (
    ParsedCryptoAmount,
    parse_crypto_amounts_from_text,
)
from crypto_converter.crypto_price_converter import (
    CryptoPriceConversion,
    convert_crypto_to_fiat,
)
from crypto_converter.usage_limiter import (
    CoinGeckoDailyRequestLimitExceeded,
    crypto_usage_limiter,
)
from telegram_bot.logging_config import (
    format_log_metadata,
    get_update_metadata,
    log_detected_crypto_conversion,
)


LOGGER = logging.getLogger(__name__)
LIMIT_REACHED_MESSAGE = "Наразі ліміт вичерпано."


def _format_decimal(value: Decimal) -> str:
    formatted_value = format(value, ".8f").rstrip("0").rstrip(".")

    return formatted_value or "0"


def _format_fiat_amount(value: Decimal) -> str:
    if value >= 1:
        return format(value, ",.2f").replace(",", " ")

    return _format_decimal(value)


def _format_crypto_conversion(conversion: CryptoPriceConversion) -> str:
    amount = _format_decimal(conversion.amount)
    total_usd = _format_fiat_amount(conversion.total_usd)
    total_uah = _format_fiat_amount(conversion.total_uah)

    return (
        f"{amount} {conversion.ticker}:\n"
        f"{total_usd} USD\n"
        f"{total_uah} UAH"
    )


def format_crypto_response(conversion: CryptoPriceConversion) -> str:
    """Format a cryptocurrency conversion for a Telegram reply."""
    return format_crypto_responses([conversion])


def format_crypto_responses(
    conversions: list[CryptoPriceConversion],
) -> str:
    """Format multiple cryptocurrency conversions in one Telegram reply."""
    formatted_conversions = (
        _format_crypto_conversion(conversion)
        for conversion in conversions
    )

    return "<code>" + "\n\n".join(formatted_conversions) + "</code>"


async def handle_crypto_message(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Reply with all supported crypto amounts found in a message."""
    message = update.effective_message

    if message is None:
        return

    message_text = message.text or message.caption

    if message_text is None:
        return

    parsed_crypto_amounts = parse_crypto_amounts_from_text(message_text)[
        :MAX_CRYPTO_PAIRS_PER_MESSAGE
    ]

    if not parsed_crypto_amounts:
        return

    converted_matches: list[
        tuple[ParsedCryptoAmount, CryptoPriceConversion]
    ] = []
    metadata = get_update_metadata(update)
    metadata_text = format_log_metadata(metadata)
    user_id = metadata["user_id"]
    chat_id = metadata["chat_id"]
    limit_reached = False

    if not isinstance(user_id, int):
        user_id = None

    if not isinstance(chat_id, int):
        chat_id = None

    for parsed_crypto_amount in parsed_crypto_amounts:
        if not crypto_usage_limiter.try_acquire_conversion_attempt(
            user_id=user_id,
            chat_id=chat_id,
        ):
            limit_reached = True
            LOGGER.warning(
                "Daily crypto conversion limit reached | %s",
                metadata_text,
            )
            break

        try:
            conversion = await asyncio.to_thread(
                convert_crypto_to_fiat,
                parsed_crypto_amount.amount,
                parsed_crypto_amount.ticker,
            )
        except CoinGeckoDailyRequestLimitExceeded:
            crypto_usage_limiter.release_conversion_attempt(
                user_id=user_id,
                chat_id=chat_id,
            )
            limit_reached = True
            LOGGER.warning(
                "Daily CoinGecko request limit reached | %s",
                metadata_text,
            )
            break
        except Exception:
            crypto_usage_limiter.release_conversion_attempt(
                user_id=user_id,
                chat_id=chat_id,
            )
            raise

        if conversion is not None:
            if not crypto_usage_limiter.try_complete_conversion(
                user_id=user_id,
                chat_id=chat_id,
            ):
                limit_reached = True
                LOGGER.warning(
                    "Daily crypto conversion limit reached | %s",
                    metadata_text,
                )
                break

            converted_matches.append((parsed_crypto_amount, conversion))

    if converted_matches:
        matched_texts = [
            parsed_crypto_amount.matched_text
            for parsed_crypto_amount, _conversion in converted_matches
        ]

        LOGGER.info(
            "Crypto amounts detected: %d | matches=%r | %s",
            len(converted_matches),
            matched_texts,
            metadata_text,
        )
        log_detected_crypto_conversion(
            {
                "chat_type": metadata["chat_type"],
                "matches": [
                    {
                        "matched_text": parsed_crypto_amount.matched_text,
                        "parsed_amount": str(parsed_crypto_amount.amount),
                        "parsed_ticker": parsed_crypto_amount.ticker,
                        "coin_id": conversion.coin_id,
                        "converted_amounts": {
                            "usd": str(conversion.total_usd),
                            "uah": str(conversion.total_uah),
                        },
                    }
                    for parsed_crypto_amount, conversion in converted_matches
                ],
            }
        )

        await message.reply_text(
            text=format_crypto_responses(
                [conversion for _parsed, conversion in converted_matches]
            ),
            parse_mode=ParseMode.HTML,
            do_quote=True,
        )

        LOGGER.info(
            "Crypto conversion reply sent: %d conversions | %s",
            len(converted_matches),
            metadata_text,
        )

    if limit_reached:
        await message.reply_text(
            text=LIMIT_REACHED_MESSAGE,
            do_quote=True,
        )
        LOGGER.info("Limit reached reply sent | %s", metadata_text)
