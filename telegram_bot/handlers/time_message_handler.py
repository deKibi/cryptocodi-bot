# telegram_bot/handlers/time_message_handler.py

# Standard Libraries
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


def format_time_response(utc_datetime: datetime) -> str:
    """Format UTC, Kyiv, and Central Europe times for a Telegram reply."""
    kyiv_datetime = convert_utc_to_kyiv(utc_datetime)
    central_europe_datetime = convert_utc_to_central_europe(utc_datetime)
    first_line_prefix = (
        f"{utc_datetime:%H:%M} UTC ({utc_datetime:%H:%M}) UTC "
    )
    continuation_indent = " " * len(first_line_prefix)

    return (
        "<pre>"
        f"{first_line_prefix}┬─> {kyiv_datetime:%H:%M} KIEV\n"
        f"{continuation_indent}├─> {central_europe_datetime:%H:%M} CET\n"
        f"{continuation_indent}└─> {utc_datetime:%H:%M} UTC\n\n"
        "UTC — UTC (UTC+00:00)"
        "</pre>"
    )


async def handle_time_message(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Reply with converted times when a text message contains UTC time."""
    message = update.effective_message

    if message is None or message.text is None:
        return

    utc_datetime = parse_utc_time_from_text(message.text)

    if utc_datetime is None:
        return

    await message.reply_text(
        text=format_time_response(utc_datetime),
        parse_mode=ParseMode.HTML,
        do_quote=True,
    )
