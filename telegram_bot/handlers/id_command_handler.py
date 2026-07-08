# telegram_bot/handlers/id_command_handler.py

# Standard Libraries
import logging
import re
from html import escape
from typing import Final, Optional

# Third-party Libraries
from telegram import Chat, Message, ReplyKeyboardRemove, Update, User
from telegram.constants import ChatType, ParseMode
from telegram.ext import ContextTypes

# Custom Modules
from telegram_bot.keyboards.id_keyboard import (
    BOT_REQUEST_ID,
    CHANNEL_REQUEST_ID,
    CHAT_REQUEST_ID,
    USER_REQUEST_ID,
    build_entity_selection_keyboard,
    build_find_different_id_keyboard,
)
from telegram_bot.localization.language_preferences import (
    DEFAULT_LANGUAGE,
    resolve_user_language,
)
from telegram_bot.localization.messages import get_message
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
    language: str = DEFAULT_LANGUAGE,
) -> str:
    if value is None or value == "":
        return get_message("missing_value", language=language)

    formatted_value = f"{escape(prefix)}{escape(str(value))}"

    if monospace:
        return get_message(
            "monospace_value",
            language=language,
            value=formatted_value,
        )

    return formatted_value


def _format_current_id_response(
    chat: Chat,
    user: User,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    creation_month = estimate_account_creation_month(user.id, language)

    return get_message(
        "current_id_response",
        language=language,
        chat_title=_format_optional_value(chat.title, language=language),
        chat_type=_format_optional_value(
            chat.type,
            monospace=True,
            language=language,
        ),
        chat_username=_format_optional_value(
            chat.username,
            prefix="@",
            language=language,
        ),
        chat_id=_format_optional_value(
            chat.id,
            monospace=True,
            language=language,
        ),
        first_name=_format_optional_value(
            user.first_name,
            language=language,
        ),
        last_name=_format_optional_value(
            user.last_name,
            language=language,
        ),
        user_username=_format_optional_value(
            user.username,
            prefix="@",
            language=language,
        ),
        language_code=_format_optional_value(
            user.language_code,
            monospace=True,
            language=language,
        ),
        user_id=_format_optional_value(
            user.id,
            monospace=True,
            language=language,
        ),
        creation_month=_format_optional_value(
            creation_month,
            monospace=True,
            language=language,
        ),
    )


def _format_user_id_response(
    user_id: int,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    return get_message(
        "user_id_response",
        language=language,
        user_id=user_id,
        creation_month=estimate_account_creation_month(user_id, language),
    )


def _format_chat_id_response(
    chat_id: int,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    return get_message(
        "chat_id_response",
        language=language,
        chat_id=chat_id,
    )


async def handle_find_different_id_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Prompt the user to select a Telegram entity in a private chat."""
    callback_query = update.callback_query

    if callback_query is None:
        return

    await callback_query.answer()
    response_message = callback_query.message

    if not isinstance(response_message, Message):
        LOGGER.warning("ID entity selection skipped: message unavailable")
        return

    if response_message.chat.type != ChatType.PRIVATE:
        LOGGER.warning(
            "ID entity selection skipped outside private chat | chat_id=%s",
            response_message.chat_id,
        )
        return

    user = callback_query.from_user
    language = resolve_user_language(user.id, user.language_code)
    user_mention = get_message(
        "user_mention",
        language=language,
        user_id=user.id,
        name=escape(user.first_name),
    )
    prompt_text = get_message(
        "entity_selection_prompt",
        language=language,
        user_mention=user_mention,
    )

    await context.bot.send_message(
        chat_id=response_message.chat_id,
        text=prompt_text,
        parse_mode=ParseMode.HTML,
        reply_markup=build_entity_selection_keyboard(),
    )
    LOGGER.info(
        "ID entity selector opened | chat_id=%s, user_id=%s",
        response_message.chat_id,
        user.id,
    )


async def handle_shared_id_entity(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Reply with the ID of an entity shared through the selector."""
    message = update.effective_message
    user = update.effective_user

    if message is None:
        return

    language = resolve_user_language(
        user.id if user is not None else None,
        user.language_code if user is not None else None,
    )

    shared_chat = message.chat_shared
    shared_users = message.users_shared

    if shared_chat is not None:
        if shared_chat.request_id not in {
            CHAT_REQUEST_ID,
            CHANNEL_REQUEST_ID,
        }:
            LOGGER.warning(
                "Unknown shared chat request ID: %s",
                shared_chat.request_id,
            )
            return

        response_text = _format_chat_id_response(
            shared_chat.chat_id,
            language,
        )
        entity_type = (
            "channel"
            if shared_chat.request_id == CHANNEL_REQUEST_ID
            else "chat"
        )
        entity_id = shared_chat.chat_id
    elif shared_users is not None:
        if shared_users.request_id not in {USER_REQUEST_ID, BOT_REQUEST_ID}:
            LOGGER.warning(
                "Unknown shared user request ID: %s",
                shared_users.request_id,
            )
            return

        if not shared_users.users:
            LOGGER.warning("Shared users response contains no users")
            return

        entity_id = shared_users.users[0].user_id
        response_text = _format_user_id_response(entity_id, language)
        entity_type = (
            "bot"
            if shared_users.request_id == BOT_REQUEST_ID
            else "user"
        )
    else:
        return

    await message.reply_text(
        text=response_text,
        parse_mode=ParseMode.HTML,
        do_quote=True,
        reply_markup=ReplyKeyboardRemove(),
    )
    LOGGER.info(
        "Shared ID entity handled: entity_type=%s, entity_id=%s | %s",
        entity_type,
        entity_id,
        format_log_metadata(get_update_metadata(update)),
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

    language = resolve_user_language(
        user.id if user is not None else None,
        user.language_code if user is not None else None,
    )

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

        response_text = _format_current_id_response(chat, user, language)
        response_signature = (
            "current",
            language,
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

        response_text = get_message("invalid_user_id", language=language)
        response_signature = ("invalid", language)
    elif argument_type == "group":
        response_text = get_message(
            "positive_user_ids_only",
            language=language,
        )
        response_signature = ("group", language)
    else:
        if user_id is None:
            return

        response_text = _format_user_id_response(user_id, language)
        response_signature = ("user", user_id, language)

    response_keyboard = None

    if (
        argument_type in {"empty", "user"}
        and chat.type == ChatType.PRIVATE
    ):
        response_keyboard = build_find_different_id_keyboard()

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
            reply_markup=response_keyboard,
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
            reply_markup=response_keyboard,
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
