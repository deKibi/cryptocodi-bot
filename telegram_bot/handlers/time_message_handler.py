# telegram_bot/handlers/time_message_handler.py

# Standard Libraries
import logging
from datetime import datetime

# Third-party Libraries
from telegram import Update
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

# Custom Modules
from time_converter.time_utils import convert_to_timezone
from time_converter.utc_time_parser import ParsedTime, parse_times_from_text
from telegram_bot.localization.language_preferences import (
    DEFAULT_LANGUAGE,
    resolve_context_language,
)
from telegram_bot.localization.messages import get_message
from telegram_bot.state.message_reply_tracker import (
    forget_related_reply_message_id,
    get_related_reply_message_id,
    remember_related_reply_message_id,
)
from telegram_bot.settings.group_settings import get_effective_chat_settings
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


def _format_utc_offset(source_datetime: datetime) -> str:
    offset = source_datetime.utcoffset()

    if offset is None:
        return "UTC+00:00"

    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    absolute_minutes = abs(total_minutes)
    hours, minutes = divmod(absolute_minutes, 60)

    return f"UTC{sign}{hours:02d}:{minutes:02d}"


def _format_timezone_description(
    timezone_label: str,
    language: str,
) -> str:
    if (
        timezone_label.startswith("UTC+")
        or timezone_label.startswith("UTC-")
    ):
        return timezone_label

    return get_message(
        f"timezone_description_{timezone_label.lower()}",
        language=language,
    )


def _format_time_conversion_block(
    parsed_time: ParsedTime,
) -> str:
    """Format one parsed time conversion block."""
    source_datetime = parsed_time.source_datetime
    source_timezone = parsed_time.timezone_label
    display_timezone = (
        parsed_time.display_timezone_label or source_timezone
    )
    first_line_prefix = (
        f"{source_datetime:%H:%M} {display_timezone} "
        f"({source_datetime:%H:%M}) {source_timezone} "
    )
    continuation_indent = " " * len(first_line_prefix)
    lines: list[str] = []

    for index, timezone_label in enumerate(TIMEZONE_LABELS):
        if index == 0:
            line_prefix = first_line_prefix
            branch = "┬─>"
        elif index == len(TIMEZONE_LABELS) - 1:
            line_prefix = continuation_indent
            branch = "└─>"
        else:
            line_prefix = continuation_indent
            branch = "├─>"

        converted_time = convert_to_timezone(source_datetime, timezone_label)
        lines.append(
            f"{line_prefix}{branch} {converted_time:%H:%M} {timezone_label}"
        )

    return "\n".join(lines)


def _get_source_timezone_data(
    parsed_times: list[ParsedTime],
) -> dict[str, tuple[str, datetime]]:
    source_timezone_data: dict[str, tuple[str, datetime]] = {}

    for parsed_time in parsed_times:
        source_timezone_data.setdefault(
            parsed_time.timezone_label,
            (
                parsed_time.display_timezone_label
                or parsed_time.timezone_label,
                parsed_time.source_datetime,
            ),
        )

    return source_timezone_data


def _format_timezone_descriptions(
    parsed_times: list[ParsedTime],
    language: str,
) -> str:
    description_lines: list[str] = []

    for timezone_label, (display_timezone_label, source_datetime) in (
        _get_source_timezone_data(parsed_times).items()
    ):
        description_lines.append(
            get_message(
                "timezone_description_line",
                language=language,
                timezone=display_timezone_label,
                description=_format_timezone_description(
                    timezone_label,
                    language,
                ),
                utc_offset=_format_utc_offset(source_datetime),
            )
        )

    return "\n".join(description_lines)


def format_time_response(
    parsed_times: list[ParsedTime],
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Format parsed time conversions for a Telegram reply."""
    conversion_blocks = "\n\n".join(
        _format_time_conversion_block(parsed_time)
        for parsed_time in parsed_times
    )
    timezone_descriptions = _format_timezone_descriptions(
        parsed_times,
        language,
    )

    return get_message(
        "time_response",
        language=language,
        conversion_blocks=conversion_blocks,
        timezone_descriptions=timezone_descriptions,
    )


async def _cleanup_tracked_time_response(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    source_message_id: int,
) -> None:
    related_reply_message_id = get_related_reply_message_id(
        context.bot_data,
        TIME_MESSAGE_FEATURE,
        chat_id,
        source_message_id,
    )

    if related_reply_message_id is not None:
        try:
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=related_reply_message_id,
            )
        except TelegramError as error:
            LOGGER.warning(
                "Stale time response deletion failed: %s | "
                "chat_id=%s, source_message_id=%s",
                error,
                chat_id,
                source_message_id,
            )

    forget_related_reply_message_id(
        context.bot_data,
        TIME_MESSAGE_FEATURE,
        chat_id,
        source_message_id,
    )
    forget_message_signature(
        context.bot_data,
        TIME_MESSAGE_FEATURE,
        chat_id,
        source_message_id,
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

    chat = update.effective_chat

    if chat is None:
        return

    settings = get_effective_chat_settings(chat.id, chat.type)

    if not settings.time_converter_enabled:
        await _cleanup_tracked_time_response(
            context,
            chat.id,
            message.message_id,
        )
        return

    parsed_times = parse_times_from_text(
        message_text,
        limit=settings.max_time_matches_per_message,
    )

    if not parsed_times:
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
    time_signature = (
        tuple(
            (
                parsed_time.source_datetime.hour,
                parsed_time.source_datetime.minute,
                parsed_time.timezone_label,
                (
                    parsed_time.display_timezone_label
                    or parsed_time.timezone_label
                ),
            )
            for parsed_time in parsed_times
        ),
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
    parsed_time_logs = []

    for parsed_time in parsed_times:
        source_datetime = parsed_time.source_datetime
        converted_datetimes = {
            timezone_label.lower(): convert_to_timezone(
                source_datetime,
                timezone_label,
            )
            for timezone_label in TIMEZONE_LABELS
        }
        converted_times = {
            timezone_label: f"{converted_datetime:%H:%M}"
            for timezone_label, converted_datetime
            in converted_datetimes.items()
        }
        parsed_time_logs.append(
            {
                "source_timezone": parsed_time.timezone_label,
                "parsed_datetime": source_datetime.isoformat(),
                "converted_times": converted_times,
            }
        )

    LOGGER.info(
        "%d time conversion match(es) detected | %s",
        len(parsed_times),
        metadata_text,
    )
    log_detected_time_conversion(
        {
            "chat_type": metadata["chat_type"],
            "parsed_times": parsed_time_logs,
        }
    )

    response_text = format_time_response(parsed_times, language)
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
            "Time conversion reply sent: %d match(es) | %s",
            len(parsed_times),
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
            "Time conversion reply updated: %d match(es) | %s",
            len(parsed_times),
            metadata_text,
        )

    remember_message_signature(
        context.bot_data,
        TIME_MESSAGE_FEATURE,
        chat.id,
        message.message_id,
        time_signature,
    )
