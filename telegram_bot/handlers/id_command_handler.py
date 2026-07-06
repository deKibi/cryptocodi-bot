# telegram_bot/handlers/id_command_handler.py

# Standard Libraries
import logging
import re
from html import escape
from typing import Final, Optional

# Third-party Libraries
from telegram import Chat, Update, User
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Custom Modules
from telegram_bot.logging_config import (
    format_log_metadata,
    get_update_metadata,
)
from telegram_bot.services.account_creation_date import (
    estimate_account_creation_month,
)
from telegram_bot.state.message_reply_tracker import (
    get_related_reply_message_id,
    remember_related_reply_message_id,
)
from telegram_bot.state.message_signature_tracker import (
    is_message_signature_unchanged,
    remember_message_signature,
)


LOGGER = logging.getLogger(__name__)
ID_LOOKUP_FEATURE: Final[str] = "id_lookup"
MAX_TELEGRAM_USER_ID: Final[int] = (1 << 52) - 1
POSITIVE_USER_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"[1-9][0-9]*"
)
NEGATIVE_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"-[1-9][0-9]*"
)
INVALID_USER_ID_MESSAGE: Final[str] = (
    "Вкажіть один додатний цілий ID користувача Telegram."
)
GROUP_ID_MESSAGE: Final[str] = (
    "Це ID групи. Визначення приблизної дати створення наразі "
    "підтримується лише для користувачів."
)


def _parse_user_id_argument(
    arguments: list[str],
) -> tuple[str, Optional[int]]:
    if not arguments:
        return "empty", None

    if len(arguments) != 1:
        return "invalid", None

    raw_user_id = arguments[0]

    if NEGATIVE_ID_PATTERN.fullmatch(raw_user_id):
        return "group", None

    if not POSITIVE_USER_ID_PATTERN.fullmatch(raw_user_id):
        return "invalid", None

    user_id = int(raw_user_id)

    if user_id > MAX_TELEGRAM_USER_ID:
        return "invalid", None

    return "user", user_id


def _format_optional_value(
    value: Optional[object],
    prefix: str = "",
    monospace: bool = False,
) -> str:
    if value is None or value == "":
        return "-"

    formatted_value = f"{escape(prefix)}{escape(str(value))}"

    if monospace:
        return f"<code>{formatted_value}</code>"

    return formatted_value


def _format_current_id_response(chat: Chat, user: User) -> str:
    creation_month = estimate_account_creation_month(user.id)

    return "\n".join(
        (
            "<b>CHAT:</b>",
            f"  <b>title:</b> {_format_optional_value(chat.title)}",
            "  <b>type:</b> "
            f"{_format_optional_value(chat.type, monospace=True)}",
            "  <b>username:</b> "
            f"{_format_optional_value(chat.username, prefix='@')}",
            f"  <b>ID:</b> {_format_optional_value(chat.id, monospace=True)}",
            "",
            "<b>YOU:</b>",
            f"  <b>first name:</b> {_format_optional_value(user.first_name)}",
            f"  <b>last name:</b> {_format_optional_value(user.last_name)}",
            "  <b>username:</b> "
            f"{_format_optional_value(user.username, prefix='@')}",
            "  <b>language:</b> "
            f"{_format_optional_value(user.language_code, monospace=True)}",
            f"  <b>ID:</b> {_format_optional_value(user.id, monospace=True)}",
            "⭐<b>Creation date</b>⭐ <b>(approximately):</b> "
            f"{_format_optional_value(creation_month, monospace=True)}",
        )
    )


def _format_user_id_response(user_id: int) -> str:
    creation_month = estimate_account_creation_month(user_id)

    return "\n".join(
        (
            "<b>USER:</b>",
            f"  <b>ID:</b> <code>{user_id}</code>",
            "  ⭐<b>Creation date</b>⭐ <b>(approximately):</b> "
            f"<code>{creation_month}</code>",
        )
    )


async def handle_id_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Reply with current IDs or an estimated creation date by user ID."""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    metadata_text = format_log_metadata(get_update_metadata(update))

    LOGGER.info("Command received: /id | %s", metadata_text)

    if message is None or chat is None:
        return

    argument_type, user_id = _parse_user_id_argument(context.args)
    related_reply_message_id = get_related_reply_message_id(
        context.bot_data,
        ID_LOOKUP_FEATURE,
        chat.id,
        message.message_id,
    )

    if argument_type == "empty":
        if user is None:
            return

        response_text = _format_current_id_response(chat, user)
        response_signature = (
            "current",
            chat.title,
            chat.type,
            chat.username,
            chat.id,
            user.first_name,
            user.last_name,
            user.username,
            user.language_code,
            user.id,
        )
    elif argument_type == "invalid":
        if related_reply_message_id is not None:
            return

        response_text = INVALID_USER_ID_MESSAGE
        response_signature = ("invalid",)
    elif argument_type == "group":
        response_text = GROUP_ID_MESSAGE
        response_signature = ("group",)
    else:
        if user_id is None:
            return

        response_text = _format_user_id_response(user_id)
        response_signature = ("user", user_id)

    if is_message_signature_unchanged(
        context.bot_data,
        ID_LOOKUP_FEATURE,
        chat.id,
        message.message_id,
        response_signature,
    ):
        return

    if related_reply_message_id is None:
        reply_message = await message.reply_text(
            text=response_text,
            parse_mode=ParseMode.HTML,
            do_quote=True,
        )
        remember_related_reply_message_id(
            context.bot_data,
            ID_LOOKUP_FEATURE,
            chat.id,
            message.message_id,
            reply_message.message_id,
        )
        LOGGER.info(
            "ID lookup reply sent: argument_type=%s | %s",
            argument_type,
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
            "ID lookup reply updated: argument_type=%s | %s",
            argument_type,
            metadata_text,
        )

    remember_message_signature(
        context.bot_data,
        ID_LOOKUP_FEATURE,
        chat.id,
        message.message_id,
        response_signature,
    )
