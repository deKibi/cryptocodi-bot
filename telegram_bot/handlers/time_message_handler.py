# telegram_bot/handlers/time_message_handler.py

# Standard Libraries
from datetime import datetime

# Third-party Libraries
from telegram import Update
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

    return (
        f"{kyiv_datetime:%H:%M} KYIV\n"
        f"{central_europe_datetime:%H:%M} CET\n"
        f"{utc_datetime:%H:%M} UTC"
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
        do_quote=True,
    )
