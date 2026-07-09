# telegram_bot/handlers/time_message_handler.py

# Standard Libraries
import logging

# Third-party Libraries
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Custom Modules
from time_converter.time_utils import (
    TIMEZONES_BY_LABEL,
    convert_to_timezone,
)
from time_converter.utc_time_parser import ParsedTime, parse_time_from_text
from telegram_bot.localization.language_preferences import (
    DEFAULT_LANGUAGE,
    resolve_context_language,
)
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
TIMEZONE_LABELS = ("KYIV", "CET", "UTC")


def format_time_response(
    parsed_time: ParsedTime,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Format a source time and the other supported timezones."""
    source_datetime = parsed_time.source_datetime
    source_timezone = parsed_time.timezone_label
    target_timezones = [
        timezone_label
        for timezone_label in TIMEZONE_LABELS
        if timezone_label != source_timezone
    ]
    first_line_prefix = (
        f"{source_datetime:%H:%M} {source_timezone} "
        f"({source_datetime:%H:%M}) {source_timezone} "
    )
    continuation_indent = " " * len(first_line_prefix)
    first_target_timezone, second_target_timezone = target_timezones
    first_target_time = convert_to_timezone(
        source_datetime,
        first_target_timezone,
    )
    second_target_time = convert_to_timezone(
        source_datetime,
        second_target_timezone,
    )

    return get_message(
        "time_response",
        language=language,
        first_line_prefix=first_line_prefix,
        continuation_indent=continuation_indent,
        first_time=f"{first_target_time:%H:%M}",
        first_timezone=first_target_timezone,
        second_time=f"{second_target_time:%H:%M}",
        second_timezone=second_target_timezone,
        source_timezone=source_timezone,
        source_timezone_description=get_message(
            f"timezone_description_{source_timezone.lower()}",
            language=language,
        ),
    )


async def handle_time_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Reply with converted times when a text message contains a timezone."""
    message = update.effective_message

    if message is None:
        return

    message_text = message.text or message.caption

    if message_text is None:
        return

    parsed_time = parse_time_from_text(message_text)
    chat = update.effective_chat

    if chat is None:
        return

    if parsed_time is None:
        forget_message_signature(
            context.bot_data,
            TIME_MESSAGE_FEATURE,
            chat.id,
            message.message_id,
        )
        return

    user = update.effective_user
    language = resolve_context_language(
        chat.id,
        chat.type,
        user.id if user is not None else None,
        user.language_code if user is not None else None,
    )
    source_datetime = parsed_time.source_datetime
    source_timezone = parsed_time.timezone_label
    time_signature = (
        source_datetime.hour,
        source_datetime.minute,
        source_timezone,
        language,
    )

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
    converted_datetimes = {
        timezone_label.lower(): convert_to_timezone(
            source_datetime,
            timezone_label,
        )
        for timezone_label in TIMEZONES_BY_LABEL
    }
    converted_times = {
        timezone_label: f"{converted_datetime:%H:%M}"
        for timezone_label, converted_datetime in converted_datetimes.items()
    }

    LOGGER.info(
        "%s time detected: %s | %s",
        source_timezone,
        f"{source_datetime:%H:%M}",
        metadata_text,
    )
    log_detected_time_conversion(
        {
            "chat_type": metadata["chat_type"],
            "source_timezone": source_timezone,
            "parsed_datetime": source_datetime.isoformat(),
            "converted_times": converted_times,
        }
    )

    response_text = format_time_response(parsed_time, language)
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
            f"{converted_datetimes['kyiv']:%H:%M}",
            f"{converted_datetimes['cet']:%H:%M}",
            f"{converted_datetimes['utc']:%H:%M}",
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
            f"{converted_datetimes['kyiv']:%H:%M}",
            f"{converted_datetimes['cet']:%H:%M}",
            f"{converted_datetimes['utc']:%H:%M}",
            metadata_text,
        )

    remember_message_signature(
        context.bot_data,
        TIME_MESSAGE_FEATURE,
        chat.id,
        message.message_id,
        time_signature,
    )
