# telegram_bot/handlers/time_message_handler.py

# Standard Libraries
import logging
from datetime import datetime

# Third-party Libraries
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Custom Modules
from time_converter.time_utils import (
    convert_utc_to_central_europe,
    convert_utc_to_kyiv,
)
from time_converter.utc_time_parser import parse_utc_time_from_text
from telegram_bot.localization.messages import get_message
from telegram_bot.state.message_reply_tracker import (
    get_related_reply_message_id,
    remember_related_reply_message_id,
)
from telegram_bot.state.message_signature_tracker import (
    forget_message_signature,
    is_message_signature_unchanged,
    remember_message_signature,
)
from telegram_bot.logging_config import (
    format_log_metadata,
    get_update_metadata,
    log_detected_time_conversion,
)


LOGGER = logging.getLogger(__name__)
TIME_MESSAGE_FEATURE = "utc_time"


def format_time_response(utc_datetime: datetime) -> str:
    """Format UTC, Kyiv, and Central Europe times for a Telegram reply."""
    kyiv_datetime = convert_utc_to_kyiv(utc_datetime)
    central_europe_datetime = convert_utc_to_central_europe(utc_datetime)
    first_line_prefix = (
        f"{utc_datetime:%H:%M} UTC ({utc_datetime:%H:%M}) UTC "
    )
    continuation_indent = " " * len(first_line_prefix)

    return get_message(
        "time_response",
        first_line_prefix=first_line_prefix,
        continuation_indent=continuation_indent,
        kyiv_time=f"{kyiv_datetime:%H:%M}",
        central_europe_time=f"{central_europe_datetime:%H:%M}",
        utc_time=f"{utc_datetime:%H:%M}",
    )


async def handle_time_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Reply with converted times when a text message contains UTC time."""
    message = update.effective_message

    if message is None:
        return

    message_text = message.text or message.caption

    if message_text is None:
        return

    utc_datetime = parse_utc_time_from_text(message_text)
    chat = update.effective_chat

    if chat is None:
        return

    if utc_datetime is None:
        forget_message_signature(
            context.bot_data,
            TIME_MESSAGE_FEATURE,
            chat.id,
            message.message_id,
        )
        return

    time_signature = (utc_datetime.hour, utc_datetime.minute)

    if is_message_signature_unchanged(
        context.bot_data,
        TIME_MESSAGE_FEATURE,
        chat.id,
        message.message_id,
        time_signature,
    ):
        return

    metadata = get_update_metadata(update)
    metadata_text = format_log_metadata(metadata)
    kyiv_datetime = convert_utc_to_kyiv(utc_datetime)
    central_europe_datetime = convert_utc_to_central_europe(utc_datetime)

    LOGGER.info(
        "UTC time detected: %s | %s",
        f"{utc_datetime:%H:%M}",
        metadata_text,
    )
    log_detected_time_conversion(
        {
            "chat_type": metadata["chat_type"],
            "parsed_utc_datetime": utc_datetime.isoformat(),
            "converted_times": {
                "kyiv": f"{kyiv_datetime:%H:%M}",
                "central_europe": f"{central_europe_datetime:%H:%M}",
                "utc": f"{utc_datetime:%H:%M}",
            },
        }
    )

    response_text = format_time_response(utc_datetime)
    related_reply_message_id = get_related_reply_message_id(
        context.bot_data,
        TIME_MESSAGE_FEATURE,
        chat.id,
        message.message_id,
    )

    if related_reply_message_id is None:
        reply_message = await message.reply_text(
            text=response_text,
            parse_mode=ParseMode.HTML,
            do_quote=True,
        )
        remember_related_reply_message_id(
            context.bot_data,
            TIME_MESSAGE_FEATURE,
            chat.id,
            message.message_id,
            reply_message.message_id,
        )
        LOGGER.info(
            "Time conversion reply sent: %s KYIV, %s CET, %s UTC | %s",
            f"{kyiv_datetime:%H:%M}",
            f"{central_europe_datetime:%H:%M}",
            f"{utc_datetime:%H:%M}",
            metadata_text,
        )
    else:
        await context.bot.edit_message_text(
            chat_id=chat.id,
            message_id=related_reply_message_id,
            text=response_text,
            parse_mode=ParseMode.HTML,
        )
        LOGGER.info(
            "Time conversion reply updated: %s KYIV, %s CET, %s UTC | %s",
            f"{kyiv_datetime:%H:%M}",
            f"{central_europe_datetime:%H:%M}",
            f"{utc_datetime:%H:%M}",
            metadata_text,
        )

    remember_message_signature(
        context.bot_data,
        TIME_MESSAGE_FEATURE,
        chat.id,
        message.message_id,
        time_signature,
    )
